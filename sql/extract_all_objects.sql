-- extract_all_objects.sql (v3)
-- Script para extraer objetos de Oracle a archivos SQL
--
-- CAMBIOS v3:
--   ✅ USA ALL_SOURCE con SELECT directo (evita partición de identificadores)
--   ✅ AGREGA delimitador / automáticamente entre objetos
--   ✅ Preserva código fuente EXACTO tal como fue compilado
--   ✅ Compatible con prepare_migration_v4.py (parsing granular)
--   ✅ Mantiene DBMS_METADATA para TABLES, CONSTRAINTS, SEQUENCES
--
-- Ejecutar con charset UTF-8:
--   bash extract_with_utf8.sh
--
-- O manualmente:
--   export NLS_LANG=AMERICAN_AMERICA.AL32UTF8
--   sqlplus latino_migracion/latino_migracion123@AWS_BD_TEST @extract_all_objects.sql
--

SET LONG 100000000
SET LONGCHUNKSIZE 100000000
SET LINESIZE 32767
SET PAGESIZE 0
SET HEADING OFF
SET FEEDBACK OFF
SET VERIFY OFF
SET TRIMSPOOL ON
SET TIMING OFF
SET SERVEROUTPUT ON SIZE UNLIMITED

-- Crear directorio de salida
!mkdir -p extracted

PROMPT =====================================================
PROMPT Extraccion v3 - ALL_SOURCE + Delimitadores automaticos
PROMPT - Codigo fuente EXACTO (sin particion de identificadores)
PROMPT - Delimitador / agregado entre objetos
PROMPT - Compatible con prepare_migration_v4.py
PROMPT =====================================================

-- =====================================================
-- METADATA DE OBJETOS (Archivo separado con info de compilación)
-- =====================================================
PROMPT Generando metadata.json...
SPOOL extracted/metadata.json

SELECT '[' FROM dual;

-- FUNCTIONS metadata
SELECT
    CASE
        WHEN ROW_NUMBER() OVER (ORDER BY owner, name) > 1 THEN ','
        ELSE ''
    END ||
    '{' ||
    '"schema":"' || owner || '",' ||
    '"object_name":"' || name || '",' ||
    '"object_type":"FUNCTION",' ||
    '"source_file":"functions.sql",' ||
    '"last_ddl_time":"' || TO_CHAR((SELECT last_ddl_time FROM all_objects o WHERE o.owner = s.owner AND o.object_name = s.name AND o.object_type = 'FUNCTION'), 'YYYY-MM-DD HH24:MI:SS') || '",' ||
    '"lines_of_code":' || MAX(line) ||
    '}'
FROM all_source s
WHERE type = 'FUNCTION'
  AND owner IN ('LATINO_PLSQL')
GROUP BY owner, name
ORDER BY owner, name;

-- PROCEDURES metadata
SELECT
    ',' ||
    '{' ||
    '"schema":"' || owner || '",' ||
    '"object_name":"' || name || '",' ||
    '"object_type":"PROCEDURE",' ||
    '"source_file":"procedures.sql",' ||
    '"last_ddl_time":"' || TO_CHAR((SELECT last_ddl_time FROM all_objects o WHERE o.owner = s.owner AND o.object_name = s.name AND o.object_type = 'PROCEDURE'), 'YYYY-MM-DD HH24:MI:SS') || '",' ||
    '"lines_of_code":' || MAX(line) ||
    '}'
FROM all_source s
WHERE type = 'PROCEDURE'
  AND owner IN ('LATINO_PLSQL')
GROUP BY owner, name
ORDER BY owner, name;

-- PACKAGE SPEC metadata
SELECT
    ',' ||
    '{' ||
    '"schema":"' || owner || '",' ||
    '"object_name":"' || name || '",' ||
    '"object_type":"PACKAGE_SPEC",' ||
    '"source_file":"packages_spec.sql",' ||
    '"last_ddl_time":"' || TO_CHAR((SELECT last_ddl_time FROM all_objects o WHERE o.owner = s.owner AND o.object_name = s.name AND o.object_type = 'PACKAGE'), 'YYYY-MM-DD HH24:MI:SS') || '",' ||
    '"lines_of_code":' || MAX(line) ||
    '}'
FROM all_source s
WHERE type = 'PACKAGE'
  AND owner IN ('LATINO_PLSQL')
  AND name != 'ORA_EXCEL'
GROUP BY owner, name
ORDER BY owner, name;

-- PACKAGE BODY metadata
SELECT
    ',' ||
    '{' ||
    '"schema":"' || owner || '",' ||
    '"object_name":"' || name || '",' ||
    '"object_type":"PACKAGE_BODY",' ||
    '"source_file":"packages_body.sql",' ||
    '"last_ddl_time":"' || TO_CHAR((SELECT last_ddl_time FROM all_objects o WHERE o.owner = s.owner AND o.object_name = s.name AND o.object_type = 'PACKAGE BODY'), 'YYYY-MM-DD HH24:MI:SS') || '",' ||
    '"lines_of_code":' || MAX(line) ||
    '}'
FROM all_source s
WHERE type = 'PACKAGE BODY'
  AND owner IN ('LATINO_PLSQL')
  AND name != 'ORA_EXCEL'
GROUP BY owner, name
ORDER BY owner, name;

