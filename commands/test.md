---
name: test
description: Ejecutar shadow testing comparativo entre Oracle y PostgreSQL
arguments:
  - name: batch
    description: "Número de batch a testear (ej: 001, 002, ...) o 'next' para siguiente pendiente"
    required: false
    default: "next"
  - name: count
    description: "Cantidad de objetos a testear en paralelo (default: 50)"
    required: false
    default: "50"
  - name: mode
    description: "Modo de testing: 'unit' (pruebas unitarias), 'integration' (pruebas de integración), o 'both' (default: both)"
    required: false
    default: "both"
---

# Comando: /test

Ejecuta la **Fase 4: Shadow Testing Comparativo** Oracle vs PostgreSQL.

## Uso

```bash
/test                       # Testea siguiente batch pendiente (50 objetos)
/test 001                   # Testea batch específico
/test next 20 unit          # Testea 20 objetos (solo pruebas unitarias)
/test all 10 integration    # Testea todos los objetos (solo integración)
```

## Pre-requisitos

- ✅ **Fase 3 completada** con >95% compilación exitosa
- ✅ **Oracle 19c accesible** (para comparación)
- ✅ **PostgreSQL 17.4 accesible**
- ✅ **Datos de prueba disponibles** (opcionalmente)

## Variables de Entorno Requeridas

### PostgreSQL
```bash
export PGHOST=your-aurora-endpoint.amazonaws.com
export PGPORT=5432
export PGDATABASE=phantomx
export PGUSER=postgres
export PGPASSWORD=your-password
```

### Oracle
```bash
export ORACLE_HOST=your-oracle-host.com
export ORACLE_PORT=1521
export ORACLE_SID=ORCL
export ORACLE_USER=system
export ORACLE_PASSWORD=your-password
```

## Lo que hace este comando

1. **Ejecuta objetos en Oracle** con inputs de prueba
2. **Ejecuta mismos objetos en PostgreSQL** con mismos inputs
3. **Compara resultados** (valores, tipos, errores)
4. **Genera reportes de diferencias**

## Estructura de salida

```
shadow_tests/
├── results/
│   ├── batch_001_obj_001.json     # Comparación Oracle vs PostgreSQL
│   └── ...
├── mismatches/
│   ├── batch_001_obj_050.md       # Diferencias encontradas
│   └── ...
└── summary.json                   # Resumen de resultados
```

---

**PROMPT DE EJECUCIÓN:**

Voy a ejecutar la **Fase 4: Shadow Testing Comparativo** usando el agente `shadow-tester`.

**Configuración:**
- Batch: {{batch}}
- Objetos en paralelo: {{count}}
- Modo: {{mode}}

**Pasos que realizaré:**

1. **Verificar pre-requisitos**
   ```bash
   # Verificar conexión a Oracle
   sqlplus -s $ORACLE_USER/$ORACLE_PASSWORD@$ORACLE_HOST:$ORACLE_PORT/$ORACLE_SID <<< "SELECT banner FROM v\$version;" || echo "ERROR: No se puede conectar a Oracle"

   # Verificar conexión a PostgreSQL
   psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c "SELECT version();" || echo "ERROR: No se puede conectar a PostgreSQL"

   # Verificar objetos compilados exitosamente
   test -d compilation_results/success/ || echo "ERROR: Fase 3 no completada"
   ```

2. **Cargar objetos a testear**
   - Leer archivos de `compilation_results/success/`
   - Determinar rango para el batch {{batch}}
   - Cargar metadata de análisis (Fase 1) para generar inputs de prueba

3. **Invocar agente shadow-tester**

   Usaré el Tool `Task` con estas especificaciones:
   - `subagent_type`: "shadow-tester"
   - `prompt`: Incluir batch, objetos, credenciales Oracle + PostgreSQL
   - `description`: "Shadow testing batch {{batch}}"

   El agente creará automáticamente:
   - {{count}} sub-agentes en paralelo (menos que otras fases por complejidad)
   - Conexiones duales (Oracle + PostgreSQL)
   - Generación de inputs de prueba basados en signatures
   - Ejecución y comparación de resultados

4. **Tipos de comparaciones**

   {{#if (or (eq mode "unit") (eq mode "both"))}}
   **Unit Testing:**
   - Ejecutar funciones/procedimientos con inputs sintéticos
   - Comparar valores de retorno
   - Comparar excepciones lanzadas
   - Comparar efectos secundarios (inserts, updates, deletes)
   {{/if}}

   {{#if (or (eq mode "integration") (eq mode "both"))}}
   **Integration Testing:**
   - Ejecutar flujos completos (múltiples objetos encadenados)
   - Comparar resultados finales
   - Verificar consistencia transaccional
   - Medir diferencias de performance
   {{/if}}

5. **Analizar resultados**
   ```bash
   # Contar matches vs mismatches
   match_count=$(find shadow_tests/results/ -name "*.json" | xargs grep -l '"status":"MATCH"' | wc -l)
   mismatch_count=$(find shadow_tests/mismatches/ -name "*.md" | wc -l)

   # Generar summary.json
   python scripts/generate_shadow_summary.py
   ```

6. **Mostrar resumen**
   - **Resultados idénticos:** X objetos (XX%)
   - **Diferencias encontradas:** Y objetos (YY%)
   - **Tipos de diferencias:**
     - Diferencias de precisión numérica: Z casos
     - Diferencias de formato fecha/hora: W casos
     - Diferencias funcionales: V casos
   - **Siguiente acción:**
     - Si >95% match → **MIGRACIÓN EXITOSA** ✅
     - Si <95% match → Investigar diferencias y ajustar conversión

**Estrategias de manejo de diferencias:**

- **Precisión numérica:** Usar ROUND() para normalizar
- **Formatos de fecha:** Usar TO_CHAR() consistente
- **Diferencias aceptables:** Documentar y aprobar
- **Diferencias críticas:** Revisar conversión (volver a Fase 2B)

**Performance Benchmarking (opcional):**

El agente puede medir:
- Tiempo de ejecución Oracle vs PostgreSQL
- Uso de memoria
- Planes de ejecución (EXPLAIN)
- Identificar oportunidades de optimización

¿Procedo con el shadow testing del batch {{batch}}?
