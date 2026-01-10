---
name: migrate-convert
description: Convertir objetos PL/SQL complejos a PostgreSQL usando estrategias arquitectónicas
arguments:
  - name: batch
    description: "Número de batch a procesar (ej: 001, 002, ...) o 'next' para siguiente pendiente"
    required: false
    default: "next"
  - name: count
    description: "Cantidad de objetos complejos a procesar en paralelo (default: 200)"
    required: false
    default: "200"
  - name: strategy
    description: "Filtrar por estrategia específica (opcional): AUTONOMOUS_TRANSACTION, UTL_HTTP, UTL_FILE, DBMS_SQL, etc."
    required: false
---

# Comando: /migrate-convert

Ejecuta la **Fase 2B: Conversión de Objetos Complejos** usando estrategias arquitectónicas.

## Uso

```bash
/migrate-convert                           # Procesa siguiente batch de objetos complejos
/migrate-convert 001                       # Procesa batch específico
/migrate-convert next 100                  # Procesa 100 objetos del siguiente batch
/migrate-convert next 50 UTL_HTTP          # Procesa solo objetos con estrategia UTL_HTTP
```

## Pre-requisitos

- ✅ **Fase 1 completada** (análisis y clasificación)
- ✅ **Fase 2A ejecutada** (ora2pg para objetos SIMPLE)
- ✅ Archivo `classification/complex_objects.txt` debe existir

## Lo que hace este comando

1. **Lee objetos complejos** de `classification/complex_objects.txt`
2. **Filtra por estrategia** (si se especifica)
3. **Invoca el agente plsql-converter** con contexto arquitectónico
4. **Genera código PostgreSQL** con estrategias específicas para cada patrón

## Estrategias Soportadas

- `AUTONOMOUS_TRANSACTION` → Usar `dblink` o reestructurar lógica
- `UTL_HTTP` → Reemplazar con AWS Lambda + API Gateway
- `UTL_FILE` → Reemplazar con S3 + presigned URLs
- `DBMS_SQL` → Convertir a SQL dinámico de PostgreSQL
- `DBMS_JOB` → Migrar a `pg_cron`
- `DBMS_OUTPUT` → Reemplazar con `RAISE NOTICE`
- `CUSTOM_TYPES` → Convertir a tipos compuestos de PostgreSQL

## Estructura de salida

```
migrated/
├── complex/
│   ├── batch_001_obj_050.sql      # Código convertido
│   ├── batch_001_obj_051.sql
│   └── ...
└── conversion_log/
    ├── batch_001_obj_050.md       # Log de decisiones
    └── ...
```

---

**PROMPT DE EJECUCIÓN:**

Voy a ejecutar la **Fase 2B: Conversión de Objetos Complejos** usando el agente `plsql-converter`.

**Configuración:**
- Batch: {{batch}}
- Objetos en paralelo: {{count}}
{{#if strategy}}
- Estrategia filtrada: {{strategy}}
{{/if}}

**Pasos que realizaré:**

1. **Verificar pre-requisitos**
   ```bash
   # Verificar que Fase 1 está completa
   test -f classification/complex_objects.txt || echo "ERROR: Fase 1 no completada"

   # Verificar que Fase 2A ejecutada
   test -d migrated/simple/ || echo "WARNING: Fase 2A no ejecutada (ora2pg)"
   ```

2. **Cargar objetos complejos**
   - Leer `classification/complex_objects.txt`
   - Filtrar por estrategia si se especificó
   - Determinar rango de objetos para el batch

3. **Invocar agente plsql-converter**

   Usaré el Tool `Task` con estas especificaciones:
   - `subagent_type`: "plsql-converter"
   - `prompt`: Incluir batch, rango, estrategias a aplicar
   - `description`: "Convertir batch {{batch}} objetos complejos"

   El agente creará automáticamente:
   - 20 sub-agentes en paralelo
   - Código SQL convertido en `migrated/complex/`
   - Logs de decisiones en `conversion_log/`
   - Aplicará estrategias arquitectónicas específicas

4. **Actualizar progreso**
   ```bash
   python scripts/update_progress.py --phase 2B --update
   ```

5. **Mostrar resumen**
   - Objetos convertidos en este batch
   - Estrategias aplicadas (distribución)
   - Código generado (líneas, archivos)
   - Siguiente batch recomendado

**Contexto arquitectónico clave:**

El agente tiene conocimiento de:
- AWS Aurora PostgreSQL 17.4 capabilities
- AWS Lambda para reemplazar UTL_HTTP
- S3 para reemplazar UTL_FILE
- Extensiones disponibles: pgvector, pg_cron, dblink
- Patrones de PostgreSQL modernos

¿Procedo con la conversión del batch {{batch}}?
