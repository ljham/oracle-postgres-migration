# Changelog - Oracle to PostgreSQL Migration

> **📖 Contexto del Proyecto:** Herramienta basada en agentes IA para migrar 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora) en 3 meses. Ver [00_index.md](./00_index.md) para resumen ejecutivo completo.

**Versión Actual:** 2.2 | **Fecha:** 2025-12-31

---

## Version 2.2 - 2025-12-31 (⚠️ CRÍTICO - Features Oracle NO Documentadas)

**Cambios realizados:**

1. **Constraint 7 Agregado: Features Oracle Críticas NO Documentadas Inicialmente**
   - ✅ Detectado durante refinamiento de discovery por análisis de package ejemplo
   - ✅ Package analizado: RHH_K_ADMINISTRA_FORMULA (624 líneas)
   - ⚠️ IMPACTO: ALTO - Afecta arquitectura de conversión y planificación

2. **Nuevas Features Críticas Documentadas:**

   **7.1 DBMS_SQL (SQL Dinámico Nativo Oracle)**
   - 🔍 Cantidad estimada: < 20 objetos
   - ⚠️ Impacto: MEDIO-ALTO
   - 🔧 Conversión: EXECUTE + format() / EXECUTE USING (PostgreSQL)
   - 📊 Uso detectado: Motor de evaluación de fórmulas dinámicas
   - ⚙️ Métodos: OPEN_CURSOR, PARSE, BIND_VARIABLE, EXECUTE, VARIABLE_VALUE, CLOSE_CURSOR

   **7.2 Tipos Colección (TABLE OF, VARRAY, OBJECT TYPES)**
   - 🔍 Tipos: TABLE OF INDEX BY, TABLE OF, VARRAY, OBJECT TYPES
   - ⚠️ Impacto: ALTO (afecta arquitectura)
   - 🔧 Conversión: Arrays, Composite Types, hstore (PostgreSQL)
   - 🎯 Ejemplo: `TYPE T_Gt_Variables IS TABLE OF Varchar2(61) INDEX BY BINARY_INTEGER;`

   **7.3 Configuraciones NLS (ALTER SESSION)**
   - 🔍 Configuraciones: NLS_NUMERIC_CHARACTERS, NLS_DATE_FORMAT, NLS_LANGUAGE
   - ⚠️ Impacto: MEDIO (comportamiento runtime)
   - 🔧 Conversión: SET lc_numeric, datestyle, lc_messages (PostgreSQL)
   - 🎯 Ejemplo: `EXECUTE IMMEDIATE 'ALTER SESSION SET NLS_NUMERIC_CHARACTERS=''.,''';`

   **7.4 Motor de Evaluación de Fórmulas Dinámicas**
   - 🔍 Packages: RHH_K_ADMINISTRA_FORMULA (+ otros pendientes scan)
   - 📝 Funcionalidad: Evalúa expresiones matemáticas con variables en runtime
   - ⚠️ Impacto: ALTO (lógica crítica de nómina)
   - 🔧 Opciones: EXECUTE nativo (A), Parser seguro (B), Lambda AST (C)
   - 🎯 Ejemplo: Evaluar `"RHH_F_SUELDO / 30 + 15"` dinámicamente

3. **Decisions 8, 9, 10 Creadas como DEFERRED:**
   - ✅ **Decision 8:** DBMS_SQL Conversion Strategy (DEFERRED - post-scan)
   - ✅ **Decision 9:** Collection Types Mapping (DEFERRED - post-scan)
   - ✅ **Decision 10:** Dynamic Formula Engine Strategy (DEFERRED - post-scan)
   - 📊 Rationale: Se tomarán después del scan con métricas reales

4. **Plan de Acción Definido:**
   1. ✅ Documentar en discovery (COMPLETADO)
   2. ⏳ Actualizar Code Comprehension Agent para detectar patterns (Fase 1 - PENDIENTE)
   3. ⏳ Ejecutar scan completo de 8,122 objetos (Fase 1 - PENDIENTE)
   4. ⏳ Analizar estadísticas reales generadas (Fase 1 - PENDIENTE)
   5. ⏳ Tomar decisiones técnicas definitivas (Post-scan - PENDIENTE)
   6. ⏳ Implementar estrategias de conversión (Fase 2 - PENDIENTE)

**Impacto en el Proyecto:**
- 🔴 **Complejidad aumentada:** 4 features adicionales requieren conversión especializada
- 🟡 **Tasa COMPLEX puede incrementar:** Objetos con estas features probablemente serán COMPLEX
- 🟢 **Estrategia data-driven:** Decisiones técnicas basadas en scan real (no suposiciones)
- 🟢 **Riesgo mitigado:** Detección temprana evita sorpresas en Fase 2
- 🟡 **Code Comprehension Agent ampliado:** Debe detectar 4 patterns adicionales

