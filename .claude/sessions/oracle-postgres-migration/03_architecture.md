# Architecture - Oracle to PostgreSQL Migration

> **📖 Contexto del Proyecto:** Herramienta basada en agentes IA para migrar 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora) en 3 meses. Ver [00_index.md](./00_index.md) para resumen ejecutivo completo.

**Versión:** 1.9 | **Fecha:** 2025-12-29 | **Estado:** validated

---

## Arquitectura del Sistema de Migración (5 Fases)

```
+------------------------------------------------------------------+
|                    ESTADO ACTUAL (Completado)                     |
+------------------------------------------------------------------+
|  ✅ Extracción de objetos Oracle realizada manualmente           |
|  ✅ Script usado: sql/extract_all_objects.sql                    |
|  ✅ Ejecutado en: sqlplus local                                  |
|  ✅ Output: extracted/*.sql (8,122 objetos)                      |
|                                                                   |
|  ✅ Conversión DDL a PostgreSQL realizada con ora2pg             |
|  ✅ Herramienta: ora2pg (especializada en Oracle→PostgreSQL)     |
|  ✅ Output: sql/exported/*.sql                                   |
|     • tables.sql (estructura completa convertida)                |
|     • sequences.sql (sintaxis PostgreSQL)                        |
|     • types.sql (tipos convertidos)                              |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|      FASE 1: COMPRENSIÓN SEMÁNTICA (Claude Code Web)             |
+------------------------------------------------------------------+
|                                                                  |
|  Input:                                                          |
|  • sql/extracted/*.sql (objetos PL/SQL extraídos)                |
|  • sql/exported/*.sql (DDL PostgreSQL ya convertido con ora2pg)  |
|                                                                  |
|  [Sub-agente único]                                              |
|  Code Comprehension Agent                                        |
|  ↓                                                               |
|  Input: TODOS los objetos                                        |
|  • sql/extracted/tables.sql (relaciones Oracle)                  |
|  • sql/extracted/primary_keys.sql                                |
|  • sql/extracted/foreign_keys.sql                                |
|  • sql/extracted/functions.sql                                   |
|  • sql/extracted/procedures.sql                                  |
|  • sql/extracted/packages_*.sql                                  |
|  • sql/extracted/triggers.sql                                    |
|  • sql/extracted/views.sql                                       |
|  • sql/extracted/materialized_views.sql                          |
|  • sql/exported/*.sql (DDL PostgreSQL para referencia)           |
|                                                                  |
|  Tarea (COMPRENSIÓN SEMÁNTICA):                                  |
|  • Interpretar relaciones entre tablas                           |
|  • Extraer reglas de negocio del código PL/SQL                   |
|  • Comprender validaciones y su propósito                        |
|  • Capturar cálculos de negocio                                  |
|  • Mapear dependencias entre objetos                             |
|  • Identificar features técnicas Oracle-específicas              |
|  • NO clasifica complejidad (eso es Fase 2)                      |
|                                                                  |
|  Output:                                                         |
|  knowledge/                                                      |
|  ├── schema/ (relaciones e interpretación del modelo)            |
|  ├── rules/ (reglas de negocio extraídas)                        |
|  ├── flows/ (flujos de proceso documentados)                     |
|  ├── dependencies/ (grafo de dependencias)                       |
|  ├── features_detected.json (features técnicas)                  |
|  └── embeddings/ (indexado en pgvector)                          |
|                                                                  |
|  Tiempo estimado: 1-2 horas                                      |
+------------------------------------------------------------------+
                              ↓
+------------------------------------------------------------------+
|         FASE 2: DECISIÓN ESTRATÉGICA (Claude Code Web)           |
|                        (SECUENCIAL)                              |
+------------------------------------------------------------------+
|                                                                  |
|  [Sub-agente C]                                                  |
|  Migration Strategist (DECISIÓN - Evaluación de Riesgo)          |
|  ↓                                                               |
|  Input:                                                          |
|  • knowledge/features_detected.json  ← Del Code Comprehension    |
|  • knowledge/rules/                  ← Reglas de negocio         |
|  • knowledge/dependencies/           ← Dependencias              |
|  • extracted/*.sql                   ← Código fuente (contexto)  |
|                                                                  |
|  Proceso (RAZONAMIENTO DE DECISIÓN):                             |
|  1. Lee conocimiento estructurado (NO código raw)                |
|  2. Evalúa complejidad técnica de migración                      |
|  3. Analiza impacto arquitectónico en el sistema                 |
|  4. Calcula riesgo de cada estrategia (ora2pg vs agentes)        |
|  5. Clasifica con justificación razonada:                        |
|     • ¿Por qué este objeto es complejo para migrar?              |
|     • ¿Qué riesgos tiene usar ora2pg?                            |
|     • ¿Requiere decisiones arquitectónicas humanas?              |
|     • ¿Cuál es la estrategia óptima?                             |
|                                                                  |
|  Output:                                                         |
|  ├── complexity_report.md     (análisis con justificación)       |
|  ├── simple_objects.txt       (para ora2pg ~70%)                 |
|  └── complex_objects.txt      (para agentes IA ~30%)             |
|                                                                  |
|  Tiempo: 30-45 min                                               |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|              FASE 3: CONVERSIÓN BIFURCADA                        |
+------------------------------------------------------------------+
|                                                                  |
|  RUTA A: Objetos SIMPLES        RUTA B: Objetos COMPLEJOS        |
|  (~70% de objetos)              (~30% de objetos)                |
|  ↓                              ↓                                |
|  Herramienta: ora2pg            Herramienta: Agentes IA Claude   |
|  (Local - Ejecución manual)     (Claude Code Web)                |
|  ↓                              ↓                                |
|  Input:                         Input:                           |
|  • simple_objects.txt           • complex_objects.txt            |
|  • sql/extracted/*.sql          • knowledge/ (contexto completo) |
|                                 • sql/extracted/*.sql            |
|                                                                  |
|  Proceso:                       Proceso:                         |
|  1. Configurar ora2pg.conf      1. Para cada objeto complejo:    |
|  2. Ejecutar conversión:            • Leer contexto              |
|     ora2pg -t FUNCTION              • Analizar arquitectura      |
|     ora2pg -t PROCEDURE             • Generar opciones           |
|     ora2pg -t PACKAGE               • PAUSAR si requiere         |
|  3. Validar sintaxis                  decisión humana            |
|                                     • Documentar decisión        |
|  Output:                            • Implementar conversión     |
|  migrated/simple/                                                |
|  ├── functions.sql              2. Validar sintaxis              |
|  ├── procedures.sql                                              |
|  ├── packages.sql               Output:                          |
|  └── triggers.sql               migrated/complex/                |
|                                 ├── PKG_AUDITORIA.sql            |
|  Tokens usados: 0               ├── PKG_SEGURIDAD.sql            |
|  (herramienta externa)          └── decisions_log.md             |
|                                                                  |
|  Tiempo: 1-2 horas              Tokens usados: Alto              |
|  (manual)                       (pero justificado)               |
|                                                                  |
|                                 Tiempo: Variable (según          |
|                                 decisiones humanas)              |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                   FASE 4: VALIDACIÓN (Claude Code Web)            |
+------------------------------------------------------------------+
|                                                                   |
|  Input:                                                          |
|  • migrated/ddl/*.sql         (DDL PostgreSQL)                   |
|  • migrated/simple/*.sql      (Objetos simples convertidos)      |
|  • migrated/complex/*.sql     (Objetos complejos convertidos)    |
|                                                                   |
|  Proceso:                                                        |
|  1. Validación de sintaxis PostgreSQL (todos los objetos)        |
|  2. Shadow testing (procedures críticos)                         |
|     • Ejecutar en Oracle y PostgreSQL con mismos datos           |
|     • Comparar resultados                                        |
|  3. Reporte final de migración                                   |
|                                                                   |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                   FASE BACKEND (Claude Code Web)                  |
+------------------------------------------------------------------+
|                                                                   |
|  Para cada proyecto:                                             |
|  1. Escanear configuraciones y queries                           |
|  2. Actualizar ORM config                                        |
|  3. Convertir queries nativas                                    |
|  4. Validar compilación                                          |
|                                                                   |
+------------------------------------------------------------------+
```

