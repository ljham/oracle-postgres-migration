# Plan Consolidado - Oracle to PostgreSQL Migration Tool

**Versión:** 1.1
**Fecha:** 2025-12-31 (actualizado desde 2025-12-30)
**Estado:** Planificación Fase 1 - COMPLETADA AL 100% ✅
**Modelo usado:** Claude Opus 4.5

**🔄 Actualizado v1.1:** Incorporadas 4 features críticas detectadas en discovery v2.2:
- DBMS_SQL (Decision 8 DEFERRED)
- Tipos Colección (Decision 9 DEFERRED)
- Configuraciones NLS (conversión automática)
- Motores de Evaluación Dinámica (Decision 10 DEFERRED)

---

## 📋 Estado de Planificación

### ✅ Completado (3 de 3 sub-agentes)

1. **pydantic-ai-architect** (Opus 4.5) - COMPLETADO ✅
   - Archivo: `plan_pydantic_ai_agents.md` (v1.1 - 1,965 líneas)
   - Diseño completo de Code Comprehension Agent y Migration Strategist
   - **Actualizado:** Detección de 4 features críticas adicionales

2. **backend-developer** (Opus 4.5) - COMPLETADO ✅
   - Archivo: `plan_backend_logic.md` (1,430 líneas)
   - Arquitectura de infraestructura AWS, orquestación, integración ora2pg

3. **backend-test-engineer** (Opus 4.5) - COMPLETADO ✅
   - Archivo: `plan_testing_strategy.md` (2,698 líneas)
   - Framework de shadow testing completo
   - Validación de sintaxis PostgreSQL 17.4
   - Testing de objetos complejos
   - Automatización y reportes

**Total líneas de planificación:** 6,093 líneas (actualizado desde 6,336)

---

## 🎯 Resumen de Planes Completados

### 1. Agentes de IA (Pydantic AI)

**Code Comprehension Agent (v1.1):**
- **Propósito:** Comprensión semántica de código PL/SQL legacy (10+ años)
- **System prompt:** Especializado para interpretar código confuso, workarounds históricos
- **Modelos Pydantic:**
  - `CodeComprehensionDeps`: Dependencias del agente
  - `ObjectAnalysis`: Análisis de un objeto
  - `BatchAnalysisResult`: Resultado de batch
  - `BusinessRule`, `ProcessFlow`, `Dependency`: Conocimiento estructurado
- **Tools (5):**
  1. `read_plsql_object` - Lee código fuente
  2. `get_table_schema` - Obtiene estructura de tablas
  3. `get_foreign_keys` - Obtiene relaciones
  4. `store_knowledge` - Persiste conocimiento
  5. `generate_embedding` - Genera vector para pgvector
- **Features Oracle detectadas (18 tipos):**
  - **Críticas nuevas (v1.1):**
    - DBMS_SQL (SQL dinámico complejo)
    - TABLE_OF_INDEX_BY, TABLE_OF, VARRAY, OBJECT_TYPE (colecciones)
    - NLS_SESSION_CONFIG (ALTER SESSION)
    - DYNAMIC_FORMULA_ENGINE (motores de evaluación)
  - **Previamente validadas:**
    - AUTONOMOUS_TRANSACTION, UTL_HTTP, UTL_FILE, DIRECTORY
    - PACKAGE_STATE_VARIABLE, DBMS_SCHEDULER, REF_CURSOR, etc.
- **Estrategia:** Batches de 50 objetos en paralelo (5 workers)
- **Output:** `knowledge/` (rules/, flows/, dependencies/, features_detected.json)

**Migration Strategist:**
- **Propósito:** Decisión estratégica sobre clasificación SIMPLE vs COMPLEX
- **System prompt:** Criterios claros de clasificación basados en features Oracle
- **Modelos Pydantic:**
  - `MigrationStrategyDeps`: Dependencias del agente
  - `MigrationDecision`: Decisión por objeto
  - `ComplexityReport`: Reporte consolidado
- **Tools (5):**
  1. `read_features_detected` - Lee análisis de Code Comprehension
  2. `get_object_knowledge` - Consulta conocimiento extraído
  3. `get_dependency_graph` - Obtiene dependencias
  4. `evaluate_ora2pg_compatibility` - Evalúa si ora2pg puede convertir
  5. `write_complexity_report` - Genera reporte con justificación
