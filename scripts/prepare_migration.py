#!/usr/bin/env python3
"""
Script de preparación para migración Oracle → PostgreSQL (VERSIÓN 7.6 - SIN LÍMITES)

MEJORAS V7.6:
- ✅ LÍMITE ELIMINADO: Captura TODAS las declaraciones del SPEC (no solo primeras 20)
- ✅ FIX CRÍTICO: RHH_K_VARIABLES ahora captura 78 variables (no truncadas a 20)
- ✅ TIPOS: Sin límite en types, constants, cursors, variables, exceptions
- ✅ PRECISIÓN: Manifest.json refleja exactamente el contenido del SPEC

MEJORAS V7.5:
- ✅ SPEC EN MANIFEST: Información del SPEC consolidada directamente en manifest.json
- ✅ NO ARCHIVOS EXTERNOS: Elimina necesidad de knowledge/packages/*.json
- ✅ EFICIENCIA: Agente solo lee manifest (no archivos adicionales)
- ✅ CAMPOS NUEVOS: spec_file, spec_line_start, spec_line_end, spec_has_declarations, spec_declarations

MEJORAS V7.4:
- ✅ NOMBRES CON COMILLAS: Soporte completo para nombres entre comillas dobles sin esquema
- ✅ TRIGGERS: Detecta correctamente 'TRIGGER "nombre"' (antes solo sin comillas)
- ✅ TODOS LOS TIPOS: Fix aplicado a FUNCTION, PROCEDURE, PACKAGE, VIEW, TABLE, etc.
- ✅ PARSING CORRECTO: Ahora detecta correctamente el fin de cada objeto

MEJORAS V7.3:
- ✅ JAVA STORED FUNCTIONS: Detecta funciones/procedures Java (LANGUAGE JAVA NAME '...')
- ✅ Sin END para Java: Busca ; después de NAME '...' en lugar de END
- ✅ Soporte completo: Aplica a FUNCTION y PROCEDURE con LANGUAGE JAVA

MEJORAS V7.2:
- ✅ FUNCIONES/PROCEDURES ANIDADOS: Filtra solo top-level (omite anidados en cuerpos)
- ✅ Eliminación de comentarios previa: Evita falsos positivos como "-- Procedure anidado"
- ✅ Contexto de parsing mejorado: Verifica CREATE OR REPLACE, inicio de archivo, o delimitador /
- ✅ Logging de objetos omitidos: Muestra funciones/procedures anidados filtrados para debugging

MEJORAS V7.1:
- ✅ PACKAGE_SPEC como METADATA: SPEC no se incluye en manifest (solo contexto para BODY)
- ✅ Declaraciones PÚBLICAS vs PRIVADAS: Distingue entre SPEC (público) y BODY (privado)
- ✅ Reducción de objetos: ~588 objetos menos en manifest (más eficiente)

MEJORAS V7.0:
- ✅ Soporte completo SPEC + BODY: Extrae declaraciones públicas del SPEC
- ✅ Estructura contexto mejorada: public_declarations + private_declarations

MEJORAS V4-V6:
- ✅ PARSING GRANULAR DE PACKAGES: Extrae cada PROCEDURE/FUNCTION individual
- ✅ CONTEXT SHARING: Genera archivos de contexto para packages
- ✅ CHUNKS INTELIGENTES: Divide packages grandes en chunks de 20 objects
- ✅ AGRUPACIÓN OPTIMIZADA: Procedures del mismo package agrupados secuencialmente
- ✅ Eliminación de comentarios: Evita falsos positivos en parsing
- ✅ Detección de Java functions: Clasifica y mapea correctamente
- ✅ Declaraciones globales completas: TYPES, CONSTANTS, CURSORS, VARIABLES, EXCEPTIONS

ORDEN DE PROCESAMIENTO (Optimizado para PostgreSQL):
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
11. PACKAGE_BODY   → Package bodies (SPEC incluido como metadata de contexto)
12. TRIGGERS       → Triggers (usan packages, functions)
13. JOBS           → Jobs (programación de ejecución) [OPCIONAL]

NOTA: PACKAGE_SPEC no aparece en el orden porque PostgreSQL no tiene concepto
de SPEC/BODY. El SPEC se procesa internamente para extraer declaraciones públicas
que se guardan en el archivo de contexto del BODY.

Uso:
    cd /path/to/phantomx-nexus
    python scripts/prepare_migration_v4.py [opciones]

Opciones:
    --dry-run           Solo valida parsing sin generar manifest
    --force             Sobrescribir progress.json existente
    --no-granular       Deshabilitar parsing granular de packages (usa v3 behavior)
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Directorio base del proyecto
BASE_DIR = Path.cwd()
EXTRACTED_DIR = BASE_DIR / "sql" / "extracted"
OBJECTS_DIR = EXTRACTED_DIR / "objects"
MANIFEST_FILE = EXTRACTED_DIR / "manifest.json"
PROGRESS_FILE = EXTRACTED_DIR / "progress.json"
VALIDATION_LOG = EXTRACTED_DIR / "parsing_validation.log"

# Nuevos directorios para v4.0
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
PACKAGES_CONTEXT_DIR = KNOWLEDGE_DIR / "packages"

# Tracking de errores
parsing_errors = []

# Configuración de chunks
CHUNK_SIZE = 20  # Máximo de procedures/functions por chunk


def log_parsing_error(error_msg: str, object_info: Dict = None):
    """Log de errores de parsing."""
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "error": error_msg,
        "object": object_info,
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
        g
        for g in groups
        if g is not None and not re.match(r"^(OR|REPLACE|IS|AS|\s)+$", g, re.IGNORECASE)
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
    content: str, start_pos: int, end_pos: int, object_name: str, object_type: str
) -> Tuple[int, str]:
    """
    Encuentra el fin del objeto de forma robusta usando el nombre EXACTO del objeto.

    ESTRATEGIA (TODAS incluyen el delimitador / obligatorio):
    0. Para JAVA STORED FUNCTIONS: Buscar "NAME '...' ; / " - Java functions NO tienen END
    1. Buscar "END nombre_exacto; / " - Funciona cuando el END tiene el mismo nombre que el CREATE
    2. Para TRIGGER: Buscar "END cualquier_nombre; / " - Los triggers a menudo tienen nombres diferentes
    3. Para FUNCTION/PROCEDURE/TRIGGER: Buscar "END; / " sin nombre
    4. Para PACKAGE: Buscar último "END; / " en el rango
    5. FALLBACK: Usar end_pos (loguea warning)

    IMPORTANTE: El delimitador / es OBLIGATORIO y parte del código PL/SQL.
    ESPECIAL: Java Stored Functions terminan con ; después de NAME '...' (no tienen END)

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

    # ESTRATEGIA 0: Para JAVA STORED FUNCTIONS/PROCEDURES (no tienen END)
    # Formato: FUNCTION nombre(...) RETURN tipo IS LANGUAGE JAVA NAME 'clase.metodo(...)' ;
    # Terminan con ; después de NAME '...' (no tienen BEGIN...END)
    if object_type in ["FUNCTION", "PROCEDURE"]:
        # Buscar LANGUAGE JAVA en las primeras 200 caracteres
        java_check = search_content[:200]
        if re.search(r"LANGUAGE\s+JAVA", java_check, re.IGNORECASE):
            # Es una Java Stored Function - buscar ; después de NAME '...'
            # Formato: NAME 'clase.metodo(...)' ; [newlines] / [newlines] SIGUIENTE_OBJETO
            # Captura todas las líneas en blanco después del / hasta el siguiente objeto
            java_pattern = (
                r"NAME\s+'[^']+'\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/[ \t]*(?=\n|\S|$)"
            )
            java_match = re.search(
                java_pattern, search_content, re.IGNORECASE | re.DOTALL
            )

            if java_match:
                actual_end = start_pos + java_match.end()
                return actual_end, "java_stored_function"
            else:
                # Java function sin delimitador / (buscar solo ;)
                java_pattern_no_slash = r"NAME\s+'[^']+'\s*;"
                java_match_no_slash = re.search(
                    java_pattern_no_slash, search_content, re.IGNORECASE
                )
                if java_match_no_slash:
                    actual_end = start_pos + java_match_no_slash.end()
                    return actual_end, "java_stored_function_no_slash"

    # ESTRATEGIA 1: Buscar END con el nombre exacto del objeto + delimitador /
    # Formato: END nombre; [newlines/comentarios] / [newlines] SIGUIENTE_OBJETO
    # El delimitador / SÍ es parte del código PL/SQL (separa objetos)
    # Captura: END nombre; + líneas en blanco/comentarios hasta / + el / + líneas en blanco hasta siguiente objeto
    pattern_exact_with_slash = rf"END\s+{re.escape(object_name)}\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/[ \t]*(?=\n|\S|$)"
    match_exact = re.search(
        pattern_exact_with_slash, search_content, re.IGNORECASE | re.DOTALL
    )

    if match_exact:
        actual_end = start_pos + match_exact.end()
        return actual_end, "exact_name_with_slash"

    # ESTRATEGIA 2: Para TRIGGER - Buscar END con cualquier nombre seguido de /
    # Los triggers a veces terminan con un nombre diferente al del CREATE
    # Ejemplo: CREATE TRIGGER AGE_T_X ... END AGE_T_LOG_Y; / [newlines] SIGUIENTE_TRIGGER
    if object_type == "TRIGGER":
        # Buscar END [cualquier_nombre]; [newlines/comentarios] / [newlines] SIGUIENTE_OBJETO
        # Captura todas las líneas en blanco después del / hasta el siguiente objeto
        pattern_trigger_end = (
            r"END\s+\w+\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/[ \t]*(?=\n|\S|$)"
        )
        match_trigger = re.search(
            pattern_trigger_end, search_content, re.IGNORECASE | re.DOTALL
        )

        if match_trigger:
            actual_end = start_pos + match_trigger.end()
            return actual_end, "trigger_end_with_slash"

    # ESTRATEGIA 3: Para FUNCTION/PROCEDURE/TRIGGER que pueden usar solo END;
    # Buscar END; seguido de / obligatorio (pero evitar END LOOP; END IF;)
    if object_type in ["FUNCTION", "PROCEDURE", "TRIGGER"]:
        # Buscar END; que NO sea seguido por IF o LOOP
        # Formato: END; [newlines/comentarios] / [newlines] SIGUIENTE_OBJETO
        # Usa lookahead negativo (?!\s+(?:IF|LOOP)\b) para evitar END IF; y END LOOP;
        # Captura todas las líneas en blanco después del / hasta el siguiente objeto
        pattern_end_only = r"END(?!\s+(?:IF|LOOP)\b)\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/[ \t]*(?=\n|\S|$)"

        # Buscar todas las coincidencias y tomar la PRIMERA (corresponde al final del objeto actual)
        matches = list(
            re.finditer(pattern_end_only, search_content, re.IGNORECASE | re.DOTALL)
        )
        if matches:
            # Tomar el PRIMER match (es el final del objeto actual, no de objetos siguientes)
            first_match = matches[0]
            actual_end = start_pos + first_match.end()
            return actual_end, "end_only_with_slash"

    # ESTRATEGIA 4: Para PACKAGE sin nombre en END (raro pero posible)
    # Buscar END; seguido de / obligatorio al final del search_content
    if object_type in ["PACKAGE_BODY", "PACKAGE_SPEC"]:
        # Buscar END; cerca del final del rango de búsqueda con / obligatorio
        # Formato: END; [newlines/comentarios] / [newlines] SIGUIENTE_OBJETO
        # Captura todas las líneas en blanco después del / hasta el siguiente objeto
        pattern_end_near_end = (
            r"END\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/[ \t]*(?=\n|\S|$)"
        )
        matches = list(
            re.finditer(pattern_end_near_end, search_content, re.IGNORECASE | re.DOTALL)
        )
        if matches:
            # Tomar el último match
            last_match = matches[-1]
            actual_end = start_pos + last_match.end()
            return actual_end, "end_with_slash_near_end"

    # ESTRATEGIA 5: FALLBACK - Usar end_pos (menos preciso, loguear warning)
    log_parsing_error(
        f"No se encontró END exacto para {object_type} '{object_name}'",
        {"object_name": object_name, "object_type": object_type},
    )
    return end_pos, "fallback_end_pos"


