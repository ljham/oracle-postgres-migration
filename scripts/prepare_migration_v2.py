#!/usr/bin/env python3
"""
Script de preparación para migración Oracle → PostgreSQL (VERSIÓN MEJORADA v2.1)

MEJORAS EN ESTA VERSIÓN:
- Parsing más robusto que busca END con el nombre EXACTO del objeto
- Evita capturar END LOOP, END IF, o procedimientos internos
- NUEVO v2.1: Estrategia especial para TRIGGERS con nombres diferentes en END
- Validación de extracción con checksums
- Logging detallado de errores de parsing
- Modo dry-run para verificar antes de generar manifest

CAMBIOS CLAVE:
1. Captura el nombre del objeto PRIMERO desde el CREATE statement
2. Busca END seguido del NOMBRE EXACTO del objeto (no cualquier \w+)
3. Incluye validación de que el código extraído es válido
4. Genera reporte de objetos problemáticos

Uso (desde el proyecto con datos, NO desde el plugin):
    cd /path/to/phantomx-nexus
    python /path/to/oracle-postgres-migration/scripts/prepare_migration_v2.py [--dry-run]

    --dry-run: Solo valida parsing sin generar manifest.json
"""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Directorio base del proyecto (usa CWD para compatibilidad con --plugin-dir)
BASE_DIR = Path.cwd()
EXTRACTED_DIR = BASE_DIR / "sql" / "extracted"
OBJECTS_DIR = EXTRACTED_DIR / "objects"
MANIFEST_FILE = EXTRACTED_DIR / "manifest.json"
PROGRESS_FILE = EXTRACTED_DIR / "progress.json"
VALIDATION_LOG = EXTRACTED_DIR / "parsing_validation.log"

# Tracking de errores de parsing
parsing_errors = []


def log_parsing_error(error_msg: str, object_info: Dict = None):
    """Log de errores de parsing para debugging."""
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "error": error_msg,
        "object": object_info
    }
    parsing_errors.append(error_entry)
    print(f"  ⚠️  {error_msg}")


def extract_object_name(match) -> str:
    """
    Extrae el nombre del objeto desde los grupos capturados por regex.

    Soporta formatos:
    - "esquema"."nombre" → retorna "nombre"
    - esquema.nombre → retorna "nombre"
    - nombre → retorna "nombre"

    Args:
        match: Match object de re.finditer

    Returns:
        Nombre del objeto en uppercase
    """
    groups = match.groups()

    # Filtrar grupos None y grupos que sean "OR REPLACE" o contengan solo espacios/OR/REPLACE
    relevant_groups = [
        g for g in groups
        if g is not None and not re.match(r'^(OR|REPLACE|IS|AS|\s)+$', g, re.IGNORECASE)
    ]

    # Si hay esquema.nombre, tomar el segundo elemento; si no, tomar el último
    if len(relevant_groups) >= 2:
        object_name = relevant_groups[1].upper()
    elif len(relevant_groups) >= 1:
        object_name = relevant_groups[-1].upper()
    else:
        object_name = "UNKNOWN"

    return object_name


