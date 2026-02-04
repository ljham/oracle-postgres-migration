# Ejemplos de Conversiones Exitosas Oracle → PostgreSQL

**Propósito:** Referencia de patrones comunes de conversión con sintaxis validada.

**Uso:** Consulta estos ejemplos cuando conviertas objetos similares.

---

## 1. Functions Simples

### Ejemplo 1.1: Function con NVL y SYSDATE

```sql
-- ❌ Oracle Original
CREATE OR REPLACE FUNCTION get_employee_name(p_id NUMBER)
RETURN VARCHAR2 IS
  v_name VARCHAR2(100);
  v_date DATE := SYSDATE;
BEGIN
  SELECT NVL(first_name, 'Unknown')
  INTO v_name
  FROM employees
  WHERE employee_id = p_id;
  RETURN v_name;
END;

-- ✅ PostgreSQL CORRECTO
CREATE OR REPLACE FUNCTION get_employee_name(p_id NUMERIC)
RETURNS VARCHAR
LANGUAGE plpgsql AS $$
DECLARE
  v_name VARCHAR(100);
  v_date TIMESTAMP := CURRENT_TIMESTAMP;  -- SYSDATE → CURRENT_TIMESTAMP
BEGIN
  SELECT COALESCE(first_name, 'Unknown')  -- NVL → COALESCE
  INTO v_name
  FROM employees
  WHERE employee_id = p_id;
  RETURN v_name;
END;
$$;
```

### Ejemplo 1.2: Function con Sequence y Tipos de Datos

```sql
-- ❌ Oracle Original
CREATE OR REPLACE FUNCTION create_order(p_customer_id NUMBER)
RETURN NUMBER IS
  v_order_id NUMBER;
BEGIN
  v_order_id := order_seq.NEXTVAL;
  INSERT INTO orders (order_id, customer_id, order_date)
  VALUES (v_order_id, p_customer_id, SYSDATE);
  RETURN v_order_id;
END;

-- ✅ PostgreSQL CORRECTO
CREATE OR REPLACE FUNCTION create_order(p_customer_id NUMERIC)
RETURNS NUMERIC
LANGUAGE plpgsql AS $$
DECLARE
  v_order_id NUMERIC;
BEGIN
  v_order_id := nextval('order_seq'::regclass);  -- seq.NEXTVAL → nextval()
  INSERT INTO orders (order_id, customer_id, order_date)
  VALUES (v_order_id, p_customer_id, CURRENT_TIMESTAMP);
  RETURN v_order_id;
END;
$$;
```

---

## 2. Procedures con Cursores y Loops

### Ejemplo 2.1: Procedure con FOR Loop Simple ⚠️ CRÍTICO

```sql
-- ❌ Oracle Original
CREATE OR REPLACE PROCEDURE process_employees IS
BEGIN
  FOR rec IN (SELECT employee_id, salary FROM employees) LOOP
    UPDATE salaries SET amount = rec.salary WHERE emp_id = rec.employee_id;
  END LOOP;
END;

-- ✅ PostgreSQL CORRECTO
CREATE OR REPLACE PROCEDURE process_employees()
LANGUAGE plpgsql AS $$
DECLARE
  rec RECORD;  -- ⚠️ CRÍTICO: Declarar variable de loop EXPLÍCITAMENTE
BEGIN
  FOR rec IN (SELECT employee_id, salary FROM employees) LOOP
    UPDATE salaries SET amount = rec.salary WHERE emp_id = rec.employee_id;
  END LOOP;
END;
$$;
```

### Ejemplo 2.2: Procedure con Loops Anidados ⚠️ CRÍTICO

