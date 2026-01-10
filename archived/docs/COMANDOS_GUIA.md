# Guía Completa de Comandos Slash

Esta guía explica cómo usar los **comandos slash** del plugin para facilitar la migración Oracle → PostgreSQL.

---

## 🎯 ¿Por Qué Usar Comandos en Lugar de Invocar Agentes Directamente?

### ❌ Forma Manual (Sin Comandos)

```
Usuario: "Quiero analizar los primeros 200 objetos PL/SQL.
Por favor lanza 20 agentes plsql-analyzer en paralelo.
Lee el manifest desde sql/extracted/manifest.json.
Determina los objetos del batch_001 (1-200).
Para cada agente, procesa 10 objetos.
Al terminar, actualiza progress.json.
Guarda los resultados en knowledge/json/ y knowledge/markdown/.
Clasifica en classification/simple_objects.txt y complex_objects.txt."
```

**Problemas:**
- ❌ Instrucciones largas y repetitivas
- ❌ Fácil olvidar parámetros
- ❌ Sin validación de pre-requisitos
- ❌ No actualiza progreso automáticamente

### ✅ Forma con Comandos

```bash
/analyze next
```

**Beneficios:**
- ✅ **Una línea** ejecuta todo el flujo
- ✅ **Validaciones automáticas** de pre-requisitos
- ✅ **Progreso actualizado** automáticamente
- ✅ **Defaults inteligentes** (200 objetos, modo next, etc.)
- ✅ **Resumen claro** al finalizar

---

## 📋 Lista Completa de Comandos

### 1. `/init` - Inicialización de Proyecto

**Propósito:** Prepara el proyecto para la migración.

**Uso:**
```bash
/init              # Inicialización normal (solo si no existe)
/init force        # Regenerar todo (sobrescribir existente)
```

**Lo que hace:**
1. Verifica archivos fuente en `sql/extracted/*.sql`
2. Copia `prepare_migration.py` al proyecto
3. Ejecuta script para generar `manifest.json` y `progress.json`
4. Crea estructura de directorios (`knowledge/`, `migrated/`, etc.)
5. Valida configuración completa

**Cuándo usar:**
- ✅ **Primera vez** que usas el plugin en un proyecto
- ✅ Cuando quieres **regenerar manifest/progress** (con `force`)
- ✅ Si moviste archivos y necesitas **reinicializar**

**Output esperado:**
```
╔════════════════════════════════════════════╗
║  PROYECTO INICIALIZADO CORRECTAMENTE ✅    ║
╠════════════════════════════════════════════╣
║  Total objetos: 8,122                      ║
║  Fases configuradas: 4                     ║
║  Directorios creados: 4                    ║
║  Estado: LISTO PARA INICIAR                ║
╚════════════════════════════════════════════╝

Siguiente paso: /analyze next
```

---

### 2. `/status` - Estado de la Migración

**Propósito:** Muestra progreso completo de todas las fases.

**Uso:**
```bash
/status           # Todas las fases
/status 1         # Solo Fase 1
/status 2         # Solo Fase 2
/status 3         # Solo Fase 3
/status 4         # Solo Fase 4
```

**Lo que muestra:**
- Progreso por fase (%)
- Objetos procesados / total
- Tiempo transcurrido
- Siguiente batch recomendado
- Problemas detectados (si hay)

**Cuándo usar:**
- ✅ **Antes de iniciar** cualquier fase (para saber el estado)
- ✅ **Después de cada batch** (para ver progreso)
- ✅ **Después de límite de sesión** (para saber dónde retomar)
- ✅ **Para verificar éxito final** (debe mostrar 100% en todas las fases)

**Output esperado:**
```
Progreso General:
████████████████████░░░░░░░░  65% (5,279 / 8,122 objetos)

Fase 1: ████████████████████ 100% ✅ COMPLETA
Fase 2: ███████████████░░░░░  75% 🔄 EN PROGRESO
Fase 3: ██████░░░░░░░░░░░░░░  30% ⏳ PENDIENTE
Fase 4: ░░░░░░░░░░░░░░░░░░░░   0% ⏳ PENDIENTE

Siguiente acción: /convert next
```

---

### 3. `/analyze` - Fase 1: Análisis

**Propósito:** Analiza objetos PL/SQL y los clasifica en SIMPLE/COMPLEX.