**Cambios en archivos:**
- ✅ `.claude/sessions/oracle-postgres-migration/01_problem_statement.md` - Constraint 7 añadido
- ✅ `.claude/sessions/oracle-postgres-migration/04_decisions.md` - Decisions 8, 9, 10 añadidas
- ✅ `.claude/sessions/oracle-postgres-migration/05_changelog.md` - v2.2 documentada
- ⏳ `.claude/sessions/oracle-postgres-migration/00_index.md` - Pendiente actualización

**Próximos pasos INMEDIATOS:**
1. ⏳ Actualizar 00_index.md con resumen de features críticas
2. ⏳ Actualizar plan de Pydantic AI Agents para detectar estas 4 features
3. ⏳ Proceder con implementación de Code Comprehension Agent

**Sin cambios en:**
- Timeline (3 meses)
- Métricas de éxito (>95% compilación, >70% automático)
- Extensiones Aurora (todas validadas)
- Arquitectura en 5 fases

---

## Version 2.1 - 2025-12-30 (⚠️ CRÍTICO - Contexto de Código Legacy)

**Cambios realizados:**

1. **Nueva Constraint Crítica: Código Legacy de 10+ Años**
   - ✅ Usuario confirma código evolutivo sin refactorización completa
   - ✅ Múltiples niveles de experiencia (juniors → seniors → expertos)
   - ⚠️ Calidad variable esperada: redundancia, confusión, workarounds históricos, lógica avanzada
   - ⚠️ Inconsistencias de estilo y deuda técnica acumulada
   - ⚠️ Conocimiento tribal perdido (autores originales ya no están)

2. **Constraint 6 Agregada en 01_problem_statement.md:**
   - **Título:** "Código Legacy de 10+ Años (CRÍTICO para Estrategia de Análisis)"
   - **Impacto en sub-agentes:**
     - Code Comprehension Agent debe interpretar sin asumir calidad consistente
     - Migration Strategist debe marcar código confuso como COMPLEX
     - Documentación de conocimiento es CRÍTICA (preservar lógica antes de que se pierda)

3. **00_index.md Actualizado:**
   - ✅ Nueva sección: "⚠️ Contexto Crítico: Código Legacy de 10+ Años"
   - ✅ Resalta implicaciones para la migración
   - ✅ Enfatiza criticidad de la documentación de conocimiento

**Impacto en el Proyecto:**
- 🟡 **Expectativas ajustadas:** Código legacy aumenta complejidad esperada
- 🟡 **Estrategia de análisis refinada:** Sub-agentes deben ser más cautelosos
- 🟢 **Documentación más valiosa:** Preservar conocimiento tribal antes de que se pierda completamente
- 🟡 **Tasa de objetos COMPLEX puede aumentar:** Código confuso requerirá más revisión humana

**Beneficios de esta información:**
1. ✅ Sub-agentes no asumirán código "ideal" (expectativas realistas)
2. ✅ Migration Strategist será más conservador (marcará más como COMPLEX ante la duda)
3. ✅ Code Comprehension Agent documentará más exhaustivamente (conocimiento tribal)
4. ✅ Equipo de revisión humana estará preparado para código inconsistente

**Sin cambios en:**
- Timeline (3 meses)
- Métricas de éxito (>95% compilación, >70% automático)
- Decisiones técnicas (1-7)
- Arquitectura en 5 fases

**Próximos pasos:**
- Proceder con `/worktree oracle-postgres-migration` para iniciar Fase 1
- Sub-agentes ahora tienen contexto completo del desafío real

---

## Version 2.0 - 2025-12-29 (⚠️ CRÍTICO - Consumo de APIs REST)

**Cambios realizados:**

1. **Nueva Información Crítica del Usuario:**
   - ✅ Usuario reporta > 100 objetos PL/SQL que consumen APIs REST/SOAP usando UTL_HTTP
   - ✅ APIs mixtas: internas (VPC) + externas (internet público)
   - ✅ Criticidad: MUST HAVE (sin esto el sistema no funciona)
   - ⚠️ Volumen significativo: ~12% del total de objetos PL/SQL

2. **Investigación y Validación:**
   - ❌ Extensión `pgsql-http` NO está soportada en Aurora PostgreSQL
   - ✅ Solución AWS oficial: aws_lambda + aws_commons (YA instaladas)
   - ✅ AWS Blog post disponible: "Build custom HTTP client for Aurora PostgreSQL"
   - ✅ Código de ejemplo: GitHub aws-samples/wrapper-for-utl-http-with-amazon-aurora