-- TRIGGERS metadata
SELECT
    ',' ||
    '{' ||
    '"schema":"' || s.owner || '",' ||
    '"object_name":"' || s.name || '",' ||
    '"object_type":"TRIGGER",' ||
    '"source_file":"triggers.sql",' ||
    '"table_name":"' || t.table_owner || '.' || t.table_name || '",' ||
    '"trigger_type":"' || t.trigger_type || '",' ||
    '"triggering_event":"' || t.triggering_event || '",' ||
    '"last_ddl_time":"' || TO_CHAR((SELECT last_ddl_time FROM all_objects o WHERE o.owner = s.owner AND o.object_name = s.name AND o.object_type = 'TRIGGER'), 'YYYY-MM-DD HH24:MI:SS') || '",' ||
    '"lines_of_code":' || MAX(s.line) ||
    '}'
FROM all_source s
INNER JOIN all_triggers t ON s.owner = t.owner AND s.name = t.trigger_name
WHERE s.type = 'TRIGGER'
  AND s.owner IN ('LATINO_OWNER')
GROUP BY s.owner, s.name, t.table_owner, t.table_name, t.trigger_type, t.triggering_event
ORDER BY s.owner, t.table_name, s.name;

-- JAVA SOURCE metadata
SELECT
    ',' ||
    '{' ||
    '"schema":"' || owner || '",' ||
    '"object_name":"' || name || '",' ||
    '"object_type":"JAVA_SOURCE",' ||
    '"source_file":"java_sources.sql",' ||
    '"last_ddl_time":"' || TO_CHAR((SELECT last_ddl_time FROM all_objects o WHERE o.owner = s.owner AND o.object_name = s.name AND o.object_type = 'JAVA SOURCE'), 'YYYY-MM-DD HH24:MI:SS') || '",' ||
    '"lines_of_code":' || MAX(line) || ',' ||
    '"note":"Migrar a PL/pgSQL, Python o Java externo en PostgreSQL"' ||
    '}'
FROM all_source s
WHERE type = 'JAVA SOURCE'
  AND owner IN ('LATINO_PLSQL')
GROUP BY owner, name
ORDER BY owner, name;

SELECT ']' FROM dual;

SPOOL OFF

-- =====================================================
-- FUNCIONES (ALL_SOURCE + delimitador / automático)
-- =====================================================
PROMPT Extrayendo FUNCTIONS...
SPOOL extracted/functions.sql

SET SERVEROUTPUT OFF

-- Agregar delimitador / entre objetos
SELECT
    CASE
        -- Detectar cambio de función: agregar / antes del nuevo objeto
        WHEN LAG(name) OVER (ORDER BY owner, name, line) IS NOT NULL
             AND LAG(name) OVER (ORDER BY owner, name, line) != name THEN
            '/' || CHR(10) || text
        -- Primera línea del archivo o líneas normales
        ELSE
            text
    END AS text
FROM all_source
WHERE type = 'FUNCTION'
  AND owner IN ('LATINO_PLSQL')
ORDER BY owner, name, line;

-- Agregar delimitador final después de la última función
SELECT '/' || CHR(10) FROM dual;

SPOOL OFF

-- =====================================================
-- PROCEDIMIENTOS (ALL_SOURCE + delimitador / automático)
-- =====================================================
PROMPT Extrayendo PROCEDURES...
SPOOL extracted/procedures.sql

-- Agregar delimitador / entre objetos
SELECT
    CASE
        -- Detectar cambio de procedure: agregar / antes del nuevo objeto
        WHEN LAG(name) OVER (ORDER BY owner, name, line) IS NOT NULL
             AND LAG(name) OVER (ORDER BY owner, name, line) != name THEN
            '/' || CHR(10) || text
        -- Primera línea del archivo o líneas normales
        ELSE
            text
    END AS text
FROM all_source
WHERE type = 'PROCEDURE'
  AND owner IN ('LATINO_PLSQL')
ORDER BY owner, name, line;

-- Agregar delimitador final
SELECT '/' || CHR(10) FROM dual;

SPOOL OFF

-- =====================================================
-- PACKAGES SPEC (ALL_SOURCE + delimitador / automático)
-- =====================================================
PROMPT Extrayendo PACKAGE SPECS...
SPOOL extracted/packages_spec.sql

-- Agregar delimitador / entre objetos
SELECT
    CASE
        -- Detectar cambio de package: agregar / antes del nuevo objeto
        WHEN LAG(name) OVER (ORDER BY owner, name, line) IS NOT NULL
             AND LAG(name) OVER (ORDER BY owner, name, line) != name THEN
            '/' || CHR(10) || text
        -- Primera línea del archivo o líneas normales
        ELSE
            text
    END AS text
FROM all_source
WHERE type = 'PACKAGE'
  AND owner IN ('LATINO_PLSQL')
  AND name != 'ORA_EXCEL'  -- Excluir librería ORA_EXCEL (no migrable a PostgreSQL)
ORDER BY owner, name, line;

-- Agregar delimitador final
SELECT '/' || CHR(10) FROM dual;

SPOOL OFF

-- =====================================================
-- PACKAGES BODY (ALL_SOURCE + delimitador / automático)
-- =====================================================
PROMPT Extrayendo PACKAGE BODIES...
SPOOL extracted/packages_body.sql

-- Agregar delimitador / entre objetos
SELECT
    CASE
        -- Detectar cambio de package body: agregar / antes del nuevo objeto
        WHEN LAG(name) OVER (ORDER BY owner, name, line) IS NOT NULL
             AND LAG(name) OVER (ORDER BY owner, name, line) != name THEN
            '/' || CHR(10) || text
        -- Primera línea del archivo o líneas normales
        ELSE
            text
    END AS text
FROM all_source
WHERE type = 'PACKAGE BODY'
  AND owner IN ('LATINO_PLSQL')
  AND name != 'ORA_EXCEL'  -- Excluir librería ORA_EXCEL (no migrable a PostgreSQL)