**Uso:**
```bash
/analyze                    # Siguiente batch pendiente (200 objetos)
/analyze next               # Mismo efecto
/analyze 001                # Batch específico
/analyze next 100           # Siguiente batch con 100 objetos
/analyze all                # Todos los pendientes (usar con precaución)
```

**Lo que hace:**
1. Lee `progress.json` para determinar siguiente batch
2. Lee `manifest.json` para obtener definiciones de objetos
3. Invoca **20 agentes `plsql-analyzer`** en paralelo
4. Cada agente procesa **10 objetos** (total 200 objetos/mensaje)
5. Genera outputs:
   - `knowledge/json/` - Análisis estructurado
   - `knowledge/markdown/` - Análisis legible
   - `classification/simple_objects.txt` - Objetos para ora2pg
   - `classification/complex_objects.txt` - Objetos para IA
6. Actualiza `progress.json`

**Cuándo usar:**
- ✅ **Inicio de la migración** (primera fase)
- ✅ **Después de cada batch** hasta completar 8,122 objetos
- ✅ **~42 ejecuciones** necesarias (8,122 / 200 = 41.6)

**Duración:** ~5 horas totales (42 mensajes, ~7 min/mensaje)

**Output esperado:**
```
✅ Batch 001 completado: 200 objetos analizados

Clasificación:
- SIMPLE: 127 objetos (63%)
- COMPLEX: 73 objetos (37%)

Progreso total: 200 / 8,122 (2.5%)

Siguiente batch: /analyze next  (batch 002)
```

---

### 4. `/convert` - Fase 2B: Conversión Compleja

**Propósito:** Convierte objetos COMPLEX usando estrategias arquitectónicas.

**Uso:**
```bash
/convert                           # Siguiente batch pendiente
/convert next                      # Mismo efecto
/convert 001                       # Batch específico
/convert next 100                  # Siguiente batch con 100 objetos
/convert next 50 UTL_HTTP          # Solo objetos con UTL_HTTP
/convert all 20 AUTONOMOUS_TRANSACTION  # Todos con AUTONOMOUS_TRANSACTION
```

**Pre-requisitos:**
- ✅ Fase 1 completada (100% objetos analizados)
- ✅ Fase 2A ejecutada (`bash scripts/convert_simple_objects.sh`)
- ✅ Archivo `classification/complex_objects.txt` existe

**Lo que hace:**
1. Lee `classification/complex_objects.txt`
2. Filtra por estrategia si se especificó
3. Invoca **20 agentes `plsql-converter`** en paralelo
4. Aplica estrategias arquitectónicas:
   - `AUTONOMOUS_TRANSACTION` → dblink / Lambda
   - `UTL_HTTP` → AWS Lambda + wrapper
   - `UTL_FILE` → aws_s3 export a S3
   - `DBMS_SQL` → EXECUTE + format()
   - etc.
5. Genera código PostgreSQL en `migrated/complex/`
6. Documenta decisiones en `conversion_log/`
7. Actualiza `progress.json`

**Cuándo usar:**
- ✅ **Después de Fase 1 y 2A**
- ✅ **~16 ejecuciones** necesarias (~3,122 complex / 200 = 15.6)

**Duración:** ~5 horas totales (16 mensajes, ~20 min/mensaje)

**Output esperado:**
```
✅ Batch 001 completado: 200 objetos complejos convertidos

Estrategias aplicadas:
- UTL_HTTP: 45 objetos → AWS Lambda wrapper
- AUTONOMOUS_TRANSACTION: 32 objetos → dblink
- UTL_FILE: 28 objetos → aws_s3
- DBMS_SQL: 18 objetos → EXECUTE
- Otros: 77 objetos → Diversas estrategias

Archivos generados:
- migrated/complex/: 200 archivos .sql
- conversion_log/: 200 archivos .md

Progreso Fase 2B: 200 / 3,122 (6.4%)

Siguiente batch: /convert next  (batch 002)
```

---

### 5. `/validate` - Fase 3: Validación

**Propósito:** Valida compilación en PostgreSQL 17.4.

**Uso:**
```bash
/validate                    # Siguiente batch pendiente
/validate next               # Mismo efecto
/validate 001                # Batch específico
/validate next 100 complex   # Solo objetos complejos
/validate all 50 simple      # Todos los simples (batches de 50)
```