---

## Estructura de Archivos Completa

```
proyecto/
+-- .claude/
|   +-- sessions/
|   |   +-- oracle-postgres-migration/
|   |   |   +-- 00_index.md
|   |   |   +-- 01_problem_statement.md
|   |   |   +-- 02_user_stories.md
|   |   |   +-- 03_architecture.md
|   |   |   +-- 04_decisions.md
|   |   |   +-- 05_changelog.md
|   |   +-- context_session_migration.md            # Contexto de sesión
|   |   +-- migration_state.json                    # Estado para reanudación
|   |   +-- migration_log.md                        # Log de trazabilidad
|   +-- doc/
|       +-- migration/
|           +-- plan_epic0_infrastructure.md
|           +-- plan_epic1_knowledge.md
|           +-- plan_epic2_migration.md
|           +-- plan_epic3_validation.md
|           +-- plan_epic4_backend.md
|
+-- sql/
|   +-- extract_all_objects.sql                     # ✅ Script de extracción (ejecutado)
|   +-- exported/                                    # ✅ DDL PostgreSQL (COMPLETADO con ora2pg)
|       +-- tables.sql                               # Estructura de tablas convertida
|       +-- sequences.sql                            # Sequences en sintaxis PostgreSQL
|       +-- types.sql                                # Tipos personalizados convertidos
|
+-- extracted/                                       # ✅ Objetos PL/SQL Oracle (COMPLETADO)
|   +-- functions.sql                                # 146 objetos
|   +-- procedures.sql                               # 196 objetos
|   +-- packages_spec.sql                            # 569 objetos
|   +-- packages_body.sql                            # 569 objetos
|   +-- triggers.sql                                 # 87 objetos
|   +-- tables.sql                                   # Estructura de tablas Oracle
|   +-- primary_keys.sql                             # Primary keys
|   +-- foreign_keys.sql                             # Foreign keys
|   +-- sequences.sql                                # Sequences Oracle
|   +-- types.sql                                    # Tipos personalizados Oracle
|   +-- views.sql                                    # Views
|   +-- materialized_views.sql                       # Materialized views
|   +-- directories.sql                              # Directories
|   +-- inventory.md                                 # Inventario generado
|
+-- migrated/                                        # Código PL/pgSQL PostgreSQL (OUTPUT)
|   |
|   +-- simple/                                      # Output de ora2pg (~70%)
|   |   +-- functions.sql
|   |   +-- procedures.sql
|   |   +-- packages.sql
|   |   +-- triggers.sql
|   |
|   +-- complex/                                     # Output de agentes IA (~30%)
|       +-- PKG_AUDITORIA.sql
|       +-- PKG_SEGURIDAD.sql
|       +-- decisions_log.md                         # Decisiones documentadas
|
+-- knowledge/                                       # Output de Code Comprehension Agent
|   +-- schema/                                      # Relaciones de tablas
|   |   +-- table_relations.md                       # PKs, FKs documentadas
|   |   +-- er_diagram.mermaid                       # Diagrama ER
|   |   +-- constraints.md                           # CHECK constraints
|   |
|   +-- rules/                                       # Reglas de negocio
|   |   +-- business_rules.md                        # Reglas extraídas (comprensión)
|   |   +-- validations.md                           # Validaciones interpretadas
|   |   +-- calculations.md                          # Cálculos capturados
|   |
|   +-- flows/                                       # Flujos de proceso
|   |   +-- process_flows.md                         # Descripción de flujos
|   |   +-- call_graph.mermaid                       # Grafos de llamadas
|   |
|   +-- dependencies/                                # Dependencias
|   |   +-- object_dependencies.md                   # Quién llama a quién
|   |   +-- dependency_matrix.csv                    # Matriz de dependencias
|   |
|   +-- features_detected.json                       # Features técnicas (INPUT para Migration Strategist)
|   |
|   +-- embeddings/                                  # Búsqueda semántica
|       +-- pgvector_inserts.sql                     # Script para indexar en pgvector
|
+-- complexity/                                      # Output de Migration Strategist
|   +-- complexity_report.md                         # Decisiones con justificación
|   +-- simple_objects.txt                           # Lista para ora2pg
|   +-- complex_objects.txt                          # Lista para agentes IA
|
+-- validation/                                      # Resultados de testing
    +-- syntax_check/
    +-- shadow_test/
```

