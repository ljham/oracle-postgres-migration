---
name: migrate-validate
description: Validar compilación de objetos migrados en PostgreSQL 17.4
arguments:
  - name: batch
    description: "Número de batch a validar (ej: 001, 002, ...) o 'next' para siguiente pendiente"
    required: false
    default: "next"
  - name: count
    description: "Cantidad de objetos a validar en paralelo (default: 200)"
    required: false
    default: "200"
  - name: type
    description: "Tipo de objetos a validar: 'simple', 'complex', o 'all' (default: all)"
    required: false
    default: "all"
---

# Comando: /migrate-validate

Ejecuta la **Fase 3: Validación de Compilación** en PostgreSQL 17.4.

## Uso

```bash
/migrate-validate                    # Valida siguiente batch pendiente (todos los tipos)
/migrate-validate 001                # Valida batch específico
/migrate-validate next 100 complex   # Valida solo objetos complejos
/migrate-validate all 50 simple      # Valida todos los objetos simples (batches de 50)
```

## Pre-requisitos

- ✅ **Fase 2A y 2B completadas** (conversión)
- ✅ **PostgreSQL 17.4 accesible** (variables de entorno configuradas)
- ✅ Archivos en `migrated/simple/` y/o `migrated/complex/`

## Variables de Entorno Requeridas

```bash
export PGHOST=your-aurora-endpoint.amazonaws.com
export PGPORT=5432
export PGDATABASE=phantomx
export PGUSER=postgres
export PGPASSWORD=your-password
export PGSSLMODE=require
```

## Lo que hace este comando

1. **Verifica conexión a PostgreSQL**
2. **Carga scripts SQL migrados** (simple y/o complex según filtro)
3. **Invoca el agente compilation-validator**
4. **Ejecuta compilación en PostgreSQL** y captura errores
5. **Genera reportes de éxito/error**

## Estructura de salida

```
compilation_results/
├── success/
│   ├── batch_001_obj_001.log      # Compilación exitosa
│   └── ...
├── errors/
│   ├── batch_001_obj_050.log      # Errores de compilación
│   └── ...
└── summary.json                   # Resumen de resultados
```

---

**PROMPT DE EJECUCIÓN:**

Voy a ejecutar la **Fase 3: Validación de Compilación** usando el agente `compilation-validator`.

**Configuración:**
- Batch: {{batch}}
- Objetos en paralelo: {{count}}
- Tipo: {{type}}

**Pasos que realizaré:**

1. **Verificar pre-requisitos**
   ```bash
   # Verificar conexión a PostgreSQL
   psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c "SELECT version();" || echo "ERROR: No se puede conectar a PostgreSQL"

   # Verificar extensiones necesarias
   psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c "SELECT * FROM pg_extension WHERE extname IN ('vector', 'pg_cron', 'dblink');"

   # Verificar archivos migrados
   test -d migrated/ || echo "ERROR: Fase 2 no completada"
   ```

2. **Cargar scripts a validar**
   {{#if (eq type "simple")}}
   - Leer solo archivos de `migrated/simple/`
   {{else if (eq type "complex")}}
   - Leer solo archivos de `migrated/complex/`
   {{else}}
   - Leer archivos de ambos directorios
   {{/if}}
   - Determinar rango para el batch {{batch}}

3. **Invocar agente compilation-validator**

   Usaré el Tool `Task` con estas especificaciones:
   - `subagent_type`: "compilation-validator"
   - `prompt`: Incluir batch, archivos SQL, credenciales PostgreSQL
   - `description`: "Validar batch {{batch}}"

   El agente creará automáticamente:
   - 20 sub-agentes en paralelo
   - Conexiones independientes a PostgreSQL
   - Ejecución de scripts SQL con captura de errores
   - Clasificación de resultados (success/errors)

4. **Analizar resultados**
   ```bash
   # Contar éxitos y errores
   success_count=$(find compilation_results/success/ -name "*.log" | wc -l)
   error_count=$(find compilation_results/errors/ -name "*.log" | wc -l)

   # Generar summary.json
   python scripts/generate_validation_summary.py
   ```

5. **Mostrar resumen**
   - **Compilación exitosa:** X objetos (XX%)
   - **Errores de compilación:** Y objetos (YY%)
   - **Errores comunes:** Top 5 tipos de errores
   - **Siguiente acción:**
     - Si >95% éxito → Proceder a Fase 4 (shadow testing)
     - Si <95% éxito → Revisar errores y re-convertir objetos problemáticos

**Tipos de errores esperados:**

- **Sintaxis:** Diferencias PL/SQL vs PL/pgSQL
- **Tipos de datos:** NUMBER vs NUMERIC, DATE vs TIMESTAMP
- **Funciones:** Funciones Oracle sin equivalente directo
- **Privilegios:** Permisos faltantes en PostgreSQL
- **Dependencias:** Objetos referenciados no migrados

¿Procedo con la validación del batch {{batch}}?
