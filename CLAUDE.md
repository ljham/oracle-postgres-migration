# Configuración Claude Code - Plugin Migración Oracle → PostgreSQL

**Proyecto:** oracle-postgres-migration
**Tipo:** Plugin de Claude Code
**Versión:** 2.0.0
**Última Actualización:** 2026-01-31

---

## 🎯 ¿Qué es este Proyecto?

Este es un **plugin de Claude Code** que proporciona 4 agentes especializados para migrar 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora).

**El plugin se instala desde el marketplace de Claude Code y se usa en cualquier proyecto de migración Oracle → PostgreSQL.**

---

## 📖 Documentación Principal - LEER PRIMERO

### Inicio Rápido
1. **[README.md](README.md)** ← **EMPEZAR AQUÍ** - Índice principal con inicio rápido (5 minutos)
2. **[docs/GUIA_MIGRACION.md](docs/GUIA_MIGRACION.md)** - Proceso completo de migración paso a paso

### Documentación Técnica Completa

**Para Usuarios (Ejecutar Migración):**
- **[docs/GUIA_MIGRACION.md](docs/GUIA_MIGRACION.md)** - Proceso completo de migración (4 fases, timeline, sistema de progreso)
- **[docs/COMANDOS.md](docs/COMANDOS.md)** - Referencia de comandos de terminal y troubleshooting

**Para Desarrolladores (Mantener/Extender):**
- **[docs/DESARROLLO.md](docs/DESARROLLO.md)** - Arquitectura del plugin, sistema de parsing, decisiones técnicas

### Ejemplos Prácticos
- **[docs/examples/phase1_launch_example.md](docs/examples/phase1_launch_example.md)** - Ejemplo completo Fase 1

### ⚠️ IMPORTANTE: Política de Documentación Consolidada

**❌ NO CREAR MÁS ARCHIVOS .MD**

La documentación está **consolidada en 3 archivos base:**
1. **GUIA_MIGRACION.md** - Para usuarios (proceso, fases, comandos, troubleshooting)
2. **DESARROLLO.md** - Para desarrolladores (arquitectura, diseño, parsing)
3. **COMANDOS.md** - Referencia rápida de comandos de terminal

**Razón:** Evitar fragmentación y duplicación de información.

**Si necesitas agregar información nueva:**
- ✅ Integra en uno de los 3 archivos base según audiencia
- ✅ Actualiza el índice del README.md si es relevante
- ❌ NO crees archivos como: `ESTRATEGIA_HIBRIDA.md`, `FEATURE_X.md`, `GUIA_Y.md`

**Archivos especiales permitidos (únicos):**
- `archived/` - Documentos consolidados/obsoletos (con README.md explicativo)
- `docs/examples/` - Ejemplos prácticos específicos de cada fase

---

## 📝 Política de Creación de Archivos (Evitar Desorden)

**ACTUALIZADO:** 2026-02-02

### ⚠️ REGLA GENERAL: Solo crear archivos .md cuando aporten valor a largo plazo

**Problema identificado:** Se creaban demasiados archivos .md temporales de resúmenes, correcciones y análisis que solo agregaban desorden al proyecto.

### ❌ NO Crear Archivos .md Para:

- **Resúmenes de cambios o correcciones** → Mostrar en pantalla, usuario decide si guardar
- **Resultados de tests intermedios** → Mostrar en pantalla
- **Análisis temporales** → Mostrar en pantalla
- **Correcciones puntuales** → Mostrar en pantalla
- **Updates de versiones** → Usar CHANGELOG.md (centralizado)

**Excepciones:**
- Si el usuario solicita explícitamente: "crea un archivo con este resumen"
- Si es documentación técnica permanente (ver siguiente sección)

### ✅ SÍ Crear Archivos .md Para:

- **Documentación técnica permanente:**
  - GUIA_MIGRACION.md - Proceso de migración
  - DESARROLLO.md - Arquitectura del plugin
  - COMANDOS.md - Referencia de comandos
  - README.md - Índice principal