**Pre-requisitos:**
- ✅ Fase 2A y 2B completadas
- ✅ **PostgreSQL 17.4 accesible** (env vars configuradas)
- ✅ Archivos en `migrated/simple/` y/o `migrated/complex/`

**Variables de entorno requeridas:**
```bash
export PGHOST=your-aurora-endpoint.amazonaws.com
export PGPORT=5432
export PGDATABASE=phantomx
export PGUSER=postgres
export PGPASSWORD=your-password
export PGSSLMODE=require
```

**Lo que hace:**
1. Verifica conexión a PostgreSQL
2. Lee scripts SQL de `migrated/`
3. Invoca **20 agentes `compilation-validator`** en paralelo
4. Cada agente:
   - Conecta a PostgreSQL
   - Ejecuta script SQL
   - Captura errores de compilación
5. Clasifica resultados:
   - `compilation_results/success/` - Compilación exitosa
   - `compilation_results/errors/` - Errores + sugerencias
6. Genera `summary.json` con estadísticas
7. Actualiza `progress.json`

**Cuándo usar:**
- ✅ **Después de Fase 2**
- ✅ **~42 ejecuciones** necesarias (8,122 / 200 = 41.6)
- ✅ **Objetivo:** >95% compilación exitosa

**Duración:** ~5 horas totales (42 mensajes, ~7 min/mensaje)

**Output esperado:**
```
✅ Batch 001 completado: 200 objetos validados

Resultados:
- ✅ Compilación exitosa: 192 objetos (96%)
- ❌ Errores de compilación: 8 objetos (4%)

Tipos de errores:
1. Función Oracle sin equivalente: 3 casos
2. Tipo de dato incompatible: 2 casos
3. Sintaxis PL/pgSQL: 2 casos
4. Privilegios faltantes: 1 caso

Progreso Fase 3: 200 / 8,122 (2.5%)

Siguiente acción:
- Si >95% éxito → /validate next (continuar)
- Si <95% éxito → Revisar errores antes de continuar
```

---

### 6. `/test` - Fase 4: Shadow Testing

**Propósito:** Ejecuta objetos en Oracle y PostgreSQL, compara resultados.

**Uso:**
```bash
/test                       # Siguiente batch pendiente (50 objetos)
/test next                  # Mismo efecto
/test 001                   # Batch específico
/test next 20 unit          # Solo pruebas unitarias
/test all 10 integration    # Todos (integración, batches de 10)
```

**Pre-requisitos:**
- ✅ Fase 3 completada con >95% éxito
- ✅ **Oracle 19c accesible** (para comparación)
- ✅ **PostgreSQL 17.4 accesible**

**Variables de entorno requeridas:**
```bash
# PostgreSQL
export PGHOST=...
export PGDATABASE=...
export PGUSER=...
export PGPASSWORD=...

# Oracle
export ORACLE_HOST=...
export ORACLE_SID=...
export ORACLE_USER=...
export ORACLE_PASSWORD=...
```

**Lo que hace:**
1. Verifica conexión a Oracle y PostgreSQL
2. Lee objetos de `compilation_results/success/`
3. Invoca **10 agentes `shadow-tester`** en paralelo (menos por complejidad)
4. Cada agente:
   - Ejecuta objeto en Oracle con inputs de prueba
   - Ejecuta mismo objeto en PostgreSQL con mismos inputs
   - Compara resultados (valores, tipos, errores)
   - Documenta diferencias
5. Genera comparaciones en `shadow_tests/results/`
6. Documenta diferencias en `shadow_tests/mismatches/`
7. Genera `summary.json` con estadísticas
8. Actualiza `progress.json`

**Cuándo usar:**
- ✅ **Después de Fase 3 con >95% éxito**
- ✅ **~84 ejecuciones** necesarias (8,122 / 50 = 162, pero usamos batches de 100)
- ✅ **Objetivo:** >95% resultados idénticos

**Duración:** ~10 horas totales (84 mensajes, ~7 min/mensaje)

**Output esperado:**
```
✅ Batch 001 completado: 50 objetos testeados

Resultados:
- ✅ Resultados idénticos: 48 objetos (96%)
- ⚠️ Diferencias encontradas: 2 objetos (4%)

Tipos de diferencias:
- Precisión numérica: 1 caso (aceptable, usar ROUND)
- Formato fecha/hora: 1 caso (aceptable, usar TO_CHAR)
- Diferencias funcionales: 0 casos (crítico)

Progreso Fase 4: 50 / 8,122 (0.6%)

Siguiente acción:
- Si >95% match → /test next (continuar)
- Si <95% match → Investigar diferencias
```

