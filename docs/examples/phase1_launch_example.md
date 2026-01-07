# FASE 1: Ejemplo de Lanzamiento - Análisis y Clasificación

**Objetivo:** Analizar 8,122 objetos PL/SQL y clasificarlos en SIMPLE vs COMPLEX

**Timeline:** 5 horas (1 sesión)
**Agentes:** 20 en paralelo
**Objetos por mensaje:** 200 (20 agentes × 10 objetos cada uno)
**Mensajes necesarios:** 42 mensajes para completar 8,122 objetos

---

## Pre-requisitos

1. **Archivos Oracle extraídos:**
   ```bash
   ls sql/extracted/
   # Debe contener:
   # - functions.sql (146 objetos)
   # - procedures.sql (196 objetos)
   # - packages_spec.sql (569 objetos)
   # - packages_body.sql (569 objetos)
   # - triggers.sql (87 objetos)
   ```

2. **Estructura de directorios creada:**
   ```bash
   mkdir -p knowledge/{json,markdown,classification}
   mkdir -p knowledge/json/{batch_001..batch_050}
   mkdir -p knowledge/markdown/{batch_001..batch_050}
   ```

3. **Plugin cargado:**
   - El plugin `oracle-postgres-migration` debe estar en `.claude/plugins/`
   - Claude Code lo detectará automáticamente

---

## Estrategia de Lanzamiento

### Opción 1: Lanzar 20 agentes en un solo mensaje (RECOMENDADO)

**En Claude Code CLI o Web, escribe:**

```
Necesito analizar los primeros 200 objetos PL/SQL usando el agente plsql-analyzer.

Lanza 20 agentes en paralelo, cada uno procesando 10 objetos:

Batch 1: Task plsql-analyzer "Analyze objects 1-10 from sql/extracted/functions.sql (lines 1-500)"
Batch 2: Task plsql-analyzer "Analyze objects 11-20 from sql/extracted/functions.sql (lines 501-1000)"
Batch 3: Task plsql-analyzer "Analyze objects 21-30 from sql/extracted/functions.sql (lines 1001-1500)"
... (continuar hasta batch 20)

Cada agente debe:
1. Leer el código fuente PL/SQL
2. Comprender la lógica de negocio (no solo sintaxis)
3. Extraer reglas de negocio, validaciones, flujos
4. Detectar features Oracle-específicas (AUTONOMOUS_TRANSACTION, UTL_HTTP, etc.)
5. Clasificar como SIMPLE o COMPLEX con razonamiento
6. Generar outputs en knowledge/json/batch_XXX/ y knowledge/markdown/batch_XXX/
7. Agregar a classification/simple_objects.txt o complex_objects.txt

Genera summary.json al final con estadísticas del batch.
```

**Resultado esperado:** 20 agentes trabajando simultáneamente, completando 200 objetos en ~15-20 minutos.

---

### Opción 2: Dividir por tipo de objeto

**Funciones (146 objetos):**
```
Task plsql-analyzer "Analyze all functions from sql/extracted/functions.sql"
```

**Procedimientos (196 objetos):**
```
Task plsql-analyzer "Analyze all procedures from sql/extracted/procedures.sql"
```

**Packages (1,138 objetos - 569 specs + 569 bodies):**
```
# Dividir en múltiples batches (20 agentes por mensaje)
Task plsql-analyzer "Analyze package bodies batch 1: objects 1-200"
Task plsql-analyzer "Analyze package bodies batch 2: objects 201-400"
...
```

---

## Ejemplo Completo - Primer Mensaje

**Prompt para Claude Code:**

