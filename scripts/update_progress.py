#!/usr/bin/env python3
"""
Script para actualizar progreso de migración después de cada batch.

Este script:
1. Lee outputs generados por sub-agentes (knowledge/json/)
2. Actualiza progress.json con objetos procesados
3. Marca objetos como completados en manifest
4. Genera instrucciones para próximo batch

Uso (desde el proyecto con datos, NO desde el plugin):
    cd /path/to/phantomx-nexus
    python /path/to/oracle-postgres-migration/scripts/update_progress.py batch_001

    O si el plugin está en directorio padre:
    cd /path/to/phantomx-nexus
    python ../oracle-postgres-migration/scripts/update_progress.py batch_001

IMPORTANTE: El script usa Path.cwd() para detectar el directorio del proyecto.
            Debe ejecutarse desde el directorio que contiene sql/extracted/ y knowledge/

Args:
    batch_id: ID del batch completado (ej: batch_001)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Directorio base del proyecto (usa CWD para compatibilidad con --plugin-dir)
BASE_DIR = Path.cwd()
EXTRACTED_DIR = BASE_DIR / "sql" / "extracted"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
JSON_DIR = KNOWLEDGE_DIR / "json"
MANIFEST_FILE = EXTRACTED_DIR / "manifest.json"
PROGRESS_FILE = EXTRACTED_DIR / "progress.json"


def load_manifest() -> Dict:
    """Carga manifest.json"""
    if not MANIFEST_FILE.exists():
        print(f"❌ Error: {MANIFEST_FILE} no existe")
        print("   Ejecuta primero: python scripts/prepare_migration.py")
        sys.exit(1)

    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_progress() -> Dict:
    """Carga progress.json"""
    if not PROGRESS_FILE.exists():
        print(f"❌ Error: {PROGRESS_FILE} no existe")
        print("   Ejecuta primero: python scripts/prepare_migration.py")
        sys.exit(1)

    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def detect_processed_objects(batch_id: str) -> List[str]:
    """
    Detecta qué objetos fueron procesados buscando outputs JSON.

    Args:
        batch_id: ID del batch (ej: batch_001)

    Returns:
        Lista de object_ids procesados
    """
    print(f"\n🔍 Detectando objetos procesados en {batch_id}...\n")

    batch_dir = JSON_DIR / batch_id

    if not batch_dir.exists():
        print(f"⚠️  Directorio {batch_dir} no existe")
        print(f"   No se encontraron outputs para {batch_id}")
        return []

    # Buscar archivos JSON generados
    json_files = list(batch_dir.glob("obj_*.json"))

    processed_ids = []
    for json_file in json_files:
        # Extraer object_id del nombre de archivo
        # Formato: obj_0001_NOMBRE_OBJETO.json
        parts = json_file.stem.split('_', 2)  # Split máximo 2 veces
        if len(parts) >= 2:
            object_id = f"{parts[0]}_{parts[1]}"  # obj_0001
            processed_ids.append(object_id)

    processed_ids.sort()

    print(f"  ✅ Encontrados {len(processed_ids)} objetos procesados")
    if processed_ids:
        print(f"     Primero: {processed_ids[0]}")
        print(f"     Último: {processed_ids[-1]}")

    return processed_ids


def update_manifest(manifest: Dict, processed_ids: List[str]) -> Dict:
    """
    Actualiza manifest marcando objetos como procesados.

    Args:
        manifest: Manifest actual
        processed_ids: Lista de object_ids procesados

    Returns:
        Manifest actualizado
    """
    print(f"\n📝 Actualizando manifest...\n")

    updated_count = 0

    for obj in manifest["objects"]:
        if obj["object_id"] in processed_ids and obj["status"] == "pending":
            obj["status"] = "processed"
            obj["processed_at"] = datetime.now().isoformat()
            updated_count += 1

    print(f"  ✅ Actualizados {updated_count} objetos en manifest")

    # Guardar manifest actualizado
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest


def update_progress(progress: Dict, batch_id: str, processed_count: int, last_object_id: str) -> Dict:
    """
    Actualiza progress.json con información del batch completado.

    Args:
        progress: Progress actual
        batch_id: ID del batch completado
        processed_count: Cantidad de objetos procesados
        last_object_id: ID del último objeto procesado

    Returns:
        Progress actualizado
    """
    print(f"\n📊 Actualizando progreso...\n")

    # Actualizar contadores
    progress["processed_count"] += processed_count
    progress["pending_count"] = progress["total_objects"] - progress["processed_count"]
    progress["current_batch"] = batch_id
    progress["last_object_processed"] = last_object_id
    progress["last_updated"] = datetime.now().isoformat()

    # Agregar batch a historial
    batch_info = {
        "batch_id": batch_id,
        "processed_count": processed_count,
        "completed_at": datetime.now().isoformat()
    }
    progress["batches"].append(batch_info)

    # Actualizar status
    if progress["pending_count"] == 0:
        progress["status"] = "completed"
    else:
        progress["status"] = "in_progress"

    # Guardar progress actualizado
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

    print(f"  ✅ Progreso actualizado:")
    print(f"     Procesados: {progress['processed_count']}/{progress['total_objects']}")
    print(f"     Pendientes: {progress['pending_count']}")
    print(f"     Porcentaje: {progress['processed_count']/progress['total_objects']*100:.1f}%")

    return progress


def generate_next_batch_instructions(manifest: Dict, progress: Dict, batch_size: int = 200):
    """
    Genera instrucciones para procesar próximo batch.

    Args:
        manifest: Manifest actualizado
        progress: Progress actualizado
        batch_size: Objetos por batch (default: 200)
    """
    print(f"\n{'='*80}")
    print("PRÓXIMO BATCH")
    print(f"{'='*80}\n")

    if progress["status"] == "completed":
        print("✅ ¡FASE 1 COMPLETADA! Todos los objetos han sido procesados.")
        print("\nPróximo paso:")
        print("  Ejecutar FASE 2A: Conversión simple con ora2pg")
        print("  ```bash")
        print("  ./scripts/convert_simple_objects.sh")
        print("  ```")
        return

    # Obtener objetos pendientes
    all_objects = manifest["objects"]
    pending_objects = [obj for obj in all_objects if obj["status"] == "pending"]

    if not pending_objects:
        print("⚠️  No hay objetos pendientes (pero status no es 'completed')")
        return

    # Próximo batch
    batch_num = int(progress["current_batch"].split('_')[1]) + 1
    next_batch = f"batch_{batch_num:03d}"

    batch_objects = pending_objects[:batch_size]

    print(f"📦 Próximo batch: {next_batch}")
    print(f"   Objetos pendientes: {len(pending_objects)}")
    print(f"   Objetos en este batch: {len(batch_objects)}")
    print(f"   Progreso después: {progress['processed_count'] + len(batch_objects)}/{progress['total_objects']}")

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


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("❌ Error: Falta argumento batch_id")
        print("\nUso:")
        print("  python scripts/update_progress.py batch_001")
        sys.exit(1)

    batch_id = sys.argv[1]

    print("="*80)
    print(f"ACTUALIZAR PROGRESO - {batch_id}")
    print("="*80)

    # Cargar archivos
    manifest = load_manifest()
    progress = load_progress()

    # Detectar objetos procesados
    processed_ids = detect_processed_objects(batch_id)

    if not processed_ids:
        print("\n⚠️  No se encontraron objetos procesados")
        print(f"   Verifica que los sub-agentes generaron outputs en knowledge/json/{batch_id}/")
        sys.exit(1)

    # Actualizar manifest
    manifest = update_manifest(manifest, processed_ids)

    # Actualizar progress
    last_object_id = processed_ids[-1] if processed_ids else None
    progress = update_progress(progress, batch_id, len(processed_ids), last_object_id)

    # Generar instrucciones para próximo batch
    generate_next_batch_instructions(manifest, progress)

    print("\n" + "="*80)
    print("✅ PROGRESO ACTUALIZADO")
    print("="*80)


if __name__ == "__main__":
    main()