---

## 🔄 Flujo Completo con Comandos

### Sesión 1: Inicialización + Fase 1 (5 horas)

```bash
# 1. Inicializar proyecto
/init

# 2. Verificar estado
/status

# 3. Fase 1: Analizar (42 batches)
/analyze next    # Batch 001 (objetos 1-200)
/analyze next    # Batch 002 (objetos 201-400)
# ... repetir hasta batch 042
/analyze next    # Batch 042 (objetos 8,001-8,122)

# 4. Verificar progreso Fase 1
/status 1        # Debe mostrar 100%
```

**Límite de sesión:** ~45-60 mensajes cada 5 horas
**Mensajes usados:** ~42 mensajes para Fase 1

---

### Sesión 2: Fase 2A + 2B (5 horas)

```bash
# 1. Verificar progreso
/status

# 2. Fase 2A: Conversión simple (LOCAL, no usa Claude)
bash scripts/convert_simple_objects.sh

# 3. Fase 2B: Conversión compleja (16 batches)
/convert next    # Batch 001 (objetos complejos 1-200)
/convert next    # Batch 002 (objetos complejos 201-400)
# ... repetir hasta batch 016
/convert next    # Batch 016 (objetos complejos 3,001-3,122)

# 4. Verificar progreso Fase 2
/status 2        # Debe mostrar 100%
```

**Mensajes usados:** ~16 mensajes para Fase 2B

---

### Sesión 3: Fase 3 (5 horas)

```bash
# 1. Verificar progreso
/status

# 2. Configurar PostgreSQL env vars
export PGHOST=...
export PGDATABASE=...
export PGUSER=...
export PGPASSWORD=...

# 3. Fase 3: Validación (42 batches)
/validate next   # Batch 001 (objetos 1-200)
/validate next   # Batch 002 (objetos 201-400)
# ... repetir hasta batch 042
/validate next   # Batch 042 (objetos 8,001-8,122)

# 4. Verificar progreso Fase 3
/status 3        # Debe mostrar >95% compilación exitosa
```

**Mensajes usados:** ~42 mensajes para Fase 3

---

### Sesión 4-5: Fase 4 (10 horas, 2 sesiones)

```bash
# 1. Verificar progreso
/status

# 2. Configurar Oracle + PostgreSQL env vars
export ORACLE_HOST=...
export ORACLE_USER=...
export PGHOST=...

# 3. Fase 4: Shadow Testing (84 batches de 100 objetos)
/test next       # Batch 001 (objetos 1-100)
/test next       # Batch 002 (objetos 101-200)
# ... repetir hasta batch 084
/test next       # Batch 084 (objetos 8,001-8,122)

# 4. Verificar progreso Fase 4
/status 4        # Debe mostrar >95% match
```

**Mensajes usados:** ~84 mensajes para Fase 4 (dividir en 2 sesiones)

---

## 🎯 Consejos de Uso

### 1. Modo "next" es tu Amigo

```bash
# ✅ RECOMENDADO: Siempre usar "next"
/analyze next
/convert next
/validate next
/test next

# ❌ EVITAR: Especificar batches manualmente (propenso a errores)
/analyze 042
```

**Razón:** El modo `next` lee `progress.json` automáticamente y determina el siguiente batch pendiente. Nunca procesarás el mismo batch dos veces ni saltarás batches.

---

### 2. Verificar Estado Frecuentemente

```bash
# Antes de cada sesión
/status

# Después de cada batch
/status 1   # o 2, 3, 4 según la fase

# Al final de cada sesión (antes del límite)
/status
```

**Razón:** Permite ver progreso, detectar problemas, y saber exactamente dónde retomar después del límite de sesión.

---

### 3. Ajustar Batch Size Según Necesidad

```bash
# Default: 200 objetos (óptimo para análisis y conversión)
/analyze next

# Reducir si objetos son muy grandes (tarda mucho)
/analyze next 100

# Aumentar si objetos son simples (procesar más rápido)
/analyze next 300

# Shadow testing: 50 objetos por batch (más complejo)
/test next 50
```