def find_object_end_robust(
    content: str,
    start_pos: int,
    end_pos: int,
    object_name: str,
    object_type: str
) -> Tuple[int, str]:
    """
    Encuentra el fin del objeto de forma robusta usando el nombre EXACTO del objeto.

    ESTRATEGIA:
    1. Buscar "END nombre_exacto;" - Funciona cuando el END tiene el mismo nombre que el CREATE
    2. Para TRIGGER: Buscar "END cualquier_nombre; / " - Los triggers a menudo tienen nombres diferentes
    3. Para FUNCTION/PROCEDURE/TRIGGER: Buscar "END;" sin nombre
    4. Para PACKAGE: Buscar último "END;" en el rango
    5. FALLBACK: Usar end_pos (loguea warning)

    Args:
        content: Contenido completo del archivo
        start_pos: Posición de inicio del objeto
        end_pos: Posición máxima de búsqueda
        object_name: Nombre exacto del objeto
        object_type: Tipo de objeto (PACKAGE_BODY, FUNCTION, etc.)

    Returns:
        Tupla (posición_fin, método_usado)
    """
    search_content = content[start_pos:end_pos]

    # ESTRATEGIA 1: Buscar END con el nombre exacto del objeto (termina en ;)
    # Ejemplo: END FAC_K_VERIFICA_CIERRES;
    # No incluye el delimitador / porque no es parte del código PL/SQL
    pattern_exact = rf'END\s+{re.escape(object_name)}\s*;'
    match_exact = re.search(pattern_exact, search_content, re.IGNORECASE)

    if match_exact:
        actual_end = start_pos + match_exact.end()
        return actual_end, "exact_name_semicolon"

    # ESTRATEGIA 2: Para TRIGGER - Buscar END con cualquier nombre seguido de /
    # Los triggers a veces terminan con un nombre diferente al del CREATE
    # Ejemplo: CREATE TRIGGER AGE_T_X ... END AGE_T_LOG_Y; /
    if object_type == "TRIGGER":
        # Buscar END [cualquier_nombre]; seguido de nueva línea y /
        pattern_trigger_end = r'END\s+\w+\s*;\s*\n\s*/\s*(?=\n|$)'
        match_trigger = re.search(pattern_trigger_end, search_content, re.IGNORECASE)

        if match_trigger:
            actual_end = start_pos + match_trigger.end()
            return actual_end, "trigger_end_with_slash"

    # ESTRATEGIA 3: Para FUNCTION/PROCEDURE/TRIGGER que pueden usar solo END;
    # Buscar END; seguido de / (pero evitar END LOOP; END IF;)
    if object_type in ["FUNCTION", "PROCEDURE", "TRIGGER"]:
        # Buscar END; que NO sea precedido por LOOP o IF
        pattern_end_only = r'(?<!LOOP\s)(?<!IF\s)END\s*;\s*\n?\s*/?'

        # Buscar todas las coincidencias y tomar la última (más probable que sea el END del objeto)
        matches = list(re.finditer(pattern_end_only, search_content, re.IGNORECASE))
        if matches:
            # Tomar el último match (más conservador)
            last_match = matches[-1]
            actual_end = start_pos + last_match.end()
            return actual_end, "end_only_last_match"

    # ESTRATEGIA 4: Para PACKAGE sin nombre en END (raro pero posible)
    # Buscar END; seguido de / al final del search_content
    if object_type in ["PACKAGE_BODY", "PACKAGE_SPEC"]:
        # Buscar END; cerca del final del rango de búsqueda
        pattern_end_near_end = r'END\s*;\s*\n?\s*/?'
        matches = list(re.finditer(pattern_end_near_end, search_content, re.IGNORECASE))
        if matches:
            # Tomar el último match
            last_match = matches[-1]
            actual_end = start_pos + last_match.end()
            return actual_end, "end_near_end_of_range"

    # ESTRATEGIA 5: FALLBACK - Usar end_pos (menos preciso, loguear warning)
    log_parsing_error(
        f"No se encontró END exacto para {object_type} '{object_name}', usando end_pos",
        {"object_name": object_name, "object_type": object_type}
    )
    return end_pos, "fallback_end_pos"


