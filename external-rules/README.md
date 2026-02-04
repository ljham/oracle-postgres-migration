# External Rules - Conocimiento de Conversión Oracle→PostgreSQL

<purpose>
Directorio con reglas, estrategias y ejemplos de conversión externalizados del agente `plsql-converter`.
Mantiene el agente optimizado (~500 líneas) sin perder funcionalidad.
</purpose>

---

<files>

## 📂 Archivos Disponibles

### 1. `syntax-mapping.md`
**Contenido:** Mapeos sintácticos Oracle→PostgreSQL (errores, fecha/hora, datos, secuencias, cursores, procedures, packages, colecciones)
**Cuándo:** Referencia rápida para conversiones comunes
**Tamaño:** ~160 líneas

### 2. `feature-strategies.md`
**Contenido:** 9 estrategias arquitectónicas para features complejas:
- PRAGMA AUTONOMOUS_TRANSACTION (dblink, staging, Lambda)
- UTL_HTTP (AWS Lambda)
- UTL_FILE (AWS S3)
- DBMS_SQL (EXECUTE)
- OBJECT TYPES (Composite Types)
- BULK COLLECT/FORALL (Arrays + FOREACH)
- PIPELINED (RETURNS SETOF)
- CONNECT BY (WITH RECURSIVE)
- PACKAGES → SCHEMAS

**Cuándo:** Objetos COMPLEX con features Oracle-específicas
**Tamaño:** ~290 líneas

### 3. `procedure-function-preservation.md`
**Contenido:** Reglas para preservar lógica de negocio intacta durante conversión
**Principio:** PRESERVAR > OPTIMIZAR
**Cuándo:** Siempre - checklist obligatorio antes de completar conversión
**Tamaño:** ~240 líneas

### 4. `conversion-examples.md`
**Contenido:** Ejemplos end-to-end de conversiones complejas
**Cuándo:** Necesitas ver patrón completo aplicado
**Tamaño:** ~300 líneas

### 5. `prompt-engineering-techniques.md`
**Contenido:** Técnicas de prompt engineering aplicadas (CoT, ReAct, CAPR)
**Cuándo:** Entender cómo estructurar reasoning del agente
**Tamaño:** ~130 líneas

</files>

---

<usage>

## 🔧 Cómo Usa plsql-converter Estos Archivos

**Método 1: Referencias en prompt** (actual)
```markdown
@see external-rules/syntax-mapping.md para mapeos
```

**Método 2: Read on-demand** (futuro)
```python
# El agente lee cuando necesita conocimiento específico
mapping = Read("external-rules/syntax-mapping.md")
```

**Beneficio:** Conocimiento modular, agente liviano (~500 líneas vs ~900 líneas con reglas inline).

</usage>

---

<optimization>

## ✅ Optimizaciones Aplicadas (v2.0)

**Cambios desde v1.0:**
- ✅ XML tags para estructura semántica (`<purpose>`, `<mappings>`, `<strategy>`, etc.)
- ✅ Reducción ~40% en tamaño total (de ~2,200 → ~1,300 líneas)
- ✅ Ejemplos concisos (mantener solo esencial)
- ✅ Español consistente
- ✅ Siguiendo Marco de Trabajo (CLAUDE.md)

**Principios aplicados:**
- Anthropic best practices (XML tags como estándar estructural)
- Anti-prompt bloat (minimalismo enfocado)
- Estructura semántica clara

</optimization>

---

**Versión:** 2.0 (optimizada)
**Última Actualización:** 2026-02-03
**Total:** ~1,120 líneas (optimizado desde ~2,222)
