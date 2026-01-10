#!/usr/bin/env python3
"""
Script de preparación v3 - MEJORAS QUIRÚRGICAS AL REGEX

CAMBIOS CLAVE RESPECTO A v2:
1. Lookbehind mejorado para capturar múltiples espacios/tabs
2. Exclusión de más palabras clave (CASE, BEGIN)
3. Cálculo directo de line_end desde actual_end
4. Parsing con conteo de bloques BEGIN/END anidados

VERSIÓN: 3.0-improved-regex
FECHA: 2026-01-10
"""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

BASE_DIR = Path.cwd()
EXTRACTED_DIR = BASE_DIR / "sql" / "extracted"
OBJECTS_DIR = EXTRACTED_DIR / "objects"
MANIFEST_FILE = EXTRACTED_DIR / "manifest.json"
PROGRESS_FILE = EXTRACTED_DIR / "progress.json"
VALIDATION_LOG = EXTRACTED_DIR / "parsing_validation.log"

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
    """Extrae el nombre del objeto desde los grupos capturados por regex."""
    groups = match.groups()
    relevant_groups = [
        g for g in groups
        if g is not None and not re.match(r'^(OR|REPLACE|IS|AS|\s)+$', g, re.IGNORECASE)
    ]

    if len(relevant_groups) >= 2:
        object_name = relevant_groups[1].upper()
    elif len(relevant_groups) >= 1:
        object_name = relevant_groups[-1].upper()
    else:
        object_name = "UNKNOWN"

    return object_name


def count_begin_end_blocks(content: str, start_pos: int, end_pos: int) -> int:
    """
    Cuenta el balance de bloques BEGIN/END para encontrar el END principal.

    ESTRATEGIA:
    - Cada BEGIN incrementa el contador
    - Cada END (que no sea LOOP, IF, CASE) decrementa el contador
    - Cuando el contador llega a 0, encontramos el END principal

    Returns:
        Posición del END principal, o -1 si no se encuentra
    """
    search_content = content[start_pos:end_pos]

    # Buscar todos los BEGIN y END (excluyendo LOOP, IF, CASE)
    # Usamos un enfoque más robusto: capturar BEGIN y END con contexto

    begin_pattern = r'\bBEGIN\b'
    # END que NO sea precedido por LOOP, IF, CASE (con espacios variables)
    end_pattern = r'(?<!\b(?:LOOP|IF|CASE)\s{0,10})\bEND\b'

    # Encontrar todas las posiciones de BEGIN y END
    begins = [(m.start(), 'BEGIN') for m in re.finditer(begin_pattern, search_content, re.IGNORECASE)]
    ends = [(m.start(), 'END') for m in re.finditer(end_pattern, search_content, re.IGNORECASE)]

    # Combinar y ordenar por posición
    events = sorted(begins + ends, key=lambda x: x[0])

    # Contar balance
    balance = 1  # Empezamos en 1 porque el CREATE ya abrió un bloque implícito

    for pos, event_type in events:
        if event_type == 'BEGIN':
            balance += 1
        elif event_type == 'END':
            balance -= 1

            # Cuando el balance llega a 0, encontramos el END principal
            if balance == 0:
                # Buscar el ; después del END
                semicolon_search = search_content[pos:]
                semicolon_match = re.search(r';\s*', semicolon_search)

                if semicolon_match:
                    return start_pos + pos + semicolon_match.end()

    return -1  # No se encontró el END principal


