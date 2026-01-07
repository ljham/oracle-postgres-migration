# Plugin de Migración Oracle → PostgreSQL

**Versión:** 1.0.0
**Compatibilidad:** Claude Code CLI/Web Pro
**Objetivo:** Migrar 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora)

---

## 🎯 Resumen

Este plugin proporciona **4 agentes especializados** para migrar código PL/SQL de Oracle a PL/pgSQL de PostgreSQL mediante un flujo de trabajo estructurado de 4 fases con seguimiento automático de progreso y capacidad de reanudación.

**Características Clave:**
- 🎯 **Procesamiento por lotes:** 10-20 objetos por instancia de agente
- 🔄 **Ejecución paralela:** Hasta 20 agentes concurrentes
- 📊 **Outputs estructurados:** Extracción de conocimiento en JSON + Markdown
- 🧠 **Preservación de conocimiento:** Reglas de negocio indexadas en pgvector
- 🔁 **Seguimiento de progreso:** Reanudación automática después de límites de sesión
- ✅ **Alta tasa de éxito:** >95% objetivo para compilación y testing

---

## 🚀 Inicio Rápido (5 minutos)

### 1. Instalar Plugin desde Marketplace

```bash
# Opción 1: Desde Claude Code CLI
claude plugins install oracle-postgres-migration

# Opción 2: Desde Claude Code Web/Desktop
# Marketplace → Buscar "oracle-postgres-migration" → Install
```

### 2. Preparar tu Proyecto de Migración

```bash
# Navegar a tu proyecto con objetos PL/SQL
cd /path/to/tu-proyecto

# Copiar scripts del plugin a tu proyecto
mkdir -p scripts
cp ~/.claude/plugins/oracle-postgres-migration/scripts/prepare_migration.py scripts/
cp ~/.claude/plugins/oracle-postgres-migration/scripts/update_progress.py scripts/
cp ~/.claude/plugins/oracle-postgres-migration/scripts/convert_simple_objects.sh scripts/

# Generar archivos manifest y progress tracking
python scripts/prepare_migration.py
```

Esto crea:
- `sql/extracted/manifest.json` - Índice de todos los objetos PL/SQL
- `sql/extracted/progress.json` - Seguimiento de progreso
- Directorios: `knowledge/`, `migrated/`, `compilation_results/`, `shadow_tests/`

### 3. Iniciar Claude Code y Lanzar Fase 1

```bash
# Iniciar Claude Code (el plugin se carga automáticamente)
claude
```

En Claude Code, ejecuta:

```
Quiero iniciar la FASE 1 de la migración Oracle a PostgreSQL.
Por favor lanza 20 agentes plsql-analyzer en paralelo para procesar batch_001 (objetos 1-200).
Lee el manifest desde sql/extracted/manifest.json para saber qué objetos procesar.
```

### 4. Continuar Leyendo

- **[QUICKSTART.md](QUICKSTART.md)** - Guía detallada paso a paso
- **[docs/ESTRATEGIA.md](docs/ESTRATEGIA.md)** - Estrategia completa de migración
- **[CLAUDE.md](CLAUDE.md)** - Contexto completo del plugin para Claude

---

## 📚 Documentación

### Primeros Pasos
- **[QUICKSTART.md](QUICKSTART.md)** - Guía de inicio rápido
- **[examples/phase1_launch_example.md](examples/phase1_launch_example.md)** - Ejemplo completo Fase 1

### Documentación Técnica
- **[docs/ESTRATEGIA.md](docs/ESTRATEGIA.md)** - Estrategia completa (4 fases, timeline, capacidad)
- **[docs/TRACKING_SYSTEM.md](docs/TRACKING_SYSTEM.md)** - Sistema de seguimiento y reanudación
- **[docs/ARQUITECTURA.md](docs/ARQUITECTURA.md)** - Arquitectura del plugin y decisiones de diseño
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Problemas comunes y soluciones

---

## 🤖 Agentes Especializados