```sql
-- ❌ Oracle Original
CREATE OR REPLACE PROCEDURE process_departments IS
BEGIN
  FOR dept IN (SELECT department_id FROM departments) LOOP
    FOR emp IN (SELECT employee_id, salary FROM employees WHERE dept_id = dept.department_id) LOOP
      UPDATE salaries SET amount = emp.salary WHERE emp_id = emp.employee_id;
    END LOOP;
  END LOOP;
END;

-- ✅ PostgreSQL CORRECTO
CREATE OR REPLACE PROCEDURE process_departments()
LANGUAGE plpgsql AS $$
DECLARE
  dept RECORD;  -- ⚠️ Declarar AMBAS variables de loop
  emp RECORD;
BEGIN
  FOR dept IN (SELECT department_id FROM departments) LOOP
    FOR emp IN (SELECT employee_id, salary FROM employees WHERE dept_id = dept.department_id) LOOP
      UPDATE salaries SET amount = emp.salary WHERE emp_id = emp.employee_id;
    END LOOP;
  END LOOP;
END;
$$;
```

### Ejemplo 2.3: Procedure con Cursor Explícito

```sql
-- ❌ Oracle Original
CREATE OR REPLACE PROCEDURE process_high_salaries IS
  CURSOR emp_cursor IS
    SELECT employee_id, salary FROM employees WHERE salary > 5000;
  v_emp_id NUMBER;
  v_salary NUMBER;
BEGIN
  OPEN emp_cursor;
  LOOP
    FETCH emp_cursor INTO v_emp_id, v_salary;
    EXIT WHEN emp_cursor%NOTFOUND;
    -- Process employee
    UPDATE bonuses SET amount = v_salary * 0.1 WHERE emp_id = v_emp_id;
  END LOOP;
  CLOSE emp_cursor;
END;

-- ✅ PostgreSQL CORRECTO (preferir FOR loop)
CREATE OR REPLACE PROCEDURE process_high_salaries()
LANGUAGE plpgsql AS $$
DECLARE
  rec RECORD;
BEGIN
  FOR rec IN (SELECT employee_id, salary FROM employees WHERE salary > 5000) LOOP
    UPDATE bonuses SET amount = rec.salary * 0.1 WHERE emp_id = rec.employee_id;
  END LOOP;
END;
$$;
```

### Ejemplo 2.4: Cursores Parametrizados ⚠️ CRÍTICO - ERROR COMÚN

**PROBLEMA:** Sintaxis de cursores parametrizados es INCOMPATIBLE entre Oracle y PostgreSQL

```sql
-- ❌ Oracle Original (sintaxis válida en Oracle)
CREATE OR REPLACE PROCEDURE process_user_data(pn_user_id NUMBER) IS
  -- Cursor parametrizado en Oracle
  CURSOR c_usuario(id NUMERIC) IS
    SELECT nombre, email FROM usuarios WHERE usuario_id = id;

  reg_usuario c_usuario%ROWTYPE;
BEGIN
  -- Llamada al cursor con parámetro
  FOR reg_usuario IN c_usuario(pn_user_id) LOOP
    DBMS_OUTPUT.PUT_LINE('Usuario: ' || reg_usuario.nombre);
  END LOOP;
END;

-- ❌ CONVERSIÓN INCORRECTA (NO compilará en PostgreSQL)
CREATE OR REPLACE PROCEDURE process_user_data(pn_user_id NUMERIC)
LANGUAGE plpgsql AS $$
DECLARE
  CURSOR c_usuario(id NUMERIC) IS  -- ❌ PostgreSQL NO soporta esta sintaxis
    SELECT nombre, email FROM usuarios WHERE usuario_id = id;

  reg_usuario RECORD;
BEGIN
  FOR reg_usuario IN c_usuario(pn_user_id) LOOP  -- ❌ ERROR: syntax error
    RAISE NOTICE 'Usuario: %', reg_usuario.nombre;
  END LOOP;
END;
$$;

-- ✅ PostgreSQL CORRECTO - Inline cursor en FOR loop
CREATE OR REPLACE PROCEDURE process_user_data(pn_user_id NUMERIC)
LANGUAGE plpgsql AS $$
DECLARE
  reg_usuario RECORD;
BEGIN
  -- Inline cursor: parámetros se usan directamente en la query
  FOR reg_usuario IN (
    SELECT nombre, email
    FROM usuarios
    WHERE usuario_id = pn_user_id  -- Usar parámetro directamente
  ) LOOP
    RAISE NOTICE 'Usuario: %', reg_usuario.nombre;
  END LOOP;
END;
$$;
```