---

## Estrategia Claude Code Web vs CLI

| Tarea | Donde Ejecutar | Razón |
|-------|----------------|-------|
| Escaneo inicial (8,122 objetos) | **Claude Code Web** | Larga duración, puede correr en background |
| Migración automática | **Claude Code Web** | Alto volumen, sub-agentes paralelos |
| Decisiones de objetos complejos | **Claude Code CLI** | Interacción rápida con usuario |
| Validación de sintaxis | **Claude Code Web** | Batch processing |
| Shadow testing | **Claude Code CLI** | Requiere acceso a ambas DBs |
| Migración backend | **Claude Code Web** | 30 proyectos, paralel izable |

---

## Integración con ora2pg

**IMPORTANTE:** ora2pg NO se usa para extracción (ya completada con `extract_all_objects.sql`).

**Uso de ora2pg en este proyecto:** SOLO para convertir objetos clasificados como SIMPLES.

**Flujo de uso:**

```bash
# PREREQUISITO: Fase 1 y 2 completadas
# - extracted/*.sql ya existe (extracción manual completada)
# - knowledge/ ya generado (Knowledge Extractor completado)
# - complexity/simple_objects.txt ya existe (Complexity Analyzer completado)

# 1. Instalar ora2pg (una vez)
sudo apt-get install ora2pg  # o equivalente

# 2. Configurar ora2pg.conf para CONVERSIÓN (no extracción)
cat > ora2pg.conf << EOF
ORACLE_HOME /usr/lib/oracle/19.3/client64

# Usar archivos locales extraídos (NO conectar a Oracle)
# ora2pg puede procesar archivos .sql directamente
INPUT_FILE  extracted/

# Solo convertir objetos clasificados como SIMPLES
# Leer lista de complexity/simple_objects.txt
ALLOW       complexity/simple_objects.txt

# Output a directorio simple/
OUTPUT      migrated/simple/

# Tipos a procesar
TYPE        FUNCTION,PROCEDURE,PACKAGE,TRIGGER
EOF

# 3. Ejecutar conversión de objetos SIMPLES
ora2pg -c ora2pg.conf -t FUNCTION -o migrated/simple/functions.sql
ora2pg -c ora2pg.conf -t PROCEDURE -o migrated/simple/procedures.sql
ora2pg -c ora2pg.conf -t PACKAGE -o migrated/simple/packages.sql
ora2pg -c ora2pg.conf -t TRIGGER -o migrated/simple/triggers.sql

# 4. Validar sintaxis de código generado
psql -h localhost -U postgres -d test_db -f migrated/simple/functions.sql
# (verificar que no hay errores de sintaxis)

# 5. Commit código convertido
git add migrated/simple/
git commit -m "Conversión de objetos simples con ora2pg"
git push
```

**Nota sobre objetos COMPLEJOS:**
Los objetos en `complexity/complex_objects.txt` NO se procesan con ora2pg.
Estos requieren agentes IA de Claude Code que puedan tomar decisiones arquitectónicas.

---

**Ver también:**
- [00_index.md](./00_index.md) - Resumen ejecutivo completo
- [01_problem_statement.md](./01_problem_statement.md) - Problema y objetivos
- [02_user_stories.md](./02_user_stories.md) - User Stories detalladas
- [04_decisions.md](./04_decisions.md) - Decisiones técnicas clave
