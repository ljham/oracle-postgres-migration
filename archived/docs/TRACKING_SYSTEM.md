# Mecanismo de Tracking y Reanudación

**Problema:** ¿Cómo procesar 8,122 objetos PL/SQL en lotes cuando están todos mezclados en archivos SQL grandes?

**Solución:** Sistema de 3 componentes para tracking automático y reanudación desde cualquier punto.

---

## 📋 Componentes del Sistema

### 1. Manifest (`sql/extracted/manifest.json`)

**Propósito:** Índice completo de todos los objetos a migrar

**Contiene:**
- Lista de 8,122 objetos con metadata
- Posición exacta en archivos fuente (líneas, caracteres)
- Estado de procesamiento (pending/processed)
- Tipo de objeto, nombre, ID único

**Ejemplo:**
```json
{
  "generated_at": "2025-01-05T10:00:00",
  "total_objects": 8122,
  "objects_by_type": {
    "FUNCTION": 146,
    "PROCEDURE": 196,
    "PACKAGE_SPEC": 589,
    "PACKAGE_BODY": 569,
    "TRIGGER": 87
  },
  "objects": [
    {
      "object_id": "obj_0001",
      "object_name": "VALIDAR_EMAIL",
      "object_type": "FUNCTION",
      "source_file": "functions.sql",
      "line_start": 1,
      "line_end": 25,
      "char_start": 0,
      "char_end": 543,
      "code_length": 543,
      "status": "pending"
    },
    {
      "object_id": "obj_0002",
      "object_name": "PKG_VENTAS.CALCULAR_DESCUENTO",
      "object_type": "PACKAGE_BODY",
      "source_file": "packages_body.sql",
      "line_start": 1234,
      "line_end": 1456,
      "char_start": 45678,
      "char_end": 52341,
      "code_length": 6663,
      "status": "processed",
      "processed_at": "2025-01-05T12:30:00"
    }
  ]
}
```

### 2. Progress (`sql/extracted/progress.json`)

**Propósito:** Estado actual del procesamiento

**Contiene:**
- Contadores de objetos procesados/pendientes
- Último batch completado
- Último objeto procesado
- Historial de batches

**Ejemplo:**
```json
{
  "initialized_at": "2025-01-05T10:00:00",
  "last_updated": "2025-01-05T15:30:00",
  "total_objects": 8122,
  "processed_count": 2400,
  "pending_count": 5722,
  "current_batch": "batch_012",
  "last_object_processed": "obj_2400",
  "status": "in_progress",
  "batches": [
    {
      "batch_id": "batch_001",
      "processed_count": 200,
      "completed_at": "2025-01-05T10:30:00"
    },
    {
      "batch_id": "batch_002",
      "processed_count": 200,
      "completed_at": "2025-01-05T11:00:00"
    }
  ]
}
```

### 3. Outputs Detectables (`knowledge/json/batch_XXX/`)

**Propósito:** Los sub-agentes generan outputs con IDs únicos

**Patrón:**
- Archivo: `obj_0001_VALIDAR_EMAIL.json`
- Si existe → objeto ya procesado
- Si no existe → objeto pendiente

**Ejemplo estructura:**
```
knowledge/
├── json/
│   ├── batch_001/
│   │   ├── obj_0001_VALIDAR_EMAIL.json
│   │   ├── obj_0002_CALCULAR_DESCUENTO.json
│   │   └── ...
│   ├── batch_002/
│   │   ├── obj_0201_GENERAR_REPORTE.json
│   │   └── ...
└── ...
```

---

## 🔄 Flujo de Trabajo Completo

### Paso 1: Preparación Inicial (Una sola vez)

```bash
# Ejecutar script de preparación
python scripts/prepare_migration.py
```

**Este script:**
1. ✅ Parsea archivos SQL grandes (functions.sql, packages_body.sql, etc.)
2. ✅ Extrae posición exacta de cada objeto
3. ✅ Genera `manifest.json` con 8,122 objetos indexados
4. ✅ Crea `progress.json` en estado inicial
5. ✅ Genera instrucciones para Batch 1