- **Referencias de decisiones arquitectónicas importantes:**
  - Cuando una decisión afecta diseño a largo plazo
  - Cuando requiere consulta frecuente por otros desarrolladores

- **Backups antes de modificaciones críticas:**
  - `agents/backups/agente.md.vX.X.X` - Siempre crear backup antes de editar agentes

- **Cuando el usuario lo solicita explícitamente:**
  - "Crea un documento con..."
  - "Guarda esto en un archivo..."

### 📊 Alternativas Recomendadas:

**Para cambios y updates:**
- **CHANGELOG.md** - Historial centralizado de todas las versiones
- **Git commits** - Mensajes descriptivos con detalles técnicos
- **Conversación de Claude** - El historial ya tiene toda la info

**Para análisis y resúmenes:**
- **Mostrar en pantalla** - Output directo en la conversación
- **Usuario decide** - Preguntar: "¿Quieres que guarde esto en un archivo?"

### 🗑️ Limpieza de Archivos Temporales:

**Proceso aplicado (2026-02-02):**
```bash
# Archivos temporales movidos a archived/temp-docs-2026-02-02/
- ACTUALIZACIONES_FRAMEWORK_v3.3.2_FINAL.md
- PATH_CORRECTION_v3.3.2.md
- TEST_VALIDATION_V3.1_RESULTS.md
- TEST_PLSQL_UNIT_RULE_UPDATE.md
- ULTRA_MINIMALISTA_RESULTS.md
- ANALISIS_INTEGRACION_FASE1_FASE2.md
- MEJORA_V3.2_INTEGRACION_FASE1_FASE2.md
- SOLUTION_C_IMPLEMENTED.md

Total: 8 archivos → archived/
```

**Resultado:** Directorio raíz más limpio y organizado.

### 💡 Workflow Recomendado para Claude:

1. **Al hacer cambios:**
   - Crear backup si modificas archivo crítico
   - Actualizar CHANGELOG.md con el cambio
   - Mostrar resumen en pantalla
   - **NO crear archivo .md de resumen automáticamente**

2. **Al finalizar:**
   - Preguntar: "¿Quieres que cree un documento con el resumen de cambios?"
   - Si usuario dice sí → crear archivo
   - Si usuario dice no → dejar solo en conversación

3. **Commits de git:**
   - Mensajes descriptivos que documenten el cambio
   - Ejemplo: `fix(plsql-converter): corregir paths sql/migrated/ → migrated/`

---

## 🚀 Instalación y Uso del Plugin

### Estructura del Plugin

```
oracle-postgres-migration/          ← Plugin instalado desde marketplace
├── README.md                       ← Índice principal con inicio rápido
├── CLAUDE.md                       ← Este archivo (contexto para Claude)
├── CONSOLIDACION_FINAL.md          ← Resumen de consolidación de docs
├── .claude-plugin/
│   └── plugin.json                 ← Manifest del plugin
├── agents/                         ← 4 agentes especializados
│   ├── plsql-analyzer.md          ← Fase 1: Análisis
│   ├── plsql-converter.md         ← Fase 2B: Conversión compleja
│   ├── plpgsql-validator.md   ← Fase 3: Validación
│   └── shadow-tester.md           ← Fase 4: Testing
├── docs/                           ← Documentación técnica
│   ├── GUIA_MIGRACION.md          ← Para usuarios (proceso completo)
│   ├── DESARROLLO.md              ← Para desarrolladores (arquitectura)
│   ├── COMANDOS.md                ← Referencia de comandos
│   └── examples/
├── scripts/                        ← Scripts de soporte
│   ├── prepare_migration.py
│   ├── update_progress.py
│   └── convert_simple_objects.sh
├── examples/                       ← Ejemplos de uso
└── archived/                       ← Documentos obsoletos
```