ORDER BY owner, name, line;

-- Agregar delimitador final
SELECT '/' || CHR(10) FROM dual;

SPOOL OFF

-- =====================================================
-- TRIGGERS (ALL_SOURCE + delimitador / automático)
-- =====================================================
PROMPT Extrayendo TRIGGERS...
SPOOL extracted/triggers.sql

-- Agregar delimitador / entre objetos
SELECT
    CASE
        -- Detectar cambio de trigger: agregar / antes del nuevo objeto
        WHEN LAG(name) OVER (ORDER BY owner, name, line) IS NOT NULL
             AND LAG(name) OVER (ORDER BY owner, name, line) != name THEN
            '/' || CHR(10) || text
        -- Primera línea del archivo o líneas normales
        ELSE
            text
    END AS text
FROM all_source
WHERE type = 'TRIGGER'
  AND owner IN ('LATINO_OWNER')
ORDER BY owner, name, line;

-- Agregar delimitador final
SELECT '/' || CHR(10) FROM dual;

SPOOL OFF

-- =====================================================
-- JAVA SOURCE (ALL_SOURCE directo - solo código)
-- =====================================================
PROMPT Extrayendo JAVA SOURCE...
SPOOL extracted/java_sources.sql

SELECT text
FROM all_source
WHERE type = 'JAVA SOURCE'
  AND owner IN ('LATINO_PLSQL')
ORDER BY owner, name, line;

SPOOL OFF

-- =====================================================
-- TABLAS, CONSTRAINTS, SEQUENCES, etc.
-- (Usar DBMS_METADATA - funcionan bien sin partición)
-- =====================================================
SET SERVEROUTPUT ON SIZE UNLIMITED

-- Configurar DBMS_METADATA
BEGIN
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SQLTERMINATOR', TRUE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'PRETTY', TRUE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SEGMENT_ATTRIBUTES', FALSE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'STORAGE', FALSE);
END;
/

-- A partir de aquí, copiar el resto del script original extract_all_objects.sql
-- Desde la línea 248 (TABLES) hasta el final (línea 893)
-- Las siguientes secciones NO necesitan cambios porque funcionan bien con DBMS_METADATA:
--   - TABLES
--   - PRIMARY KEYS
--   - FOREIGN KEYS
--   - CHECK CONSTRAINTS
--   - SEQUENCES
--   - TYPES
--   - VIEWS
--   - MATERIALIZED VIEWS
--   - DIRECTORIES
--   - JOBS
--   - INVENTORY

-- [COPIAR AQUI LINEAS 248-893 del script original]

PROMPT
PROMPT =====================================================
PROMPT Extraccion completada (v2)
PROMPT
PROMPT CODIGO FUENTE (ALL_SOURCE - SIN particion):
PROMPT   - functions.sql
-- TABLES (DDL) - ESTRUCTURA + CONSTRAINTS SEPARADOS
-- =====================================================
PROMPT =====================================================
PROMPT Extrayendo TABLES + CONSTRAINTS
PROMPT =====================================================

-- =====================================================
-- TABLAS - ESTRUCTURA
-- =====================================================
PROMPT Extrayendo estructura de TABLES...

SPOOL extracted/tables.sql

DECLARE
    v_sql CLOB;
    v_col_list CLOB;
    v_first BOOLEAN;
    v_default_val LONG;
BEGIN
    -- Header
    DBMS_OUTPUT.PUT_LINE('-- ============================================');
    DBMS_OUTPUT.PUT_LINE('-- ESTRUCTURA DE TABLAS - LATINO_OWNER');
    DBMS_OUTPUT.PUT_LINE('-- Fecha: ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS'));
    DBMS_OUTPUT.PUT_LINE('-- ============================================');
    DBMS_OUTPUT.PUT_LINE('');

    -- Iterar sobre cada tabla
    FOR t IN (
        SELECT owner, table_name, num_rows, tablespace_name
        FROM all_tables
        WHERE owner = 'LATINO_OWNER'
          AND table_name NOT LIKE 'BIN$%'
        ORDER BY table_name
    ) LOOP
        BEGIN
            -- Header de la tabla
            DBMS_OUTPUT.PUT_LINE('-- Tabla: ' || t.table_name);
            DBMS_OUTPUT.PUT_LINE('-- Filas: ' || NVL(t.num_rows, 0));
            DBMS_OUTPUT.PUT_LINE('-- Tablespace: ' || t.tablespace_name);
            DBMS_OUTPUT.PUT_LINE('CREATE TABLE ' || t.owner || '.' || t.table_name);
            DBMS_OUTPUT.PUT_LINE('(');

            -- Construir lista de columnas
            v_first := TRUE;
            FOR c IN (
                SELECT
                    column_name,
                    data_type,
                    char_length,
                    char_used,
                    data_precision,
                    data_scale,
                    data_length,
                    nullable,
                    data_default
                FROM all_tab_columns
                WHERE owner = t.owner
                  AND table_name = t.table_name
                ORDER BY column_id
            ) LOOP
                -- Agregar coma excepto en primera columna
                IF NOT v_first THEN
                    DBMS_OUTPUT.PUT_LINE(',');
                END IF;
                v_first := FALSE;

                -- Construir definición de columna
                v_col_list := '    ' || c.column_name || ' ' || c.data_type;

                -- Agregar tamaño según tipo de dato
                IF c.data_type IN ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR') THEN
                    v_col_list := v_col_list || '(' || c.char_length;
                    IF c.char_used = 'C' THEN
                        v_col_list := v_col_list || ' CHAR';
                    END IF;
                    v_col_list := v_col_list || ')';
                ELSIF c.data_type = 'NUMBER' AND c.data_precision IS NOT NULL THEN
                    v_col_list := v_col_list || '(' || c.data_precision;
                    IF c.data_scale > 0 THEN
                        v_col_list := v_col_list || ',' || c.data_scale;
                    END IF;
                    v_col_list := v_col_list || ')';
                ELSIF c.data_type = 'RAW' THEN
                    v_col_list := v_col_list || '(' || c.data_length || ')';
                ELSIF c.data_type LIKE 'TIMESTAMP%' AND c.data_scale IS NOT NULL THEN
                    v_col_list := v_col_list || '(' || c.data_scale || ')';
                END IF;

                -- DEFAULT value (manejo especial para LONG)
                IF c.data_default IS NOT NULL THEN
                    BEGIN
                        -- Convertir LONG a VARCHAR2 (máximo 4000 chars)
                        v_default_val := c.data_default;
                        -- Remover espacios en blanco al inicio/final
                        v_default_val := LTRIM(RTRIM(v_default_val));
                        -- Limitar a 4000 caracteres para evitar overflow
                        IF LENGTH(v_default_val) > 0 THEN
                            v_col_list := v_col_list || ' DEFAULT ' || SUBSTR(v_default_val, 1, 4000);
                        END IF;
                    EXCEPTION
                        WHEN OTHERS THEN
                            -- Si falla, ignorar el DEFAULT
                            NULL;
                    END;
                END IF;

                -- NOT NULL
                IF c.nullable = 'N' THEN
                    v_col_list := v_col_list || ' NOT NULL';
                END IF;

                DBMS_OUTPUT.PUT(v_col_list);
            END LOOP;

            DBMS_OUTPUT.PUT_LINE('');
            DBMS_OUTPUT.PUT_LINE(');');
            DBMS_OUTPUT.PUT_LINE('');

        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('-- ERROR extrayendo tabla ' || t.table_name || ': ' || SQLERRM);
                DBMS_OUTPUT.PUT_LINE('');
        END;
    END LOOP;