**Output:**
```
📖 Parseando functions.sql...
  ✅ Encontrados 146 objetos de tipo FUNCTION

📖 Parseando procedures.sql...
  ✅ Encontrados 196 objetos de tipo PROCEDURE

📖 Parseando packages_spec.sql...
  ✅ Encontrados 589 objetos de tipo PACKAGE_SPEC

📖 Parseando packages_body.sql...
  ✅ Encontrados 569 objetos de tipo PACKAGE_BODY

📖 Parseando triggers.sql...
  ✅ Encontrados 87 objetos de tipo TRIGGER

✅ Manifest generado: sql/extracted/manifest.json
   Total objetos: 8122
   - FUNCTION: 146
   - PROCEDURE: 196
   - PACKAGE_SPEC: 589
   - PACKAGE_BODY: 569
   - TRIGGER: 87

📦 Batch: batch_001
   Objetos: 1 - 200
   Total en batch: 200
   Progreso: 200/8122 (2.5%)

================================================================================
INSTRUCCIONES PARA CLAUDE CODE
================================================================================

Lanzar 20 agentes plsql-analyzer en paralelo para procesar batch_001:

```
# Agente 1: Objetos obj_0001 a obj_0010
Task plsql-analyzer "Analizar objetos obj_0001 a obj_0010 del batch_001"

# Agente 2: Objetos obj_0011 a obj_0020
Task plsql-analyzer "Analizar objetos obj_0011 a obj_0020 del batch_001"

...

# Agente 20: Objetos obj_0191 a obj_0200
Task plsql-analyzer "Analizar objetos obj_0191 a obj_0200 del batch_001"
```

Después de completar el batch, ejecuta:
```bash
python scripts/update_progress.py batch_001
```
```

### Paso 2: Procesar Batch en Claude Code

**Copiar y pegar las instrucciones generadas:**

```
Lanzar 20 agentes plsql-analyzer en paralelo para batch_001:

# Agente 1
Task plsql-analyzer "Analizar objetos obj_0001 a obj_0010 del batch_001"

# Agente 2
Task plsql-analyzer "Analizar objetos obj_0011 a obj_0020 del batch_001"

...
```

**Los sub-agentes:**
1. ✅ Leen `manifest.json` para obtener metadata de objetos
2. ✅ Extraen código desde posiciones especificadas
3. ✅ Analizan y generan outputs en `knowledge/json/batch_001/`
4. ✅ Cada output tiene ID único: `obj_0001_VALIDAR_EMAIL.json`

### Paso 3: Actualizar Progreso

```bash
# Después de que todos los agentes terminen
python scripts/update_progress.py batch_001
```

**Este script:**
1. ✅ Busca outputs en `knowledge/json/batch_001/`
2. ✅ Detecta qué objetos fueron procesados (archivos existen)
3. ✅ Actualiza `manifest.json` (marca objetos como "processed")
4. ✅ Actualiza `progress.json` (contadores, último batch)
5. ✅ Genera instrucciones para **batch_002**

**Output:**
```
🔍 Detectando objetos procesados en batch_001...

  ✅ Encontrados 200 objetos procesados
     Primero: obj_0001
     Último: obj_0200

📝 Actualizando manifest...

  ✅ Actualizados 200 objetos en manifest

📊 Actualizando progreso...

  ✅ Progreso actualizado:
     Procesados: 200/8122
     Pendientes: 7922
     Porcentaje: 2.5%

================================================================================
PRÓXIMO BATCH
================================================================================

📦 Próximo batch: batch_002
   Objetos pendientes: 7922
   Objetos en este batch: 200
   Progreso después: 400/8122

================================================================================
INSTRUCCIONES PARA CLAUDE CODE
================================================================================

Lanzar 20 agentes plsql-analyzer en paralelo para procesar batch_002:

```
# Agente 1: Objetos obj_0201 a obj_0210
Task plsql-analyzer "Analizar objetos obj_0201 a obj_0210 del batch_002"

...
```
```

### Paso 4: Repetir hasta Completar

**Ciclo:**
```
1. Ejecutar batch en Claude Code (20 agentes paralelos)
   ↓
2. Ejecutar update_progress.py
   ↓
3. Copiar nuevas instrucciones
   ↓
4. Repetir
```

**Total batches:** 42 (8,122 objetos ÷ 200 por batch = 41.1)

**Tiempo estimado:** 5 horas (1 sesión de Claude Code Pro)

---

## 🔄 Reanudación Automática

### Escenario 1: Sesión Claude Code se cierra

**Sin problema:**
```bash
# Simplemente ejecutar update_progress.py con último batch
python scripts/update_progress.py batch_005

# El script:
# - Detecta qué objetos YA fueron procesados
# - Actualiza progress.json
# - Genera instrucciones para batch_006 (próximo pendiente)
```

**Resultado:** Continúas desde donde quedaste, sin reprocesar nada.

### Escenario 2: Llegas al límite de mensajes

**Sin problema:**
```bash
# Espera 5 horas para reset de límite
# Cuando vuelvas, ejecuta:
python scripts/update_progress.py batch_012

# Genera automáticamente instrucciones para batch_013
```

