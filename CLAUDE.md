# Configuración Claude Code - Plugin Migración Oracle → PostgreSQL

**Proyecto:** oracle-postgres-migration
**Tipo:** Plugin de Claude Code
**Versión:** 1.0.0
**Última Actualización:** 2026-01-10

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
│   ├── compilation-validator.md   ← Fase 3: Validación
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
phantomx-nexus/                     ← Tu proyecto con datos
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
├── compilation_results/            ← Resultados de validación
└── shadow_tests/                   ← Resultados de testing
```

### Cómo Usar el Plugin

```bash
# 1. Instalar el plugin desde marketplace (solo primera vez)
# Ir a Claude Code → Marketplace → Buscar "oracle-postgres-migration" → Install

# 2. Navegar al proyecto con datos
cd /home/ljham/Documentos/desarrollo/PythonProjects/phantomx-nexus

# 3. Iniciar Claude Code (el plugin se carga automáticamente)
claude

# Claude Code carga automáticamente los 4 agentes del plugin instalado
# Los agentes trabajan con archivos en el directorio actual (phantomx-nexus/)
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

### 3. compilation-validator (Fase 3 - Validación)
- **Propósito:** Validar compilación en PostgreSQL 17.4
- **Input:** migrated/{simple,complex}/*.sql
- **Output:** compilation_results/success/, compilation_results/errors/
- **Conexión:** Requiere PostgreSQL accesible (env vars PGHOST, PGDATABASE, etc.)
- **Uso:** `Task compilation-validator "Validar batch_001 objetos 1-10"`

### 4. shadow-tester (Fase 4 - Testing Comparativo)
- **Propósito:** Ejecutar código en Oracle y PostgreSQL, comparar resultados
- **Input:** compilation_results/success/*.log
- **Output:** shadow_tests/*.json (comparaciones)
- **Conexión:** Requiere Oracle + PostgreSQL accesibles
- **Uso:** `Task shadow-tester "Testear batch_001 objetos 1-5"`

---

## 📊 Flujo de Trabajo (4 Fases)

### FASE 1: Análisis y Clasificación (5 horas - 1 sesión)
- 20 agentes plsql-analyzer en paralelo
- Procesar 200 objetos por mensaje (20 × 10)
- 42 mensajes para 8,122 objetos
- Output: knowledge/ + classification/

### FASE 2A: Conversión Simple (30 min - LOCAL)
- Ejecutar ora2pg localmente (NO usa Claude)
- ~5,000 objetos SIMPLE
- Costo tokens: 0 ✅

### FASE 2B: Conversión Compleja (5 horas - 1 sesión)
- 20 agentes plsql-converter en paralelo
- ~3,122 objetos COMPLEX
- 16 mensajes
- Output: migrated/complex/

### FASE 3: Validación de Compilación (5 horas - 1 sesión)
- 20 agentes compilation-validator en paralelo
- Conectan a PostgreSQL y ejecutan scripts
- 42 mensajes
- Output: compilation_results/

### FASE 4: Shadow Testing (10 horas - 2 sesiones)
- 10 agentes shadow-tester en paralelo
- Conectan a Oracle + PostgreSQL
- 84 mensajes
- Output: shadow_tests/

**Timeline Total:** 25.5 horas efectivas, 184 mensajes, 5-6 sesiones

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
cd /home/ljham/Documentos/desarrollo/PythonProjects/phantomx-nexus

# 3. Verificar archivos fuente Oracle
ls sql/extracted/*.sql
# Debe mostrar: functions.sql, procedures.sql, packages_spec.sql, packages_body.sql, triggers.sql

# 4. Copiar script de preparación al proyecto (solo primera vez)
# Nota: El script está incluido en el plugin instalado
cp ~/.claude/plugins/oracle-postgres-migration/scripts/prepare_migration.py scripts/

# 5. Generar manifest, progress y estructura de directorios (solo primera vez)
# IMPORTANTE: Ejecutar DESDE tu proyecto, el script usa Path.cwd()
# El script crea automáticamente: knowledge/, migrated/, compilation_results/, shadow_tests/
python scripts/prepare_migration.py

# 6. Verificar que todo se creó correctamente
ls -la sql/extracted/manifest.json sql/extracted/progress.json
ls -la knowledge/ migrated/ compilation_results/ shadow_tests/

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
pwd  # Debe ser phantomx-nexus
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
   - Si progress.json no existe → Guiar al usuario a ejecutar `prepare_migration_v2.py`
   - Si processed_count = 0 → Sugerir iniciar Fase 1
   - Si processed_count > 0 → Mostrar progreso actual y preguntar si continuar

**Contexto clave a recordar:**
- Este es un PLUGIN instalado desde marketplace, no parte del proyecto del usuario
- Los datos están en el proyecto del usuario (ej: phantomx-nexus/), no en el plugin
- Los agentes trabajan con el CWD (directorio del proyecto), no con la ubicación del plugin
- Usar rutas relativas desde el directorio del proyecto cuando invoques agentes
- El usuario debe copiar los scripts (prepare_migration.py, update_progress.py) a su proyecto
- Documentación en español, código en inglés

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

---

**Última Actualización:** 2026-01-10
**Versión:** 1.0.0
**Estado:** Documentación consolidada, parsing validado (90.2% valid), listo para migración
**Próximo Paso:** Ver [README.md](README.md) → [GUIA_MIGRACION.md](docs/GUIA_MIGRACION.md) → Iniciar Fase 1