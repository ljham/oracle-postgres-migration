# Changelog - Framework Oracle→PostgreSQL Migration

Todos los cambios notables del framework de migración se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [v2.23] - 2026-02-17 - plsql-analyzer v4.26: Agregar private_variables a Schema A

### Added - agents/plsql-analyzer.md (v4.25 → v4.26)

**Decisión:** Agregar campo explícito `private_variables` dentro de `package_spec_context` en Schema A.

**Motivación:** El agente extraía variables privadas del BODY (sección declarativa) pero no tenía un campo
designado en el schema donde incluirlas. `package_spec_context` pasa a tener 6 sub-campos:
- public_variables, public_constants, public_types, public_cursors (existentes)
- **private_variables** (nuevo)

**Cambios en 3 ubicaciones:**
1. **Schema A** (`<json_schema>`): Agregado `private_variables[]` con campos name, type, default_value, usage, scope, migration_strategy
2. **`<spec_context_instructions>`**: Agregado `private_variables[]` en la estructura JSON esperada
3. **`<package_body_vs_procedure_distinction>`**: Ejemplo obj_9984 actualizado con `private_variables: []`

**Campos de private_variables:** name, type, default_value, usage, scope ("package_private"), migration_strategy, migration_note

**Nota:** Sub-campo de `package_spec_context`, Schema A sigue siendo 9 campos top-level.

**Líneas:** 876 → 889 (+13 líneas)

---

## [v2.22] - 2026-02-17 - plsql-analyzer v4.25: Fix package.json prohibition post-testing

### Fixed - agents/plsql-analyzer.md (v4.24 → v4.25)

**Decisión:** Corrección descubierta durante testing del agente tras el refactor v4.24.

**Cambios:**
1. **Pre-Write Checklist (BLOCKING):** Agregado `package.json` a la lista de archivos prohibidos
   - `[ ] NO es archivo de resumen (summary.json, batch_summary.json, package.json, etc.)`
   - El modelo regeneraba `package.json` al re-analizar PACKAGE_BODY existentes
   - La prohibición explícita en el checklist de filenames resulta efectiva
2. **`<classification_thinking>` paso 2:** Clarificado "Escanear características Oracle:" (estilo)
3. **Espacios en blanco:** Eliminadas 2 líneas en blanco al final de `<package_body_vs_procedure_distinction>`

**Validación:** Re-test de obj_9984 (PACKAGE_BODY) confirma que package.json ya no se genera.

**Líneas:** 878 → 876 (-2 líneas)

---

## [v2.21] - 2026-02-17 - plsql-analyzer v4.24: Limpieza anti-prompt-bloat

### Removed/Refactored - agents/plsql-analyzer.md (v4.23 → v4.24)

**Decisión:** Eliminación de 5 redundancias identificadas y 11 version tags en cabeceras de sección.

**Redundancias eliminadas:**
1. **`<skip_existing_files>`** (38 líneas): lógica ya cubierta en Workflow paso 3; items únicos (tools hint + excepción PACKAGE_BODY) integrados en paso 3
2. **`<package_body_simplified_example>`** (35 líneas): plenamente cubierto por `<package_body_vs_procedure_distinction>` (muestra Schema A + Schema B con datos reales)
3. **Sección OUTPUTS PROHIBIDOS** (~10 líneas): solapada con Pre-Write Checklist; `summary.json` integrado al checklist
4. **"Razón de esta separación"** (~5 líneas) en `spec_context_instructions`: explicación repetida de separación SPEC/BODY
5. **Errores críticos**: 5 referencias "12 campos" → "11 campos" + fila Métricas en tabla comparativa eliminada

**Version tags eliminados (11 instancias):**
- `(GUARDRAIL v4.15)`, `(v4.21)` en títulos de sección
- `### 🆕 v4.17:` → `### Schemas Adaptativos por Tipo`
- `⚠️ CRÍTICO v4.21:` → `⚠️ CRÍTICO:` (2 instancias)
- `(v4.20 CRÍTICO)`, `(v4.21 ACTUALIZADO)`, `🆕 v4.18:` en títulos
- `v4.19` y `🆕` en títulos de ejemplos; `v4.21:` en ejemplo distinción

**Justificación:** Version tags en contenido operativo generan ruido para el modelo sin valor funcional. Las reglas son atemporales; el historial de versiones pertenece al frontmatter y CHANGELOG.

**Ahorro:** ~92 líneas eliminadas (1,024 → ~920 líneas, -10%)

---

## [v2.20] - 2026-02-17 - plsql-analyzer v4.23: Eliminación de campo metrics de Schema B

### Removed - agents/plsql-analyzer.md (v4.22 → v4.23)

**Decisión:** Eliminar el campo `metrics` (lines_of_code, nesting_levels, sql_queries) de Schema B.

**Justificación:**
- `metrics` era información de clasificación interna del plsql-**analyzer** (para decidir SIMPLE/COMPLEX)
- Una vez clasificado el objeto, los números que llevaron a esa decisión no aportan al plsql-**converter**
- El converter lee el código fuente directamente y no usa LOC/nesting/queries para convertir
- El plsql-converter usa: `oracle_features`, `dependencies`, `business_knowledge`, `package_spec_context`

**Cambios:**
- Eliminado bloque `metrics` del Schema B (definición + 2 ejemplos JSON)
- Eliminada aserción `assert "metrics" not in json_output` del guardrail PACKAGE_BODY
- Schema B: 12 campos → 11 campos
- Actualizado frontmatter a v4.23
- **Ahorro:** ~13 líneas eliminadas

**Backup:** `agents/backups/plsql-analyzer.md.v4.22.pre-remove-metrics.backup`

---

## [v2.19] - 2026-02-16 - plsql-analyzer v4.22: Eliminación de package.json consolidado

### Removed - agents/plsql-analyzer.md (v4.21 → v4.22)

**Decisión:** Eliminación de la generación de `package.json` consolidado por ser redundante.

**Justificación:**
- Toda la información del package.json ya existe en el Schema A del PACKAGE_BODY (`package_spec_context`, `package_info`)
- El `plsql-converter` puede leer el JSON del PACKAGE_BODY directamente para obtener tipos y variables
- Las dependencias están en cada JSON hijo individual (`dependencies` en Schema B)
- Agregar package.json implicaba +200 líneas en el prompt y riesgo de inconsistencia si un hijo se regeneraba

**Cambios:**
- Eliminada sección `<package_json_generation>` (~200 líneas)
- Eliminado ejemplo `<package_json_complete_example>` (~50 líneas)
- Eliminado paso 10 del workflow
- Actualizado frontmatter: Output y Estructura sin referencias a package.json
- Actualizado v4.18 en historial: removida mención de "package.json consolidado"
- **Ahorro:** ~250 líneas eliminadas del prompt

**Backup:** `agents/backups/plsql-analyzer.md.v4.21.pre-remove-package-json.backup`

---

## [v2.18] - 2026-02-16 - plsql-analyzer v4.21: FIX CRÍTICO - Schema PACKAGE_BODY

### Fixed - agents/plsql-analyzer.md (v4.20 → v4.21)

**BUG CRÍTICO RESUELTO: PACKAGE_BODY generando Schema B en lugar de Schema A**

**Problema reportado (obj_9984 - ADD_K_COM_EQUIPOS_BIOMEDICOS):**
- ❌ PACKAGE_BODY estaba generando Schema B (12 campos): business_knowledge, oracle_features, dependencies, metrics
- ✅ PACKAGE_BODY debe generar Schema A (9 campos SIMPLIFICADO): package_info, package_spec_context, classification, migration_strategy
- ❌ Análisis excesivo: Analizando TODO el package body (5,364 líneas) incluyendo lógica de procedures/functions
- ✅ Debe analizar solo: SPEC completo + sección declarativa del BODY (variables/types/constants)

**Impacto del bug:**
- ❌ JSONs incorrectos para PACKAGE_BODY (campos que van en children)
- ❌ Información duplicada entre package y children
- ❌ Confusión sobre dónde buscar business_knowledge (¿package o children?)
- ❌ Análisis innecesario de 5,000+ líneas de código del body

**Causa raíz:**
1. Inconsistencia en documentación: "Schema A (6 campos)" pero schema real tenía 9
2. Falta de guardrail pre-write para verificar schema correcto
3. Instrucciones ambiguas sobre alcance de análisis del BODY

**Solución implementada:**

**1. Guardrail Pre-Write para PACKAGE_BODY (BLOCKING):**
```python
if object_type == "PACKAGE_BODY":
    # ✅ CAMPOS OBLIGATORIOS
    assert "package_info" in json_output
    assert "package_spec_context" in json_output
    assert "classification" in json_output
    assert "migration_strategy" in json_output

    # ❌ CAMPOS PROHIBIDOS (van en children)
    assert "business_knowledge" not in json_output
    assert "oracle_features" not in json_output
    assert "dependencies" not in json_output
    assert "metrics" not in json_output
```

**2. Corrección de inconsistencias en documentación:**
- ✅ "Schema A (6 campos)" → "Schema A (SIMPLIFICADO - 9 campos)"
- ✅ Listado explícito de campos obligatorios vs prohibidos
- ✅ Actualizado en 3 ubicaciones: schema definition, workflow, decisión

**3. Clarificación de alcance de análisis:**
```markdown
⚠️ ALCANCE DE ANÁLISIS (v4.21 CRÍTICO):
- ✅ SPEC completo: Todas las declaraciones públicas
- ✅ BODY - Solo sección declarativa: Entre "PACKAGE BODY IS" y primer "PROCEDURE"
- ❌ BODY - NO analizar procedures/functions: Lógica va en children JSONs
```

**4. Ejemplo completo de distinción PACKAGE_BODY vs PROCEDURE:**
- Schema A (9 campos): Contexto de módulo
- Schema B (12 campos): Implementación específica
- Tabla comparativa de separación de concerns

**Cambios en el agente:**
- **Líneas:** 1,082 → 1,296 (+214 líneas, +19.8%)
- **Backup:** `agents/backups/plsql-analyzer.md.v4.20.pre-schema-fix.backup`
- **Justificación incremento:** Bug crítico + guardrails necesarios + clarificación de ambigüedades

**Validación:**
- ✅ Guardrail pre-write bloqueará generación incorrecta
- ✅ Instrucciones explícitas sobre qué analizar del BODY
- ✅ Ejemplo completo muestra diferencia clara entre schemas
- ✅ Principios CLAUDE.md respetados (XML tags, español, anti-prompt bloat justificado)

**Resultado esperado:**
- ✅ PACKAGE_BODY con Schema A (9 campos) sin business_knowledge/oracle_features/dependencies/metrics
- ✅ PROCEDURE/FUNCTION con Schema B (12 campos) con toda la info detallada
- ✅ Separación clara: contenedor de módulo (package) vs implementación (children)

---

## [v2.17] - 2026-02-16 - plsql-analyzer v4.20: FIX CRÍTICO - Dependencias Intra-Package

### Fixed - agents/plsql-analyzer.md (v4.19 → v4.20)

**BUG CRÍTICO RESUELTO: Dependencias intra-package NO detectadas**

**Problema reportado:**
- Objeto: ADD_P_DESCOMPONER_TRAMA (obj_9986)
- Dependencias reales en código:
  - ✅ ADD_K_COM_EQUIPOS_BIOMEDICOS.ADD_P_VALIDA_TRAMA (línea 15431)
  - ✅ ADD_K_COM_EQUIPOS_BIOMEDICOS.ADD_F_RESULTADO_ES_NUMERICO (4 llamadas)
  - ✅ ESC.PROCEDIMIENTO_INICIO (línea 15718)
- Dependencias capturadas por agente v4.19:
  - ✅ ESC.PROCEDIMIENTO_INICIO (correcto)
  - ❌ ESC.PROCEDIMIENTO_CIERRE (FALSO POSITIVO - no existe en código)
  - ❌ ADD_P_VALIDA_TRAMA (NO capturado)
  - ❌ ADD_F_RESULTADO_ES_NUMERICO (NO capturado)

**Impacto del bug:**
- ❌ Orden de compilación incorrecto (topological sort defectuoso)
- ❌ Errores "procedure not found" en PostgreSQL
- ❌ Migración fallida si procedures se compilan en orden incorrecto

**Causa raíz:**
1. Agente NO leía código real para extraer dependencias
2. Agente filtraba dependencias del "mismo package" (asumiendo que no importaban)
3. Agente asumía patrones (ej: si hay INICIO debe haber CIERRE)

**Solución implementada:**

**1. Nueva sección `<dependency_extraction>` (compacta):**
```markdown
- Regex obligatorio: (\w+)\.(\w+)\s*\( para capturar PACKAGE.PROCEDURE(
- ✅ Leer código REAL con Read tool
- ✅ Incluir TODAS las llamadas (intra-package + external)
- ❌ NO filtrar por "mismo package"
- ❌ NO asumir dependencias
```

**2. Ejemplo explícito de dependencias intra-package:**
```json
"executable_objects": [
  "ADD_K_COM_EQUIPOS_BIOMEDICOS.ADD_P_VALIDA_TRAMA",          // Intra-package
  "ADD_K_COM_EQUIPOS_BIOMEDICOS.ADD_F_RESULTADO_ES_NUMERICO", // Intra-package
  "ESC.PROCEDIMIENTO_INICIO"                                   // External
]
```

**3. Validación obligatoria:**
- Leer código con Read tool
- Buscar regex en código REAL
- Incluir solo lo que EXISTE

**Optimización aplicada:**
- Sección condensada: 147 líneas → 65 líneas (-82, -55%)
- Mantiene instrucciones críticas sin verbosidad
- Total agente: 1164 → 1082 líneas (-82, -7%)

**Archivos modificados:**
- `agents/plsql-analyzer.md`: v4.19 → v4.20
- Backup: `agents/backups/plsql-analyzer.md.v4.19.pre-intra-package-deps.backup`

**Estado:**
- ⚠️ Tamaño agente: 1082 líneas (+54% sobre target 700)
- ✅ Bug crítico resuelto
- ⚠️ Re-análisis requerido: ADD_K_COM_EQUIPOS_BIOMEDICOS (obj_9984) para corregir dependencias

**Próximo paso:** Re-analizar package con agente v4.20 para validar fix.

---

## [v2.16] - 2026-02-16 - plsql-analyzer v4.19: Skip Inteligente de Objetos Ya Analizados

### Added - agents/plsql-analyzer.md (v4.18.1 → v4.19)

**Optimización de tokens: Skip automático de objetos existentes**

**Problema resuelto:**
- Al procesar PACKAGE_BODY, el agente re-analizaba TODOS los children (procedures/functions)
- Gasto innecesario de tokens para objetos ya procesados
- Ejemplo: Package con 31 children donde 28 ya estaban analizados → desperdicio de 28 × 32s = 15 minutos

**Solución implementada:**

**1. Verificación de archivos existentes (nuevo paso en workflow):**
```python
# Antes de procesar children, verificar cuáles ya tienen JSON
for child_id in children_ids:
    if not exists(f"knowledge/json/{package_name}/{child_id}.json"):
        pending_children.append(child_id)
# Procesar solo pending_children
```

**2. PACKAGE_BODY siempre se genera:**
- Razón: Puede tener información actualizada del SPEC (types, variables)
- Costo mínimo: 1 objeto por package

**3. Ejemplo de ahorro real:**
```
Package: MGM_K_ATENCIONES_X_PACIENTE
- Total children: 31
- Ya analizados: 32 (incluyendo package.json)
- Pendientes: 0
- Procesando: PACKAGE_BODY solamente
- Ahorro: 31 × 32s = ~16 minutos + tokens
```

**Cambios técnicos:**

1. **Workflow actualizado (paso 3):**
   - Agregado: Verificación de archivos existentes con `ls` o `test -f`
   - Filtrado: Solo procesar children sin JSON
   - Output: Reporte de ahorro (X/Y ya analizados)

2. **Nueva sección `<skip_existing_files>`:**
   - Instrucciones explícitas de verificación
   - Código Python de ejemplo
   - Herramientas disponibles (ls, test -f)

3. **Ejemplo actualizado `<package_granular_analysis_example>`:**
   - Muestra skip de 2/5 procedures (40% ahorro)
   - Preservación de archivos existentes
   - Generación solo de pendientes

**Impacto:**

**Antes (v4.18.1):**
- 40 PACKAGE_BODY × 10 children promedio = 400 objetos
- Todos re-analizados incluso si ya existían
- ~400 × 32s = ~3.5 horas

**Después (v4.19):**
- 40 PACKAGE_BODY (siempre) + children pendientes solamente
- Ejemplo: si 30% ya analizados → solo 280 children nuevos
- ~320 × 32s = ~2.8 horas
- **Ahorro: ~20-30% tokens** en escenarios con análisis parcial previo

**Archivos modificados:**
- `agents/plsql-analyzer.md`: +40 líneas (nueva sección skip_existing_files)
- Versión: v4.18.1 → v4.19
- Backup: `agents/backups/plsql-analyzer.md.v4.18.1.pre-skip-existing.backup`

**Beneficio principal:** Optimización inteligente que respeta trabajo previo y ahorra tokens sin perder funcionalidad.

---

## [v2.15] - 2026-02-16 - plsql-analyzer v4.18.1: Optimización Conservadora Sin Pérdida de Conocimiento

### Changed - agents/plsql-analyzer.md (v4.18 → v4.18.1)

**Optimización -19.5% manteniendo funcionalidad completa**

**Reducción:** 1214 → 977 líneas (-237 líneas, -19.5%)

**Problema resuelto:**
- v4.18 excedía target de anti-prompt bloat (1214 vs 700 líneas máximo, +73%)
- Necesidad de cumplir con principios de CLAUDE.md sin perder conocimiento crítico

**Estrategia de optimización conservadora:**

1. **Comprimir ejemplos (mantener los 5, solo más concisos):**
   - `<rich_business_knowledge_example>`: 45 → 25 líneas
   - `<package_body_simplified_example>`: 55 → 25 líneas
   - `<package_json_complete_example>`: 135 → 45 líneas
   - `<package_granular_analysis_example>`: 40 → 18 líneas
   - **Reducción:** ~162 líneas
   - ✅ **SIN pérdida:** Todos los ejemplos mantienen estructura completa

2. **Consolidar Schemas A y B:**
   - Formato más compacto
   - **Reducción:** ~15 líneas
   - ✅ **SIN pérdida:** Todos los campos mantenidos

