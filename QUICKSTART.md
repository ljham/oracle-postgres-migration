# Quick Start - Oracle to PostgreSQL Migration Plugin

**Tiempo de lectura:** 7 minutos
**Objetivo:** Iniciar FASE 1 en menos de 10 minutos

**⚡ NUEVO:** Sistema automático de tracking y reanudación - Ver [TRACKING.md](TRACKING.md)

---

## 🎯 Problema Resuelto

**Pregunta:** ¿Cómo procesar 8,122 objetos que están mezclados en archivos SQL grandes?

**Respuesta:** Sistema de 3 componentes:
1. **`manifest.json`** - Índice de todos los objetos con posiciones exactas
2. **`progress.json`** - Estado del procesamiento (qué se procesó, qué falta)
3. **Detección automática** - Scripts detectan outputs y actualizan progreso

**Beneficios:**
- ✅ Reanudación automática desde cualquier punto
- ✅ Tolerante a cierres de sesión / límites de mensajes
- ✅ Sin reprocesar objetos ya completados
- ✅ Progreso visible en todo momento

Ver detalles: [TRACKING.md](TRACKING.md)

---

## 🚀 Inicio Rápido (4 Pasos)

### Paso 0: Instalar Plugin (1 minuto) - **⚡ NUEVO**

```bash
# Instalar plugin desde marketplace
claude plugins install oracle-postgres-migration

# Verificar instalación
claude plugins list | grep oracle-postgres-migration
```

### Paso 1: Preparar Sistema de Tracking (2 minutos)

```bash
# Navegar a tu proyecto con datos
cd /path/to/tu-proyecto

# Copiar scripts del plugin a tu proyecto
mkdir -p scripts
cp ~/.claude/plugins/oracle-postgres-migration/scripts/prepare_migration.py scripts/
cp ~/.claude/plugins/oracle-postgres-migration/scripts/update_progress.py scripts/
cp ~/.claude/plugins/oracle-postgres-migration/scripts/convert_simple_objects.sh scripts/

# Ejecutar script de preparación
python scripts/prepare_migration.py

# IMPORTANTE: El script usa el directorio actual (CWD) para encontrar
# los archivos sql/extracted/*.sql y crear manifest.json
```

**Este script:**
- ✅ Parsea archivos SQL grandes (functions.sql, packages_body.sql, etc.)
- ✅ Extrae posición exacta de cada uno de los 8,122 objetos
- ✅ Genera `sql/extracted/manifest.json` con índice completo
- ✅ Crea `sql/extracted/progress.json` para tracking
- ✅ **Crea automáticamente estructura de directorios (knowledge/, migrated/, etc.)**
- ✅ **Genera instrucciones listas para copiar/pegar en Claude Code**

**Output esperado:**
```
📁 Creando estructura de directorios...
  ✅ Creados 14 directorios nuevos

✅ Manifest generado: sql/extracted/manifest.json
   Total objetos: 8122
   - FUNCTION: 146
   - PROCEDURE: 196
   - PACKAGE_SPEC: 589
   - PACKAGE_BODY: 569
   - TRIGGER: 87

📦 Batch: batch_001
   Objetos: 1 - 200
   Progreso: 200/8122 (2.5%)

INSTRUCCIONES PARA CLAUDE CODE:
(instrucciones listas para copiar/pegar)
```

✅ **Listo:** Si el script se ejecutó sin errores, continúa al Paso 2.

---

### Paso 2: Verificar Pre-requisitos (1 minuto)

```bash
# 1. Archivos Oracle extraídos (OBLIGATORIO - deben existir)
ls sql/extracted/
# Debe mostrar: functions.sql, procedures.sql, packages_spec.sql, packages_body.sql, triggers.sql

# 2. Scripts copiados (se copian en Paso 1)
ls scripts/prepare_migration.py scripts/update_progress.py
# Debe mostrar: prepare_migration.py, update_progress.py

# 3. Manifest generado (se crea en Paso 1)
ls sql/extracted/manifest.json sql/extracted/progress.json
# Debe mostrar: manifest.json, progress.json

# 4. Estructura de directorios (se crea automáticamente en Paso 1)
ls knowledge/ migrated/ compilation_results/ shadow_tests/
# ✅ El script prepare_migration.py crea estos directorios automáticamente
```

✅ **Listo:** Si `sql/extracted/*.sql` existen y ejecutaste el Paso 1, continúa al Paso 3.

---

### Paso 3: Lanzar FASE 1 - Primer Batch (5 minutos)

```bash
# Iniciar Claude Code (el plugin se carga automáticamente)
claude
```

**En Claude Code, copiar y pegar las instrucciones generadas por `prepare_migration.py`**

Alternativamente, si necesitas generar manualmente:

**En Claude Code CLI o Web, ejecuta este prompt:**

