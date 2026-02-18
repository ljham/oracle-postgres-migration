# External Rules - Conocimiento de Conversión Oracle→PostgreSQL

<purpose>
Directorio con reglas, estrategias y ejemplos de conversión externalizados del agente `plsql-converter`.
Mantiene el agente optimizado (~520 líneas) externalizando conocimiento de referencia.
</purpose>

---

<files>

## Archivos Activos

### 1. `syntax-mapping.md` (~320 líneas)
**Contenido:** Mapeos sintácticos Oracle→PostgreSQL (errores, fecha/hora, datos, secuencias, cursores, procedures, transacciones, variables globales, colecciones, diferencias semánticas silenciosas)
**Carga:** SIEMPRE — toda conversión requiere mapeos sintácticos (Paso 4)

### 2. `feature-strategies.md` (~350 líneas)
**Contenido:** Estrategias arquitectónicas para features complejas:
- AUTONOMOUS_TRANSACTION → aws_lambda (NUNCA dblink)
- UTL_HTTP → AWS Lambda
- UTL_FILE → AWS S3
- DBMS_SQL → EXECUTE nativo
- OBJECT TYPES → Composite Types
- PIPELINED → RETURNS SETOF
- CONNECT BY → WITH RECURSIVE
- PACKAGES → Schemas + Getters/Setters
**Carga:** SOLO si `oracle_features` contiene alguna de estas features (Paso 3)

### 3. `procedure-function-preservation.md` (~240 líneas)
**Contenido:** Reglas para preservar lógica de negocio intacta durante conversión
**Principio:** PRESERVAR > OPTIMIZAR
**Carga:** SOLO si objeto tiene parámetros OUT/INOUT, migration_impact HIGH, o dependencias externas (Paso 5-E)

### 4. `conversion-examples.md` (~285 líneas)
**Contenido:** 5 ejemplos end-to-end: OUT→INOUT, FOR loop RECORD, AUTONOMOUS_TRANSACTION (aws_lambda), Variables globales, EXECUTE IMMEDIATE
**Carga:** Referencia opcional — no cargado automáticamente por el agente

</files>

---

<usage>

## Cómo Usa plsql-converter Estos Archivos

**Método: Read on-demand** — El agente decide qué cargar según `migration_thinking` punto 6:

```
1. syntax-mapping.md     → SIEMPRE (Paso 4)
2. feature-strategies.md → ¿Features COMPLEX? → SÍ: Paso 3 / NO: omitir
3. procedure-function-preservation.md → ¿OUT params / HIGH impact? → SÍ: Paso 5-E / NO: omitir
```

Condiciones de carga definidas en SECCIÓN 1.5 del agente.

</usage>

---

**Versión:** 3.0
**Última Actualización:** 2026-02-17
**Total:** ~1,196 líneas en 4 archivos activos