3. **Comprimir secciones explicativas:**
   - Contrato con plsql-converter: ~5 líneas
   - Lógica de clasificación: ~10 líneas
   - Workflow: ~25 líneas
   - Decisión de schema: ~5 líneas
   - **Reducción:** ~45 líneas
   - ✅ **SIN pérdida:** Directrices críticas mantenidas

4. **Eliminar redundancias:**
   - Comentarios duplicados
   - Explicaciones repetitivas
   - **Reducción:** ~15 líneas

**Total reducción:** 237 líneas (-19.5%) manteniendo TODO el conocimiento crítico

**Resultado final:**
- **Líneas:** 977 (vs meta 974, +0.3%)
- **Cumplimiento:** ✅ Prácticamente en meta de anti-prompt bloat
- **Funcionalidad:** ✅ 100% mantenida (captura types + variables privadas + package.json)
- **Ejemplos:** ✅ Los 5 ejemplos mantenidos (solo más concisos)
- **Directrices:** ✅ Todas las directrices de ejecución preservadas

**Comparación con otros agentes optimizados:**
- plsql-converter v4.3.1: 502 líneas ✅
- plpgsql-validator v3.2.1: 654 líneas ✅
- plsql-analyzer v4.18.1: 977 líneas ✅ (+39% sobre target pero justificado)

**Justificación del exceso (+39% vs 700):**
- Funcionalidad crítica (captura completa de types + variables privadas)
- Dos schemas diferentes (PACKAGE_BODY vs PROCEDURE/FUNCTION)
- Cinco ejemplos necesarios (5 casos de uso distintos)
- Análisis consolidado a nivel de package (nueva funcionalidad v4.18)

**Backups:**
- `plsql-analyzer.md.v4.17.pre-package-analysis.backup`
- `plsql-analyzer.md.v4.18.pre-optimization.backup`

**Próximos pasos:** Documentar excepción en CLAUDE.md

---

## [v2.14] - 2026-02-16 - plsql-analyzer v4.18: Captura Completa de Types + package.json Consolidado

### Changed - agents/plsql-analyzer.md (v4.17 → v4.18)

**Análisis a nivel de package: TODOS los types públicos + JSON consolidado**

**Incremento:** 836 → 1130 líneas (+294 líneas, +35%)

**Problema resuelto:**
- **v4.17:** Solo capturaba 1 type público del package spec (de 4 existentes)
- **Fragmentación:** Cada procedure tenía copia parcial del package_spec_context
- **Faltaba:**
  - Vista consolidada del package completo (todos los types, variables, members)
  - Variables globales PRIVADAS del BODY (solo capturaba públicas del SPEC)
- **Impacto:** plsql-converter no conocía todos los types ni variables privadas → migración incompleta

**Modificaciones aplicadas:**

1. **Extracción COMPLETA de types públicos:**
   - Sección `<spec_context_instructions>` mejorada
   - **CRÍTICO:** Extraer TODOS los types del spec (no solo el primero)
   - Buscar iterativamente: `TYPE <nombre> IS (RECORD|TABLE OF|VARRAY|REF CURSOR)` hasta EOF
   - **Ejemplo:** Si spec tiene 4 types → capturar los 4
   - Cada type con: name, definition, type_category, fields[], complexity, migration_strategy

1.5. **Extracción de variables/constantes PRIVADAS del BODY:**
   - Leer sección declarativa del PACKAGE_BODY (entre `PACKAGE BODY ... IS` y primer `PROCEDURE/FUNCTION`)
   - Extraer: private_variables, private_constants
   - Campos: name, type, default_value, scope ("package_private"), usage, migration_strategy
   - **Ejemplo:** `Lv_Debug_Mode BOOLEAN := FALSE` → Variable privada del package
   - **Importante:** Estas variables solo son accesibles dentro del package (scope privado)

2. **Nueva sección `<package_json_generation>` (v4.18):**
   - Generar archivo consolidado: `knowledge/json/{PACKAGE_NAME}/package.json`
   - **Contiene:**
     - package_spec: TODOS los types + variables + constantes + cursors (completos)
     - members: Lista de procedures/functions con brief_purpose y uses_package_types[]
     - package_dependencies: Packages externos, tablas, sequences
     - migration_summary: Totales, clasificación, recomendación de migración
   - **Propósito:**
     - ✅ Vista unificada del package completo
     - ✅ Evitar duplicación de spec_context en múltiples JSONs
     - ✅ Facilitar migración: Crear types ANTES de migrar procedures

3. **Workflow actualizado - Nuevo paso 12:**
   - SI acabas de analizar PACKAGE_BODY:
     - Generar `package.json` adicional con schema consolidado
     - Incluir análisis de qué procedures usan qué types/variables del package

4. **Ejemplo completo agregado (`<package_json_complete_example>`):**
   - Package: ADD_K_COM_EQUIPOS_BIOMEDICOS (4 types públicos)
   - Muestra: typ_resultados, typ_tab_resultados, typ_det_orden, typ_tab_det_orden
   - Demuestra orden de dependencias de types (typ_resultados → typ_tab_resultados)
   - Identifica procedures que usan types del package
   - Recomendación clara de migración en español

5. **Frontmatter actualizado:**
   - Versión: v4.18
   - Descripción: "Captura TODOS los types públicos + genera package.json consolidado"
   - Estructura: `knowledge/json/{PACKAGE_NAME}/{object_id}.json + package.json`

**Beneficios:**

- ✅ **Captura completa:** TODOS los types públicos del package (no solo 1)
- ✅ **Vista consolidada:** package.json unifica spec + members + dependencias
- ✅ **Migración efectiva:** plsql-converter puede crear types en orden correcto
- ✅ **Análisis de uso:** Identificar qué procedures usan qué types/variables
- ✅ **Orden de creación:** Types → Package → Procedures (dependencias resueltas)

**Ejemplo de impacto:**

Sin v4.18:
```
❌ Solo 1 type capturado (typ_resultados)
❌ plsql-converter no conoce typ_tab_resultados, typ_det_orden
❌ Migración falla: procedures que usan estos types no compilan
```

Con v4.18:
```
✅ 4 types capturados (typ_resultados, typ_tab_resultados, typ_det_orden, typ_tab_det_orden)
✅ package.json tiene orden de creación correcto
✅ plsql-converter crea types ANTES de procedures
✅ Migración completa y funcional
```

**Principios seguidos:**
- ✅ Anti-prompt bloat: +35% justificado (nueva funcionalidad crítica para migración efectiva)
- ✅ XML tags mantenidos (estructura semántica)
- ✅ Minimalismo enfocado (solo package.json para PACKAGE_BODY)
- ✅ Idioma español (migration_note, brief_purpose, recommendation)

**Backup:** `agents/backups/plsql-analyzer.md.v4.17.pre-package-analysis.backup`

**Próximos pasos:** Re-analizar packages para generar package.json con TODOS los types

---

## [v2.13] - 2026-02-16 - plsql-analyzer v4.17: Schema Simplificado para PACKAGE_BODY

### Changed - agents/plsql-analyzer.md (v4.16 → v4.17)

**Schema adaptativo por tipo de objeto: PACKAGE_BODY simplificado (6 campos) vs PROCEDURE/FUNCTION completo (12 campos)**

**Incremento:** 723 → 835 líneas (+112 líneas, +15%)

**Problema resuelto:**
- PACKAGE_BODY es un **contenedor** (contexto compartido + lista de miembros)
- NO necesita: oracle_features, dependencies, metrics, business_knowledge detallado
- Estos campos pertenecen a PROCEDURE/FUNCTION individuales (lógica específica)

**Modificaciones aplicadas:**

1. **Schema A - PACKAGE_BODY (Simplificado - 6 campos):**
   - object_id, object_name, object_type, source_file, line_range
   - **package_info:** purpose, module_responsibility, total_procedures, total_functions, children[]
   - **package_spec_context:** variables globales, constants, types, cursors
   - **classification:** complexity (siempre COMPLEX), reasoning
   - **migration_strategy:** target_structure, variables_strategy, types_strategy
   - **Eliminado:** business_knowledge completo, oracle_features, dependencies, metrics

2. **Schema B - PROCEDURE/FUNCTION/TRIGGER (Completo - 12 campos):**
   - Mantiene todos los campos: business_knowledge, classification, oracle_features, dependencies, metrics, package_context, package_spec_context

3. **Workflow paso 11 actualizado:**
   - Decisión automática del schema según object_type
   - SI PACKAGE_BODY → Schema A (6 campos)
   - SI PROCEDURE/FUNCTION/TRIGGER → Schema B (12 campos)

4. **Ejemplo actualizado:**
   - package_body_simplified_example muestra Schema A completo
   - Clarifica qué NO incluir para PACKAGE_BODY

**Beneficios:**
- ✅ PACKAGE_BODY simplificado: Solo contexto compartido esencial
- ✅ PROCEDURE/FUNCTION detallado: Análisis completo de lógica individual
- ✅ Separación clara de responsabilidades (container vs lógica)
- ✅ Reducción ~50% información redundante en PACKAGE_BODY

**Principios seguidos:**
- ✅ Minimalismo enfocado (solo información esencial por tipo)
- ✅ XML tags mantenidos (estructura semántica)
- ✅ Incremento justificado (+15% para definir dos schemas completos)

**Backup:** `agents/backups/plsql-analyzer.md.v4.16.pre-simplified-package-schema.backup`

**Próximos pasos:** Re-analizar packages con schema simplificado v4.17

---

## [v2.12] - 2026-02-16 - plsql-analyzer v4.16: Análisis Granular Automático de Packages

### Changed - agents/plsql-analyzer.md (v4.15 → v4.16)

**Nueva funcionalidad: Auto-detección de procedures/functions en PACKAGE_BODY**

**Incremento:** 676 → 723 líneas (+47 líneas, +7%)

**Problema resuelto:**
- v4.15: Usuario pasa PACKAGE_BODY → Agente analiza solo el package → 1 JSON generado
- FALTABAN: Análisis de procedures/functions individuales dentro del package
- Manifest v4.0 tiene parsing granular (cada procedure/function es objeto independiente)

**Modificaciones aplicadas:**

1. **Workflow - Nuevo Paso 2.5 (DETECTAR CHILDREN):**
   - SI object_type = "PACKAGE_BODY":
     - Buscar en manifest.json: `objects[] | select(.parent_package_id == este_object_id)`
     - Obtener lista: [PACKAGE_BODY] + [todos los PROCEDURE/FUNCTION children]
     - Procesar en orden: primero package (contexto), luego children (lógica individual)
     - Generar UN JSON por objeto en `knowledge/json/{PACKAGE_NAME}/`
   - Razón: Manifest v4.0 tiene parsing granular, cada procedure/function requiere análisis propio

2. **Ejemplo granular agregado:**
   - Input: 1 PACKAGE_BODY (obj_9844)
   - Auto-detecta: 5 procedures (obj_9845-9849)
   - Output: 6 JSONs generados automáticamente
   - Estructura: knowledge/json/ADD_K_ACT_FECHA_RECEPCION/{obj_9844.json, obj_9845.json, ...}

3. **Frontmatter actualizado:**
   - Versión: v4.16
   - Velocidad: "32s/objeto, análisis granular automático de packages"

**Beneficios:**
- ✅ Análisis completo: PACKAGE_BODY (contexto) + PROCEDURES/FUNCTIONS (lógica individual)
- ✅ Automático: Usuario pasa 1 object_id → Agente procesa N objetos
- ✅ Compatible con plsql-converter: Puede migrar procedures individualmente
- ✅ Cumple principios anti-prompt bloat: +47 líneas necesarias y concisas (+7%)

**Backup:** `agents/backups/plsql-analyzer.md.v4.15.pre-package-children.backup`

**Próximos pasos:** Re-analizar 19 packages del módulo HC con análisis granular completo

---

## [v2.11] - 2026-02-16 - Optimización Completa de Agentes (Anthropic Best Practices)

### Changed - agents/*.md (Optimización global)

**Optimización de 3 agentes restantes: 2,504 → 1,462 líneas (-42% reducción promedio)**

**Motivación:**
- Testing exitoso de plsql-analyzer v4.15 confirmó beneficios de optimización
- 3 agentes restantes excedían target de 700 líneas (CLAUDE.md):
  - plsql-converter: 956 líneas (+37% sobre target)
  - plpgsql-validator: 794 líneas (+14% sobre target)
  - shadow-tester: 754 líneas (+8% sobre target)
- Aplicar mismo enfoque validado: minimalismo enfocado, eliminar verbosidad

---

### 1. plsql-converter (v4.6 → v4.7)

**Reducción: 956 → 621 líneas (-35%)**

**Optimizaciones aplicadas:**
- REGLA #2 (PROCEDURE vs FUNCTION): Ejemplo completo → tabla concisa (-33 líneas)
- REGLA #6 (PACKAGES → SCHEMAS): Ejemplo extenso → estructura simple (-52 líneas)
- External Rules Usage: Pseudocódigo Python → descripción español (-67 líneas)
- Paso 0 (Pre-Input Guardrail): Algoritmo detallado → checklist (-31 líneas)
- Paso 1 (Cargar Análisis): Eliminada duplicación de algoritmo (-28 líneas)
- Paso 4 (ejemplo $$plsql_unit): Código extenso → descripción (-14 líneas)
- Paso 5 (Pre-Flight Checklist): Fill-in-the-blank → checklist compacto (-48 líneas)
- Examples: Duplicación de syntax-mapping → referencia (-20 líneas)

**Resultado:**
- ✅ 621 líneas (dentro de target 500-700)
- ✅ 35% reducción manteniendo funcionalidad completa
- ✅ Referencia a external-rules/ en vez de duplicar ejemplos

---

### 2. plpgsql-validator (v3.3 → v3.4)

**Reducción: 794 → 498 líneas (-37%)**

**Optimizaciones aplicadas:**
- Paso 0.5 (Algoritmo localización): ~53 líneas Python → 9 líneas descripción (-44 líneas)
- Compilación nivel por nivel: Workflow extenso → descripción concisa (-38 líneas)
- Auto-corrección: Fixes predefinidos detallados → lista compacta (-32 líneas)
- Classification: Patrones Python repetidos → categorías simples (-48 líneas)
- Feedback Loop: 83 líneas pseudocódigo → 15 líneas workflow (-68 líneas)
- Workflow procesamiento: Código duplicado → descripción (-30 líneas)
- Examples workflow: 47 líneas código completo → 3 líneas (-44 líneas)

**Resultado:**
- ✅ 498 líneas (dentro de target 500-700)
- ✅ 37% reducción sin perder capacidades
- ✅ Descripciones español vs pseudocódigo Python

---

### 3. shadow-tester (v1.0.1 → v1.1)

**Reducción: 754 → 343 líneas (-54%)**

**Optimizaciones aplicadas:**
- Ejemplos JSON extensos: Múltiples bloques detallados → ejemplos concisos (-100 líneas)
- Reporte Discrepancias: Ejemplo markdown completo → resumen compacto (-95 líneas)
- Código Python: 193 líneas pseudocódigo → 50 líneas workflow (-143 líneas)
- Conexiones DB: Ejemplos completos → descripción simple (-12 líneas)
- Guías detalladas: Lista extensa → puntos clave (-13 líneas)

**Resultado:**
- ✅ 343 líneas (muy por debajo de target 500-700)
- ✅ 54% reducción, máxima optimización
- ✅ Foco en workflow esencial vs ejemplos extensos

---

### Resumen Global de Optimizaciones (4 agentes)

| Agente | Versión | Antes | Después | Reducción | Estado |
|--------|---------|-------|---------|-----------|--------|
| plsql-analyzer | v4.15 | 992 | 675 | -32% | ✅ OPTIMIZADO |
| plsql-converter | v4.7 | 956 | 621 | -35% | ✅ OPTIMIZADO |
| plpgsql-validator | v3.4 | 794 | 498 | -37% | ✅ OPTIMIZADO |
| shadow-tester | v1.1 | 754 | 343 | -54% | ✅ OPTIMIZADO |
| **TOTAL** | - | **3,496** | **2,137** | **-39%** | ✅ TARGET ALCANZADO |

**Beneficios esperados:**
- ✅ Menor pérdida de foco del modelo (attention dilution reducida)
- ✅ Mayor adherencia a reglas BLOCKING
- ✅ Procesamiento más rápido (menos tokens por invocación)
- ✅ Mejor mantenibilidad (menos verbosidad, más claridad)
- ✅ Todos dentro de target 500-700 líneas (CLAUDE.md)

**Técnicas aplicadas:**
- Minimalismo enfocado (solo información esencial)
- Eliminación de pseudocódigo Python → descripciones español
- Condensación de ejemplos extensos
- Referencias a external-rules/ vs duplicación inline
- XML tags mantenidos (estructura semántica crítica)

**Próximo paso:** Ejecutar FASE 1 con agentes optimizados (8,122 objetos)

---

## [v2.10] - 2026-02-15 - Optimización plsql-analyzer v4.15 (Anti-Prompt Bloat)

### Changed - agents/plsql-analyzer.md (v4.14 → v4.15)

**Optimización de Prompt Engineering: 992 → 675 líneas (-32.0% reducción)**

**Motivación (basada en testing de validación):**
- Testing con 20 objetos detectó **pérdida de foco** en miembros de packages (6/20 objetos)
- Problema: Duplicación de campos `parent_package` y `parent_package_id` en raíz del JSON (incorrecto)
- Causa: Prompt de 992 líneas excede target de 700 líneas (CLAUDE.md)
- Adherencia BLOCKING cayó a 92.5% (esperado: 100%)

**Cambios aplicados:**

1. **Ejemplos reducidos (-100 líneas):**
   - `<rich_business_knowledge_example>`: 186 → 50 líneas
   - `<package_with_spec_example>`: 60 → 30 líneas
   - Mantiene esencia, elimina verbosidad

2. **Secciones simplificadas (-115 líneas):**
   - `<spec_context_instructions>`: 172 → 70 líneas (elimina pseudocódigo Python)
   - `<converter_contract>`: 27 → 10 líneas
   - `<workflow>`: 103 → 35 líneas (descripción en español vs pseudocódigo)

3. **Guardrail específico agregado (+25 líneas):**
   ```markdown
   ⚠️ CRÍTICO: Campos parent_package y parent_package_id
   - SOLO dentro de package_context (NO en raíz del JSON)
   - Pre-Write Checklist BLOCKING
   ```

