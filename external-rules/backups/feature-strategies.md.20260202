# Estrategias de Conversión por Feature Oracle

**Propósito:** Estrategias arquitectónicas para convertir features complejas de Oracle a PostgreSQL.
**Uso:** Consultar cuando el agente converter encuentre objetos COMPLEX con features específicas.

---

## 1. PRAGMA AUTONOMOUS_TRANSACTION

**Feature Oracle:** Transacciones autónomas (commits independientes del caller).

**Frecuencia estimada:** ~40 objetos

### Opciones de Conversión

| Opción | Pros | Contras | Cuándo usar |
|--------|------|---------|-------------|
| **A: dblink** | Comportamiento exacto | Overhead conexión | Default, conversión directa |
| **B: Staging + pg_cron** | Mejor performance | Más diseño | Logging/auditoría no crítica |
| **C: AWS Lambda** | Cloud-native, async | Complejidad infra | Auditoría distribuida |

**Recomendación:** Opción A (dblink) por defecto.

### Implementación Opción A (dblink)

```sql
-- Oracle
PROCEDURE log_audit(p_action VARCHAR2) IS
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
  INSERT INTO audit_log VALUES (SYSDATE, p_action);
  COMMIT;
END;

-- PostgreSQL
CREATE OR REPLACE PROCEDURE log_audit(p_action VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
  PERFORM dblink_exec(
    'dbname=<db_name>',
    format('INSERT INTO audit_log VALUES (CURRENT_TIMESTAMP, %L)', p_action)
  );
END;
$$;
```

**Notas:**
- Requiere extensión `dblink` instalada
- Configurar connection string en `dblink_exec()`

---

## 2. UTL_HTTP (Llamadas HTTP)

**Feature Oracle:** Cliente HTTP para consumir APIs externas.

**Frecuencia estimada:** ~15 objetos

### Estrategia: AWS Lambda (Cloud-Native)

**Arquitectura:**
```
PostgreSQL → aws_lambda.invoke() → Lambda Function → HTTP API → Response
```

**Implementación:**

```sql
-- Oracle
v_response := UTL_HTTP.REQUEST('https://api.example.com/endpoint');

-- PostgreSQL
CREATE OR REPLACE FUNCTION http_get(p_url VARCHAR)
RETURNS TEXT
LANGUAGE plpgsql AS $$
DECLARE
  v_payload JSONB;
  v_response TEXT;
BEGIN
  v_payload := jsonb_build_object('url', p_url, 'method', 'GET');

  SELECT aws_lambda.invoke(
    'arn:aws:lambda:region:account:function:http-client',
    v_payload::TEXT
  ) INTO v_response;

  RETURN v_response;
END;
$$;
```

**Prerequisitos:**
- Lambda function `http-client` creada
- Extension `aws_lambda` instalada en Aurora PostgreSQL

---

## 3. UTL_FILE (Operaciones de Archivos)

**Feature Oracle:** Lectura/escritura de archivos en filesystem.

**Frecuencia estimada:** ~20 objetos

### Estrategia: AWS S3 (Cloud-Native)

**Arquitectura:**
```
PostgreSQL → aws_s3.query_export_to_s3() → S3 Bucket
PostgreSQL ← aws_s3.table_import_from_s3() ← S3 Bucket
```

**Implementación:**

```sql
-- Oracle (escribir archivo)
UTL_FILE.PUT_LINE(v_file, 'contenido');

-- PostgreSQL (escribir a S3)
SELECT aws_s3.query_export_to_s3(
  'SELECT contenido FROM tabla',
  aws_commons.create_s3_uri(
    'bucket-name',
    'path/to/file.txt',
    'us-east-1'
  )
);

-- Oracle (leer archivo)
v_line := UTL_FILE.GET_LINE(v_file);

-- PostgreSQL (leer desde S3)
CREATE TEMP TABLE tmp_data (linea TEXT);
SELECT aws_s3.table_import_from_s3(
  'tmp_data',
  '',
  '(FORMAT CSV)',
  aws_commons.create_s3_uri('bucket-name', 'path/to/file.txt', 'us-east-1')
);
```

**Prerequisitos:**
- Bucket S3 creado
- Extension `aws_s3` instalada
- IAM role configurado

---

## 4. DBMS_SQL (SQL Dinámico)

**Feature Oracle:** Construcción y ejecución dinámica de SQL.

**Frecuencia estimada:** ~30 objetos

### Estrategia: EXECUTE en PostgreSQL

**Conversión:**

```sql
-- Oracle (DBMS_SQL)
v_cursor := DBMS_SQL.OPEN_CURSOR;
DBMS_SQL.PARSE(v_cursor, 'SELECT * FROM ' || v_table);
DBMS_SQL.EXECUTE(v_cursor);

-- PostgreSQL (EXECUTE)
EXECUTE 'SELECT * FROM ' || quote_ident(v_table);
```

**⚠️ IMPORTANTE - Seguridad:**
- SIEMPRE usar `quote_ident()` para identifiers (tablas, columnas)
- SIEMPRE usar `quote_literal()` para valores literales
- NUNCA concatenar directamente input de usuario (SQL injection)