END;
/

SPOOL OFF

-- =====================================================
-- PRIMARY KEYS
-- =====================================================
PROMPT Extrayendo PRIMARY KEYS...
SPOOL extracted/primary_keys.sql

-- Header
SELECT '-- ============================================' || CHR(10) ||
       '-- PRIMARY KEYS - LATINO_OWNER' || CHR(10) ||
       '-- Fecha: ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') || CHR(10) ||
       '-- ============================================' || CHR(10) || CHR(10)
FROM dual;

-- Generar ALTER TABLE ADD PRIMARY KEY
SELECT
    '-- Tabla: ' || c.owner || '.' || c.table_name || CHR(10) ||
    '-- Constraint: ' || c.constraint_name || CHR(10) ||
    '-- Columnas: ' ||
    (
        SELECT LISTAGG(cc.column_name, ', ') WITHIN GROUP (ORDER BY cc.position)
        FROM all_cons_columns cc
        WHERE cc.constraint_name = c.constraint_name
          AND cc.owner = c.owner
    ) || CHR(10) ||
    '-- Status: ' || c.status || CHR(10) ||
    'ALTER TABLE ' || c.owner || '.' || c.table_name || CHR(10) ||
    '    ADD CONSTRAINT ' || c.constraint_name || CHR(10) ||
    '    PRIMARY KEY (' ||
    (
        SELECT LISTAGG(cc.column_name, ', ') WITHIN GROUP (ORDER BY cc.position)
        FROM all_cons_columns cc
        WHERE cc.constraint_name = c.constraint_name
          AND cc.owner = c.owner
    ) || ')' || CHR(10) ||
    CASE WHEN c.status = 'ENABLED' THEN '    ENABLE' ELSE '    DISABLE' END ||
    ';' || CHR(10) || CHR(10)
FROM all_constraints c
WHERE c.constraint_type = 'P'
  AND c.owner = 'LATINO_OWNER'
  AND c.table_name NOT LIKE 'BIN$%'
ORDER BY c.table_name, c.constraint_name;

SPOOL OFF

-- =====================================================
-- FOREIGN KEYS
-- =====================================================
PROMPT Extrayendo FOREIGN KEYS...
SPOOL extracted/foreign_keys.sql

-- Header
SELECT '-- ============================================' || CHR(10) ||
       '-- FOREIGN KEYS - LATINO_OWNER' || CHR(10) ||
       '-- Fecha: ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') || CHR(10) ||
       '-- ============================================' || CHR(10) || CHR(10)
FROM dual;

