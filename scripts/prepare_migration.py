#!/usr/bin/env python3
"""
Script de preparación para migración Oracle → PostgreSQL (VERSIÓN 3.0 - ORDEN CORRECTO)

MEJORAS EN ESTA VERSIÓN:
- Procesa objetos en el ORDEN DE COMPILACIÓN de Oracle
- Distingue correctamente objetos REFERENCIA vs EJECUTABLES
- VIEWS/MVIEWS en ambas categorías (referencia + ejecutables)
- Incluye JOBS y DIRECTORIES (opcionales)
- Manifest ordenado para análisis óptimo por el agente

ORDEN DE PROCESAMIENTO (Sigue compilación Oracle):
1. TYPES           → Tipos de datos base
2. SEQUENCES       → Secuencias para IDs
3. TABLES          → Tablas (usan types)
4. PRIMARY_KEYS    → Constraints PK (usan tables)
5. FOREIGN_KEYS    → Constraints FK (usan tables)
6. DIRECTORIES     → Directorios (para UTL_FILE) [OPCIONAL]
7. VIEWS           → Views (usan tables, types)
8. MVIEWS          → Materialized Views (usan views, tables)
9. FUNCTIONS       → Funciones (usan todo lo anterior)
10. PROCEDURES     → Procedures (usan functions)
11. PACKAGE_SPEC   → Package specs (definen interfaz)
12. PACKAGE_BODY   → Package bodies (implementan spec)
13. TRIGGERS       → Triggers (usan packages, functions)
14. JOBS           → Jobs (programación de ejecución) [OPCIONAL]

Uso:
    cd /path/to/phantomx-nexus
    python /path/to/oracle-postgres-migration/scripts/prepare_migration_v3.py [opciones]

Opciones:
    --dry-run           Solo valida parsing sin generar manifest
    --force             Sobrescribir progress.json existente
"""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Directorio base del proyecto
BASE_DIR = Path.cwd()
EXTRACTED_DIR = BASE_DIR / "sql" / "extracted"
OBJECTS_DIR = EXTRACTED_DIR / "objects"
MANIFEST_FILE = EXTRACTED_DIR / "manifest.json"
PROGRESS_FILE = EXTRACTED_DIR / "progress.json"
VALIDATION_LOG = EXTRACTED_DIR / "parsing_validation.log"

# Tracking de errores
parsing_errors = []