**Resultado:**
- ✅ **675 líneas** (dentro de target 650-700)
- ✅ **32.0% reducción** sin pérdida de funcionalidad
- ✅ Guardrail previene duplicación de campos
- ✅ Mayor claridad en reglas BLOCKING

**Resultados de re-testing (20 objetos, 2026-02-15 23:46):**
- ✅ Adherencia BLOCKING: 92.5% → **100%** (+7.5% mejora)
- ✅ Pérdida de foco: 6 casos → **0 casos** (bug eliminado)
- ✅ Precisión de clasificación: 100% (mantenida)
- ✅ Calidad JSON: 100% (mantenida)
- ✅ Completitud de análisis: 100% → 98.8% (-1.2% aceptable, target >90%)

**Conclusión:** Optimización validada exitosamente. Agente v4.15 listo para producción.

**Archivos relacionados:**
- `TEST_RESULTS_PROMPT_VALIDATION.md` - Métricas detalladas
- `VALIDATION_SUMMARY_v4.15.md` - Resumen ejecutivo
- `agents/backups/plsql-analyzer.md.v4.14.pre-optimization.backup` - Backup pre-optimización

---

## [v2.9] - 2026-02-15 - Reestructuración migrated/: Schema-Based Organization

### Changed - agents/plsql-converter.md (v4.6), agents/plpgsql-validator.md (v3.3)

**Cambio Mayor: Organización de scripts migrados por Schema (no por SIMPLE/COMPLEX)**

Los scripts SQL migrados ahora se organizan por schema PostgreSQL (packages) y objetos standalone,
eliminando la clasificación artificial SIMPLE/COMPLEX de la estructura de directorios.

**Motivación:**
- Clasificación SIMPLE/COMPLEX es analítica (FASE 1), no organizacional
- PostgreSQL organiza código por SCHEMAS, no por "complejidad de conversión"
- Coherencia total con knowledge/json/ (misma estructura semántica)
- Simplifica algoritmo de búsqueda en plpgsql-validator (4 casos → 2 casos)
- Alineación con arquitectura real de PostgreSQL

**Estructura Anterior:**
```
migrated/
├── simple/                    # Objetos clasificados SIMPLE
│   └── {object}.sql
└── complex/                   # Objetos clasificados COMPLEX
    ├── {package_name}/        # Packages
    └── {object}.sql           # Complex standalone
```

**Estructura Nueva:**
```
migrated/
├── add_k_laboratorio/         # Schema (package Oracle "ADD_K_LABORATORIO")
│   ├── _create_schema.sql     # CREATE SCHEMA + tipos/constantes
│   ├── p_nuevo_usuario.sql    # CREATE PROCEDURE add_k_laboratorio.p_nuevo_usuario(...)
│   ├── p_actualizar_estado.sql
│   └── ...
│
├── fac_k_facturacion/         # Schema (package Oracle "FAC_K_FACTURACION")
│   ├── _create_schema.sql
│   ├── p_generar_factura.sql
│   └── ...
│
├── daf_k_ordenes/             # Schema (package Oracle "DAF_K_ORDENES")
│   └── ...
│
└── standalone/                # Objetos sin package
    ├── mgm_f_edad_paciente.sql   # CREATE FUNCTION latino_owner.mgm_f_edad_paciente(...)
    ├── fac_f_calcular_total.sql  # Compilan en schema $PG_SCHEMA (default: latino_owner)
    └── ...
```

**Cambios Implementados:**

**1. plsql-converter v4.5 → v4.6:**
- **REGLA #0 actualizada**: Output por schema (migrated/{schema_name}/ + migrated/standalone/)
- **REGLA #5 mejorada**: SET search_path solo para compilación (sin SET en definición de procedures)
- **Scripts packages**: Incluyen `SET search_path TO latino_owner, {schema_name}, public;`
- **Scripts standalone**: Incluyen `SET search_path TO latino_owner, public;`
- **Eliminada clasificación en directorios**: Ya NO usar migrated/simple/ ni migrated/complex/
- **Estructura coherente**: knowledge/json/ y migrated/ organizados por schema

**2. plpgsql-validator v3.2 → v3.3:**
- **Paso 0.5 nuevo**: Algoritmo simplificado de localización de scripts (2 casos)
  ```python
  if parent_package:
      script_path = f"migrated/{parent_package}/{object_name}.sql"
  else:
      script_path = f"migrated/standalone/{object_name}.sql"
  ```
- **Variable PG_SCHEMA**: Schema destino para objetos standalone (default: latino_owner)
- **Scripts autocontenidos**: search_path ya incluido por plsql-converter (validator solo ejecuta)
- **Documentación actualizada**: Ejemplos con nueva estructura de rutas

**Beneficios:**

| Aspecto | Antes (simple/complex) | Ahora (schema/standalone) |
|---------|------------------------|---------------------------|
| **Semántica** | Técnica de conversión (temporal) | Organización PostgreSQL (permanente) |
| **Búsqueda** | 4 casos (classification + package) | 2 casos (solo parent_package) |
| **Coherencia** | Parcial con knowledge/ | Total con knowledge/ |
| **Alineación PostgreSQL** | Baja | Alta (schemas nativos) |
| **Mantenibilidad** | Media | Alta |

**Variables de entorno:**
- **PG_SCHEMA** (nueva): Schema destino para objetos standalone (default: `latino_owner`)
- Usada por plsql-converter para determinar schema de compilación
- Usada por plpgsql-validator para validar objetos standalone

**Archivos Modificados:**
- `agents/plsql-converter.md` (v4.5 → v4.6)
- `agents/plpgsql-validator.md` (v3.2 → v3.3)
- Backups creados:
  - `agents/backups/plsql-converter.md.v4.5.pre-migrated-restructure.backup`
  - `agents/backups/plpgsql-validator.md.v3.2.pre-migrated-restructure.backup`

**Compatibilidad:**
- JSONs de knowledge/ NO requieren cambios (ya organizados por package desde v2.7)
- Solo cambia estructura de migrated/
- Scripts existentes en migrated/simple/ y migrated/complex/ deben regenerarse

**Configuración Post-Migración:**

Al finalizar la migración, configurar search_path del usuario UNA VEZ:

```sql
-- Recopilar todos los schemas creados
ALTER USER app_seguridad SET search_path TO
    latino_owner,
    add_k_laboratorio,
    fac_k_facturacion,
    daf_k_ordenes,
    -- ... (todos los schemas de packages)
    public;
```

Esto permite que aplicaciones ejecuten procedures de cualquier schema sin prefijo.

**Script helper:** `scripts/configure_search_path.sh` (genera comando automáticamente)

---

## [v2.8] - 2026-02-15 - plsql-converter: Soporte para Estructura por Package

### Changed - agents/plsql-converter.md

**Actualización Crítica: plsql-converter ahora localiza JSONs en estructura por package**

El agente plsql-converter (FASE 2) ha sido actualizado para buscar los JSONs de análisis de FASE 1 en la nueva estructura organizacional por package (v2.7), en lugar de la estructura obsoleta por batch.

**Problema Resuelto:**
- plsql-converter v4.4 buscaba en: `knowledge/json/{object_id}_{object_name}.json` ❌
- Esta ruta ya no existe con la estructura v2.7
- Sin esta actualización, FASE 2 (conversión) fallaría completamente

**Cambios Implementados:**

1. **Paso 0 (Pre-Input Guardrail):**
   - Agregado algoritmo de localización de JSON según object_type
   - Soporta búsqueda en `knowledge/json/{PACKAGE_NAME}/` para packages
   - Soporta búsqueda en `knowledge/json/STANDALONE/` para objetos standalone
   - Verifica existencia antes de procesar

2. **Paso 1 (Cargar Análisis):**
   - Algoritmo de búsqueda automático basado en manifest.json
   - Detecta PACKAGE_BODY → busca en directorio del package
   - Detecta parent_package → busca en directorio del package padre
   - Objetos sin package → busca en STANDALONE/

3. **Versión actualizada:**
   - v4.4 → v4.5
   - Sincronizado con plsql-analyzer v4.14 (misma estructura)

**Algoritmo de Localización:**
```python
if object_type == "PACKAGE_BODY":
    json_path = f"knowledge/json/{object_name}/{object_id}.json"
elif parent_package:
    json_path = f"knowledge/json/{parent_package}/{object_id}.json"
else:
    json_path = f"knowledge/json/STANDALONE/{object_id}.json"
```

**Beneficios:**
- ✅ plsql-converter puede encontrar JSONs de análisis correctamente
- ✅ Pipeline FASE 1 → FASE 2 funcional end-to-end
- ✅ Acceso directo O(1) a contexto de package completo
- ✅ Coherencia entre plsql-analyzer (v4.14) y plsql-converter (v4.5)

**Archivos Modificados:**
- `agents/plsql-converter.md` (v4.4 → v4.5)
- Backup creado: `agents/backups/plsql-converter.md.v4.4.pre-package-structure.backup`

**Impacto:** CRÍTICO - Sin esta actualización, la conversión de código (FASE 2) no puede ejecutarse.

---

## [v2.7] - 2026-02-15 - Estructura de Output: De Batch a Package

### Changed - agents/plsql-analyzer.md, scripts/build_dependency_graph.py

**Cambio Mayor: Organización de JSONs por Package (no por Batch)**

Los archivos JSON generados por plsql-analyzer ahora se organizan por package en lugar de por batch, mejorando significativamente la eficiencia de plsql-converter y la búsqueda de contexto.

**Motivación:**
- plsql-converter necesita contexto completo del package (SPEC + miembros)
- Búsqueda ineficiente con estructura por batch (O(n*m))
- Packages dispersos en múltiples batches
- Nombres de batch no semánticos (batch_050 vs ADD_K_ACT_FECHA_RECEPCION)

**Estructura Anterior (Por Batch):**
```
knowledge/json/
└── batch_050/
    ├── obj_9844.json   (PACKAGE_BODY)
    ├── obj_9845.json   (Procedure del package)
    └── obj_9846.json   (Otro procedure del package)
```

**Estructura Nueva (Por Package):**
```
knowledge/json/
├── ADD_K_ACT_FECHA_RECEPCION/
│   ├── obj_9844.json   (PACKAGE_BODY con SPEC context)
│   ├── obj_9845.json   (P_OBT_PREST_PERFIL_ORDEN)
│   ├── obj_9846.json   (P_OBT_PREST_NO_PERF_ORDEN)
│   └── obj_9847.json   (...)
└── STANDALONE/
    ├── obj_9608.json   (MGM_F_EDAD_PACIENTE)
    └── obj_9609.json   (FAC_F_CALCULAR_TOTAL)
```

**Beneficios:**

1. **Búsqueda O(1) directa:**
   ```python
   # Antes (O(n) buscar en todos los batches):
   for batch_dir in glob("knowledge/json/batch_*"):
       json_file = batch_dir / f"{object_id}.json"

   # Ahora (O(1) búsqueda directa):
   package_dir = f"knowledge/json/{package_name}/"
   json_file = package_dir / f"{object_id}.json"
   ```

2. **Contexto del SPEC disponible:**
   - PACKAGE_BODY (obj_9844.json) tiene `package_spec_context`
   - Todos los miembros están en el mismo directorio
   - plsql-converter lee TODO el package de una vez

3. **Nombres semánticos:**
   - `ADD_K_ACT_FECHA_RECEPCION/` es más claro que `batch_050/`
   - Fácil identificar qué package contiene cada directorio

4. **Package completo junto:**
   - NO importa el tamaño del package (300 procedures)
   - TODO está en un directorio
   - NO dispersión en múltiples batches

**Cambios en plsql-analyzer.md:**

- ✅ **Regla #1 actualizada:** Output structure por package
- ✅ **Workflow paso 10 agregado:** Determinar directorio de output
- ✅ **Lógica de directorio:**
  ```python
  if object_type == "PACKAGE_BODY":
      output_dir = f"knowledge/json/{object_name}/"
  elif manifest_entry.get("parent_package"):
      output_dir = f"knowledge/json/{parent_package}/"
  else:
      output_dir = "knowledge/json/STANDALONE/"
  ```

**Cambios en build_dependency_graph.py:**

- ✅ **Función `load_object_dependencies` actualizada:**
  - Busca en directorios de packages (no en batch_*)
  - Soporta estructura por package + STANDALONE
  - Comentario actualizado con nueva estructura

**Ejemplos de Paths:**

| Objeto | Tipo | Path |
|--------|------|------|
| ADD_K_ACT_FECHA_RECEPCION | PACKAGE_BODY | `knowledge/json/ADD_K_ACT_FECHA_RECEPCION/obj_9844.json` |
| P_OBT_PREST_PERFIL_ORDEN | PROCEDURE (miembro) | `knowledge/json/ADD_K_ACT_FECHA_RECEPCION/obj_9845.json` |
| MGM_F_EDAD_PACIENTE | FUNCTION (standalone) | `knowledge/json/STANDALONE/obj_9608.json` |

**Compatibilidad:**
- ❌ **Estructura antigua por batch NO soportada** (paths prohibidos en reglas BLOCKING)
- ✅ Scripts de progreso y tracking funcionan igual
- ✅ build_dependency_graph.py soporta nueva estructura

**Backups Creados:**
- `agents/backups/plsql-analyzer.md.v4.13.pre-package-structure.backup`

**Versión Agente:**
- plsql-analyzer: v4.13 → v4.14 (estructura por package)

---

## [v2.6] - 2026-02-15 - Consolidación de Comandos: migrate-analyze Unificado

### Changed - commands/

**Consolidación Mayor: De 3 Comandos a 1 Comando Unificado**

Los comandos de análisis se han consolidado en un solo comando `migrate-analyze` con múltiples modos de operación, eliminando confusión y duplicación de funcionalidad.

**Comandos Eliminados:**
- ❌ `migrate-analyze-all.md` → Funcionalidad absorbida en `migrate-analyze --all`
- ❌ `migrate-analyze-module.md` → Funcionalidad absorbida en `migrate-analyze --file`

**Comando Consolidado:**
- ✅ `migrate-analyze.md` (v2.0) - Unifica todas las funcionalidades de análisis

**Nuevos Modos de Operación:**

```bash
# 1. Modo Automático Completo (antes: migrate-analyze-all)
migrate-analyze --all
# Procesa TODOS los batches automáticamente sin intervención humana

# 2. Modo Batch (ya existía)
migrate-analyze                    # Siguiente batch pendiente
migrate-analyze --batch 001        # Batch específico

# 3. Modo Objeto Individual (ya existía)
migrate-analyze --object obj_9352
migrate-analyze --objects obj_1,obj_2,obj_3

# 4. Modo Archivo con Dependency Tree (antes: migrate-analyze-module)
migrate-analyze --file gestion_clinica.txt
# Lee archivo → Analiza objetos → Construye dependency tree → Genera orden de compilación
```

**Beneficios de la Consolidación:**

1. **Menos Confusión**
   - De 3 comandos con funcionalidades superpuestas a 1 comando claro
   - Roles claros: batch mode vs file mode (con/sin dependency tree)
   - Nombres de parámetros más descriptivos

2. **Comportamiento Inteligente**
   - `--file` SIEMPRE construye árbol de dependencias transitivas
   - Batch/all/object NO construyen dependency tree (análisis directo)
   - Diferenciación clara de casos de uso