### Estructura de tu Proyecto

```
<nombre-proyecto>/                  ← Tu proyecto con datos
├── sql/extracted/                  ← Archivos fuente PL/SQL
│   ├── functions.sql
│   ├── procedures.sql
│   ├── packages_spec.sql
│   ├── packages_body.sql
│   ├── triggers.sql
│   ├── manifest.json              ← Generado por prepare_migration.py
│   └── progress.json              ← Generado por prepare_migration.py
├── knowledge/                      ← Generado por agentes
├── migrated/                       ← Código convertido
├── compilation/                    ← Resultados de validación
└── shadow_tests/                   ← Resultados de testing
```

### Cómo Usar el Plugin

```bash
# 1. Instalar el plugin desde marketplace (solo primera vez)
# Ir a Claude Code → Marketplace → Buscar "oracle-postgres-migration" → Install

# 2. Navegar al proyecto con datos
cd /ruta/a/<nombre-proyecto>

# 3. Iniciar Claude Code (el plugin se carga automáticamente)
claude

# Claude Code carga automáticamente los 4 agentes del plugin instalado
# Los agentes trabajan con archivos en el directorio actual (<nombre-proyecto>/)
# Los outputs se guardan en knowledge/, migrated/, etc.
```

**Ventajas del plugin desde marketplace:**
- ✅ Instalación con un clic desde marketplace
- ✅ Actualizaciones automáticas del plugin
- ✅ Disponible en todos tus proyectos de migración
- ✅ Plugin y proyecto separados (sin mezclar código)
- ✅ Reutilizable para múltiples proyectos Oracle → PostgreSQL

---

## 🤖 Los 4 Agentes Especializados

