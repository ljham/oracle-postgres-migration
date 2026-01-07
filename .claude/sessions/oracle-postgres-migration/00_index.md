# Oracle to PostgreSQL Migration Tool - Índice Maestro

**Versión:** 2.2 | **Fecha:** 2025-12-31 | **Estado:** validated | ready-for-planning

---

## 🎯 Resumen Ejecutivo

### Problema
Migrar **8,122 objetos PL/SQL** de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora) en **3 meses** debido a costos prohibitivos de licenciamiento Oracle.

### Alcance
- **Base de Datos:** 8,122 objetos PL/SQL (146 functions, 569 packages, 196 procedures, 87 triggers) + DDL
- **Backend:** ~30 proyectos (Java, Node.js, TypeScript, Python) con conexiones Oracle
- **Conocimiento:** Captura de reglas de negocio en base de datos vectorial (pgvector) para uso futuro por agentes IA

### Resultado Esperado
1. Código migrado listo para producción (objetos simples ~70%)
2. Código migrado con revisión humana (objetos complejos ~30%)
3. Reportes de compatibilidad con sugerencias
4. Trazabilidad completa de todas las acciones
5. Base de conocimiento con reglas de negocio extraídas

---

## 🏗️ Arquitectura en 5 Fases

```
✅ COMPLETADO: Extracción Oracle (sql/extract_all_objects.sql → extracted/*.sql)
✅ COMPLETADO: Conversión DDL (ora2pg → sql/exported/*.sql)
↓
FASE 1: COMPRENSIÓN SEMÁNTICA (Code Comprehension Agent)
  • Interpreta código PL/SQL y extrae conocimiento estructurado
  • Output: knowledge/ (reglas, flujos, dependencias) + pgvector
  • Tiempo: 1-2 horas | Tokens: Moderado
↓
FASE 2: DECISIÓN ESTRATÉGICA (Migration Strategist)
  • Evalúa complejidad y decide estrategia de migración
  • Clasifica: SIMPLE (ora2pg) vs COMPLEX (agentes IA)
  • Output: complexity/*.txt (listas) + complexity_report.md (justificación)
  • Tiempo: 30-45 min | Tokens: Moderado
↓
FASE 3: CONVERSIÓN BIFURCADA
  ├─ RUTA A: Objetos SIMPLES (~70%) → ora2pg (0 tokens Claude)
  └─ RUTA B: Objetos COMPLEJOS (~30%) → Agentes IA Claude (alto razonamiento)
  • Output: migrated/simple/*.sql + migrated/complex/*.sql
  • Tiempo: Variable | Tokens: Alto solo para complejos
↓
FASE 4: VALIDACIÓN
  • Validación sintaxis PostgreSQL 17.4
  • Shadow testing (Oracle vs PostgreSQL resultados idénticos)
  • Tasa de éxito objetivo: >95%
↓
FASE 5: BACKEND (después de DB completa)
  • Escaneo de 30 proyectos backend
  • Actualización ORMs y queries SQL nativos
  • Validación de endpoints
```

---

## ⚠️ Contexto Crítico: Código Legacy de 10+ Años

**Calidad del código variable:**
- ✅ **10+ años de evolución** - Sin refactorización completa
- ⚠️ **Múltiples niveles de experiencia** - Juniors, seniors, expertos (código inconsistente)
- ⚠️ **Calidad mixta esperada:**
  - Lógica redundante, confusa, sin sentido aparente (workarounds históricos)
  - Lógica avanzada (optimizaciones complejas)
- ⚠️ **Deuda técnica acumulada** - Parches sobre parches
- ⚠️ **Conocimiento tribal perdido** - Autores originales ya no están

**Implicación para la migración:**
- Code Comprehension Agent debe ser especialmente cuidadoso al interpretar
- Migration Strategist marcará código confuso como COMPLEX (requiere revisión humana)
- Documentación de conocimiento es CRÍTICA (preservar lógica antes de que se pierda)

---

## ⚠️ Features Oracle Críticas (Detectadas Post-Discovery v2.2)

**Estado:** ⏳ DEFERRED - Decisiones técnicas se tomarán después del scan completo

**Detectado:** 2025-12-31 durante análisis del package RHH_K_ADMINISTRA_FORMULA

### 🔍 Feature 1: DBMS_SQL (SQL Dinámico Nativo)
- **Cantidad estimada:** < 20 objetos
- **Impacto:** MEDIO-ALTO
- **Conversión:** EXECUTE + format() (PostgreSQL)
- **Ejemplo:** Motor de evaluación de fórmulas dinámicas
- **Decision:** 8 (DEFERRED - post-scan)

