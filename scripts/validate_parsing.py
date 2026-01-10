#!/usr/bin/env python3
"""
Script de validación de parsing - Verifica que la extracción sea correcta

Este script debe ejecutarse DESPUÉS de prepare_migration.py para validar
que todos los objetos fueron extraídos correctamente del SQL.

Validaciones:
1. line_start < line_end
2. char_start < char_end
3. Objetos PL/SQL terminan con /
4. Objetos DDL terminan con ;
5. Código extraído coincide con líneas originales

Uso:
    cd /path/to/phantomx-nexus
    python /path/to/oracle-postgres-migration/scripts/validate_parsing.py

    O con modo verbose:
    python validate_parsing.py --verbose

    O validar solo un tipo de objeto:
    python validate_parsing.py --type PACKAGE_BODY

Output:
    - Imprime resumen de validación
    - Exit code 0 si todo OK
    - Exit code 1 si hay errores críticos
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Directorio base del proyecto (usa CWD)
BASE_DIR = Path.cwd()
EXTRACTED_DIR = BASE_DIR / "sql" / "extracted"
MANIFEST_FILE = EXTRACTED_DIR / "manifest.json"


def validate_object_boundaries(obj: Dict) -> List[str]:
    """
    Valida que los límites del objeto sean coherentes.

    Args:
        obj: Diccionario con metadata del objeto

    Returns:
        Lista de errores encontrados (vacía si OK)
    """
    errors = []

    # Validar line_start < line_end
    if obj["line_start"] >= obj["line_end"]:
        errors.append(f"line_start ({obj['line_start']}) >= line_end ({obj['line_end']})")

    # Validar char_start < char_end
    if obj["char_start"] >= obj["char_end"]:
        errors.append(f"char_start ({obj['char_start']}) >= char_end ({obj['char_end']})")

    # Validar code_length coherente
    expected_length = obj["char_end"] - obj["char_start"]
    if obj["code_length"] != expected_length:
        errors.append(f"code_length ({obj['code_length']}) != expected ({expected_length})")

    return errors


def validate_object_delimiters(obj: Dict, extracted_code: str, verbose: bool = False) -> Tuple[List[str], List[str]]:
    """
    Valida que el código extraído tenga los delimitadores correctos.

    Args:
        obj: Diccionario con metadata del objeto
        extracted_code: Código extraído del SQL
        verbose: Si True, muestra detalles adicionales

    Returns:
        Tupla (errores, warnings)
    """
    errors = []
    warnings = []

    code_stripped = extracted_code.strip()
    obj_type = obj["object_type"]
    obj_name = obj["object_name"]

    # Validar que objetos PL/SQL terminan con /
    if obj_type in ["FUNCTION", "PROCEDURE", "PACKAGE_SPEC", "PACKAGE_BODY", "TRIGGER"]:
        if not code_stripped.endswith('/'):
            warnings.append(f"No termina con '/' (última línea: '{code_stripped[-50:]}')")

        # Validar que empieza con CREATE
        if not code_stripped.upper().startswith('CREATE'):
            errors.append(f"No empieza con CREATE")

    # Validar que objetos DDL terminan con ;
    if obj_type in ["VIEW", "MVIEW"]:
        if not code_stripped.endswith(';'):
            errors.append(f"No termina con ';'")

        # Validar que empieza con CREATE
        if not code_stripped.upper().startswith('CREATE'):
            errors.append(f"No empieza con CREATE")

    # Validar objetos de referencia
    if obj.get("category") == "REFERENCE":
        if obj_type == "TYPE":
            # TYPEs pueden terminar con / o ;
            if not (code_stripped.endswith('/') or code_stripped.endswith(';')):
                warnings.append(f"TYPE no termina con '/' ni ';'")
        elif obj_type in ["TABLE", "SEQUENCE", "PRIMARY_KEY", "FOREIGN_KEY"]:
            # DDL debe terminar con ;
            if not code_stripped.endswith(';'):
                errors.append(f"No termina con ';'")

    return errors, warnings


def validate_extraction(object_type_filter: str = None, verbose: bool = False) -> Tuple[int, int, int]:
    """
    Valida que todos los objetos fueron extraídos correctamente.

    Args:
        object_type_filter: Si se especifica, solo valida ese tipo de objeto
        verbose: Si True, muestra información detallada

    Returns:
        Tupla (total_objects, total_warnings, total_errors)
    """
    print("🔍 Validando extracción de objetos...\n")

    # Verificar que manifest existe
    if not MANIFEST_FILE.exists():
        print(f"❌ Error: {MANIFEST_FILE} no existe")
        print("   Ejecuta primero prepare_migration.py")
        return 0, 0, 1

    # Cargar manifest
    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    all_objects = manifest["objects"]

    # Filtrar por tipo si se especificó
    if object_type_filter:
        all_objects = [obj for obj in all_objects if obj["object_type"] == object_type_filter]
        print(f"🔎 Filtrando por tipo: {object_type_filter}")
        print(f"   Objetos encontrados: {len(all_objects)}\n")

    errors_by_object = {}
    warnings_by_object = {}

    # Validar cada objeto
    for obj in all_objects:
        obj_id = obj["object_id"]
        obj_errors = []
        obj_warnings = []

        # Validación 1: Límites coherentes
        boundary_errors = validate_object_boundaries(obj)
        obj_errors.extend(boundary_errors)

        # Validación 2: Leer código real
        source_file = EXTRACTED_DIR / obj["source_file"]

        if not source_file.exists():
            obj_errors.append(f"Archivo fuente no encontrado: {source_file}")
            errors_by_object[obj_id] = obj_errors
            continue

        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            extracted_code = content[obj["char_start"]:obj["char_end"]]

            # Validación 3: Delimitadores correctos
            delim_errors, delim_warnings = validate_object_delimiters(obj, extracted_code, verbose)
            obj_errors.extend(delim_errors)
            obj_warnings.extend(delim_warnings)

            # Validación 4: Comparar líneas
            lines_in_file = content[:obj["char_start"]].count('\n') + 1
            if lines_in_file != obj["line_start"]:
                obj_errors.append(f"line_start no coincide: manifest={obj['line_start']}, real={lines_in_file}")

        except Exception as e:
            obj_errors.append(f"Error al leer archivo: {str(e)}")

        # Guardar errores y warnings
        if obj_errors:
            errors_by_object[obj_id] = obj_errors
        if obj_warnings:
            warnings_by_object[obj_id] = obj_warnings

    # Mostrar resultados
    total_objects = len(all_objects)
    total_warnings = len(warnings_by_object)
    total_errors = len(errors_by_object)

    print(f"{'='*80}")
    print(f"RESULTADOS DE VALIDACIÓN")
    print(f"{'='*80}\n")

    print(f"📊 Total objetos validados: {total_objects}")
    print(f"✅ Objetos sin problemas: {total_objects - total_warnings - total_errors}")
    print(f"⚠️  Objetos con warnings: {total_warnings}")
    print(f"❌ Objetos con errores: {total_errors}\n")

    # Mostrar warnings (primeros 10)
    if warnings_by_object:
        print(f"{'='*80}")
        print("WARNINGS (primeros 10)")
        print(f"{'='*80}\n")

        for i, (obj_id, warnings) in enumerate(list(warnings_by_object.items())[:10]):
            obj = next((o for o in all_objects if o["object_id"] == obj_id), None)
            print(f"⚠️  {obj_id}: {obj['object_name']} ({obj['object_type']})")
            for w in warnings:
                print(f"   - {w}")
            print()

        if len(warnings_by_object) > 10:
            print(f"... y {len(warnings_by_object) - 10} objetos más con warnings\n")

    # Mostrar errores (primeros 10)
    if errors_by_object:
        print(f"{'='*80}")
        print("ERRORES CRÍTICOS (primeros 10)")
        print(f"{'='*80}\n")

        for i, (obj_id, errors) in enumerate(list(errors_by_object.items())[:10]):
            obj = next((o for o in all_objects if o["object_id"] == obj_id), None)
            print(f"❌ {obj_id}: {obj['object_name']} ({obj['object_type']})")
            for e in errors:
                print(f"   - {e}")
            print()

        if len(errors_by_object) > 10:
            print(f"... y {len(errors_by_object) - 10} objetos más con errores\n")

    # Resumen final
    print(f"{'='*80}")
    print("RESUMEN")
    print(f"{'='*80}\n")

    if total_errors == 0 and total_warnings == 0:
        print("✅ APROBADO: Todos los objetos fueron extraídos correctamente")
        return total_objects, total_warnings, total_errors

    if total_errors == 0 and total_warnings < total_objects * 0.01:
        print(f"✅ APROBADO CON WARNINGS: {total_warnings} warnings ({total_warnings/total_objects*100:.2f}%)")
        print("   Revisar warnings manualmente antes de proceder")
        return total_objects, total_warnings, total_errors

    if total_errors == 0:
        print(f"⚠️  REVISAR: {total_warnings} warnings ({total_warnings/total_objects*100:.2f}%)")
        print("   Más del 1% de objetos tienen warnings - revisar antes de proceder")
        return total_objects, total_warnings, total_errors

    print(f"❌ NO APROBADO: {total_errors} errores críticos encontrados")
    print("   Corregir errores en prepare_migration.py antes de proceder")
    return total_objects, total_warnings, total_errors


def show_sample_objects(manifest_path: Path, sample_size: int = 5):
    """
    Muestra una muestra aleatoria de objetos extraídos para revisión manual.

    Args:
        manifest_path: Ruta al manifest.json
        sample_size: Número de objetos a mostrar
    """
    import random

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # Seleccionar muestra aleatoria
    sample = random.sample(manifest["objects"], min(sample_size, len(manifest["objects"])))

    print(f"\n{'='*80}")
    print(f"MUESTRA ALEATORIA ({sample_size} objetos)")
    print(f"{'='*80}\n")

    for obj in sample:
        print(f"📄 {obj['object_id']}: {obj['object_name']} ({obj['object_type']})")
        print(f"   Archivo: {obj['source_file']}")
        print(f"   Líneas: {obj['line_start']} - {obj['line_end']}")
        print(f"   Caracteres: {obj['char_start']} - {obj['char_end']}")

        # Leer y mostrar primeras/últimas líneas
        source_file = EXTRACTED_DIR / obj["source_file"]
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        extracted_code = content[obj["char_start"]:obj["char_end"]].strip()
        lines = extracted_code.split('\n')

        print(f"   Primera línea: {lines[0][:80]}...")
        if len(lines) > 1:
            print(f"   Última línea: {lines[-1][:80]}...")
        print()


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Valida extracción de objetos PL/SQL')
    parser.add_argument('--type', help='Filtrar por tipo de objeto (ej: PACKAGE_BODY)')
    parser.add_argument('--verbose', action='store_true', help='Mostrar información detallada')
    parser.add_argument('--sample', type=int, help='Mostrar N objetos aleatorios para revisión manual')

    args = parser.parse_args()

    # Mostrar muestra si se solicitó
    if args.sample:
        show_sample_objects(MANIFEST_FILE, args.sample)
        return

    # Ejecutar validación
    total_objects, total_warnings, total_errors = validate_extraction(
        object_type_filter=args.type,
        verbose=args.verbose
    )

    # Exit code
    if total_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