### 1. plsql-analyzer (Fase 1 - Análisis)
- **Propósito:** Análisis semántico profundo y clasificación SIMPLE/COMPLEX
- **Input:** sql/extracted/*.sql (8,122 objetos)
- **Output:** knowledge/json/, knowledge/markdown/, classification/
- **Batch:** 10 objetos por agente, 20 agentes en paralelo = 200 objetos/mensaje
- **Uso:** `Task plsql-analyzer "Analizar batch_001 objetos 1-10"`

### 2. plsql-converter (Fase 2B - Conversión Compleja)
- **Propósito:** Convertir objetos COMPLEX con estrategias arquitectónicas
- **Input:** classification/complex_objects.txt (~3,122 objetos)
- **Output:** migrated/complex/*.sql + conversion_log/*.md
- **Estrategias:** AUTONOMOUS_TRANSACTION, UTL_HTTP, UTL_FILE, DBMS_SQL, etc.
- **Uso:** `Task plsql-converter "Convertir batch_001 objetos complejos 1-10"`

### 3. plpgsql-validator (Fase 3 - Validación)
- **Propósito:** Validar compilación en PostgreSQL 17.4
- **Input:** migrated/{simple,complex}/*.sql
- **Output:** compilation/success/, compilation/errors/
- **Conexión:** Requiere PostgreSQL accesible (env vars PGHOST, PGDATABASE, etc.)
- **Uso:** `Task plpgsql-validator "Validar batch_001 objetos 1-10"`

### 4. shadow-tester (Fase 4 - Testing Comparativo)
- **Propósito:** Ejecutar código en Oracle y PostgreSQL, comparar resultados
- **Input:** compilation/success/*.log
- **Output:** shadow_tests/*.json (comparaciones)
- **Conexión:** Requiere Oracle + PostgreSQL accesibles
- **Uso:** `Task shadow-tester "Testear batch_001 objetos 1-5"`

---

## 🎯 Marco de Trabajo y Optimizaciones (IMPORTANTE)

**Versión del Framework:** 3.2.1 - Optimizado con Anthropic Best Practices
**Última Actualización:** 2026-02-03

### Principios de Diseño Establecidos

**TODA modificación futura a los agentes DEBE seguir estos principios:**

#### 1. **Prompt Engineering - Anthropic Best Practices**
- ✅ **XML Tags como estándar estructural** (recomendación oficial de Anthropic)
  - Uso de `<role>`, `<rules>`, `<workflow>`, `<classification>`, `<examples>`, etc.
  - Proporciona estructura semántica clara sin overhead de procesamiento
  - "Most Claude-y approach" según Anthropic documentation
- ✅ **Structured CoT (Chain of Thought)** para razonamiento paso a paso
- ✅ **ReAct Pattern** para decisiones y acciones
- ✅ **CAPR (Conversational Repair)** para feedback loops
- ✅ **Context7 Integration** para consultas de documentación en tiempo real

#### 2. **Política Anti-Prompt Bloat**
- ⚠️ **CRÍTICO:** Evitar prompts extensos que causen pérdida de memoria del modelo
- ✅ **Minimalismo enfocado:** Solo información ESENCIAL para la tarea
- ✅ **Eliminar verbosidad:** Sin documentación extensa dentro de prompts
- ✅ **Ejemplos concisos:** 3 ejemplos claros > 6 ejemplos extensos
- ✅ **Target:** Mantener agentes entre 500-700 líneas (máximo)
- ❌ **Prohibido:** Agregar secciones de reportes, tracking detallado, o ejemplos redundantes

**Razón:** Prompts extensos (>2,000 líneas) causan:
- Pérdida de foco del modelo (attention dilution)
- Procesamiento más lento
- Menor precisión en la ejecución de tareas

#### 3. **Idioma y Consistencia**
- ✅ **Español para todos los system prompts de agentes** (decisión de equipo)
- ✅ **Código en inglés** (nombres de variables, funciones, clases)
- ✅ **Términos técnicos sin traducir** (endpoint, hook, batch, feedback loop)
- ✅ **Documentación externa en español** (README, GUIA_MIGRACION, DESARROLLO)

**Razón:** Español mejora comprensión para el equipo, inglés mantiene estándares de código internacional.

#### 4. **Versionamiento y Backups Obligatorios**
- ✅ **SIEMPRE crear backup antes de modificar un agente**
  - Formato: `agents/backups/{agente}.md.v{X.Y}.{descripcion}.backup`
  - Ejemplo: `plpgsql-validator.md.v3.2.pre-path-fix.backup`
- ✅ **Actualizar CHANGELOG.md** con cada cambio significativo
- ✅ **Versión semántica:**
  - Major (X.0): Cambios arquitectónicos o de estructura
  - Minor (X.Y): Nuevas features o mejoras
  - Patch (X.Y.Z): Correcciones de bugs o ajustes menores

#### 5. **Herramientas Probadas en Migración Oracle→PostgreSQL**
- ✅ **ora2pg:** Conversión batch de objetos SIMPLE (estándar de industria)
- ✅ **Context7:** Consulta de docs PostgreSQL 17.4 en tiempo real
- ✅ **Kahn's Algorithm:** Compilación por niveles de dependencia (topological sort)
- ✅ **Feedback Loops:** Retry automático con plsql-converter para errores COMPLEX
- ✅ **Auto-corrección limitada:** Máximo 3 intentos para errores sintácticos simples

### Versiones Actuales de Agentes (Optimizadas)

| Agente | Versión | Líneas | Target | Características Clave |
|--------|---------|--------|--------|----------------------|
| **plsql-analyzer** | v4.25 | 876 | 700 ⚠️ | Skip inteligente objetos existentes + captura completa types + variables privadas |
| **plsql-converter** | v4.3.1 | 502 | 700 ✅ | Español + 12 XML tags, estrategias híbridas, feedback loop |
| **plpgsql-validator** | v3.2.1 | 654 | 700 ✅ | Compilación por niveles, auto-corrección (máx 3), feedback loop |
| **shadow-tester** | v1.0.1 | ~400 | 700 ✅ | Comparación Oracle vs PostgreSQL |

**Excepción Documentada:**
- **plsql-analyzer v4.25:** 876 líneas (+25% sobre target de 700)
  - **Justificación:** Funcionalidad crítica para migración efectiva
    - Skip automático de objetos ya analizados (ahorro 20-30% tokens)
    - Captura TODOS los types públicos del package (no solo 1)
    - Extracción de variables/constantes PRIVADAS del BODY
    - Dos schemas adaptativos (PACKAGE_BODY vs PROCEDURE/FUNCTION)
    - Cinco ejemplos necesarios (casos de uso distintos)
  - **Optimización histórica:** 1214 → 977 (-19.5%) → 1037 (v4.21) → 1024 (v4.23 -metrics) → 878 (v4.24 -146) → 876 (v4.25 fix)
  - **Aprobación:** 2026-02-16/17 (cumple con espíritu de anti-prompt bloat, funcionalidad esencial + ahorro de tokens)

### Técnicas Aplicadas

**Optimizaciones implementadas (2026-01 a 2026-02):**
1. **v3.0:** Agregado de XML tags (estructura semántica)
2. **v3.1:** Reducción drástica 68% (2,064 → 577 líneas en plpgsql-validator)
3. **v3.2:** Integración de compilación por niveles (topological sort)
4. **v3.2.1:** Corrección de paths (compilation_results → compilation)
5. **v4.3:** Español + XML tags en plsql-converter
6. **v4.18:** plsql-analyzer - Captura completa de types + variables privadas
7. **v4.18.1:** plsql-analyzer - Optimización conservadora (1214 → 977, -19.5%) sin pérdida de conocimiento
8. **v4.22:** plsql-analyzer - Eliminación de package.json consolidado (redundante con Schema A)
9. **v4.23:** plsql-analyzer - Eliminación de campo metrics de Schema B (12 → 11 campos)
10. **v4.24:** plsql-analyzer - Limpieza anti-prompt-bloat: 5 redundancias + 11 version tags eliminados (878 líneas)
11. **v4.25:** plsql-analyzer - Fix: package.json agregado a lista de archivos prohibidos (post-testing)

### Directrices para Futuras Modificaciones

**ANTES de modificar cualquier agente:**
1. ✅ Crear backup con versionamiento claro
2. ✅ Leer CHANGELOG.md para entender historial
3. ✅ Verificar que el cambio no viola política anti-prompt bloat
4. ✅ Mantener XML tags como estructura (no eliminar)
5. ✅ Mantener idioma español en prompts
6. ✅ Actualizar CHANGELOG.md con la modificación
7. ✅ Validar que el cambio sigue Anthropic best practices

**RECHAZAR cambios que:**
- ❌ Agreguen >100 líneas sin justificación técnica clara
- ❌ Introduzcan verbosidad innecesaria (ejemplos extensos, documentación inline)
- ❌ Eliminen XML tags (estructura semántica crítica)
- ❌ Cambien idioma a inglés sin consenso de equipo
- ❌ No incluyan backup ni actualización de CHANGELOG

### Referencias de Documentación

**Para optimizaciones futuras consultar:**
- `CHANGELOG.md` - Historial completo de versiones y cambios
- `agents/backups/` - Todas las versiones anteriores de agentes
- `docs/DESARROLLO.md` - Arquitectura técnica y decisiones de diseño
- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering) - Best practices oficiales

---

## 📊 Flujo de Trabajo (4 Fases)

### FASE 1: Análisis y Clasificación (5 horas - 1 sesión)
- 20 agentes plsql-analyzer en paralelo
- Procesar 200 objetos por mensaje (20 × 10)
- 42 mensajes para 8,122 objetos
- Output: knowledge/ + classification/

### FASE 2: Conversión Híbrida (5 horas - 1 sesión) ⚡ NUEVO
- **Orquestación automática:** El agente plsql-converter decide la mejor herramienta por objeto
- **⚡ ora2pg:** ~5,000 objetos SIMPLE standalone (0 tokens)
- **🤖 Agente IA:** ~3,122 objetos COMPLEX + packages (~20 mensajes)
- **Fallback automático:** Si ora2pg falla → Agente IA toma el control
- **Ahorro:** ~60% en consumo de tokens Claude
- Output: migrated/simple/ + migrated/complex/

### FASE 3: Validación de Compilación (5 horas - 1 sesión)
- 20 agentes plpgsql-validator en paralelo
- Conectan a PostgreSQL y ejecutan scripts
- 42 mensajes
- Output: compilation/

### FASE 4: Shadow Testing (10 horas - 2 sesiones)
- 10 agentes shadow-tester en paralelo
- Conectan a Oracle + PostgreSQL
- 84 mensajes
- Output: shadow_tests/

**Timeline Total:** 25 horas efectivas, ~188 mensajes, 5 sesiones
**Ahorro:** ~60% tokens en FASE 2 gracias a estrategia híbrida ora2pg + Agente IA

---

## 🔧 Sistema de Tracking y Reanudación

**Problema Resuelto:** ¿Cómo continuar después de límites de sesión (45-60 mensajes cada 5 horas)?

**Solución:**
1. **manifest.json** - Índice de todos los 8,122 objetos con posiciones exactas
2. **progress.json** - Estado actual del procesamiento
3. **Detección automática** - Scripts detectan outputs y actualizan progreso

**Beneficios:**
- ✅ Reanudación automática desde último batch
- ✅ Tolerante a cierres de sesión
- ✅ Sin reprocesar objetos completados
- ✅ Progreso visible en todo momento

Ver detalles: **[docs/GUIA_MIGRACION.md](docs/GUIA_MIGRACION.md)** - Sección "Sistema de Progreso y Reanudación"

---

## 🎯 Capacidades Confirmadas (Experimentación 2025-01-05)

**Test 1:** 3 sub-agentes en paralelo - ✅ EXITOSO
**Test 2:** 10 sub-agentes en paralelo - ✅ EXITOSO (172,383 líneas procesadas)
**Test 3:** 20 sub-agentes en paralelo - ✅ EXITOSO

**Límites Claude Code Pro:**
- ~45-60 mensajes cada 5 horas
- Contexto: 200K tokens por mensaje
- Sub-agentes en paralelo: 20+ confirmado
- Modelo: Claude Sonnet 4.5 (suficiente para análisis de código)

---

## 📝 Convenciones del Proyecto

- **Documentación:** Español (README, docs/, CLAUDE.md)
- **Código:** Inglés (nombres de variables, funciones, clases)
- **Términos técnicos:** Sin traducir (endpoint, hook, middleware, batch, etc.)
- **System prompts de agentes:** Español (para mejor comprensión)

---

## ⚙️ Preparación Antes de Usar

### Pre-requisitos en tu proyecto

```bash
# 1. Instalar el plugin (solo primera vez)
# Claude Code → Marketplace → "oracle-postgres-migration" → Install

# 2. Navegar al proyecto con datos
cd /ruta/a/<nombre-proyecto>

# 3. Verificar archivos fuente Oracle
ls sql/extracted/*.sql
# Debe mostrar: functions.sql, procedures.sql, packages_spec.sql, packages_body.sql, triggers.sql

# 4. Copiar script de preparación al proyecto (solo primera vez)
# Nota: El script está incluido en el plugin instalado
cp ~/.claude/plugins/oracle-postgres-migration/scripts/prepare_migration.py scripts/

# 5. Generar manifest, progress y estructura de directorios (solo primera vez)
# IMPORTANTE: Ejecutar DESDE tu proyecto, el script usa Path.cwd()
# El script crea automáticamente: knowledge/, migrated/, compilation/, shadow_tests/
python scripts/prepare_migration.py

# 6. Verificar que todo se creó correctamente
ls -la sql/extracted/manifest.json sql/extracted/progress.json
ls -la knowledge/ migrated/ compilation/ shadow_tests/

# 7. Iniciar Claude Code (el plugin se carga automáticamente)
claude
```

---

## 🛠️ Herramientas Requeridas

### Incluido en Plugin (Gratis)
- Sub-agentes Claude Code (nativos de Claude Code Pro)
- Scripts Python (manifest, progress tracking)
- Scripts Bash (ora2pg automation)

### Tú Provees
- **ora2pg** - Para conversión de objetos SIMPLE (Fase 2A)
- **PostgreSQL 17.4+ con pgvector** - Base de datos destino
- **sentence-transformers** (opcional) - Para embeddings locales

### AWS (Ya Configurado)
- Aurora PostgreSQL 17.4
- S3 (para UTL_FILE)
- Lambda (para UTL_HTTP - pendiente crear)

---

## 🆘 Resolución de Problemas Rápida

### Plugin no carga
```bash
# Verificar instalación del plugin
claude plugins list | grep oracle-postgres-migration

# Reinstalar si es necesario
# Claude Code → Marketplace → "oracle-postgres-migration" → Reinstall
```

### Agentes no encuentran archivos
```bash
pwd  # Debe ser <nombre-proyecto>
ls sql/extracted/*.sql
```

### Progress no actualiza
```bash
python scripts/update_progress.py --check
```

Ver guía completa: **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**

---

## 📈 Criterios de Éxito

- ✅ 100% objetos analizados (Fase 1)
- ✅ 100% objetos convertidos (Fase 2A + 2B)
- ✅ >95% compilación exitosa (Fase 3)
- ✅ >95% resultados idénticos Oracle vs PostgreSQL (Fase 4)

---

## 📚 Archivos Archivados

**[archived/](archived/)** - Documentos consolidados y archivos obsoletos:

**Scripts Obsoletos:**
- `scripts/prepare_migration_v3_improved.py` - Demo incompleta (usar v2.1 en su lugar)
- `scripts/test_parsing_v2.py` - Test obsoleto (usar validate_parsing.py)

**Documentación Consolidada (2026-01-10):**
- `docs/ARQUITECTURA.md` → Consolidado en `DESARROLLO.md`
- `docs/ESTRATEGIA.md` → Consolidado en `GUIA_MIGRACION.md`
- `docs/OBJETOS_CONTEXTO.md` → Split entre `GUIA_MIGRACION.md` y `DESARROLLO.md`
- `docs/TRACKING_SYSTEM.md` → Consolidado en `GUIA_MIGRACION.md`
- `docs/PARSING_ANALYSIS.md` → Consolidado en `DESARROLLO.md`
- `docs/VALIDATION_REPORT.md` → Consolidado en `DESARROLLO.md`
- `docs/COMANDOS_GUIA.md` → Obsoleto (comandos slash no implementados)

Ver `archived/README.md` para detalles completos.

---

## 🔗 Enlaces Importantes

### Documentación Oficial
- [Claude Code Docs](https://code.claude.com/docs/en/)
- [PostgreSQL 17 Docs](https://www.postgresql.org/docs/17/)
- [ora2pg Docs](https://ora2pg.darold.net/)
- [pgvector Extension](https://github.com/pgvector/pgvector)

### Conocimiento Preservado (Sessions Discovery)
- `.claude/sessions/oracle-postgres-migration/` - Discovery del proyecto original
  - `00_index.md` - Resumen ejecutivo
  - `01_problem_statement.md` - Problema, objetivos, scope
  - `02_user_stories.md` - Épicas y user stories
  - `04_decisions.md` - Decisiones técnicas críticas

---

## 💡 Instrucciones para Claude

**Cuando una nueva sesión de Claude Code se inicie con este plugin:**

1. **Leer primero:** Este archivo (CLAUDE.md) para entender el contexto completo
2. **Índice principal:** Ver [README.md](README.md) para navegación completa
3. **Entender el proceso:** Ver [docs/GUIA_MIGRACION.md](docs/GUIA_MIGRACION.md) para las 4 fases detalladas
4. **Arquitectura técnica:** Ver [docs/DESARROLLO.md](docs/DESARROLLO.md) para decisiones de diseño
5. **Verificar progreso:** Leer `sql/extracted/progress.json` si existe en el directorio actual
6. **Determinar siguiente acción:**
   - Si progress.json no existe → Guiar al usuario a ejecutar `prepare_migration.py`
   - Si processed_count = 0 → Sugerir iniciar Fase 1
   - Si processed_count > 0 → Mostrar progreso actual y preguntar si continuar

**Contexto clave a recordar:**
- Este es un PLUGIN instalado desde marketplace, no parte del proyecto del usuario
- Los datos están en el proyecto del usuario (ej: <nombre-proyecto>/), no en el plugin
- Los agentes trabajan con el CWD (directorio del proyecto), no con la ubicación del plugin
- Usar rutas relativas desde el directorio del proyecto cuando invoques agentes
- El usuario debe copiar los scripts (prepare_migration.py, update_progress.py) a su proyecto
- Documentación en español, código en inglés

**⚠️ CRÍTICO - Marco de Trabajo de Optimización:**
- **LEER OBLIGATORIO:** Sección "🎯 Marco de Trabajo y Optimizaciones" en este archivo
- **Versiones actuales:** plsql-analyzer v4.25, plsql-converter v4.3.1, plpgsql-validator v3.2.1
- **ANTES de modificar agentes:** Crear backup + seguir principios establecidos
- **Política anti-prompt bloat:** Mantener agentes entre 500-700 líneas máximo
- **XML tags obligatorios:** No eliminar estructura semántica
- **Idioma español:** Todos los system prompts en español (decisión de equipo)
- **Actualizar CHANGELOG.md:** Con cada modificación significativa
- **Consultar:** `CHANGELOG.md` para historial completo de optimizaciones

**Estructura de Documentación (Consolidada 2026-01-10):**
- **Organizada por AUDIENCIA**, no por tema
- **3 documentos principales:** GUIA_MIGRACION.md (usuarios), DESARROLLO.md (desarrolladores), COMANDOS.md (referencia)
- **Aplicadas mejores prácticas:** Divio Documentation System, Single Source of Truth, máximo 5 documentos
- **Sin duplicación:** Cada información existe en UN solo lugar
- **Documentos antiguos:** Todos consolidados y movidos a `archived/docs/` (ver `archived/README.md`)

**Cuando el usuario pregunte por información:**
1. **Proceso de migración/fases** → `GUIA_MIGRACION.md`
2. **Arquitectura/diseño técnico** → `DESARROLLO.md`
3. **Comandos/troubleshooting** → `COMANDOS.md`
4. **Parsing/validación** → `DESARROLLO.md` (sección Sistema de Parsing)
5. **Sistema de progreso** → `GUIA_MIGRACION.md` (sección Sistema de Progreso y Reanudación)
6. **Optimizaciones/marco de trabajo** → Sección "🎯 Marco de Trabajo y Optimizaciones" en este archivo
7. **Historial de cambios** → `CHANGELOG.md`

---

**Última Actualización:** 2026-02-03
**Versión Framework:** 3.2.1 (Agentes optimizados con Anthropic best practices)
**Estado:**
- ✅ Agentes optimizados (v3.2.1, v4.3.1, v4.6)
- ✅ Paths corregidos (compilation/ unificado)
- ✅ Marco de trabajo establecido
- ✅ Documentación consolidada
- ✅ Listo para migración
**Próximo Paso:** Ver [README.md](README.md) → [GUIA_MIGRACION.md](docs/GUIA_MIGRACION.md) → Iniciar Fase 1