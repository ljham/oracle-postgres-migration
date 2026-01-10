---
name: migrate-status
description: Mostrar estado actual de la migración y progreso por fases
arguments:
  - name: phase
    description: "Mostrar detalle de fase específica: '1', '2', '3', '4', o 'all' (default: all)"
    required: false
    default: "all"
---

# Comando: /migrate-status

Muestra el **estado completo de la migración** Oracle → PostgreSQL.

## Uso

```bash
/migrate-status           # Muestra progreso de todas las fases
/migrate-status 1         # Muestra solo Fase 1 (Análisis)
/migrate-status 2         # Muestra solo Fase 2 (Conversión)
/migrate-status 3         # Muestra solo Fase 3 (Validación)
/migrate-status 4         # Muestra solo Fase 4 (Testing)
```

## Lo que muestra

### Resumen General
- Total de objetos: 8,122
- Progreso global: XX%
- Fase actual: X
- Tiempo estimado restante: X horas

### Fase 1: Análisis (5 horas)
- ✅ Objetos analizados: X / 8,122 (XX%)
- ✅ Clasificados como SIMPLE: X (XX%)
- ✅ Clasificados como COMPLEX: X (XX%)
- 📊 Siguiente batch: XXX
- ⏱️ Tiempo transcurrido: X horas

### Fase 2A: Conversión Simple (30 min - LOCAL)
- ✅ Objetos convertidos con ora2pg: X / ~5,000 (XX%)
- 📁 Archivos generados: `migrated/simple/*.sql`
- ⚙️ Comando ejecutado: `bash scripts/convert_simple_objects.sh`

### Fase 2B: Conversión Compleja (5 horas)
- ✅ Objetos convertidos: X / ~3,122 (XX%)
- 📊 Estrategias aplicadas:
  - AUTONOMOUS_TRANSACTION: X objetos
  - UTL_HTTP: X objetos
  - UTL_FILE: X objetos
  - DBMS_SQL: X objetos
  - Otras: X objetos
- 📁 Archivos generados: `migrated/complex/*.sql`
- 📊 Siguiente batch: XXX

### Fase 3: Validación (5 horas)
- ✅ Objetos validados: X / 8,122 (XX%)
- ✅ Compilación exitosa: X (XX%)
- ❌ Errores de compilación: X (XX%)
- 📊 Tipos de errores comunes:
  1. Error tipo A: X casos
  2. Error tipo B: X casos
  3. Error tipo C: X casos
- 📊 Siguiente batch: XXX

### Fase 4: Shadow Testing (10 horas)
- ✅ Objetos testeados: X / 8,122 (XX%)
- ✅ Resultados idénticos: X (XX%)
- ⚠️ Diferencias encontradas: X (XX%)
- 📊 Tipos de diferencias:
  - Precisión numérica: X casos
  - Formato fecha/hora: X casos
  - Diferencias funcionales: X casos
- 📊 Siguiente batch: XXX

---

**PROMPT DE EJECUCIÓN:**

Voy a mostrar el **estado actual de la migración** leyendo los archivos de progreso.

**Fase solicitada:** {{phase}}

**Pasos que realizaré:**

1. **Leer archivos de estado**
   ```bash
   # Progress general
   cat sql/extracted/progress.json

   # Clasificación (Fase 1)
   test -f classification/simple_objects.txt && wc -l classification/simple_objects.txt
   test -f classification/complex_objects.txt && wc -l classification/complex_objects.txt

   # Conversión simple (Fase 2A)
   test -d migrated/simple/ && find migrated/simple/ -name "*.sql" | wc -l

   # Conversión compleja (Fase 2B)
   test -d migrated/complex/ && find migrated/complex/ -name "*.sql" | wc -l

   # Validación (Fase 3)
   test -f compilation_results/summary.json && cat compilation_results/summary.json

   # Shadow testing (Fase 4)
   test -f shadow_tests/summary.json && cat shadow_tests/summary.json
   ```

2. **Calcular estadísticas**
   - Progreso por fase (%)
   - Tiempo transcurrido (basándome en timestamps)
   - Tiempo estimado restante
   - Siguiente batch recomendado para cada fase

3. **Generar visualización**

   {{#if (eq phase "all")}}
   **Progreso General:**
   ```
   ████████████████████░░░░░░░░  65% (5,279 / 8,122 objetos)

   Fase 1: ████████████████████ 100% ✅ COMPLETA
   Fase 2: ███████████████░░░░░  75% 🔄 EN PROGRESO
   Fase 3: ██████░░░░░░░░░░░░░░  30% ⏳ PENDIENTE
   Fase 4: ░░░░░░░░░░░░░░░░░░░░   0% ⏳ PENDIENTE
   ```
   {{/if}}

4. **Mostrar siguiente acción recomendada**

   Basándome en el estado actual, recomendaré:
   - Si Fase 1 incompleta → Ejecutar `/migrate-analyze next`
   - Si Fase 1 completa y Fase 2A no ejecutada → Ejecutar `bash scripts/convert_simple_objects.sh`
   - Si Fase 2A completa y Fase 2B incompleta → Ejecutar `/migrate-convert next`
   - Si Fase 2 completa y Fase 3 incompleta → Ejecutar `/migrate-validate next`
   - Si Fase 3 >95% éxito y Fase 4 incompleta → Ejecutar `/migrate-test next`
   - Si Fase 4 >95% match → **¡MIGRACIÓN COMPLETA!** 🎉

5. **Detectar problemas**
   - ⚠️ Fase 3 con <95% éxito → Recomendar revisar errores
   - ⚠️ Fase 4 con <95% match → Recomendar investigar diferencias
   - ⚠️ Archivos faltantes → Recomendar ejecutar `prepare_migration.py`

**Archivos leídos:**
- `sql/extracted/progress.json` - Progreso general
- `sql/extracted/manifest.json` - Índice de objetos
- `classification/*.txt` - Resultados de Fase 1
- `migrated/simple/*.sql` - Resultados de Fase 2A
- `migrated/complex/*.sql` - Resultados de Fase 2B
- `compilation_results/summary.json` - Resultados de Fase 3
- `shadow_tests/summary.json` - Resultados de Fase 4

Mostrando estado...
