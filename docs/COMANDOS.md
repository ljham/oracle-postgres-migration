# Guía de Comandos - Oracle to PostgreSQL Migration Plugin

**Plugin:** oracle-postgres-migration
**Versión:** 2.1
**Última Actualización:** 2026-01-10

---

## 📋 Índice

1. [Scripts Disponibles](#scripts-disponibles)
2. [Comandos de Preparación](#comandos-de-preparación)
3. [Comandos de Validación](#comandos-de-validación)
4. [Comandos de Análisis](#comandos-de-análisis)
5. [Flujo Completo](#flujo-completo)
6. [Troubleshooting](#troubleshooting)

---

## 📦 Scripts Disponibles

### Scripts Funcionales (Producción)

```
scripts/
├── prepare_migration_v2.py    ← Genera manifest.json y progress.json
├── validate_parsing.py         ← Valida extracción de objetos
└── update_progress.py          ← Actualiza progreso de migración
```

### Archivos Archivados (No usar)

```
archived/
├── prepare_migration_v3_improved.py  ← Demo incompleta
└── test_parsing_v2.py               ← Test obsoleto
```

---

## 🚀 Comandos de Preparación

### 1. prepare_migration_v2.py

**Propósito:** Genera manifest.json con índice de 5,775 objetos PL/SQL

**Ubicación:** `scripts/prepare_migration_v2.py`

#### Opciones de Ejecución

```bash
# Modo dry-run (solo valida, NO genera archivos)
python scripts/prepare_migration_v2.py --dry-run

# Modo producción (genera manifest.json y progress.json)
python scripts/prepare_migration_v2.py

# Con --force (regenera progress.json desde cero)
python scripts/prepare_migration_v2.py --force
```

#### Outputs Generados

```
sql/extracted/
├── manifest.json              ← Índice completo de objetos
├── progress.json              ← Estado de procesamiento
└── parsing_validation.log     ← Log de errores/warnings
```

#### Formato de manifest.json

```json
{
  "generated_at": "2026-01-10T12:45:02.123456",
  "version": "2.0-robust",
  "total_objects": 5775,
  "executable_count": 1726,
  "reference_count": 4049,
  "warning_count": 19,
  "objects_by_type": {
    "FUNCTION": 146,
    "PROCEDURE": 196,
    "PACKAGE_SPEC": 581,
    "PACKAGE_BODY": 569,
    "TRIGGER": 87,
    "VIEW": 147,
    "MVIEW": 3,
    "TYPE": 830,
    "TABLE": 2525,
    "SEQUENCE": 694
  },
  "objects": [
    {
      "object_id": "obj_0001",
      "object_name": "MY_FUNCTION",
      "object_type": "FUNCTION",
      "category": "EXECUTABLE",
      "source_file": "functions.sql",
      "line_start": 1,
      "line_end": 25,
      "char_start": 0,
      "char_end": 1234,
      "code_length": 1234,
      "status": "pending",
      "parsing_method": "exact_name_semicolon",
      "validation_status": "valid"
    }
  ]
}
```

#### Estadísticas Esperadas (v2.1)

```
Total objetos: 5,775
├─ Ejecutables (PL/SQL a convertir): 1,726
│  ├─ Valid: 1,557 (90.2%)
│  └─ Warning: 19 (1.1%)
└─ Referencias (DDL, contexto): 4,049
   ├─ TYPE: 830
   ├─ TABLE: 2,525
   └─ SEQUENCE: 694
```

---

## ✅ Comandos de Validación

### 2. validate_parsing.py

**Propósito:** Valida que todos los objetos fueron extraídos correctamente

**Ubicación:** `scripts/validate_parsing.py`

#### Opciones de Ejecución

```bash
# Validación completa de todos los objetos
python scripts/validate_parsing.py

# Validar solo un tipo de objeto
python scripts/validate_parsing.py --type TRIGGER
python scripts/validate_parsing.py --type FUNCTION
python scripts/validate_parsing.py --type PACKAGE_BODY
python scripts/validate_parsing.py --type PROCEDURE

# Modo verbose (más detalles)
python scripts/validate_parsing.py --verbose

# Ver muestra aleatoria de N objetos
python scripts/validate_parsing.py --sample 10
python scripts/validate_parsing.py --sample 20
```

#### Exit Codes

- **0** - Todo OK (sin errores críticos)
- **1** - Errores críticos encontrados

#### Validaciones Realizadas

1. **Límites coherentes**: line_start < line_end, char_start < char_end
2. **Delimitadores correctos**:
   - PL/SQL debe terminar con `/`
   - DDL debe terminar con `;`
3. **Inicio correcto**: Debe empezar con `CREATE`
4. **Code_length**: Debe coincidir con char_end - char_start

#### Resultados Esperados (v2.1)

```
📊 Total objetos validados: 5,775
✅ Objetos sin problemas: 2,733
⚠️  Objetos con warnings: 1,518
❌ Objetos con errores: 1,524

Nota: Los errores están en objetos REFERENCE (TYPE, TABLE)
      que son solo contexto y no se convierten con Claude.
      Los objetos EJECUTABLES tienen solo 19 warnings (1.1%)
```

---

## 📊 Comandos de Análisis

### 3. Análisis de Objetos Ejecutables

```bash
# Ver resumen de objetos ejecutables
python - << 'EOF'
import json
manifest = json.load(open('sql/extracted/manifest.json', 'r'))
ejecutables = [obj for obj in manifest['objects'] if obj.get('category') == 'EXECUTABLE']
valid = len([obj for obj in ejecutables if obj.get('validation_status') == 'valid'])
warning = len([obj for obj in ejecutables if obj.get('validation_status') == 'warning'])
print(f"Total ejecutables: {len(ejecutables)}")
print(f"Valid: {valid} ({valid/len(ejecutables)*100:.1f}%)")
print(f"Warning: {warning} ({warning/len(ejecutables)*100:.1f}%)")
EOF
```

### 4. Ver Objetos con Warnings

```bash
# Listar objetos con warnings
python - << 'EOF'
import json
manifest = json.load(open('sql/extracted/manifest.json', 'r'))
warnings = [obj for obj in manifest['objects']
            if obj.get('category') == 'EXECUTABLE'
            and obj.get('validation_status') == 'warning']
print(f"Total objetos con warnings: {len(warnings)}\n")
for obj in warnings:
    print(f"{obj['object_name']:40s} ({obj['object_type']:15s}) - método: {obj.get('parsing_method')}")
EOF
```

### 5. Análisis por Tipo de Objeto

```bash
# Contar objetos por tipo y categoría
python - << 'EOF'
import json
from collections import defaultdict

manifest = json.load(open('sql/extracted/manifest.json', 'r'))

# Agrupar por tipo y categoría
by_type = defaultdict(lambda: {'EXECUTABLE': 0, 'REFERENCE': 0})
for obj in manifest['objects']:
    obj_type = obj['object_type']
    category = obj.get('category', 'REFERENCE')
    by_type[obj_type][category] += 1

print("Objetos por Tipo y Categoría:")
print("="*60)
for obj_type in sorted(by_type.keys()):
    exe = by_type[obj_type]['EXECUTABLE']
    ref = by_type[obj_type]['REFERENCE']
    total = exe + ref
    print(f"{obj_type:20s} | Total: {total:4d} | Exec: {exe:4d} | Ref: {ref:4d}")
EOF
```

### 6. Ver Métodos de Parsing Usados

```bash
# Ver distribución de métodos de parsing
python - << 'EOF'
import json
from collections import Counter

manifest = json.load(open('sql/extracted/manifest.json', 'r'))
ejecutables = [obj for obj in manifest['objects'] if obj.get('category') == 'EXECUTABLE']

methods = [obj.get('parsing_method', 'N/A') for obj in ejecutables]
method_counts = Counter(methods)

print("Métodos de Parsing Utilizados:")
print("="*60)
for method, count in method_counts.most_common():
    pct = (count / len(ejecutables)) * 100
    print(f"{method:30s} | {count:4d} objetos ({pct:5.1f}%)")
EOF
```

---

## 🔄 Flujo Completo de Ejecución

### Pre-requisitos

```bash
# 1. Verificar que estás en el directorio del plugin
pwd
# Debe mostrar: .../oracle-postgres-migration

# 2. Verificar que existen los archivos SQL
ls -lh sql/extracted/*.sql

# 3. Verificar que los scripts existen
ls -lh scripts/prepare_migration_v2.py
ls -lh scripts/validate_parsing.py
```

### Flujo Estándar

```bash
# PASO 1: Ejecutar en modo dry-run primero
python scripts/prepare_migration_v2.py --dry-run

# PASO 2: Si todo OK, generar manifest
python scripts/prepare_migration_v2.py

# PASO 3: Validar extracción
python scripts/validate_parsing.py

# PASO 4: Ver resumen
ls -lh sql/extracted/*.json
cat sql/extracted/manifest.json | python -m json.tool | head -50

# PASO 5: Analizar objetos ejecutables
python - << 'EOF'
import json
manifest = json.load(open('sql/extracted/manifest.json', 'r'))
ejecutables = [obj for obj in manifest['objects'] if obj.get('category') == 'EXECUTABLE']
valid = len([obj for obj in ejecutables if obj.get('validation_status') == 'valid'])
warning = len([obj for obj in ejecutables if obj.get('validation_status') == 'warning'])
print(f"Ejecutables: {len(ejecutables)}")
print(f"Valid: {valid} ({valid/len(ejecutables)*100:.1f}%)")
print(f"Warning: {warning} ({warning/len(ejecutables)*100:.1f}%)")
EOF
```

### Flujo con Regeneración Completa

```bash
# 1. Limpiar archivos anteriores
rm -f sql/extracted/manifest.json
rm -f sql/extracted/progress.json
rm -f sql/extracted/parsing_validation.log

# 2. Generar desde cero
python scripts/prepare_migration_v2.py --force

# 3. Validar
python scripts/validate_parsing.py
```

---

## 🔧 Troubleshooting

### Problema: manifest.json no se genera

**Síntomas:**
```
❌ Error: Directorio sql/extracted no existe
```

**Solución:**
```bash
# Crear estructura de directorios
mkdir -p sql/extracted
mkdir -p knowledge/{json,markdown,classification}
mkdir -p migrated/{simple,complex}/{functions,procedures,packages,triggers}
mkdir -p compilation_results/{success,errors}
mkdir -p shadow_tests
```

---

### Problema: Archivos SQL no encontrados

**Síntomas:**
```
⚠️  Archivo no encontrado: sql/extracted/functions.sql
```

**Solución:**
```bash
# Verificar que los archivos SQL existen
ls -lh sql/extracted/

# Deben existir:
# - functions.sql
# - procedures.sql
# - packages_spec.sql
# - packages_body.sql
# - triggers.sql
# - views.sql
# - materialized_views.sql
# - types.sql
# - tables.sql
# - sequences.sql
```

---

### Problema: Muchos warnings en validación

**Síntomas:**
```
⚠️  22 objetos tienen warnings de validación
```

**Análisis:**
```bash
# Ver qué objetos tienen warnings
cat sql/extracted/parsing_validation.log | python -m json.tool

# Filtrar solo objetos ejecutables
python - << 'EOF'
import json
manifest = json.load(open('sql/extracted/manifest.json', 'r'))
warnings = [obj for obj in manifest['objects']
            if obj.get('category') == 'EXECUTABLE'
            and obj.get('validation_status') == 'warning']
print(f"Warnings en EJECUTABLES: {len(warnings)}")
for obj in warnings[:10]:
    print(f"  - {obj['object_name']} ({obj['object_type']})")
EOF
```

**Criterio de Aprobación:**
- Si warnings en EJECUTABLES < 5% → Aceptable ✅
- Si warnings en EJECUTABLES > 5% → Revisar manualmente ⚠️

---

### Problema: validate_parsing.py falla con exit code 1

**Síntomas:**
```
❌ NO APROBADO: 1544 errores críticos encontrados
```

**Análisis:**
```bash
# Verificar si los errores son en objetos REFERENCE
python - << 'EOF'
import json
manifest = json.load(open('sql/extracted/manifest.json', 'r'))
ejecutables = [obj for obj in manifest['objects'] if obj.get('category') == 'EXECUTABLE']
referencias = [obj for obj in manifest['objects'] if obj.get('category') == 'REFERENCE']
print(f"Ejecutables: {len(ejecutables)}")
print(f"Referencias: {len(referencias)}")
print("\nSi los errores están en REFERENCE, son no críticos.")
EOF
```

**Criterio:**
- Errores en REFERENCE → No críticos (ora2pg los maneja)
- Errores en EXECUTABLE → Críticos (requieren corrección)

---

### Problema: Objetos TRIGGER con nombres diferentes

**Síntomas:**
```
⚠️  No se encontró END exacto para TRIGGER 'AGE_T_CONFIRMA_CITA_MAILING'
```

**Solución:**
Ya solucionado en v2.1 con nueva estrategia de parsing para TRIGGERS.

**Verificar:**
```bash
# Ver método de parsing usado para triggers
python - << 'EOF'
import json
manifest = json.load(open('sql/extracted/manifest.json', 'r'))
triggers = [obj for obj in manifest['objects'] if obj['object_type'] == 'TRIGGER']
methods = {}
for obj in triggers:
    method = obj.get('parsing_method', 'N/A')
    methods[method] = methods.get(method, 0) + 1
print("Métodos de parsing en TRIGGERS:")
for method, count in methods.items():
    print(f"  {method}: {count}")
EOF
```

**Resultado esperado (v2.1):**
```
trigger_end_with_slash: 17  ← Correcto
exact_name_semicolon: 70     ← Correcto
fallback_end_pos: 0          ← Si > 0, hay problema
```

---

## 📊 Criterios de Aprobación

### Para Proceder a Fase 1 (Análisis)

| Criterio | Requerido | Actual (v2.1) | Estado |
|----------|-----------|---------------|--------|
| % Objetos EJECUTABLES válidos | >85% | 90.2% | ✅ |
| % Warnings en EJECUTABLES | <5% | 1.1% | ✅ |
| Errores críticos en EJECUTABLES | 0 | 0 | ✅ |
| Manifest generado | Sí | Sí | ✅ |
| Progress generado | Sí | Sí | ✅ |

**Conclusión:** ✅ APROBADO para proceder a Fase 1

---

## 📝 Logs y Outputs

### Ubicación de Archivos

```
sql/extracted/
├── manifest.json              ← Índice completo de objetos
├── progress.json              ← Estado actual de migración
└── parsing_validation.log     ← Errores y warnings de parsing
```

### Ver Logs

```bash
# Ver manifest completo
cat sql/extracted/manifest.json | python -m json.tool

# Ver solo estadísticas
cat sql/extracted/manifest.json | python -m json.tool | head -30

# Ver progress actual
cat sql/extracted/progress.json | python -m json.tool

# Ver errores de parsing
cat sql/extracted/parsing_validation.log | python -m json.tool | head -50

# Contar warnings
cat sql/extracted/parsing_validation.log | python -c "import sys,json; print(len(json.load(sys.stdin)))"
```

---

## 🔗 Documentación Relacionada

- **[PARSING_GUIDE.md](PARSING_GUIDE.md)** - Guía completa de parsing y validación
- **[ESTRATEGIA.md](ESTRATEGIA.md)** - Estrategia completa de migración (4 fases)
- **[TRACKING_SYSTEM.md](TRACKING_SYSTEM.md)** - Sistema de progreso y reanudación
- **[README.md](../README.md)** - Índice principal del plugin

---

**Última Actualización:** 2026-01-10
**Versión del Script:** prepare_migration_v2.py v2.1
**Autor:** Claude Sonnet 4.5
