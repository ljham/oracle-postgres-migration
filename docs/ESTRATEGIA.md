# Estrategia de Migración Oracle → PostgreSQL

**Proyecto:** phantomx-nexus
**Fecha de definición:** 2025-01-05
**Última actualización:** 2025-01-05
**Estado:** Estrategia definida - Lista para implementación
**Modelo:** Claude Sonnet 4.5 (Claude Code Pro)

---

## 🎯 Contexto del Proyecto

### Objetivo
Migrar 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora) usando **Claude Code CLI/Web con suscripción Pro ($20/mes)** - SIN usar API de Anthropic.

### Estado Actual
```
✅ COMPLETADO:
- Fase 0: Discovery y análisis de requisitos
- Extracción de 8,122 objetos PL/SQL desde Oracle (sql/extracted/)
- Conversión de DDL con ora2pg (sql/exported/)
- DDL ejecutado exitosamente en PostgreSQL

⏳ PENDIENTE:
- Migración de código PL/SQL → PL/pgSQL (functions, procedures, packages)
- Validación de compilación
- Shadow testing (Oracle vs PostgreSQL)
```

---

## 🔬 Experimentos Realizados (2025-01-05)

### Descubrimiento de Capacidades de Sub-agentes

**Test 1: 3 sub-agentes en paralelo**
- ✅ EXITOSO - Todos completaron sin errores

**Test 2: 10 sub-agentes en paralelo**
- ✅ EXITOSO - Procesaron 172,383 líneas de código

**Test 3: 20 sub-agentes en paralelo**
- ✅ EXITOSO - Todos los agentes completaron exitosamente

**Conclusión:**
- Claude Code soporta al menos 20 sub-agentes en paralelo
- 1 mensaje puede procesar 200+ objetos (20 sub-agentes × 10 objetos cada uno)
- Límite real mucho más alto de lo documentado oficialmente

### Límites de Suscripción Confirmados

**Claude Code Pro ($20/mes):**
- ~45-60 mensajes cada 5 horas (estimado)
- Contexto: 200K tokens por mensaje
- Contexto por sub-agente: 200K tokens (independiente)
- Sub-agentes en paralelo: 20+ confirmado experimentalmente

**IMPORTANTE:**
- Claude Code CLI y Web comparten los MISMOS límites
- El modelo a usar es Claude Sonnet 4.5 (suficiente para análisis de código)

---

## 🔄 Flujo de Migración en 4 Fases

### FASE 1: ANÁLISIS Y CLASIFICACIÓN (5 horas - 1 sesión)

**Objetivo:** Analizar 8,122 objetos y clasificarlos en SIMPLE vs COMPLEX

**Input:**
```
sql/extracted/
├── functions.sql (146 functions)
├── procedures.sql (196 procedures)
├── packages_spec.sql (589 package specs)
├── packages_body.sql (569 package bodies)
├── triggers.sql (87 triggers)
├── tables.sql (para análisis de dependencias)
├── foreign_keys.sql (para análisis de relaciones)
└── primary_keys.sql (para análisis de estructura)
```

**Proceso:**
- 20 sub-agentes "plsql-analyzer" en paralelo por mensaje
- 10 objetos por sub-agente = 200 objetos por mensaje
- 42 mensajes para 8,122 objetos
- Tiempo estimado: 5 horas (1 sesión)

**Output:**
```
knowledge/
├── json/               # Para base de datos vectorial (pgvector)
│   └── batch_XXX/
│       └── obj_XXX_[nombre].json
├── markdown/           # Para lectura humana/IA
│   └── batch_XXX/
│       └── obj_XXX_[nombre].md
└── classification/
    ├── simple_objects.txt (~5,000 objetos)
    ├── complex_objects.txt (~3,122 objetos)
    └── summary.json
```

**Criterios de Clasificación:**

**COMPLEX** (migrar con sub-agentes Claude):
- AUTONOMOUS_TRANSACTION
- UTL_HTTP
- UTL_FILE / DIRECTORY
- DBMS_SQL
- TABLE OF INDEX BY / VARRAY
- Motores de fórmulas dinámicas
- Lógica muy compleja (50+ reglas)

**SIMPLE** (migrar con ora2pg):
- Código estándar PL/SQL
- Sin features Oracle avanzadas
- Lógica directa y clara

---

### FASE 2A: CONVERSIÓN SIMPLE con ora2pg (30 minutos)

**Input:** classification/simple_objects.txt (~5,000 objetos)

**Proceso:**
- Ejecutar script bash local: `scripts/convert_simple_objects.sh`
- ora2pg convierte objetos automáticamente
- TÚ ejecutas localmente (no Claude)

**Output:**
```
migrated/simple/
├── functions/*.sql
├── procedures/*.sql
└── packages/*.sql
```

**Costo tokens Claude:** 0 ✅

---

### FASE 2B: CONVERSIÓN COMPLEJA con Sub-agentes (5 horas - 1 sesión)

**Input:** classification/complex_objects.txt (~3,122 objetos)