def validate_extracted_code(
    code: str, object_name: str, object_type: str
) -> Tuple[bool, str]:
    """
    Valida que el código extraído sea sintácticamente coherente.

    Verificaciones:
    1. Inicia con CREATE OR REPLACE o directamente con el tipo (FUNCTION, PROCEDURE, etc)
    2. Termina con END; o END nombre; OBLIGATORIAMENTE seguido de / (objetos PL/SQL estándar)
       - EXCEPCIÓN: Java Stored Functions terminan con NAME '...' ; /
    3. No contiene múltiples CREATE statements (indicaría parsing incorrecto)
    4. PACKAGE_BODY contiene al menos un PROCEDURE o FUNCTION

    Args:
        code: Código extraído
        object_name: Nombre del objeto
        object_type: Tipo de objeto

    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Verificación 1: Debe iniciar con CREATE o directamente con el tipo de objeto
    # Formato DBMS_METADATA: "CREATE OR REPLACE FUNCTION..."
    # Formato ALL_SOURCE: "FUNCTION..." o "procedure..." o "package body..."
    valid_start = re.match(
        r"^\s*(CREATE|FUNCTION|PROCEDURE|PACKAGE|TRIGGER)", code, re.IGNORECASE
    )
    if not valid_start:
        return False, "No inicia con CREATE o tipo de objeto válido"

    # MEJORA V7.3: Detectar Java Stored Functions (validación diferente)
    is_java_function = False
    if object_type in ["FUNCTION", "PROCEDURE"]:
        if re.search(r"LANGUAGE\s+JAVA", code, re.IGNORECASE):
            is_java_function = True

    # Verificación 2: Debe terminar con END; o END nombre; OBLIGATORIAMENTE seguido de /
    if object_type in [
        "FUNCTION",
        "PROCEDURE",
        "PACKAGE_SPEC",
        "PACKAGE_BODY",
        "TRIGGER",
    ]:
        if is_java_function:
            # Java functions terminan con NAME '...' ; / (no tienen END)
            java_end_pattern = r"NAME\s+'[^']+'\s*;(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/$"
            if not re.search(java_end_pattern, code.strip(), re.IGNORECASE | re.DOTALL):
                return False, f"Java function: No termina con NAME '...' ; /"
        else:
            # Objetos PL/SQL estándar terminan con END
            # El / es OBLIGATORIO para objetos PL/SQL
            # Permite comentarios inline y múltiples líneas en blanco/comentarios antes del /
            end_pattern = rf"(END\s+{re.escape(object_name)}\s*;|END\s*;)(?:--[^\n]*)?(?:[\s]|--[^\n]*\n)*/$"
            if not re.search(end_pattern, code.strip(), re.IGNORECASE | re.DOTALL):
                return False, f"No termina con END {object_name}; / o END; /"
    # Verificación 3: No debe contener múltiples CREATE statements o múltiples objetos
    # Para ALL_SOURCE: verificar que no haya múltiples "FUNCTION nombre" o "PROCEDURE nombre"
    # Para DBMS_METADATA: verificar que no haya múltiples "CREATE OR REPLACE"
    # MEJORA: Eliminar comentarios primero para evitar falsos positivos (ej: "-- Este procedure es...")
    code_no_comments, _ = remove_sql_comments(code)
    create_count = len(
        re.findall(
            r"\b(?:CREATE\s+(?:OR\s+REPLACE\s+)?)?(?:PACKAGE\s+BODY|PACKAGE|FUNCTION|PROCEDURE|TRIGGER)\s+\w+",
            code_no_comments,
            re.IGNORECASE,
        )
    )
    if create_count > 1:
        # Permitir múltiples si es un PACKAGE_BODY (contiene procedures/functions internos)
        if object_type != "PACKAGE_BODY":
            return (
                False,
                f"Contiene {create_count} definiciones de objetos (esperado: 1)",
            )

    # Verificación 4: Para PACKAGE_BODY, verificar que contiene procedimientos/funciones
    if object_type == "PACKAGE_BODY":
        proc_func_count = len(
            re.findall(r"\b(PROCEDURE|FUNCTION)\s+\w+", code_no_comments, re.IGNORECASE)
        )
        if proc_func_count == 0:
            return (
                False,
                "PACKAGE_BODY sin procedimientos/funciones (posible parsing incorrecto)",
            )

    return True, "OK"


def remove_sql_comments(code: str) -> Tuple[str, Dict[int, int]]:
    """
    Elimina comentarios SQL (-- y /* */) manteniendo el mapeo de posiciones.

    Args:
        code: Código SQL original

    Returns:
        Tupla (código sin comentarios, mapeo de posiciones offset_limpio -> offset_original)
    """
    # Mapeo de posiciones
    position_map = {}
    result = []
    i = 0
    result_pos = 0

    while i < len(code):
        # Comentario de bloque /* ... */
        if i < len(code) - 1 and code[i : i + 2] == "/*":
            # Buscar el cierre */
            end = code.find("*/", i + 2)
            if end != -1:
                # Reemplazar el comentario por espacios (mantener newlines para contar líneas)
                comment_content = code[i : end + 2]
                # Mantener newlines, reemplazar resto con espacios
                cleaned = "".join("\n" if c == "\n" else " " for c in comment_content)
                result.append(cleaned)
                position_map[result_pos] = i
                result_pos += len(cleaned)
                i = end + 2
                continue
            else:
                # Comentario sin cierre (error de sintaxis, pero lo manejamos)
                i += 2
                continue

        # Comentario de línea --
        if i < len(code) - 1 and code[i : i + 2] == "--":
            # Buscar el fin de línea
            end = code.find("\n", i)
            if end != -1:
                # Reemplazar comentario por espacios, mantener newline
                comment_length = end - i
                result.append(" " * comment_length + "\n")
                position_map[result_pos] = i
                result_pos += comment_length + 1
                i = end + 1
                continue
            else:
                # Comentario hasta el final del archivo
                result.append(" " * (len(code) - i))
                position_map[result_pos] = i
                break

        # Carácter normal
        result.append(code[i])
        position_map[result_pos] = i
        result_pos += 1
        i += 1

    return "".join(result), position_map


def parse_package_internals(
    package_code: str, package_name: str, package_id: str, package_line_start: int
) -> Tuple[List[Dict], Dict]:
    """
    Parsea PROCEDURES y FUNCTIONS dentro de un PACKAGE_BODY.

    Args:
        package_code: Código completo del package body
        package_name: Nombre del package
        package_id: ID del package en el manifest
        package_line_start: Línea donde inicia el package en el archivo fuente

    Returns:
        Tupla (lista de objects internos, contexto del package)
    """
    internal_objects = []

    # MEJORA V3: Eliminar comentarios antes de parsear
    cleaned_code, position_map = remove_sql_comments(package_code)

    # Patrón para encontrar PROCEDURE o FUNCTION (ya no necesita excluir comentarios manualmente)
    # Busca: PROCEDURE nombre o FUNCTION nombre (al inicio de línea o después de espacios)
    pattern = r"^[ \t]*(PROCEDURE|FUNCTION)\s+(\w+)"
    matches = list(re.finditer(pattern, cleaned_code, re.IGNORECASE | re.MULTILINE))

    print(f"    Parseando {len(matches)} procedures/functions en {package_name}...")

    for idx, match in enumerate(matches):
        obj_type = match.group(1).upper()  # PROCEDURE o FUNCTION
        obj_name = match.group(2).upper()

        # Encontrar el END de este procedure/function
        start_offset = match.start()

        # CASO ESPECIAL: Detectar Java Stored Functions
        # Formato: FUNCTION nombre (params) RETURN tipo (IS|AS) LANGUAGE JAVA NAME '...';
        # FIXED v7.4:
        #   - Aceptar tanto IS como AS (Oracle permite ambos)
        #   - Aceptar parámetros opcionales antes de RETURN (puede tener newlines)
        #   - Tipo puede tener paréntesis: VARCHAR2(100), NUMBER(10,2), etc.
        java_pattern = rf"FUNCTION\s+{re.escape(obj_name)}(?:\s*\([\s\S]*?\))?\s+RETURN\s+\w+(?:\([^)]*\))?\s+(IS|AS)\s+LANGUAGE\s+JAVA"
        java_match = re.search(
            java_pattern, cleaned_code[start_offset : start_offset + 300], re.IGNORECASE
        )

        if java_match:
            # Es una Java Stored Function (no tiene END, termina con ;)
            semicolon_pattern = r";"
            semicolon_match = re.search(
                semicolon_pattern, cleaned_code[start_offset : start_offset + 500]
            )

            if semicolon_match:
                end_offset = start_offset + semicolon_match.end()

                # Calcular líneas
                lines_before_in_package = package_code[:start_offset].count("\n")
                lines_in_object = package_code[start_offset:end_offset].count("\n") + 1
                absolute_line_start = package_line_start + lines_before_in_package
                absolute_line_end = absolute_line_start + lines_in_object - 1

                # Extraer el código Java
                obj_code = package_code[start_offset:end_offset].strip()

                # Parsear la llamada Java
                java_name_pattern = r"NAME\s+'([^']+)'"
                java_name_match = re.search(java_name_pattern, obj_code, re.IGNORECASE)
                java_call = java_name_match.group(1) if java_name_match else "UNKNOWN"

                internal_objects.append(
                    {
                        "object_id": f"{package_id}_{idx + 1:03d}",
                        "object_name": f"{package_name}.{obj_name}",
                        "object_type": "JAVA_FUNCTION",
                        "parent_package": package_name,
                        "parent_package_id": package_id,
                        "source_file": "packages_body.sql",
                        "line_start": absolute_line_start,
                        "line_end": absolute_line_end,
                        "code_length": len(obj_code),
                        "status": "pending",
                        "category": "EXECUTABLE",
                        "internal_to_package": True,
                        "procedure_index": idx + 1,
                        "total_in_package": len(matches),
                        "java_call": java_call,
                        "migration_note": "Java Stored Function - Requiere conversión especial a PostgreSQL",
                    }
                )
                continue  # Siguiente objeto

        # ESTRATEGIA 1: Buscar END con el nombre específico del procedure/function
        # Ejemplo: END dig_p_regla_agenda_new_prueba;
        # Buscar en código limpio (sin comentarios)
        end_pattern_named = rf"END\s+{re.escape(obj_name)}\s*;"
        end_matches_named = list(
            re.finditer(end_pattern_named, cleaned_code[start_offset:], re.IGNORECASE)
        )

        if end_matches_named:
            # Encontrado END con nombre específico (más confiable)
            end_offset = start_offset + end_matches_named[0].end()
        else:
            # ESTRATEGIA 2: Si no hay END con nombre, buscar el siguiente PROCEDURE/FUNCTION
            # y tomar el ÚLTIMO END; antes de ese punto
            next_proc_pattern = r"^[ \t]*(PROCEDURE|FUNCTION)\s+\w+"
            next_proc_matches = list(
                re.finditer(
                    next_proc_pattern,
                    cleaned_code[start_offset + 10 :],
                    re.IGNORECASE | re.MULTILINE,
                )
            )

            if next_proc_matches:
                # Hay otro procedure/function después
                search_limit = start_offset + 10 + next_proc_matches[0].start()
            else:
                # Es el último procedure/function del package
                search_limit = len(cleaned_code)

            # Buscar todos los END; en el rango (en código limpio)
            end_pattern_generic = r"END\s*;"
            end_matches_generic = list(
                re.finditer(
                    end_pattern_generic,
                    cleaned_code[start_offset:search_limit],
                    re.IGNORECASE,
                )
            )

            if not end_matches_generic:
                # No se encontró END, skip este objeto
                # Calcular línea absoluta para el mensaje de error
                lines_before = package_code[:start_offset].count("\n")
                absolute_line = package_line_start + lines_before

                log_parsing_error(
                    f"No se encontró END para {obj_type} '{obj_name}' en package {package_name} (línea ~{absolute_line})",
                    {
                        "object_name": obj_name,
                        "object_type": obj_type,
                        "package": package_name,
                        "line_start": absolute_line,
                        "offset_in_package": start_offset,
                    },
                )
                continue

            # Tomar el ÚLTIMO END; encontrado (más probable que sea el del procedure/function)
            end_offset = start_offset + end_matches_generic[-1].end()

        # Calcular líneas
        lines_before_in_package = package_code[:start_offset].count("\n")
        lines_in_object = package_code[start_offset:end_offset].count("\n") + 1
        absolute_line_start = package_line_start + lines_before_in_package
        absolute_line_end = absolute_line_start + lines_in_object - 1

        # Código del objeto
        obj_code = package_code[start_offset:end_offset].strip()
        code_length = len(obj_code)

        internal_objects.append(
            {
                "object_id": f"{package_id}_{idx + 1:03d}",
                "object_name": f"{package_name}.{obj_name}",
                "object_type": obj_type,
                "parent_package": package_name,
                "parent_package_id": package_id,
                "source_file": "packages_body.sql",  # Siempre viene de packages_body.sql
                "line_start": absolute_line_start,
                "line_end": absolute_line_end,
                "code_length": code_length,
                "status": "pending",
                "category": "EXECUTABLE",
                "internal_to_package": True,
                "procedure_index": idx + 1,
                "total_in_package": len(matches),
            }
        )

    return internal_objects


def create_package_context(
    package_code: str, package_name: str, package_id: str
) -> Dict:
    """
    Extrae metadata y contexto de un package para compartir con procedures/functions.

    Args:
        package_code: Código completo del package
        package_name: Nombre del package
        package_id: ID del package

    Returns:
        Diccionario con contexto del package
    """
    context = {
        "package_name": package_name,
        "package_id": package_id,
        "package_variables": [],
        "package_constants": [],
        "package_types": [],
        "package_cursors": [],
        "package_exceptions": [],
        "total_procedures": 0,
        "total_functions": 0,
    }

    # MEJORA V6: Extraer TODAS las declaraciones globales del package
    # Sección global = entre "PACKAGE BODY ... IS" y el primer "PROCEDURE/FUNCTION"

    # Eliminar comentarios primero
    cleaned_code_for_vars, _ = remove_sql_comments(package_code)

    # Encontrar el primer PROCEDURE o FUNCTION
    first_proc_pattern = r"^[ \t]*(PROCEDURE|FUNCTION)\s+\w+"
    first_proc_match = re.search(
        first_proc_pattern, cleaned_code_for_vars, re.IGNORECASE | re.MULTILINE
    )

    if first_proc_match:
        # Sección global = desde el inicio hasta el primer PROCEDURE/FUNCTION
        global_section = cleaned_code_for_vars[: first_proc_match.start()]
    else:
        # No hay procedures/functions (raro, pero manejar)
        global_section = cleaned_code_for_vars[:10000]

    # 1. TYPES personalizados (TYPE nombre IS ...)
    type_pattern = r"^\s*TYPE\s+(\w+)\s+IS\s+([^;]+);"
    types = re.findall(type_pattern, global_section, re.IGNORECASE | re.MULTILINE)
    context["package_types"] = [
        {"name": t[0], "definition": t[1][:100]}  # Primeros 100 chars de definición
        for t in types
    ]  # No limit - v7.6

    # 2. CONSTANTS (nombre CONSTANT tipo := valor;)
    const_pattern = r"^\s*(\w+)\s+CONSTANT\s+(\w+(?:\([^\)]*\))?)\s*:=\s*([^;]+);"
    constants = re.findall(const_pattern, global_section, re.IGNORECASE | re.MULTILINE)
    context["package_constants"] = [
        {"name": c[0], "type": c[1], "value": c[2][:50]}  # Primeros 50 chars del valor
        for c in constants
    ]  # No limit - v7.6

    # 3. CURSORS (CURSOR nombre IS ...)
    cursor_pattern = r"^\s*CURSOR\s+(\w+)(?:\s*\([^\)]*\))?\s+IS\s+([^;]+);"
    cursors = re.findall(
        cursor_pattern, global_section, re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    context["package_cursors"] = [
        {"name": cur[0], "query": cur[1][:100]}  # Primeros 100 chars de query
        for cur in cursors
    ]  # No limit - v7.6

    # 4. VARIABLES (nombre tipo [:= valor];)
    # Incluir tipos estándar Y tipos personalizados
    var_pattern = r"^\s*(\w+)\s+(\w+(?:\([^\)]*\))?)\s*(?::=\s*[^;]+)?;"
    all_vars = re.findall(var_pattern, global_section, re.IGNORECASE | re.MULTILINE)

    # Filtrar: excluir palabras reservadas y ya capturadas (TYPES, CONSTANTS, CURSORS)
    type_names = {t[0].upper() for t in types}
    const_names = {c[0].upper() for c in constants}
    cursor_names = {cur[0].upper() for cur in cursors}
    reserved_words = {
        "TYPE",
        "CURSOR",
        "EXCEPTION",
        "PRAGMA",
        "PROCEDURE",
        "FUNCTION",
        "BEGIN",
        "END",
        "IS",
        "AS",
        "CONSTANT",
    }

    filtered_vars = [
        {"name": v[0], "type": v[1]}
        for v in all_vars
        if v[0].upper() not in reserved_words
        and v[0].upper() not in type_names
        and v[0].upper() not in const_names
        and v[0].upper() not in cursor_names
    ]  # No limit - v7.6

    context["package_variables"] = filtered_vars

    # 5. EXCEPCIONES personalizadas (nombre EXCEPTION;)
    exception_pattern = r"^\s*(\w+)\s+EXCEPTION;"
    exceptions = re.findall(
        exception_pattern, global_section, re.IGNORECASE | re.MULTILINE
    )
    context["package_exceptions"] = [
        {"name": exc} for exc in exceptions
    ]  # No limit - v7.6

    # MEJORA V4: Contar procedures y functions SIN comentarios
    # Eliminar comentarios antes de contar (igual que parse_package_internals)
    cleaned_code, _ = remove_sql_comments(package_code)

    # Usar el mismo pattern que parse_package_internals() para consistencia
    # Pattern: al inicio de línea o después de espacios (no dentro de comentarios)
    proc_pattern = r"^[ \t]*PROCEDURE\s+\w+"
    func_pattern = r"^[ \t]*FUNCTION\s+\w+"

    context["total_procedures"] = len(
        re.findall(proc_pattern, cleaned_code, re.IGNORECASE | re.MULTILINE)
    )
    context["total_functions"] = len(
        re.findall(func_pattern, cleaned_code, re.IGNORECASE | re.MULTILINE)
    )

    return context


def extract_global_declarations(code: str, _code_type: str = "body") -> Dict:
    """
    Extrae declaraciones globales de código Oracle (SPEC o BODY).

    VERSIÓN 7.0: Función reutilizable para extraer declaraciones de SPEC o BODY

    Args:
        code: Código SQL del SPEC o BODY
        _code_type: "spec" o "body" (reservado para logging futuro)

    Returns:
        Diccionario con 5 categorías de declaraciones:
        - types: TYPE nombre IS definición;
        - constants: nombre CONSTANT tipo := valor;
        - cursors: CURSOR nombre IS query;
        - variables: nombre tipo [:= valor];
        - exceptions: nombre EXCEPTION;
    """
    declarations = {
        "types": [],
        "constants": [],
        "cursors": [],
        "variables": [],
        "exceptions": [],
    }

    # Eliminar comentarios primero
    cleaned_code, _ = remove_sql_comments(code)

    # Encontrar el primer PROCEDURE o FUNCTION
    first_proc_pattern = r"^[ \t]*(PROCEDURE|FUNCTION)\s+\w+"
    first_proc_match = re.search(
        first_proc_pattern, cleaned_code, re.IGNORECASE | re.MULTILINE
    )

    if first_proc_match:
        # Sección global = desde el inicio hasta el primer PROCEDURE/FUNCTION
        global_section = cleaned_code[: first_proc_match.start()]
    else:
        # No hay procedures/functions (puede pasar en SPEC), usar todo el código
        global_section = cleaned_code

    # 1. TYPES personalizados (TYPE nombre IS ...)
    type_pattern = r"^\s*TYPE\s+(\w+)\s+IS\s+([^;]+);"
    types = re.findall(type_pattern, global_section, re.IGNORECASE | re.MULTILINE)
    declarations["types"] = [
        {"name": t[0], "definition": t[1][:100]}  # Primeros 100 chars
        for t in types
    ]  # No limit - capture all types

    # 2. CONSTANTS (nombre CONSTANT tipo := valor;)
    const_pattern = r"^\s*(\w+)\s+CONSTANT\s+(\w+(?:\([^\)]*\))?)\s*:=\s*([^;]+);"
    constants = re.findall(const_pattern, global_section, re.IGNORECASE | re.MULTILINE)
    declarations["constants"] = [
        {"name": c[0], "type": c[1], "value": c[2][:50]}  # Primeros 50 chars
        for c in constants
    ]  # No limit - capture all constants

    # 3. CURSORS (CURSOR nombre IS ...)
    cursor_pattern = r"^\s*CURSOR\s+(\w+)(?:\s*\([^\)]*\))?\s+IS\s+([^;]+);"
    cursors = re.findall(
        cursor_pattern, global_section, re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    declarations["cursors"] = [
        {"name": cur[0], "query": cur[1][:100]}  # Primeros 100 chars
        for cur in cursors
    ]  # No limit - capture all cursors

    # 4. VARIABLES (nombre tipo [:= valor];)
    var_pattern = r"^\s*(\w+)\s+(\w+(?:\([^\)]*\))?)\s*(?::=\s*[^;]+)?;"
    all_vars = re.findall(var_pattern, global_section, re.IGNORECASE | re.MULTILINE)

    # Filtrar: excluir palabras reservadas y ya capturadas
    type_names = {t[0].upper() for t in types}
    const_names = {c[0].upper() for c in constants}
    cursor_names = {cur[0].upper() for cur in cursors}
    reserved_words = {
        "TYPE",
        "CURSOR",
        "EXCEPTION",
        "PRAGMA",
        "PROCEDURE",
        "FUNCTION",
        "BEGIN",
        "END",
        "IS",
        "AS",
        "CONSTANT",
        "PACKAGE",
        "BODY",
    }

    filtered_vars = [
        {"name": v[0], "type": v[1]}
        for v in all_vars
        if v[0].upper() not in reserved_words
        and v[0].upper() not in type_names
        and v[0].upper() not in const_names
        and v[0].upper() not in cursor_names
    ]  # No limit - capture all variables

    declarations["variables"] = filtered_vars

    # 5. EXCEPCIONES personalizadas (nombre EXCEPTION;)
    exception_pattern = r"^\s*(\w+)\s+EXCEPTION;"
    exceptions = re.findall(
        exception_pattern, global_section, re.IGNORECASE | re.MULTILINE
    )
    declarations["exceptions"] = [
        {"name": exc} for exc in exceptions
    ]  # No limit - capture all exceptions

    return declarations


def extract_package_spec_code(package_name: str, spec_content: str) -> Optional[str]:
    """
    Extrae el código del PACKAGE SPEC dado el nombre del package.

    VERSIÓN 7.5: Patrón flexible para packages con o sin CREATE OR REPLACE

    Args:
        package_name: Nombre del package a buscar
        spec_content: Contenido completo del archivo packages_spec.sql

    Returns:
        Código del SPEC o None si no se encuentra
    """
    # Buscar el SPEC del package (con o sin CREATE OR REPLACE)
    # FIXED v7.5: CREATE OR REPLACE es opcional
    pattern = r"(?:CREATE\s+OR\s+REPLACE\s+)?PACKAGE\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)[^\n]*?\s+(IS|AS)"
    matches = list(re.finditer(pattern, spec_content, re.IGNORECASE))

    for i, match in enumerate(matches):
        # Extraer nombre del package
        groups = match.groups()
        relevant_groups = [
            g
            for g in groups
            if g is not None
            and not re.match(r"^(OR|REPLACE|IS|AS|\s)+$", g, re.IGNORECASE)
        ]

        if len(relevant_groups) >= 2:
            found_name = relevant_groups[1].upper()
        else:
            found_name = relevant_groups[-1].upper()

        # Si es el package que buscamos, extraer su código
        if found_name == package_name.upper():
            start_pos = match.start()

            # Encontrar el final del SPEC
            if i + 1 < len(matches):
                search_end = matches[i + 1].start()
            else:
                search_end = len(spec_content)

            search_content = spec_content[start_pos:search_end]
            end_pattern = rf"END\s+{re.escape(package_name)}\s*;"
            end_match = re.search(end_pattern, search_content, re.IGNORECASE)

            if end_match:
                actual_end = start_pos + end_match.end()
            else:
                actual_end = search_end

            return spec_content[start_pos:actual_end].strip()

    return None


def extract_package_spec_with_lines(
    package_name: str, spec_content: str
) -> Optional[Tuple[str, int, int]]:
    """
    Extrae el código del PACKAGE SPEC y sus líneas de inicio/fin.

    VERSIÓN 7.5: Nueva función para consolidar SPEC en manifest.json

    Args:
        package_name: Nombre del package a buscar
        spec_content: Contenido completo del archivo packages_spec.sql

    Returns:
        Tupla (código, line_start, line_end) o None si no se encuentra
    """
    # Buscar el SPEC del package (con o sin CREATE OR REPLACE)
    # Formato 1: CREATE OR REPLACE PACKAGE nombre IS/AS
    # Formato 2: PACKAGE nombre IS/AS (sin CREATE OR REPLACE)
    # Formato 3: package nombre is/as (minúsculas)
    pattern = r"(?:CREATE\s+OR\s+REPLACE\s+)?PACKAGE\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)[^\n]*?\s+(IS|AS)"
    matches = list(re.finditer(pattern, spec_content, re.IGNORECASE))

    for i, match in enumerate(matches):
        # Extraer nombre del package
        groups = match.groups()
        relevant_groups = [
            g
            for g in groups
            if g is not None
            and not re.match(r"^(OR|REPLACE|IS|AS|\s)+$", g, re.IGNORECASE)
        ]

        if len(relevant_groups) >= 2:
            found_name = relevant_groups[1].upper()
        else:
            found_name = relevant_groups[-1].upper()

        # Si es el package que buscamos, extraer su código y líneas
        if found_name == package_name.upper():
            start_pos = match.start()

            # Encontrar el final del SPEC
            if i + 1 < len(matches):
                search_end = matches[i + 1].start()
            else:
                search_end = len(spec_content)

            search_content = spec_content[start_pos:search_end]
            end_pattern = rf"END\s+{re.escape(package_name)}\s*;"
            end_match = re.search(end_pattern, search_content, re.IGNORECASE)

            if end_match:
                actual_end = start_pos + end_match.end()
            else:
                actual_end = search_end

            # Calcular líneas
            line_start = spec_content[:start_pos].count("\n") + 1
            line_end = spec_content[:actual_end].count("\n") + 1

            spec_code = spec_content[start_pos:actual_end].strip()

            return (spec_code, line_start, line_end)

    return None


def create_package_context_v7(
    package_name: str, package_id: str, body_code: str, spec_code: Optional[str] = None
) -> Dict:
    """
    Extrae metadata y contexto de un package (SPEC + BODY).

    VERSIÓN 7.0: Distingue entre declaraciones PÚBLICAS (SPEC) y PRIVADAS (BODY)

    Args:
        package_name: Nombre del package
        package_id: ID del package
        body_code: Código completo del PACKAGE BODY
        spec_code: Código completo del PACKAGE SPEC (opcional)

    Returns:
        Diccionario con contexto del package distinguiendo público vs privado
    """
    context = {
        "package_name": package_name,
        "package_id": package_id,
        "version": "7.0",  # Indica que usa nueva estructura
        "has_public_declarations": spec_code is not None,
        "public_declarations": {
            "types": [],
            "constants": [],
            "cursors": [],
            "variables": [],
            "exceptions": [],
        },
        "private_declarations": {
            "types": [],
            "constants": [],
            "cursors": [],
            "variables": [],
            "exceptions": [],
        },
        "total_procedures": 0,
        "total_functions": 0,
    }

    # Extraer declaraciones PÚBLICAS del SPEC (si existe)
    if spec_code:
        context["public_declarations"] = extract_global_declarations(spec_code, "spec")

    # Extraer declaraciones PRIVADAS del BODY
    context["private_declarations"] = extract_global_declarations(body_code, "body")

    # Contar procedures y functions en el BODY
    cleaned_code, _ = remove_sql_comments(body_code)
    proc_pattern = r"^[ \t]*PROCEDURE\s+\w+"
    func_pattern = r"^[ \t]*FUNCTION\s+\w+"

    context["total_procedures"] = len(
        re.findall(proc_pattern, cleaned_code, re.IGNORECASE | re.MULTILINE)
    )
    context["total_functions"] = len(
        re.findall(func_pattern, cleaned_code, re.IGNORECASE | re.MULTILINE)
    )

    return context


def save_package_context(context: Dict, package_id: str):
    """Guarda el contexto del package en un archivo JSON."""
    PACKAGES_CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    context_file = PACKAGES_CONTEXT_DIR / f"{package_id}_context.json"

    with open(context_file, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)


def parse_sql_file_robust(
    file_path: Path, object_type: str, spec_content: Optional[str] = None
) -> List[Dict]:
    """
    Parsea archivo SQL grande y extrae objetos individuales (VERSIÓN ROBUSTA v2).

    MEJORAS V7.0:
    - Acepta spec_content para parsear declaraciones públicas de packages
    - Usa create_package_context_v7() para distinguir público/privado

    MEJORAS V2:
    - Usa find_object_end_robust() para encontrar el END correcto
    - Valida el código extraído
    - Loguea objetos problemáticos

    Args:
        file_path: Ruta al archivo SQL
        object_type: Tipo de objeto (FUNCTION, PROCEDURE, PACKAGE, etc.)
        spec_content: Contenido completo de packages_spec.sql (solo para PACKAGE_BODY)

    Returns:
        Lista de diccionarios con metadata de cada objeto
    """
    print(f"📖 Parseando {file_path.name}...")

    """Parsea archivo SQL y extrae objetos individuales."""
    if not file_path.exists():
        print(f"⚠️  Archivo no encontrado: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    objects = []

    # Patrones de detección según tipo de objeto
    if object_type in ["FUNCTION", "PROCEDURE"]:
        # MEJORA V7.2: Eliminar comentarios antes de parsear para evitar falsos positivos
        # Ejemplo: "-- Procedure anidado nivel 1" no debe ser capturado como procedure
        cleaned_content, position_map = remove_sql_comments(content)

        # Pattern flexible: acepta con o sin CREATE OR REPLACE
        # Formato ALL_SOURCE: "FUNCTION nombre" o "procedure              nombre" o con comillas
        # Formato DBMS_METADATA: "CREATE OR REPLACE FUNCTION nombre"
        # FIXED v7.4: Añadido soporte para nombres con comillas dobles sin esquema
        pattern = (
            r"(?:CREATE\s+OR\s+REPLACE\s+)?"
            + object_type
            + r"\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)"
        )
        all_matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))

        # MEJORA V4.1: Filtrar solo funciones/procedimientos TOP-LEVEL (no anidados)
        # Las funciones anidadas tienen FUNCTION dentro del cuerpo de otra función
        # Las funciones top-level tienen uno de estos contextos:
        # 1. Inicio del archivo (solo whitespace antes)
        # 2. Precedidas por CREATE OR REPLACE
        # 3. Precedidas por delimitador / en línea anterior (separa objetos en ALL_SOURCE)

        matches = []
        for match in all_matches:
            start_pos = match.start()

            # Obtener contexto antes del match (últimos 200 caracteres)
            # Usar cleaned_content para detectar, pero content para líneas
            context_start = max(0, start_pos - 200)
            context_before = cleaned_content[context_start:start_pos]

            # Verificar si es top-level
            is_top_level = False

            # CASO 1: Tiene CREATE OR REPLACE antes
            if re.search(
                r"CREATE\s+OR\s+REPLACE\s*$", context_before, re.IGNORECASE | re.DOTALL
            ):
                is_top_level = True

            # CASO 2: Al inicio del archivo (solo whitespace/comentarios antes)
            elif start_pos < 100 and re.match(
                r"^[\s\n\r]*$", cleaned_content[:start_pos]
            ):
                is_top_level = True

            # CASO 3: Precedido por delimitador / (separa objetos)
            # Buscar / en línea propia antes del FUNCTION/PROCEDURE
            # Formato: END nombre; / \n\n FUNCTION siguiente
            elif re.search(r"/\s*\n[\s\n]*$", context_before, re.DOTALL):
                is_top_level = True

            if is_top_level:
                matches.append(match)
            else:
                # Loguear funciones anidadas omitidas (para debugging)
                nested_name = extract_object_name(match)
                # Usar content original para calcular líneas (limpio tiene mismas posiciones)
                line_num = content[:start_pos].count("\n") + 1
                print(
                    f"      🔸 Omitida función anidada: {nested_name} (línea {line_num})"
                )

        print(
            f"      📊 Encontrados {len(all_matches)} matches totales, {len(matches)} top-level (filtrados {len(all_matches) - len(matches)} anidados)"
        )

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
            is_valid, error_msg = validate_extracted_code(
                object_code, object_name, object_type
            )

            if not is_valid:
                log_parsing_error(
                    f"{object_type} '{object_name}': {error_msg} (método: {method})",
                    {
                        "object_name": object_name,
                        "object_type": object_type,
                        "line_start": content[:start_pos].count("\n") + 1,
                        "method": method,
                        "validation_error": error_msg,
                    },
                )

            # Calcular líneas
            lines_before = content[:start_pos].count("\n") + 1
            lines_in_object = object_code.count("\n") + 1

            # Construir objeto base
            obj = {
                "object_id": f"{object_type.lower()}_{i + 1:04d}",
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
                "validation_status": "valid" if is_valid else "warning",
            }

            # MEJORA V7.3: Detectar y marcar Java Stored Functions
            if method in ["java_stored_function", "java_stored_function_no_slash"]:
                # Extraer la llamada Java del código
                java_name_pattern = r"NAME\s+'([^']+)'"
                java_name_match = re.search(
                    java_name_pattern, object_code, re.IGNORECASE
                )
                java_call = java_name_match.group(1) if java_name_match else "UNKNOWN"

                obj["is_java_function"] = True
                obj["java_call"] = java_call
                obj["migration_note"] = (
                    "Java Stored Function - Requiere conversión especial a PostgreSQL"
                )
                obj["category"] = "EXECUTABLE"

            objects.append(obj)

    elif object_type == "PACKAGE_SPEC":
        # MEJORA: Eliminar comentarios antes de parsear para evitar falsos positivos
        # Ejemplo: "-- Este PACKAGE es importante IS necesario" no debe ser capturado
        cleaned_content, _ = remove_sql_comments(content)

        # Patrón flexible: acepta con o sin CREATE OR REPLACE
        # Formato ALL_SOURCE: "package nombre IS" o "PACKAGE nombre AS" o con comillas
        # Formato DBMS_METADATA: "CREATE OR REPLACE PACKAGE nombre IS"
        # FIXED v7.4: Añadido soporte para nombres con comillas dobles sin esquema
        pattern = r"(?:CREATE\s+OR\s+REPLACE\s+)?PACKAGE\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)[^\n]*?\s+(IS|AS)"
        matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

            object_name = extract_object_name(match)
            actual_end, method = find_object_end_robust(
                content, start_pos, end_pos, object_name, object_type
            )

            object_code = content[start_pos:actual_end].strip()
            is_valid, error_msg = validate_extracted_code(
                object_code, object_name, object_type
            )

            if not is_valid:
                log_parsing_error(
                    f"PACKAGE_SPEC '{object_name}': {error_msg} (método: {method})",
                    {
                        "object_name": object_name,
                        "object_type": object_type,
                        "line_start": content[:start_pos].count("\n") + 1,
                        "method": method,
                        "validation_error": error_msg,
                    },
                )

            lines_before = content[:start_pos].count("\n") + 1
            lines_in_object = object_code.count("\n") + 1

            objects.append(
                {
                    "object_id": f"pkg_spec_{i + 1:04d}",
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
                    "validation_status": "valid" if is_valid else "warning",
                }
            )

    elif object_type == "PACKAGE_BODY":
        # MEJORA: Eliminar comentarios antes de parsear para evitar falsos positivos
        # Ejemplo: "-- Este PACKAGE BODY es crítico IS fundamental" no debe ser capturado
        cleaned_content, _ = remove_sql_comments(content)

        # VERSIÓN 4.0: Parsing granular de packages
        # Patrón flexible: acepta con o sin CREATE OR REPLACE
        # Formato ALL_SOURCE: "package body nombre is" (case insensitive, espacios variables) o con comillas
        # Formato DBMS_METADATA: "CREATE OR REPLACE PACKAGE BODY nombre IS"
        # FIXED v7.4: Añadido soporte para nombres con comillas dobles sin esquema
        pattern = r"(?:CREATE\s+OR\s+REPLACE\s+)?PACKAGE\s+BODY\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)[^\n]*?\s+(IS|AS)"
        matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

            object_name = extract_object_name(match)
            actual_end, method = find_object_end_robust(
                content, start_pos, end_pos, object_name, object_type
            )

            object_code = content[start_pos:actual_end].strip()
            is_valid, error_msg = validate_extracted_code(
                object_code, object_name, object_type
            )

            if not is_valid:
                log_parsing_error(
                    f"PACKAGE_BODY '{object_name}': {error_msg} (método: {method})",
                    {
                        "object_name": object_name,
                        "object_type": object_type,
                        "line_start": content[:start_pos].count("\n") + 1,
                        "method": method,
                        "validation_error": error_msg,
                    },
                )

            lines_before = content[:start_pos].count("\n") + 1
            lines_in_object = object_code.count("\n") + 1
            package_id = f"obj_{10000 + i:05d}"  # IDs consistentes para packages

            # ===== NUEVO EN V4.0: PARSING GRANULAR =====
            # 1. Parsear procedures/functions internos
            internal_objects = parse_package_internals(
                object_code, object_name, package_id, lines_before
            )

            # 2. Crear contexto del package (V7.5: SPEC + BODY consolidado en manifest)
            # Buscar el SPEC correspondiente si spec_content está disponible
            spec_code = None
            spec_line_start = None
            spec_line_end = None
            spec_result = None

            if spec_content:
                spec_result = extract_package_spec_with_lines(object_name, spec_content)
                if spec_result:
                    spec_code, spec_line_start, spec_line_end = spec_result
                    print(
                        f"      📝 SPEC encontrado para {object_name} (líneas {spec_line_start}-{spec_line_end})"
                    )

            # Usar V7 si tenemos SPEC, V6 si solo tenemos BODY
            if spec_code or spec_content:
                # V7: Distingue entre público (SPEC) y privado (BODY)
                pkg_context = create_package_context_v7(
                    object_name, package_id, object_code, spec_code
                )
            else:
                # V6: Solo declaraciones privadas (BODY) - compatibilidad hacia atrás
                pkg_context = create_package_context(
                    object_code, object_name, package_id
                )
                # Adaptar formato V6 a V7 para consistencia
                pkg_context = {
                    "package_name": pkg_context["package_name"],
                    "package_id": pkg_context["package_id"],
                    "version": "6.0",
                    "has_public_declarations": False,
                    "public_declarations": {
                        "types": [],
                        "constants": [],
                        "cursors": [],
                        "variables": [],
                        "exceptions": [],
                    },
                    "private_declarations": {
                        "types": pkg_context.get("package_types", []),
                        "constants": pkg_context.get("package_constants", []),
                        "cursors": pkg_context.get("package_cursors", []),
                        "variables": pkg_context.get("package_variables", []),
                        "exceptions": pkg_context.get("package_exceptions", []),
                    },
                    "total_procedures": pkg_context["total_procedures"],
                    "total_functions": pkg_context["total_functions"],
                }

            save_package_context(pkg_context, package_id)

            # 3. Agregar el package completo como objeto contenedor
            # V7.5: SPEC consolidado en manifest (no archivos externos)
            package_obj = {
                "object_id": package_id,
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
                "validation_status": "valid" if is_valid else "warning",
                "category": "EXECUTABLE",
                "granular": True,  # Indica que tiene objetos internos
                "total_procedures": pkg_context["total_procedures"],
                "total_functions": pkg_context["total_functions"],
                "children": [obj["object_id"] for obj in internal_objects],
            }

            # V7.5: Agregar información del SPEC directamente al manifest
            if spec_code and spec_line_start and spec_line_end:
                package_obj["spec_file"] = "packages_spec.sql"
                package_obj["spec_line_start"] = spec_line_start
                package_obj["spec_line_end"] = spec_line_end
                package_obj["spec_has_declarations"] = pkg_context[
                    "has_public_declarations"
                ]
                package_obj["spec_declarations"] = pkg_context["public_declarations"]
            else:
                package_obj["spec_file"] = None
                package_obj["spec_line_start"] = None
                package_obj["spec_line_end"] = None
                package_obj["spec_has_declarations"] = False
                package_obj["spec_declarations"] = {
                    "types": [],
                    "constants": [],
                    "cursors": [],
                    "variables": [],
                    "exceptions": [],
                }
            objects.append(package_obj)

            # 4. Agregar todos los procedures/functions internos
            objects.extend(internal_objects)
            print(
                f"      ✅ {object_name}: {len(internal_objects)} objetos internos parseados"
            )

    elif object_type == "TRIGGER":
        # MEJORA: Eliminar comentarios antes de parsear para evitar falsos positivos
        # Ejemplo: "-- Este TRIGGER debe ejecutarse automáticamente" no debe ser capturado
        cleaned_content, _ = remove_sql_comments(content)

        # Patrón flexible: acepta con o sin CREATE OR REPLACE
        # Formato ALL_SOURCE: "trigger nombre" o 'TRIGGER "nombre"' (con comillas)
        # Formato DBMS_METADATA: "CREATE OR REPLACE TRIGGER nombre"
        # FIXED v7.4: Añadido soporte para nombres con comillas dobles sin esquema
        pattern = r"(?:CREATE\s+OR\s+REPLACE\s+)?TRIGGER\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)"
        matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

            object_name = extract_object_name(match)
            actual_end, method = find_object_end_robust(
                content, start_pos, end_pos, object_name, object_type
            )

            object_code = content[start_pos:actual_end].strip()
            is_valid, error_msg = validate_extracted_code(
                object_code, object_name, object_type
            )

            if not is_valid:
                log_parsing_error(
                    f"TRIGGER '{object_name}': {error_msg}",
                    {"object_name": object_name, "object_type": object_type},
                )

            lines_before = content[:start_pos].count("\n") + 1
            lines_in_object = object_code.count("\n") + 1

            objects.append(
                {
                    "object_id": f"trigger_{i + 1:04d}",
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
                    "validation_status": "valid" if is_valid else "warning",
                }
            )

    elif object_type in ["VIEW", "MVIEW"]:
        # MEJORA: Eliminar comentarios antes de parsear para evitar falsos positivos
        # Ejemplo: "-- Nota: CREATE OR REPLACE VIEW usuarios debe incluir..." no debe ser capturado
        cleaned_content, _ = remove_sql_comments(content)

        # FIXED v7.4: Añadido soporte para nombres con comillas dobles sin esquema
        if object_type == "VIEW":
            pattern = r"CREATE\s+OR\s+REPLACE\s+(?:FORCE\s+)?VIEW\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)"
        else:  # MVIEW
            pattern = r"CREATE\s+MATERIALIZED\s+VIEW\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)"

        matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

            semicolon_search = content[start_pos:end_pos]
            semicolon_match = re.search(r";", semicolon_search)

            actual_end = (
                start_pos + semicolon_match.end() if semicolon_match else end_pos
            )
            object_name = extract_object_name(match)
            object_code = content[start_pos:actual_end].strip()

            lines_before = content[:start_pos].count("\n") + 1
            lines_in_object = object_code.count("\n") + 1

            object_id_prefix = "view" if object_type == "VIEW" else "mview"

            objects.append(
                {
                    "object_id": f"{object_id_prefix}_{i + 1:04d}",
                    "object_name": object_name,
                    "object_type": object_type,
                    "source_file": file_path.name,
                    "line_start": lines_before,
                    "line_end": lines_before + lines_in_object - 1,
                    "char_start": start_pos,
                    "char_end": actual_end,
                    "code_length": actual_end - start_pos,
                    "status": "pending",
                }
            )

    print(f"  ✅ Encontrados {len(objects)} objetos de tipo {object_type}")
    return objects


def parse_reference_objects(file_path: Path, object_type: str) -> List[Dict]:
    """Parsea objetos de referencia (DDL, Types, etc.)."""
    if not file_path.exists():
        return []

    print(f"📖 Parseando objetos de referencia: {file_path.name}...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # MEJORA: Eliminar comentarios antes de parsear para evitar falsos positivos
    # Ejemplo: "-- TODO: CREATE TABLE usuarios debe incluir..." no debe ser capturado
    cleaned_content, _ = remove_sql_comments(content)

    objects = []

    # Patrones según tipo
    # FIXED v7.4: Añadido soporte para nombres con comillas dobles sin esquema en todos los tipos
    if object_type == "TABLE":
        pattern = r"CREATE\s+TABLE\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)"
    elif object_type == "TYPE":
        pattern = r"CREATE\s+(OR\s+REPLACE\s+)?TYPE\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)"
    elif object_type == "SEQUENCE":
        pattern = r"CREATE\s+SEQUENCE\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)"
    elif object_type == "DIRECTORY":
        pattern = r"CREATE\s+(OR\s+REPLACE\s+)?DIRECTORY\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)"
    elif object_type == "PRIMARY_KEY":
        # Patrón mejorado que captura tabla (grupos 1-3) Y constraint name completo (grupo 4)
        # Incluye caracteres especiales como $ en constraint names (ej: ADD_APER_CIER$P1)
        pattern = r"ALTER\s+TABLE\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)[\s\S]*?ADD\s+CONSTRAINT\s+([\w$]+)[\s\S]*?PRIMARY\s+KEY"
    elif object_type == "FOREIGN_KEY":
        # Patrón mejorado que captura tabla (grupos 1-3) Y constraint name completo (grupo 4)
        # Incluye caracteres especiales como $ en constraint names (ej: ADD_ARC_PRO$F1)
        pattern = r"ALTER\s+TABLE\s+(?:\"?(\w+)\"?\.\"?(\w+)\"?|\"?(\w+)\"?)[\s\S]*?ADD\s+CONSTRAINT\s+([\w$]+)[\s\S]*?FOREIGN\s+KEY"
    elif object_type == "JOB":
        # Patrón corregido que captura desde BEGIN hasta el nombre del job
        # Formato completo: BEGIN + dbms_scheduler.create_job('"JOB_NAME"', ...)
        pattern = r'BEGIN\s+dbms_scheduler\.create_job\s*\(\s*\'?"([^"]+)"\'?'
    else:
        return []

    matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))

    for i, match in enumerate(matches):
        start_pos = match.start()
        end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)

        semicolon_search = content[start_pos:end_pos]

        if object_type == "TYPE":
            end_match = re.search(r"\)\s*\n\s*/\s*(?=\n|$)", semicolon_search)
            if not end_match:
                end_match = re.search(r"/\s*(?=\n|$)", semicolon_search)
        elif object_type == "JOB":
            # Formato correcto: END; + nueva línea + / (obligatorio)
            end_match = re.search(r"END;\s*\n\s*/", semicolon_search)
        else:
            end_match = re.search(r";", semicolon_search)

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

        lines_before = content[:start_pos].count("\n") + 1
        lines_in_object = object_code.count("\n") + 1

        # Construir objeto base
        obj = {
            "object_id": f"{object_type.lower()}_{i + 1:04d}",
            "object_name": object_name,
            "object_type": object_type,
            "category": "REFERENCE",
            "source_file": file_path.name,
            "line_start": lines_before,
            "line_end": lines_before + lines_in_object - 1,
            "char_start": start_pos,
            "char_end": actual_end,
            "code_length": actual_end
            - start_pos,  # Calcular desde posiciones, no desde object_code.strip()
            "status": "reference_only",
            "note": "Contexto para análisis - Conversión manejada por ora2pg",
        }

        # Agregar tabla propietaria para constraints (FK/PK)
        if table_name is not None:
            obj["table_name"] = table_name

        objects.append(obj)

    print(f"  ✅ Encontrados {len(objects)} objetos de tipo {object_type} (referencia)")
    return objects


def generate_manifest(dry_run: bool = False) -> Dict:
    """
    Genera manifest.json optimizado para migración a PostgreSQL.

    Args:
        dry_run: Si es True, solo valida sin guardar archivos

    ORDEN CORRECTO (V7.1 - SPEC como metadata):
    1. TYPES          → Tipos base
    2. SEQUENCES      → Secuencias
    3. TABLES         → Tablas
    4. PRIMARY_KEYS   → PKs
    5. FOREIGN_KEYS   → FKs
    6. DIRECTORIES    → Directorios (opcional)
    7. VIEWS          → Views (REFERENCIA + EJECUTABLE)
    8. MVIEWS         → MViews (REFERENCIA + EJECUTABLE)
    9. FUNCTIONS      → Funciones
    10. PROCEDURES    → Procedures
    11. PACKAGE_BODY  → Package bodies (SPEC incluido como metadata)
    12. TRIGGERS      → Triggers
    13. JOBS          → Jobs (opcional)

    NOTA V7.1: PACKAGE_SPEC ya NO se incluye como objeto individual.
    El SPEC se procesa internamente para extraer declaraciones públicas
    que se guardan en el contexto del BODY.
    """
    print("\n🔍 Generando manifest (V7.1 - SPEC como metadata)...\n")

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
    directories = parse_reference_objects(
        EXTRACTED_DIR / "directories.sql", "DIRECTORY"
    )
    if directories:
        for d in directories:
            d["note"] = (
                "Contexto para UTL_FILE - PostgreSQL no usa DIRECTORIES (migrar a S3)"
            )
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

    # 11. PACKAGE BODIES (V7.0/V7.1: con soporte para SPEC como metadata)
    # NOTA V7.1: PACKAGE_SPEC ya NO se agrega como objeto individual al manifest
    # porque PostgreSQL no tiene concepto de SPEC/BODY. El SPEC se usa solo como
    # metadata de contexto para extraer declaraciones públicas del package.
    print("\n1️⃣1️⃣  PACKAGE BODIES (V7.1: SPEC como metadata, no como objeto)")

    # Cargar contenido de packages_spec.sql para extraer declaraciones públicas
    spec_file_path = EXTRACTED_DIR / "packages_spec.sql"
    spec_content = None
    if spec_file_path.exists():
        print("   📖 Cargando packages_spec.sql para extraer declaraciones públicas...")
        with open(spec_file_path, "r", encoding="utf-8") as f:
            spec_content = f.read()
        print(f"   ✅ SPEC cargado ({len(spec_content):,} caracteres)")
    else:
        print(
            "   ⚠️  packages_spec.sql no encontrado - solo se extraerán declaraciones privadas"
        )

    # Parsear PACKAGE_BODY con el contenido del SPEC
    pkg_bodies = parse_sql_file_robust(
        EXTRACTED_DIR / "packages_body.sql", "PACKAGE_BODY", spec_content=spec_content
    )
    for body in pkg_bodies:
        body["category"] = "EXECUTABLE"
    all_objects.extend(pkg_bodies)

    # 12. TRIGGERS
    print("\n1️⃣2️⃣  TRIGGERS")
    triggers = parse_sql_file_robust(EXTRACTED_DIR / "triggers.sql", "TRIGGER")
    for trigger in triggers:
        trigger["category"] = "EXECUTABLE"
    all_objects.extend(triggers)

    # 13. JOBS
    print("\n1️⃣3️⃣  JOBS (programación)")
    jobs = parse_reference_objects(EXTRACTED_DIR / "jobs.sql", "JOB")
    all_objects.extend(jobs)

    # Re-numerar object_ids en orden procesado
    for i, obj in enumerate(all_objects, start=1):
        obj["object_id"] = f"obj_{i:04d}"
        obj["processing_order"] = i

    # Estadísticas
    reference_count = len([o for o in all_objects if o.get("category") == "REFERENCE"])
    executable_count = len(
        [o for o in all_objects if o.get("category") == "EXECUTABLE"]
    )
    dual_count = len(
        [o for o in all_objects if o.get("category") == "REFERENCE_AND_EXECUTABLE"]
    )
    warning_count = len(
        [o for o in all_objects if o.get("validation_status") == "warning"]
    )

    objects_by_type = {}
    for obj in all_objects:
        obj_type = obj["object_type"]
        objects_by_type[obj_type] = objects_by_type.get(obj_type, 0) + 1

    # Processing order según configuración
    processing_order = [
        "TYPES",
        "SEQUENCES",
        "TABLES",
        "PRIMARY_KEYS",
        "FOREIGN_KEYS",
        "DIRECTORIES",
        "VIEWS",
        "MVIEWS",
        "FUNCTIONS",
        "PROCEDURES",
        "PACKAGE_SPEC",
        "PACKAGE_BODY",
        "TRIGGERS",
        "JOBS",
    ]

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "version": "4.0-granular",
        "total_objects": len(all_objects),
        "reference_count": reference_count,
        "executable_count": executable_count,
        "dual_purpose_count": dual_count,
        "warning_count": warning_count,
        "objects_by_category": {
            "REFERENCE": reference_count,
            "EXECUTABLE": executable_count,
            "REFERENCE_AND_EXECUTABLE": dual_count,
        },
        "objects_by_type": objects_by_type,
        "processing_order": processing_order,
        "note": "v4.0: Parsing granular de packages - Cada procedure/function es un objeto independiente con contexto compartido",
        "parsing_info": {
            "total_errors": len(parsing_errors),
            "error_summary": f"{warning_count} objetos con warnings",
        },
        "objects": all_objects,
    }

    if not dry_run:
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        if parsing_errors:
            with open(VALIDATION_LOG, "w", encoding="utf-8") as f:
                json.dump(parsing_errors, f, indent=2, ensure_ascii=False)
            print(f"\n⚠️  Log de parsing: {VALIDATION_LOG}")

    print(f"\n{'=' * 80}")
    print(f"📊 RESUMEN (v3 - ORDEN CORRECTO):")
    print(f"{'=' * 80}")
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
        "knowledge/classification",
        "migrated/simple/functions",
        "migrated/simple/procedures",
        "migrated/simple/packages",
        "migrated/simple/triggers",
        "migrated/complex/functions",
        "migrated/complex/procedures",
        "migrated/complex/packages",
        "migrated/complex/triggers",
        "compilation/success",
        "compilation/errors",
        "shadow_tests",
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
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            existing_progress = json.load(f)

        print(
            f"   Progreso: {existing_progress['processed_count']}/{existing_progress['total_objects']}"
        )
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
        "batches": [],
    }

    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

    print(f"✅ Progress inicializado: {PROGRESS_FILE}")
    return progress


def main():
    """Función principal"""
    import sys

    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    print("=" * 80)
    print("PREPARACIÓN MIGRACIÓN ORACLE → POSTGRESQL (v3 - ORDEN CORRECTO)")
    print("=" * 80)

    if not EXTRACTED_DIR.exists():
        print(f"\n❌ Error: {EXTRACTED_DIR} no existe")
        return

    create_directory_structure()
    manifest = generate_manifest(dry_run=dry_run)

    if not dry_run:
        initialize_progress(manifest, force=force)

    print("\n" + "=" * 80)
    print("✅ PREPARACIÓN COMPLETADA (v3)")
    print("=" * 80)

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