### 🔍 Feature 2: Tipos Colección
- **Tipos:** TABLE OF INDEX BY, TABLE OF, VARRAY, OBJECT TYPES
- **Impacto:** ALTO (afecta arquitectura)
- **Conversión:** Arrays `tipo[]`, Composite Types, hstore (PostgreSQL)
- **Ejemplo:** `TYPE T_Gt_Variables IS TABLE OF Varchar2(61) INDEX BY BINARY_INTEGER;`
- **Decision:** 9 (DEFERRED - post-scan)

### 🔍 Feature 3: Configuraciones NLS (ALTER SESSION)
- **Configuraciones:** NLS_NUMERIC_CHARACTERS, NLS_DATE_FORMAT, NLS_LANGUAGE
- **Impacto:** MEDIO (comportamiento runtime)
- **Conversión:** SET lc_numeric, datestyle, lc_messages (PostgreSQL)
- **Ejemplo:** `EXECUTE IMMEDIATE 'ALTER SESSION SET NLS_NUMERIC_CHARACTERS=''.,''';`
- **Estrategia:** Conversión automática per-object

### 🔍 Feature 4: Motor de Evaluación de Fórmulas Dinámicas
- **Packages detectados:** RHH_K_ADMINISTRA_FORMULA (+ otros pendientes)
- **Funcionalidad:** Evalúa `"RHH_F_SUELDO / 30 + 15"` dinámicamente
- **Impacto:** ALTO (lógica crítica de nómina)
- **Opciones:** EXECUTE nativo (A), Parser seguro (B), Lambda AST (C)
- **Decision:** 10 (DEFERRED - post-scan)

**🎯 Plan de Acción:**
1. ✅ Documentar features (COMPLETADO v2.2)
2. ⏳ Actualizar Code Comprehension Agent (detectar 4 patterns)
3. ⏳ Ejecutar scan de 8,122 objetos
4. ⏳ Analizar estadísticas reales
5. ⏳ Tomar decisiones definitivas (Decisions 8, 9, 10)
6. ⏳ Implementar estrategias de conversión

---

## 🔑 Decisiones Técnicas Críticas

### Decision 1: Variables de Estado en Packages → Session Variables
- **Oracle:** Variables de paquete globales (session state)
- **PostgreSQL:** `SET pkg_name.var = 'value'` + `current_setting('pkg_name.var')`
- **Rationale:** Más limpia que tablas temporales

### Decision 2: AUTONOMOUS_TRANSACTION (~40 objetos)
- **Estrategias disponibles:**
  - Opción A (RECOMENDADA): Rediseño arquitectónico (staging + pg_cron)
  - Opción B: dblink (comportamiento exacto, overhead)
  - Opción C: AWS Lambda (cloud-native)
- **Estado extensiones:** ✅ dblink 1.2, aws_lambda 1.0, pg_cron 1.6 - TODAS disponibles en Aurora
- **Decisión:** Por objeto según criticidad (usuario decide en Fase 2)

### Decision 3: Base de Conocimiento → pgvector en Aurora
- **Extensión:** vector 0.8.0 ✅ INSTALADA en Aurora
- **Uso:** Embeddings de reglas de negocio para búsqueda semántica
- **Beneficio:** Consultas sin re-análisis de código (optimización tokens)