-- Generar ALTER TABLE ADD FOREIGN KEY
SELECT
    '-- Tabla: ' || c.owner || '.' || c.table_name || CHR(10) ||
    '-- Constraint: ' || c.constraint_name || CHR(10) ||
    '-- Columnas: ' ||
    (
        SELECT LISTAGG(cc.column_name, ', ') WITHIN GROUP (ORDER BY cc.position)
        FROM all_cons_columns cc
        WHERE cc.constraint_name = c.constraint_name
          AND cc.owner = c.owner
    ) || CHR(10) ||
    '-- Referencia: ' || rc.owner || '.' || rc.table_name || ' (' ||
    (
        SELECT LISTAGG(rcc.column_name, ', ') WITHIN GROUP (ORDER BY rcc.position)
        FROM all_cons_columns rcc
        WHERE rcc.constraint_name = c.r_constraint_name
          AND rcc.owner = c.r_owner
    ) || ')' || CHR(10) ||
    '-- Status: ' || c.status || CHR(10) ||
    '-- Delete Rule: ' || c.delete_rule || CHR(10) ||
    'ALTER TABLE ' || c.owner || '.' || c.table_name || CHR(10) ||
    '    ADD CONSTRAINT ' || c.constraint_name || CHR(10) ||
    '    FOREIGN KEY (' ||
    (
        SELECT LISTAGG(cc.column_name, ', ') WITHIN GROUP (ORDER BY cc.position)
        FROM all_cons_columns cc
        WHERE cc.constraint_name = c.constraint_name
          AND cc.owner = c.owner
    ) || ')' || CHR(10) ||
    '    REFERENCES ' || rc.owner || '.' || rc.table_name || ' (' ||
    (
        SELECT LISTAGG(rcc.column_name, ', ') WITHIN GROUP (ORDER BY rcc.position)
        FROM all_cons_columns rcc
        WHERE rcc.constraint_name = c.r_constraint_name
          AND rcc.owner = c.r_owner
    ) || ')' || CHR(10) ||
    CASE
        WHEN c.delete_rule = 'CASCADE' THEN '    ON DELETE CASCADE' || CHR(10)
        WHEN c.delete_rule = 'SET NULL' THEN '    ON DELETE SET NULL' || CHR(10)
        ELSE ''
    END ||
    CASE WHEN c.status = 'ENABLED' THEN '    ENABLE' ELSE '    DISABLE' END ||
    ';' || CHR(10) || CHR(10)
FROM all_constraints c
INNER JOIN all_constraints rc ON c.r_constraint_name = rc.constraint_name
                              AND c.r_owner = rc.owner
WHERE c.constraint_type = 'R'
  AND c.owner = 'LATINO_OWNER'
  AND c.table_name NOT LIKE 'BIN$%'
ORDER BY c.table_name, c.constraint_name;

SPOOL OFF

-- =====================================================
-- CHECK CONSTRAINTS
-- =====================================================
PROMPT Extrayendo CHECK CONSTRAINTS...

SPOOL extracted/check_constraints.sql

-- Header
SELECT '-- ============================================' FROM dual;
SELECT '-- CHECK CONSTRAINTS - LATINO_OWNER' FROM dual;
SELECT '-- Fecha: ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') FROM dual;
SELECT '-- ============================================' FROM dual;
SELECT '' FROM dual;

-- Extraer cada constraint individualmente
DECLARE
    v_search_condition LONG;
    v_output VARCHAR2(32767);
    v_count NUMBER := 0;

    CURSOR c_constraints IS
        SELECT
            c.owner,
            c.table_name,
            c.constraint_name,
            c.status,
            c.validated
        FROM all_constraints c
        WHERE c.constraint_type = 'C'
          AND c.owner = 'LATINO_OWNER'
          AND c.table_name NOT LIKE 'BIN$%'
          AND c.constraint_name NOT LIKE 'SYS_%'
          AND c.search_condition IS NOT NULL
        ORDER BY c.table_name, c.constraint_name;
BEGIN
    FOR rec IN c_constraints LOOP
        BEGIN
            v_count := v_count + 1;

            -- Obtener search_condition (tipo LONG)
            SELECT search_condition
            INTO v_search_condition
            FROM all_constraints
            WHERE owner = rec.owner
              AND constraint_name = rec.constraint_name;

            -- Escribir header del constraint
            DBMS_OUTPUT.PUT_LINE('-- Tabla: ' || rec.owner || '.' || rec.table_name);
            DBMS_OUTPUT.PUT_LINE('-- Constraint: ' || rec.constraint_name);
            DBMS_OUTPUT.PUT_LINE('-- Status: ' || rec.status);
            DBMS_OUTPUT.PUT_LINE('-- Validated: ' || rec.validated);

            -- Escribir el ALTER TABLE
            DBMS_OUTPUT.PUT_LINE('ALTER TABLE ' || rec.owner || '.' || rec.table_name);
            DBMS_OUTPUT.PUT_LINE('    ADD CONSTRAINT ' || rec.constraint_name);

            -- Escribir CHECK con la condición completa
            DBMS_OUTPUT.PUT('    CHECK (');

            -- Escribir search_condition en chunks pequeños
            DECLARE
                v_pos INTEGER := 1;
                v_chunk_size CONSTANT INTEGER := 200;
                v_len INTEGER;
                v_chunk VARCHAR2(200);
            BEGIN
                v_len := LENGTH(v_search_condition);

                WHILE v_pos <= v_len LOOP
                    v_chunk := SUBSTR(v_search_condition, v_pos, v_chunk_size);
                    DBMS_OUTPUT.PUT(v_chunk);
                    v_pos := v_pos + v_chunk_size;
                END LOOP;
            END;

            DBMS_OUTPUT.PUT_LINE(')');

            -- Status ENABLE/DISABLE
            IF rec.status = 'ENABLED' THEN
                DBMS_OUTPUT.PUT_LINE('    ENABLE');
            ELSE
                DBMS_OUTPUT.PUT_LINE('    DISABLE');
            END IF;

            -- Validated
            IF rec.validated = 'VALIDATED' THEN
                DBMS_OUTPUT.PUT_LINE('    VALIDATE');
            ELSIF rec.validated = 'NOT VALIDATED' THEN
                DBMS_OUTPUT.PUT_LINE('    NOVALIDATE');
            END IF;

            DBMS_OUTPUT.PUT_LINE(';');
            DBMS_OUTPUT.PUT_LINE('');

        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('-- ERROR: ' || rec.constraint_name || ' - ' || SQLERRM);
                DBMS_OUTPUT.PUT_LINE('');
        END;
    END LOOP;

    -- Footer con total
    DBMS_OUTPUT.PUT_LINE('-- ============================================');
    DBMS_OUTPUT.PUT_LINE('-- Total CHECK constraints: ' || v_count);
    DBMS_OUTPUT.PUT_LINE('-- ============================================');

EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('-- ERROR GENERAL: ' || SQLERRM);
END;
/

SPOOL OFF

-- =====================================================
-- SEQUENCES
-- =====================================================
PROMPT Extrayendo SEQUENCES...
SPOOL extracted/sequences.sql

SELECT '-- ============================================' || CHR(10) ||
       '-- Schema: ' || o.owner || CHR(10) ||
       '-- Secuencia: ' || o.object_name || CHR(10) ||
       '-- Ultima modificacion: ' || TO_CHAR(o.last_ddl_time, 'YYYY-MM-DD HH24:MI:SS') || CHR(10) ||
       '-- Valor actual: ' || s.last_number || CHR(10) ||
       '-- Incremento: ' || s.increment_by || CHR(10) ||
       '-- Cache: ' || s.cache_size || CHR(10) ||
       '-- Min Value: ' || s.min_value || CHR(10) ||
       '-- Max Value: ' || s.max_value || CHR(10) ||
       '-- Cycle: ' || s.cycle_flag || CHR(10) ||
       '-- ============================================' || CHR(10) ||
       DBMS_METADATA.GET_DDL('SEQUENCE', o.object_name, o.owner) || CHR(10) || CHR(10)
FROM all_objects o
INNER JOIN all_sequences s ON o.object_name = s.sequence_name AND o.owner = s.sequence_owner
WHERE o.object_type = 'SEQUENCE'
  AND o.owner IN ('LATINO_OWNER')
ORDER BY o.owner, o.object_name;

SPOOL OFF

-- =====================================================
-- TYPES (Object Types)
-- =====================================================
PROMPT Extrayendo TYPES...
SPOOL extracted/types.sql

SELECT '-- ============================================' || CHR(10) ||
       '-- Schema: ' || o.owner || CHR(10) ||
       '-- Objeto: ' || o.object_name || CHR(10) ||
       '-- Tipo: TYPE' || CHR(10) ||
       '-- Ultima modificacion: ' || TO_CHAR(o.last_ddl_time, 'YYYY-MM-DD HH24:MI:SS') || CHR(10) ||
       '-- ============================================' || CHR(10) ||
       DBMS_METADATA.GET_DDL('TYPE', o.object_name, o.owner) || CHR(10) || CHR(10)
FROM all_objects o
WHERE o.object_type = 'TYPE'
  AND o.owner IN ('LATINO_OWNER')
  AND o.object_name NOT LIKE 'SYS_%'  -- Excluir tipos del sistema
ORDER BY o.owner, o.object_name;

SPOOL OFF

-- =====================================================
-- VIEWS
-- =====================================================
PROMPT Extrayendo VIEWS...
SPOOL extracted/views.sql

SELECT '-- ============================================' || CHR(10) ||
       '-- Schema: ' || o.owner || CHR(10) ||
       '-- Vista: ' || o.object_name || CHR(10) ||
       '-- Ultima modificacion: ' || TO_CHAR(o.last_ddl_time, 'YYYY-MM-DD HH24:MI:SS') || CHR(10) ||
       '-- ============================================' || CHR(10) ||
       DBMS_METADATA.GET_DDL('VIEW', o.object_name, o.owner) || CHR(10) || CHR(10)
FROM all_objects o
WHERE o.object_type = 'VIEW'
  AND o.owner IN ('LATINO_OWNER')
  AND o.object_name NOT LIKE 'BIN$%'
ORDER BY o.owner, o.object_name;

SPOOL OFF

-- =====================================================
-- MATERIALIZED VIEWS
-- =====================================================
PROMPT Extrayendo MATERIALIZED VIEWS...
SPOOL extracted/materialized_views.sql

SELECT '-- ============================================' || CHR(10) ||
       '-- Schema: ' || o.owner || CHR(10) ||
       '-- MView: ' || o.object_name || CHR(10) ||
       '-- Ultima modificacion: ' || TO_CHAR(o.last_ddl_time, 'YYYY-MM-DD HH24:MI:SS') || CHR(10) ||
       '-- Refresh Method: ' || m.refresh_method || CHR(10) ||
       '-- Refresh Mode: ' || m.refresh_mode || CHR(10) ||
       '-- ============================================' || CHR(10) ||
       DBMS_METADATA.GET_DDL('MATERIALIZED_VIEW', o.object_name, o.owner) || CHR(10) || CHR(10)
FROM all_objects o
INNER JOIN all_mviews m ON o.object_name = m.mview_name AND o.owner = m.owner
WHERE o.object_type = 'MATERIALIZED VIEW'
  AND o.owner IN ('LATINO_OWNER')
ORDER BY o.owner, o.object_name;

SPOOL OFF

-- =====================================================
-- DIRECTORIES
-- =====================================================
PROMPT Extrayendo DIRECTORIES...
SPOOL extracted/directories.sql