---

## 5. OBJECT TYPES y Collections

**Feature Oracle:** Tipos de datos compuestos, VARRAYs, Nested Tables.

**Frecuencia estimada:** ~50 objetos

### Estrategia: Tipos Compuestos + Arrays

**Conversión:**

```sql
-- Oracle (OBJECT TYPE)
CREATE TYPE t_empleado AS OBJECT (
  id NUMBER,
  nombre VARCHAR2(100)
);

CREATE TYPE t_empleados AS TABLE OF t_empleado;

-- PostgreSQL (COMPOSITE TYPE + ARRAY)
CREATE TYPE t_empleado AS (
  id NUMERIC,
  nombre VARCHAR(100)
);

-- Usar como array:
DECLARE
  v_empleados t_empleado[];
BEGIN
  v_empleados := ARRAY[
    ROW(1, 'Juan')::t_empleado,
    ROW(2, 'María')::t_empleado
  ];
END;
```

---

## 6. BULK COLLECT y FORALL

**Feature Oracle:** Operaciones masivas optimizadas.

**Frecuencia estimada:** ~25 objetos

### Estrategia: Arrays + FOREACH

**Conversión:**

```sql
-- Oracle (BULK COLLECT)
SELECT id BULK COLLECT INTO v_ids FROM empleados WHERE activo = 'S';

-- PostgreSQL (ARRAY)
v_ids := ARRAY(SELECT id FROM empleados WHERE activo = 'S');

-- Oracle (FORALL)
FORALL i IN v_ids.FIRST..v_ids.LAST
  UPDATE empleados SET procesado = 'S' WHERE id = v_ids(i);

-- PostgreSQL (FOREACH + UPDATE)
FOREACH v_id IN ARRAY v_ids LOOP
  UPDATE empleados SET procesado = 'S' WHERE id = v_id;
END LOOP;

-- Alternativa (más eficiente en PostgreSQL):
UPDATE empleados SET procesado = 'S' WHERE id = ANY(v_ids);
```

---

## 7. PIPELINED FUNCTIONS

**Feature Oracle:** Funciones que retornan filas incrementalmente.

**Frecuencia estimada:** ~10 objetos

### Estrategia: RETURNS SETOF + RETURN NEXT

**Conversión:**

```sql
-- Oracle (PIPELINED)
CREATE FUNCTION get_empleados RETURN t_empleados PIPELINED IS
BEGIN
  FOR rec IN (SELECT * FROM empleados) LOOP
    PIPE ROW(t_empleado(rec.id, rec.nombre));
  END LOOP;
  RETURN;
END;

-- PostgreSQL (RETURNS SETOF)
CREATE OR REPLACE FUNCTION get_empleados()
RETURNS SETOF t_empleado
LANGUAGE plpgsql AS $$
DECLARE
  rec RECORD;
BEGIN
  FOR rec IN SELECT * FROM empleados LOOP
    RETURN NEXT ROW(rec.id, rec.nombre)::t_empleado;
  END LOOP;
  RETURN;
END;
$$;
```

---

## 8. CONNECT BY (Queries Jerárquicas)

**Feature Oracle:** Navegación de jerarquías (árboles).

**Frecuencia estimada:** ~15 objetos

### Estrategia: WITH RECURSIVE (CTE)

**Conversión:**

```sql
-- Oracle (CONNECT BY)
SELECT id, nombre, LEVEL
FROM categorias
START WITH id_padre IS NULL
CONNECT BY PRIOR id = id_padre;

-- PostgreSQL (WITH RECURSIVE)
WITH RECURSIVE jerarquia AS (
  -- Nodo raíz
  SELECT id, nombre, 1 AS level
  FROM categorias
  WHERE id_padre IS NULL

  UNION ALL

  -- Nodos hijos
  SELECT c.id, c.nombre, j.level + 1
  FROM categorias c
  INNER JOIN jerarquia j ON c.id_padre = j.id
)
SELECT * FROM jerarquia;
```

---

## 9. PACKAGES → SCHEMAS

**Feature Oracle:** Agrupación lógica de procedures, functions, variables.

**Frecuencia estimada:** ~100 packages (TODOS)

### Estrategia: Schema PostgreSQL + Funciones

**⚠️ REGLA CRÍTICA DE NAMING:**
- El schema PostgreSQL **DEBE tener exactamente el mismo nombre** que el package Oracle
- Convertir a lowercase (convención PostgreSQL)
- **NO agregar prefijos** (como `pkg_`, `sch_`, etc.)
- **NO agregar sufijos**

**Ejemplos:**
- Oracle: `PKG_VENTAS` → PostgreSQL: `CREATE SCHEMA pkg_ventas;` ✅
- Oracle: `DAFX_K_REPLICA_USUARIOS_PHA` → PostgreSQL: `CREATE SCHEMA dafx_k_replica_usuarios_pha;` ✅
- Oracle: `VENTAS` → PostgreSQL: `CREATE SCHEMA ventas;` ✅