### 1. plsql-analyzer (Fase 1)
**Propósito:** Análisis semántico y clasificación
**Input:** `sql/extracted/*.sql` (8,122 objetos)
**Output:**
- `knowledge/json/` - Conocimiento estructurado para pgvector
- `knowledge/markdown/` - Análisis legible para humanos
- `classification/simple_objects.txt` - Objetos para ora2pg (~5,000)
- `classification/complex_objects.txt` - Objetos para conversión IA (~3,122)

**Características:**
- Comprensión semántica profunda (no solo parsing sintáctico)
- Extracción de reglas de negocio
- Detección de features específicas de Oracle
- Clasificación razonada SIMPLE/COMPLEX

**Uso:** `Task plsql-analyzer "Analizar batch_001 objetos 1-10"`

---

### 2. plsql-converter (Fase 2B)
**Propósito:** Convertir objetos complejos que requieren estrategias arquitectónicas
**Input:** `classification/complex_objects.txt`
**Output:**
- `migrated/complex/*.sql` - Código convertido
- `conversion_log/*.md` - Documentación de cambios

**Características:**
- **AUTONOMOUS_TRANSACTION** → dblink/rediseño/Lambda
- **UTL_HTTP** → AWS Lambda + funciones wrapper
- **UTL_FILE/DIRECTORY** → aws_s3 export a S3
- **DBMS_SQL** → EXECUTE + format()
- **Variables de paquete** → Variables de sesión (set_config/current_setting)
- **TABLE OF INDEX BY** → Arrays nativos

**Uso:** `Task plsql-converter "Convertir batch_001 objetos complejos 1-10"`

---

### 3. compilation-validator (Fase 3)
**Propósito:** Validar compilación en PostgreSQL
**Input:** `migrated/{simple,complex}/*.sql`
**Output:**
- `compilation_results/success/*.log` - Compilados exitosamente
- `compilation_results/errors/*.error` - Errores + sugerencias de fix
- `compilation_results/global_report.md` - Estadísticas y patrones

**Características:**
- Ejecuta scripts en PostgreSQL 17.4
- Detecta errores de compilación
- Sugiere fixes automáticos
- Clasifica errores (CRITICAL/HIGH/MEDIUM/LOW)
- Identifica patrones de error

**Uso:** `Task compilation-validator "Validar batch_001 objetos 1-10"`

---

### 4. shadow-tester (Fase 4)
**Propósito:** Validación funcional (Oracle vs PostgreSQL)
**Input:** `compilation_results/success/*.log`
**Output:**
- `shadow_tests/[objeto].json` - Comparación de resultados
- `shadow_tests/discrepancies.txt` - Diferencias encontradas

**Características:**
- Ejecuta mismo código en Oracle y PostgreSQL
- Compara outputs (datos, estructura, performance)
- Identifica discrepancias funcionales
- Objetivo >95% resultados idénticos

**Uso:** `Task shadow-tester "Testear batch_001 objetos 1-5"`

---

## ⚡ Comandos Slash (Simplificados)

El plugin incluye **6 comandos slash** que facilitan la invocación de los agentes:

### Comandos de Utilidad

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/init` | Inicializa proyecto (manifest, progress, directorios) | `/init` |
| `/status` | Muestra progreso de todas las fases | `/status` |

### Comandos de Fases

| Comando | Fase | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `/analyze` | 1 | Analiza y clasifica objetos PL/SQL | `/analyze next` |
| `/convert` | 2B | Convierte objetos complejos | `/convert next` |
| `/validate` | 3 | Valida compilación en PostgreSQL | `/validate next` |
| `/test` | 4 | Shadow testing Oracle vs PostgreSQL | `/test next 50` |

**Ejemplo de flujo completo:**

```bash
# Inicializar
/init

# Verificar estado
/status

# Fase 1: Análisis
/analyze next          # Procesa 200 objetos
/analyze next          # Repetir hasta completar

