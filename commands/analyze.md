---
name: analyze
description: Analizar objetos PL/SQL de Oracle y clasificarlos en SIMPLE/COMPLEX
arguments:
  - name: batch
    description: "Número de batch a procesar (ej: 001, 002, ...) o 'next' para siguiente pendiente"
    required: false
    default: "next"
  - name: count
    description: "Cantidad de objetos a procesar en paralelo (default: 200)"
    required: false
    default: "200"
---

# Comando: /analyze

Ejecuta la **Fase 1: Análisis y Clasificación** de objetos PL/SQL.

## Uso

```bash
/analyze                    # Procesa siguiente batch pendiente (200 objetos)
/analyze 001                # Procesa batch específico
/analyze next 100           # Procesa siguiente batch con 100 objetos
```

## Lo que hace este comando

1. **Verifica progreso actual** leyendo `sql/extracted/progress.json`
2. **Determina siguiente batch** a procesar (o usa el especificado)
3. **Invoca el agente plsql-analyzer** con la configuración correcta
4. **Procesa múltiples objetos en paralelo** usando sub-agentes

## Estructura de salida

```
knowledge/
├── json/
│   ├── batch_001_obj_001.json
│   ├── batch_001_obj_002.json
│   └── ...
├── markdown/
│   ├── batch_001_obj_001.md
│   └── ...
└── classification/
    ├── simple_objects.txt
    └── complex_objects.txt
```

---

**PROMPT DE EJECUCIÓN:**

Voy a ejecutar la **Fase 1: Análisis de objetos PL/SQL** usando el agente `plsql-analyzer`.

**Configuración:**
- Batch: {{batch}}
- Objetos en paralelo: {{count}}

**Pasos que realizaré:**

1. **Verificar estado actual**
   ```bash
   python scripts/update_progress.py --check
   ```

2. **Determinar objetos a procesar**
   - Leer `sql/extracted/progress.json` para encontrar objetos pendientes
   - Si batch = "next", seleccionar automáticamente siguiente batch
   - Determinar rango exacto de objetos basándome en manifest.json

3. **Invocar agente plsql-analyzer**

   Usaré el Tool `Task` con estas especificaciones:
   - `subagent_type`: "plsql-analyzer" (del registro de agentes del plugin)
   - `prompt`: Indicar batch específico, rango de objetos, y archivos fuente
   - `description`: "Analizar batch {{batch}}"

   El agente creará automáticamente:
   - 20 sub-agentes en paralelo (cada uno procesa 10 objetos)
   - Archivos JSON en `knowledge/json/`
   - Archivos Markdown en `knowledge/markdown/`
   - Actualización de `classification/simple_objects.txt` y `complex_objects.txt`

4. **Actualizar progreso**
   ```bash
   python scripts/update_progress.py --update
   ```

5. **Mostrar resumen**
   - Objetos procesados en este batch
   - Objetos clasificados como SIMPLE vs COMPLEX
   - Progreso total (X de 8,122 objetos completados)
   - Siguiente batch recomendado

¿Procedo con el análisis del batch {{batch}}?