def log_parsing_error(error_msg: str, object_info: Dict = None):
    """Log de errores de parsing."""
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

    ESTRATEGIA (TODAS incluyen el delimitador / obligatorio):
    1. Buscar "END nombre_exacto; / " - Funciona cuando el END tiene el mismo nombre que el CREATE
    2. Para TRIGGER: Buscar "END cualquier_nombre; / " - Los triggers a menudo tienen nombres diferentes
    3. Para FUNCTION/PROCEDURE/TRIGGER: Buscar "END; / " sin nombre
    4. Para PACKAGE: Buscar último "END; / " en el rango
    5. FALLBACK: Usar end_pos (loguea warning)

    IMPORTANTE: El delimitador / es OBLIGATORIO y parte del código PL/SQL.

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

    # ESTRATEGIA 1: Buscar END con el nombre exacto del objeto + delimitador /
    # Formato: END nombre; + [comentario opcional] + nueva línea + [comentarios/líneas en blanco] + /
    # El delimitador / SÍ es parte del código PL/SQL (separa objetos)
    # Permite comentarios inline (--END PACKAGE BODY) y múltiples líneas en blanco/comentarios antes del /
    pattern_exact_with_slash = rf'END\s+{re.escape(object_name)}\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/'
    match_exact = re.search(pattern_exact_with_slash, search_content, re.IGNORECASE | re.DOTALL)

    if match_exact:
        actual_end = start_pos + match_exact.end()
        return actual_end, "exact_name_with_slash"

    # ESTRATEGIA 2: Para TRIGGER - Buscar END con cualquier nombre seguido de /
    # Los triggers a veces terminan con un nombre diferente al del CREATE
    # Ejemplo: CREATE TRIGGER AGE_T_X ... END AGE_T_LOG_Y; /
    if object_type == "TRIGGER":
        # Buscar END [cualquier_nombre]; seguido de nueva línea y /
        # Permite comentarios inline y múltiples líneas en blanco/comentarios antes del /
        pattern_trigger_end = r'END\s+\w+\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/\s*(?=\n|$)'
        match_trigger = re.search(pattern_trigger_end, search_content, re.IGNORECASE | re.DOTALL)

        if match_trigger:
            actual_end = start_pos + match_trigger.end()
            return actual_end, "trigger_end_with_slash"

    # ESTRATEGIA 3: Para FUNCTION/PROCEDURE/TRIGGER que pueden usar solo END;
    # Buscar END; seguido de / obligatorio (pero evitar END LOOP; END IF;)
    if object_type in ["FUNCTION", "PROCEDURE", "TRIGGER"]:
        # Buscar END; que NO sea precedido por LOOP o IF, seguido de /
        # Permite comentarios inline y múltiples líneas en blanco/comentarios antes del /
        pattern_end_only = r'(?<!LOOP\s)(?<!IF\s)END\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/'

        # Buscar todas las coincidencias y tomar la última (más probable que sea el END del objeto)
        matches = list(re.finditer(pattern_end_only, search_content, re.IGNORECASE | re.DOTALL))
        if matches:
            # Tomar el último match (más conservador)
            last_match = matches[-1]
            actual_end = start_pos + last_match.end()
            return actual_end, "end_only_with_slash"

    # ESTRATEGIA 4: Para PACKAGE sin nombre en END (raro pero posible)
    # Buscar END; seguido de / obligatorio al final del search_content
    if object_type in ["PACKAGE_BODY", "PACKAGE_SPEC"]:
        # Buscar END; cerca del final del rango de búsqueda con / obligatorio
        # Permite comentarios inline y múltiples líneas en blanco/comentarios antes del /
        pattern_end_near_end = r'END\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/'
        matches = list(re.finditer(pattern_end_near_end, search_content, re.IGNORECASE | re.DOTALL))
        if matches:
            # Tomar el último match
            last_match = matches[-1]
            actual_end = start_pos + last_match.end()
            return actual_end, "end_with_slash_near_end"

    # ESTRATEGIA 5: FALLBACK - Usar end_pos (menos preciso, loguear warning)
    log_parsing_error(
        f"No se encontró END exacto para {object_type} '{object_name}'",
        {"object_name": object_name, "object_type": object_type}
    )
    return end_pos, "fallback_end_pos"


