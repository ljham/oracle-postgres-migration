# Mapeo de Sintaxis Oracle → PostgreSQL

<purpose>
Referencia rápida de conversiones sintácticas Oracle→PostgreSQL para agente plsql-converter.
</purpose>

---

<mappings>

## Manejo de Errores

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `RAISE_APPLICATION_ERROR(-20001, 'msg')` | `RAISE EXCEPTION 'msg'` | Sin código numérico |
| `$$plsql_unit` | `'nombre_literal'` | Reemplazo directo con nombre del objeto |
| `dbms_utility.format_error_backtrace` | `GET STACKED DIAGNOSTICS v_context = PG_EXCEPTION_CONTEXT` | Declarar `v_context TEXT` |
| `SQLERRM` | `SQLERRM` | Compatible |

**⚠️ CRÍTICO `$$plsql_unit`:** Reemplazar con literal directo, NO crear variable constante.

```sql
-- ✅ CORRECTO
BEGIN
  RAISE EXCEPTION 'Error en schema.proc_name: %', SQLERRM;
END;
```

---

## Fecha/Hora

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `SYSDATE` | `LOCALTIMESTAMP` | Sin timezone. Nota: retorna tiempo de inicio de tx, no wall-clock. Para tx cortas es equivalente |
| `SYSTIMESTAMP` | `CURRENT_TIMESTAMP` | Con timezone |
| `TRUNC(date)` | `DATE_TRUNC('day', date)` | Truncar |
| `ADD_MONTHS(date, n)` | `date + INTERVAL 'n months'` | Sumar meses |
| `MONTHS_BETWEEN(d1, d2)` | `EXTRACT(YEAR FROM AGE(d1, d2)) * 12 + EXTRACT(MONTH FROM AGE(d1, d2))` | Diferencia |

---

## Manipulación de Datos

| Oracle | PostgreSQL |
|--------|-----------|
| `NVL(a, b)` | `COALESCE(a, b)` |
| `NVL2(a, b, c)` | `CASE WHEN a IS NOT NULL THEN b ELSE c END` |
| `DECODE(expr, v1, r1, default)` | `CASE expr WHEN v1 THEN r1 ELSE default END` |

---

## Secuencias

| Oracle | PostgreSQL |
|--------|-----------|
| `seq.NEXTVAL` | `nextval('seq'::regclass)` |
| `seq.CURRVAL` | `currval('seq'::regclass)` |

---

## Sintaxis Eliminada

| Oracle | PostgreSQL | Acción |
|--------|-----------|--------|
| `FROM DUAL` | — | Eliminar |
| `WITH READ ONLY` | — | Eliminar (vistas) |
| `FORCE` | — | Eliminar (CREATE VIEW) |

---

## Cursores y Loops

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `CURSOR c IS SELECT ...` | `FOR var IN (SELECT ...) LOOP` | Query inline |
| Variable FOR loop *(implícita)* | `var RECORD` *(explícita DECLARE)* | **CRÍTICO** |

**Ejemplo FOR loop:**
```sql
-- PostgreSQL (variable OBLIGATORIA)
DECLARE
  reg RECORD;  -- ✅ Declarar siempre
BEGIN
  FOR reg IN (SELECT * FROM t) LOOP
    -- usar reg
  END LOOP;
END;
```

---

## Procedures y Functions

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `PROCEDURE proc(p IN VARCHAR2)` | `PROCEDURE proc(p VARCHAR)` | Sin `IN`, sin `2` |
| `FUNCTION func RETURN NUMBER` | `FUNCTION func() RETURNS NUMERIC` | `()` obligatorio |
| `pkg.proc(...)` | `CALL schema.proc(...)` | `CALL` + schema |

**⚠️ CRÍTICO - CAST SOLO en literales hardcodeados:**

**APLICAR CAST únicamente a:**
```sql
-- ✅ CORRECTO - Literales hardcodeados
CALL schema.proc(
  pv_contrasenia => CAST('2rR9A9NbRXI=' AS VARCHAR),  -- String literal
  pv_esactivo    => CAST('S' AS VARCHAR),              -- Char literal
  pn_codigo      => CAST(100 AS NUMERIC)               -- Numeric literal
);
```

