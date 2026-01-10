#!/usr/bin/env python3
"""
Script de prueba para validar parsing robusto v2
Prueba específicamente el objeto FAC_K_VERIFICA_CIERRES que estaba mal parseado
"""

import re
from pathlib import Path

BASE_DIR = Path.cwd()
EXTRACTED_DIR = BASE_DIR / "sql" / "extracted"
PACKAGES_BODY_FILE = EXTRACTED_DIR / "packages_body.sql"


def extract_object_name(match) -> str:
    """Extrae el nombre del objeto desde los grupos capturados."""
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


def find_object_end_robust(content: str, start_pos: int, end_pos: int, object_name: str) -> tuple:
    """Encuentra el fin del objeto usando el nombre exacto."""
    search_content = content[start_pos:end_pos]

    # Estrategia 1: Buscar END con nombre exacto (termina en ;)
    pattern_exact = rf'END\s+{re.escape(object_name)}\s*;'
    match_exact = re.search(pattern_exact, search_content, re.IGNORECASE)

    if match_exact:
        actual_end = start_pos + match_exact.end()
        return actual_end, "exact_name_semicolon"

    # Estrategia 2: Buscar último END; cerca del final
    pattern_end_near_end = r'END\s*;\s*\n?\s*/?'
    matches = list(re.finditer(pattern_end_near_end, search_content, re.IGNORECASE))
    if matches:
        last_match = matches[-1]
        actual_end = start_pos + last_match.end()
        return actual_end, "end_near_end_of_range"

    return end_pos, "fallback_end_pos"


def test_package_body_parsing():
    """Prueba el parsing de PACKAGE_BODY con FAC_K_VERIFICA_CIERRES."""
    print("="*80)
    print("TEST: Parsing de PACKAGE_BODY FAC_K_VERIFICA_CIERRES")
    print("="*80)

    if not PACKAGES_BODY_FILE.exists():
        print(f"❌ Archivo no encontrado: {PACKAGES_BODY_FILE}")
        return

    with open(PACKAGES_BODY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar el package específico
    pattern = r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+BODY\s+(?:"?(\w+)"?\.\"?(\w+)\"?|(\w+))\s+(IS|AS)'
    matches = list(re.finditer(pattern, content, re.IGNORECASE))

    print(f"\n📊 Total PACKAGE_BODY encontrados: {len(matches)}")

    # Buscar FAC_K_VERIFICA_CIERRES
    target_found = False
    for i, match in enumerate(matches):
        object_name = extract_object_name(match)

        if object_name == "FAC_K_VERIFICA_CIERRES":
            target_found = True
            print(f"\n✅ Encontrado: {object_name} (índice {i})")

            start_pos = match.start()

            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            # Parsear con método v2
            actual_end, method = find_object_end_robust(content, start_pos, end_pos, object_name)

            # Calcular líneas
            lines_before = content[:start_pos].count('\n') + 1
            object_code = content[start_pos:actual_end]
            lines_in_object = object_code.count('\n') + 1
            line_end = lines_before + lines_in_object - 1

            print(f"\n📝 RESULTADOS DEL PARSING:")
            print(f"   Objeto: {object_name}")
            print(f"   Método: {method}")
            print(f"   Línea inicio: {lines_before}")
            print(f"   Línea fin: {line_end}")
            print(f"   Total líneas: {lines_in_object}")
            print(f"   Tamaño código: {len(object_code)} chars")

            # Mostrar inicio y fin del código
            code_lines = object_code.split('\n')
            print(f"\n📄 PRIMERAS 5 LÍNEAS:")
            for idx, line in enumerate(code_lines[:5], start=lines_before):
                print(f"   {idx}: {line[:80]}")

            print(f"\n📄 ÚLTIMAS 5 LÍNEAS:")
            for idx, line in enumerate(code_lines[-5:], start=line_end-4):
                print(f"   {idx}: {line[:80]}")

            # Validación
            print(f"\n✅ VALIDACIÓN:")
            if line_end == 913974:
                print(f"   ✅ Línea fin CORRECTA: {line_end} (esperado: 913974)")
            else:
                print(f"   ❌ Línea fin INCORRECTA: {line_end} (esperado: 913974)")

            if lines_before == 913149:
                print(f"   ✅ Línea inicio CORRECTA: {lines_before} (esperado: 913149)")
            else:
                print(f"   ❌ Línea inicio INCORRECTA: {lines_before} (esperado: 913149)")

            # Verificar que termina correctamente
            last_lines = '\n'.join(code_lines[-3:])
            if 'end FAC_K_VERIFICA_CIERRES' in last_lines.lower():
                print(f"   ✅ Termina con END FAC_K_VERIFICA_CIERRES;")
            else:
                print(f"   ❌ NO termina con END FAC_K_VERIFICA_CIERRES;")

            break

    if not target_found:
        print(f"\n❌ No se encontró el package FAC_K_VERIFICA_CIERRES")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    test_package_body_parsing()
