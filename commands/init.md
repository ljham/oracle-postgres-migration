---
name: init
description: Inicializar proyecto de migración (generar manifest, progress y estructura de directorios)
arguments:
  - name: force
    description: "Regenerar archivos existentes (default: false)"
    required: false
    default: "false"
---

# Comando: /init

Inicializa el **proyecto de migración** Oracle → PostgreSQL.

## Uso

```bash
/init              # Configuración inicial (solo si no existe)
/init force        # Regenerar todo (sobrescribir existente)
```

## Pre-requisitos

- ✅ Archivos fuente en `sql/extracted/*.sql`
- ✅ Python 3.8+ instalado
- ✅ Script `scripts/prepare_migration.py` disponible

## Lo que hace este comando

1. **Verifica archivos fuente** en `sql/extracted/`
2. **Ejecuta `prepare_migration.py`** para generar manifest y progress
3. **Crea estructura de directorios** necesaria
4. **Valida configuración** completa

## Estructura Generada

```
phantomx-nexus/                     ← Proyecto del usuario
├── sql/extracted/
│   ├── functions.sql               ← Fuente Oracle (requerido)
│   ├── procedures.sql              ← Fuente Oracle (requerido)
│   ├── packages_spec.sql           ← Fuente Oracle (requerido)
│   ├── packages_body.sql           ← Fuente Oracle (requerido)
│   ├── triggers.sql                ← Fuente Oracle (requerido)
│   ├── manifest.json               ← ✨ GENERADO
│   └── progress.json               ← ✨ GENERADO
├── knowledge/                      ← ✨ CREADO
│   ├── json/
│   ├── markdown/
│   └── classification/
├── migrated/                       ← ✨ CREADO
│   ├── simple/
│   └── complex/
├── compilation_results/            ← ✨ CREADO
│   ├── success/
│   └── errors/
└── shadow_tests/                   ← ✨ CREADO
    ├── results/
    └── mismatches/
```

## Validaciones Ejecutadas

- ✅ Archivos fuente existen y son legibles
- ✅ Total de objetos detectados: ~8,122
- ✅ Manifest generado correctamente
- ✅ Progress inicializado en 0
- ✅ Directorios creados con permisos correctos

---

**PROMPT DE EJECUCIÓN:**

Voy a **inicializar el proyecto de migración** ejecutando la preparación completa.

**Modo:** {{#if (eq force "true")}}FORCE (regenerar todo){{else}}NORMAL (solo si no existe){{/if}}

**Pasos que realizaré:**

1. **Verificar ubicación actual**
   ```bash
   pwd
   # Debe ser el directorio del proyecto (ej: phantomx-nexus/)
   # NO debe ser el directorio del plugin
   ```

2. **Verificar archivos fuente**
   ```bash
   # Verificar que existen archivos SQL de Oracle
   required_files=(
     "sql/extracted/functions.sql"
     "sql/extracted/procedures.sql"
     "sql/extracted/packages_spec.sql"
     "sql/extracted/packages_body.sql"
     "sql/extracted/triggers.sql"
   )

   for file in "${required_files[@]}"; do
     test -f "$file" || echo "ERROR: Falta archivo $file"
   done
   ```

3. **Copiar script de preparación** (si no existe)
   ```bash
   # El script está incluido en el plugin instalado
   # Copiar al proyecto del usuario si no existe
   if [ ! -f scripts/prepare_migration.py ]; then
     mkdir -p scripts
     cp ~/.claude/plugins/oracle-postgres-migration/scripts/prepare_migration.py scripts/
     echo "✅ Script copiado: scripts/prepare_migration.py"
   fi
   ```

4. **Ejecutar preparación**

   {{#if (eq force "true")}}
   ```bash
   # Modo FORCE: Regenerar todo
   python scripts/prepare_migration.py --force
   ```
   {{else}}
   ```bash
   # Modo NORMAL: Solo si no existe
   if [ -f sql/extracted/manifest.json ]; then
     echo "⚠️ Manifest ya existe. Usar /init force para regenerar."
   else
     python scripts/prepare_migration.py
   fi
   ```
   {{/if}}

   El script:
   - Lee todos los archivos SQL en `sql/extracted/`
   - Extrae definiciones de objetos (CREATE FUNCTION, CREATE PROCEDURE, etc.)
   - Genera `manifest.json` con índice completo:
     ```json
     {
       "total_objects": 8122,
       "objects": [
         {
           "id": "obj_0001",
           "name": "CALCULATE_TOTAL",
           "type": "FUNCTION",
           "source_file": "functions.sql",
           "line_start": 1,
           "line_end": 50,
           "complexity": "SIMPLE"
         },
         ...
       ]
     }
     ```
   - Genera `progress.json` con estado inicial:
     ```json
     {
       "total_objects": 8122,
       "processed_count": 0,
       "phases": {
         "1_analysis": {"completed": 0, "total": 8122},
         "2_conversion": {"completed": 0, "total": 8122},
         "3_validation": {"completed": 0, "total": 8122},
         "4_testing": {"completed": 0, "total": 8122}
       },
       "last_updated": "2025-01-07T10:00:00Z"
     }
     ```

5. **Crear estructura de directorios**
   ```bash
   # El script crea automáticamente:
   mkdir -p knowledge/{json,markdown,classification}
   mkdir -p migrated/{simple,complex}
   mkdir -p compilation_results/{success,errors}
   mkdir -p shadow_tests/{results,mismatches}

   echo "✅ Estructura de directorios creada"
   ```

6. **Validar configuración**
   ```bash
   # Verificar que todo se creó correctamente
   echo "Validando configuración..."

   # Verificar manifest
   test -f sql/extracted/manifest.json && echo "✅ Manifest generado"
   total=$(jq '.total_objects' sql/extracted/manifest.json)
   echo "   Total objetos detectados: $total"

   # Verificar progress
   test -f sql/extracted/progress.json && echo "✅ Progress inicializado"

   # Verificar directorios
   for dir in knowledge migrated compilation_results shadow_tests; do
     test -d "$dir" && echo "✅ Directorio $dir creado"
   done
   ```

7. **Mostrar resumen**
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

**Troubleshooting:**

Si encuentro problemas:
- **Error:** `sql/extracted/ no existe`
  - **Solución:** Crear directorio y colocar archivos SQL de Oracle

- **Error:** `prepare_migration.py no encuentra objetos`
  - **Solución:** Verificar formato de archivos SQL (deben tener CREATE FUNCTION, etc.)

- **Error:** `Permisos insuficientes`
  - **Solución:** Ejecutar con permisos de escritura en el directorio

¿Procedo con la inicialización del proyecto?