---

### 4. Filtrar por Tipo o Estrategia

```bash
# Solo objetos complejos
/validate next 100 complex

# Solo objetos simples
/validate next 100 simple

# Solo objetos con estrategia específica
/convert next 50 UTL_HTTP
```

---

### 5. Reiniciar si Algo Sale Mal

```bash
# Regenerar manifest y progress (sobrescribe existente)
/init force

# Verificar que todo está correcto
/status

# Continuar desde donde quedó
/analyze next
```

---

## 🚨 Problemas Comunes y Soluciones

### Problema: Comando no reconocido

```
ERROR: Command '/analyze' not found
```

**Solución:**
```bash
# Verificar que el plugin está cargado
claude plugins list | grep oracle-postgres-migration

# Reiniciar Claude Code
exit
claude
```

---

### Problema: Variables no reemplazan

```
ERROR: {{batch}} not defined
```

**Solución:**
Los comandos usan sintaxis especial `{{variable}}` que Claude Code reemplaza automáticamente. Si ves este error, verifica:
1. Estás usando el comando correcto (con `/` al inicio)
2. El plugin está actualizado
3. Claude Code está en la versión correcta (>=1.0.0)

---

### Problema: Pre-requisitos fallan

```
ERROR: sql/extracted/manifest.json not found
```

**Solución:**
```bash
# Ejecutar inicialización
/init

# Verificar archivos fuente existen
ls sql/extracted/*.sql
```

---

### Problema: PostgreSQL no conecta (Fase 3)

```
ERROR: Cannot connect to PostgreSQL
```

**Solución:**
```bash
# Configurar env vars
export PGHOST=your-host.amazonaws.com
export PGDATABASE=phantomx
export PGUSER=postgres
export PGPASSWORD=your-password
export PGSSLMODE=require

# Verificar conexión manualmente
psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c "SELECT version();"

# Reintentar
/validate next
```

---

### Problema: Oracle no conecta (Fase 4)

```
ERROR: Cannot connect to Oracle
```

**Solución:**
```bash
# Configurar env vars Oracle
export ORACLE_HOST=your-oracle-host.com
export ORACLE_PORT=1521
export ORACLE_SID=ORCL
export ORACLE_USER=system
export ORACLE_PASSWORD=your-password

# Verificar conexión manualmente
sqlplus $ORACLE_USER/$ORACLE_PASSWORD@$ORACLE_HOST:$ORACLE_PORT/$ORACLE_SID

# Reintentar
/test next
```

---

## 📊 Métricas de Éxito

### Fase 1: Análisis
- ✅ **100% objetos analizados** (8,122 / 8,122)
- ✅ **Clasificación completa** (simple_objects.txt + complex_objects.txt)

### Fase 2: Conversión
- ✅ **100% objetos convertidos** (8,122 / 8,122)
- ✅ **Archivos generados** en `migrated/simple/` y `migrated/complex/`

### Fase 3: Validación
- ✅ **>95% compilación exitosa** (objetivo mínimo)
- ✅ **100% compilación exitosa** (objetivo ideal)

### Fase 4: Testing
- ✅ **>95% resultados idénticos** (objetivo mínimo)
- ✅ **100% resultados idénticos** (objetivo ideal)

---

## 🎉 Migración Exitosa

Cuando ejecutas `/status` al final y ves:

```
╔════════════════════════════════════════════╗
║  MIGRACIÓN COMPLETADA EXITOSAMENTE ✅      ║
╠════════════════════════════════════════════╣
║  Fase 1: ████████████████████ 100%        ║
║  Fase 2: ████████████████████ 100%        ║
║  Fase 3: ████████████████████  98%        ║
║  Fase 4: ████████████████████  97%        ║
╠════════════════════════════════════════════╣
║  Total objetos: 8,122                      ║
║  Compilación exitosa: 7,999 (98.5%)        ║
║  Resultados idénticos: 7,876 (97.0%)       ║
║                                            ║
║  ¡LISTO PARA PRODUCCIÓN! 🚀                ║
╚════════════════════════════════════════════╝
```

**¡FELICITACIONES!** Has migrado exitosamente 8,122 objetos de Oracle a PostgreSQL.

---

**Última Actualización:** 2025-01-07
**Versión:** 1.0.0