### Escenario 3: Error en batch (algunos agentes fallaron)

**Detección inteligente:**
```bash
python scripts/update_progress.py batch_003

# Output:
🔍 Detectando objetos procesados en batch_003...

  ⚠️ Encontrados 180 objetos procesados (esperados: 200)
     Primero: obj_0401
     Último: obj_0580
     Faltantes: 20 objetos

📝 Actualizando manifest...

  ✅ Actualizados 180 objetos en manifest

📊 Actualizando progreso...

  ✅ Progreso actualizado:
     Procesados: 580/8122
     Pendientes: 7542
     Porcentaje: 7.1%
```

**Solución:** El próximo batch incluirá los objetos faltantes automáticamente (porque siguen con status "pending").

### Escenario 4: Re-procesar objetos específicos

**Modificar manualmente manifest.json:**
```bash
# Buscar objeto en manifest.json
# Cambiar "status": "processed" → "status": "pending"
# Ejecutar update_progress.py

# El objeto volverá a ser incluido en próximo batch
```

---

## 📊 Verificación de Progreso

### Ver estado actual

```bash
# Ver progreso global
cat sql/extracted/progress.json | jq '.processed_count, .pending_count'

# Output:
# 2400
# 5722

# Ver porcentaje completado
cat sql/extracted/progress.json | jq '(.processed_count / .total_objects * 100)'

# Output:
# 29.54
```

### Ver objetos de un batch específico

```bash
# Ver qué objetos se procesaron en batch_005
ls knowledge/json/batch_005/ | head -20

# Output:
# obj_0801_PKG_VENTAS.json
# obj_0802_CALCULAR_IMPUESTO.json
# ...
```

### Ver objetos pendientes

```bash
# Contar objetos pendientes
cat sql/extracted/manifest.json | jq '[.objects[] | select(.status == "pending")] | length'

# Output:
# 5722

# Ver primeros 10 objetos pendientes
cat sql/extracted/manifest.json | jq '[.objects[] | select(.status == "pending")][0:10] | .[] | .object_id'

# Output:
# "obj_2401"
# "obj_2402"
# ...
```

---

## 🎯 Sub-agentes: Cómo Leen el Manifest

Los sub-agentes tienen acceso a herramientas Read, Grep, Glob.

**Ejemplo prompt para sub-agente:**

```
Analizar objetos obj_0001 a obj_0010 del batch_001

Para cada objeto:
1. Lee manifest: sql/extracted/manifest.json
2. Busca objeto por object_id
3. Extrae metadata: source_file, line_start, line_end
4. Lee código desde source_file entre line_start y line_end
5. Analiza código
6. Genera output: knowledge/json/batch_001/obj_XXXX_NOMBRE.json
```

**El sub-agente ejecuta:**
```python
# Pseudo-código de lo que hace el sub-agente

# 1. Leer manifest
manifest = read_json("sql/extracted/manifest.json")

# 2. Buscar objeto
for obj in manifest["objects"]:
    if obj["object_id"] in ["obj_0001", "obj_0002", ...]:

        # 3. Extraer metadata
        source_file = obj["source_file"]
        line_start = obj["line_start"]
        line_end = obj["line_end"]

        # 4. Leer código
        code = read_file_lines(f"sql/extracted/{source_file}", line_start, line_end)

        # 5. Analizar código
        analysis = analyze_plsql(code)

        # 6. Guardar output
        output_path = f"knowledge/json/batch_001/{obj['object_id']}_{obj['object_name']}.json"
        write_json(output_path, analysis)
```

---

## ✅ Ventajas del Sistema

1. **Reanudación automática** - Siempre sabes desde dónde continuar
2. **Tolerante a fallos** - Objetos faltantes se re-procesan automáticamente
3. **Verificable** - Outputs con IDs únicos detectables
4. **Escalable** - Mismo mecanismo para 8,122 o 100,000 objetos
5. **Transparente** - Progreso visible en todo momento
6. **Sin duplicados** - Objetos procesados nunca se re-procesan
7. **Paralelo seguro** - 20 agentes pueden trabajar simultáneamente sin conflictos

---

## 🚀 Inicio Rápido

```bash
# 1. Preparar migración (una sola vez)
python scripts/prepare_migration.py

# 2. Copiar instrucciones generadas y ejecutar en Claude Code
# (Lanzar 20 agentes en paralelo)

# 3. Actualizar progreso
python scripts/update_progress.py batch_001

# 4. Repetir pasos 2-3 hasta completar
```

**¡Listo para procesar 8,122 objetos de forma resiliente!** 🎉
