# Guía de Migración Oracle → PostgreSQL

**Plugin:** oracle-postgres-migration v1.0
**Objetivo:** Migrar 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4
**Última Actualización:** 2026-01-10

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Qué Se Migra](#qué-se-migra)
3. [Las 4 Fases de Migración](#las-4-fases-de-migración)
4. [Sistema de Progreso y Reanudación](#sistema-de-progreso-y-reanudación)
5. [Timeline y Capacidad](#timeline-y-capacidad)
6. [Comandos de Ejecución](#comandos-de-ejecución)

---

## 🎯 Visión General

### Objetivo

Migrar 8,122 objetos PL/SQL usando Claude Code Pro ($20/mes) mediante un flujo estructurado de 4 fases con tracking automático y capacidad de reanudación.

### Estado Actual del Proyecto

```
✅ COMPLETADO:
- Extracción de 8,122 objetos PL/SQL desde Oracle
- Conversión de DDL con ora2pg
- DDL ejecutado en PostgreSQL
- Sistema de parsing y validación (v2.1)

⏳ SIGUIENTE:
- FASE 1: Análisis y clasificación de objetos
- FASE 2: Conversión de código
- FASE 3: Validación de compilación
- FASE 4: Shadow testing
```

### Capacidades Confirmadas

**Experimentación (2025-01-05):**
- ✅ 20 sub-agentes en paralelo funcionan correctamente
- ✅ 1 mensaje puede procesar 200 objetos (20 × 10)
- ✅ 172,383 líneas procesadas exitosamente

**Límites Claude Code Pro:**
- ~45-60 mensajes cada 5 horas
- 200K tokens de contexto por mensaje
- Modelo: Claude Sonnet 4.5

---

## 📊 Qué Se Migra

### Dos Categorías de Objetos

```
Total: 8,122 objetos
├── EJECUTABLES (1,726) - Se convierten con Claude/ora2pg
│   ├── FUNCTIONS: 146
│   ├── PROCEDURES: 196
│   ├── PACKAGE_SPEC: 581
│   ├── PACKAGE_BODY: 569
│   ├── TRIGGERS: 87
│   ├── VIEWS: 147
│   └── MVIEWS: 3
│
└── REFERENCIA (4,049) - Solo contexto (ya convertidos)
    ├── TYPES: 830
    ├── TABLES: 2,525
    └── SEQUENCES: 694
```

### EJECUTABLES - Se Convierten

**Qué son:**
- Código PL/SQL que ejecuta lógica de negocio
- Functions, Procedures, Packages, Triggers

**Cómo se convierten:**
1. **SIMPLE** (~5,000): ora2pg (local, sin Claude)
2. **COMPLEX** (~3,122): Claude sub-agentes

**Clasificación SIMPLE vs COMPLEX:**

**COMPLEX** (requiere Claude):
- AUTONOMOUS_TRANSACTION
- UTL_HTTP / UTL_FILE
- DBMS_SQL (SQL dinámico)
- TABLE OF INDEX BY / VARRAY
- Variables de paquete globales
- Lógica muy compleja (50+ reglas)

**SIMPLE** (ora2pg automático):
- PL/SQL estándar
- Sin features Oracle avanzadas
- Conversión directa

### REFERENCIA - Solo Contexto

**Qué son:**
- DDL (TABLES, TYPES, SEQUENCES)
- Ya convertidos con ora2pg
- NO se procesan con Claude

**Por qué se incluyen:**
- El agente necesita saber qué tablas/tipos existen
- Para validar dependencias
- Para análisis de impacto

---

## 🔄 Las 4 Fases de Migración

### FASE 1: Análisis y Clasificación

**Duración:** 5 horas (1 sesión)
**Mensajes:** 42
**Costo tokens:** Incluido en suscripción Pro

**Objetivo:**
Analizar 8,122 objetos y clasificarlos en SIMPLE vs COMPLEX

**Input:**
```
sql/extracted/
├── functions.sql
├── procedures.sql
├── packages_spec.sql
├── packages_body.sql
├── triggers.sql
├── views.sql
└── materialized_views.sql
```

**Proceso:**
1. Lanzar 20 agentes `plsql-analyzer` en paralelo
2. Cada agente analiza 10 objetos
3. Por mensaje: 200 objetos procesados
4. Total: 42 mensajes para 8,122 objetos

**Output:**
```
knowledge/
├── json/                    ← Para pgvector (búsqueda semántica)
│   └── batch_XXX/
│       └── obj_XXX_[nombre].json
├── markdown/                ← Para lectura humana
│   └── batch_XXX/
│       └── obj_XXX_[nombre].md
└── classification/
    ├── simple_objects.txt   (~5,000 objetos)
    ├── complex_objects.txt  (~3,122 objetos)
    └── summary.json
```

**Comando de Inicio:**
```bash
# En Claude Code
"Quiero iniciar FASE 1 de la migración.
Lanza 20 agentes plsql-analyzer en paralelo para batch_001 (objetos 1-200).
Lee manifest desde sql/extracted/manifest.json."
```

---

### FASE 2A: Conversión Simple (LOCAL)

**Duración:** 30 minutos
**Costo tokens:** 0 (se ejecuta localmente, sin Claude)

**Input:** `classification/simple_objects.txt` (~5,000 objetos)

**Proceso:**
1. Ejecutar script local:
```bash
bash scripts/convert_simple_objects.sh
```

2. ora2pg convierte automáticamente
3. TÚ ejecutas, NO Claude

**Output:**
```
migrated/simple/
├── functions/*.sql
├── procedures/*.sql
├── packages/*.sql
└── triggers/*.sql
```

**Ventaja:** Ahorra tokens al no usar Claude para objetos simples

---

### FASE 2B: Conversión Compleja

**Duración:** 5 horas (1 sesión)
**Mensajes:** 16
**Costo tokens:** Incluido en suscripción Pro

**Input:** `classification/complex_objects.txt` (~3,122 objetos)

**Proceso:**
1. Lanzar 20 agentes `plsql-converter` en paralelo
2. Cada agente convierte 10 objetos complejos
3. Por mensaje: 200 objetos procesados
4. Total: 16 mensajes para 3,122 objetos

**Estrategias de Conversión:**

**AUTONOMOUS_TRANSACTION:**
```sql
-- Oracle
PRAGMA AUTONOMOUS_TRANSACTION;

-- PostgreSQL (dblink)
PERFORM dblink_exec('dbname=mydb', 'BEGIN ... END;');
```

**UTL_HTTP:**
```sql
-- Oracle
UTL_HTTP.REQUEST('http://api.example.com')

-- PostgreSQL (Lambda wrapper)
SELECT http_request('GET', 'http://api.example.com');
```

**TABLE OF INDEX BY:**
```sql
-- Oracle
TYPE t_array IS TABLE OF VARCHAR2(100) INDEX BY BINARY_INTEGER;

-- PostgreSQL
v_array VARCHAR(100)[];  -- Array nativo
```

**Variables de Paquete:**
```sql
-- Oracle
v_global := 'value';

-- PostgreSQL (session variables)
PERFORM set_config('pkg.v_global', 'value', false);
v_global := current_setting('pkg.v_global');
```

**Output:**
```
migrated/complex/
├── functions/*.sql
├── procedures/*.sql
└── packages/*.sql

conversion_log/
└── [objeto].md  ← Documentación de cambios
```

---

### FASE 3: Validación de Compilación

**Duración:** 5 horas (1 sesión)
**Mensajes:** 42
**Conexión requerida:** PostgreSQL 17.4

**Input:** `migrated/{simple,complex}/*.sql`

**Proceso:**
1. Lanzar 20 agentes `compilation-validator` en paralelo
2. Cada agente valida 10 objetos
3. Conecta a PostgreSQL y ejecuta scripts
4. Por mensaje: 200 objetos validados

**Output:**
```
compilation_results/
├── success/
│   └── [objeto].log  ← Compilación exitosa
└── errors/
    └── [objeto].log  ← Errores a corregir
```

**Criterio de éxito:** >95% compilación exitosa

---

### FASE 4: Shadow Testing

**Duración:** 10 horas (2 sesiones)
**Mensajes:** 84
**Conexión requerida:** Oracle + PostgreSQL

**Input:** `compilation_results/success/*.log`

**Proceso:**
1. Lanzar 10 agentes `shadow-tester` en paralelo
2. Cada agente testea 5 objetos
3. Ejecuta en Oracle y PostgreSQL con mismos datos
4. Compara resultados

**Output:**
```
shadow_tests/
└── [objeto].json  ← Comparación Oracle vs PostgreSQL
```

**Estructura del resultado:**
```json
{
  "object_name": "MY_FUNCTION",
  "test_cases": 10,
  "oracle_results": [...],
  "postgres_results": [...],
  "differences": [],
  "match_percentage": 98.5,
  "status": "PASS"
}
```

**Criterio de éxito:** >95% resultados idénticos

---

## 🔄 Sistema de Progreso y Reanudación

### El Problema

**Límite de Claude Code Pro:**
- ~45-60 mensajes cada 5 horas
- Para 8,122 objetos necesitamos ~184 mensajes
- Requiere múltiples sesiones (5-6 sesiones)

**Pregunta:** ¿Cómo sabemos dónde continuar después de un límite de sesión?

### La Solución: Manifest + Progress

#### 1. Manifest (manifest.json)

**Propósito:** Índice completo de todos los objetos con posiciones exactas

**Generado por:** `scripts/prepare_migration.py`

**Estructura:**
```json
{
  "generated_at": "2026-01-10T12:45:02",
  "version": "2.1",
  "total_objects": 5775,
  "executable_count": 1726,
  "reference_count": 4049,
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
      "status": "pending"
    }
  ]
}
```

#### 2. Progress (progress.json)

**Propósito:** Estado actual del procesamiento

**Actualizado por:** Los agentes automáticamente

**Estructura:**
```json
{
  "initialized_at": "2026-01-10T10:00:00",
  "last_updated": "2026-01-10T15:30:00",
  "total_objects": 5775,
  "processed_count": 2000,
  "pending_count": 3775,
  "current_batch": "batch_011",
  "last_object_processed": "obj_2000",
  "status": "in_progress",
  "batches": [
    {
      "batch_id": "batch_001",
      "objects_range": "1-200",
      "status": "completed",
      "completed_at": "2026-01-10T11:00:00"
    },
    {
      "batch_id": "batch_011",
      "objects_range": "2001-2200",
      "status": "in_progress"
    }
  ]
}
```

### Flujo de Reanudación

```
Sesión 1 (45 mensajes):
  ↓ Procesar batch_001 a batch_045 (9,000 objetos)
  ↓ Actualizar progress.json
  ↓ LÍMITE ALCANZADO

Esperar 5 horas ⏱️

Sesión 2 (45 mensajes):
  ↓ Leer progress.json → last_batch = "batch_045"
  ↓ Continuar desde batch_046
  ↓ NO reprocesar objetos ya completados ✅
```

### Detección Automática

**Los agentes detectan automáticamente:**
1. Si `progress.json` existe
2. Qué batch procesar siguiente
3. Qué objetos ya están completados
4. Actualizar progreso al terminar

**Tú solo dices:**
```
"Continúa la migración desde donde quedó.
Lee progress.json para saber qué batch sigue."
```

---

## ⏱️ Timeline y Capacidad

### Resumen por Fase

| Fase | Objetos | Mensajes | Tiempo | Sesiones |
|------|---------|----------|--------|----------|
| 1. Análisis | 8,122 | 42 | 5h | 1 |
| 2A. Simple (local) | 5,000 | 0 | 30min | 0 |
| 2B. Compleja | 3,122 | 16 | 5h | 1 |
| 3. Validación | 8,122 | 42 | 5h | 1 |
| 4. Testing | 8,122 | 84 | 10h | 2 |
| **TOTAL** | **8,122** | **184** | **25.5h** | **5-6** |

### Distribución de Sesiones

```
Día 1 (Sesión 1 - 5h):
  ✅ FASE 1 completa (42 mensajes)

Día 1 (Local - 30min):
  ✅ FASE 2A completa (0 mensajes)

Día 2 (Sesión 2 - 5h):
  ✅ FASE 2B completa (16 mensajes)

Día 2 (Sesión 3 - 5h):
  ⏳ FASE 3 parcial (45 mensajes de 42)
  ✅ FASE 3 completa

Día 3 (Sesión 4 - 5h):
  ⏳ FASE 4 parcial (45 mensajes)

Día 3 (Sesión 5 - 5h):
  ⏳ FASE 4 parcial (39 mensajes)
  ✅ FASE 4 completa
```

**Duración total:** 3-4 días laborables (25.5 horas efectivas)

### Cálculo de Objetos por Mensaje

**Fase 1, 2B, 3:**
- 20 agentes × 10 objetos = 200 objetos/mensaje
- 8,122 objetos ÷ 200 = 42 mensajes

**Fase 4:**
- 10 agentes × 5 objetos = 50 objetos/mensaje
- 8,122 objetos ÷ 50 = 163 mensajes
- (Conservador porque testing es más lento)

---

## 🚀 Comandos de Ejecución

### Preparación (Una Sola Vez)

```bash
# 1. Generar manifest y progress
python scripts/prepare_migration.py

# 2. Validar parsing
python scripts/validate_parsing.py

# 3. Verificar archivos generados
ls -lh sql/extracted/manifest.json
ls -lh sql/extracted/progress.json
```

### Iniciar Fase 1

```bash
# En Claude Code:
"Quiero iniciar FASE 1 de la migración Oracle → PostgreSQL.
Lanza 20 agentes plsql-analyzer en paralelo para batch_001 (objetos 1-200).
Lee el manifest desde sql/extracted/manifest.json.
Al terminar, actualiza progress.json."
```

### Continuar Después de Límite

```bash
# Claude Code detecta automáticamente
"Continúa la migración FASE 1 desde donde quedó.
Lee progress.json para determinar el próximo batch."
```

### Ejecutar Fase 2A (Local)

```bash
# Sin Claude - ejecutas tú
bash scripts/convert_simple_objects.sh
```

### Iniciar Fase 2B

```bash
"Iniciar FASE 2B: Conversión de objetos complejos.
Leer classification/complex_objects.txt.
Lanzar 20 agentes plsql-converter en paralelo para batch_001."
```

---

## ✅ Criterios de Éxito

| Fase | Criterio | Objetivo |
|------|----------|----------|
| 1. Análisis | Objetos analizados | 100% |
| 1. Análisis | Clasificación | SIMPLE + COMPLEX = 100% |
| 2. Conversión | Código generado | 100% |
| 3. Validación | Compilación exitosa | >95% |
| 4. Testing | Resultados idénticos | >95% |

---

## 🔗 Documentación Relacionada

- **[COMANDOS.md](COMANDOS.md)** - Referencia completa de comandos
- **[DESARROLLO.md](DESARROLLO.md)** - Arquitectura y decisiones técnicas
- **[QUICKSTART.md](../QUICKSTART.md)** - Inicio rápido (5 minutos)
- **[README.md](../README.md)** - Índice principal

---

**Última Actualización:** 2026-01-10
**Versión del Plugin:** 1.0
**Autor:** Claude Sonnet 4.5
