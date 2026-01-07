#!/usr/bin/env python3
"""
Script de preparación para migración Oracle → PostgreSQL

Este script:
1. Parsea archivos SQL grandes (functions.sql, packages_body.sql, etc.)
2. Extrae objetos individuales
3. Genera manifest.json con índice de todos los objetos
4. Crea progress.json para tracking de progreso
5. Permite reanudación desde cualquier punto

Uso (desde el proyecto con datos, NO desde el plugin):
    cd /path/to/phantomx-nexus
    python /path/to/oracle-postgres-migration/scripts/prepare_migration.py

    O si el plugin está en directorio padre:
    cd /path/to/phantomx-nexus
    python ../oracle-postgres-migration/scripts/prepare_migration.py

IMPORTANTE: El script usa Path.cwd() para detectar el directorio del proyecto.
            Debe ejecutarse desde el directorio que contiene sql/extracted/

Output (creado en CWD):
    sql/extracted/manifest.json          # Índice de todos los objetos
    sql/extracted/progress.json          # Estado del procesamiento
    sql/extracted/objects/               # Objetos individuales (opcional)
"""

import re
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Directorio base del proyecto (usa CWD para compatibilidad con --plugin-dir)
BASE_DIR = Path.cwd()
EXTRACTED_DIR = BASE_DIR / "sql" / "extracted"
OBJECTS_DIR = EXTRACTED_DIR / "objects"
MANIFEST_FILE = EXTRACTED_DIR / "manifest.json"
PROGRESS_FILE = EXTRACTED_DIR / "progress.json"


