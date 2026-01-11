# Guía de Desarrollo del Plugin

**Plugin:** oracle-postgres-migration v1.0
**Para:** Desarrolladores que mantienen/extienden el plugin
**Última Actualización:** 2026-01-10

---

## 📋 Tabla de Contenidos

1. [Arquitectura del Plugin](#arquitectura-del-plugin)
2. [Sistema de Parsing](#sistema-de-parsing)
3. [Procesamiento de Objetos](#procesamiento-de-objetos)
4. [Extender el Plugin](#extender-el-plugin)
5. [Testing y Validación](#testing-y-validación)

---

## 🏗️ Arquitectura del Plugin

### Filosofía de Diseño

**Principios Fundamentales:**

1. **Especialización por Fase**
   - Cada agente maneja una fase específica
   - No mezclar análisis con conversión
   - Outputs claros y estructurados

2. **Procesamiento Masivo por Lotes**
   - 10-20 objetos por agente
   - 20 agentes en paralelo
   - Máxima eficiencia de tokens

3. **Reanudación Automática**
   - Manifest indexa todos los objetos
   - Progress rastrea qué se procesó
   - Tolerante a límites de sesión

4. **Sin Estado entre Agentes**
   - Cada agente es independiente
   - Outputs en archivos, no en memoria
   - Paralelismo sin coordinación

### Por Qué 4 Agentes Especializados

#### Alternativa Descartada: 1 Agente Generalista

```
❌ 1 agente que hace todo:
   - Analizar
   - Convertir
   - Validar
   - Testear

Problemas:
- System prompt demasiado largo (>10K tokens)
- Confusión entre fases
- Difícil de mantener
- Prompt genérico = resultados mediocres
```

#### Solución: 4 Agentes Especializados

```
✅ plsql-analyzer (Fase 1)
   - System prompt especializado en análisis
   - Detecta features Oracle
   - Clasifica SIMPLE vs COMPLEX
   - Output: JSON + Markdown

✅ plsql-converter (Fase 2B)
   - System prompt especializado en conversión
   - Conoce patrones de migración
   - Estrategias por feature Oracle
   - Output: Código PL/pgSQL + Documentación

✅ compilation-validator (Fase 3)
   - System prompt especializado en validación
   - Ejecuta en PostgreSQL
   - Captura errores de compilación
   - Output: Logs de compilación

✅ shadow-tester (Fase 4)
   - System prompt especializado en testing
   - Ejecuta en Oracle + PostgreSQL
   - Compara resultados
   - Output: JSON de comparación
```

**Ventajas:**
- ✅ System prompts enfocados (1-2K tokens cada uno)
- ✅ Mejor calidad en cada fase
- ✅ Fácil mantener/actualizar cada agente
- ✅ Reutilizables en otros proyectos

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                   USUARIO (Ingeniero)                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Ejecuta comandos
                      ▼
           ┌──────────────────────┐
           │   Claude Code CLI    │
           │  (o Web/Desktop)     │
           └──────────┬───────────┘
                      │
                      │ Carga plugin
                      ▼
       ┌──────────────────────────────────┐
       │   oracle-postgres-migration      │
       │         (Plugin)                 │
       ├──────────────────────────────────┤
       │  - 4 agentes en agents/          │
       │  - Scripts en scripts/           │
       │  - Docs en docs/                 │
       └──────────┬───────────────────────┘
                  │
                  │ Invoca agentes
                  ▼
    ┌─────────────────────────────────────┐
    │        Sub-agentes Paralelos        │
    ├─────────────────────────────────────┤
    │  plsql-analyzer (20 en paralelo)    │
    │  plsql-converter (20 en paralelo)   │
    │  compilation-validator (20)         │
    │  shadow-tester (10)                 │
    └─────────────┬───────────────────────┘
                  │
                  │ Procesa
                  ▼
    ┌─────────────────────────────────────┐
    │      Archivos en Proyecto           │
    ├─────────────────────────────────────┤
    │  INPUT:                             │
    │  - sql/extracted/*.sql              │
    │  - sql/extracted/manifest.json      │
    │  - sql/extracted/progress.json      │
    │                                     │
    │  OUTPUT:                            │
    │  - knowledge/json/                  │
    │  - knowledge/markdown/              │
    │  - migrated/simple/                 │
    │  - migrated/complex/                │
    │  - compilation_results/             │
    │  - shadow_tests/                    │
    └─────────────────────────────────────┘
```

### Decisiones Técnicas Críticas

#### 1. Manifest como Índice Central

**Problema:** ¿Cómo saber qué objetos procesar y dónde están?

**Solución:** `manifest.json` generado por parsing inicial

**Ventajas:**
- ✅ Una sola fuente de verdad
- ✅ Posiciones exactas (line_start, line_end)
- ✅ Metadata de cada objeto
- ✅ Permite paralelismo (cada agente lee índice)

**Alternativa descartada:**
- ❌ Leer archivos SQL directamente en cada agente
- Problema: Redundancia, difícil paralelizar

#### 2. Progress Tracking Externo

**Problema:** ¿Cómo saber qué ya se procesó?

**Solución:** `progress.json` actualizado por agentes

**Ventajas:**
- ✅ Reanudación automática
- ✅ Tolerante a límites de sesión
- ✅ Sin reprocesar objetos

**Alternativa descartada:**
- ❌ Estado en memoria del agente
- Problema: Se pierde al terminar sesión

#### 3. Outputs Estructurados

**Problema:** ¿Cómo preservar el conocimiento extraído?

**Solución:** Dual output JSON + Markdown

**Ventajas:**
- ✅ JSON → pgvector (búsqueda semántica)
- ✅ Markdown → Humanos/IA (legible)
- ✅ Fácil de procesar/consultar

**Alternativa descartada:**
- ❌ Solo comentarios en código
- Problema: Difícil buscar, no estructurado

---

## 🔧 Sistema de Parsing

### Visión General

**Propósito:** Extraer objetos PL/SQL individuales de archivos SQL grandes

**Script:** `scripts/prepare_migration.py` (v2.1)

**Input:** Archivos SQL monolíticos (ej: `packages_body.sql` - 71MB)

**Output:** `manifest.json` con posiciones exactas de 5,775 objetos

### Desafíos del Parsing PL/SQL

#### 1. END Anidados

```sql
CREATE OR REPLACE FUNCTION MY_FUNC AS
BEGIN
  FOR i IN 1..10 LOOP     -- END LOOP; ← NO es el final
    IF i > 5 THEN         -- END IF; ← NO es el final
      CASE i
        WHEN 6 THEN NULL; -- END CASE; ← NO es el final
      END CASE;
    END IF;
  END LOOP;
  RETURN 1;
END MY_FUNC;              -- ✅ Este es el END correcto
/
```

#### 2. Nombres Diferentes en CREATE vs END

```sql
-- Común en TRIGGERS
CREATE OR REPLACE TRIGGER AGE_T_CONFIRMA_CITA_MAILING
  BEFORE INSERT ON RESERVAS
BEGIN
  ...
END AGE_T_LOG_MAILING;    -- ← Nombre diferente!
/
```

#### 3. Procedimientos Internos en Packages

```sql
CREATE OR REPLACE PACKAGE BODY MY_PKG AS
  PROCEDURE PROC1 AS
  BEGIN
    ...
  END PROC1;              -- ← NO es el final del package

  PROCEDURE PROC2 AS
  BEGIN
    ...
  END PROC2;              -- ← NO es el final del package

END MY_PKG;               -- ✅ Este es el END correcto
/
```

### Las 5 Estrategias de Detección

El parser usa 5 estrategias en orden de preferencia:

#### Estrategia 1: Nombre Exacto (Más Confiable)

```python
pattern = rf'END\s+{re.escape(object_name)}\s*;'
```

**Ejemplo:**
```sql
CREATE OR REPLACE FUNCTION FAC_F_CALCULA ...
END FAC_F_CALCULA;        -- ✅ Match
```

**Uso:** Mayoría de FUNCTIONS, PROCEDURES, PACKAGES
**Confiabilidad:** ⭐⭐⭐⭐⭐

#### Estrategia 2: TRIGGER con Cualquier Nombre (v2.1)

```python
pattern = r'END\s+\w+\s*;\s*\n\s*/\s*(?=\n|$)'
```

**Ejemplo:**
```sql
CREATE OR REPLACE TRIGGER AGE_T_X ...
END AGE_T_Y;              -- ✅ Match (nombre diferente OK)
/
```

**Uso:** TRIGGERS (17 casos en phantomx-nexus)
**Confiabilidad:** ⭐⭐⭐⭐
**Novedad:** Agregado en v2.1 para solucionar triggers con nombres diferentes

#### Estrategia 3: END Sin Nombre

```python
pattern = r'(?<!LOOP\s)(?<!IF\s)END\s*;'
```

**Ejemplo:**
```sql
CREATE OR REPLACE FUNCTION MY_FUNC AS
BEGIN
  ...
END;                      -- ✅ Match (sin nombre)
```

**Uso:** FUNCTIONS/PROCEDURES que no usan nombre en END
**Confiabilidad:** ⭐⭐⭐

**Limitación:** Lookbehind débil, puede fallar con espacios variables

#### Estrategia 4: Último END en Rango

**Uso:** PACKAGES sin nombre en END

**Confiabilidad:** ⭐⭐

#### Estrategia 5: Fallback

**Uso:** Solo cuando todas las estrategias anteriores fallan

**Confiabilidad:** ⭐

**Impacto:** Puede capturar comentarios/metadata del siguiente objeto

### Estructura de manifest.json

```json
{
  "generated_at": "2026-01-10T12:45:02",
  "version": "2.1",
  "total_objects": 5775,
  "executable_count": 1726,
  "reference_count": 4049,
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

### Validación del Parsing

**Script:** `scripts/validate_parsing.py`

**Validaciones:**
1. `line_start < line_end`
2. `char_start < char_end`
3. Código inicia con `CREATE`
4. PL/SQL termina con `/`
5. DDL termina con `;`

**Criterios de Aprobación:**
- >85% objetos válidos ✅
- <5% warnings ✅
- 0 errores críticos en EJECUTABLES ✅

**Resultados v2.1:**
```
EJECUTABLES: 1,726 objetos
  ✅ Valid: 1,557 (90.2%)
  ⚠️  Warning: 19 (1.1%)
  ❌ Errores: 0

REFERENCIA: 4,049 objetos
  (No críticos - ya convertidos con ora2pg)
```

---

## 📊 Procesamiento de Objetos

### Categorías de Objetos

#### EJECUTABLES (Se Convierten)

**Definición:** Código PL/SQL que ejecuta lógica de negocio

**Tipos:**
- FUNCTION
- PROCEDURE
- PACKAGE_SPEC
- PACKAGE_BODY
- TRIGGER
- VIEW (con lógica compleja)
- MVIEW

**Procesamiento:**
1. Análisis con `plsql-analyzer`
2. Clasificación SIMPLE vs COMPLEX
3. Conversión con ora2pg (SIMPLE) o Claude (COMPLEX)
4. Validación de compilación
5. Shadow testing

**Metadata en manifest.json:**
```json
{
  "category": "EXECUTABLE",
  "validation_status": "valid",
  "parsing_method": "exact_name_semicolon"
}
```

#### REFERENCIA (Solo Contexto)

**Definición:** DDL ya convertido con ora2pg, incluido para contexto

**Tipos:**
- TYPE
- TABLE
- SEQUENCE
- PRIMARY_KEY
- FOREIGN_KEY
- INDEX

**Procesamiento:**
1. Indexado en `manifest.json`
2. NO se analizan con Claude
3. Disponibles para agentes como contexto

**Por qué se incluyen:**
- El agente necesita saber qué tablas existen
- Para validar dependencias (`SELECT FROM tabla_x`)
- Para analizar tipos de datos (`TYPE t_record`)

**Metadata en manifest.json:**
```json
{
  "category": "REFERENCE",
  "status": "reference_only",
  "note": "Convertido por ora2pg - Incluido como contexto"
}
```

### Flujo de Datos

```
1. EXTRACCIÓN (Manual desde Oracle)
   ↓
   sql/extracted/*.sql

2. PARSING (prepare_migration.py)
   ↓
   sql/extracted/manifest.json

3. ANÁLISIS (plsql-analyzer)
   ↓
   knowledge/json/
   knowledge/markdown/
   classification/

4. CONVERSIÓN
   4A. ora2pg (local) → migrated/simple/
   4B. plsql-converter → migrated/complex/

5. VALIDACIÓN (compilation-validator)
   ↓
   compilation_results/

6. TESTING (shadow-tester)
   ↓
   shadow_tests/
```

---

## 🔌 Extender el Plugin

### Agregar un Nuevo Agente

**Ejemplo:** Crear agente para análisis de performance

#### 1. Crear archivo del agente

```markdown
<!-- .claude-plugin/agents/performance-analyzer.md -->
---
name: performance-analyzer
description: Analiza performance de queries SQL
color: orange
---

Eres un experto en optimización de SQL.

## Objetivo

Analizar queries en objetos PL/SQL y sugerir optimizaciones.

## Input

Recibirás un objeto PL/SQL con queries SQL embebidas.

## Output

Genera un JSON con:
- Queries detectadas
- Índices recomendados
- Estimación de mejora
```

#### 2. Registrar en plugin.json

```json
{
  "agents": [
    "plsql-analyzer",
    "plsql-converter",
    "compilation-validator",
    "shadow-tester",
    "performance-analyzer"
  ]
}
```

#### 3. Invocar desde Claude Code

```bash
"Lanza 10 agentes performance-analyzer para analizar
los 100 objetos más consultados."
```

### Modificar Estrategia de Parsing

**Ejemplo:** Agregar soporte para SYNONYM

#### 1. Editar prepare_migration.py

```python
# Agregar nuevo tipo de objeto
elif object_type == "SYNONYM":
    pattern = r'CREATE\s+OR\s+REPLACE\s+SYNONYM\s+(\w+)'
    matches = list(re.finditer(pattern, content, re.IGNORECASE))

    for i, match in enumerate(matches):
        # ... lógica de extracción
```

#### 2. Agregar validación

```python
# En validate_extracted_code()
if object_type == "SYNONYM":
    if not re.match(r'^CREATE.*SYNONYM', code):
        return False, "No inicia con CREATE SYNONYM"
```

#### 3. Actualizar tests

```python
# scripts/test_parsing.py
def test_synonym_parsing():
    content = "CREATE SYNONYM my_syn FOR table_x;"
    result = parse_sql_file(content, "SYNONYM")
    assert len(result) == 1
    assert result[0]['object_type'] == "SYNONYM"
```

---

## ✅ Testing y Validación

### Testing del Parsing

**Script:** `scripts/validate_parsing.py`

```bash
# Validar todos los objetos
python scripts/validate_parsing.py

# Solo TRIGGERS
python scripts/validate_parsing.py --type TRIGGER

# Muestra aleatoria
python scripts/validate_parsing.py --sample 10
```

**Exit codes:**
- 0: Todo OK
- 1: Errores críticos encontrados

### Testing de Agentes

**Método:** Probar con subconjunto pequeño primero

```bash
# Test con 1 objeto
"Lanza 1 agente plsql-analyzer para obj_0001 solamente"

# Test con 10 objetos
"Lanza 1 agente plsql-analyzer para objetos 1-10"

# Producción
"Lanza 20 agentes plsql-analyzer para batch_001 (1-200)"
```

### Debugging

**Ver logs de parsing:**
```bash
cat sql/extracted/parsing_validation.log | python -m json.tool
```

**Ver objetos con warnings:**
```python
import json
manifest = json.load(open('sql/extracted/manifest.json'))
warnings = [obj for obj in manifest['objects']
            if obj.get('validation_status') == 'warning']
for obj in warnings:
    print(f"{obj['object_name']} - {obj.get('parsing_method')}")
```

**Extraer un objeto específico para análisis:**
```python
import json
manifest = json.load(open('sql/extracted/manifest.json'))
obj = next(o for o in manifest['objects'] if o['object_name'] == 'MY_FUNC')

with open(f"sql/extracted/{obj['source_file']}") as f:
    content = f.read()

code = content[obj['char_start']:obj['char_end']]
print(code)
```

---

## 🔗 Referencias

- **[GUIA_MIGRACION.md](GUIA_MIGRACION.md)** - Proceso de migración completo
- **[COMANDOS.md](COMANDOS.md)** - Referencia de comandos
- **[CLAUDE.md](../CLAUDE.md)** - Contexto completo para Claude
- **[README.md](../README.md)** - Índice principal

---

## 📝 Changelog

### v2.1 (2026-01-10)

**Parsing:**
- ✅ Nueva estrategia para TRIGGERS con nombres diferentes
- ✅ Reducción de warnings de 22 a 19 (-14%)
- ✅ 0 triggers con fallback (antes: 17)

**Documentación:**
- ✅ Consolidación en GUIA_MIGRACION.md + DESARROLLO.md
- ✅ Archivado de documentos obsoletos

### v2.0 (2026-01-06)

**Parsing:**
- Múltiples estrategias de detección de END
- Validación automática de código extraído
- Logging detallado de errores

### v1.0 (2026-01-05)

**Plugin:**
- 4 agentes especializados
- Sistema de tracking automático
- Experimentación de capacidad

---

**Última Actualización:** 2026-01-10
**Mantenedores:** Ver CLAUDE.md
**Contribuciones:** Ver repositorio del plugin