- **Estrategia:** Secuencial (necesita vista global)
- **Criterios COMPLEX actualizados (v1.1):**
  - DBMS_SQL (Decision 8 DEFERRED)
  - Tipos colección (Decision 9 DEFERRED)
  - Motores de fórmulas dinámicas (Decision 10 DEFERRED)
  - AUTONOMOUS_TRANSACTION, UTL_HTTP, UTL_FILE (validados)
  - Variables de estado de paquete, baja confianza (<0.7)
- **Output:** `complexity/` (simple_objects.txt ~62%, complex_objects.txt ~38%)

**Optimización de Tokens (actualizada v1.1):**
- Ahorro estimado: **60%** (9.7M vs 24M tokens)
- ~62% objetos SIMPLE → ora2pg (0 tokens Claude)
- ~38% objetos COMPLEX → Agentes IA (tokens justificados)
- ⚠️ **Impacto nuevas features:** +8% tasa COMPLEX estimada (30% → 38%)
- Justificación: ~589 objetos adicionales con features críticas detectadas

**Integración pgvector:**
- Schema SQL para embeddings
- Índices HNSW para búsqueda semántica
- Función `search_knowledge()` para consultas

---

### 2. Infraestructura Backend

**Arquitectura de 4 Componentes:**

#### 2.1 Infraestructura AWS Lambda