**NO APLICAR CAST a:**
```sql
-- ✅ CORRECTO - Variables, campos, parámetros, funciones
CALL schema.proc(
  pv_codigousuario     => reg_usuario.codigo_usuario,  -- Campo de registro
  pn_secuenciapersonal => ln_secpersonal,              -- Variable local
  pv_usuarioingreso    => pv_usuario_ing,              -- Parámetro
  pd_fechaingreso      => LOCALTIMESTAMP,              -- Función built-in
  pv_msgerror          => pv_msgerror                  -- Parámetro OUT
);
```

**Razón:** PostgreSQL no infiere tipo de literales de texto en named parameters, pero SÍ infiere tipo de variables, campos y funciones built-in.

**⚠️ CRÍTICO - UPDATE: NO usar alias en cláusula SET:**

```sql
-- ❌ INCORRECTO (Oracle syntax, falla en PostgreSQL)
UPDATE daf_usuarios_sistema u
SET u.cuenta_mail = 'email@example.com',    -- ERROR: alias en SET
    u.es_activo = 'N'
WHERE u.codigo_usuario = 'USR001';

-- ✅ CORRECTO (PostgreSQL syntax)
UPDATE daf_usuarios_sistema u
SET cuenta_mail = 'email@example.com',      -- Sin alias en SET
    es_activo = 'N'
WHERE u.codigo_usuario = 'USR001';           -- Alias permitido en WHERE
```

**Razón:** PostgreSQL NO permite alias de tabla en la cláusula SET del UPDATE. El alias solo se puede usar en WHERE, FROM, JOIN.

---

## COMMIT y Control de Transacciones

| Oracle | PostgreSQL | Acción |
|--------|-----------|--------|
| `COMMIT;` dentro de PROCEDURE | `COMMIT;` | **PRESERVAR tal cual** (PG 11+ soporta COMMIT en procedures) |
| `ROLLBACK;` dentro de PROCEDURE | `ROLLBACK;` | **PRESERVAR tal cual** |
| `COMMIT;` dentro de FUNCTION | — | **NO compila en PG** → registrar en bitácora para revisión humana |
| `SAVEPOINT nombre;` | `SAVEPOINT nombre;` | Compatible |
| `AUTONOMOUS_TRANSACTION` + COMMIT | `aws_lambda.invoke()` | Ver feature-strategies.md #1 (NUNCA dblink) |

**⚠️ PRINCIPIO:** Migrar la lógica de transacciones **tal cual está en Oracle**. No modificar el comportamiento transaccional — la aplicación (Java/Python) depende de él.