3. **Decision 7 Agregada:**
   - **Problema:** Aurora NO soporta pgsql-http para HTTP requests
   - **Cantidad afectada:** < 100 objetos usan UTL_HTTP
   - **Solución:** Lambda HTTP client (Nodejs + Axios) + function PL/pgSQL
   - **Arquitectura:** PL/pgSQL → JSON request → Lambda → HTTP call → respuesta
   - **APIs:** Requiere VPC config (internas) + NAT Gateway (externas)
   - **Wrapper function:** consumir_api_rest

4. **Nueva US-2.9 Creada:**
   - **Título:** Consumo de APIs REST desde Base de Datos
   - **Alcance:** < 100 objetos a convertir
   - **Fases:** Análisis → Infraestructura → Function → Conversión → Testing
   - **Criterios de Aceptación:** 25+ criterios detallados
   - **Referencias:** AWS Blog + GitHub example repo

5. **Dependencies Actualizadas:**
   - ✅ Lambda HTTP client (Nodejs + Axios) - CRÍTICO
   - ✅ Function PL/pgSQL para UTL_HTTP API - CRÍTICO
   - ✅ Lambda VPC configuration para APIs internas
   - ✅ NAT Gateway para APIs externas
   - ✅ Security groups Aurora → APIs
   - ✅ IAM role para Aurora invoke Lambda

6. **Risks Actualizados:**
   - ⚠️ < 100 objetos con UTL_HTTP aumentan complejidad (Alta/Alto)
   - ⚠️ Latencia Lambda afecta performance de llamadas API (Media/Medio)
   - ⚠️ Conversión UTL_HTTP no es 1:1 (Media/Alto)
   - ⚠️ APIs externas pueden estar bloqueadas por firewall/WAF (Media/Alto)

7. **Scope Actualizado:**
   - ✅ Migración de consumo de APIs REST (< 100 objetos UTL_HTTP → Lambda + functions)

8. **Números Clave Actualizados:**
   - **UTL_HTTP (APIs REST):** < 100 objetos - ⚠️ CRÍTICO

**Impacto en el Proyecto:**
- 🔴 **Complejidad aumentada significativamente** (~12% objetos afectados)
- 🔴 **Nueva infraestructura crítica requerida** (Lambda HTTP client)
- 🔴 **Conversión NO directa** (functions + JSON marshalling)
- 🟢 **Solución AWS oficial disponible** (estrategia validada)
- 🟢 **Extensiones ya instaladas** (aws_lambda, aws_commons)

**Próximos pasos críticos:**
1. ⚠️ Fase 1: Identificar volumen EXACTO de objetos con UTL_HTTP
2. ⚠️ Fase 1: Catalogar TODAS las APIs consumidas (URLs, autenticación, formato)
3. ⚠️ Pre-Fase 1: Crear Lambda HTTP client (Nodejs + Axios)
4. ⚠️ Pre-Fase 1: Crear wrapper functions PL/pgSQL (consumir_api_rest)