**Proceso:**
- 20 sub-agentes "plsql-converter" en paralelo por mensaje
- 10 objetos complejos por sub-agente = 200 objetos por mensaje
- 16 mensajes para 3,122 objetos
- Tiempo estimado: 5 horas (1 sesión)

**Estrategias de Conversión por Feature:**

**AUTONOMOUS_TRANSACTION:**
```sql
-- Oracle:
PRAGMA AUTONOMOUS_TRANSACTION;

-- PostgreSQL (opción dblink):
PERFORM dblink_exec('dbname=veris_dev', 'BEGIN ... END;');
```

**UTL_HTTP:**
```sql
-- Oracle:
UTL_HTTP.REQUEST('http://api.example.com')

-- PostgreSQL (wrapper + Lambda):
SELECT http_request('GET', 'http://api.example.com');
```

**TABLE OF INDEX BY:**
```sql
-- Oracle:
TYPE t_array IS TABLE OF VARCHAR2(100) INDEX BY BINARY_INTEGER;

-- PostgreSQL:
v_array VARCHAR(100)[]; -- Array nativo
```

**Variables de Paquete:**
```sql
-- Oracle:
v_global := 'value';

-- PostgreSQL:
PERFORM set_config('pkg_name.v_global', 'value', false);
v_global := current_setting('pkg_name.v_global');
```

**Output:**
```
migrated/complex/
├── functions/*.sql
├── procedures/*.sql
└── packages/*.sql

conversion_log/
└── [objeto].md (documentación de cambios)
```

---

### FASE 3: VALIDACIÓN DE COMPILACIÓN (5 horas - 1 sesión)

**Input:** migrated/{simple,complex}/**/*.sql (8,122 archivos)

**Proceso:**
- 20 sub-agentes "compilation-validator" en paralelo
- Conectan a PostgreSQL y ejecutan scripts
- Capturan errores y sugieren fixes
- 42 mensajes para validar 8,122 objetos

**Output:**
```
compilation_results/
├── success/*.log (objetos compilados OK)
└── errors/*.error (objetos con errores + fix sugerido)
```

---

### FASE 4: SHADOW TESTING (10 horas - 2 sesiones)