**REGLA DE CONVERSIÓN:**

Oracle:
```sql
CURSOR c_name(param TYPE) IS SELECT ... WHERE col = param;
FOR rec IN c_name(value) LOOP
```

PostgreSQL:
```sql
-- Eliminar cursor parametrizado, usar inline query con variable directa
FOR rec IN (SELECT ... WHERE col = value) LOOP
```

**MÚLTIPLES CURSORES PARAMETRIZADOS:**

```sql
-- ❌ Oracle Original
CREATE OR REPLACE PROCEDURE sync_user_roles(pn_user_id NUMBER) IS
  CURSOR c_sucursales(id NUMBER) IS
    SELECT sucursal_id FROM usuario_sucursal WHERE usuario_id = id;

  CURSOR c_roles(uid NUMBER, sid NUMBER) IS
    SELECT rol_id FROM usuario_rol WHERE usuario_id = uid AND sucursal_id = sid;
BEGIN
  FOR reg_suc IN c_sucursales(pn_user_id) LOOP
    FOR reg_rol IN c_roles(pn_user_id, reg_suc.sucursal_id) LOOP
      -- Process role
      INSERT INTO roles_sync VALUES (reg_rol.rol_id);
    END LOOP;
  END LOOP;
END;

-- ✅ PostgreSQL CORRECTO
CREATE OR REPLACE PROCEDURE sync_user_roles(pn_user_id NUMERIC)
LANGUAGE plpgsql AS $$
DECLARE
  reg_suc RECORD;
  reg_rol RECORD;
BEGIN
  FOR reg_suc IN (
    SELECT sucursal_id
    FROM usuario_sucursal
    WHERE usuario_id = pn_user_id
  ) LOOP
    FOR reg_rol IN (
      SELECT rol_id
      FROM usuario_rol
      WHERE usuario_id = pn_user_id
        AND sucursal_id = reg_suc.sucursal_id
    ) LOOP
      -- Process role
      INSERT INTO roles_sync VALUES (reg_rol.rol_id);
    END LOOP;
  END LOOP;
END;
$$;
```

---

## 3. Manejo de Errores

### Ejemplo 3.1: RAISE_APPLICATION_ERROR (español)

```sql
-- ❌ Oracle Original
CREATE OR REPLACE FUNCTION validate_salary(p_amount NUMBER)
RETURN NUMBER IS
BEGIN
  IF p_amount < 0 THEN
    RAISE_APPLICATION_ERROR(-20001, 'El salario no puede ser negativo');
  END IF;
  RETURN p_amount;
END;

-- ✅ PostgreSQL CORRECTO (preservar idioma)
CREATE OR REPLACE FUNCTION validate_salary(p_amount NUMERIC)
RETURNS NUMERIC
LANGUAGE plpgsql AS $$
BEGIN
  IF p_amount < 0 THEN
    RAISE EXCEPTION 'El salario no puede ser negativo';  -- Idioma preservado
  END IF;
  RETURN p_amount;
END;
$$;
```

### Ejemplo 3.2: Exception Handling con Variables de Error

```sql
-- ❌ Oracle Original
CREATE OR REPLACE PROCEDURE safe_update(p_id NUMBER, p_amount NUMBER) IS
  v_error_msg VARCHAR2(4000);
BEGIN
  UPDATE accounts SET balance = p_amount WHERE id = p_id;
EXCEPTION
  WHEN OTHERS THEN
    v_error_msg := SQLERRM || ' - ' || dbms_utility.format_error_backtrace;
    INSERT INTO error_log (message, timestamp) VALUES (v_error_msg, SYSDATE);
END;

-- ✅ PostgreSQL CORRECTO
CREATE OR REPLACE PROCEDURE safe_update(p_id NUMERIC, p_amount NUMERIC)
LANGUAGE plpgsql AS $$
DECLARE
  v_error_msg TEXT;
  v_context TEXT;
BEGIN
  UPDATE accounts SET balance = p_amount WHERE id = p_id;
EXCEPTION
  WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_context = PG_EXCEPTION_CONTEXT;
    v_error_msg := SQLERRM || ' - ' || v_context;
    INSERT INTO error_log (message, timestamp) VALUES (v_error_msg, CURRENT_TIMESTAMP);
END;
$$;
```