def parse_sql_file(file_path: Path, object_type: str) -> List[Dict]:
    """
    Parsea archivo SQL grande y extrae objetos individuales.

    Args:
        file_path: Ruta al archivo SQL
        object_type: Tipo de objeto (FUNCTION, PROCEDURE, PACKAGE, etc.)

    Returns:
        Lista de diccionarios con metadata de cada objeto
    """
    print(f"📖 Parseando {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    objects = []

    # Patrones de detección según tipo de objeto
    if object_type in ["FUNCTION", "PROCEDURE"]:
        # Patrón: CREATE OR REPLACE FUNCTION/PROCEDURE nombre ...
        pattern = r'CREATE\s+OR\s+REPLACE\s+' + object_type + r'\s+(\w+\.?\w*)'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            # Encontrar END; del objeto actual
            # Buscar próximo CREATE o final del archivo
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            # Buscar el END; más cercano antes del próximo CREATE
            end_search = content[start_pos:end_pos]
            end_match = re.search(r'END\s+\w*\s*;', end_search, re.IGNORECASE)

            if end_match:
                actual_end = start_pos + end_match.end()
            else:
                actual_end = end_pos

            object_name = match.group(1).upper()
            object_code = content[start_pos:actual_end].strip()

            # Calcular líneas
            lines_before = content[:start_pos].count('\n') + 1
            lines_in_object = object_code.count('\n') + 1

            objects.append({
                "object_id": f"{object_type.lower()}_{i+1:04d}",
                "object_name": object_name,
                "object_type": object_type,
                "source_file": file_path.name,
                "line_start": lines_before,
                "line_end": lines_before + lines_in_object - 1,
                "char_start": start_pos,
                "char_end": actual_end,
                "code_length": len(object_code),
                "status": "pending"
            })

    elif object_type == "PACKAGE_SPEC":
        # Patrón: CREATE OR REPLACE PACKAGE nombre IS/AS
        pattern = r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+(\w+\.?\w*)\s+(IS|AS)'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()

            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            end_search = content[start_pos:end_pos]
            end_match = re.search(r'END\s+\w*\s*;', end_search, re.IGNORECASE)

            if end_match:
                actual_end = start_pos + end_match.end()
            else:
                actual_end = end_pos

            object_name = match.group(1).upper()
            object_code = content[start_pos:actual_end].strip()

            lines_before = content[:start_pos].count('\n') + 1
            lines_in_object = object_code.count('\n') + 1

            objects.append({
                "object_id": f"pkg_spec_{i+1:04d}",
                "object_name": object_name,
                "object_type": "PACKAGE_SPEC",
                "source_file": file_path.name,
                "line_start": lines_before,
                "line_end": lines_before + lines_in_object - 1,
                "char_start": start_pos,
                "char_end": actual_end,
                "code_length": len(object_code),
                "status": "pending"
            })

    elif object_type == "PACKAGE_BODY":
        # Patrón: CREATE OR REPLACE PACKAGE BODY nombre IS/AS
        pattern = r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+BODY\s+(\w+\.?\w*)\s+(IS|AS)'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()

            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            end_search = content[start_pos:end_pos]
            # Package body termina con END package_name;
            end_match = re.search(r'END\s+\w+\s*;', end_search, re.IGNORECASE)

            if end_match:
                actual_end = start_pos + end_match.end()
            else:
                actual_end = end_pos

            object_name = match.group(1).upper()
            object_code = content[start_pos:actual_end].strip()

            lines_before = content[:start_pos].count('\n') + 1
            lines_in_object = object_code.count('\n') + 1

            objects.append({
                "object_id": f"pkg_body_{i+1:04d}",
                "object_name": object_name,
                "object_type": "PACKAGE_BODY",
                "source_file": file_path.name,
                "line_start": lines_before,
                "line_end": lines_before + lines_in_object - 1,
                "char_start": start_pos,
                "char_end": actual_end,
                "code_length": len(object_code),
                "status": "pending"
            })

    elif object_type == "TRIGGER":
        # Patrón: CREATE OR REPLACE TRIGGER nombre
        pattern = r'CREATE\s+OR\s+REPLACE\s+TRIGGER\s+(\w+\.?\w*)'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()

            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            end_search = content[start_pos:end_pos]
            end_match = re.search(r'END\s*;', end_search, re.IGNORECASE)

            if end_match:
                actual_end = start_pos + end_match.end()
            else:
                actual_end = end_pos

            object_name = match.group(1).upper()
            object_code = content[start_pos:actual_end].strip()

            lines_before = content[:start_pos].count('\n') + 1
            lines_in_object = object_code.count('\n') + 1

            objects.append({
                "object_id": f"trigger_{i+1:04d}",
                "object_name": object_name,
                "object_type": "TRIGGER",
                "source_file": file_path.name,
                "line_start": lines_before,
                "line_end": lines_before + lines_in_object - 1,
                "char_start": start_pos,
                "char_end": actual_end,
                "code_length": len(object_code),
                "status": "pending"
            })

    print(f"  ✅ Encontrados {len(objects)} objetos de tipo {object_type}")
    return objects


def generate_manifest() -> Dict:
    """
    Genera manifest.json con índice completo de todos los objetos.

    Returns:
        Diccionario con manifest completo
    """
    print("\n🔍 Generando manifest de objetos...\n")

    all_objects = []

    # Archivos a procesar
    files_to_parse = [
        (EXTRACTED_DIR / "functions.sql", "FUNCTION"),
        (EXTRACTED_DIR / "procedures.sql", "PROCEDURE"),
        (EXTRACTED_DIR / "packages_spec.sql", "PACKAGE_SPEC"),
        (EXTRACTED_DIR / "packages_body.sql", "PACKAGE_BODY"),
        (EXTRACTED_DIR / "triggers.sql", "TRIGGER"),
    ]

    for file_path, object_type in files_to_parse:
        if file_path.exists():
            objects = parse_sql_file(file_path, object_type)
            all_objects.extend(objects)
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")

    # Renumerar object_id secuencialmente
    for i, obj in enumerate(all_objects, start=1):
        obj["object_id"] = f"obj_{i:04d}"

    # Generar manifest
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "total_objects": len(all_objects),
        "objects_by_type": {
            "FUNCTION": sum(1 for o in all_objects if o["object_type"] == "FUNCTION"),
            "PROCEDURE": sum(1 for o in all_objects if o["object_type"] == "PROCEDURE"),
            "PACKAGE_SPEC": sum(1 for o in all_objects if o["object_type"] == "PACKAGE_SPEC"),
            "PACKAGE_BODY": sum(1 for o in all_objects if o["object_type"] == "PACKAGE_BODY"),
            "TRIGGER": sum(1 for o in all_objects if o["object_type"] == "TRIGGER"),
        },
        "objects": all_objects
    }

    # Guardar manifest
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Manifest generado: {MANIFEST_FILE}")
    print(f"   Total objetos: {manifest['total_objects']}")
    for obj_type, count in manifest['objects_by_type'].items():
        print(f"   - {obj_type}: {count}")

    return manifest


def initialize_progress(manifest: Dict) -> Dict:
    """
    Inicializa archivo progress.json para tracking.

    Args:
        manifest: Manifest generado

    Returns:
        Diccionario con estado inicial de progreso
    """
    print("\n📊 Inicializando tracking de progreso...\n")

    # Verificar si ya existe progress.json
    if PROGRESS_FILE.exists():
        print(f"⚠️  Ya existe {PROGRESS_FILE}")
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            existing_progress = json.load(f)

        print(f"   Progreso actual:")
        print(f"   - Procesados: {existing_progress['processed_count']}/{existing_progress['total_objects']}")
        print(f"   - Último batch: {existing_progress['current_batch']}")
        print(f"   - Último objeto: {existing_progress['last_object_processed']}")

        response = input("\n¿Resetear progreso? (s/n): ")
        if response.lower() != 's':
            print("   Manteniendo progreso existente")
            return existing_progress

    # Crear nuevo progress.json
    progress = {
        "initialized_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "total_objects": manifest["total_objects"],
        "processed_count": 0,
        "pending_count": manifest["total_objects"],
        "current_batch": "batch_000",
        "last_object_processed": None,
        "status": "initialized",
        "batches": []
    }

    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

    print(f"✅ Progress inicializado: {PROGRESS_FILE}")
    return progress