# Fase 2A: Conversión simple (LOCAL)
bash scripts/convert_simple_objects.sh

# Fase 2B: Conversión compleja
/convert next          # Procesa 200 objetos complejos
/convert next          # Repetir hasta completar

# Fase 3: Validación
/validate next         # Valida 200 objetos
/validate next         # Repetir hasta completar

# Fase 4: Testing
/test next            # Testea 50 objetos
/test next            # Repetir hasta completar

# Verificar éxito
/status               # Debe mostrar 100% en todas las fases
```

**Beneficios de los comandos:**
- ✅ **Sintaxis simple:** `/analyze` vs `Task plsql-analyzer "..."`
- ✅ **Argumentos con defaults:** No necesitas recordar parámetros
- ✅ **Validaciones automáticas:** Verifica pre-requisitos antes de ejecutar
- ✅ **Progreso automático:** Actualiza `progress.json` sin intervención
- ✅ **Modo "next":** Detecta automáticamente el siguiente batch pendiente

Ver detalles: **[commands/README.md](commands/README.md)**

---

## 📦 Cómo Funciona la Instalación

Este plugin se instala globalmente desde el marketplace de Claude Code:

```bash
# Ubicación del plugin instalado:
~/.claude/plugins/oracle-postgres-migration/
├── .claude-plugin/
├── agents/                 # 4 agentes especializados
├── scripts/                # Scripts de soporte
└── docs/                   # Documentación

# Estructura de tu proyecto:
tu-proyecto/
├── sql/extracted/          # Tus archivos fuente PL/SQL
├── scripts/                # Scripts copiados del plugin
│   ├── prepare_migration.py
│   ├── update_progress.py
│   └── convert_simple_objects.sh
├── knowledge/              # Generado por agentes
├── migrated/               # Generado por agentes
└── ...
```

**Cuando ejecutas `claude` en tu proyecto:**
1. Claude Code carga automáticamente el plugin desde `~/.claude/plugins/`
2. Los agentes trabajan con archivos en tu proyecto (directorio actual)
3. Los outputs se guardan en `knowledge/`, `migrated/`, etc. de tu proyecto
4. Tu proyecto y el plugin permanecen separados ✅
5. El plugin está disponible para todos tus proyectos de migración

---

## 🔧 Requisitos de Configuración del Proyecto

Antes de iniciar, asegúrate que tu proyecto tenga:

```
tu-proyecto/
├── sql/extracted/               # Archivos fuente Oracle (REQUERIDO)
│   ├── functions.sql
│   ├── procedures.sql
│   ├── packages_spec.sql
│   ├── packages_body.sql
│   └── triggers.sql
├── scripts/                     # Scripts copiados del plugin
│   ├── prepare_migration.py
│   ├── update_progress.py
│   └── convert_simple_objects.sh
├── sql/extracted/manifest.json  # Generado por prepare_migration.py
├── sql/extracted/progress.json  # Generado por prepare_migration.py
├── knowledge/                   # Creado por prepare_migration.py
│   ├── json/
│   ├── markdown/
│   └── classification/
├── migrated/                    # Creado por prepare_migration.py
│   ├── simple/
│   └── complex/
├── compilation_results/         # Creado por prepare_migration.py
│   ├── success/
│   └── errors/
└── shadow_tests/                # Creado por prepare_migration.py
```

Ejecuta `python scripts/prepare_migration.py` para auto-crear esta estructura.

---

## 📊 Timeline de Migración

| Fase | Descripción | Duración | Mensajes |
|------|-------------|----------|----------|
| **Fase 1** | Análisis y Clasificación | 5 horas | 42 |
| **Fase 2A** | Conversión simple (ora2pg) | 30 min | 0 |
| **Fase 2B** | Conversión compleja | 5 horas | 16 |
| **Fase 3** | Validación de compilación | 5 horas | 42 |
| **Fase 4** | Shadow testing | 10 horas | 84 |
| **TOTAL** | **Migración completa** | **25.5 horas** | **184** |

**Planificación de sesiones:** 5-6 sesiones de 5 horas cada una (Límites Claude Code Pro: ~45-60 mensajes por ventana de 5 horas)

---

## 🛠️ Herramientas y Tecnologías

### Incluido en el Plugin
- **Sub-agentes Claude Code** - Nativos de Claude Code Pro (sin costo de API)
- **Scripts Python** - Generación de manifest, seguimiento de progreso
- **Scripts Bash** - Automatización ora2pg (Fase 2A)

### Requerido (Tú Provees)
- **ora2pg** - Conversión automática de objetos SIMPLE
- **PostgreSQL 17.4 + pgvector** - Base de datos destino
- **sentence-transformers** - Generación local de embeddings (opcional, para knowledge base)

### Infraestructura AWS (Opcional)
- **Aurora PostgreSQL 17.4** - Base de datos destino administrada
- **S3** - Almacenamiento de archivos (reemplaza objetos DIRECTORY)
- **Lambda** - Cliente HTTP (reemplaza UTL_HTTP)

---

## 🎓 Ejemplos de Uso

### Ejemplo 1: Instalación y Primera Ejecución
```bash
# 1. Instalar plugin
claude plugins install oracle-postgres-migration