### Decision 4: Herramientas de Migración → Estrategia Híbrida
- **Extracción:** ✅ COMPLETADA (sql/extract_all_objects.sql ejecutado manualmente)
- **DDL:** ✅ COMPLETADO (ora2pg → sql/exported/*.sql)
- **Objetos SIMPLES:** ora2pg (conversión sintáctica, 0 tokens Claude)
- **Objetos COMPLEJOS:** Agentes IA Claude (razonamiento arquitectónico)
- **Optimización:** ~33% ahorro de tokens (16.3M vs 24.4M)

### Decision 5: Sub-agentes → Comprensión + Decisión (NO mecánico vs inteligente)
- **Code Comprehension Agent:** ¿QUÉ hace este código? (comprensión semántica)
- **Migration Strategist:** ¿CÓMO debemos migrarlo? (decisión estratégica)
- **Analogía:** Radiólogo (interpreta) vs Médico (decide tratamiento)
- **Ambos usan razonamiento de Claude** (prompts especializados, reutilización de conocimiento)

### Decision 6: DIRECTORY Objects → AWS S3 (LA ÚNICA OPCIÓN VIABLE en Aurora)
- **Problema:** Aurora PostgreSQL NO permite acceso a filesystem local
- **Solución:** aws_s3 extension ✅ INSTALADA (nativa en Aurora)
- **Mapeo:** 8 DIRECTORY objects → S3 bucket `efs-veris-compartidos-dev` (us-east-1)
- **Conversión:** UTL_FILE → aws_s3.query_export_to_s3()
- **Formatos:** .txt ✅, .csv ✅, .xlsx ⚠️ (requiere AWS Lambda para conversión)
- **⚠️ CRÍTICO:** Lambda function requerida para CSV → XLSX (Excel es formato binario)

### Decision 7: Consumo de APIs REST → AWS Lambda + Wrapper Functions (< 100 objetos)
- **Problema:** Aurora PostgreSQL NO soporta extensión `pgsql-http` para HTTP requests
- **Cantidad afectada:** **< 100 objetos** usan UTL_HTTP (crítico para negocio)
- **Solución AWS:** aws_lambda + aws_commons ✅ YA INSTALADAS (estrategia oficial de AWS)
- **Conversión:** UTL_HTTP → PL/pgSQL wrapper functions + Lambda HTTP client
- **Arquitectura:** PL/pgSQL construye JSON request → Lambda (Python) hace HTTP call → retorna respuesta
- **APIs:** Mixtas (internas VPC + externas internet público)
- **Wrapper functions necesarias:** BEGIN_REQUEST, SET_HEADER, SET_AUTHENTICATION, WRITE_TEXT, GET_RESPONSE
- **Ref:** [AWS Blog - Build custom HTTP client for Aurora PostgreSQL](https://aws.amazon.com/blogs/database/build-a-custom-http-client-in-amazon-aurora-postgresql-and-amazon-rds-for-postgresql-an-alternative-to-oracles-utl_http/)

---

## 📊 Números Clave

| Métrica | Valor | Notas |
|---------|-------|-------|
| **Objetos PL/SQL** | 8,122 | 146 func + 569 pkg + 196 proc + 87 trig |
| **Proyectos Backend** | ~30 | Java, Node.js, TypeScript, Python |
| **Timeline** | 3 meses | No negociable |
| **Tasa Automática Objetivo** | >70% | Objetos simples con ora2pg |
| **Tasa Éxito Objetivo** | >95% | Compilación + shadow testing |
| **DIRECTORY Objects** | 8 | Oracle → AWS S3 (S3 bucket configurado) |
| **AUTONOMOUS_TRANSACTION** | ~40 | Múltiples estrategias disponibles |
| **UTL_HTTP (APIs REST)** | **< 100** | ⚠️ CRÍTICO - Wrapper + Lambda requerido |
| **Extensiones Aurora Validadas** | 5/5 | aws_s3, aws_commons, dblink, aws_lambda, vector |

---

## 🚀 Estado Actual

### ✅ Completado
- [x] Fase 0: Descubrimiento de Requisitos (documento validado v1.9)
- [x] Extracción de objetos Oracle (sql/extract_all_objects.sql ejecutado)
- [x] Conversión DDL a PostgreSQL (ora2pg → sql/exported/*.sql)
- [x] Validación de extensiones Aurora (todas disponibles)
- [x] Configuración S3 bucket (efs-veris-compartidos-dev en us-east-1)

### ⏳ Pendiente
- [ ] Fase 1: Planificación técnica (próximo paso con `/worktree`)
- [ ] Crear Lambda function para CSV → XLSX (requerido para archivos Excel)
- [ ] **Crear Lambda HTTP client** (< 100 objetos con UTL_HTTP - CRÍTICO)
- [ ] **Crear wrapper functions PL/pgSQL** para UTL_HTTP API
- [ ] Configurar security groups para Aurora → APIs (internas VPC + externas internet)

---

## 📁 Estructura de Archivos

```
.claude/sessions/oracle-postgres-migration/
├── 00_index.md                    # Este archivo (resumen ejecutivo + TOC)
├── 01_problem_statement.md        # 5W1H + JTBD + Scope + Assumptions + Constraints
├── 02_user_stories.md             # 7 Épicas + 25+ User Stories + Criterios de Aceptación
├── 03_architecture.md             # Diseño del sistema + Estructura de archivos + Workflows
├── 04_decisions.md                # Decisiones técnicas + Mapeo de conversiones Oracle→PG
├── 05_changelog.md                # Historial de versiones + cambios (v1.1 a v1.9)

proyecto/
├── sql/
│   ├── extract_all_objects.sql        # ✅ Script de extracción (ejecutado)
│   └── exported/                       # ✅ DDL PostgreSQL (ora2pg)
│       ├── tables.sql, sequences.sql, types.sql
├── extracted/                          # ✅ Objetos PL/SQL Oracle extraídos
│   ├── functions.sql (146), procedures.sql (196)
│   ├── packages_spec.sql (569), packages_body.sql (569)
│   ├── triggers.sql (87), tables.sql, views.sql, etc.
├── knowledge/                          # Output de Code Comprehension Agent
│   ├── schema/ rules/ flows/ dependencies/
│   ├── features_detected.json
│   └── embeddings/ (pgvector)
├── complexity/                         # Output de Migration Strategist
│   ├── complexity_report.md
│   ├── simple_objects.txt, complex_objects.txt
└── migrated/                           # Código PL/pgSQL PostgreSQL
    ├── simple/ (ora2pg output ~70%)
    └── complex/ (agentes IA output ~30%)
```

---

## 🔗 Tabla de Contenido - Módulos

| Módulo | Contenido | Uso Principal |
|--------|-----------|---------------|
| **00_index.md** | Resumen ejecutivo + TOC | Quick reference, contexto global |
| **01_problem_statement.md** | 5W1H, JTBD, Scope, Métricas | Entender el problema y objetivos |
| **02_user_stories.md** | Épicas + User Stories + AC | Requisitos funcionales detallados |
| **03_architecture.md** | Diseño técnico + Workflows | Implementación y estructura |
| **04_decisions.md** | Decisiones + Conversiones | Guía técnica de migración |
| **05_changelog.md** | Historial de cambios | Trazabilidad de evolución del proyecto |

---

## 🎯 Próximos Pasos

1. **Iniciar Fase 1: Planificación Técnica**
   ```bash
   /worktree oracle-postgres-migration
   ```

2. **Activar plan mode** y delegar a sub-agentes:
   - pydantic-ai-architect (diseño de agentes IA)
   - backend-developer (lógica de migración)
   - backend-test-engineer (estrategia de shadow testing)

3. **Habilitar extensiones PostgreSQL** (después de planificación):
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_cron;
   ```

---

## 📝 Notas para Sub-agentes

### Al Leer Este Documento
- **Contexto completo:** Este índice contiene suficiente información para entender el proyecto
- **Detalles específicos:** Consulta módulos 01-05 según necesidad
- **Optimización de tokens:** Lee solo los módulos relevantes para tu tarea

### Mapeo de Tareas → Módulos Recomendados

Si tu tarea es específica, lee solo los módulos que necesites:

| Tu Tarea/Rol | Módulos a Leer | Orden Sugerido |
|--------------|----------------|----------------|
| **Planificación general** | Todos | 00 → 01 → 02 → 03 → 04 |
| **Code Comprehension Agent** | 01, 02, 03, 04 | 00 → 01 → 02 → 04 |
| **Migration Strategist** | 01, 02, 04 | 00 → 04 → 02 |
| **Backend Developer** | 02, 03, 04 | 00 → 03 → 04 → 02 |
| **Test Engineer (QA)** | 02, 03 | 00 → 02 → 03 |
| **Investigación técnica** | 04, 03 | 00 → 04 → 03 |
| **Revisión de decisiones** | 04, 05 | 00 → 04 → 05 |

**Nota:** Consulta `README.md` para guía completa de navegación.

### Convenciones de Idioma
- **Documentación:** Español (este proyecto está en español)
- **Código:** Inglés (nombres de variables, funciones, clases)
- **Términos técnicos:** Sin traducir (endpoint, hook, middleware, etc.)

### Principios del Framework Context Flow
- **Context Engineering:** Persistencia en Markdown (este archivo es contexto permanente)
- **Sub-agentes especializados:** Planifican (NO ejecutan código directamente)
- **Desarrollo paralelo:** Git Worktrees (`.trees/feature-{nombre}`)
- **Optimización de tokens:** Planes estructurados en lugar de código completo

---

**Documento creado por:** Agente principal (modularización de discovery document)
**Fuente original:** discovery_oracle_postgres_migration.md (1,835 líneas)
**Fecha de creación:** 2025-12-29
**Versión:** 1.0
**Propósito:** Proveer contexto denso y completo para sub-agentes sin perder información valiosa