SELECT '-- ============================================' || CHR(10) ||
       '-- Directory: ' || directory_name || CHR(10) ||
       '-- Owner: ' || owner || CHR(10) ||
       '-- Path: ' || directory_path || CHR(10) ||
       '-- ============================================' || CHR(10) ||
       'CREATE OR REPLACE DIRECTORY ' || directory_name || CHR(10) ||
       'AS ''' || directory_path || ''';' || CHR(10) || CHR(10)
FROM all_directories
WHERE directory_name LIKE 'DIR_DOC_%'
ORDER BY owner, directory_name;

SPOOL OFF

-- =====================================================
-- JOBS
-- =====================================================
PROMPT Extrayendo JOBS...
SPOOL extracted/jobs.sql

SELECT
    '-- JOB: ' || job_name || CHR(10) ||
    '-- Tipo: ' || job_type || CHR(10) ||
    '-- Estado: ' || (CASE WHEN enabled = 'TRUE' THEN 'ENABLED' ELSE 'DISABLED' END) || CHR(10) ||
    DBMS_METADATA.GET_DDL('PROCOBJ', job_name, owner) || CHR(10) ||
    '/' || CHR(10) || CHR(10)
FROM all_scheduler_jobs
WHERE owner = 'LATINO_PLSQL'
ORDER BY job_name;

SPOOL OFF

-- =====================================================
-- RESUMEN E INVENTARIO
-- =====================================================
PROMPT Generando inventario...
SPOOL extracted/inventory.md

SELECT '# Inventario de Objetos Extraídos' || CHR(10) || CHR(10) FROM dual;
SELECT '**Fecha extracción:** ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') || CHR(10) FROM dual;
SELECT '**Base de datos:** ' || SYS_CONTEXT('USERENV', 'DB_NAME') || CHR(10) FROM dual;
SELECT '**Usuario:** ' || SYS_CONTEXT('USERENV', 'SESSION_USER') || CHR(10) || CHR(10) FROM dual;

SELECT '## Resumen por Tipo de Objeto' || CHR(10) || CHR(10) FROM dual;
SELECT '| Tipo | Cantidad | Archivo |' || CHR(10) FROM dual;
SELECT '|------|----------|---------|' || CHR(10) FROM dual;

SELECT '| FUNCTION | ' || COUNT(*) || ' | extracted/functions.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'FUNCTION' AND owner IN ('LATINO_PLSQL');

SELECT '| PROCEDURE | ' || COUNT(*) || ' | extracted/procedures.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'PROCEDURE' AND owner IN ('LATINO_PLSQL');

SELECT '| PACKAGE (SPEC) | ' || COUNT(*) || ' | extracted/packages_spec.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'PACKAGE' AND owner IN ('LATINO_PLSQL');

SELECT '| PACKAGE BODY | ' || COUNT(*) || ' | extracted/packages_body.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'PACKAGE BODY' AND owner IN ('LATINO_PLSQL');

SELECT '| TRIGGER | ' || COUNT(*) || ' | extracted/triggers.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'TRIGGER' AND owner IN ('LATINO_OWNER');

SELECT '| JAVA SOURCE | ' || COUNT(*) || ' | extracted/java_sources.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'JAVA SOURCE' AND owner IN ('LATINO_PLSQL');

SELECT '| TABLE | ' || COUNT(*) || ' | extracted/tables.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'TABLE' AND object_name NOT LIKE 'BIN$%' AND owner IN ('LATINO_OWNER');

SELECT '| PRIMARY KEY | ' || COUNT(*) || ' | extracted/primary_keys.sql |' || CHR(10)
FROM all_constraints WHERE constraint_type = 'P' AND owner IN ('LATINO_OWNER') AND table_name NOT LIKE 'BIN$%';

SELECT '| FOREIGN KEY | ' || COUNT(*) || ' | extracted/foreign_keys.sql |' || CHR(10)
FROM all_constraints WHERE constraint_type = 'R' AND owner IN ('LATINO_OWNER') AND table_name NOT LIKE 'BIN$%';

SELECT '| CHECK CONSTRAINTS | ' || COUNT(*) || ' | extracted/check_constraints.sql |' || CHR(10)
FROM all_constraints WHERE constraint_type = 'C' AND owner = 'LATINO_OWNER' AND table_name NOT LIKE 'BIN$%' AND constraint_name NOT LIKE 'SYS_%' AND UPPER(search_condition) NOT LIKE '%IS NOT NULL%';

SELECT '| SEQUENCE | ' || COUNT(*) || ' | extracted/sequences.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'SEQUENCE' AND owner IN ('LATINO_OWNER');

SELECT '| TYPE | ' || COUNT(*) || ' | extracted/types.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'TYPE' AND object_name NOT LIKE 'SYS_%' AND owner IN ('LATINO_OWNER');

SELECT '| VIEW | ' || COUNT(*) || ' | extracted/views.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'VIEW' AND object_name NOT LIKE 'BIN$%' AND owner IN ('LATINO_OWNER');

SELECT '| MATERIALIZED VIEW | ' || COUNT(*) || ' | extracted/materialized_views.sql |' || CHR(10)
FROM all_objects WHERE object_type = 'MATERIALIZED VIEW' AND owner IN ('LATINO_OWNER');

SELECT '| DIRECTORY | ' || COUNT(*) || ' | extracted/directories.sql |' || CHR(10)
FROM all_directories;

SELECT '| JOB | ' || COUNT(*) || ' | extracted/jobs.sql |' || CHR(10)
FROM all_scheduler_jobs
WHERE owner = 'LATINO_PLSQL';

SELECT CHR(10) || '**Total de objetos de código:** ' || COUNT(*) || CHR(10) || CHR(10)
FROM all_objects
WHERE owner IN ('LATINO_OWNER', 'LATINO_PLSQL')
  AND object_type IN ('FUNCTION', 'PROCEDURE', 'PACKAGE', 'PACKAGE BODY', 'TRIGGER');

SELECT '**Total de objetos de estructura:** ' || COUNT(*) || CHR(10) || CHR(10)
FROM all_objects
WHERE owner IN ('LATINO_OWNER')
  AND object_type IN ('TABLE', 'SEQUENCE', 'TYPE', 'VIEW', 'MATERIALIZED VIEW');

-- Análisis por Schema
SELECT '## Distribución por Schema' || CHR(10) || CHR(10) FROM dual;
SELECT '| Schema | Objetos Código | Objetos Estructura |' || CHR(10) FROM dual;
SELECT '|--------|----------------|-------------------|' || CHR(10) FROM dual;

SELECT '| ' || owner || ' | ' ||
       (SELECT COUNT(*) FROM all_objects o2
        WHERE o2.owner = o1.owner
          AND o2.owner = 'LATINO_PLSQL'
          AND o2.object_type IN ('FUNCTION', 'PROCEDURE', 'PACKAGE', 'PACKAGE BODY', 'TRIGGER')) ||
       ' | ' ||
       (SELECT COUNT(*) FROM all_objects o3
        WHERE o3.owner = o1.owner
          AND o3.owner = 'LATINO_OWNER'
          AND o3.object_type IN ('TABLE', 'SEQUENCE', 'TYPE', 'VIEW', 'MATERIALIZED VIEW')) ||
       ' |' || CHR(10)
FROM (SELECT DISTINCT owner FROM all_objects WHERE owner IN ('LATINO_OWNER','LATINO_PLSQL')) o1;

-- Análisis de complejidad inicial
SELECT CHR(10) || '## Análisis Inicial de Complejidad' || CHR(10) || CHR(10) FROM dual;
SELECT '### Packages con mayor cantidad de líneas (Top 20)' || CHR(10) || CHR(10) FROM dual;
SELECT '| Schema | Package | Líneas (SPEC) | Líneas (BODY) | Total |' || CHR(10) FROM dual;
SELECT '|--------|---------|---------------|---------------|-------|' || CHR(10) FROM dual;

SELECT '| ' || owner || ' | ' || name || ' | ' || spec_lines || ' | ' || body_lines || ' | ' || total_lines || ' |' || CHR(10)
FROM (
    SELECT
        spec.owner,
        spec.name,
        MAX(spec.line) as spec_lines,
        NVL(MAX(body.line), 0) as body_lines,
        (NVL(MAX(body.line), 0) + MAX(spec.line)) as total_lines
    FROM
        (SELECT name, owner, line FROM all_source WHERE type = 'PACKAGE' AND owner IN ('LATINO_PLSQL')) spec
    LEFT JOIN
        (SELECT name, owner, line FROM all_source WHERE type = 'PACKAGE BODY' AND owner IN ('LATINO_PLSQL')) body
        ON spec.name = body.name AND spec.owner = body.owner
    GROUP BY spec.owner, spec.name
    ORDER BY (NVL(MAX(body.line), 0) + MAX(spec.line)) DESC
)
WHERE ROWNUM <= 20;

SELECT CHR(10) || '### Procedures/Functions con mayor cantidad de líneas (Top 20)' || CHR(10) || CHR(10) FROM dual;
SELECT '| Schema | Nombre | Tipo | Líneas |' || CHR(10) FROM dual;
SELECT '|--------|--------|------|--------|' || CHR(10) FROM dual;

SELECT '| ' || owner || ' | ' || name || ' | ' || type || ' | ' || lines || ' |' || CHR(10)
FROM (
    SELECT owner, name, type, MAX(line) as lines
    FROM all_source
    WHERE type IN ('PROCEDURE', 'FUNCTION')
      AND owner IN ('LATINO_PLSQL')
    GROUP BY owner, name, type
    ORDER BY MAX(line) DESC
)
WHERE ROWNUM <= 20;

SELECT CHR(10) || '### Tablas con mayor cantidad de filas (Top 20)' || CHR(10) || CHR(10) FROM dual;
SELECT '| Schema | Tabla | Filas (aprox) | Tablespace |' || CHR(10) FROM dual;
SELECT '|--------|-------|---------------|------------|' || CHR(10) FROM dual;

SELECT '| ' || owner || ' | ' || table_name || ' | ' || NVL(num_rows, 0) || ' | ' || tablespace_name || ' |' || CHR(10)
FROM (
    SELECT owner, table_name, num_rows, tablespace_name
    FROM all_tables
    WHERE owner IN ('LATINO_OWNER')
      AND table_name NOT LIKE 'BIN$%'
    ORDER BY NVL(num_rows, 0) DESC
)
WHERE ROWNUM <= 20;

SPOOL OFF

PROMPT
PROMPT =====================================================
PROMPT Extracción completada exitosamente
PROMPT
PROMPT Archivos generados en el directorio extracted/:
PROMPT   - metadata.json          (Info compilación: schema, objeto, tipo, fecha, líneas)
PROMPT   - functions.sql
PROMPT   - procedures.sql
PROMPT   - packages_spec.sql     (SOLO especificación, sin body)
PROMPT   - packages_body.sql     (excluye ORA_EXCEL)
PROMPT   - triggers.sql
PROMPT   - java_sources.sql      (3 objetos Java - migrar a PL/pgSQL o Python)
PROMPT   - tables.sql
PROMPT   - primary_keys.sql
PROMPT   - foreign_keys.sql
PROMPT   - check_constraints.sql
PROMPT   - sequences.sql
PROMPT   - types.sql
PROMPT   - views.sql
PROMPT   - materialized_views.sql
PROMPT   - directories.sql
PROMPT   - jobs.sql
PROMPT   - inventory.md
PROMPT
PROMPT =====================================================