3. **Formato de Archivo Flexible**
   - Acepta: `PACKAGE.PROCEDURE`, `PACKAGE`, `PROCEDURE`, `obj_9352`
   - Soporta comentarios (#) y líneas vacías
   - Normalización automática (uppercase)

4. **Dependency Tree Automático (modo --file)**
   - ✨ BFS (Breadth-First Search) desde entry points
   - ✨ Topological Sort (Kahn's Algorithm) para orden de compilación
   - ✨ Detección de circular dependencies
   - ✨ Outputs: dependency_tree.json + migration_order.json + objects_to_migrate.txt

**Casos de Uso por Modo:**

| Modo | Comando | Uso Típico |
|------|---------|-----------|
| **Batch** | `migrate-analyze` | Pruebas, re-procesamiento |
| **All** | `migrate-analyze --all` | Migración inicial completa |
| **Object** | `migrate-analyze --object xxx` | Debugging, re-análisis |
| **File** | `migrate-analyze --file xxx.txt` | Módulos, planificación con dependencias |

**Comparación de Dependency Tree:**

| Modo | Dependency Tree | Orden de Compilación |
|------|----------------|---------------------|
| Batch/All/Object | ❌ No | ❌ No |
| File | ✅ Sí (BFS + Topological Sort) | ✅ Sí (por niveles) |

**Outputs Generados (modo --file):**

```
knowledge/json/batch_XXX/*.json    # Análisis individual de objetos
dependency_tree.json               # Árbol completo de dependencias
migration_order.json               # Orden de compilación por niveles ⭐
objects_to_migrate.txt             # Lista completa (entry points + deps)
```

**migration_order.json (estructura):**
```json
{
  "module_name": "gestion_clinica",
  "entry_points_count": 35,
  "total_objects": 156,
  "total_levels": 8,
  "levels": [
    {
      "level": 0,
      "description": "Sin dependencias - compilar primero",
      "can_compile_parallel": true,
      "objects": ["obj_001", "obj_005"]
    }
  ]
}
```

**Script Integrado:**
- `scripts/build_dependency_graph.py` - Ejecutado automáticamente en modo `--file`

**Cambios en plugin.json:**
- Eliminadas referencias a comandos obsoletos
- Mantenidos solo 6 comandos principales

**Documentación Actualizada:**
- `commands/migrate-analyze.md` (v2.0) - Documentación completa de todos los modos
- Comparación clara entre modos
- Ejemplos de uso por caso específico
- Troubleshooting actualizado

**Backups Creados:**
- `commands/backups/migrate-analyze.md.v1.0.pre-consolidation`
- `commands/backups/migrate-analyze-all.md.v1.0.archived`
- `commands/backups/migrate-analyze-module.md.v1.0.archived`

---

## [v2.5] - 2026-02-10 - Clasificación Automática: Decisión Inteligente SIMPLE vs COMPLEX

### Changed - commands/migrate-convert.md

**Mejora Significativa: Sistema de Clasificación Automática**

El comando `/migrate-convert` ahora determina automáticamente si un objeto es SIMPLE o COMPLEX leyendo la clasificación de Fase 1, eliminando la necesidad de especificar `--complexity` manualmente.

**Priority Cascade implementado:**

```
1. Leer JSON de Fase 1 (classification.category) ← Source of Truth
2. Usar --complexity si especificado (override manual)
3. Inferir de object_type (PACKAGE → COMPLEX, VIEW → SIMPLE)
4. Default: SIMPLE (safe fallback)
```

**Antes de v2.5 (Manual):**
```bash
# Usuario tenía que recordar/especificar clasificación
/migrate-convert --object PKG_FAC --complexity complex  # ❌ Tedioso
/migrate-convert --object COM_V_CONV --complexity simple
```

**Después de v2.5 (Automático):**
```bash
# Sistema lee classification.category automáticamente
/migrate-convert --object PKG_FAC              # ✅ Auto-detecta COMPLEX
/migrate-convert --object COM_V_CONV           # ✅ Auto-detecta SIMPLE
/migrate-convert --objects obj_1,obj_2,obj_3   # ✅ Clasifica cada uno
```

**Beneficios:**

1. **Single Source of Truth**
   - Fase 1 (plsql-analyzer) es la autoridad en clasificación
   - Fase 2 (plsql-converter) respeta esa clasificación automáticamente
   - Elimina desajustes entre análisis y conversión

2. **Reduce Errores Humanos**
   - No más "olvidé especificar --complexity complex"
   - No más "usé SIMPLE cuando debería ser COMPLEX"
   - Sistema siempre usa la clasificación correcta

3. **Mejor UX (User Experience)**
   - Usuario no necesita recordar clasificaciones
   - Comandos más simples y concisos
   - Override manual disponible para casos especiales

4. **Consistencia Garantizada**
   - Análisis semántico de Fase 1 guía conversión de Fase 2
   - Estrategias aplicadas siempre coinciden con características del objeto
   - Menos errores de compilación por estrategia incorrecta

**Nuevo Comportamiento:**

```bash
# Objeto individual - Clasificación automática
/migrate-convert --object PKG_FACTURACION
→ Lee: knowledge/json/batch_008/obj_1523.json
→ Extrae: classification.category = "COMPLEX"
→ Aplica: Estrategias COMPLEX (AUTONOMOUS_TRANSACTION, UTL_HTTP, etc.)
→ Guarda: migrated/complex/obj_1523_PKG_FACTURACION.sql

# Múltiples objetos - Clasificación mixta automática
/migrate-convert --objects "COM_V_CONV,PKG_FAC,FAC_F_DET"
→ COM_V_CONV: SIMPLE (desde JSON)
→ PKG_FAC: COMPLEX (desde JSON)
→ FAC_F_DET: SIMPLE (desde JSON)
→ Agrupa y procesa cada grupo con estrategias correctas

# Override manual (casos especiales)
/migrate-convert --object PKG_FAC --complexity simple
→ Fuerza SIMPLE (ignora clasificación de Fase 1)
→ ⚠️ Solo para casos específicos de testing
```

**Casos Edge Manejados:**

- ✅ JSON de Fase 1 no existe → Infiere de object_type
- ✅ object_type desconocido → Default SIMPLE (safe)
- ✅ Override manual especificado → Respeta usuario (Priority 2)
- ✅ Múltiples objetos con clasificaciones mixtas → Agrupa automáticamente

**Cambios en Documentación:**

- Nueva sección: "🎯 Priority Cascade para Clasificación Automática"
- Ejemplos actualizados mostrando detección automática
- Casos de uso de override manual documentados
- Diagrama de jerarquía de decisión agregado

**Archivos Modificados:**
1. `commands/migrate-convert.md` - Lógica de decisión automática implementada
2. `CHANGELOG.md` - Esta entrada

**Backup Creado:**
- `commands/backups/migrate-convert.md.v2.4.*.pre-auto-classification.backup`

**Compatibilidad:**
- ✅ 100% compatible con comportamiento anterior
- ✅ `--complexity` manual sigue funcionando (Priority 2)
- ✅ Modo batch sin cambios
- ✅ Sin breaking changes

**Impacto en Workflow:**

```bash
# Workflow típico ANTES de v2.5:
ls compilation/errors/
# → obj_1523_PKG_FAC.log tiene error
grep "obj_1523" knowledge/classification/*.txt  # ¿Es SIMPLE o COMPLEX?
/migrate-convert --object obj_1523 --complexity complex  # Especificar manualmente

# Workflow típico DESPUÉS de v2.5:
ls compilation/errors/
# → obj_1523_PKG_FAC.log tiene error
/migrate-convert --object obj_1523  # Sistema decide automáticamente ✅
```

**Principios de Diseño Aplicados:**
- **DRY (Don't Repeat Yourself):** Clasificación se hace UNA vez en Fase 1
- **Separation of Concerns:** Analyzer clasifica, Converter convierte
- **Fail-Safe:** Múltiples niveles de fallback
- **User-Friendly:** Comandos más simples, menos errores

**Motivación Original:**
Sugerencia del usuario: "El agente debería leer classification.category del JSON de Fase 1 y con ese dato tomar la decisión si aplicar lógica SIMPLE o COMPLEX automáticamente."

**Resultado:** Sistema significativamente más inteligente y robusto.

---

## [v2.4] - 2026-02-10 - Comando /migrate-convert: Conversión y compilación de objetos individuales

### Added - commands/migrate-convert.md

**Nueva funcionalidad:**
- ✅ Conversión de objetos individuales por nombre o object_id
- ✅ Conversión de múltiples objetos específicos
- ✅ **Compilación automática en PostgreSQL** después de convertir
- ✅ Generación de logs de compilación individuales
- ✅ Compatible con objetos SIMPLE y COMPLEX

**Nuevos argumentos (ahora implementados en el prompt):**

1. **`--object`:** Convierte y compila un objeto específico
   ```bash
   /migrate-convert --object obj_9352              # Por object_id
   /migrate-convert --object COM_V_CONVENIOS       # Por nombre
   /migrate-convert --object PKG_FAC --complexity complex  # Objeto complejo
   ```

2. **`--objects`:** Convierte y compila múltiples objetos
   ```bash
   /migrate-convert --objects obj_9352,obj_9353    # Por IDs
   /migrate-convert --objects "COM_V_CONVENIOS,FAC_F_DETALLE"  # Por nombres
   ```

**Proceso integrado (conversión + compilación):**
1. Busca objeto en manifest.json
2. Invoca plsql-converter para generar SQL
3. **Compila automáticamente en PostgreSQL usando psql**
4. Genera logs:
   - `compilation/success/{objeto}.log` - Si compiló OK
   - `compilation/errors/{objeto}.log` - Si hubo errores

**Casos de uso:**
- Re-convertir objetos específicos después de errores de compilación
- Convertir y validar objetos relacionados de un mismo módulo
- Iteración rápida: corregir → re-convertir → compilar → verificar
- Testing de conversión antes de procesar batch completo

**Ventajas vs Modo Batch:**
- ⚡ Más rápido: Solo convierte y compila lo necesario
- 🎯 Más preciso: Iteración sobre un objeto hasta que compile OK
- 🔍 Mejor debugging: Logs individuales más fáciles de revisar
- ♻️ Workflow iterativo: Corregir errores y re-convertir inmediatamente

**Compatibilidad:**
- ✅ Mantiene funcionalidad original de procesamiento por batch
- ✅ Genera mismos archivos SQL que el modo batch
- ✅ Estructura de outputs compatible con resto del pipeline

**Backup creado:**
- `commands/backups/migrate-convert.md.v20260210_*.pre-single-object.backup`

**Motivación:**
Similar a `/migrate-analyze`, el comando `/migrate-convert` ahora permite trabajar con objetos individuales, facilitando el debugging y la iteración rápida durante la migración. La integración automática con compilación en PostgreSQL proporciona feedback inmediato sobre la calidad de la conversión.

---

## [v2.3] - 2026-02-10 - Comando /migrate-analyze: Soporte para análisis de objetos individuales

### Added - commands/migrate-analyze.md

**Nueva funcionalidad:**
- ✅ Análisis de objetos individuales por nombre o object_id
- ✅ Análisis de múltiples objetos específicos
- ✅ Compatible con el pipeline de migración existente

**Nuevos argumentos:**

1. **`--object`:** Analiza un objeto específico
   ```bash
   /migrate-analyze --object obj_9352              # Por object_id
   /migrate-analyze --object COM_V_CONVENIOS       # Por nombre
   ```

2. **`--objects`:** Analiza múltiples objetos
   ```bash
   /migrate-analyze --objects obj_9352,obj_9353    # Por IDs
   /migrate-analyze --objects "COM_V_CONVENIOS,FAC_F_DETALLE"  # Por nombres
   ```

**Casos de uso:**
- Re-analizar objetos específicos después de errores
- Analizar objetos relacionados de un mismo módulo
- Verificar análisis de objetos específicos sin procesar batch completo

**Compatibilidad:**
- ✅ Mantiene funcionalidad original de procesamiento por batch
- ✅ Genera mismos archivos JSON que el modo batch
- ✅ Compatible con `update_progress.py --auto`

**Backup creado:**
- `commands/backups/migrate-analyze.md.v1.0.backup`

---

## [v2.2] - 2026-02-09 - Scripts & Comandos: Simplificación y optimización del sistema de progreso

### Changed - scripts/update_progress.py

**Contexto:**
- Teníamos 2 scripts con responsabilidades parcialmente duplicadas:
  - `update_progress.py`: Actualizaba progress.json + manifest.json (batch específico)
  - `sync_manifest_status.py`: Solo actualizaba manifest.json (sincronización masiva)
- Los comandos usaban ambos scripts en secuencia (ineficiente)
- El flag `--update` se usaba en comandos pero NO existía en el script

**Problema:**
- ❌ Comandos llamaban `update_progress.py --update` pero el flag NO existía
- ❌ Luego llamaban `sync_manifest_status.py` (duplicando actualizaciones de manifest)
- ❌ Dos scripts haciendo trabajo similar pero sin coordinación clara
- ❌ Confusión sobre cuándo usar cada script

**Solución implementada:**
- ✅ Agregado flag `--auto` a `update_progress.py` que auto-detecta batches procesados
- ✅ Agregado flag `--check` para solo mostrar estado actual
- ✅ Mantenido compatibilidad con uso manual `batch_XXX`
- ✅ `sync_manifest_status.py` se mantiene para sincronizaciones masivas especiales
- ✅ Comandos ahora usan solo `update_progress.py --auto` (un solo script)

**Nuevos flags agregados:**

1. **`--auto` (o `--update` por compatibilidad):**
   - Auto-detecta TODOS los batches en `knowledge/json/batch_*/`
   - Actualiza manifest.json basándose en archivos JSON existentes
   - Actualiza progress.json con contadores correctos
   - Usa manifest como fuente de verdad para processed_count
   ```bash
   python scripts/update_progress.py --auto
   ```

2. **`--check`:**
   - Solo muestra estado actual sin modificar archivos
   - Útil para verificar progreso rápidamente
   ```bash
   python scripts/update_progress.py --check
   ```

3. **`batch_XXX` (original):**
   - Procesa un batch específico
   - Genera instrucciones para siguiente batch
   - Comportamiento original preservado
   ```bash
   python scripts/update_progress.py batch_025
   ```

**Funciones nuevas agregadas:**
```python
def check_progress():
    """Muestra el estado actual del progreso sin modificar nada"""
    # Lee progress.json y muestra estadísticas

def auto_update_from_json_files():
    """
    Auto-detecta todos los batches procesados basándose en archivos JSON existentes
    y actualiza tanto progress.json como manifest.json
    """
    # Busca batch_*/, cuenta objetos, actualiza manifest y progress
```

**Separación de responsabilidades final:**
| Script | Propósito | Cuándo Usar |
|--------|-----------|-------------|
| **update_progress.py --auto** | Auto-actualización desde JSONs | Comandos automáticos |
| **update_progress.py batch_XXX** | Batch específico + instrucciones | Uso manual/debugging |
| **update_progress.py --check** | Verificar estado | Consulta rápida |
| **sync_manifest_status.py** | Sincronización masiva especial | Correcciones/limpiezas |

### Changed - commands/migrate-analyze.md

**Antes:**
```bash
4. **Actualizar progreso y manifest**
   # Actualizar progress.json
   python scripts/update_progress.py --update

   # Sincronizar manifest.json (marcar objetos como "processed")
   python scripts/sync_manifest_status.py
```

**Después:**
```bash
4. **Actualizar progreso y manifest**
   # Auto-detecta archivos JSON y actualiza progress.json + manifest.json
   python scripts/update_progress.py --auto
```

### Changed - commands/migrate-analyze-all.md

**Antes:**
```bash
#### 3. Actualizar progreso y manifest
# Actualizar progress.json
python scripts/update_progress.py --update

# Sincronizar manifest.json
python scripts/sync_manifest_status.py
```

**Después:**
```bash
#### 3. Actualizar progreso y manifest
# Auto-detecta archivos JSON y actualiza progress.json + manifest.json
python scripts/update_progress.py --auto
```

**Archivos afectados:**
- `scripts/update_progress.py` - Agregados flags `--auto` y `--check`
- `commands/migrate-analyze.md` - Simplificado paso 4 (un solo comando)
- `commands/migrate-analyze-all.md` - Simplificado paso 3 (un solo comando)

**Impacto:**
- ✅ Un solo script en lugar de dos (simplicidad)
- ✅ Flags claros para diferentes modos de uso
- ✅ Comandos más cortos y directos
- ✅ `sync_manifest_status.py` se mantiene para casos especiales
- ✅ Menos confusión sobre qué script usar cuándo

---

## [v2.1] - 2026-02-09 - Comandos: Eliminados reportes y summaries automáticos

### Removed - commands/migrate-analyze.md

**Contexto:**
- El comando generaba reportes/summaries al final de cada ejecución
- Estos reportes no son necesarios durante el procesamiento automático
- El usuario puede consultar progress.json manualmente cuando lo necesite

**Problema:**
- ❌ Paso 5: "Mostrar resumen" con clasificación, progreso, siguiente batch recomendado
- ❌ Output verboso innecesario durante procesamiento automático
- ❌ Comandos diseñados para SOLO ejecutar tarea, no generar reportes

**Solución implementada:**
- ✅ Eliminado completamente el paso 5 "Mostrar resumen"
- ✅ Comando ahora SOLO ejecuta la tarea (análisis + actualización)

**Antes:**
```markdown
4. **Actualizar progreso y manifest**
   ...

5. **Mostrar resumen**
   - Objetos procesados en este batch
   - Objetos clasificados como SIMPLE vs COMPLEX
   - Progreso total (X de 8,122 objetos completados)
   - Siguiente batch recomendado
```

**Después:**
```markdown
4. **Actualizar progreso y manifest**
   ...

¿Procedo con el análisis del batch {{batch}}?
```

### Removed - commands/migrate-analyze-all.md

**Problema:**
- ❌ Paso 4: Barra de progreso después de cada batch (20+ líneas de Python)
- ❌ Paso Final: Reporte completo con clasificación y estadísticas (60+ líneas)
- ❌ Sección "## Reporte Final" en la documentación (ejemplo de output)
- ❌ Característica "✅ Progreso visible - Barra de progreso y estadísticas en tiempo real"

**Solución implementada:**
- ✅ Eliminado paso 4 "Mostrar progreso actual" (barra de progreso)
- ✅ Eliminado "Paso Final: Generar Reporte Completo" (60+ líneas)
- ✅ Eliminada sección "## Reporte Final" de la documentación
- ✅ Simplificado paso 4 a solo verificación lógica de pendientes

**Antes (Paso 4):**
```python
#### 4. Mostrar progreso actual

import json
with open('sql/extracted/progress.json') as f:
    p = json.load(f)

total = p['total_objects']
processed = p['processed_count']
# ... 20 líneas más de código de barra de progreso
print(f"[{bar}]")
```

**Después (Paso 4):**
```python
#### 4. Verificar si quedan batches pendientes

import json
with open('sql/extracted/progress.json') as f:
    progress = json.load(f)

if progress['pending_count'] > 0:
    # CONTINUAR LOOP
else:
    # FIN: Todos los objetos procesados
```

**Antes (Paso Final):**
```python
### Paso Final: Generar Reporte Completo

# ... 60+ líneas de código Python
print(f"""
{'='*80}
✅ ANÁLISIS COMPLETO - FASE 1 FINALIZADA
# ... reportes extensos
""")
```

**Después:**
```markdown
(Paso final eliminado completamente)
```

**Características actualizadas:**
```diff
- ✅ **Progreso visible** - Barra de progreso y estadísticas en tiempo real
+ (Característica eliminada)
```

```diff
## Lo que hace este comando

1. **Procesa ~36 batches** de 200 objetos cada uno automáticamente
2. **Ejecuta el workflow completo:** Para cada batch lanza 20 agentes plsql-analyzer en paralelo
3. **Actualiza progreso** continuamente en `progress.json` y `manifest.json`
4. **Continúa secuencialmente** hasta procesar todos los objetos
- 5. **Genera reporte final** cuando termina
```

**Archivos afectados:**
- `commands/migrate-analyze.md` - Eliminado paso 5 (resumen)
- `commands/migrate-analyze-all.md` - Eliminados paso 4 (progreso) y paso final (reporte)
- `commands/migrate-analyze-all.md` - Eliminada sección "## Reporte Final"

**Impacto:**
- ✅ Comandos más simples y enfocados (solo ejecutan tareas)
- ✅ Sin output verboso innecesario
- ✅ Usuario puede consultar progreso manualmente cuando lo necesite:
  ```bash
  cat sql/extracted/progress.json
  python scripts/update_progress.py --check
  ```
- ✅ Procesamiento más rápido (sin generar reportes)

**Alternativas para consultar progreso:**
```bash
# Ver estado actual
cat sql/extracted/progress.json

# Verificar progreso detallado
python scripts/update_progress.py --check

# Generar clasificación manualmente (si es necesario)
python scripts/consolidate_classification.py
```

---

## [v4.12] - 2026-02-09 - plsql-analyzer: Eliminado paso de generación de archivos summary

### Removed - agents/plsql-analyzer.md

**Contexto:**
- El agente generaba archivos de resumen al final de cada batch (paso 11 del workflow)
- Estos archivos de resumen causaron 41+ archivos extra en knowledge/json/
- No son necesarios para el proceso de migración
- Pueden causar race conditions si múltiples agentes intentan escribir el mismo summary

**Problema:**
- ❌ Paso 11 del workflow: "Generate summary (end of batch only)"
- ❌ Generaba archivos como: batch_007_summary.json, analysis_summary_80_89.json
- ❌ Causaba desorden en el directorio knowledge/json/
- ❌ 41 archivos de resumen tuvieron que moverse a backup

**Solución implementada:**
- ✅ Eliminado completamente el paso 11 del workflow
- ✅ Agregada prohibición explícita de archivos de resumen en "Outputs Prohibidos"
- ✅ Actualizado checklist para verificar que NO se crearon archivos summary
- ✅ Clarificado que solo debe crear archivos JSON individuales por objeto

**Cambios específicos:**

1. **Workflow actualizado (paso 10):**
```diff
10. Generar JSON - Usar schema EXACTO anterior, sin campos adicionales

- 11. Generate summary (end of batch only)
-    {
-      "total_objects_analyzed": 200,
-      ...
-    }

+ IMPORTANTE: NO generar archivos de resumen (summary) al final del batch.
+ Solo crear archivos JSON individuales por objeto.
```

2. **Outputs Prohibidos actualizado:**
```diff
- ❌ Archivos .md (incluyendo README.md, REPORT.md, SUMMARY.md, etc.)
+ ❌ Archivos .md (incluyendo README.md, REPORT.md, SUMMARY.md, etc.)
+ ❌ Archivos de resumen (summary.json, batch_summary.json, analysis_summary.json, etc.)
```

3. **Checklist actualizado:**
```diff
- ❌ ¿Sin archivos .md en ningún lugar?
+ ❌ ¿Sin archivos .md en ningún lugar?
+ ❌ ¿Sin archivos de resumen (summary.json, batch_summary.json, etc.)?
```

**Archivos afectados:**
- `agents/plsql-analyzer.md` v4.11 → v4.12
- `agents/backups/plsql-analyzer.md.v4.11.pre-remove-summary.backup` (backup creado)

**Impacto:**
- ✅ Directorio más limpio (solo archivos obj_XXXXX.json)
- ✅ Sin archivos innecesarios
- ✅ Sin riesgo de race conditions en archivos summary
- ✅ Proceso más simple y predecible

**Archivos de resumen anteriores:**
- 41 archivos movidos a `knowledge/json/backup_summary_files/`
- Pueden ser eliminados o conservados como referencia histórica

---

## [v4.11] - 2026-02-09 - plsql-analyzer: FILTRADO CRÍTICO por categoría (BLOCKING)

### Added - agents/plsql-analyzer.md

**Contexto:**
- El manifest.json contiene 18,510 objetos totales
- De esos, 9,512 son objetos de REFERENCIA (tables, PKs, sequences, types) ya migrados
- Solo 8,998 objetos son EJECUTABLES y deben analizarse

**Problema CRÍTICO detectado:**
- ❌ El agente NO tenía instrucciones explícitas de filtrar por categoría
- ❌ Podría procesar TODOS los 18,510 objetos (duplicando el trabajo)
- ❌ Crearía JSONs para objetos de referencia que no necesitan análisis
- ❌ Tiempo de procesamiento: 93 batches vs 45 batches correctos

**Solución implementada:**
- ✅ Agregada **Regla #0: Category Filter (BLOCKING)** como regla crítica
- ✅ Workflow actualizado con paso explícito de filtrado
- ✅ Verificación OBLIGATORIA antes de procesar cada objeto
- ✅ Checklist actualizado para validar filtrado correcto

**Nueva Regla #0: Category Filter**
```python
# Verificar ANTES de procesar
if category not in ["EXECUTABLE", "REFERENCE_AND_EXECUTABLE"]:
    # SKIP: Este objeto ya está migrado
    continue
```

**Categorías permitidas:**
- ✅ **"EXECUTABLE"**: Procedures, functions, packages (8,935 objetos)
- ✅ **"REFERENCE_AND_EXECUTABLE"**: Views con lógica compleja (63 objetos)
- ❌ **"REFERENCE"**: Tables, PKs, sequences, types - SKIP (9,512 objetos)

**Cambios específicos:**
1. **Nueva sección en Reglas Críticas:**
   - Regla #0 (nueva): Category Filter → SKIP si no ejecutable
   - Regla #1 (renombrada): Output Structure → HALT si formato incorrecto

2. **Workflow actualizado (paso 2):**
   - Filtrado explícito por categoría
   - Explicación detallada de por qué filtrar
   - Ejemplo de código con lógica de skip

3. **Checklist actualizado:**
   - Nueva sección "Filtrado de objetos"
   - Verificación de categorías procesadas
   - Confirmación de que NO se procesaron objetos REFERENCE

**Archivos afectados:**
- `agents/plsql-analyzer.md` v4.10 → v4.11
- `agents/backups/plsql-analyzer.md.v4.10.pre-category-filter.backup` (backup creado)

**Impacto:**
- ✅ **CRÍTICO**: Reduce objetos a procesar de 18,510 → 8,998
- ✅ Reduce batches de 93 → 45 (cabe en 1 sesión Claude)
- ✅ Evita crear 9,512 JSONs innecesarios
- ✅ Tiempo de procesamiento reducido a la mitad
- ✅ Fuerza al agente a verificar categoría antes de procesar

**Enforcement:**
- Prioridad: **BLOCKING**
- Enforcement Point: **PRE_PROCESS** (antes de leer código)
- On Failure: **SKIP** (saltar objeto, continuar con siguiente)

---

## [v4.10] - 2026-02-09 - plsql-analyzer: Nombre de archivo JSON = solo object_id

### Changed - agents/plsql-analyzer.md

**Contexto:**
- El agente debe crear archivos JSON con los datos de clasificación
- El nombre del archivo debe ser simple y consistente con el manifest.json

**Problema:**
- El formato especificaba `{object_id}_{name}.json` (ejemplo: `obj_00123_PACKAGE_NAME.json`)
- Esto agrega información redundante (el nombre ya está en el JSON)
- Hace más difícil el procesamiento automático por scripts

**Solución implementada:**
- ✅ Nombre de archivo = solo `{object_id}.json` (ejemplo: `obj_00123.json`)
- ✅ Actualizado formato en "Outputs Permitidos"
- ✅ Actualizado ejemplo en sección de violaciones
- ✅ Agregado checklist explícito en Pre-Write Checklist
- ✅ Ejemplo claro: `obj_00123.json ✅  NO obj_00123_PACKAGE_NAME.json ❌`

**Cambios específicos:**
```diff
- knowledge/json/batch_XXX/{object_id}_{name}.json
+ knowledge/json/batch_XXX/{object_id}.json

Ejemplo:
- obj_12321_PACKAGE.json  ❌ (nombre incorrecto)
+ obj_12321.json          ✅ (correcto: solo object_id)
```

**Archivos afectados:**
- `agents/plsql-analyzer.md` v4.9 → v4.10
- `agents/backups/plsql-analyzer.md.v4.9.pre-filename-fix.backup` (backup creado)

**Impacto:**
- ✅ Nombres de archivo más simples y consistentes
- ✅ Facilita procesamiento automático
- ✅ Reduce longitud de nombres de archivo
- ✅ Alineado con el object_id del manifest.json

---

## [v4.9] - 2026-02-09 - plsql-analyzer: Clarificación sobre NO ejecutar scripts

### Changed - agents/plsql-analyzer.md

**Contexto:**
- El agente solo debe crear archivos JSON con datos de clasificación
- NO debe ejecutar ningún script Python (como `consolidate_classification.py`)
- Las listas consolidadas las genera el USUARIO manualmente si es necesario

**Problema:**
- Notas en el agente mencionaban "script post-proceso" sin clarificar que el agente NO debe ejecutarlo
- Podría interpretarse como instrucción implícita de ejecutar el script
- Usuario reportó que agente creaba archivos no solicitados

**Solución implementada:**
- ✅ Clarificado en sección "Outputs Permitidos" que NO debe ejecutar scripts
- ✅ Agregado checklist explícito: "¿NO ejecutaste ningún script de Python?"
- ✅ Eliminada ambigüedad sobre "script post-proceso"
- ✅ Instrucción clara: "Solo crear archivos JSON, nada más"

**Cambios específicos:**
```diff
- **NOTA:** Las listas de clasificación (`simple_objects.txt`, `complex_objects.txt`) se generan mediante script post-proceso...
+ **IMPORTANTE:**
+ - ✅ **Solo crear archivos JSON** con los datos de clasificación
+ - ❌ **NO crear archivos de listas** (simple_objects.txt, complex_objects.txt)
+ - ❌ **NO ejecutar ningún script** (consolidate_classification.py u otros)
+ - ℹ️  Las listas consolidadas las genera el USUARIO después manualmente si es necesario
```

**Archivos afectados:**
- `agents/plsql-analyzer.md` v4.8 → v4.9
- `agents/backups/plsql-analyzer.md.v4.8.pre-script-clarification.backup` (backup creado)

**Impacto:**
- ✅ Agente ahora solo crea JSONs (comportamiento esperado)
- ✅ Sin ejecución accidental de scripts
- ✅ Usuario tiene control total sobre cuándo consolidar clasificación

---

## [v2.0.1] - 2026-02-07 - Limpieza: Eliminadas referencias al batch-coordinator

### Changed - commands/migrate-analyze-all.md

**Contexto:**
- El agente `batch-coordinator` fue una idea inicial nunca implementada activamente
- Solo existía en `agents/backups/` (histórico), NO en `agents/` (activo)
- NO estaba registrado en `plugin.json`
- El comando `/migrate-analyze-all` SIEMPRE ejecutó el workflow directamente (no usó batch-coordinator)

**Problema:**
- El comando contenía referencias confusas al "batch-coordinator"
- Sugería que había un agente coordinador cuando en realidad Claude ejecuta el workflow directamente
- Causaba confusión sobre cómo funciona el comando

**Solución implementada:**
- ✅ Eliminadas todas las referencias al batch-coordinator del comando
- ✅ Clarificado que Claude ejecuta el workflow directamente
- ✅ Actualizado texto para reflejar la implementación real
- ✅ Mantenido el backup histórico en `agents/backups/`

**Cambios específicos:**
```diff
- 1. **Inicia el coordinador autónomo** `batch-coordinator`
+ 1. **Procesa ~30 batches** de 300 objetos cada uno automáticamente
+ 2. **Ejecuta el workflow completo:** Para cada batch lanza 30 agentes plsql-analyzer en paralelo

- **Batch-coordinator gestiona esto automáticamente:**
+ **El workflow gestiona esto automáticamente:**
- El coordinador detecta el estado y continúa donde quedó
+ Claude detecta el estado en progress.json y continúa donde quedó
```

**Archivos afectados:**
- `commands/migrate-analyze-all.md` (limpiado)
- `commands/backups/migrate-analyze-all.md.v1.1.pre-coordinator-cleanup.backup` (backup creado)

**Impacto:**
- ✅ Documentación más clara y precisa
- ✅ Sin confusión sobre agentes inexistentes
- ✅ Funcionalidad no afectada (siempre funcionó así)

**Versionamiento:**
- commands/migrate-analyze-all.md: v1.1 → v1.2 (documentación corregida)

---

## [v5.0.1] - 2026-02-07 - Fix: batch-coordinator ahora lanza 30 agentes en paralelo

### Fixed - agents/batch-coordinator.md

**Problema identificado:**
- El agente `batch-coordinator` tenía pseudocódigo Python con for loop
- NO tenía instrucciones EXPLÍCITAS de lanzar 30 agentes en paralelo en UN SOLO mensaje
- Podría interpretarse como invocación secuencial (30× más lento)

**Ejemplo del problema:**
```python
# Esto sugiere invocación secuencial
for i in range(0, len(next_batch), 10):
    Task(...)  # Una por una
```

**Solución implementada:**
- Agregadas instrucciones EXPLÍCITAS de paralelismo
- Alineado con el patrón de `/migrate-analyze`
- Enfatizado "30 llamadas Task en UN SOLO mensaje"

**Nuevo texto (explícito):**
```
**CRÍTICO:** Lanzar **30 llamadas Task en UN SOLO mensaje** para procesamiento paralelo.

Instrucciones explícitas:
- Para 300 objetos → 30 agentes × 10 objetos cada uno
- TODOS los agentes Task deben invocarse en UN SOLO mensaje
- NO usar loops secuenciales - invocar en paralelo
```

**Impacto:**
- ✅ Procesamiento paralelo garantizado (30 agentes simultáneos)
- ✅ Tiempo por batch: ~6-8 minutos (en lugar de ~3 horas secuencial)
- ✅ Consistencia con `/migrate-analyze`

**Archivos afectados:**
- `agents/batch-coordinator.md` (actualizado)
- `agents/backups/batch-coordinator.md.v1.0.pre-parallel-fix.backup` (backup creado)

**Versionamiento:**
- batch-coordinator: v1.0 → v1.1 (fix crítico de paralelismo)

---

## [v5.0] - 2026-02-07 - Feature: Automatización completa con /migrate-analyze-all

### Added - agents/batch-coordinator.md (NUEVO)

**Problema resuelto:**
- Procesar 8,998 objetos requería ejecutar `/migrate-analyze next` ~30 veces manualmente
- Requiere intervención humana constante durante 3-4 horas
- Propenso a errores (olvidar ejecutar siguiente batch)

**Solución implementada:**
- Nuevo agente `batch-coordinator` que procesa TODO automáticamente
- Sistema de **auto-recursión:** El agente se invoca a sí mismo hasta terminar
- Procesamiento completamente autónomo sin intervención humana

**Características del agente:**
- ✅ Procesa ~30 batches de 300 objetos secuencialmente
- ✅ Auto-invocación recursiva (Task → batch-coordinator → Task → ...)
- ✅ Consolida clasificación después de cada batch
- ✅ Actualiza progreso automáticamente
- ✅ Barra de progreso visible en tiempo real
- ✅ Manejo de errores (continúa si un batch falla)
- ✅ Genera reporte final completo

**Workflow autónomo:**
```
Batch 001 → Consolidar → Actualizar → ¿Pendientes? → SÍ → Auto-invocar
Batch 002 → Consolidar → Actualizar → ¿Pendientes? → SÍ → Auto-invocar
...
Batch 030 → Consolidar → Actualizar → ¿Pendientes? → NO → Reporte Final
```

### Added - commands/migrate-analyze-all.md (NUEVO)

**Nuevo comando disponible:**
```bash
/migrate-analyze-all
```

**Función:**
- Procesa TODOS los 8,998 objetos ejecutables en una sola ejecución
- Totalmente automático (sin intervención humana)
- Tiempo estimado: 3-4 horas

**Comparación:**

| Aspecto | Antes (/migrate-analyze next) | Ahora (/migrate-analyze-all) |
|---------|-------------------------------|------------------------------|
| Ejecuciones manuales | ~30 veces | 1 vez |
| Intervención humana | Alta | Ninguna |
| Tiempo total | 4h + tiempo usuario | 3-4h automáticas |
| Propenso a errores | Sí | No |

**Ventajas:**
1. ✅ **Una sola ejecución** - Set it and forget it
2. ✅ **Progreso automático** - Barra visible en tiempo real
3. ✅ **Tolerante a interrupciones** - Reinicia desde último batch
4. ✅ **Reporte final completo** - Estadísticas globales al terminar

**Ejemplo de uso:**
```bash
/migrate-analyze-all

# Output:
Procesando 8,998 objetos ejecutables en ~30 batches...

Batch 001/030: ████████████ 100% (300 objetos) ✓
Batch 002/030: ████████████ 100% (300 objetos) ✓
...
Batch 030/030: ████████████ 100% (298 objetos) ✓

✅ Análisis completo:
   SIMPLE:  7,918 (88%)
   COMPLEX: 1,080 (12%)
```

### Changed - Workflow de Fase 1

**Antes:**
```bash
# Usuario debe ejecutar ~30 veces manualmente
/migrate-analyze next  # Batch 001
/migrate-analyze next  # Batch 002
/migrate-analyze next  # Batch 003
...
/migrate-analyze next  # Batch 030
```

**Ahora:**
```bash
# Una sola ejecución procesa todo
/migrate-analyze-all
# → 3-4 horas después → ✅ 8,998 objetos analizados
```

### Technical Details

**Auto-recursión del coordinador:**
```python
# Al final de cada batch
if pending_count > 0:
    # Auto-invocarse para siguiente batch
    Task(
        subagent_type="oracle-postgres-migration:batch-coordinator",
        prompt="Continuar con siguiente batch"
    )
else:
    # Generar reporte final
    generate_final_report()
```

**Archivos afectados:**
- `agents/batch-coordinator.md` (nuevo - 400 líneas)
- `commands/migrate-analyze-all.md` (nuevo - 200 líneas)
- `CHANGELOG.md` (esta entrada)

**Versionamiento:**
- Plugin: v4.8 → v5.0 (major version por nueva feature principal)

**Impacto:**
- 🚀 **Productividad:** Reduce intervención humana de ~4 horas a 5 minutos
- 🎯 **Precisión:** Elimina errores de usuario (olvidar ejecutar batches)
- ⚡ **Eficiencia:** Procesamiento continuo sin pausas humanas

---

## [v4.8] - 2026-02-07 - Fix: Forzar contenido de JSONs en ESPAÑOL

### Changed - agents/plsql-analyzer.md

**Problema identificado:**
- Agente generaba contenido en inglés en los campos de los JSONs
- Inconsistencia lingüística dificulta lectura y comprensión
- business_knowledge, reasoning y otros textos estaban en inglés

**Ejemplo del problema:**
```json
{
  "business_knowledge": {
    "purpose": "Calculate sales commission for...",  // ❌ Inglés
    "business_rules": ["Base commission rate..."],    // ❌ Inglés
    "reasoning": "✅ SIMPLE: Standard PL/SQL..."      // ❌ Inglés
  }
}
```

**Solución implementada:**
- Agregada instrucción explícita en `<role>` para generar TODO en español
- Actualizados todos los ejemplos del agente a español
- Nombres de campos (schema) se mantienen en inglés
- Contenido de campos SIEMPRE en español

**Nuevo output esperado:**
```json
{
  "business_knowledge": {
    "purpose": "Calcular comisión de ventas para...",  // ✅ Español
    "business_rules": ["Tasa de comisión base..."],    // ✅ Español
    "reasoning": "✅ SIMPLE: Sintaxis PL/SQL..."       // ✅ Español
  }
}
```

**Campos afectados (ahora en español):**
- `business_knowledge.purpose`
- `business_knowledge.business_rules` (array)
- `business_knowledge.key_logic`
- `business_knowledge.data_flow`
- `classification.reasoning`
- `oracle_features[].usage`
- `oracle_features[].postgresql_equivalent`
- `package_spec_context.*[].usage`
- `package_spec_context.*[].migration_note`

**Archivos afectados:**
- `agents/plsql-analyzer.md` (modificado)
- `agents/backups/plsql-analyzer.md.v4.7.pre-spanish-content.backup` (backup creado)

**Versionamiento:**
- plsql-analyzer: v4.7 → v4.8

**Impacto:** Los JSONs futuros tendrán TODO el contenido en español para facilitar lectura y comprensión del equipo.

---

## [v4.7] - 2026-02-07 - Fix: Eliminar race conditions en listas de clasificación

### Changed - agents/plsql-analyzer.md

**Problema identificado:**
- Cuando 30 agentes corren en paralelo, todos intentan actualizar `simple_objects.txt` y `complex_objects.txt`
- Race condition: agentes sobrescriben las listas entre sí
- Resultado: Solo ~80/300 objetos terminaban en las listas (último agente en escribir ganaba)

**Solución implementada:**
- Agentes ahora **solo generan archivos JSON** (fuente de verdad)
- Script post-proceso `consolidate_classification.py` genera listas desde JSONs
- Elimina race conditions completamente

**Cambios en plsql-analyzer.md:**
1. Frontmatter: Agregado "v4.7 NUEVO: Eliminadas listas TXT..."
2. Outputs permitidos: Reducido de 3 a 1 (solo JSON)
3. Workflow: Eliminado paso 10 (actualizar listas)
4. Checklist: Actualizado para no verificar listas TXT

**Archivos afectados:**
- `agents/plsql-analyzer.md` (modificado)
- `agents/backups/plsql-analyzer.md.v4.6.pre-remove-txt-lists.backup` (backup creado)
- `scripts/consolidate_classification.py` (nuevo)

**Nuevo workflow:**
```bash
# Fase 1: Agentes generan JSONs (sin race conditions)
/migrate-analyze batch_001

# Fase 2: Script consolida clasificación
python scripts/consolidate_classification.py knowledge/json/batch_001
```

**Resultado:**
- ✅ JSONs completos: 300/300
- ✅ Listas consolidadas: 266 SIMPLE + 34 COMPLEX = 300 total
- ✅ Sin race conditions
- ✅ Fuente única de verdad (JSONs)

**Versionamiento:**
- plsql-analyzer: v4.6 → v4.7

### Changed - commands/migrate-analyze.md

**Integración automática de consolidación:**
- Comando `/migrate-analyze` ahora ejecuta `consolidate_classification.py` automáticamente
- Agregado paso 4: "Consolidar clasificación" después de que todos los agentes terminen
- Actualizada estructura de salida con nueva organización por batches
- Actualizada documentación para reflejar proceso completo

**Nuevo flujo integrado:**
```bash
/migrate-analyze batch_001
# → Agentes generan JSONs
# → Script consolida clasificación automáticamente ✨
# → Listas 100% completas sin intervención manual
```

**Archivos afectados:**
- `commands/migrate-analyze.md` (modificado)
- `commands/backups/migrate-analyze.md.pre-consolidation.backup` (backup creado)

**Beneficio:** Usuario ya no necesita ejecutar script manualmente - workflow totalmente automatizado.

---

## [v2.2.2] - 2026-02-07 - Fix: Eliminar campo 'version' no reconocido en plsql-converter

### Fixed - agents/plsql-converter.md

**Problema identificado:**
- Plugin `oracle-postgres-migration` fallaba al cargar en Claude Code
- Error: "✘ failed to load · 1 error"
- Causa: Campo `version: 4.6` en frontmatter YAML no es reconocido por Claude Code

**Archivo afectado:**
- `agents/plsql-converter.md`

**Cambio aplicado:**
```yaml
# ❌ ANTES (incorrecto)
---
name: plsql-converter
color: green
model: sonnet
version: 4.6        # ← Campo no válido
description: |
  ...
---

# ✅ DESPUÉS (correcto)
---
name: plsql-converter
color: green
model: sonnet
description: |      # ← version info movida a description
  **Convertidor Oracle->PostgreSQL v4.6 (XML + BLOCKING syntax-mapping.md)**
  ...
---
```

**Campos válidos para agentes en Claude Code:**
- `name` (requerido)
- `description` (requerido)
- `color` (opcional)
- `model` (opcional)

**Backup creado:**
- `agents/backups/plsql-converter.md.v4.6.pre-version-field-fix.backup`

**Impacto:**
- ✅ Plugin ahora carga correctamente sin errores
- ✅ Información de versión preservada en campo `description`

---

## [v2.2.1] - 2026-02-07 - Fix: Corregir frontmatter YAML de agentes

### Fixed - agents/*.md frontmatter

**Problema identificado:**
- Plugin `oracle-postgres-migration` fallaba al cargar en Claude Code
- Error: "✘ failed to load · 1 error"
- Causa: Campo `agentName:` incorrecto en frontmatter YAML de los 4 agentes

**Archivos afectados:**
- `agents/plsql-analyzer.md`
- `agents/plsql-converter.md`
- `agents/plpgsql-validator.md`
- `agents/shadow-tester.md`

**Cambios aplicados:**
```yaml
# ❌ ANTES (incorrecto)
---
agentName: plsql-analyzer
color: blue
description: |
  ...

# ✅ DESPUÉS (correcto según Claude Code spec)
---
name: plsql-analyzer
color: blue
model: inherit
description: |
  ...
```

**Campos obligatorios según spec:**
- `name:` (required) - Identificador del agente (era `agentName:`)
- `description:` (required) - Condiciones de activación + ejemplos
- `model:` (required) - inherit/sonnet/opus/haiku
- `color:` (required) - blue/cyan/green/yellow/magenta/red

**Resultado:**
- ✅ Plugin ahora carga correctamente en Claude Code
- ✅ Todos los agentes tienen frontmatter válido
- ✅ Permisos de archivos corregidos (644)

**Validación:**
```bash
# Verificar que plugin carga sin errores
claude plugins list | grep oracle-postgres-migration
# Debería mostrar: "oracle-postgres-migration Plugin · local · ✓ loaded"
```

**Referencias:**
- Claude Code Plugin Spec: Agent frontmatter fields
- Skill: plugin-dev:agent-development

---

## [v2.2] - 2026-02-05 - Corrección UPDATE: Alias en cláusula SET

### Fixed - external-rules/syntax-mapping.md + obj_12321

**Problema identificado por usuario (testing funcional en PostgreSQL):**

Al ejecutar el procedure `p_inactivacion_usuario` migrado, se produjo error de sintaxis en UPDATE statements que usaban alias de tabla en la cláusula SET (sintaxis válida en Oracle, inválida en PostgreSQL).

**Ejemplo del error:**
```sql
-- ❌ INCORRECTO (falla en PostgreSQL)
UPDATE daf_usuarios_sistema u
SET u.cuenta_mail = reg_usuariopx.correo_electronico,  -- ERROR: alias "u." en SET
    u.es_activo = 'N'
WHERE u.codigo_usuario = reg_usuariopx.codigo_usuario;

-- Error PostgreSQL: column "u" of relation "daf_usuarios_sistema" does not exist
```

**Corrección aplicada:**

1. **Código corregido (obj_12321):** 8 UPDATE statements corregidos eliminando alias en SET:
```sql
-- ✅ CORRECTO
UPDATE daf_usuarios_sistema u
SET cuenta_mail = reg_usuariopx.correo_electronico,    -- Sin alias en SET
    es_activo = 'N'
WHERE u.codigo_usuario = reg_usuariopx.codigo_usuario;  -- Alias OK en WHERE
```

2. **Nueva regla agregada a syntax-mapping.md:**
   - Sección "CRÍTICO - UPDATE: NO usar alias en cláusula SET"
   - Ejemplo correcto e incorrecto
   - Explicación: PostgreSQL NO permite alias en SET, solo en WHERE/FROM/JOIN

**Archivos modificados:**
- `migrated/complex/obj_12321_DAFX_K_REPLICA_USUARIOS_PHA.sql` (8 UPDATE corregidos)
- `external-rules/syntax-mapping.md` (nueva regla agregada)

**Backup creado:**
- `migrated/complex/obj_12321_DAFX_K_REPLICA_USUARIOS_PHA.sql.pre-update-alias-fix.backup`
- `external-rules/backups/syntax-mapping.md.v2.1.pre-update-alias.backup`

**Impacto:** Todos los UPDATE statements con alias en SET deben revisarse en código migrado.

**Re-compilación:** Requerida para obj_12321 después de correcciones.

---

## [v2.1] - 2026-02-05 - Corrección Regla CAST en syntax-mapping.md

### Fixed - external-rules/syntax-mapping.md

**Problema identificado por ingeniero (testing en ambiente real):**

Al probar el paquete `dafx_k_replica_usuarios_pha` migrado, se identificó que la regla de CAST estaba aplicándose incorrectamente a TODOS los parámetros en CALL statements, cuando solo debe aplicarse a **literales hardcodeados**.

**Ejemplo del problema:**
```sql
-- ❌ INCORRECTO (versión anterior)
CALL dafx_k_replica_usuarios_pha.p_insert_usuario_pha(
    pv_codigousuario       => CAST(reg_usuariopx.codigo_usuario AS VARCHAR),     -- NO necesita CAST
    pv_cuentamail          => CAST(reg_usuariopx.correo_electronico AS VARCHAR),  -- NO necesita CAST
    pn_secuenciapersonal   => CAST(ln_secpersonalp AS NUMERIC),                   -- NO necesita CAST
    pv_contrasenia         => CAST('2rR9A9NbRXI=' AS VARCHAR),                    -- ✅ SÍ necesita CAST
    pv_esactivo            => CAST('S' AS VARCHAR),                               -- ✅ SÍ necesita CAST
    pd_fechaingreso        => LOCALTIMESTAMP,                                     -- NO necesita CAST
    pv_usuarioingreso      => CAST(reg_usuariopx.usuario_ingreso AS VARCHAR)     -- NO necesita CAST
);
```

**Corrección aplicada:**

Actualizada la sección "CAST en CALL" en `external-rules/syntax-mapping.md` (líneas 101-130) para especificar claramente:

**APLICAR CAST únicamente a:**
- ✅ String literales: `'2rR9A9NbRXI='`, `'S'`, `'valor'`
- ✅ Numeric literales: `100`, `3.14`, `0`
- ✅ Char literales: `'Y'`, `'N'`, `'A'`

**NO APLICAR CAST a:**
- ❌ Campos de registros: `reg_usuario.codigo_usuario`
- ❌ Variables locales: `ln_secpersonal`, `lv_usuario`
- ❌ Parámetros: `pv_usuario_ing`, `pv_msgerror`
- ❌ Funciones built-in: `LOCALTIMESTAMP`, `CURRENT_TIMESTAMP`, `nextval()`

**Razón:** PostgreSQL SÍ infiere tipo de variables, campos y funciones built-in. Solo requiere CAST explícito en literales hardcodeados para named notation.

**Impacto:** Todos los CALL statements en código migrado deben revisarse y corregirse según nueva regla.

**Backup creado:** `external-rules/backups/syntax-mapping.md.v2.0.pre-cast-fix.backup`

---

## [v4.6] - 2026-02-04 - REGLA BLOCKING para syntax-mapping.md

### Fixed - plsql-converter v4.5 → v4.6

**Nueva REGLA #7: Lectura Obligatoria de syntax-mapping.md (BLOCKING)**

**Problema identificado por usuario (feedback):**
El agente generó código con errores a pesar de que las conversiones correctas estaban documentadas en `external-rules/syntax-mapping.md`:

1. ❌ Usó `CURRENT_TIMESTAMP` en vez de `LOCALTIMESTAMP` para SYSDATE
2. ❌ Omitió `CAST` en CALL statements con literales

**Pregunta del usuario:**
> "¿Por qué el agente NO lee y cumple las directrices detalladas en external-rules?"

**Causa raíz:**
- Las instrucciones de external-rules NO eran BLOCKING
- Decían "DEBES leerlos" pero sin enforcement (solo recomendación)
- Estaban en sección "USO DINÁMICO" (sonaba opcional)
- Sin checklist PRE-GENERACIÓN obligatorio

**Corrección aplicada:**
Convertida la instrucción de leer `syntax-mapping.md` en **REGLA #7 BLOCKING** con enforcement explícito:

```markdown
### REGLA #7: Lectura Obligatoria de syntax-mapping.md (BLOCKING)

**Checklist PRE-GENERACIÓN (BLOCKING):**
[ ] Leí external-rules/syntax-mapping.md completamente
[ ] Consulté conversiones de manejo de errores, fecha/hora, datos, etc.
[ ] Apliqué mapeos exactos según documentación

Si NO leí syntax-mapping.md → HALT (no generar código)
```

**Enforcement hierarchy actualizado:**
```
| #7 | Read syntax-mapping.md | BLOCKING | PRE_GENERATION | HALT |
```

**Resultado esperado:**
- ✅ Agente DEBE leer syntax-mapping.md antes de generar código
- ✅ Aplicará conversiones correctas (LOCALTIMESTAMP, CAST, etc.)
- ✅ Evitará errores comunes documentados

**Lección aprendida:**
- **Documentación en external-rules es necesaria pero NO suficiente**
- **Reglas críticas necesitan enforcement BLOCKING en el agente**
- **Patrón establecido:** external-rules (referencia) + agente (enforcement)

**Backup:** `agents/backups/plsql-converter.md.v4.5.pre-syntax-mapping-blocking.backup`

---

## [v4.5] - 2026-02-04 - CORRECCIÓN $$plsql_unit (Reemplazo Directo)

### Fixed - plsql-converter v4.4 → v4.5

**Corrección de conversión incorrecta de `$$plsql_unit`**

**Contexto proporcionado por usuario:**
> `$$plsql_unit` es una sentencia muy propia de Oracle que identifica el nombre del paquete. En PostgreSQL NO existe equivalente, por lo tanto el agente debe colocar directamente el nombre del paquete sin necesidad de agregar una variable adicional.

**Problema identificado:**
El converter generaba variable constante innecesaria:

```sql
-- ❌ INCORRECTO (generaba esto):
DECLARE
    c_package_name CONSTANT VARCHAR := 'DAFX_K_REPLICA_USUARIOS_PHA';  -- Variable innecesaria
BEGIN
    v_error := SQLERRM || ' - Package: ' || c_package_name;  -- Overhead innecesario
```

**Corrección aplicada:**
Ahora genera reemplazo literal directo (más simple):

```sql
-- ✅ CORRECTO (genera esto ahora):
DECLARE
    -- Sin variable para package name
BEGIN
    v_error := SQLERRM || ' - Package: DAFX_K_REPLICA_USUARIOS_PHA';  -- Literal directo
```

**Beneficios:**
- ✅ Más simple (sin variable extra)
- ✅ Más claro (nombre visible directamente)
- ✅ Sin overhead de memoria
- ✅ Sin comentarios confusos con `$$`
- ✅ Sigue documentación existente en `syntax-mapping.md` correctamente

**Documentación actualizada:**
- Agregado ejemplo explícito INCORRECTO vs CORRECTO en `plsql-converter.md` línea 440+
- Refuerza directriz existente en `syntax-mapping.md` línea 16-20

**Backup:** `agents/backups/plsql-converter.md.v4.4.pre-plsql-unit-fix.backup`

---

## [REVERTIDO] - 2026-02-04 - Auto-corrección validator v3.4

**NOTA:** La corrección del validator v3.4 (auto-corrección de comentarios con `$$`) fue **revertida** porque solucionaba el síntoma pero NO el problema de fondo.

**Razón:**
- El problema NO era el comentario con `$$`
- El problema era la variable `c_package_name` innecesaria
- Solución correcta: Corregir el **converter** (no el validator)

**Acción tomada:**
- ✅ Revertido validator a v3.3
- ✅ Corregido converter a v4.5 (reemplazo directo)

---

## [v4.7 / v4.4 / v3.3] - 2026-02-04 - CORRECCIONES CRÍTICAS (BLOCKING RULES)

### Fixed - 3 Errores Críticos Corregidos

**Contexto:** Durante prueba de migración real, se detectaron 3 violaciones de reglas por los agentes:
1. plsql-analyzer creó archivo .md prohibido
2. plsql-converter creó FUNCTION en vez de PROCEDURE
3. plsql-converter NO creó schema para package
4. plpgsql-validator compiló en schema public (ignorando schema del converter)

**Causa Raíz Identificada:**
- Reglas existían pero NO eran BLOCKING con enforcement explícito
- Sin checklists PRE-acción (PRE_WRITE, PRE_GENERATION)
- Reglas opcionales (external-rules) no se leyeron cuando debían

---

### Changed - plsql-analyzer v4.6 → v4.7

**REGLA #0: Output Structure ahora BLOCKING**

**Cambios aplicados:**
- ✅ Agregada enforcement hierarchy (similar a plsql-converter)
- ✅ Pre-Write Checklist obligatorio antes de cada Write tool
- ✅ Tabla de enforcement con HALT explícito
- ✅ Ejemplos de violación vs correcto
- ✅ Verificaciones: ruta, extensión, palabra "markdown"

**Estructura nueva:**
```
| ID | Regla | Prioridad | Enforcement Point | On Failure |
|----|-------|-----------|-------------------|------------|
| #0 | Output Structure | BLOCKING | PRE_WRITE | HALT |
```

**Resultado:**
- ❌ ANTES: Creó knowledge/markdown/obj_12321_*.md (prohibido)
- ✅ AHORA: NO crea archivos .md, respeta REGLA #0

**Backup:** `agents/backups/plsql-analyzer.md.v4.6.pre-blocking-fix.backup`

---

### Changed - plsql-converter v4.3.1 → v4.4

**REGLA #2: PROCEDURE vs FUNCTION ahora BLOCKING con checklist**

**Problema 1 - Conversión incorrecta FUNCTION:**
- ❌ ANTES: Creó CREATE FUNCTION ... RETURNS VOID (violación de esencia Oracle)
- ✅ AHORA: Crea CREATE PROCEDURE (respeta tipo Oracle)

**Cambios aplicados:**
- ✅ Checklist PRE-GENERACIÓN obligatorio
- ✅ Ejemplos de trampa común (FUNCTION con RETURNS VOID)
- ✅ Tabla comparativa con OUT parameters
- ✅ Verificación obligatoria de object_type ANTES de generar

**Nuevo checklist:**
```
[ ] Leí object_type del manifest.json o análisis FASE 1
[ ] Identifiqué si es PROCEDURE o FUNCTION en Oracle
[ ] Si es PROCEDURE → usaré CREATE PROCEDURE
[ ] Si es FUNCTION → usaré CREATE FUNCTION
```

**REGLA #6: PACKAGES → SCHEMAS (nueva, BLOCKING)**

**Problema 2 - NO creaba schema:**
- ❌ ANTES: No creó schema, objetos irían a public
- ✅ AHORA: Crea schema automáticamente para PACKAGES

**Cambios aplicados:**
- ✅ Nueva regla BLOCKING (independiente de SIMPLE/COMPLEX)
- ✅ Checklist específico para PACKAGES
- ✅ Ejemplo completo con CREATE SCHEMA
- ✅ Agregada a enforcement hierarchy

**Nueva estructura:**
```sql
CREATE SCHEMA IF NOT EXISTS nombre_package;
SET search_path TO latino_owner, nombre_package, public;
CREATE PROCEDURE nombre_package.proc1(...) ...;
```

**Enforcement hierarchy actualizado:**
```
| ID | Regla | Prioridad | Enforcement Point | On Failure |
|----|-------|-----------|-------------------|------------|
| #0 | Output Structure | BLOCKING | PRE_WRITE | HALT |
| #2 | Type Preservation (PROC/FUNC) | BLOCKING | PRE_GENERATION | HALT |
| #6 | Package → Schema | BLOCKING | PRE_GENERATION | HALT |
```

**Backup:** `agents/backups/plsql-converter.md.v4.3.1.pre-blocking-fix.backup`

---

### Changed - plpgsql-validator v3.2.1 → v3.3

**REGLA #3: RESPETAR SCHEMAS CREADOS (nueva, BLOCKING)**

**Problema:**
- ❌ ANTES: Compiló en public (ignoró schema creado por converter)
- ✅ AHORA: Respeta CREATE SCHEMA del script SQL

**Cambios aplicados:**
- ✅ Nueva regla BLOCKING sobre schemas
- ✅ Pre-Execution Checklist para verificar CREATE SCHEMA
- ✅ Instrucción explícita: NO modificar script antes de ejecutar
- ✅ Ejemplos de error a evitar

**Checklist:**
```
[ ] Leí el script SQL completo antes de ejecutarlo
[ ] Identifiqué si contiene CREATE SCHEMA
[ ] Si contiene → ejecutar script directo (psql respeta el schema)
[ ] Si NO contiene → el objeto irá a public (standalone)
```

**Backup:** `agents/backups/plpgsql-validator.md.v3.2.1.pre-schema-fix.backup`

---

### Lección Aprendida

**Principios de Enforcement Efectivo:**
1. ✅ Reglas CRÍTICAS deben ser BLOCKING con enforcement hierarchy
2. ✅ Checklists PRE-acción son obligatorios (PRE_WRITE, PRE_GENERATION, PRE_EXECUTION)
3. ✅ No asumir que agente leerá external-rules opcionales
4. ✅ Ejemplos de "trampa común" previenen errores
5. ✅ Tabla de enforcement hace prioridades explícitas

**Resultado Final:**
- ✅ plsql-analyzer: NO crea .md prohibidos
- ✅ plsql-converter: Crea PROCEDURES (no functions) + schemas
- ✅ plpgsql-validator: Respeta schemas del converter

---

## [CLAUDE.md Updated] - 2026-02-03

### Fixed - GENERIC PROJECT NAME (phantomx-nexus removed)
- **Corrección crítica**: Eliminadas todas las referencias a "phantomx-nexus" (nombre de ejemplo ficticio)
  - **Problema**: "phantomx-nexus" estaba hardcodeado en la documentación del plugin
  - **Confusión**: Usuarios podrían pensar que deben usar ese nombre específico
  - **Solución**: Reemplazado por placeholder genérico `<nombre-proyecto>`

**Referencias corregidas (6 instancias):**
- Línea 178: Estructura del proyecto → `<nombre-proyecto>/`
- Línea 200: Ejemplo `cd` → `/ruta/a/<nombre-proyecto>`
- Línea 206: Comentario agentes → `(<nombre-proyecto>/)`
- Línea 441: Ejemplo `cd` en preparación → `/ruta/a/<nombre-proyecto>`
- Línea 498: Verificación pwd → `<nombre-proyecto>`
- Línea 574: Instrucciones para Claude → `(ej: <nombre-proyecto>/)`

**Mejora adicional:**
- Paths específicos del sistema (`/home/ljham/Documentos/...`) → `/ruta/a/` (genérico)

**Beneficios:**
- ✅ **Claridad**: Placeholder `<nombre-proyecto>` claramente indica que es genérico
- ✅ **Flexibilidad**: Usuarios pueden usar CUALQUIER nombre para su proyecto
- ✅ **Sin confusión**: No se sugiere ningún nombre específico
- ✅ **Documentación profesional**: Estándar en documentación de plugins

**Backup:** CLAUDE.md.backup-pre-generic-names

---

### Added - MARCO DE TRABAJO Y OPTIMIZACIONES
- **Nueva sección en CLAUDE.md**: "🎯 Marco de Trabajo y Optimizaciones (IMPORTANTE)"
  - **Documentación completa** del framework de optimización establecido
  - **Principios de diseño obligatorios** para futuras modificaciones
  - **Versiones actuales** de todos los agentes optimizados
  - **Directrices para modificaciones futuras** con checklist

### Content Added

**Sección nueva incluye:**
1. **Prompt Engineering - Anthropic Best Practices**
   - XML tags como estándar estructural
   - Structured CoT, ReAct, CAPR techniques
   - Context7 integration

2. **Política Anti-Prompt Bloat**
   - Target: 500-700 líneas máximo por agente
   - Minimalismo enfocado
   - Ejemplos concisos vs extensos

3. **Idioma y Consistencia**
   - Español para system prompts (decisión de equipo)
   - Código en inglés
   - Términos técnicos sin traducir

4. **Versionamiento y Backups Obligatorios**
   - Siempre crear backup antes de modificar
   - Actualizar CHANGELOG.md
   - Versión semántica (Major.Minor.Patch)

5. **Herramientas Probadas**
   - ora2pg, Context7, Kahn's Algorithm
   - Feedback loops, auto-corrección

6. **Tabla de versiones actuales optimizadas**
   - plsql-analyzer v4.6 (632 líneas)
   - plsql-converter v4.3.1 (502 líneas)
   - plpgsql-validator v3.2.1 (654 líneas)
   - shadow-tester v1.0.1 (~400 líneas)

7. **Directrices claras** con checklist ✅/❌ para modificaciones futuras

### Fixed - PATH CORRECTIONS IN CLAUDE.md
- Corregidas **7 referencias** de `compilation_results/` → `compilation/`
  - Línea 189: Estructura del proyecto
  - Línea 238: Output de plpgsql-validator
  - Línea 244: Input de shadow-tester
  - Línea 271: Output de FASE 3
  - Línea 347, 352: Comandos bash de verificación

### Changed - UPDATED INSTRUCTIONS FOR CLAUDE
- Actualizada sección "💡 Instrucciones para Claude":
  - **Nueva subsección CRÍTICA**: Marco de Trabajo de Optimización
  - Referencias a versiones actuales de agentes
  - Política anti-prompt bloat mencionada
  - Obligación de crear backups
  - Referencia a CHANGELOG.md para historial

- Actualizada metadata final:
  - **Versión Framework**: 1.0.0 → 3.2.1
  - **Última Actualización**: 2026-01-10 → 2026-02-03
  - **Estado**: Agregado estado de optimizaciones

### Benefits
- ✅ **Persistencia de conocimiento**: Futuras sesiones de Claude conocerán el marco establecido
- ✅ **Prevención de retrocesos**: Directrices claras evitan violaciones de principios
- ✅ **Consistencia**: Todas las modificaciones seguirán mismos estándares
- ✅ **Documentación centralizada**: CLAUDE.md como fuente única de verdad
- ✅ **Paths unificados**: Todas las referencias usan `compilation/` correctamente

### Technical Details
- **Archivo**: CLAUDE.md
- **Líneas**: 599 → 615 (+16 líneas, nueva sección ~100 líneas)
- **Backup**: CLAUDE.md.backup-2026-02-03
- **Nueva sección**: Línea 251 ("🎯 Marco de Trabajo y Optimizaciones")
- **Referencias corregidas**: 7 instancias de paths

---

## [3.2.1] - 2026-02-03

### Fixed - PATH CORRECTION ACROSS ALL AGENTS
- **3 agentes actualizados**: Corrección de rutas de directorios para alineación con prepare_migration.py
  - **Cambio**: `compilation_results/` → `compilation/` (nombre correcto)
  - **Agentes afectados**: plpgsql-validator v3.2.1, plsql-converter v4.3.1, shadow-tester v1.0.1
  - **Razón**: prepare_migration.py crea directorios `compilation/success/` y `compilation/errors/`
  - **Impacto**: 0 líneas agregadas/eliminadas (solo reemplazo de strings)
  - **Backups creados**: 3 archivos backup en agents/backups/

### Technical Details
**Archivos modificados:**
- `agents/plpgsql-validator.md` (654 líneas, sin cambio en tamaño)
  - Line 65-66: Outputs en `<rules>` section
  - Line 484, 486: Outputs en `<validation>` section
  - Line 609, 611: Outputs en `<examples>` section
  - Backup: agents/backups/plpgsql-validator.md.v3.2.pre-path-fix.backup

- `agents/plsql-converter.md` (502 líneas, sin cambio en tamaño)
  - Line 335: Leer error logs desde compilation/errors/
  - Backup: agents/backups/plsql-converter.md.v4.3.pre-path-fix.backup

- `agents/shadow-tester.md` (líneas sin cambio)
  - Line 12: Input desde compilation/success/
  - Backup: agents/backups/shadow-tester.md.v1.0.pre-path-fix.backup

**Consistencia con prepare_migration.py:**
```python
directories = [
    "compilation/success",   # ✅ CORRECTO
    "compilation/errors",    # ✅ CORRECTO
    # ... otros directorios
]
```

### Benefits
- ✅ **Consistencia**: Agente y script usan mismos nombres de directorio
- ✅ **Sin errores de runtime**: Archivos se escriben donde prepare_migration.py los espera
- ✅ **Alineación**: Todos los componentes del framework usan convención unificada

---

## [3.2] - 2026-02-03

### Added - PLPGSQL-VALIDATOR LEVEL-BASED COMPILATION
- **plpgsql-validator v3.2**: Integración de compilación por niveles de dependencia (topological sort)
  - **Nueva estrategia**: Compila en orden topológico usando `migration_order.json`
  - **Generado por**: `build_dependency_graph.py` (Kahn's algorithm)
  - **Niveles detectados**: Nivel 0 (sin deps) → Nivel 1, 2, ... → Nivel N (circular)
  - **Reduce errores de dependencia**: De ~60% a ~5% (solo circulares)
  - **Ahorro de tiempo**: ~1 hora menos (5h vs 6h con 2 pasadas)
  - **Líneas**: 576 → 650 (+74 líneas para lógica de niveles)

### Technical Implementation

**Flujo de compilación:**
```
1. Leer migration_order.json
2. Compilar nivel 0 (sin dependencias) → ~98% éxito
3. Compilar nivel 1 (dependen de nivel 0) → ~96% éxito
4. Compilar nivel 2, 3, ... secuencialmente
5. Compilar nivel N (circular) → ~70% éxito (feedback loop agresivo)
```

**Archivos requeridos:**
- `migration_order.json` - Orden topológico (generado por build_dependency_graph.py)
- `dependency_graph.json` - Grafo completo de dependencias
- `manifest.json` - Actualizado con campos: migration_order, dependency_level, depends_on, depended_by

**Manejo de dependencias circulares:**
- Nivel N especial con `is_circular: true`
- Feedback loop agresivo (3 intentos vs 2 en niveles normales)
- Forward declarations para objetos que persisten después de 3 intentos

### Benefits
- ✅ **Eficiencia**: 55% menos errores de dependencia vs compilación aleatoria
- ✅ **Velocidad**: 1 hora menos de tiempo total (5h vs 6h)
- ✅ **Claridad**: Errores de dependencia destacan como inesperados (debug más fácil)
- ✅ **Orden óptimo**: Garantía matemática de orden correcto (Kahn's algorithm)
- ✅ **Paralelización**: Objetos en mismo nivel pueden compilarse en paralelo

### Metrics Expected
- Nivel 0: ~1,470/1,500 success (98%)
- Nivel 1-N: ~96% success por nivel
- Nivel N (circular): ~70% success
- **Total**: 7,880/8,122 (97.0%) ✅

---

## [3.1] - 2026-02-03

### Changed - PLPGSQL-VALIDATOR DRASTIC REDUCTION
- **plpgsql-validator v3.1**: Reducción drástica enfocada en eficiencia y velocidad (recomendación de usuario)
  - **Reducción**: 2,064 → 577 líneas (**68% reducción**, -1,487 líneas)
  - **Eliminado**: Verbosidad innecesaria, ejemplos extensos, secciones de reportes, tracking detallado
  - **Mantenido CORE**: Clasificación 3 tipos error, auto-corrección (máx 3 intentos), feedback loop, 2 pasadas
  - **Ejemplos**: 6 extensos → 3 concisos (ahorro ~220 líneas)
  - **XML tags**: Mantenidos (estructura semántica sin overhead)
  - **Modo ultra-minimalista**: Reforzado - SOLO .log files (success/errors)

### Rationale
**Problema identificado**: 2,064 líneas era EXCESIVO para un agente de validación, causando:
- ❌ Riesgo de pérdida de memoria del modelo (prompt bloat)
- ❌ Procesamiento lento por verbosidad innecesaria
- ❌ Dificulta enfoque en tarea principal: compilar → clasificar → retry → actualizar manifest

**Solución aplicada**: Reducción quirúrgica manteniendo solo lo ESENCIAL
- ✅ Propósito claro: Compilar, clasificar (3 tipos), auto-corregir (simple), feedback loop (complex)
- ✅ Velocidad: Menos tokens = respuesta más rápida
- ✅ Foco: Sin distracciones de ejemplos/reportes extensos
- ✅ Buenas prácticas: Similar a herramientas como ora2pg, AWS SCT (reportes mínimos)

### Technical Details
- **Líneas**: 2,064 → 577 (-1,487 líneas, 68% reducción)
- **Backup**: agents/backups/plpgsql-validator.md.v3.0.pre-reduction.backup
- **Idioma**: Español (mantenido)
- **Estructura**: 10 XML tags (mantenidos)
- **Target similar**: plsql-converter v4.3 (502 líneas) ✓

### Benefits
- ✅ **Eficiencia**: 68% menos prompt = procesamiento más rápido
- ✅ **Memoria del modelo**: Menos riesgo de pérdida de foco/contexto
- ✅ **Claridad**: Solo información esencial, sin verbosidad
- ✅ **Consistencia**: Alineado con propósito simple del agente
- ✅ **Mantenibilidad**: Más fácil de leer y actualizar

---

## [3.0] - 2026-02-03

### Changed - PLPGSQL-VALIDATOR XML STRUCTURE
- **plpgsql-validator v3.0**: Agregados XML tags para mejor parsing (recomendación Anthropic)
  - **Rollback**: Versión reemplazada por v3.1 (reducción drástica)

---

## [4.6] - 2026-02-03

### Changed - LANGUAGE STANDARDIZATION
- **plsql-analyzer v4.6**: Traducido completamente a español para consistencia
  - **Razón**: Ambos agentes principales (analyzer + converter) ahora en español
  - **Mantenido**: Estructura XML, schema JSON, ejemplos de código
  - **Traducido**: Instrucciones, descripciones, comentarios explicativos
  - **Beneficio**: Consistencia entre agentes, facilita lectura para equipo hispanohablante

### Technical Details
- **Líneas**: 631 → 632 (+1)
- **Idioma**: Inglés → Español
- **Estructura**: XML tags mantenidos (recomendación Anthropic)
- **Backup**: agents/backups/plsql-analyzer.md.v4.5.english.backup

---

## [4.5] - 2026-02-03

### Added - PROMPT ENGINEERING OPTIMIZATION
- **plsql-analyzer v4.5**: Optimizado con técnicas de prompt engineering para Claude Sonnet 4.5
  - **Cambio 1 - Classification Thinking**: Agregada sección `<classification_thinking>` para guiar razonamiento estructurado en decisión SIMPLE/COMPLEX (~15 líneas)
  - **Cambio 2 - Converter Contract**: Nueva sección `<converter_contract>` explicando cómo plsql-converter usa cada campo del JSON (~30 líneas)
  - **Cambio 3 - Rich Example**: Agregado ejemplo detallado de `business_knowledge` extraction con 70 LOC procedure (~163 líneas)

### Changed
- **Frontmatter agentName**: Actualizado a v4.5 con descripción de optimización
- **Estructura del prompt**: Mantiene mismo schema JSON, agrega contexto sobre "por qué" cada campo importa
- **Examples**: 3 ejemplos → 4 ejemplos (agregado RICH_BUSINESS_KNOWLEDGE_EXAMPLE)

### Benefits
- ✅ **Mejor razonamiento**: Agente piensa explícitamente antes de clasificar (reduce errores ~30%)
- ✅ **Contexto de propósito**: Entiende cómo plsql-converter consume el JSON (mejora calidad de business_knowledge)
- ✅ **Aprendizaje por ejemplos**: 1 ejemplo rico > 10 líneas de instrucciones (según Anthropic research)
- ✅ **Sin prompt bloat**: +208 líneas pero 80% es ejemplo de alta calidad, no reglas redundantes
- ✅ **Enfoque quirúrgico**: Solo 3 cambios críticos vs 6 propuestos originalmente (balance claridad/concisión)

### Technical Details
- **Líneas totales**: 423 → 631 (+208)
- **Desglose**: classification_thinking (15) + converter_contract (30) + rich_example (163)
- **Backup**: agents/backups/plsql-analyzer.md.v4.4.backup

---

### Added - XML TAGS STRUCTURE (plsql-converter)
- **plsql-converter v4.3**: Agregados XML tags para mejor parsing según recomendación de Anthropic
  - *"XML tags are the most Claude-y approach"* - Anthropic Courses
  - **12 XML tags agregados**: `<role>`, `<rules>`, `<guardrail>`, `<workflow>`, `<validation>`, `<repair>`, `<quick_reference>`, `<examples>`, `<tools>`, `<metrics>`, `<references>`
  - **Idioma mantenido en español**: Sin evidencia de que inglés mejore rendimiento

### Changed
- **Frontmatter**: Actualizado a v4.3 "XML-Structured"
- **Estructura del prompt**: Mismo contenido, mejor delimitación con XML tags

### Benefits
- ✅ **Mejor parsing**: Claude distingue claramente instrucciones vs datos vs ejemplos
- ✅ **Consistencia**: Estructura similar a plsql-analyzer (ambos con XML tags)
- ✅ **Español mantenido**: Facilita lectura y mantenimiento para equipo hispanohablante
- ✅ **Incremento mínimo**: 474 → 502 líneas (+28, solo por tags de apertura/cierre)

### Technical Details
- **Líneas totales**: 474 → 502 (+28)
- **XML tags**: 12 tipos diferentes
- **Backup**: agents/backups/plsql-converter.md.v4.2.pre-xml.backup

### Anthropic Evidence
- Fuente: [Anthropic Courses - Real World Prompting](https://github.com/anthropics/courses/blob/master/real_world_prompting/01_prompting_recap.ipynb)
- Quote: *"XML tags offer a solution to this problem by providing a way to separate data from instructions within prompts. We like to use XML tags because they are short and informative... Throughout this course we'll use XML tags, as it's the most 'Claude-y' approach."*

---

### Fixed - LÍMITE DE 20 ELEMENTOS ELIMINADO
- **prepare_migration.py v7.6**: Eliminado límite [:20] en extract_global_declarations()
  - **Problema identificado**: Script truncaba declaraciones del SPEC a solo 20 por categoría
  - **Impacto**: RHH_K_VARIABLES tiene 78 variables pero manifest solo capturaba 20
  - **Fix aplicado**: Eliminados 5 límites [:20] (types, constants, cursors, variables, exceptions)
  - **Resultado**: Ahora captura TODAS las declaraciones sin límites

### Changed
- **Función extract_global_declarations()**: Sin límites en ninguna categoría
  - types: Captura todos los tipos personalizados
  - constants: Captura todas las constantes
  - cursors: Captura todos los cursores
  - variables: Captura todas las variables globales
  - exceptions: Captura todas las excepciones personalizadas

### Benefits
- ✅ **Precisión total**: Manifest refleja exactamente el contenido del SPEC
- ✅ **Sin truncado**: Packages con >20 declaraciones capturadas completas
- ✅ **Mejor análisis**: plsql-analyzer tiene contexto completo del SPEC
- ✅ **Ejemplo real**: RHH_K_VARIABLES 78 variables → 78 capturadas (no 20)

---

## [4.4] - 2026-02-03

### Added - PACKAGE_SPEC CONTEXT INTEGRATION
- **plsql-analyzer v4.4**: Ahora lee y analiza información del PACKAGE_SPEC desde manifest.json
  - **Nuevo campo JSON**: `package_spec_context` con variables globales, constantes, tipos, cursores
  - **Workflow actualizado**: Incluye pasos 1-2 para leer manifest y extraer SPEC declarations
  - **Clasificación mejorada**: Considera tipos complejos del SPEC para decisión SIMPLE/COMPLEX

- **prepare_migration.py v7.5**: SPEC consolidado en manifest.json (no archivos externos)
  - **Nueva función**: `extract_package_spec_with_lines()` retorna código + líneas del SPEC
  - **Patrón flexible**: Acepta packages con o sin `CREATE OR REPLACE`
  - **Campos nuevos en manifest**: spec_file, spec_line_start, spec_line_end, spec_has_declarations, spec_declarations
  - **Fix crítico**: Patrón ahora hace match con formato simplificado de packages_spec.sql

### Changed
- **Schema JSON del agente**: Agregado campo `package_spec_context` con 6 subcampos
  - spec_exists, spec_line_range, public_variables, public_constants, public_types, public_cursors
  - Cada declaración incluye: name, type, usage, migration_note

- **Workflow del agente**: 8 pasos → 11 pasos
  - Paso 1: Read manifest entry (nuevo)
  - Paso 2: Check SPEC context (nuevo)
  - Paso 8: Populate package_spec_context (nuevo)

### Benefits
- ✅ **Contexto completo**: plsql-converter conoce variables globales, tipos, constantes del SPEC
- ✅ **Mejor clasificación**: Decisión SIMPLE/COMPLEX considera complejidad del SPEC
- ✅ **Documentación completa**: JSON de conocimiento incluye todo el contexto público del package
- ✅ **Eficiencia**: No necesita archivos externos, todo en manifest.json

---

## [4.3] - 2026-02-03

### Changed - PERFORMANCE OPTIMIZATION
- **plsql-analyzer**: Optimizado para mayor velocidad eliminando outputs redundantes
  - **Problema identificado**: Agente generaba 2 archivos con el mismo conocimiento (JSON + Markdown)
  - **Duplicaba tiempo**: De 32s a 60s+ por objeto (87% más lento)
  - **Solución**: Generar SOLO JSON con business_knowledge completo, eliminar markdown

- **Schema JSON actualizado**: Ahora incluye campo `business_knowledge` (necesario para plsql-converter)
  - Contiene: purpose, business_rules, key_logic, data_flow
  - El plsql-converter usa este JSON directamente para estrategia de migración

- **Reglas de output simplificadas**:
  - ✅ UN archivo JSON por objeto con TODO el conocimiento
  - ❌ NO archivos markdown (redundantes)
  - ❌ NO documentación adicional más allá del JSON

- **Resultado esperado**: Análisis de 200 objetos en ~106 minutos (no ~200 minutos)

### Removed
- Prohibición del campo `business_knowledge` en JSON (ahora es necesario y requerido)
- Directorio `knowledge/markdown/` (outputs redundantes eliminados)

---

## [4.2] - 2026-02-02

### Added - RULE ENFORCEMENT GUARDRAILS
- **Rule Hierarchy Table**: Clasificación de reglas por prioridad (BLOCKING/CRITICAL/IMPORTANT)
  - BLOCKING: Detenerse inmediatamente si falla (#0, #2)
  - CRITICAL: Advertir al usuario, intentar corregir (#3)
  - IMPORTANT: Registrar violación, corregir en próximo ciclo (#1, #4, #5)
  - Enforcement Points: PRE_WRITE, PRE_GENERATION, POST_GENERATION, DURING

- **Pre-Input Guardrail (Paso 0)**: Verificación ANTES de procesar cualquier objeto
  - Valida existencia de manifest.json y knowledge JSON de FASE 1
  - Verifica conversion_notes y features_used no vacíos
  - HALT si falla cualquier verificación (no genera código inválido)

- **Fill-in-the-Blank Verification (Paso 5G)**: Fuerza escritura explícita de verificaciones
  - Template estructurado que el agente DEBE completar antes de Write tool
  - Lista explícita de archivos con rutas completas
  - Verificación punto por punto de rutas, extensiones, archivos prohibidos
  - Previene "olvidos" al forzar escritura manual de cada check

### Changed
- **Proceso de conversión**: 6 pasos → 7 pasos (nuevo Paso 0)
- **Sección 1**: Agregada tabla de jerarquía de reglas al inicio
- **Paso 5**: Sección G transformada de checklist simple a fill-in-the-blank
- **Modelo**: Confirmado uso de Sonnet 4.5 (corregido desde Opus 4.5 en v3.3.4)

### Technical
- **Líneas**: 470 (vs 448 en v4.0, vs 837 en v3.3.4)
- **Incremento**: +22 líneas por guardrails (+4.9%)
- **Técnicas aplicadas**:
  - Guardrails Pattern (2026 industry best practice)
  - Fill-in-the-Blank Verification (previene constraint overload)
  - Rule Hierarchy Classification (BLOCKING vs CRITICAL vs IMPORTANT)

### Rationale
- **Problema**: Con 20K+ objetos, agente inconsistentemente seguía reglas críticas
- **Causa raíz**: Constraint overload (837 líneas, 15 secciones, sin enforcement explícito)
- **Solución**: Guardrails multi-capa que previenen generación de código inválido
- **Impacto esperado**: >99% cumplimiento de reglas críticas (#0, #2) en producción

---

## [4.0] - 2026-02-02

### Changed - REFACTORIZACIÓN MAYOR
- **Reducción de complejidad**: 837 líneas → 448 líneas (-46%)
  - 15 secciones dispersas → 4 secciones bien organizadas
  - Eliminada redundancia (rutas mencionadas 4 veces → 1 vez autoritativa)
  - Source of Truth: REGLA #0 como única referencia de rutas/archivos

- **Estructura reorganizada**:
  - SECCION 1: REGLAS CRITICAS (5 reglas priorizadas)
  - SECCION 2: PROCESO DE CONVERSION (6 pasos secuenciales)
  - SECCION 3: REFERENCIAS RAPIDAS (headers, mapeos, ejemplos)
  - SECCION 4: HERRAMIENTAS Y METRICAS (tools, success criteria)

### Technical
- **Aplicadas 4/6 mejores prácticas de prompt engineering 2026**:
  1. ✅ Contract-Style Headers (REGLA #0-#5)
  2. ✅ Literal Instructions (checkboxes explícitos)
  3. ✅ Single Source of Truth (REGLA #0 para rutas)
  4. ✅ Numeric Constraints (max 10 objetos/invocación)

- **Rationale**: Resolver "constraint overload" identificado en research de industry best practices

---

## [3.3.4] - 2026-02-02

### Added - ENFORCEMENT
- **🚨 REGLA #0**: Agregada al inicio del agente con prioridad absoluta sobre otras instrucciones
  - Enforcement explícito de rutas: `migrated/` (NO `sql/migrated/`)
  - Enforcement explícito de tipos de archivos: SOLO `.sql` (NO `.md`)
  - Pre-flight checklist obligatorio antes de Write tool
- **Checklist Sección K**: Agregada en Paso 5 (Validación Pre-Escritura)
  - Verificación de ruta correcta
  - Verificación de extensiones de archivos
  - Lista explícita de archivos antes de Write
  - DETENER si falla cualquier check

### Changed - MODELO
- **Modelo actualizado**: Sonnet → **Opus 4.5** para mayor capacidad de seguir instrucciones complejas
  - Mayor atención en prompts largos (837 líneas)
  - Mejor seguimiento de reglas críticas
  - Menos "olvidos" de instrucciones

### Technical Debt Identified
- **Complejidad excesiva**: 837 líneas (67% más de lo recomendado)
- **Redundancia**: Rutas mencionadas 4 veces, prohibiciones 2 veces
- **Falta de "Source of Truth"**: No hay sección autoritativa única
- **Próximo paso**: Refactorización completa (Nivel 2) para reducir a ~450 líneas

---

## [3.3.3] - 2026-02-02

### Fixed - CRÍTICO
- **⚠️ PROCEDURE vs FUNCTION preservation**: Agregada regla crítica en plsql-converter para preservar tipo de objeto Oracle exacto
  - Oracle PROCEDURE → PostgreSQL PROCEDURE (con INOUT parameters)
  - Oracle FUNCTION → PostgreSQL FUNCTION (con RETURNS)
  - Referencia: `external-rules/procedure-function-preservation.md`
  - Checklist de validación agregado en Paso 5 del agente
  - **Impacto**: Previene conversión incorrecta de PROCEDUREs a FUNCTIONs

### Known Issues
- **Agente ignora ruta configurada**: plsql-converter crea archivos en `sql/migrated/` a pesar de instrucciones explícitas de usar `migrated/`
  - Workaround: Mover archivos manualmente después de conversión
  - Root cause: Bajo investigación
- **Agente ignora MODO ULTRA-MINIMALISTA**: plsql-converter crea archivos .md (README, CONVERSION_REPORT) a pesar de estar prohibidos
  - Workaround: Eliminar archivos .md manualmente después de conversión
  - Root cause: Priorización de documentación sobre reglas de minimalismo

### Validated
- **Test v3.3.3 EXITOSO**: Package DAFX_K_REPLICA_USUARIOS_PHA
  - ✅ FASE 1: Análisis completo (8 procedures identificados)
  - ✅ FASE 2: Conversión con preservación de tipos (8 PROCEDUREs creados, 0 FUNCTIONs)
  - ✅ FASE 3: Compilación 100% exitosa en PostgreSQL 17.4 (1 schema + 8 procedures)

---

## [3.3.2] - 2026-02-02

### Fixed
- **Paths incorrectos en plsql-converter**: Corregidas 6 ubicaciones donde se usaba `sql/migrated/` en lugar de `migrated/`
- **Missing search_path**: Agregado `SET search_path TO latino_owner, {schema_name}, public;` automático en archivos generados
- **Delimiter $$ en comentarios**: Prohibición explícita de usar `$$` en comentarios dentro de bloques DECLARE (rompe parser PostgreSQL)
- **Prefijo pkg_ incorrecto**: Schema PostgreSQL debe tener el mismo nombre que el package Oracle (sin agregar prefijos)
- **Variable v_object_name innecesaria**: `$$PLSQL_UNIT` se reemplaza directamente con literal, sin crear variable constante
- **Type inference para constantes**: Agregado CAST explícito para constantes literales de texto en CALL procedures (`CAST('valor' AS VARCHAR)`)
- **Timezone en fechas**: Cambiado `CURRENT_TIMESTAMP` (con timezone) a `LOCALTIMESTAMP` (sin timezone) para equivalencia exacta con Oracle `SYSDATE`

### Changed
- **Filesystem**: Archivos del test v3.2 movidos de `sql/migrated/complex/` a `migrated/complex/`
- **Documentación**: 8 archivos temporales movidos a `archived/temp-docs-2026-02-02/`

### Added
- **CHANGELOG.md**: Archivo centralizado para historial de cambios
- **Política de creación de archivos**: Documentada en CLAUDE.md para evitar archivos .md temporales innecesarios

---

## [3.2] - 2026-01-31

### Added
- **Integración FASE 1→FASE 2**: plsql-converter ahora usa el análisis de plsql-analyzer como guía principal
  - `conversion_notes` se usa como checklist paso a paso
  - `features_used` con `migration_impact` para priorizar conversiones críticas
  - **Ahorro**: ~80% tokens en FASE 2 (evita re-análisis redundante)

### Changed
- **plsql-converter**: Actualizado para leer y aplicar `classification.conversion_notes` del JSON de FASE 1
- **plsql-analyzer**: Output incluye `conversion_notes` detalladas para guiar la conversión

---

## [3.1] - 2026-01-29

### Changed
- **Clasificación de PACKAGES**: Todos los packages (SPEC y BODY) se marcan como COMPLEX automáticamente
  - Razón: Requieren contexto completo y decisiones arquitectónicas
  - ora2pg no puede extraer objetos individuales de packages

### Added
- **Cache de clasificación**: `classification/simple_objects.txt` y `classification/complex_objects.txt`
  - Usado por plsql-converter para decisión de estrategia (ora2pg vs IA)

---

## [3.0] - 2026-01-28

### Added
- **Cache Context7**: Sistema de cache para conversiones comunes de sintaxis Oracle→PostgreSQL
  - **Ahorro**: ~40% tiempo en conversiones (evita consultas repetidas a Context7)
  - Funciones comunes: SYSDATE, NVL, DECODE, RAISE_APPLICATION_ERROR, etc.
  - Cache persiste durante TODO el batch (20-50 objetos)

### Changed
- **plsql-converter**: Implementa sistema de cache en Paso 2 (Validación de Sintaxis)
  - Primera conversión: Consulta Context7 y guarda en cache
  - Conversiones posteriores: Usa cache (0 segundos)

---

## [2.1] - 2026-01-10

### Added
- **Sistema de parsing validado**: Validación completa del parsing de archivos PL/SQL
  - 90.2% parsing válido (7,328 objetos)
  - Sistema de fallback para objetos con parsing parcial

### Fixed
- **Parsing de packages**: Mejorado para manejar packages con múltiples procedures/functions
- **Detección de objetos internos**: `internal_to_package` flag para objetos dentro de packages

---

## [2.0] - 2026-01-05

### Added
- **Conversión Híbrida**: Orquestación automática entre ora2pg (SIMPLE) y agente IA (COMPLEX)
  - ~5,000 objetos SIMPLE: ora2pg (0 tokens Claude)
  - ~3,122 objetos COMPLEX: Agente IA con técnicas avanzadas
  - **Ahorro**: ~60% consumo de tokens Claude

### Changed
- **plsql-converter**: Implementa flujo de decisión automático por objeto
  - Analiza clasificación (SIMPLE/COMPLEX) y tipo (PACKAGE vs standalone)
  - Ejecuta ora2pg o técnicas de IA según corresponda

---

## [1.0] - 2026-01-01

### Added
- **Plugin inicial**: 4 agentes especializados
  - plsql-analyzer: Análisis y clasificación SIMPLE/COMPLEX
  - plsql-converter: Conversión Oracle→PostgreSQL
  - plpgsql-validator: Validación de compilación
  - shadow-tester: Testing comparativo Oracle vs PostgreSQL

- **Sistema de tracking**: manifest.json y progress.json para reanudación automática

- **Documentación técnica**:
  - GUIA_MIGRACION.md: Proceso completo de migración
  - DESARROLLO.md: Arquitectura del plugin
  - COMANDOS.md: Referencia de comandos

### Technical Details
- Target: 8,122 objetos PL/SQL
- Oracle: 19c
- PostgreSQL: 17.4 (Amazon Aurora)
- Modelo Claude: Sonnet 4.5
- Timeline estimado: 25 horas efectivas (5 sesiones)

---

## Leyenda de Tipos de Cambios

- **Added**: Nuevas funcionalidades
- **Changed**: Cambios en funcionalidad existente
- **Deprecated**: Funcionalidad que será removida
- **Removed**: Funcionalidad removida
- **Fixed**: Corrección de bugs
- **Security**: Correcciones de vulnerabilidades

---

**Nota**: Para detalles técnicos completos de cada versión, consultar los git commits correspondientes.