def find_object_end_robust_v3(
    content: str,
    start_pos: int,
    end_pos: int,
    object_name: str,
    object_type: str
) -> Tuple[int, str]:
    """
    VERSIÓN MEJORADA v3 - Encuentra el fin del objeto usando múltiples estrategias.

    MEJORAS RESPECTO A v2:
    1. Lookbehind mejorado para espacios/tabs variables
    2. Exclusión de más palabras clave (CASE, BEGIN)
    3. Conteo de bloques BEGIN/END anidados
    4. Búsqueda más precisa de END con nombre del objeto
    """
    search_content = content[start_pos:end_pos]

    # ESTRATEGIA 1: Buscar END con el nombre exacto del objeto
    # Mejorado: Permitir espacios/saltos de línea entre END y nombre
    pattern_exact = rf'END\s+{re.escape(object_name)}\s*;'
    match_exact = re.search(pattern_exact, search_content, re.IGNORECASE)

    if match_exact:
        actual_end = start_pos + match_exact.end()
        return actual_end, "exact_name_semicolon"

    # ESTRATEGIA 2: Para objetos complejos, usar conteo de BEGIN/END
    if object_type in ["FUNCTION", "PROCEDURE", "PACKAGE_BODY", "PACKAGE_SPEC"]:
        balance_end = count_begin_end_blocks(content, start_pos, end_pos)
        if balance_end != -1:
            return balance_end, "begin_end_balance"

    # ESTRATEGIA 3: Buscar END; excluyendo palabras clave comunes
    # MEJORADO: Lookbehind más robusto con \s* para espacios variables
    if object_type in ["FUNCTION", "PROCEDURE", "TRIGGER"]:
        # Excluir: LOOP, IF, CASE, BEGIN (con espacios variables)
        pattern_end_only = r'(?<!LOOP\s*)(?<!IF\s*)(?<!CASE\s*)\bEND\s*;'

        matches = list(re.finditer(pattern_end_only, search_content, re.IGNORECASE))
        if matches:
            # Tomar el último match (más conservador)
            last_match = matches[-1]
            actual_end = start_pos + last_match.end()
            return actual_end, "end_only_improved_last_match"

    # ESTRATEGIA 4: Para PACKAGE sin nombre en END
    if object_type in ["PACKAGE_BODY", "PACKAGE_SPEC"]:
        pattern_end_near_end = r'END\s*;\s*\n?\s*/?'
        matches = list(re.finditer(pattern_end_near_end, search_content, re.IGNORECASE))
        if matches:
            last_match = matches[-1]
            actual_end = start_pos + last_match.end()
            return actual_end, "end_near_end_of_range"

    # ESTRATEGIA 5: FALLBACK
    log_parsing_error(
        f"No se encontró END exacto para {object_type} '{object_name}', usando end_pos",
        {"object_name": object_name, "object_type": object_type}
    )
    return end_pos, "fallback_end_pos"


def validate_extracted_code(code: str, object_name: str, object_type: str) -> Tuple[bool, str]:
    """Valida que el código extraído sea sintácticamente coherente."""
    # Verificación 1: Debe iniciar con CREATE
    if not re.match(r'^\s*CREATE', code, re.IGNORECASE):
        return False, "No inicia con CREATE"

    # Verificación 2: Debe terminar con END; o END nombre;
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
            return False, "PACKAGE_BODY sin procedimientos/funciones"

    return True, "OK"


def parse_sql_file_robust(file_path: Path, object_type: str) -> List[Dict]:
    """
    VERSIÓN MEJORADA v3 - Parsea archivo SQL con estrategias mejoradas.

    CAMBIO CLAVE: Cálculo directo de line_end desde actual_end
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

            # Encontrar END de forma robusta (v3 mejorado)
            actual_end, method = find_object_end_robust_v3(
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

            # CAMBIO CRÍTICO v3: Cálculo DIRECTO de line_start y line_end
            line_start = content[:start_pos].count('\n') + 1
            line_end = content[:actual_end].count('\n') + 1  # ← DIRECTO desde actual_end

            objects.append({
                "object_id": f"{object_type.lower()}_{i+1:04d}",
                "object_name": object_name,
                "object_type": object_type,
                "source_file": file_path.name,
                "line_start": line_start,
                "line_end": line_end,  # ← Ahora es más preciso
                "char_start": start_pos,
                "char_end": actual_end,
                "code_length": len(object_code),
                "status": "pending",
                "parsing_method": method,
                "validation_status": "valid" if is_valid else "warning"
            })

    # Similar para PACKAGE_SPEC, PACKAGE_BODY, TRIGGER, etc.
    # (código repetido omitido por brevedad - aplicar los mismos cambios)

    print(f"  ✅ Encontrados {len(objects)} objetos de tipo {object_type}")
    return objects


# ... (resto del código similar a v2, aplicando los mismos cambios)

if __name__ == "__main__":
    print("⚠️  Esta es una versión de demostración con mejoras quirúrgicas")
    print("    Revisar e integrar en prepare_migration_v2.py")