```
Usa el agente plsql-analyzer para analizar los primeros 200 objetos PL/SQL.

Lanza 20 agentes en paralelo procesando 10 objetos cada uno:

1. Task plsql-analyzer "Analyze functions 1-10 from sql/extracted/functions.sql"
2. Task plsql-analyzer "Analyze functions 11-20 from sql/extracted/functions.sql"
3. Task plsql-analyzer "Analyze functions 21-30 from sql/extracted/functions.sql"
4. Task plsql-analyzer "Analyze functions 31-40 from sql/extracted/functions.sql"
5. Task plsql-analyzer "Analyze functions 41-50 from sql/extracted/functions.sql"
6. Task plsql-analyzer "Analyze functions 51-60 from sql/extracted/functions.sql"
7. Task plsql-analyzer "Analyze functions 61-70 from sql/extracted/functions.sql"
8. Task plsql-analyzer "Analyze functions 71-80 from sql/extracted/functions.sql"
9. Task plsql-analyzer "Analyze functions 81-90 from sql/extracted/functions.sql"
10. Task plsql-analyzer "Analyze functions 91-100 from sql/extracted/functions.sql"
11. Task plsql-analyzer "Analyze procedures 1-10 from sql/extracted/procedures.sql"
12. Task plsql-analyzer "Analyze procedures 11-20 from sql/extracted/procedures.sql"
13. Task plsql-analyzer "Analyze procedures 21-30 from sql/extracted/procedures.sql"
14. Task plsql-analyzer "Analyze procedures 31-40 from sql/extracted/procedures.sql"
15. Task plsql-analyzer "Analyze procedures 41-50 from sql/extracted/procedures.sql"
16. Task plsql-analyzer "Analyze procedures 51-60 from sql/extracted/procedures.sql"
17. Task plsql-analyzer "Analyze procedures 61-70 from sql/extracted/procedures.sql"
18. Task plsql-analyzer "Analyze procedures 71-80 from sql/extracted/procedures.sql"
19. Task plsql-analyzer "Analyze procedures 81-90 from sql/extracted/procedures.sql"
20. Task plsql-analyzer "Analyze procedures 91-100 from sql/extracted/procedures.sql"

Outputs esperados en knowledge/json/batch_001/, knowledge/markdown/batch_001/, y classification/*.txt
```

⏱️ **Tiempo:** ~15-20 minutos para procesar 200 objetos

---

### Paso 4: Actualizar Progreso y Continuar (2 minutos) - **⚡ NUEVO**

```bash
# Después de completar batch_001, actualizar progreso
python scripts/update_progress.py batch_001
```

**Este script:**
- ✅ Detecta outputs generados en `knowledge/json/batch_001/`
- ✅ Actualiza `manifest.json` (marca objetos como procesados)
- ✅ Actualiza `progress.json` (contadores, porcentaje)
- ✅ **Genera automáticamente instrucciones para batch_002**

**Output esperado:**
```
🔍 Detectando objetos procesados en batch_001...
  ✅ Encontrados 200 objetos procesados

📊 Actualizando progreso...
  ✅ Progreso actualizado:
     Procesados: 200/8122
     Pendientes: 7922
     Porcentaje: 2.5%

📦 Próximo batch: batch_002
   Objetos: 201 - 400

INSTRUCCIONES PARA CLAUDE CODE:
(instrucciones listas para batch_002)
```

**Verificación manual (opcional):**
```bash
# Contar archivos generados
find knowledge/json/batch_001/ -name "*.json" | wc -l
# Debe mostrar: 200

# Ver progreso actualizado
cat sql/extracted/progress.json | jq '.processed_count, .pending_count'
# Output: 200, 7922
```

✅ **Éxito:** Si ves 200 archivos procesados, continúa con batch_002.

---

### Ciclo de Repetición (hasta completar 8,122 objetos)

```
1. Copiar instrucciones del script → Ejecutar en Claude Code
   ↓
2. python scripts/update_progress.py batch_XXX
   ↓
3. Repetir con nuevas instrucciones generadas
```

**Total:** 42 batches × 200 objetos = 8,400 (cubre los 8,122)

---

## 📊 Progreso Completo - 8,122 Objetos

**FASE 1:** 42 mensajes × 200 objetos = 8,400 objetos (cubre los 8,122)

**Iteración:**
```bash
# Mensaje 1: Objetos 1-200 (HECHO arriba)
# Mensaje 2: Objetos 201-400
# Mensaje 3: Objetos 401-600
# ...
# Mensaje 42: Objetos 8,001-8,122
```

**Timeline:** 5 horas (1 sesión de trabajo)

---

## 🔄 Próximas Fases

### FASE 2A: Conversión Simple (30 minutos)
```bash
./scripts/convert_simple_objects.sh
```
→ Convierte ~5,000 objetos SIMPLE con ora2pg (0 tokens)

### FASE 2B: Conversión Compleja (5 horas)
→ Usa agente `plsql-converter` para ~3,122 objetos COMPLEX

### FASE 3: Validación (5 horas)
→ Usa agente `compilation-validator` para 8,122 objetos

### FASE 4: Shadow Testing (10 horas)
→ Usa agente `shadow-tester` para validar resultados

---

## 🆘 Troubleshooting Rápido

**Problema:** Agente no encuentra archivos
```bash
# Solución: Verifica rutas absolutas
pwd  # Debe estar en: /home/ljham/.../phantomx-nexus/
ls sql/extracted/  # Debe listar archivos .sql
```

**Problema:** No se generan outputs
```bash
# Solución: Crea directorios manualmente
mkdir -p knowledge/{json,markdown,classification}/batch_001
```

**Problema:** Clasificación incorrecta
```
# Solución: Revisa razonamiento en Markdown
cat knowledge/markdown/batch_001/obj_001_*.md
# Verifica sección "Classification"
```

**Problema:** Agente timeout
```
# Solución: Reduce batch size
# En lugar de 10 objetos, usa 5 objetos por agente
```

---

## 📚 Documentación Completa

- **Guía completa:** `.claude/plugins/oracle-postgres-migration/README.md`
- **Ejemplo FASE 1:** `examples/phase1_launch_example.md`
- **Estrategia completa:** `.claude/ESTRATEGIA_MIGRACION.md`
- **Decisiones técnicas:** `.claude/sessions/oracle-postgres-migration/04_decisions.md`

---

## 🎯 Meta de Hoy

**Objetivo:** Completar FASE 1 (8,122 objetos analizados)
**Timeline:** 5 horas
**Resultado:** Clasificación SIMPLE/COMPLEX lista para FASE 2

**¡Adelante! 🚀**
