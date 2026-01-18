---
name: migrate-convert
description: Convertir objetos PL/SQL (SIMPLE o COMPLEX) a PostgreSQL usando plsql-converter
arguments:
  - name: batch
    description: "Número de batch a procesar (ej: 001, 002, ...) o 'next' para siguiente pendiente"
    required: false
    default: "next"
  - name: count
    description: "Cantidad de objetos a procesar en paralelo (default: 200 = 20 agentes × 10 objetos)"
    required: false
    default: "200"
  - name: complexity
    description: "Tipo de objetos: 'simple' o 'complex' (default: simple)"
    required: false
    default: "simple"
---

# Comando: /migrate-convert

Ejecuta la **Fase 2: Conversión de Objetos PL/SQL a PostgreSQL** usando procesamiento paralelo con 20 sub-agentes.

## Uso

```bash
/migrate-convert                           # Procesa siguiente batch de objetos SIMPLE (200 objetos)
/migrate-convert 002                       # Procesa batch_002 específico
/migrate-convert next 100 simple           # Procesa 100 objetos SIMPLE del siguiente batch
/migrate-convert next 200 complex          # Procesa objetos COMPLEX
```

## Pre-requisitos

- ✅ **Fase 1 completada** (análisis y clasificación con /migrate-analyze)
- ✅ Archivo `classification/simple_objects.txt` o `complex_objects.txt` debe existir según complexity

## Lo que hace este comando

1. **Lee objetos** de `classification/simple_objects.txt` o `complex_objects.txt`
2. **Divide en 20 sub-agentes paralelos** (cada uno procesa 10 objetos)
3. **Invoca el agente plsql-converter** para cada sub-lote
4. **Genera código PostgreSQL** con sintaxis correcta y minimalista
5. **Crea script de compilación consolidado** para el batch completo

## Características clave

- **Procesamiento paralelo**: 20 sub-agentes simultáneos para máxima eficiencia
- **Filosofía minimalista**: Solo genera archivos SQL + 1 script de compilación
- **Sintaxis PostgreSQL correcta**: Sin comillas, minúsculas, sin (+), sin WITH READ ONLY
- **Aplicación automática de reglas**: El agente plsql-converter tiene reglas incorporadas

## Estructura de salida

```
sql/migrated/
├── simple/                              # Para objetos SIMPLE
│   ├── views/
│   │   ├── obj_9346_COM_V_CONVENIOS.sql
│   │   └── ...
│   ├── functions/
│   └── compile_batch_XXX.sql           # Script consolidado
└── complex/                             # Para objetos COMPLEX
    ├── packages/
    ├── procedures/
    └── compile_batch_XXX.sql
```

---

**PROMPT DE EJECUCIÓN:**

Voy a ejecutar la **Fase 2: Conversión de Objetos PL/SQL a PostgreSQL** usando el agente `plsql-converter` con procesamiento paralelo.

**Configuración:**
- Batch: {{batch}}
- Objetos a procesar: {{count}}
- Complejidad: {{complexity}}
- Arquitectura: 20 sub-agentes en paralelo (cada uno procesa {{count}}/20 objetos)

**Pasos que realizaré:**

1. **Verificar pre-requisitos**
   ```bash
   # Verificar que Fase 1 está completa
   test -f knowledge/classification/{{complexity}}_objects.txt || echo "ERROR: Archivo de clasificación no encontrado"

   # Verificar manifest
   test -f sql/extracted/manifest.json || echo "ERROR: Manifest no encontrado"
   ```

2. **Cargar objetos a convertir**
   - Leer `knowledge/classification/{{complexity}}_objects.txt`
   - Si batch = "next", determinar automáticamente siguiente batch pendiente
   - Calcular rango exacto de objetos (ej: objetos 101-300 para batch_002)

3. **Procesar batch con 20 sub-agentes paralelos**

   Lanzaré **20 invocaciones simultáneas del Task tool** con `subagent_type: "oracle-postgres-migration:plsql-converter"`:

   - **Sub-agente 1**: Procesa objetos 1-10 del batch
   - **Sub-agente 2**: Procesa objetos 11-20 del batch
   - **Sub-agente 3**: Procesa objetos 21-30 del batch
   - ...
   - **Sub-agente 20**: Procesa objetos 191-200 del batch

   Cada sub-agente:
   - Lee código fuente de `sql/extracted/` usando manifest.json
   - Aplica reglas de conversión PostgreSQL automáticamente
   - Genera archivos SQL en `sql/migrated/{{complexity}}/`
   - Sigue filosofía minimalista (solo SQL, sin logs innecesarios)

4. **Generar script de compilación consolidado**

   Después de completar todos los sub-agentes, crearé:
   - `sql/migrated/{{complexity}}/compile_batch_{{batch}}.sql`
   - Contiene instrucciones psql para compilar todos los objetos del batch

5. **Mostrar resumen**
   - Total objetos convertidos: X de {{count}}
   - Archivos SQL generados
   - Script de compilación: ruta completa
   - Siguiente batch recomendado (si aplica)
   - Instrucciones de compilación en PostgreSQL

**Contexto del agente plsql-converter:**

El agente tiene incorporadas:
- ✅ Reglas de sintaxis PostgreSQL (sin comillas, minúsculas, sin (+), etc.)
- ✅ Filosofía minimalista MENOS ES MÁS
- ✅ Conocimiento de AWS Aurora PostgreSQL 17.4
- ✅ Estrategias para características Oracle específicas

¿Procedo con la conversión del batch {{batch}} ({{complexity}})?