**Excepciones que requieren notificación en bitácora:**
- FUNCTION con COMMIT/ROLLBACK → no compila en PostgreSQL (limitación de PG)
- AUTONOMOUS_TRANSACTION → reemplazar con aws_lambda (ver feature-strategies.md #1, NUNCA dblink)
- Lógica claramente errónea → corregir + registrar en bitácora

---

## Variables Globales de Package (Gv_*, Gi_*, Lv_*)

| Oracle | PostgreSQL | Estrategia |
|--------|-----------|------------|
| `Gv_Variable VARCHAR2(100)` | `set_config()` / `current_setting()` | Session variable |
| `Gi_Contador NUMBER := 0` | `set_config()` / `current_setting()` | Session variable |
| `Lv_Privada VARCHAR2(50)` | Schema-level function state | Schema variable |

**Patrón obligatorio — Generar en `_create_schema.sql`:**

```sql
-- Getter
CREATE OR REPLACE FUNCTION schema_name.get_gv_variable()
RETURNS VARCHAR LANGUAGE plpgsql AS $$
BEGIN
  RETURN COALESCE(current_setting('schema_name.gv_variable', TRUE), 'default_value');
END; $$;

-- Setter
CREATE OR REPLACE FUNCTION schema_name.set_gv_variable(p_value VARCHAR)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
  PERFORM set_config('schema_name.gv_variable', p_value, FALSE);
END; $$;
```

**Uso dentro de otros procedures del mismo schema:**
```sql
-- En vez de: v_schema := Gv_Variable;
v_schema := schema_name.get_gv_variable();

-- En vez de: Gv_Variable := 'nuevo_valor';
PERFORM schema_name.set_gv_variable('nuevo_valor');
```

**Regla de naming:** `Gv_` → `gv_`, `Gi_` → `gi_`, convertir a lowercase para el config key.

---

## Tipos de Colección

| Oracle | PostgreSQL |
|--------|-----------|
| `TABLE OF VARCHAR2 INDEX BY PLS_INTEGER` | `VARCHAR[]` (array) |
| `VARRAY(10) OF NUMBER` | `NUMERIC[]` (array) |
| `BULK COLLECT INTO v_arr` | `v_arr := ARRAY(SELECT ...)` |
| `FORALL i IN v_arr.FIRST..LAST` | `FOREACH elem IN ARRAY v_arr LOOP` |

---

## ⚠️ Diferencias Semánticas Silenciosas (NO dan error de compilación)

### 1. Empty String '' vs NULL

**Oracle** trata `''` (string vacío) como `NULL`. **PostgreSQL NO** — son valores distintos.

```sql
-- Oracle: ambos son TRUE
SELECT 1 FROM DUAL WHERE '' IS NULL;          -- TRUE
SELECT 1 FROM DUAL WHERE '' || 'abc' = 'abc'; -- TRUE (NULL || 'abc' = 'abc')

-- PostgreSQL: comportamiento DIFERENTE
SELECT 1 WHERE '' IS NULL;           -- FALSE ('' no es NULL)
SELECT 1 WHERE '' || 'abc' = 'abc';  -- TRUE  ('' || 'abc' = 'abc', pero por concatenación vacía)
SELECT 1 WHERE NULL || 'abc' IS NULL; -- TRUE  (NULL || cualquier cosa = NULL)
```

**Regla de conversión:**
- Si Oracle usa `''` como valor → preservar `''` (PostgreSQL lo maneja como string vacío)
- Si Oracle usa `''` esperando comportamiento NULL → cambiar a `NULL` explícito
- **Auditar:** `NVL('', valor)` en Oracle siempre retorna `valor`. En PostgreSQL, `COALESCE('', valor)` retorna `''`

### 2. DECODE con NULL — Semántica diferente

**Oracle DECODE** trata `NULL = NULL` como TRUE. **PostgreSQL CASE** sigue estándar SQL: `NULL = NULL` es UNKNOWN (falso).

```sql
-- Oracle (DECODE): funciona, retorna 'es null'
SELECT DECODE(val, NULL, 'es null', 'no es null') FROM tabla;

-- PostgreSQL CASE (conversión INCORRECTA): NUNCA entra en 'es null'
SELECT CASE val WHEN NULL THEN 'es null' ELSE 'no es null' END FROM tabla;

-- PostgreSQL CASE (conversión CORRECTA):
SELECT CASE WHEN val IS NULL THEN 'es null' ELSE 'no es null' END FROM tabla;
```

**Regla de conversión:**
- `DECODE(expr, NULL, resultado)` → `CASE WHEN expr IS NULL THEN resultado`
- `DECODE(expr, val1, res1, val2, res2)` donde ningún val es NULL → `CASE expr WHEN val1 THEN res1 WHEN val2 THEN res2 END` (conversión directa segura)

### 3. SELECT INTO — STRICT obligatorio para equivalencia

**Oracle:** `SELECT INTO` lanza `NO_DATA_FOUND` si 0 filas y `TOO_MANY_ROWS` si >1 fila.
**PostgreSQL sin STRICT:** retorna NULL si 0 filas y toma la primera si >1 fila — **sin error**.

```sql
-- Oracle: lanza NO_DATA_FOUND si no existe
SELECT nombre INTO v_nombre FROM usuarios WHERE id = 999;

-- PostgreSQL (INCORRECTO — sin STRICT): NO lanza excepción, v_nombre queda NULL
SELECT nombre INTO v_nombre FROM usuarios WHERE id = 999;

-- PostgreSQL (CORRECTO — con STRICT): lanza NO_DATA_FOUND como Oracle
SELECT nombre INTO STRICT v_nombre FROM usuarios WHERE id = 999;
```

**Regla de conversión:**
- `SELECT ... INTO variable` → `SELECT ... INTO STRICT variable`
- **Excepción:** Si el código Oracle tiene `EXCEPTION WHEN NO_DATA_FOUND` inmediatamente después, el STRICT es necesario para que ese handler se active
- **Excepción:** Si el código intencionalmente espera 0 filas (asigna NULL), NO agregar STRICT

</mappings>

---

<references>

**Para sintaxis NO listada:**
1. Consultar Context7: `/websites/postgresql_17`
2. Aplicar sintaxis oficial validada

</references>

---

**Versión:** 2.5
**Última Actualización:** 2026-02-17
**Cambios v2.5:** Eliminadas secciones redundantes (Packages→Schemas, PRAGMA duplicada), precisión SYSDATE, limpieza redundancia interna COMMIT
