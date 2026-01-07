# Arquitectura del Plugin - Migración Oracle a PostgreSQL

**Versión:** 1.0.0
**Última Actualización:** 2025-01-06

---

## 🎯 Filosofía de Diseño

Este plugin sigue una arquitectura de **separación de responsabilidades** donde:

1. **Código del plugin** (oracle-postgres-migration/) - Instalado globalmente desde marketplace, portable, reutilizable, versionado
2. **Datos del proyecto** (phantomx-nexus/) - Archivos fuente, outputs, resultados
3. **Runtime de Claude Code** - Carga plugin automáticamente desde marketplace, opera en directorio del proyecto

**Principio Clave:** El plugin debe funcionar con CUALQUIER proyecto de migración Oracle → PostgreSQL, no solo phantomx-nexus.

---

## 🏗️ Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│ Usuario instala plugin e inicia Claude Code                 │
│ $ claude plugins install oracle-postgres-migration          │
│ $ cd phantomx-nexus                                         │
│ $ claude                                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Runtime de Claude Code                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Directorio Actual (CWD): phantomx-nexus/                │ │
│ │ Plugin Instalado: ~/.claude/plugins/oracle-postgres-    │ │
│ │                   migration/                             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────┐  ┌───────────────────────────────────┐ │
│ │ Cargar Plugin    │  │ Cargar 4 Agentes desde:          │ │
│ │ Automáticamente  │─▶│ .claude-plugin/plugin.json       │ │
│ │                  │  │ agents/*.md (system prompts)     │ │
│ └──────────────────┘  └───────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Contexto de Ejecución de Agentes                            │
│                                                             │
│ ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│ │ plsql-analyzer  │  │ plsql-converter │  │ compilation- │  │
│ │                 │  │                 │  │ validator    │  │
│ │ Lee:            │  │ Lee:            │  │ Lee:         │  │
│ │ sql/extracted/  │  │ classification/ │  │ migrated/    │  │
│ │ manifest.json   │  │ sql/extracted/  │  │ Escribe:     │  │
│ │ Escribe:        │  │ Escribe:        │  │ compilation_ │  │
│ │ knowledge/      │  │ migrated/       │  │ results/     │  │
│ └─────────────────┘  └─────────────────┘  └──────────────┘  │
│                                                             │
│ ┌─────────────────┐                                         │
│ │ shadow-tester   │                                         │
│ │                 │                                         │
│ │ Lee:            │                                         │
│ │ migrated/       │                                         │
│ │ Conecta:        │                                         │
│ │ Oracle DB       │                                         │
│ │ PostgreSQL DB   │                                         │
│ │ Escribe:        │                                         │
│ │ shadow_tests/   │                                         │
│ └─────────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Directorio del Proyecto: phantomx-nexus/                    │
│                                                             │
│ sql/extracted/       ← Archivos fuente (Oracle)             │
│ knowledge/           ← Conocimiento generado (agentes)      │
│ migrated/            ← Código convertido (agentes)          │
│ compilation_results/ ← Resultados validación (agentes)      │
│ shadow_tests/        ← Resultados tests (agentes)           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Desglose de Componentes

### 1. Manifest del Plugin (.claude-plugin/plugin.json)

```json
{
  "name": "oracle-postgres-migration",
  "version": "1.0.0",
  "description": "Agentes especializados para migración Oracle → PostgreSQL",
  "author": "Migration Team",
  "agents": [
    "agents/plsql-analyzer.md",
    "agents/plsql-converter.md",
    "agents/compilation-validator.md",
    "agents/shadow-tester.md"
  ]
}
```

**Propósito:**
- Registra el plugin con Claude Code
- Declara agentes disponibles
- Proporciona metadata

**Ubicación:** Fija en `.claude-plugin/plugin.json` (requerido por Claude Code)

---

### 2. System Prompts de Agentes (agents/*.md)

Cada agente es un archivo markdown con frontmatter YAML + system prompt:

```markdown
---
agentName: plsql-analyzer
color: blue
description: |
  Analiza objetos PL/SQL, extrae conocimiento de negocio, clasifica complejidad.
---

# System Prompt del Agente

Eres un agente especializado en...
```

**Decisiones de Diseño Clave:**

**Decisión 1: Los agentes trabajan con CWD (Current Working Directory)**
- Los agentes usan **rutas relativas** desde CWD, no desde directorio del plugin
- Ejemplo: `sql/extracted/manifest.json` se resuelve a `phantomx-nexus/sql/extracted/manifest.json`
- **Por qué:** Permite que el plugin funcione con cualquier proyecto, no hardcodeado a phantomx-nexus

**Decisión 2: Los agentes son stateless (sin estado)**
- No hay estado persistente dentro de agentes
- Todo el estado está en archivos del proyecto (manifest.json, progress.json, outputs)
- **Por qué:** Los agentes pueden ser terminados/reiniciados sin perder progreso

**Decisión 3: Procesamiento por lotes con IDs explícitos**
- Cada objeto tiene ID único: `obj_0001`, `obj_0002`, etc.
- Los outputs usan ID en nombre de archivo: `obj_0001_VALIDAR_EMAIL.json`
- **Por qué:** Fácil rastrear qué se procesó, reanudar desde fallos

**Decisión 4: Diseño seguro para paralelismo**
- Múltiples instancias de agente pueden correr concurrentemente
- Cada agente procesa IDs de objetos diferentes (sin solapamiento)
- **Por qué:** Maximizar paralelismo de sub-agentes de Claude Code (20+)

---

### 3. Sistema de Manifest (manifest.json + progress.json)

**manifest.json** - Índice completo de todos los objetos:

```json
{
  "total_objects": 8122,
  "objects": [
    {
      "object_id": "obj_0001",
      "object_name": "VALIDAR_EMAIL",
      "object_type": "FUNCTION",
      "source_file": "functions.sql",
      "line_start": 1,
      "line_end": 25,
      "status": "pending"
    }
  ]
}
```

**progress.json** - Estado actual del procesamiento:

```json
{
  "total_objects": 8122,
  "processed_count": 200,
  "pending_count": 7922,
  "current_batch": "batch_001",
  "last_object_processed": "obj_0200",
  "status": "in_progress",
  "batches": [
    {
      "batch_id": "batch_001",
      "object_ids": ["obj_0001", "obj_0002", ..., "obj_0200"],
      "status": "completed",
      "completed_at": "2025-01-06T10:30:00Z"
    }
  ]
}
```

**¿Por qué archivos separados?**
- `manifest.json` - Estático, generado una vez, nunca cambia
- `progress.json` - Dinámico, actualizado frecuentemente durante migración

---

### 4. Estructura de Outputs

Todos los outputs están en el **directorio del proyecto** (CWD), NO en el directorio del plugin:

```
phantomx-nexus/
├── knowledge/
│   ├── json/
│   │   └── batch_001/
│   │       ├── obj_0001_VALIDAR_EMAIL.json
│   │       ├── obj_0002_CALCULAR_DESCUENTO.json
│   │       └── ...
│   ├── markdown/
│   │   └── batch_001/
│   │       ├── obj_0001_VALIDAR_EMAIL.md
│   │       └── ...
│   └── classification/
│       ├── simple_objects.txt
│       ├── complex_objects.txt
│       └── summary.json
├── migrated/
│   ├── simple/
│   │   ├── functions/
│   │   ├── procedures/
│   │   └── packages/
│   └── complex/
│       ├── functions/
│       ├── procedures/
│       └── packages/
├── compilation_results/
│   ├── success/
│   └── errors/
└── shadow_tests/
```

**Decisiones de Diseño:**

**Decisión 5: Organización jerárquica por batch**
- Outputs agrupados por batch (batch_001/, batch_002/, etc.)
- **Por qué:** Fácil identificar qué batch produjo qué outputs, simplifica limpieza

**Decisión 6: Outputs en formato dual (JSON + Markdown)**
- JSON para datos estructurados (pgvector, automatización)
- Markdown para revisión humana
- **Por qué:** Sirve tanto a máquinas (automatización) como a humanos (revisión)

**Decisión 7: Nombres de archivo predecibles**
- Patrón: `{object_id}_{object_name}.{ext}`
- Ejemplo: `obj_0001_VALIDAR_EMAIL.json`
- **Por qué:** Los scripts pueden detectar fácilmente objetos completados escaneando nombres de archivo

---

## 🔄 Flujo de Datos por Fase

### Fase 1: Análisis y Clasificación

```
1. Usuario ejecuta: prepare_migration.py
   ├─▶ Parsea sql/extracted/*.sql
   ├─▶ Genera manifest.json
   └─▶ Inicializa progress.json

2. Usuario lanza 20 agentes plsql-analyzer
   ├─▶ Cada agente lee manifest.json
   ├─▶ Cada agente procesa 10 objetos (obj_0001-obj_0010, etc.)
   ├─▶ Cada agente escribe:
   │   ├─▶ knowledge/json/batch_001/obj_XXXX_NAME.json
   │   └─▶ knowledge/markdown/batch_001/obj_XXXX_NAME.md
   └─▶ Agentes agregan a classification/simple_objects.txt o complex_objects.txt

3. Usuario ejecuta: update_progress.py batch_001
   ├─▶ Escanea knowledge/json/batch_001/ por objetos completados
   ├─▶ Actualiza progress.json
   └─▶ Retorna siguiente batch a procesar
```

### Fase 2A: Conversión Simple (ora2pg)

```
1. Usuario ejecuta: convert_simple_objects.sh
   ├─▶ Lee classification/simple_objects.txt
   ├─▶ Extrae objetos de sql/extracted/*.sql
   ├─▶ Alimenta a ora2pg
   └─▶ Escribe migrated/simple/*.sql
```

**Nota:** Esta fase se ejecuta **localmente** (no con agentes Claude), sin costo de tokens.

### Fase 2B: Conversión Compleja

```
1. Usuario lanza 20 agentes plsql-converter
   ├─▶ Cada agente lee classification/complex_objects.txt
   ├─▶ Cada agente lee archivos fuente sql/extracted/
   ├─▶ Cada agente procesa 10 objetos complejos
   ├─▶ Cada agente escribe:
   │   ├─▶ migrated/complex/*.sql (código convertido)
   │   └─▶ conversion_log/obj_XXXX_NAME.md (documentación)
   └─▶ Agentes aplican estrategias arquitectónicas (AUTONOMOUS_TRANSACTION, UTL_HTTP, etc.)

2. Usuario ejecuta: update_progress.py batch_XXX
```

### Fase 3: Validación de Compilación

```
1. Usuario lanza 20 agentes compilation-validator
   ├─▶ Cada agente lee migrated/{simple,complex}/*.sql
   ├─▶ Cada agente conecta a PostgreSQL 17.4
   ├─▶ Cada agente ejecuta scripts CREATE
   ├─▶ Cada agente escribe:
   │   ├─▶ compilation_results/success/*.log (si OK)
   │   └─▶ compilation_results/errors/*.error (si falló + sugerencia de fix)
   └─▶ Agentes generan global_report.md con estadísticas

2. Usuario revisa errores, agentes re-ejecutan con fixes
```

### Fase 4: Shadow Testing

```
1. Usuario lanza 10 agentes shadow-tester (más lento, usa ambas DBs)
   ├─▶ Cada agente lee migrated/*.sql
   ├─▶ Cada agente conecta a Oracle + PostgreSQL
   ├─▶ Cada agente ejecuta mismo código en ambas DBs
   ├─▶ Cada agente compara resultados:
   │   ├─▶ Comparación de datos (fila por fila)
   │   ├─▶ Comparación de estructura (columnas, tipos)
   │   └─▶ Comparación de performance (tiempo de ejecución)
   └─▶ Cada agente escribe:
       ├─▶ shadow_tests/obj_XXXX_NAME.json (resultados de comparación)
       └─▶ shadow_tests/discrepancies.txt (si se encontraron diferencias)

2. Usuario revisa discrepancias, corrige si es necesario
```

---

## 🔧 Arquitectura de Scripts

### prepare_migration.py

**Propósito:** Configuración única antes de Fase 1

**Input:**
- `sql/extracted/*.sql` (archivos fuente Oracle)

**Output:**
- `sql/extracted/manifest.json`
- `sql/extracted/progress.json`
- Directorios creados: `knowledge/`, `migrated/`, etc.

**Algoritmo Clave:**
1. Parsear cada archivo `.sql` con regex/parser PL/SQL
2. Extraer cada objeto (FUNCTION, PROCEDURE, PACKAGE, etc.)
3. Registrar posiciones de línea (line_start, line_end)
4. Asignar ID único (obj_0001, obj_0002, ...)
5. Escribir a manifest.json
6. Inicializar progress.json con status="initialized"

**Decisión de Diseño:** Este script es **idempotente** - seguro re-ejecutar con flag `--force`.

---

### update_progress.py

**Propósito:** Actualizar progreso después de cada batch

**Input:**
- `sql/extracted/progress.json`
- `knowledge/json/batch_XXX/` (escanea por objetos completados)

**Output:**
- `sql/extracted/progress.json` actualizado
- Imprime siguiente batch a procesar

**Algoritmo Clave:**
1. Leer progress.json
2. Escanear directorio output por archivos que coincidan `obj_XXXX_*.json`
3. Extraer object_ids de nombres de archivo
4. Marcar objetos como "completed" en progress.json
5. Calcular siguiente batch (siguientes 200 objetos pendientes)
6. Actualizar contadores (processed_count, pending_count)

**Decisión de Diseño:** Usa **detección basada en nombre de archivo** en lugar de parsear contenido para velocidad.

---

### convert_simple_objects.sh

**Propósito:** Convertir objetos SIMPLE con ora2pg (Fase 2A)

**Input:**
- `classification/simple_objects.txt`
- `sql/extracted/*.sql`

**Output:**
- `migrated/simple/*.sql`

**Algoritmo Clave:**
1. Leer simple_objects.txt (lista de nombres de objetos)
2. Para cada objeto:
   - Extraer de sql/extracted/ usando posiciones de línea de manifest.json
   - Escribir a archivo temporal
   - Ejecutar ora2pg en archivo temporal
   - Guardar output en migrated/simple/
3. Limpiar archivos temporales

**Decisión de Diseño:** Se ejecuta **localmente** sin agentes Claude para ahorrar tokens.

---

## 🛡️ Manejo de Errores y Resiliencia

### Problema: Límites de sesión (45-60 mensajes por 5 horas)

**Solución:** Seguimiento de progreso + reanudación
- `progress.json` rastrea exactamente dónde paramos
- Siguiente sesión lee progress.json y continúa desde último batch
- Sin trabajo desperdiciado reprocesando objetos completados

### Problema: Fallos de agentes a mitad de batch

**Solución:** Granularidad a nivel de objeto
- Cada objeto tiene ID único
- Outputs usan ID en nombre de archivo
- `update_progress.py` solo cuenta objetos con archivos output
- Objetos fallidos permanecen "pending" y se reintentan en siguiente batch

### Problema: Archivos grandes (packages_body.sql = 50K+ líneas)

**Solución:** Manifest con posiciones de línea
- Agentes no leen archivos completos
- manifest.json contiene rangos exactos de línea
- Agentes extraen solo porción necesaria: `lines[line_start:line_end]`

### Problema: Agentes paralelos procesando mismo objeto

**Solución:** Asignaciones de batch sin solapamiento
- Usuario asigna explícitamente rangos de objetos a agentes
- Ejemplo: Agente 1 obtiene obj_0001-0010, Agente 2 obtiene obj_0011-0020
- No se necesita locking porque no hay solapamiento

---

## 📊 Análisis de Escalabilidad

### Actual: 8,122 objetos

**Fase 1 (Análisis):**
- 20 agentes × 10 objetos cada uno = 200 objetos/mensaje
- 8,122 ÷ 200 = 42 mensajes
- Tiempo: ~5 horas (1 sesión)

**¿Qué pasa con 50,000 objetos?**
- 50,000 ÷ 200 = 250 mensajes
- 250 ÷ 50 = 5 sesiones
- Tiempo: ~25 horas (5 sesiones en 2-3 días)

**Cuello de botella:** Límites de mensajes de Claude Code, no cómputo/memoria.

**Mitigación:** Aumentar tamaño de batch (20 objetos por agente en lugar de 10) si los objetos son pequeños.

---

## 🔐 Consideraciones de Seguridad

### Credenciales de Base de Datos

**Problema:** Agentes necesitan credenciales PostgreSQL para Fase 3 y 4

**Opciones de Solución:**
1. **Variables de entorno** (recomendado)
   ```bash
   export PGHOST=aurora-cluster.amazonaws.com
   export PGDATABASE=veris_dev
   export PGUSER=migration_user
   export PGPASSWORD=***
   claude
   ```

2. **Archivo de configuración** (phantomx-nexus/.pgpass)
   - No commiteado a git (en .gitignore)
   - Leído por agentes cuando se necesite

**Decisión de Diseño:** Usar variables de entorno para evitar almacenar secretos en archivos.

---

### Inyección SQL en Código Dinámico

**Problema:** Agentes ejecutan SQL proporcionado por usuario

**Solución:**
- Conexión PostgreSQL usa queries parametrizadas
- Nunca concatenar strings de usuario directamente en SQL
- Usar psycopg2/asyncpg con escapado apropiado

**Ejemplo (INCORRECTO):**
```python
# VULNERABLE
sql = f"CREATE FUNCTION {object_name}() ..."
cursor.execute(sql)
```

**Ejemplo (CORRECTO):**
```python
# SEGURO - usar quoteo de identificadores
from psycopg2 import sql
query = sql.SQL("CREATE FUNCTION {}() ...").format(sql.Identifier(object_name))
cursor.execute(query)
```

---

## 🔄 Puntos de Extensión

### Agregar una Nueva Fase

Para agregar "Fase 5: Optimización de Performance":

1. Crear `agents/performance-tuner.md` con system prompt
2. Agregar a `.claude-plugin/plugin.json`:
   ```json
   "agents": [
     ...,
     "agents/performance-tuner.md"
   ]
   ```
3. Actualizar docs/ESTRATEGIA.md con detalles de Fase 5
4. Crear directorio output: `performance_reports/`

No se necesitan cambios en agentes existentes (acoplamiento débil).

---

### Soporte para Base de Datos Fuente Diferente (ej. MySQL → PostgreSQL)

Cambios necesarios:
1. **prepare_migration.py**: Actualizar parser para reconocer sintaxis MySQL
2. **Prompts de agentes**: Cambiar referencias específicas de Oracle a MySQL
3. **Estrategias de conversión**: Mapear features MySQL a PostgreSQL

La arquitectura del plugin soporta esto - solo intercambiar lógica del parser.

---

## 📚 Patrones de Diseño Utilizados

### 1. **Patrón de Agentes Stateless**
- Agentes son funciones puras: Input → Procesamiento → Output
- Sin estado mutable dentro de agentes
- Todo el estado es externo (manifest.json, progress.json)

### 2. **Patrón de Procesamiento por Lotes**
- Dataset grande (8,122 objetos) dividido en batches (200 objetos cada uno)
- Cada batch es independiente
- Batches fallidos pueden reintentarse sin afectar otros

### 3. **Patrón de Checkpoint de Progreso**
- Guardar progreso después de cada batch
- Reanudar desde último checkpoint en fallo
- Operaciones idempotentes (seguro re-ejecutar)

### 4. **Patrón de Formato Dual de Output**
- Datos estructurados (JSON) para máquinas
- Datos legibles (Markdown) para revisión
- Misma información, diferentes representaciones

### 5. **Separación de Responsabilidades**
- Plugin: Lógica y workflows (portable)
- Proyecto: Datos y resultados (específico a phantomx-nexus)
- Runtime: Ambiente de ejecución (Claude Code)

---

## 🎓 Lecciones Aprendidas

### Lo que Funcionó Bien
1. **Instalación desde marketplace** - Plugin disponible globalmente, separación limpia de plugin y proyecto
2. **Sistema de manifest** - Elimina adivinanzas sobre qué procesar
3. **Diseño de batches** - Maximiza paralelismo dentro de límites de mensajes
4. **Seguimiento de progreso** - Sobrevive límites de sesión con gracia

### Lo que Podría Mejorarse
1. **Configuración centralizada** - Actualmente algunas rutas hardcodeadas en agentes, debería usar archivo de config
2. **Mejores mensajes de error** - Cuando un agente falla, difícil debuggear sin logging verbose
3. **Modo dry-run** - Debería tener modo para probar sin escribir outputs

### Mejoras Futuras
1. **UI Web** - Visualizar progreso, ver resultados
2. **Ejecución paralela de batches** - Ejecutar múltiples batches concurrentemente (si Claude Code lo soporta)
3. **Auto-fix de errores comunes** - Fase 3 podría auto-corregir patrones conocidos en lugar de solo sugerir

---

**Versión del Documento:** 1.0.0
**Última Actualización:** 2025-01-06
**Próxima Revisión:** Después de completar Fase 1