**Input:** compilation_results/success/*.log

**Proceso:**
- 10 sub-agentes "shadow-tester" en paralelo (más lento)
- Ejecutan mismo código en Oracle y PostgreSQL
- Comparan resultados
- 84 mensajes para testear 8,122 objetos

**Output:**
```
shadow_tests/
├── [objeto].json (comparación de resultados)
└── discrepancies.txt (diferencias encontradas)
```

**Criterio de Éxito:** >95% de objetos con resultados idénticos

---

## 📊 Timeline Completo

```
FASE 1: Análisis y Clasificación
├─ Sesión 1: 8,122 objetos analizados
├─ Tiempo: 5 horas
└─ Mensajes: 42

FASE 2A: Conversión Simple (ora2pg)
├─ Ejecución local: 5,000 objetos
├─ Tiempo: 30 minutos
└─ Mensajes: 0 ✅

FASE 2B: Conversión Compleja (sub-agentes)
├─ Sesión 2: 3,122 objetos convertidos
├─ Tiempo: 5 horas
└─ Mensajes: 16

FASE 3: Validación Compilación
├─ Sesión 3: 8,122 objetos validados
├─ Tiempo: 5 horas
└─ Mensajes: 42

FASE 4: Shadow Testing
├─ Sesiones 4-5: 8,122 objetos testeados
├─ Tiempo: 10 horas (2 sesiones)
└─ Mensajes: 84

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:
├─ Tiempo efectivo: 25.5 horas
├─ Sesiones de 5h: 5-6 sesiones
├─ Timeline calendario: 2-3 días
├─ Mensajes Claude: 184 de ~250 disponibles
└─ Margen: 66 mensajes para errores/iteraciones ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🗄️ Base de Datos Vectorial (pgvector)

### Objetivo
Almacenar conocimiento de cada objeto analizado para consulta por futuros agentes IA.

### Proceso en 2 Etapas

**Etapa 1: Sub-agentes guardan JSON (Durante análisis)**
- Sub-agentes guardan archivos JSON estructurados
- Campo `embedding_text` contiene resumen para embeddings

**Etapa 2: Script carga a pgvector (Después del análisis)**
```bash
python scripts/load_to_pgvector.py
```

Este script:
- Lee todos los JSON de knowledge/json/
- Genera embeddings con sentence-transformers (local, gratis)
- Carga a PostgreSQL con extensión pgvector
- Tiempo: ~15 minutos para 8,122 objetos

### Schema PostgreSQL

```sql
CREATE TABLE plsql_objects (
    id SERIAL PRIMARY KEY,
    object_id VARCHAR(50) UNIQUE,
    object_name VARCHAR(200),
    object_type VARCHAR(50),
    complexity VARCHAR(20),
    full_data JSONB,
    embedding vector(384)
);

CREATE TABLE business_rules (
    id SERIAL PRIMARY KEY,
    object_id VARCHAR(50) REFERENCES plsql_objects(object_id),
    rule_name TEXT,
    description TEXT,
    embedding vector(384)
);
```

### Búsqueda Semántica

```sql
-- Buscar objetos relacionados con "cálculo de nómina"
SELECT object_name,
       1 - (embedding <=> query_embedding) as similarity
FROM plsql_objects
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

---

## 🔧 Tecnologías y Herramientas

### Claude Code
- **Versión:** Claude Code CLI/Web
- **Suscripción:** Claude Code Pro ($20/mes)
- **Modelo:** Claude Sonnet 4.5
- **Límites:** ~50 mensajes cada 5 horas
- **Sub-agentes en paralelo:** 20 confirmado

### Herramientas Locales (GRATIS)
- **ora2pg:** Conversión automática de objetos SIMPLES
- **sentence-transformers:** Generación de embeddings locales
- **PostgreSQL 17.4 + pgvector:** Base de datos vectorial

### AWS (Ya configurado)
- **Aurora PostgreSQL 17.4:** Base de datos destino
- **S3:** Almacenamiento de archivos (DIRECTORY objects)
- **Lambda:** HTTP client para UTL_HTTP (pendiente crear)

---

## 🎯 Próximos Pasos Inmediatos

### 1. Reorganizar Proyecto
- [ ] Evaluar contenido del worktree `.trees/feature-oracle-postgres-migration/`
- [ ] Extraer conocimiento valioso (discovery, decisiones técnicas)
- [ ] Eliminar planes obsoletos de Pydantic AI
- [ ] Actualizar estructura del proyecto

### 2. Crear Estructura de Directorios
```bash
mkdir -p knowledge/{json,markdown,classification}
mkdir -p migrated/{simple,complex}/{functions,procedures,packages}
mkdir -p compilation_results/{success,errors}
mkdir -p shadow_tests
mkdir -p conversion_log
mkdir -p scripts
```

### 3. Preparar Scripts
- [ ] `scripts/convert_simple_objects.sh` (ora2pg)
- [ ] `scripts/load_to_pgvector.py` (embeddings)
- [ ] Configuración ora2pg

### 4. Iniciar FASE 1
- [ ] Ejecutar análisis de 8,122 objetos con sub-agentes
- [ ] Clasificar en SIMPLE vs COMPLEX
- [ ] Guardar conocimiento en JSON + Markdown

---

## 📝 Notas Importantes

### ¿Por qué NO usar Pydantic AI?
- Requiere API de Anthropic (~$30-150 USD adicionales)
- NO está incluido en Claude Code Pro
- Claude Code CLI/Web con sub-agentes es suficiente y GRATIS

### ¿Por qué Sonnet 4.5 en lugar de Opus 4.5?
- Sonnet es excelente para análisis de código estructurado
- Más rápido que Opus
- Opus solo necesario para razonamiento filosófico profundo
- PL/SQL tiene sintaxis bien definida (no requiere Opus)

### ¿Cómo funciona el límite de mensajes?
- Comparte entre CLI y Web (NO son separados)
- Se resetea cada 5 horas
- 1 mensaje puede lanzar 20 sub-agentes en paralelo
- Cada sub-agente tiene su propio contexto de 200K tokens

---

## 🔗 Referencias

### Documentación Oficial Consultada
- [Claude Code CLI Documentation](https://code.claude.com/docs/en/)
- [Claude API Rate Limits](https://platform.claude.com/docs/en/api/rate-limits.md)
- [Sub-agents Documentation](https://code.claude.com/docs/en/sub-agents.md)

### Conocimiento Preservado de Discovery
Ver archivos en `.claude/sessions/oracle-postgres-migration/`:
- `00_index.md` - Resumen ejecutivo
- `01_problem_statement.md` - 5W1H + JTBD + Scope
- `02_user_stories.md` - Épicas + User Stories
- `04_decisions.md` - Decisiones técnicas (AUTONOMOUS_TRANSACTION, UTL_HTTP, etc.)

---

**Última actualización:** 2025-01-05 por Claude Sonnet 4.5
**Próxima revisión:** Después de completar FASE 1

---

## ⚠️ ADVERTENCIA: Framework Context Flow Optimization

El framework "Context Flow Optimization" instalado en `.claude/CLAUDE.md` y los planes en `.trees/feature-oracle-postgres-migration/` fueron diseñados para:
- Aplicaciones Pydantic AI autónomas
- Uso de API de Anthropic (pago por tokens)
- Agentes ejecutados fuera de Claude Code

**Este framework YA NO aplica** para la estrategia actual que usa:
- Claude Code CLI/Web directamente
- Sub-agentes nativos de Claude Code
- Suscripción Claude Code Pro

Se recomienda:
1. Preservar discovery documents (conocimiento valioso)
2. Eliminar/archivar planes de Pydantic AI (obsoletos)
3. Actualizar `.claude/CLAUDE.md` con estrategia actual