# 2. Ir a tu proyecto
cd /path/to/tu-proyecto

# 3. Copiar scripts
cp ~/.claude/plugins/oracle-postgres-migration/scripts/*.py scripts/
cp ~/.claude/plugins/oracle-postgres-migration/scripts/*.sh scripts/

# 4. Preparar migración
python scripts/prepare_migration.py

# 5. Iniciar Claude (plugin se carga automáticamente)
claude

# En Claude Code:
> Iniciar migración FASE 1. Lanzar 20 agentes plsql-analyzer para batch_001.
```

### Ejemplo 2: Reanudar Después del Límite de Sesión
```bash
# 1. Verificar progreso
python scripts/update_progress.py --check

# 2. Iniciar Claude
claude

# En Claude Code:
> Reanudar migración FASE 1. Revisar progress.json y continuar desde el último batch.
```

### Ejemplo 3: Ejecutar Fase 2A Localmente (Sin Claude)
```bash
# Después de completar Fase 1
bash scripts/convert_simple_objects.sh

# Output: migrated/simple/*.sql (~5,000 objetos)
```

---

## 🆘 Resolución de Problemas

### ¿Plugin no carga?
```bash
# Verificar que el plugin está instalado
claude plugins list | grep oracle-postgres-migration

# Reinstalar si es necesario
claude plugins install oracle-postgres-migration --force
```

### ¿Agentes no encuentran archivos fuente?
```bash
# Verificar directorio actual
pwd  # Debe estar en tu proyecto

# Verificar que archivos fuente existen
ls sql/extracted/*.sql
```

### ¿Seguimiento de progreso no funciona?
```bash
# Regenerar manifest
python scripts/prepare_migration.py --force
```

Ver **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** para guía completa de resolución de problemas.

---

## 📈 Criterios de Éxito

- ✅ **100% objetos analizados** (Fase 1)
- ✅ **100% objetos convertidos** (Fase 2A + 2B)
- ✅ **>95% éxito de compilación** (Fase 3)
- ✅ **>95% resultados idénticos** (Fase 4 Oracle vs PostgreSQL)

---

## 📝 Licencia

Herramienta interna para proyecto de migración phantomx-nexus.

---

## 🔗 Recursos Adicionales

- [Documentación Claude Code](https://code.claude.com/docs/en/)
- [Documentación ora2pg](https://ora2pg.darold.net/)
- [Documentación PostgreSQL 17](https://www.postgresql.org/docs/17/)
- [Extensión pgvector](https://github.com/pgvector/pgvector)

---

**Última Actualización:** 2025-01-06
**Versión del Plugin:** 1.0.0
**Próximos Pasos:** Ver [QUICKSTART.md](QUICKSTART.md) para comenzar Fase 1