---

## 4. DECODE y CASE

### Ejemplo 4.1: DECODE a CASE

```sql
-- ❌ Oracle Original
SELECT employee_id,
       DECODE(status, 'A', 'Active', 'I', 'Inactive', 'P', 'Pending', 'Unknown') as status_desc
FROM employees;

-- ✅ PostgreSQL CORRECTO
SELECT employee_id,
       CASE status
         WHEN 'A' THEN 'Active'
         WHEN 'I' THEN 'Inactive'
         WHEN 'P' THEN 'Pending'
         ELSE 'Unknown'
       END as status_desc
FROM employees;
```

---

## 5. Bulk Operations

### Ejemplo 5.1: BULK COLLECT

```sql
-- ❌ Oracle Original
DECLARE
  TYPE emp_array IS TABLE OF employees.employee_id%TYPE;
  v_emp_ids emp_array;
BEGIN
  SELECT employee_id BULK COLLECT INTO v_emp_ids
  FROM employees WHERE department_id = 10;

  FORALL i IN v_emp_ids.FIRST..v_emp_ids.LAST
    UPDATE salaries SET bonus = 1000 WHERE emp_id = v_emp_ids(i);
END;

-- ✅ PostgreSQL CORRECTO
DO $$
DECLARE
  v_emp_ids NUMERIC[];
  v_id NUMERIC;
BEGIN
  SELECT ARRAY(SELECT employee_id FROM employees WHERE department_id = 10)
  INTO v_emp_ids;

  FOREACH v_id IN ARRAY v_emp_ids LOOP
    UPDATE salaries SET bonus = 1000 WHERE emp_id = v_id;
  END LOOP;
END;
$$;
```

---

## 6. Packages → Schemas

### Ejemplo 6.1: Package Simple a Schema

```sql
-- ❌ Oracle Package Spec
CREATE OR REPLACE PACKAGE employee_pkg IS
  FUNCTION get_name(p_id NUMBER) RETURN VARCHAR2;
  PROCEDURE update_salary(p_id NUMBER, p_salary NUMBER);
END employee_pkg;

-- ❌ Oracle Package Body
CREATE OR REPLACE PACKAGE BODY employee_pkg IS
  FUNCTION get_name(p_id NUMBER) RETURN VARCHAR2 IS
    v_name VARCHAR2(100);
  BEGIN
    SELECT first_name INTO v_name FROM employees WHERE employee_id = p_id;
    RETURN v_name;
  END;

  PROCEDURE update_salary(p_id NUMBER, p_salary NUMBER) IS
  BEGIN
    UPDATE employees SET salary = p_salary WHERE employee_id = p_id;
  END;
END employee_pkg;

-- ✅ PostgreSQL Schema Structure
-- File: _create_schema.sql
CREATE SCHEMA IF NOT EXISTS employee_pkg;

-- File: get_name.sql
CREATE OR REPLACE FUNCTION employee_pkg.get_name(p_id NUMERIC)
RETURNS VARCHAR
LANGUAGE plpgsql AS $$
DECLARE
  v_name VARCHAR(100);
BEGIN
  SELECT first_name INTO v_name FROM employees WHERE employee_id = p_id;
  RETURN v_name;
END;
$$;

-- File: update_salary.sql
CREATE OR REPLACE PROCEDURE employee_pkg.update_salary(p_id NUMERIC, p_salary NUMERIC)
LANGUAGE plpgsql AS $$
BEGIN
  UPDATE employees SET salary = p_salary WHERE employee_id = p_id;
END;
$$;
```