**❌ INCORRECTO:**
- Oracle: `DAFX_K_REPLICA_USUARIOS_PHA` → PostgreSQL: `CREATE SCHEMA pkg_dafx_k_replica_usuarios_pha;` ❌ (agregó prefijo)

---

### Ejemplo 1: Package con prefijo (ya lo tiene en Oracle)

```sql
-- Oracle (PACKAGE)
CREATE PACKAGE pkg_ventas IS
  g_usuario VARCHAR2(100);
  C_IVA CONSTANT NUMBER := 0.12;

  FUNCTION get_descuento RETURN NUMBER;
  PROCEDURE registrar_venta(p_monto NUMBER);
END;

-- PostgreSQL (SCHEMA + FUNCTIONS)
CREATE SCHEMA pkg_ventas;  -- ✅ Mismo nombre que Oracle (en lowercase)

-- Variable pública → Setter/Getter
CREATE FUNCTION pkg_ventas.set_usuario(p_usuario VARCHAR)
RETURNS VOID AS $$
BEGIN
  PERFORM set_config('pkg_ventas.usuario', p_usuario, false);
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION pkg_ventas.get_usuario()
RETURNS VARCHAR AS $$
BEGIN
  RETURN current_setting('pkg_ventas.usuario', true);
END;
$$ LANGUAGE plpgsql;

-- Constante → Replicar en funciones que la usan
-- Function/Procedure → Convertir normalmente
CREATE FUNCTION pkg_ventas.get_descuento() RETURNS NUMERIC AS ...
CREATE PROCEDURE pkg_ventas.registrar_venta(p_monto NUMERIC) AS ...
```

---

### Ejemplo 2: Package SIN prefijo (caso real PhantomX)

```sql
-- Oracle (PACKAGE sin prefijo pkg_)
CREATE OR REPLACE PACKAGE BODY DAFX_K_REPLICA_USUARIOS_PHA IS
  PROCEDURE p_nuevo_usuario(pn_secuencia_usuario NUMBER, pv_msg_error OUT VARCHAR2);
  PROCEDURE p_modificacion_usuario(pn_secuencia_usuario NUMBER, pv_msg_error OUT VARCHAR2);
  PROCEDURE p_inactivacion_usuario(pn_secuencia_usuario NUMBER, pv_msg_error OUT VARCHAR2);
END DAFX_K_REPLICA_USUARIOS_PHA;

-- PostgreSQL (SCHEMA con MISMO nombre, sin agregar prefijos)
CREATE SCHEMA dafx_k_replica_usuarios_pha;  -- ✅ Mismo nombre (lowercase)

-- Procedures del package → Procedures en el schema
CREATE PROCEDURE dafx_k_replica_usuarios_pha.p_nuevo_usuario(
  pn_secuencia_usuario NUMERIC,
  OUT pv_msg_error VARCHAR
) LANGUAGE plpgsql AS $$
BEGIN
  -- Lógica del procedure
END;
$$;

CREATE PROCEDURE dafx_k_replica_usuarios_pha.p_modificacion_usuario(
  pn_secuencia_usuario NUMERIC,
  OUT pv_msg_error VARCHAR
) LANGUAGE plpgsql AS $$
BEGIN
  -- Lógica del procedure
END;
$$;

CREATE PROCEDURE dafx_k_replica_usuarios_pha.p_inactivacion_usuario(
  pn_secuencia_usuario NUMERIC,
  OUT pv_msg_error VARCHAR
) LANGUAGE plpgsql AS $$
BEGIN
  -- Lógica del procedure
END;
$$;

-- Llamadas desde aplicación:
-- Oracle: DAFX_K_REPLICA_USUARIOS_PHA.p_nuevo_usuario(123, v_error);
-- PostgreSQL: CALL dafx_k_replica_usuarios_pha.p_nuevo_usuario(123, v_error);
```

**Ventajas de mantener el mismo nombre:**
1. ✅ Facilita búsqueda y mapeo 1:1 entre Oracle y PostgreSQL
2. ✅ Código de aplicación solo requiere cambio de mayúsculas/minúsculas
3. ✅ Mantiene consistencia con nomenclatura existente
4. ✅ Evita confusión con prefijos innecesarios

---

## Proceso General de Conversión

Para CUALQUIER feature:

1. **Identificar feature** en código Oracle
2. **Buscar en esta tabla** de estrategias
3. Si NO está listada:
   - **Consultar Context7:**
     ```python
     mcp__context7__query_docs(
         libraryId="/websites/postgresql_17",
         query="PostgreSQL 17 equivalent to Oracle <feature>"
     )
     ```
   - Diseñar estrategia basada en respuesta Context7
   - Documentar para futuras conversiones
4. **Aplicar estrategia** validada
5. **Validar sintaxis** con Context7 antes de escribir archivo

---

**Referencias:**
- `syntax-mapping.md` - Mapeos sintácticos básicos
- Context7 - Documentación oficial PostgreSQL 17
- AWS Aurora PostgreSQL - Extensiones cloud-native

**Última Actualización:** 2026-01-26
**Versión:** 1.0