def generate_batch_instructions(manifest: Dict, progress: Dict, batch_size: int = 200):
    """
    Genera instrucciones para procesar próximo batch.

    Args:
        manifest: Manifest de objetos
        progress: Estado actual de progreso
        batch_size: Objetos por batch (default: 200 = 20 agentes × 10 objetos)
    """
    print("\n📋 Generando instrucciones para próximo batch...\n")

    # Obtener objetos pendientes
    all_objects = manifest["objects"]
    processed_count = progress["processed_count"]

    if processed_count >= len(all_objects):
        print("✅ Todos los objetos ya fueron procesados!")
        return

    # Próximo batch
    batch_start = processed_count
    batch_end = min(batch_start + batch_size, len(all_objects))
    batch_objects = all_objects[batch_start:batch_end]

    current_batch = progress["current_batch"]
    batch_num = int(current_batch.split('_')[1]) + 1
    next_batch = f"batch_{batch_num:03d}"

    print(f"📦 Batch: {next_batch}")
    print(f"   Objetos: {batch_start + 1} - {batch_end}")
    print(f"   Total en batch: {len(batch_objects)}")
    print(f"   Progreso: {batch_end}/{len(all_objects)} ({batch_end/len(all_objects)*100:.1f}%)")

    # Generar instrucciones para Claude
    print(f"\n{'='*80}")
    print("INSTRUCCIONES PARA CLAUDE CODE")
    print(f"{'='*80}\n")

    print(f"Lanzar 20 agentes plsql-analyzer en paralelo para procesar {next_batch}:")
    print(f"\n```")

    # Dividir batch en 20 sub-agentes (10 objetos cada uno)
    objects_per_agent = 10
    num_agents = (len(batch_objects) + objects_per_agent - 1) // objects_per_agent

    for agent_idx in range(num_agents):
        agent_start = agent_idx * objects_per_agent
        agent_end = min(agent_start + objects_per_agent, len(batch_objects))
        agent_objects = batch_objects[agent_start:agent_end]

        obj_ids = [obj["object_id"] for obj in agent_objects]

        print(f"# Agente {agent_idx + 1}: Objetos {obj_ids[0]} a {obj_ids[-1]}")
        print(f"Task plsql-analyzer \"Analizar objetos {obj_ids[0]} a {obj_ids[-1]} del {next_batch}\"")
        print()

    print(f"```\n")

    print("Después de completar el batch, ejecuta:")
    print(f"```bash")
    print(f"python scripts/update_progress.py {next_batch}")
    print(f"```\n")


def create_directory_structure():
    """
    Crea estructura de directorios necesaria para la migración.

    Crea automáticamente todas las carpetas donde se guardarán outputs:
    - knowledge/ (análisis)
    - migrated/ (código convertido)
    - compilation_results/ (resultados de validación)
    - shadow_tests/ (testing comparativo)
    """
    print("\n📁 Creando estructura de directorios...\n")

    directories = [
        "knowledge/json",
        "knowledge/markdown",
        "knowledge/classification",
        "migrated/simple/functions",
        "migrated/simple/procedures",
        "migrated/simple/packages",
        "migrated/simple/triggers",
        "migrated/complex/functions",
        "migrated/complex/procedures",
        "migrated/complex/packages",
        "migrated/complex/triggers",
        "compilation_results/success",
        "compilation_results/errors",
        "shadow_tests"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = BASE_DIR / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1

    if created_count > 0:
        print(f"  ✅ Creados {created_count} directorios nuevos")
    else:
        print(f"  ✅ Estructura de directorios ya existe")


def main():
    """Función principal"""
    print("="*80)
    print("PREPARACIÓN MIGRACIÓN ORACLE → POSTGRESQL")
    print("="*80)

    # Verificar que directorio extracted/ existe
    if not EXTRACTED_DIR.exists():
        print(f"❌ Error: Directorio {EXTRACTED_DIR} no existe")
        print(f"   Ejecuta primero el script de extracción de Oracle")
        return

    # Crear estructura de directorios
    create_directory_structure()

    # Generar manifest
    manifest = generate_manifest()

    # Inicializar progress
    progress = initialize_progress(manifest)

    # Generar instrucciones para próximo batch
    generate_batch_instructions(manifest, progress)

    print("\n" + "="*80)
    print("✅ PREPARACIÓN COMPLETADA")
    print("="*80)
    print("\nArchivos generados:")
    print(f"  - {MANIFEST_FILE}")
    print(f"  - {PROGRESS_FILE}")
    print("\nPróximo paso:")
    print("  Ejecutar las instrucciones generadas arriba en Claude Code")


if __name__ == "__main__":
    main()