**Lambda HTTP Client (Node.js 18+):**
- **Propósito:** Reemplazar UTL_HTTP de Oracle (<100 objetos críticos)
- **Base:** Repositorio oficial AWS - [wrapper-for-utl-http-with-amazon-aurora](https://github.com/aws-samples/wrapper-for-utl-http-with-amazon-aurora)
- **Componentes:**
  - Schema `utl_http_utility` en PostgreSQL
  - Wrapper functions PL/pgSQL que replican API UTL_HTTP
  - Tipos personalizados `req` y `resp`
  - Lambda function (Node.js) que hace HTTP requests reales
- **Funciones wrapper:**
  - `utl_http.begin_request(url, method)` → retorna request_id
  - `utl_http.set_header(request_id, name, value)`
  - `utl_http.set_authentication(request_id, username, password, scheme)`
  - `utl_http.write_text(request_id, data)`
  - `utl_http.get_response(request_id)` → retorna response object
  - `utl_http.read_text(response)` → retorna body
  - `utl_http.end_request(request_id)` → cleanup

**Lambda CSV-XLSX (Nodejs):**
- **Propósito:** Conversión de archivos Excel generados desde PostgreSQL
- **Trigger:** S3 Event cuando se crea un .csv
- **Biblioteca:** openpyxl para generar .xlsx
- **Flujo:** PostgreSQL → CSV → S3 → Lambda → XLSX

**Configuración VPC:**
- Private subnets para Aurora y Lambda
- NAT Gateway para APIs externas (internet público)
- Security groups Aurora → Lambda → APIs

**IAM Roles:**
- Aurora → Lambda invoke permission
- Lambda → VPC access + CloudWatch Logs
- Lambda → S3 read/write

#### 2.2 Sistema de Orquestación

**Manejo de Tokens:**
- Procesamiento en lotes de 100 objetos
- Pausa automática al 90% del límite
- Reanudación automática cuando se restablecen tokens

**Sistema de Checkpoints:**
- State JSON persistido en `.claude/sessions/migration_state.json`
- Campos: `last_processed_object`, `phase`, `batch_number`, `timestamp`
- Permite reanudar exactamente donde se pausó

**Paralelización de Sub-agentes:**
- Functions, Packages 1-200, Packages 201+ en paralelo
- Semaphore para limitar workers concurrentes

#### 2.3 Integración con ora2pg

**Configuración ora2pg.conf:**
```ini
INPUT_FILE  extracted/
ALLOW       complexity/simple_objects.txt
OUTPUT      migrated/simple/
TYPE        FUNCTION,PROCEDURE,PACKAGE,TRIGGER
```

**Script de ejecución:** `run_ora2pg.sh`
```bash
ora2pg -c ora2pg.conf -t FUNCTION -o migrated/simple/functions.sql
ora2pg -c ora2pg.conf -t PROCEDURE -o migrated/simple/procedures.sql
ora2pg -c ora2pg.conf -t PACKAGE -o migrated/simple/packages.sql
ora2pg -c ora2pg.conf -t TRIGGER -o migrated/simple/triggers.sql
```

#### 2.4 Base de Conocimiento (pgvector)

**Schema completo (4 tablas):**
1. `knowledge_items` - Items de conocimiento con embeddings
2. `business_rules` - Reglas de negocio extraídas
3. `dependencies` - Grafo de dependencias
4. `technical_features` - Features Oracle detectadas

**Índices HNSW:**
```sql
CREATE INDEX ON knowledge_items
USING hnsw (embedding vector_cosine_ops);
```

**Función de búsqueda semántica:**
```sql
CREATE FUNCTION semantic_search(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.8,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    item_id bigint,
    content text,
    similarity float
);
```

**Generador de embeddings:**
- Integración con Amazon Bedrock Titan Embeddings v2
- Dimensión: 1536 (compatible con pgvector)

---

## 📁 Estructura de Archivos Generados

```
proyecto/
├── .claude/
│   ├── doc/
│   │   └── oracle-postgres-migration/
│   │       ├── 00_PLAN_CONSOLIDADO.md           # Este archivo
│   │       ├── plan_pydantic_ai_agents.md       # ✅ Completado
│   │       ├── plan_backend_logic.md            # ✅ Completado
│   │       └── plan_testing_strategy.md         # ⏳ Pendiente
│   └── sessions/
│       ├── migration_state.json                 # Estado para checkpoints
│       └── migration_log.md                     # Log de trazabilidad
│
├── src/
│   ├── agents/
│   │   ├── code_comprehension_agent.py         # Code Comprehension
│   │   └── migration_strategist.py             # Migration Strategist
│   ├── lambda/
│   │   ├── http_client/                        # Lambda HTTP (Node.js)
│   │   │   ├── index.mjs
│   │   │   └── package.json
│   │   └── csv_to_xlsx/                        # Lambda Excel (Python)
│   │       ├── lambda_function.py
│   │       └── requirements.txt
│   ├── orchestration/
│   │   ├── checkpoint_manager.py               # Sistema de checkpoints
│   │   └── token_manager.py                    # Manejo de límites
│   └── utils/
│       └── pgvector_client.py                  # Cliente pgvector
│
├── sql/
│   ├── extracted/                               # ✅ Objetos Oracle extraídos
│   │   ├── functions.sql (146)
│   │   ├── procedures.sql (196)
│   │   ├── packages_body.sql (569)
│   │   └── ...
│   ├── exported/                                # ✅ DDL PostgreSQL (ora2pg)
│   │   ├── tables.sql
│   │   └── sequences.sql
│   └── migrations/
│       ├── 001_create_utl_http_schema.sql     # Wrapper UTL_HTTP
│       ├── 002_create_pgvector_schema.sql     # Base de conocimiento
│       └── 003_create_functions.sql           # Funciones auxiliares
│
├── knowledge/                                   # Output Code Comprehension
│   ├── rules/
│   ├── flows/
│   ├── dependencies/
│   └── features_detected.json
│
├── complexity/                                  # Output Migration Strategist
│   ├── complexity_report.md
│   ├── simple_objects.txt
│   └── complex_objects.txt
│
└── migrated/                                    # Output de conversión
    ├── simple/                                  # ora2pg (~70%)
    └── complex/                                 # Agentes IA (~30%)
```

---

### 3. Estrategia de Testing

**Framework de Shadow Testing:**
- **Schema de base de datos** para almacenar resultados de comparación Oracle vs PostgreSQL
- **Comparador de resultados** con 4 modos: strict, fuzzy, type_only, structure
- **Ejecutor de shadow tests** para procedures, functions y suites completas
- **Datos de prueba:** Generación sintética, snapshots anonimizados, edge cases

**Validación de Sintaxis PostgreSQL 17.4:**
- **40+ reglas de validación** categorizadas:
  - Tipos de datos (VARCHAR2→VARCHAR, NUMBER→NUMERIC)
  - Funciones (NVL→COALESCE, DECODE→CASE, SYSDATE→CURRENT_TIMESTAMP)
  - PL/pgSQL (excepciones, RAISE_APPLICATION_ERROR, cursores)
  - Aurora-específicas (UTL_FILE, UTL_HTTP, DBMS_SCHEDULER)
- **Validador** con 3 niveles: SYNTAX, SEMANTIC, RUNTIME

**Testing de Objetos Complejos:**
- **AUTONOMOUS_TRANSACTION:** Tests con dblink para simular transacciones autónomas
- **UTL_HTTP:** Tests del wrapper Lambda (mocks + integración real)
- **DIRECTORY→S3:** Tests de migración de 34 directorios a buckets S3

**Automatización:**
- **Test Runner** con ejecución paralela
- **Reportes Markdown** con indicadores VERDE/AMARILLO/ROJO
- **Integración CI/CD** (GitHub Actions): unit → integration → shadow → summary

**Pirámide de Testing:**
```
                    /\
                   /  \        5%  - Shadow Testing (Oracle vs PG)
                  /____\
                 /      \      25% - Integration Tests
                /________\
               /          \    70% - Unit Tests
              /____________\
```

**Estructura de Tests:**
```
tests/
  ├── unit/           # 70% - Tests unitarios
  ├── integration/    # 25% - Tests de integración
  ├── shadow/         # 5%  - Shadow tests Oracle vs PostgreSQL
  ├── complex/        # Tests de objetos complejos
  ├── regression/     # Tests de regresión
  └── fixtures/       # Datos de prueba
```

**Objetos Críticos Identificados:**
- **FAC_K_EGRESO_X_FACT** (41,732 líneas) - Facturación
- **DIG_K_PAGO** (35,498 líneas) - Pagos
- **RHH_K_NOMINA** (20,430 líneas) - Nómina
- **Procedures de facturación** (FAC_P_*) con >1,000 líneas

**Métricas de Éxito:**
| Métrica | Objetivo | Mínimo Aceptable |
|---------|----------|------------------|
| Tasa de Éxito Global | >95% | >90% |
| Shadow Match Rate | >99% | >95% |
| Cobertura Código Crítico | >90% | >80% |
| Tiempo Suite | <30 min | <60 min |

---

## 🚀 Próximos Pasos

### Inmediato (Pendiente)

1. **Esperar a que se restablezcan los límites** (8pm America/Guayaquil)
2. **Resumir backend-test-engineer** usando Agent ID: `a80bc3e`
3. **Completar plan de testing:**
   - Framework de shadow testing
   - Validación de sintaxis PostgreSQL
   - Testing de objetos complejos
   - Automatización de tests

### Después de Completar Planificación

4. **Revisar y consolidar los 3 planes**
5. **Identificar gaps o inconsistencias**
6. **Salir de plan mode**

### Fase 1B: Implementación

7. **Infraestructura AWS:**
   - Crear Lambda HTTP client (Nodejs)
   - Crear Lambda CSV→XLSX (Nodejs)
   - Configurar VPC, security groups, IAM roles
   - Crear wrapper functions PL/pgSQL

8. **Base de Conocimiento:**
   - Ejecutar SQL migrations (pgvector schema)
   - Configurar Amazon Bedrock para embeddings

9. **Implementar Agentes:**
   - Code Comprehension Agent (Pydantic AI)
   - Migration Strategist (Pydantic AI)
   - Sistema de orquestación y checkpoints

10. **Ejecutar Migración:**
    - Ejecutar Code Comprehension Agent (Opus 4.5)
    - Ejecutar Migration Strategist (Opus 4.5)
    - Conversión con ora2pg (objetos SIMPLES)
    - Conversión con agentes IA (objetos COMPLEJOS)

11. **Validación:**
    - Shadow testing
    - Validación de sintaxis
    - Reporte de resultados

---

## 📊 Métricas y Objetivos

| Métrica | Target | Justificación |
|---------|--------|---------------|
| Tasa de migración automática | > 70% | ora2pg para objetos SIMPLES |
| Tasa de éxito compilación | > 95% | Objetos que compilan sin errores |
| Shadow testing pass rate | > 95% | Resultados idénticos Oracle vs PostgreSQL |
| Optimización de tokens | ~66% | 8.1M vs 24M tokens |
| Timeline total | 3 meses | No negociable |
| Objetos por día | > 100/día | 8,122 objetos / 90 días |

---

## 🔑 Decisiones Técnicas Clave Consolidadas

### 1. Variables de Estado en Packages
- **Oracle:** Variables globales de paquete
- **PostgreSQL:** `SET pkg_name.var = 'value'` + `current_setting()`

### 2. AUTONOMOUS_TRANSACTION (~40 objetos)
- **Opciones:** dblink, Lambda, pg_cron
- **Decisión:** Por objeto según criticidad

### 3. DIRECTORY → AWS S3 (8 objetos)
- **Bucket:** `efs-veris-compartidos-dev` (us-east-1)
- **Extensión:** aws_s3 1.2 (nativa en Aurora)

### 4. UTL_HTTP → Lambda + Wrapper Functions (<100 objetos)
- **Lambda:** Node.js 18+ con Axios
- **Wrapper:** Functions PL/pgSQL que replican API UTL_HTTP
- **Crítico:** Sin esto el sistema no funciona

### 5. CSV → XLSX (archivos Excel)
- **Lambda:** Nodejs + sheetjs
- **Trigger:** S3 Event cuando se crea .csv

### 6. Base de Conocimiento
- **Vector DB:** pgvector 0.8.0 en Aurora
- **Embeddings:** Amazon Bedrock Titan v2 (1536 dims)

### 7. Modelo para Agentes
- **Obligatorio:** Claude Opus 4.5
- **Razón:** Razonamiento complejo sobre código legacy de 10+ años

### 8. DBMS_SQL Conversion Strategy ⏳ DEFERRED
- **Estado:** Post-scan analysis requerido
- **Cantidad estimada:** < 20 objetos
- **Impacto:** MEDIO-ALTO
- **Opciones:**
  - A: EXECUTE + format() (nativo PL/pgSQL)
  - B: Wrapper functions (conversión 1:1)
  - C: EXECUTE USING (más seguro)
- **Uso detectado:** Motor de fórmulas dinámicas (RHH_K_ADMINISTRA_FORMULA)
- **Decisión final:** Basada en patrones reales post-scan

### 9. Collection Types Mapping ⏳ DEFERRED
- **Estado:** Post-scan analysis requerido
- **Cantidad estimada:** ~480 objetos
- **Impacto:** ALTO (afecta arquitectura)
- **Tipos detectados:**
  - TABLE OF ... INDEX BY → Arrays `tipo[]` o hstore
  - TABLE OF ... → Arrays `tipo[]`
  - VARRAY → Arrays `tipo[]` + constraint
  - OBJECT TYPE → Composite Types o JSON
- **Decisión final:** Basada en volumetría y patrones de acceso reales

### 10. Dynamic Formula Engine Strategy ⏳ DEFERRED
- **Estado:** Post-scan analysis requerido
- **Cantidad estimada:** 3+ packages
- **Impacto:** ALTO (lógica crítica de nómina)
- **Opciones:**
  - A: EXECUTE + format() nativo (preferida)
  - B: Parser seguro con validación explícita
  - C: AWS Lambda + Python AST (futura)
- **Ejemplo:** Evaluar `"RHH_F_SUELDO / 30 + 15"` dinámicamente
- **Decisión final:** Basada en complejidad y frecuencia de uso

**📊 Impacto de Decisions DEFERRED:**
- +589 objetos estimados con features críticas
- Tasa COMPLEX: 30% → 38% (+8 puntos porcentuales)
- Tokens adicionales: ~1.6M (compensado por ahorro en objetos SIMPLE)

---

## 📚 Referencias y Recursos

### Documentación Oficial Consultada

**Pydantic AI:**
- [Pydantic AI - Agents](https://ai.pydantic.dev/agents/)
- [Pydantic AI - Tools](https://ai.pydantic.dev/tools/)
- [Pydantic AI - API Reference](https://ai.pydantic.dev/api/agent/)

**AWS:**
- [AWS Blog - Build custom HTTP client for Aurora PostgreSQL](https://aws.amazon.com/blogs/database/build-a-custom-http-client-in-amazon-aurora-postgresql-and-amazon-rds-for-postgresql-an-alternative-to-oracles-utl_http/)
- [GitHub - aws-samples/wrapper-for-utl-http-with-amazon-aurora](https://github.com/aws-samples/wrapper-for-utl-http-with-amazon-aurora)
- [Aurora PostgreSQL as Knowledge Base](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.VectorDB.html)

**Herramientas:**
- [Ora2Pg Documentation](https://ora2pg.darold.net/documentation.html)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

---

**Creado por:** Agente principal (consolidación de planes)
**Fecha creación:** 2025-12-30
**Última actualización:** 2025-12-31 (v1.1)
**Framework:** Context Flow Optimization v1.5
**Modelo:** Claude Opus 4.5 (para sub-agentes)

**Changelog v1.1:**
- ✅ Incorporadas 4 features críticas detectadas en discovery v2.2
- ✅ Actualizado Code Comprehension Agent (18 tipos de features Oracle)
- ✅ Actualizado Migration Strategist (criterios COMPLEX ampliados)
- ✅ Añadidas Decisions 8, 9, 10 (DEFERRED - post-scan)
- ✅ Actualizada optimización de tokens: 66% → 60% (tasa COMPLEX 30% → 38%)
- ✅ Impacto estimado: +589 objetos con features críticas (+8% tasa COMPLEX)