---

## 7. Triggers

### Ejemplo 7.1: Before Insert Trigger

```sql
-- ❌ Oracle Original
CREATE OR REPLACE TRIGGER trg_employee_audit
BEFORE INSERT ON employees
FOR EACH ROW
BEGIN
  :NEW.created_date := SYSDATE;
  :NEW.created_by := USER;
END;

-- ✅ PostgreSQL CORRECTO
CREATE OR REPLACE FUNCTION trg_employee_audit_func()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
  NEW.created_date := CURRENT_TIMESTAMP;
  NEW.created_by := CURRENT_USER;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_employee_audit
BEFORE INSERT ON employees
FOR EACH ROW
EXECUTE FUNCTION trg_employee_audit_func();
```

---

## 8. Pipelined Functions

### Ejemplo 8.1: Pipelined Function → SETOF

```sql
-- ❌ Oracle Original
CREATE TYPE emp_type AS OBJECT (
  employee_id NUMBER,
  full_name VARCHAR2(200)
);

CREATE TYPE emp_table AS TABLE OF emp_type;

CREATE OR REPLACE FUNCTION get_employees(p_dept_id NUMBER)
RETURN emp_table PIPELINED IS
BEGIN
  FOR rec IN (SELECT employee_id, first_name || ' ' || last_name as full_name
              FROM employees WHERE department_id = p_dept_id) LOOP
    PIPE ROW(emp_type(rec.employee_id, rec.full_name));
  END LOOP;
  RETURN;
END;

-- ✅ PostgreSQL CORRECTO
CREATE TYPE employee_pkg.emp_type AS (
  employee_id NUMERIC,
  full_name VARCHAR(200)
);

CREATE OR REPLACE FUNCTION get_employees(p_dept_id NUMERIC)
RETURNS SETOF employee_pkg.emp_type
LANGUAGE plpgsql AS $$
DECLARE
  rec RECORD;
  result employee_pkg.emp_type;
BEGIN
  FOR rec IN (SELECT employee_id, first_name || ' ' || last_name as full_name
              FROM employees WHERE department_id = p_dept_id) LOOP
    result.employee_id := rec.employee_id;
    result.full_name := rec.full_name;
    RETURN NEXT result;
  END LOOP;
  RETURN;
END;
$$;
```

---

## 9. Autonomous Transactions

### Ejemplo 9.1: AUTONOMOUS_TRANSACTION → dblink

```sql
-- ❌ Oracle Original
CREATE OR REPLACE PROCEDURE log_audit(p_message VARCHAR2) IS
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
  INSERT INTO audit_log (message, log_date) VALUES (p_message, SYSDATE);
  COMMIT;
END;

-- ✅ PostgreSQL CORRECTO (dblink)
CREATE OR REPLACE PROCEDURE log_audit(p_message TEXT)
LANGUAGE plpgsql AS $$
BEGIN
  PERFORM dblink_exec('dbname=mydb',
    format('INSERT INTO audit_log (message, log_date) VALUES (%L, CURRENT_TIMESTAMP); COMMIT;',
           p_message));
END;
$$;
```

---

## 10. Hierarchical Queries

### Ejemplo 10.1: CONNECT BY → WITH RECURSIVE

```sql
-- ❌ Oracle Original
SELECT employee_id, manager_id, level
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id
ORDER BY level;

-- ✅ PostgreSQL CORRECTO
WITH RECURSIVE emp_hierarchy AS (
  -- Anchor: root employees
  SELECT employee_id, manager_id, 1 as level
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive: children
  SELECT e.employee_id, e.manager_id, eh.level + 1
  FROM employees e
  INNER JOIN emp_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT employee_id, manager_id, level
FROM emp_hierarchy
ORDER BY level;
```

---

**Última Actualización:** 2026-01-31
**Uso:** Referencia rápida para plsql-converter agent