**Referencias:**
- [AWS Blog - Build custom HTTP client for Aurora PostgreSQL](https://aws.amazon.com/blogs/database/build-a-custom-http-client-in-amazon-aurora-postgresql-and-amazon-rds-for-postgresql-an-alternative-to-oracles-utl_http/)
- [GitHub - aws-samples/wrapper-for-utl-http-with-amazon-aurora](https://github.com/aws-samples/wrapper-for-utl-http-with-amazon-aurora)

---

## Version 1.9 - 2025-12-29 (Modularización del Documento)

**Cambios realizados:**

1. **Estructura Modular Implementada:**
   - ✅ Documento original (1,835 líneas) dividido en 6 módulos temáticos
   - ✅ Estrategia aplicada: Context Engineering mediante persistencia en Markdown
   - ✅ Principio del framework: Sub-agentes deben entender contexto completo sin perder información

2. **Módulos Creados:**
   - ✅ `00_index.md` - Resumen ejecutivo DENSO + TOC (contexto global completo)
   - ✅ `01_problem_statement.md` - 5W1H + JTBD + Scope + Métricas + Dependencies
   - ✅ `02_user_stories.md` - 7 Épicas + 25+ User Stories + Criterios de Aceptación
   - ✅ `03_architecture.md` - Diseño técnico + Estructura de archivos + Workflows
   - ✅ `04_decisions.md` - Decisiones técnicas + Mapeo de conversiones Oracle→PG
   - ✅ `05_changelog.md` - Historial de versiones completo

3. **Optimización para Sub-agentes:**
   - ✅ Cada módulo < 25K tokens (legible completo)
   - ✅ Header con contexto del proyecto en cada archivo
   - ✅ Referencias cruzadas entre módulos
   - ✅ Resumen ejecutivo en 00_index.md suficiente para entender proyecto completo

4. **Beneficios:**
   - ✅ Lectura paralela posible (múltiples Read en un mensaje)
   - ✅ Sub-agentes solo leen módulos relevantes para su tarea
   - ✅ Actualizaciones futuras más fáciles (editar módulo específico)
   - ✅ Sigue mejores prácticas del Context Flow Framework

**Estructura creada:**
```
.claude/sessions/oracle-postgres-migration/
├── 00_index.md          (resumen ejecutivo + TOC)
├── 01_problem_statement.md
├── 02_user_stories.md
├── 03_architecture.md
├── 04_decisions.md
└── 05_changelog.md
```

**Documento original preservado:**
- `.claude/sessions/discovery_oracle_postgres_migration.md` (archivo completo original)

---

## Version 1.8 - 2025-12-29 (Configuración S3 Definida - Excel requiere Lambda)

**Cambios realizados:**

1. **Decisiones S3 Completadas (4 de 5):**
   - ✅ Bucket name: `efs-veris-compartidos-dev`
   - ✅ Región: `us-east-1`
   - ✅ Encriptación: SSE-S3 (estándar)
   - ✅ Excel: **SÍ es necesario** (lógica Oracle genera .xlsx, .txt, .csv)
   - ⚠️ Lifecycle policies: Pendiente (requiere más información del usuario)

2. **⚠️ CRÍTICO - Excel (.xlsx) Requiere AWS Lambda:**
   - ❌ PostgreSQL NO puede generar archivos .xlsx nativamente
   - ✅ Solución definida: **Opción A - AWS Lambda con S3 trigger**
   - 📐 Arquitectura: PostgreSQL → CSV → S3 → Lambda (convierte) → XLSX final
   - ⚠️ Nueva dependencia crítica: Lambda function para conversión CSV→XLSX
   - ⚠️ S3 Event Notification debe configurarse

---

## Version 1.7 - 2025-12-29 (✅ Validación de Extensiones Aurora - EXITOSA)

**Cambios realizados:**

1. **Validación de Extensiones Completada (BLOQUEANTE RESUELTO ✅)**
   - ✅ aws_s3 1.2 - **INSTALADA** → DIRECTORY → S3 confirmado viable
   - ✅ aws_commons 1.2 - **INSTALADA** → Soporte para aws_s3
   - ✅ dblink 1.2 - **INSTALADA** → AUTONOMOUS_TRANSACTION Opción B viable
   - ✅ aws_lambda 1.0 - **INSTALADA** → AUTONOMOUS_TRANSACTION Opción C viable
   - ✅ vector 0.8.0 - **INSTALADA** → Soporte para embeddings

**Impacto POSITIVO:**
- 🟢 **TODAS las extensiones críticas están disponibles** (aws_s3, dblink, aws_lambda)
- 🟢 **NO hay blockers de extensiones** - Todo lo necesario está presente
- 🟢 **pgvector disponible** - Base de conocimiento confirmada viable

---

## Version 1.6 - 2025-12-29 (Amazon Aurora PostgreSQL - Restricciones Críticas)

**Cambios realizados:**

1. **Constraints - Nueva Sección Crítica: Amazon Aurora PostgreSQL Managed Service**
   - ❌ NO acceso root al servidor (sin postgresql.conf directo)
   - ❌ NO acceso al filesystem (sin escritura de archivos locales)
   - ❌ Solo extensiones pre-compiladas por AWS (sin compilación custom)
   - ❌ NO COPY TO PROGRAM (sin acceso shell)

2. **Decision 6 Actualizada: DIRECTORY → AWS S3**
   - ✅ Enfatizado: **AWS S3 es LA ÚNICA OPCIÓN VIABLE** (no opcional)
   - ❌ Filesystem local: IMPOSIBLE en Aurora
   - ❌ EFS mount: IMPOSIBLE en Aurora (sin acceso a config OS)

---

## Version 1.5 - 2025-12-29 (Migración DIRECTORY → AWS S3)

**Cambios realizados:**

1. **Nueva User Story US-2.7: Migración de Objetos DIRECTORY a AWS S3**
   - ✅ Identificados 8 objetos DIRECTORY Oracle que requieren migración
   - ✅ Estrategia definida: UTL_FILE → aws_s3 extension de PostgreSQL
   - ✅ Mapeo DIRECTORY → S3 bucket prefixes documentado
   - ✅ Formatos soportados: .txt, .csv, .xlsx

2. **Nueva Decision 6: DIRECTORY Objects → AWS S3**
   - ✅ Opción elegida: AWS S3 con extensión `aws_s3` (nativa en RDS)
   - ✅ Pros/Cons documentados (durability, latencia, costo)

---

## Version 1.4 - 2025-12-29 (Conversión DDL Completada)

**Cambios realizados:**

1. **US-1.5 Marcada como COMPLETADA ✅:**
   - ✅ Conversión DDL ya realizada con ora2pg (herramienta externa)
   - ✅ Scripts PostgreSQL generados en `sql/exported/`
   - ✅ NO requiere sub-agente DDL Converter de Claude
   - ✅ Simplifica Fase 1: solo Code Comprehension Agent necesario

2. **Arquitectura del Sistema Actualizada:**
   - ✅ FASE 1 simplificada: "ANÁLISIS PARALELO" → **"COMPRENSIÓN SEMÁNTICA"**
   - ✅ Eliminado Sub-agente A (DDL Converter) - ya no es necesario
   - ✅ Solo Sub-agente único: Code Comprehension Agent

---

## Version 1.3 - 2025-12-26 (Actualización de User Stories)

**Cambios realizados:**

1. **Epic 1 - Renombrado y Reestructurado:**
   - ✅ Título actualizado: "Captura de Conocimiento" → **"Comprensión Semántica del Código"**
   - ✅ Sub-agente responsable clarificado: **Code Comprehension Agent**
   - ✅ Nueva US-1.0: Estado de Extracción (marcada como COMPLETADA ✅)
   - ✅ US-1.1 actualizada: "Escaneo" → **"Comprensión Semántica de Código PL/SQL"**

2. **Epic 2 - Renombrado y Actualizado:**
   - ✅ Título actualizado: "Migración de Base de Datos" → **"Decisión Estratégica y Migración"**
   - ✅ Sub-agente responsable clarificado: **Migration Strategist**
   - ✅ US-2.1 completamente reescrita (enfatiza RAZONAMIENTO)

---

## Version 1.2 - 2025-12-26 (Corrección Crítica)

**Análisis crítico realizado por Claude Opus 4.5**

**Problema identificado por el usuario:**
> "Para extraer las reglas de negocio, el know-how que está programado en los paquetes necesitas un razonamiento lógico NO MECÁNICO"

**Contradicción encontrada:**
- Se decía: "Knowledge Extractor es mecánico - solo extrae información"
- Pero hace: Capturar reglas de negocio, interpretar validaciones, comprender contexto
- **Conclusión de Opus:** Esto NO es mecánico, es **comprensión semántica**

**Cambios realizados:**

1. **Redefinición Completa de Roles (Decision 5):**
   - ✅ Eliminada falsa dicotomía "mecánico vs inteligente"
   - ✅ Distinción REAL: "Comprensión Semántica vs Decisión Estratégica"
   - ✅ Ambos sub-agentes usan razonamiento de Claude (con objetivos diferentes)

2. **Renombramientos Conceptuales:**
   - Knowledge Extractor → **Code Comprehension Agent**
     - Rol: Agente de comprensión semántica
     - Pregunta: "¿QUÉ hace este código?"
     - Output: Hechos estructurados (descriptivo)

   - Complexity Analyzer → **Migration Strategist**
     - Rol: Agente de decisión estratégica
     - Pregunta: "¿CÓMO debemos migrarlo?"
     - Output: Decisiones con justificación (prescriptivo)

3. **Analogía Clara Añadida:**
   ```
   Code Comprehension Agent = RADIÓLOGO (interpreta la tomografía)
   Migration Strategist = MÉDICO (decide el tratamiento)
   ```

---

## Version 1.1 - 2025-12-26

**Cambios realizados:**

1. **Estrategia de Herramientas Corregida (Decision 4):**
   - ✅ Aclarado que extracción ya se realizó con `extract_all_objects.sql`
   - ✅ ora2pg NO se usa para extracción, SOLO para conversión de objetos simples
   - ✅ Input real: archivos en `extracted/` (no conexión directa a Oracle)

2. **Roles de Sub-agentes Redefinidos (Decision 5):**
   - ✅ Knowledge Extractor: Extractor mecánico/pasivo (NO analiza complejidad)
   - ✅ Complexity Analyzer: Analista inteligente usando razonamiento de Claude

---

**Documento creado por:** requirements-engineer (sub-agente)
**Fecha de creación:** 2025-12-23
**Última actualización:** 2025-12-30
**Versión:** 2.1
**Revisión crítica:** Claude Opus 4.5