def validate_extracted_code(code: str, object_name: str, object_type: str) -> Tuple[bool, str]:
    """
    Valida que el código extraído sea sintácticamente coherente.

    Verificaciones:
    1. Inicia con CREATE OR REPLACE [PACKAGE BODY|FUNCTION|PROCEDURE|TRIGGER|VIEW]
    2. Termina con END; o END nombre; OBLIGATORIAMENTE seguido de / (objetos PL/SQL)
    3. No contiene múltiples CREATE statements (indicaría parsing incorrecto)
    4. PACKAGE_BODY contiene al menos un PROCEDURE o FUNCTION

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

    # Verificación 2: Debe terminar con END; o END nombre; OBLIGATORIAMENTE seguido de /
    if object_type in ["FUNCTION", "PROCEDURE", "PACKAGE_SPEC", "PACKAGE_BODY", "TRIGGER"]:
        # El / es OBLIGATORIO para objetos PL/SQL
        # Permite comentarios inline y múltiples líneas en blanco/comentarios antes del /
        end_pattern = rf'(END\s+{re.escape(object_name)}\s*;|END\s*;)(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/$'
        if not re.search(end_pattern, code.strip(), re.IGNORECASE | re.DOTALL):
            return False, f"No termina con END {object_name}; / o END; /"
    # Verificación 3: No debe contener múltiples CREATE statements
    create_count = len(re.findall(
        r'\bCREATE\s+(OR\s+REPLACE\s+)?(PACKAGE|FUNCTION|PROCEDURE|TRIGGER|VIEW)',
        code, re.IGNORECASE
    ))
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

    """Parsea archivo SQL y extrae objetos individuales."""
    if not file_path.exists():
        print(f"⚠️  Archivo no encontrado: {file_path}")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    objects = []

    # Patrones de detección según tipo de objeto
    if object_type in ["FUNCTION", "PROCEDURE"]:
        pattern = r'CREATE\s+OR\s+REPLACE\s+' + object_type + r'\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

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
                "code_length": actual_end - start_pos,
                "status": "pending",
                "parsing_method": method,
                "validation_status": "valid" if is_valid else "warning"
            })

    elif object_type == "PACKAGE_SPEC":
        # Patrón mejorado que permite cláusulas como AUTHID CURRENT_USER antes de IS/AS
        # [^\n]*? permite cualquier contenido en la misma línea (no cruza líneas)
        pattern = r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))[^\n]*?\s+(IS|AS)'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

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
                "code_length": actual_end - start_pos,
                "status": "pending",
                "parsing_method": method,
                "validation_status": "valid" if is_valid else "warning"
            })

    elif object_type == "PACKAGE_BODY":
        # Patrón mejorado que permite cláusulas como AUTHID CURRENT_USER antes de IS/AS
        # [^\n]*? permite cualquier contenido en la misma línea (no cruza líneas)
        pattern = r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+BODY\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))[^\n]*?\s+(IS|AS)'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

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
                "code_length": actual_end - start_pos,
                "status": "pending",
                "parsing_method": method,
                "validation_status": "valid" if is_valid else "warning"
            })

    elif object_type == "TRIGGER":
        pattern = r'CREATE\s+OR\s+REPLACE\s+TRIGGER\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

            object_name = extract_object_name(match)
            actual_end, method = find_object_end_robust(
                content, start_pos, end_pos, object_name, object_type
            )

            object_code = content[start_pos:actual_end].strip()
            is_valid, error_msg = validate_extracted_code(object_code, object_name, object_type)

            if not is_valid:
                log_parsing_error(
                    f"TRIGGER '{object_name}': {error_msg}",
                    {"object_name": object_name, "object_type": object_type}
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
                "code_length": actual_end - start_pos,
                "status": "pending",
                "parsing_method": method,
                "validation_status": "valid" if is_valid else "warning"
            })

    elif object_type in ["VIEW", "MVIEW"]:
        if object_type == "VIEW":
            pattern = r'CREATE\s+OR\s+REPLACE\s+(?:FORCE\s+)?VIEW\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
        else:  # MVIEW
            pattern = r'CREATE\s+MATERIALIZED\s+VIEW\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'

        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

            semicolon_search = content[start_pos:end_pos]
            semicolon_match = re.search(r';', semicolon_search)

            actual_end = start_pos + semicolon_match.end() if semicolon_match else end_pos
            object_name = extract_object_name(match)
            object_code = content[start_pos:actual_end].strip()

            lines_before = content[:start_pos].count('\n') + 1
            lines_in_object = object_code.count('\n') + 1

            object_id_prefix = "view" if object_type == "VIEW" else "mview"

            objects.append({
                "object_id": f"{object_id_prefix}_{i+1:04d}",
                "object_name": object_name,
                "object_type": object_type,
                "source_file": file_path.name,
                "line_start": lines_before,
                "line_end": lines_before + lines_in_object - 1,
                "char_start": start_pos,
                "char_end": actual_end,
                "code_length": actual_end - start_pos,
                "status": "pending"
            })

    print(f"  ✅ Encontrados {len(objects)} objetos de tipo {object_type}")
    return objects


def parse_reference_objects(file_path: Path, object_type: str) -> List[Dict]:
    """Parsea objetos de referencia (DDL, Types, etc.)."""
    if not file_path.exists():
        return []

    print(f"📖 Parseando objetos de referencia: {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    objects = []

    # Patrones según tipo
    if object_type == "TABLE":
        pattern = r'CREATE\s+TABLE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    elif object_type == "TYPE":
        pattern = r'CREATE\s+(OR\s+REPLACE\s+)?TYPE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    elif object_type == "SEQUENCE":
        pattern = r'CREATE\s+SEQUENCE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    elif object_type == "DIRECTORY":
        pattern = r'CREATE\s+(OR\s+REPLACE\s+)?DIRECTORY\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))'
    elif object_type == "PRIMARY_KEY":
        # Patrón mejorado que captura tabla (grupos 1-3) Y constraint name completo (grupo 4)
        # Incluye caracteres especiales como $ en constraint names (ej: ADD_APER_CIER$P1)
        pattern = r'ALTER\s+TABLE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))[\s\S]*?ADD\s+CONSTRAINT\s+([\w$]+)[\s\S]*?PRIMARY\s+KEY'
    elif object_type == "FOREIGN_KEY":
        # Patrón mejorado que captura tabla (grupos 1-3) Y constraint name completo (grupo 4)
        # Incluye caracteres especiales como $ en constraint names (ej: ADD_ARC_PRO$F1)
        pattern = r'ALTER\s+TABLE\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))[\s\S]*?ADD\s+CONSTRAINT\s+([\w$]+)[\s\S]*?FOREIGN\s+KEY'
    elif object_type == "JOB":
        # Patrón corregido que captura desde BEGIN hasta el nombre del job
        # Formato completo: BEGIN + dbms_scheduler.create_job('"JOB_NAME"', ...)
        pattern = r'BEGIN\s+dbms_scheduler\.create_job\s*\(\s*\'?"([^"]+)"\'?'
    else:
        return []

    matches = list(re.finditer(pattern, content, re.IGNORECASE))

    for i, match in enumerate(matches):
        start_pos = match.start()
        end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

        semicolon_search = content[start_pos:end_pos]

        if object_type == "TYPE":
            end_match = re.search(r'\)\s*\n\s*/\s*(?=\n|$)', semicolon_search)
            if not end_match:
                end_match = re.search(r'/\s*(?=\n|$)', semicolon_search)
        elif object_type == "JOB":
            # Formato correcto: END; + nueva línea + / (obligatorio)
            end_match = re.search(r'END;\s*\n\s*/', semicolon_search)
        else:
            end_match = re.search(r';', semicolon_search)

        actual_end = start_pos + end_match.end() if end_match else end_pos

        # Extraer nombre del objeto según tipo
        if object_type == "JOB":
            # El patrón ya captura solo el nombre sin comillas: "ADD_JOB_NAME"
            object_name = match.group(1).upper()
            table_name = None
        elif object_type in ("PRIMARY_KEY", "FOREIGN_KEY"):
            # Para constraints: nombre del objeto = constraint name, NO tabla
            # Grupo 4 = constraint name (último grupo capturado)
            constraint_name = match.group(4)
            table_name = extract_object_name(match)  # Tabla (grupos 1-3)
            object_name = constraint_name.upper()
        else:
            object_name = extract_object_name(match)
            table_name = None

        object_code = content[start_pos:actual_end].strip()

        lines_before = content[:start_pos].count('\n') + 1
        lines_in_object = object_code.count('\n') + 1

        # Construir objeto base
        obj = {
            "object_id": f"{object_type.lower()}_{i+1:04d}",
            "object_name": object_name,
            "object_type": object_type,
            "category": "REFERENCE",
            "source_file": file_path.name,
            "line_start": lines_before,
            "line_end": lines_before + lines_in_object - 1,
            "char_start": start_pos,
            "char_end": actual_end,
            "code_length": actual_end - start_pos,  # Calcular desde posiciones, no desde object_code.strip()
            "status": "reference_only",
            "note": "Contexto para análisis - Conversión manejada por ora2pg"
        }

        # Agregar tabla propietaria para constraints (FK/PK)
        if table_name is not None:
            obj["table_name"] = table_name

        objects.append(obj)

    print(f"  ✅ Encontrados {len(objects)} objetos de tipo {object_type} (referencia)")
    return objects


def generate_manifest(dry_run: bool = False) -> Dict:
    """
    Genera manifest.json en ORDEN DE COMPILACIÓN de Oracle.

    Args:
        dry_run: Si es True, solo valida sin guardar archivos

    ORDEN CORRECTO (v3):
    1. TYPES          → Tipos base
    2. SEQUENCES      → Secuencias
    3. TABLES         → Tablas
    4. PRIMARY_KEYS   → PKs
    5. FOREIGN_KEYS   → FKs
    6. DIRECTORIES    → Directorios (opcional con --skip-directories)
    7. VIEWS          → Views (REFERENCIA + EJECUTABLE)
    8. MVIEWS         → MViews (REFERENCIA + EJECUTABLE)
    9. FUNCTIONS      → Funciones
    10. PROCEDURES    → Procedures
    11. PACKAGE_SPEC  → Package specs
    12. PACKAGE_BODY  → Package bodies
    13. TRIGGERS      → Triggers
    14. JOBS          → Jobs (opcional si no existe jobs.sql)
    """
    print("\n🔍 Generando manifest (v3 - ORDEN CORRECTO)...\n")

    # ===== PROCESAMIENTO EN ORDEN DE COMPILACIÓN =====
    print("📝 Procesando objetos en ORDEN DE COMPILACIÓN de Oracle...\n")

    all_objects = []

    # 1. TYPES (tipos base)
    print("1️⃣  TYPES (tipos de datos base)")
    types = parse_reference_objects(EXTRACTED_DIR / "types.sql", "TYPE")
    all_objects.extend(types)

    # 2. SEQUENCES
    print("\n2️⃣  SEQUENCES (secuencias)")
    sequences = parse_reference_objects(EXTRACTED_DIR / "sequences.sql", "SEQUENCE")
    all_objects.extend(sequences)

    # 3. TABLES
    print("\n3️⃣  TABLES (tablas)")
    tables = parse_reference_objects(EXTRACTED_DIR / "tables.sql", "TABLE")
    all_objects.extend(tables)

    # 4. PRIMARY KEYS
    print("\n4️⃣  PRIMARY KEYS")
    pks = parse_reference_objects(EXTRACTED_DIR / "primary_keys.sql", "PRIMARY_KEY")
    all_objects.extend(pks)

    # 5. FOREIGN KEYS
    print("\n5️⃣  FOREIGN KEYS")
    fks = parse_reference_objects(EXTRACTED_DIR / "foreign_keys.sql", "FOREIGN_KEY")
    all_objects.extend(fks)

    # 6. DIRECTORIES (opcional)
    print("\n6️⃣  DIRECTORIES (para UTL_FILE - contexto de análisis)")
    directories = parse_reference_objects(EXTRACTED_DIR / "directories.sql", "DIRECTORY")
    if directories:
        for d in directories:
            d["note"] = "Contexto para UTL_FILE - PostgreSQL no usa DIRECTORIES (migrar a S3)"
        all_objects.extend(directories)

    # 7. VIEWS (DOBLE PROPÓSITO: Referencia + Ejecutable)
    print("\n7️⃣  VIEWS (referencia + ejecutable)")
    views = parse_sql_file_robust(EXTRACTED_DIR / "views.sql", "VIEW")
    for view in views:
        view["category"] = "REFERENCE_AND_EXECUTABLE"
        view["note"] = "Usado como contexto Y requiere análisis de lógica"
    all_objects.extend(views)

    # 8. MATERIALIZED VIEWS (DOBLE PROPÓSITO)
    print("\n8️⃣  MATERIALIZED VIEWS (referencia + ejecutable)")
    mviews = parse_sql_file_robust(EXTRACTED_DIR / "materialized_views.sql", "MVIEW")
    for mview in mviews:
        mview["category"] = "REFERENCE_AND_EXECUTABLE"
        mview["note"] = "Usado como contexto Y requiere análisis de lógica"
    all_objects.extend(mviews)

    # 9. FUNCTIONS
    print("\n9️⃣  FUNCTIONS")
    functions = parse_sql_file_robust(EXTRACTED_DIR / "functions.sql", "FUNCTION")
    for func in functions:
        func["category"] = "EXECUTABLE"
    all_objects.extend(functions)

    # 10. PROCEDURES
    print("\n🔟 PROCEDURES")
    procedures = parse_sql_file_robust(EXTRACTED_DIR / "procedures.sql", "PROCEDURE")
    for proc in procedures:
        proc["category"] = "EXECUTABLE"
    all_objects.extend(procedures)

    # 11. PACKAGE SPECS
    print("\n1️⃣1️⃣  PACKAGE SPECS")
    pkg_specs = parse_sql_file_robust(EXTRACTED_DIR / "packages_spec.sql", "PACKAGE_SPEC")
    for spec in pkg_specs:
        spec["category"] = "EXECUTABLE"
    all_objects.extend(pkg_specs)

    # 12. PACKAGE BODIES
    print("\n1️⃣2️⃣  PACKAGE BODIES")
    pkg_bodies = parse_sql_file_robust(EXTRACTED_DIR / "packages_body.sql", "PACKAGE_BODY")
    for body in pkg_bodies:
        body["category"] = "EXECUTABLE"
    all_objects.extend(pkg_bodies)

    # 13. TRIGGERS
    print("\n1️⃣3️⃣  TRIGGERS")
    triggers = parse_sql_file_robust(EXTRACTED_DIR / "triggers.sql", "TRIGGER")
    for trigger in triggers:
        trigger["category"] = "EXECUTABLE"
    all_objects.extend(triggers)

    # 14. JOBS
    print("\n1️⃣4️⃣  JOBS (programación)")
    jobs = parse_reference_objects(EXTRACTED_DIR / "jobs.sql", "JOB")
    all_objects.extend(jobs)

    # Re-numerar object_ids en orden procesado
    for i, obj in enumerate(all_objects, start=1):
        obj["object_id"] = f"obj_{i:04d}"
        obj["processing_order"] = i

    # Estadísticas
    reference_count = len([o for o in all_objects if o.get("category") == "REFERENCE"])
    executable_count = len([o for o in all_objects if o.get("category") == "EXECUTABLE"])
    dual_count = len([o for o in all_objects if o.get("category") == "REFERENCE_AND_EXECUTABLE"])
    warning_count = len([o for o in all_objects if o.get("validation_status") == "warning"])

    objects_by_type = {}
    for obj in all_objects:
        obj_type = obj["object_type"]
        objects_by_type[obj_type] = objects_by_type.get(obj_type, 0) + 1

    # Processing order según configuración
    processing_order = [
            "TYPES", "SEQUENCES", "TABLES", "PRIMARY_KEYS", "FOREIGN_KEYS",
            "DIRECTORIES", "VIEWS", "MVIEWS", "FUNCTIONS", "PROCEDURES",
            "PACKAGE_SPEC", "PACKAGE_BODY", "TRIGGERS", "JOBS"
        ]
       

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "version": "3.0-ordered",
        "total_objects": len(all_objects),
        "reference_count": reference_count,
        "executable_count": executable_count,
        "dual_purpose_count": dual_count,
        "warning_count": warning_count,
        "objects_by_category": {
            "REFERENCE": reference_count,
            "EXECUTABLE": executable_count,
            "REFERENCE_AND_EXECUTABLE": dual_count
        },
        "objects_by_type": objects_by_type,
        "processing_order": processing_order,
        "note": "Objetos ordenados según compilación de Oracle para análisis óptimo",
        "parsing_info": {
            "total_errors": len(parsing_errors),
            "error_summary": f"{warning_count} objetos con warnings"
        },
        "objects": all_objects
    }

    if not dry_run:
        with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        if parsing_errors:
            with open(VALIDATION_LOG, 'w', encoding='utf-8') as f:
                json.dump(parsing_errors, f, indent=2, ensure_ascii=False)
            print(f"\n⚠️  Log de parsing: {VALIDATION_LOG}")

    print(f"\n{'='*80}")
    print(f"📊 RESUMEN (v3 - ORDEN CORRECTO):")
    print(f"{'='*80}")
    print(f"   Total objetos: {manifest['total_objects']}")
    print(f"   Referencia: {reference_count}")
    print(f"   Ejecutables: {executable_count}")
    print(f"   Dual (ref + exec): {dual_count}")
    print(f"   Warnings: {warning_count}")

    if dual_count > 0:
        print(f"\n📌 {dual_count} objetos VIEWS/MVIEWS tienen doble propósito:")
        print(f"   - Se usan como CONTEXTO (referencia)")
        print(f"   - Requieren ANÁLISIS de lógica (ejecutables)")

    if dry_run:
        print(f"\n🔍 MODO DRY-RUN - Manifest NO guardado")
    else:
        print(f"\n✅ Manifest generado: {MANIFEST_FILE}")

    return manifest


def create_directory_structure():
    """Crea estructura de directorios."""
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
        print(f"  ✅ Estructura ya existe")


def initialize_progress(manifest: Dict, force: bool = False) -> Dict:
    """Inicializa progress.json."""
    print("\n📊 Inicializando progreso...\n")

    if PROGRESS_FILE.exists() and not force:
        print(f"⚠️  Ya existe {PROGRESS_FILE}")
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            existing_progress = json.load(f)

        print(f"   Progreso: {existing_progress['processed_count']}/{existing_progress['total_objects']}")
        print(f"   Batch: {existing_progress['current_batch']}")
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
    print("PREPARACIÓN MIGRACIÓN ORACLE → POSTGRESQL (v3 - ORDEN CORRECTO)")
    print("="*80)

    if not EXTRACTED_DIR.exists():
        print(f"\n❌ Error: {EXTRACTED_DIR} no existe")
        return

    create_directory_structure()
    manifest = generate_manifest(dry_run=dry_run)

    if not dry_run:
        initialize_progress(manifest, force=force)

    print("\n" + "="*80)
    print("✅ PREPARACIÓN COMPLETADA (v3)")
    print("="*80)

    if dry_run:
        print("\n🔍 DRY-RUN: Parsing validado, manifest NO guardado")
    else:
        print(f"\nArchivos generados:")
        print(f"  - {MANIFEST_FILE}")
        print(f"  - {PROGRESS_FILE}")
        if parsing_errors:
            print(f"  - {VALIDATION_LOG}")


if __name__ == "__main__":
    main()