```markdown
# FASE 1 - Análisis de Objetos PL/SQL: Batch 1

Usa el agente `plsql-analyzer` para analizar los primeros 200 objetos PL/SQL de Oracle.

## Instrucciones

Lanza **20 agentes en paralelo** (un solo mensaje con 20 Task calls), cada uno procesando **10 objetos**:

### Functions (objetos 1-100)
- Task plsql-analyzer "Analyze functions 1-10 from sql/extracted/functions.sql"
- Task plsql-analyzer "Analyze functions 11-20 from sql/extracted/functions.sql"
- Task plsql-analyzer "Analyze functions 21-30 from sql/extracted/functions.sql"
- Task plsql-analyzer "Analyze functions 31-40 from sql/extracted/functions.sql"
- Task plsql-analyzer "Analyze functions 41-50 from sql/extracted/functions.sql"
- Task plsql-analyzer "Analyze functions 51-60 from sql/extracted/functions.sql"
- Task plsql-analyzer "Analyze functions 61-70 from sql/extracted/functions.sql"
- Task plsql-analyzer "Analyze functions 71-80 from sql/extracted/functions.sql"
- Task plsql-analyzer "Analyze functions 81-90 from sql/extracted/functions.sql"
- Task plsql-analyzer "Analyze functions 91-100 from sql/extracted/functions.sql"

### Procedures (objetos 101-200)
- Task plsql-analyzer "Analyze procedures 1-10 from sql/extracted/procedures.sql"
- Task plsql-analyzer "Analyze procedures 11-20 from sql/extracted/procedures.sql"
- Task plsql-analyzer "Analyze procedures 21-30 from sql/extracted/procedures.sql"
- Task plsql-analyzer "Analyze procedures 31-40 from sql/extracted/procedures.sql"
- Task plsql-analyzer "Analyze procedures 41-50 from sql/extracted/procedures.sql"
- Task plsql-analyzer "Analyze procedures 51-60 from sql/extracted/procedures.sql"
- Task plsql-analyzer "Analyze procedures 61-70 from sql/extracted/procedures.sql"
- Task plsql-analyzer "Analyze procedures 71-80 from sql/extracted/procedures.sql"
- Task plsql-analyzer "Analyze procedures 81-90 from sql/extracted/procedures.sql"
- Task plsql-analyzer "Analyze procedures 91-100 from sql/extracted/procedures.sql"

## Outputs Esperados

Cada agente debe generar:
1. **JSON**: `knowledge/json/batch_001/obj_XXX_[nombre].json` (para pgvector)
2. **Markdown**: `knowledge/markdown/batch_001/obj_XXX_[nombre].md` (lectura humana)
3. **Clasificación**: Agregar a `classification/simple_objects.txt` o `complex_objects.txt`

Al finalizar el batch, genera:
- `knowledge/classification/batch_001_summary.json` con estadísticas

## Validación

Al terminar, verifica:
- 200 archivos JSON creados
- 200 archivos Markdown creados
- classification/*.txt actualizado con los 200 objetos
- summary.json muestra distribución SIMPLE/COMPLEX
```

---

## Progreso Esperado

### Después del primer mensaje (200 objetos):
```
knowledge/
├── json/batch_001/
│   ├── obj_001_FUNC_VALIDAR_EMAIL.json
│   ├── obj_002_FUNC_CALCULAR_EDAD.json
│   └── ... (198 más)
├── markdown/batch_001/
│   ├── obj_001_FUNC_VALIDAR_EMAIL.md
│   └── ... (199 más)
└── classification/
    ├── simple_objects.txt (ej: ~140 objetos)
    ├── complex_objects.txt (ej: ~60 objetos)
    └── batch_001_summary.json
```

### Después de 42 mensajes (8,122 objetos):
```
knowledge/
├── json/batch_001/ ... batch_042/
├── markdown/batch_001/ ... batch_042/
└── classification/
    ├── simple_objects.txt (~5,000 objetos)
    ├── complex_objects.txt (~3,122 objetos)
    └── global_summary.json
```

---

## Troubleshooting

**Problema 1: Agente no encuentra archivos**
```bash
# Verificar que extracted/ tiene los archivos
ls -lh sql/extracted/
```

**Problema 2: Outputs no se generan**
```bash
# Verificar permisos de escritura
chmod -R u+w knowledge/
```

**Problema 3: Clasificación incorrecta**
- Revisar `knowledge/markdown/` para ver razonamiento del agente
- Manualmente override en classification/*.txt si necesario

**Problema 4: Timeout de agente**
- Reducir batch de 10 a 5 objetos por agente
- Lanzar 10 agentes en lugar de 20

---

## Siguiente Paso

**Después de completar FASE 1:**
1. Revisar `classification/global_summary.json`
2. Validar distribución (esperado: ~70% SIMPLE, ~30% COMPLEX)
3. Proceder a **FASE 2A** (ora2pg para objetos SIMPLE)
4. Luego **FASE 2B** (plsql-converter para objetos COMPLEX)

Ver: `examples/phase2a_ora2pg.sh` y `examples/phase2b_launch_example.md`