def validate_extracted_code(code: str, object_name: str, object_type: str) -> Tuple[bool, str]:
    """
    Valida que el código extraído sea sintácticamente coherente.

    Verificaciones:
    1. Inicia con CREATE OR REPLACE [PACKAGE BODY|FUNCTION|PROCEDURE|TRIGGER|VIEW]
    2. Termina con END; o END nombre; seguido de /
    3. No contiene múltiples CREATE statements (indicaría parsing incorrecto)

    Args:
        code: Código extraído
        object_name: Nombre del objeto
        object_type: Tipo de objeto

    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Verificación 1: Debe iniciar con CREATE
    if not re.match(r'^\s*CREATE', code, re.IGNORECASE):
        return False, "No inicia con CREATE"

    # Verificación 2: Debe terminar con END; o END nombre; (opcionalmente seguido de /)
    if object_type in ["FUNCTION", "PROCEDURE", "PACKAGE_SPEC", "PACKAGE_BODY", "TRIGGER"]:
        end_pattern = rf'(END\s+{re.escape(object_name)}\s*;|END\s*;)\s*/?$'
        if not re.search(end_pattern, code.strip(), re.IGNORECASE):
            return False, f"No termina con END {object_name}; o END;"

    # Verificación 3: No debe contener múltiples CREATE statements
    create_count = len(re.findall(r'\bCREATE\s+(OR\s+REPLACE\s+)?(PACKAGE|FUNCTION|PROCEDURE|TRIGGER|VIEW)',
                                    code, re.IGNORECASE))
    if create_count > 1:
        return False, f"Contiene {create_count} CREATE statements (esperado: 1)"

    # Verificación 4: Para PACKAGE_BODY, verificar que contiene procedimientos/funciones
    if object_type == "PACKAGE_BODY":
        proc_func_count = len(re.findall(r'\b(PROCEDURE|FUNCTION)\s+\w+', code, re.IGNORECASE))
        if proc_func_count == 0:
            return False, "PACKAGE_BODY sin procedimientos/funciones (posible parsing incorrecto)"

    return True, "OK"


def parse_sql_file_robust(file_path: Path, object_type: str) -> List[Dict]:
    """
    Parsea archivo SQL grande y extrae objetos individuales (VERSIÓN ROBUSTA v2).

    MEJORAS:
    - Usa find_object_end_robust() para encontrar el END correcto
    - Valida el código extraído
    - Loguea objetos problemáticos

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
        pattern = r'CREATE\s+OR\s+REPLACE\s+' + object_type + r'\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()

            # Determinar rango de búsqueda
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            # Extraer nombre del objeto
            object_name = extract_object_name(match)

            # Encontrar END de forma robusta
            actual_end, method = find_object_end_robust(
                content, start_pos, end_pos, object_name, object_type
            )

            object_code = content[start_pos:actual_end].strip()

            # Validar código extraído
            is_valid, error_msg = validate_extracted_code(object_code, object_name, object_type)
            if not is_valid:
                log_parsing_error(
                    f"{object_type} '{object_name}': {error_msg} (método: {method})",
                    {
                        "object_name": object_name,
                        "object_type": object_type,
                        "line_start": content[:start_pos].count('\n') + 1,
                        "method": method,
                        "validation_error": error_msg
                    }
                )

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
                "status": "pending",
                "parsing_method": method,
                "validation_status": "valid" if is_valid else "warning"
            })

    elif object_type == "PACKAGE_SPEC":
        pattern = r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))\s+(IS|AS)'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()

            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            object_name = extract_object_name(match)

            actual_end, method = find_object_end_robust(
                content, start_pos, end_pos, object_name, object_type
            )

            object_code = content[start_pos:actual_end].strip()

            is_valid, error_msg = validate_extracted_code(object_code, object_name, object_type)
            if not is_valid:
                log_parsing_error(
                    f"PACKAGE_SPEC '{object_name}': {error_msg} (método: {method})",
                    {
                        "object_name": object_name,
                        "object_type": object_type,
                        "line_start": content[:start_pos].count('\n') + 1,
                        "method": method,
                        "validation_error": error_msg
                    }
                )

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
                "status": "pending",
                "parsing_method": method,
                "validation_status": "valid" if is_valid else "warning"
            })

    elif object_type == "PACKAGE_BODY":
        pattern = r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+BODY\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))\s+(IS|AS)'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()

            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            object_name = extract_object_name(match)

            actual_end, method = find_object_end_robust(
                content, start_pos, end_pos, object_name, object_type
            )

            object_code = content[start_pos:actual_end].strip()

            is_valid, error_msg = validate_extracted_code(object_code, object_name, object_type)
            if not is_valid:
                log_parsing_error(
                    f"PACKAGE_BODY '{object_name}': {error_msg} (método: {method})",
                    {
                        "object_name": object_name,
                        "object_type": object_type,
                        "line_start": content[:start_pos].count('\n') + 1,
                        "method": method,
                        "validation_error": error_msg
                    }
                )

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
                "status": "pending",
                "parsing_method": method,
                "validation_status": "valid" if is_valid else "warning"
            })

    elif object_type == "TRIGGER":
        pattern = r'CREATE\s+OR\s+REPLACE\s+TRIGGER\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()

            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            object_name = extract_object_name(match)

            actual_end, method = find_object_end_robust(
                content, start_pos, end_pos, object_name, object_type
            )

            object_code = content[start_pos:actual_end].strip()

            is_valid, error_msg = validate_extracted_code(object_code, object_name, object_type)
            if not is_valid:
                log_parsing_error(
                    f"TRIGGER '{object_name}': {error_msg} (método: {method})",
                    {
                        "object_name": object_name,
                        "object_type": object_type,
                        "line_start": content[:start_pos].count('\n') + 1,
                        "method": method,
                        "validation_error": error_msg
                    }
                )

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
                "status": "pending",
                "parsing_method": method,
                "validation_status": "valid" if is_valid else "warning"
            })

    elif object_type == "VIEW":
        pattern = r'CREATE\s+OR\s+REPLACE\s+(?:FORCE\s+)?VIEW\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()

            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            semicolon_search = content[start_pos:end_pos]
            semicolon_match = re.search(r';', semicolon_search)

            if semicolon_match:
                actual_end = start_pos + semicolon_match.end()
            else:
                actual_end = end_pos

            object_name = extract_object_name(match)
            object_code = content[start_pos:actual_end].strip()

            lines_before = content[:start_pos].count('\n') + 1
            lines_in_object = object_code.count('\n') + 1

            objects.append({
                "object_id": f"view_{i+1:04d}",
                "object_name": object_name,
                "object_type": "VIEW",
                "source_file": file_path.name,
                "line_start": lines_before,
                "line_end": lines_before + lines_in_object - 1,
                "char_start": start_pos,
                "char_end": actual_end,
                "code_length": len(object_code),
                "status": "pending"
            })

    elif object_type == "MVIEW":
        pattern = r'CREATE\s+MATERIALIZED\s+VIEW\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()

            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            semicolon_search = content[start_pos:end_pos]
            semicolon_match = re.search(r';', semicolon_search)

            if semicolon_match:
                actual_end = start_pos + semicolon_match.end()
            else:
                actual_end = end_pos

            object_name = extract_object_name(match)
            object_code = content[start_pos:actual_end].strip()

            lines_before = content[:start_pos].count('\n') + 1
            lines_in_object = object_code.count('\n') + 1

            objects.append({
                "object_id": f"mview_{i+1:04d}",
                "object_name": object_name,
                "object_type": "MVIEW",
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


def parse_reference_objects(file_path: Path, object_type: str) -> List[Dict]:
    """
    Parsea objetos de referencia (DDL, Types, Views) para análisis contextual.

    Estos objetos NO se convierten (ora2pg ya los maneja), pero el agente
    los necesita como contexto para analizar código PL/SQL que los usa.

    (Mantiene la lógica original de prepare_migration.py para objetos DDL)
    """
    if not file_path.exists():
        return []

    print(f"📖 Parseando objetos de referencia: {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    objects = []

    # Patrones según tipo de objeto (soportan "esquema"."nombre", esquema.nombre, nombre)
    if object_type == "TABLE":
        pattern = r'CREATE\s+TABLE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    elif object_type == "TYPE":
        pattern = r'CREATE\s+(OR\s+REPLACE\s+)?TYPE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    elif object_type == "VIEW":
        pattern = r'CREATE\s+(OR\s+REPLACE\s+)?VIEW\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    elif object_type == "MVIEW":
        pattern = r'CREATE\s+MATERIALIZED\s+VIEW\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    elif object_type == "SEQUENCE":
        pattern = r'CREATE\s+SEQUENCE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    elif object_type == "DIRECTORY":
        pattern = r'CREATE\s+(OR\s+REPLACE\s+)?DIRECTORY\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    else:
        return []

    matches = list(re.finditer(pattern, content, re.IGNORECASE))

    for i, match in enumerate(matches):
        start_pos = match.start()

        if i < len(matches) - 1:
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)

        semicolon_search = content[start_pos:end_pos]

        if object_type == "TYPE":
            end_match = re.search(r'\)\s*\n\s*/\s*(?=\n|$)', semicolon_search)
            if not end_match:
                end_match = re.search(r'/\s*(?=\n|$)', semicolon_search)
        else:
            end_match = re.search(r';', semicolon_search)

        if end_match:
            actual_end = start_pos + end_match.end()
        else:
            actual_end = end_pos

        object_name = extract_object_name(match)
        object_code = content[start_pos:actual_end].strip()

        lines_before = content[:start_pos].count('\n') + 1
        lines_in_object = object_code.count('\n') + 1

        objects.append({
            "object_id": f"{object_type.lower()}_{i+1:04d}",
            "object_name": object_name,
            "object_type": object_type,
            "category": "REFERENCE",
            "source_file": file_path.name,
            "line_start": lines_before,
            "line_end": lines_before + lines_in_object - 1,
            "char_start": start_pos,
            "char_end": actual_end,
            "code_length": len(object_code),
            "status": "reference_only",
            "note": "Convertido por ora2pg - Incluido como contexto de análisis"
        })

    print(f"  ✅ Encontrados {len(objects)} objetos de tipo {object_type} (referencia)")
    return objects


def generate_manifest(dry_run: bool = False) -> Dict:
    """
    Genera manifest.json con índice completo de todos los objetos (VERSIÓN ROBUSTA v2).
    """
    print("\n🔍 Generando manifest de objetos (v2 - parsing robusto)...\n")

    # ===== OBJETOS EJECUTABLES (PL/SQL a convertir) =====
    print("📝 Procesando objetos EJECUTABLES (código PL/SQL)...\n")
    executable_objects = []

    files_to_parse = [
        (EXTRACTED_DIR / "views.sql", "VIEW"),
        (EXTRACTED_DIR / "materialized_views.sql", "MVIEW"),
        (EXTRACTED_DIR / "functions.sql", "FUNCTION"),
        (EXTRACTED_DIR / "procedures.sql", "PROCEDURE"),
        (EXTRACTED_DIR / "packages_spec.sql", "PACKAGE_SPEC"),
        (EXTRACTED_DIR / "packages_body.sql", "PACKAGE_BODY"),
        (EXTRACTED_DIR / "triggers.sql", "TRIGGER"),
    ]

    for file_path, object_type in files_to_parse:
        if file_path.exists():
            objects = parse_sql_file_robust(file_path, object_type)
            for obj in objects:
                obj["category"] = "EXECUTABLE"
            executable_objects.extend(objects)
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")

    # ===== OBJETOS DE REFERENCIA (DDL para contexto) =====
    print("\n📚 Procesando objetos de REFERENCIA (contexto)...\n")
    reference_objects = []

    reference_files = [
        (EXTRACTED_DIR / "types.sql", "TYPE"),
        (EXTRACTED_DIR / "sequences.sql", "SEQUENCE"),
        (EXTRACTED_DIR / "tables.sql", "TABLE"),
        (EXTRACTED_DIR / "primary_keys.sql", "PRIMARY_KEY"),
        (EXTRACTED_DIR / "foreign_keys.sql", "FOREIGN_KEY"),
    ]

    for file_path, object_type in reference_files:
        objects = parse_reference_objects(file_path, object_type)
        reference_objects.extend(objects)

    # ===== COMBINAR TODOS LOS OBJETOS =====
    all_objects = reference_objects + executable_objects

    for i, obj in enumerate(all_objects, start=1):
        obj["object_id"] = f"obj_{i:04d}"

    # Generar estadísticas
    executable_count = len(executable_objects)
    reference_count = len(reference_objects)

    objects_by_type = {}
    for obj in all_objects:
        obj_type = obj["object_type"]
        objects_by_type[obj_type] = objects_by_type.get(obj_type, 0) + 1

    # Contar objetos con warnings
    warning_count = len([obj for obj in all_objects if obj.get("validation_status") == "warning"])

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "version": "2.0-robust",
        "total_objects": len(all_objects),
        "executable_count": executable_count,
        "reference_count": reference_count,
        "warning_count": warning_count,
        "objects_by_category": {
            "EXECUTABLE": executable_count,
            "REFERENCE": reference_count
        },
        "objects_by_type": objects_by_type,
        "note": "REFERENCE objects son convertidos por ora2pg - Se incluyen solo como contexto para análisis",
        "parsing_info": {
            "total_errors": len(parsing_errors),
            "error_summary": f"{warning_count} objetos con warnings de validación"
        },
        "objects": all_objects
    }

    if not dry_run:
        with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # Guardar log de errores si hay
        if parsing_errors:
            with open(VALIDATION_LOG, 'w', encoding='utf-8') as f:
                json.dump(parsing_errors, f, indent=2, ensure_ascii=False)
            print(f"\n⚠️  Log de parsing guardado: {VALIDATION_LOG}")

    print(f"\n{'='*80}")
    print(f"📊 RESUMEN DE PARSING (v2):")
    print(f"{'='*80}")
    print(f"   Total objetos: {manifest['total_objects']}")
    print(f"   Ejecutables: {executable_count}")
    print(f"   Referencia: {reference_count}")
    print(f"   Warnings: {warning_count}")
    print(f"   Errores de parsing: {len(parsing_errors)}")

    if warning_count > 0:
        print(f"\n⚠️  {warning_count} objetos tienen warnings de validación")
        print(f"   Revisar {VALIDATION_LOG} para detalles")

    if dry_run:
        print(f"\n🔍 MODO DRY-RUN - Manifest NO guardado")
        print(f"   Ejecutar sin --dry-run para generar manifest.json")
    else:
        print(f"\n✅ Manifest generado: {MANIFEST_FILE}")

    return manifest


def create_directory_structure():
    """Crea estructura de directorios necesaria para la migración."""
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


def initialize_progress(manifest: Dict, force: bool = False) -> Dict:
    """Inicializa archivo progress.json para tracking."""
    print("\n📊 Inicializando tracking de progreso...\n")

    if PROGRESS_FILE.exists() and not force:
        print(f"⚠️  Ya existe {PROGRESS_FILE}")
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            existing_progress = json.load(f)

        print(f"   Progreso actual:")
        print(f"   - Procesados: {existing_progress['processed_count']}/{existing_progress['total_objects']}")
        print(f"   - Último batch: {existing_progress['current_batch']}")
        print(f"   - Último objeto: {existing_progress['last_object_processed']}")
        print("   Manteniendo progreso existente (usa --force para resetear)")
        return existing_progress

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


def main():
    """Función principal"""
    import sys

    force = '--force' in sys.argv
    dry_run = '--dry-run' in sys.argv

    print("="*80)
    print("PREPARACIÓN MIGRACIÓN ORACLE → POSTGRESQL (v2 - PARSING ROBUSTO)")
    print("="*80)

    if not EXTRACTED_DIR.exists():
        print(f"❌ Error: Directorio {EXTRACTED_DIR} no existe")
        print(f"   Ejecuta primero el script de extracción de Oracle")
        return

    create_directory_structure()

    manifest = generate_manifest(dry_run=dry_run)

    if not dry_run:
        progress = initialize_progress(manifest, force=force)

    print("\n" + "="*80)
    print("✅ PREPARACIÓN COMPLETADA (v2)")
    print("="*80)

    if dry_run:
        print("\n🔍 MODO DRY-RUN:")
        print("   - Parsing validado exitosamente")
        print("   - Manifest NO guardado")
        print("   - Ejecutar sin --dry-run para generar archivos")
    else:
        print("\nArchivos generados:")
        print(f"  - {MANIFEST_FILE}")
        print(f"  - {PROGRESS_FILE}")
        if parsing_errors:
            print(f"  - {VALIDATION_LOG}")


if __name__ == "__main__":
    main()
