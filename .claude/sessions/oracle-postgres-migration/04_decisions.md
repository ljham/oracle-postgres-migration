# Technical Decisions - Oracle to PostgreSQL Migration

> **📖 Contexto del Proyecto:** Herramienta basada en agentes IA para migrar 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora) en 3 meses. Ver [00_index.md](./00_index.md) para resumen ejecutivo completo.

**Versión:** 2.0 | **Fecha:** 2025-12-31 | **Estado:** validated

---

## Decisiones Técnicas Clave

### Decision 1: Estado Compartido en Packages
**Opción elegida:** B - Session Variables (SET/current_setting)
**Razón:** El usuario considera que es más limpia que tablas temporales

**Implementación:**
```sql
-- Establecer variable de sesión
SET pkg_ventas.sucursal_id = '123';

-- Leer variable de sesión
SELECT current_setting('pkg_ventas.sucursal_id')::INTEGER;
```

---

### Decision 2: AUTONOMOUS_TRANSACTION
**Cantidad afectada:** ~40 objetos
**Estado extensiones Aurora:** ✅ dblink 1.2, aws_lambda 1.0, pg_cron 1.6 - TODAS disponibles

En oracle la opción de autonomous_transaction es una transacción que se ejecuta de forma independiente de la transacción principal.

Implementar una opción similar en postgres

Uso esperado:
- Realizar commit o rollback de una transacción sin afectar la transacción principal
- Verificar que no se crucen los commits/rollbacks entre transacciones

---

### Decision 3: Vector Database
**Opción elegida:** pgvector (extensión `vector`) en Amazon Aurora PostgreSQL
**Estado:** ✅ **vector 0.8.0 disponible en Aurora** - Listo para habilitar

**Validación completada:**
- ✅ Extensión pre-compilada disponible en Aurora PostgreSQL 17.4
- ✅ Versión: 0.8.0 (soporta HNSW y IVFFlat indexes)
- ✅ No requiere infraestructura adicional (managed service)
- ✅ Suficiente para el volumen de conocimiento del proyecto

**Habilitar con:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Uso esperado:**
- Almacenar embeddings de reglas de negocio
- Búsqueda semántica de conocimiento capturado
- Consultas sin re-análisis de código (optimización de tokens)

---

### Decision 4: Herramientas de Migración
**Estrategia híbrida corregida:**

**IMPORTANTE:** La extracción de objetos Oracle ya se realizó manualmente usando `sql/extract_all_objects.sql` ejecutado en sqlplus local. Los archivos resultantes están en `extracted/`.

**Flujo real:**
1. **Extracción (COMPLETADA)** ✅
   - Herramienta: Script SQL custom `extract_all_objects.sql`
   - Ejecutado localmente en sqlplus
   - Output: `extracted/*.sql` (8,122 objetos extraídos)

2. **Captura de Conocimiento** (Fase 1B - Paralelo)
   - Herramienta: Sub-agente Claude Code (Knowledge Extractor)
   - Input: TODOS los archivos en `extracted/`
   - Output: `knowledge/` (base de conocimiento + pgvector)
   - Rol: Extractor pasivo, NO analiza complejidad

3. **Análisis de Complejidad** (Fase 2 - Secuencial)
   - Herramienta: Sub-agente Claude Code (Complexity Analyzer - inteligente)
   - Input: `knowledge/` del Knowledge Extractor
   - Output: Clasificación SIMPLE vs COMPLEX con razonamiento
   - Rol: Usa experiencia de Claude para decidir estrategia de conversión

4. **Conversión de Objetos SIMPLES** (Fase 3A)
   - Herramienta: **ora2pg** (local)
   - Input: Lista de objetos simples + `extracted/*.sql`
   - Output: `migrated/simple/*.sql`
   - Razón: Conversión sintáctica automática suficiente (~70% de objetos)

5. **Conversión de Objetos COMPLEJOS** (Fase 3B)
   - Herramienta: Sub-agentes IA Claude Code
   - Input: Lista de objetos complejos + `knowledge/` (contexto)
   - Output: `migrated/complex/*.sql` + `decisions_log.md`
   - Razón: Requieren razonamiento arquitectónico (~30% de objetos)

**Optimización de tokens:**
- Code Comprehension Agent: Comprensión semántica con prompt especializado
- Migration Strategist: Decisión estratégica sobre conocimiento ya extraído
- Ambos usan razonamiento de Claude, pero con prompts especializados (más eficiente que prompt monolítico)
- Reutilización: Conocimiento extraído se almacena en pgvector (consulta sin re-análisis)
- Ahorro estimado: ~33% de tokens (16.3M vs 24.4M)
- ora2pg: 70% de objetos sin usar tokens de Claude
- Agentes IA: Solo 30% de objetos complejos que justifican tokens

---

### Decision 5: Separación de Responsabilidades entre Sub-agentes
**Enfoque:** Comprensión Semántica + Decisión Estratégica (NO mecánico vs inteligente)

**IMPORTANTE - Corrección de definiciones:**

La distinción NO es "mecánico vs inteligente" (ambos requieren razonamiento de Claude).
La distinción REAL es:

| Aspecto | Code Comprehension Agent (B) | Migration Strategist (C) |
|---------|------------------------------|--------------------------|
| **Pregunta** | "¿QUÉ hace este código?" | "¿CÓMO debemos migrarlo?" |
| **Análisis** | Comprensión semántica | Evaluación de riesgo |
| **Input** | Código PL/SQL raw | Conocimiento estructurado |
| **Output** | Hechos (descriptivo) | Decisiones (prescriptivo) |
| **Razonamiento** | ✅ Sí - code understanding | ✅ Sí - decision making |

**Analogía clara:**

```
Code Comprehension Agent = RADIÓLOGO
  → Interpreta la "tomografía" (código)
  → Pregunta: "¿Qué veo aquí?"
  → Output: Informe de hallazgos

Migration Strategist = MÉDICO
  → Evalúa el informe del radiólogo
  → Pregunta: "¿Qué tratamiento aplicamos?"
  → Output: Plan de acción
```

**Diferencia fundamental (una oración):**

> **Code Comprehension Agent COMPRENDE qué hace el código;
> Migration Strategist DECIDE qué hacer con él.**

---

### Decision 6: Migración de DIRECTORY Objects a AWS S3
**Problema:** PostgreSQL no soporta objetos DIRECTORY como Oracle
**Restricción Aurora:** Amazon Aurora NO permite acceso al filesystem del servidor
**Cantidad afectada:** 8 DIRECTORY objects + código PL/SQL que usa UTL_FILE
**Opción elegida:** AWS S3 con extensión `aws_s3` (LA ÚNICA OPCIÓN VIABLE)

**⚠️ CRÍTICO - Aurora PostgreSQL Managed Service:**
- ❌ **NO hay alternativa de filesystem local** - Aurora no permite escribir archivos en el servidor
- ❌ **COPY TO PROGRAM no funciona** - Requiere acceso shell que Aurora no permite
- ❌ **No se puede montar EFS directamente** - Sin acceso a configuración del sistema operativo
- ✅ **AWS S3 es la ÚNICA solución viable** - Extensión aws_s3 pre-instalada en Aurora
- ✅ **No requiere configuración de servidor** - Todo se hace vía SQL

**DIRECTORY objects Oracle identificados:**
```
DIR_DOC_APOYOS          → /compartidos/doc_apoyos
DIR_DOC_COMPRAS         → /compartidos/doc_compras
DIR_DOC_FINANZAS        → /compartidos/doc_finanzas
DIR_DOC_FOTOS           → /compartidos/doc_fotos
DIR_DOC_NOMINA          → /compartidos/doc_nomina
DIR_DOC_PAPERLESS       → /compartidos/doc_paperless
DIR_DOC_PORTAL          → /compartidos/portal
DIR_DOC_PORTAL_CONVENIOS → /compartidos/doc_portal_convenios
```

**Decisiones del usuario (COMPLETADAS ✅):**
1. ✅ **Nombre del bucket S3:** `efs-veris-compartidos-dev`
2. ✅ **Región AWS:** `us-east-1`
3. ✅ **Encriptación S3:** SSE-S3 (Server-Side Encryption estándar)
4. ✅ **Formato Excel (.xlsx):** **SÍ es necesario** - Hay lógica en paquetería Oracle que crea archivos .xlsx, .txt, .csv

**⚠️ CRÍTICO - Generación de archivos Excel (.xlsx):**

**Solución requerida - Opción A - AWS Lambda (RECOMENDADA):**
```
PostgreSQL → aws_s3 (genera CSV) → S3 bucket
                                      ↓
                           Lambda trigger (convierte CSV → XLSX)
                                      ↓
                           S3 bucket/excel/ (archivo final .xlsx)
```

---

### Decision 7: Consumo de APIs REST → AWS Lambda + Wrapper Functions
**Problema:** Aurora PostgreSQL NO soporta extensión `pgsql-http` para hacer HTTP requests desde PL/pgSQL
**Restricción Aurora:** Amazon Aurora NO permite extensiones custom que requieren compilación
**Cantidad afectada:** **< 100 objetos** usan UTL_HTTP para consumir APIs REST (CRÍTICO para negocio)
**Opción elegida:** AWS Lambda + aws_commons (ESTRATEGIA OFICIAL DE AWS)

**⚠️ CRÍTICO - Información del Usuario:**
- ✅ **< 100 objetos PL/SQL** consumen APIs REST usando UTL_HTTP (~12% del total)
- ✅ **Criticidad: MUST HAVE** - Sin esto el sistema no funciona
- ✅ **APIs mixtas:** Algunas internas (misma VPC), algunas externas (internet público)
- ✅ **Extensiones necesarias YA INSTALADAS:** aws_lambda 1.0, aws_commons 1.2

**Solución AWS Oficial:**

AWS publicó un blog post específico sobre este problema: ["Build a custom HTTP client in Amazon Aurora PostgreSQL and Amazon RDS for PostgreSQL: An alternative to Oracle's UTL_HTTP"](https://aws.amazon.com/blogs/database/build-a-custom-http-client-in-amazon-aurora-postgresql-and-amazon-rds-for-postgresql-an-alternative-to-oracles-utl_http/)

**Arquitectura:**

```
Oracle PL/SQL (UTL_HTTP)
  ├─ UTL_HTTP.BEGIN_REQUEST('https://api.example.com', 'POST')
  ├─ UTL_HTTP.SET_HEADER(req, 'Authorization', 'Bearer token')
  ├─ UTL_HTTP.WRITE_TEXT(req, '{"data":"value"}')
  └─ response := UTL_HTTP.GET_RESPONSE(req)
↓
AWS Lambda Function (Nodejs + Axios modules)
  ├─ Recibe JSON payload con todos los parámetros HTTP
  ├─ Hace HTTP request real a API (REST)
  ├─ Maneja autenticación (Basic, Bearer, OAuth, etc.)
  ├─ Procesa response (JSON, XML/SOAP, etc.)
  └─ Retorna response a PostgreSQL como JSON
```

**Functions requeridas:**

```sql
CREATE OR REPLACE FUNCTION consumir_api_rest(
    p_endpoint TEXT,
    p_metodo TEXT DEFAULT 'GET',
    p_body JSONB DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_payload JSONB;
    v_response JSONB;
BEGIN
    -- Armar payload para Lambda
    v_payload := jsonb_build_object(
        'endpoint', p_endpoint,
        'method', p_metodo,
        'body', p_body
    );
    
    -- Invocar Lambda (cambia 'tu-lambda-function-name')
    SELECT payload INTO v_response
    FROM aws_lambda.invoke(
        'arn:aws:lambda:us-east-1:123456789:function:tu-lambda-function-name',
        v_payload::TEXT,
        'RequestResponse'  -- Síncrono
    );
    
    RETURN v_response;
END;
$$ LANGUAGE plpgsql;
```

**Lambda Function (Nodejs + Axios):**

```javascript
// index.mjs (Node.js 18+)
export const handler = async (event) => {
    try {
        const { endpoint, method = 'GET', body = null, headers = {} } = event;
        
        // Validación básica
        if (!endpoint) {
            throw new Error('endpoint es requerido');
        }
        
        // Configurar request
        const options = {
            method: method.toUpperCase(),
            headers: {
                'Content-Type': 'application/json',
                ...headers
            }
        };
        
        // Agregar body si existe (POST, PUT, PATCH)
        if (body && ['POST', 'PUT', 'PATCH'].includes(options.method)) {
            options.body = typeof body === 'string' ? body : JSON.stringify(body);
        }
        
        // Hacer request
        const response = await fetch(endpoint, options);
        
        // Parsear respuesta
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType?.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }
        
        // Retornar respuesta estructurada
        return {
            statusCode: response.status,
            success: response.ok,
            data: data,
            headers: Object.fromEntries(response.headers.entries())
        };
        
    } catch (error) {
        // Manejo de errores
        return {
            statusCode: 500,
            success: false,
            error: error.message,
            data: null
        };
    }
};
```

**Configuración Lambda requerida:**

1. **VPC Configuration (para APIs internas):**
   - Lambda debe estar en misma VPC que Aurora
   - Security groups permiten Lambda → API endpoints

2. **Internet Access (para APIs externas):**
   - Lambda en VPC private subnet
   - NAT Gateway para acceso saliente a internet

3. **IAM Roles:**
   - Aurora → Lambda invoke permission
   - Lambda → VPC access permission
   - Lambda → CloudWatch Logs permission

**Ejemplo de conversión de código:**

```sql
-- ANTES (Oracle PL/SQL):
DECLARE
    req  UTL_HTTP.REQ;
    resp UTL_HTTP.RESP;
    value VARCHAR2(1024);
BEGIN
    req := UTL_HTTP.BEGIN_REQUEST('https://api.example.com/data', 'POST');
    UTL_HTTP.SET_HEADER(req, 'Content-Type', 'application/json');
    UTL_HTTP.SET_AUTHENTICATION(req, 'user', 'pass', 'Basic');
    UTL_HTTP.WRITE_TEXT(req, '{"key":"value"}');
    resp := UTL_HTTP.GET_RESPONSE(req);
    UTL_HTTP.READ_TEXT(resp, value);
    UTL_HTTP.END_RESPONSE(resp);

    DBMS_OUTPUT.PUT_LINE(value);
END;

-- DESPUÉS (PostgreSQL PL/pgSQL):
DO $$
DECLARE
    req  INTEGER;
    resp JSON;
    value TEXT;
BEGIN
    -- GET simple
    SELECT consumir_api_rest('https://api.ejemplo.com/usuarios/123');

    -- POST con body
    SELECT consumir_api_rest(
        'https://api.ejemplo.com/usuarios',
        'POST',
        '{"nombre": "Juan", "email": "juan@test.com"}'::jsonb
    );

END;
$$;
```

**Pros:**
- ✅ Estrategia oficial de AWS (documentada y soportada)
- ✅ API casi idéntica a UTL_HTTP (conversión mínima) no usar tabla temporal
- ✅ Extensiones necesarias YA instaladas (aws_lambda, aws_commons)
- ✅ Lambda puede acceder APIs internas (VPC) y externas (NAT Gateway)
- ✅ Código de ejemplo disponible en GitHub (aws-samples)

**Cons:**
- ❌ Overhead de latencia (Lambda invoke + cold start)
- ❌ Requiere infraestructura adicional (Lambda, VPC config, NAT Gateway)
- ❌ Conversión no es automática
- ❌ Límite timeout Lambda (máximo 15 minutos para APIs lentas)

**Decisiones del usuario:**
1. ✅ **Cantidad afectada:** < 100 objetos confirmados
2. ✅ **Ubicación APIs:** Mixtas (internas VPC + externas internet)
3. ✅ **Criticidad:** MUST HAVE (sistema no funciona sin esto)
4. ⏳ **Volumen exacto:** Por determinar en Fase 1 (análisis del código)

**Próximos pasos:**
1. ⚠️ **Fase 1:** Code Comprehension Agent identifica TODOS los usos de UTL_HTTP
2. ⚠️ **Fase 1:** Catalogar todas las APIs consumidas (URLs, autenticación, formato)
3. ⚠️ **Pre-Fase 1:** Crear Lambda HTTP client (Nodejs + Axios)
4. ⚠️ **Pre-Fase 1:** Crear function PL/pgSQL
5. ⚠️ **Fase 2:** Migration Strategist clasifica objetos según complejidad API
6. ⚠️ **Fase 3:** Convertir código Oracle → function
7. ⚠️ **Fase 4:** Shadow testing (validar responses idénticas)

**Referencias:**
- [AWS Blog - Build custom HTTP client for Aurora PostgreSQL](https://aws.amazon.com/blogs/database/build-a-custom-http-client-in-amazon-aurora-postgresql-and-amazon-rds-for-postgresql-an-alternative-to-oracles-utl_http/)
- [GitHub - aws-samples/wrapper-for-utl-http-with-amazon-aurora](https://github.com/aws-samples/wrapper-for-utl-http-with-amazon-aurora)

---

### Decision 8: DBMS_SQL Conversion Strategy
**Status:** ⏳ **DEFERRED** - Pending post-scan analysis
**Fecha:** 2025-12-31 (detectado durante discovery refinement)

**Problema:**
Oracle usa DBMS_SQL (paquete PL/SQL nativo) para SQL dinámico complejo que difiere de EXECUTE IMMEDIATE.

**Cantidad estimada afectada:** < 20 objetos (confirmación exacta pendiente en Fase 1)

**Ejemplo de uso real detectado:**
```sql
-- Package RHH_K_ADMINISTRA_FORMULA (líneas 95-107)
Li_IdCursor := DBMS_SQL.Open_Cursor;
DBMS_SQL.Parse(Li_IdCursor, Gv_StmPlSql, DBMS_SQL.Native);
DBMS_SQL.Bind_Variable(Li_IdCursor, ':Pi_IdCursor', Pi_IdCursor);
Li_Ok := DBMS_SQL.Execute(Li_IdCursor);
DBMS_SQL.Close_Cursor(Li_IdCursor);
```

**Opciones de conversión:**

| Opción | Descripción | Pros | Cons |
|--------|-------------|------|------|
| **A: EXECUTE + format()** | Convertir a PL/pgSQL nativo | ✅ Nativo PostgreSQL<br>✅ Rápido | ⚠️ Requiere refactoring |
| **B: Wrapper functions** | Crear funciones helper | ✅ Conversión 1:1<br>✅ Menos refactoring | ⚠️ Overhead funciones |
| **C: EXECUTE USING** | Usar bind parameters PG | ✅ Más seguro | ⚠️ API diferente |

**Decisión:** Se tomará después del scan basado en:
1. Cantidad exacta de objetos afectados
2. Complejidad de las operaciones DBMS_SQL
3. Patrones de uso comunes detectados
4. Impacto en timeline (3 meses)

**Próximos pasos:**
1. ⏳ Code Comprehension Agent detecta todos los usos de DBMS_SQL
2. ⏳ Analizar patrones de uso (¿todos similares o diversos?)
3. ⏳ Evaluar si son objetos CRITICAL o pueden marcarse COMPLEX
4. ⏳ Tomar decisión definitiva con métricas reales

---

### Decision 9: Collection Types Mapping
**Status:** ⏳ **DEFERRED** - Pending post-scan analysis
**Fecha:** 2025-12-31 (detectado durante discovery refinement)

**Problema:**
Oracle usa múltiples tipos de colección que no tienen equivalencia directa en PostgreSQL:

**Tipos Oracle detectados:**
1. `TABLE OF ... INDEX BY` - Asociative arrays (hash maps)
2. `TABLE OF ...` - Nested tables
3. `VARRAY` - Arrays de tamaño variable
4. `OBJECT TYPES` - Tipos personalizados complejos

**Ejemplo real detectado:**
```sql
-- RHH_K_ADMINISTRA_FORMULA línea 46
TYPE T_Gt_Variables IS TABLE OF Varchar2(61) INDEX BY BINARY_INTEGER;
Gt_Variables T_Gt_Variables;
```

**Mapeo potencial:**

| Oracle Type | PostgreSQL Options | Recomendación |
|-------------|-------------------|---------------|
| TABLE OF ... INDEX BY | Arrays `tipo[]` + hstore | ⏳ Post-scan |
| TABLE OF ... | Arrays `tipo[]` | ✅ Directo |
| VARRAY | Arrays `tipo[]` + constraint | ⏳ Evaluar |
| OBJECT TYPE | Composite Type / JSON | ⏳ Caso por caso |

**Consideraciones:**
- ⚠️ INDEX BY no tiene equivalente directo (hash map)
- ⚠️ PostgreSQL arrays son secuenciales (índice 1-N)
- ✅ Composite Types soportan anidamiento
- ⚠️ JSON pierde verificación de tipos

**Decisión:** Se tomará después del scan basado en:
1. Volumetría real de cada tipo de colección
2. Patrones de acceso (índice numérico vs string)
3. Complejidad de las estructuras anidadas
4. Performance requirements

**Próximos pasos:**
1. ⏳ Code Comprehension Agent cataloga TODOS los tipos de colección
2. ⏳ Analizar patrones de uso (¿cómo se accede/modifica?)
3. ⏳ Crear librería de conversión si hay >50 objetos afectados
4. ⏳ Definir estrategia por tipo de colección

---

### Decision 10: Dynamic Formula Engine Strategy
**Status:** ⏳ **DEFERRED** - Pending post-scan analysis
**Fecha:** 2025-12-31 (detectado durante discovery refinement)

**Problema:**
Sistema de nómina usa motor de evaluación de fórmulas dinámicas que permite almacenar expresiones matemáticas como strings y evaluarlas en runtime.

**Ejemplo de uso:**
```sql
-- Expresión almacenada: "RHH_F_SUELDO / 30 + 15"
-- Sistema:
--   1. Ejecuta función RHH_F_SUELDO → obtiene valor numérico
--   2. Evalúa expresión: valor / 30 + 15
--   3. Retorna resultado
```

**Package crítico detectado:** RHH_K_ADMINISTRA_FORMULA (624 líneas)

**Opciones de implementación:**

| Opción | Descripción | Pros | Cons | Complejidad |
|--------|-------------|------|------|-------------|
| **A: EXECUTE + format()** | PL/pgSQL nativo | ✅ Rápido<br>✅ Sin deps | ⚠️ SQL injection risk | Baja |
| **B: Parser seguro** | Validación explícita | ✅ Seguro<br>✅ Control total | ⚠️ Requiere CASE largo | Media |
| **C: AWS Lambda + Python AST** | Sandbox aislado | ✅ MUY seguro<br>✅ Escalable | ⚠️ Latencia ~50-200ms<br>⚠️ Deploy Lambda | Alta |

**Preferencia del usuario:** Nativo PostgreSQL (Opción A o B)

**Decisión:** Se tomará después del scan basado en:
1. **Cantidad de packages:** ¿Solo RHH_K_ADMINISTRA_FORMULA o hay más?
2. **Complejidad de expresiones:** ¿Solo operadores básicos o hay funciones complejas?
3. **Frecuencia de uso:** ¿Crítico en producción o esporádico?
4. **Seguridad requerida:** ¿Expresiones vienen de usuarios o son fijas en BD?

**Si 1-3 packages con expresiones simples:** Opción A (EXECUTE nativo)
**Si >3 packages o expresiones complejas:** Opción B (Parser seguro)
**Si futuro requiere evolución:** Opción C (Lambda - post-migración)

**Próximos pasos:**
1. ⏳ Code Comprehension Agent busca patrón similar en otros packages
2. ⏳ Catalogar todas las funciones usadas en expresiones (RHH_F_*)
3. ⏳ Analizar complejidad de parsing (¿solo math o incluye lógica?)
4. ⏳ Evaluar riesgo de seguridad (origen de las expresiones)
5. ⏳ Implementar opción elegida después del análisis

**Validación requerida:**
- ✅ Shadow testing exhaustivo (Oracle vs PostgreSQL resultados idénticos)
- ✅ Performance testing (latencia aceptable)
- ✅ Security audit (prevenir injection)

---

## Mapeo de Conversiones Oracle → PostgreSQL

### Tipos de Datos

| Oracle | PostgreSQL | Notas |
|--------|------------|-------|
| VARCHAR2(n) | VARCHAR(n) o TEXT | TEXT si n > 10485760 |
| NUMBER | NUMERIC | Precisión máxima 1000 en PG |
| NUMBER(p,s) | NUMERIC(p,s) | |
| DATE | TIMESTAMP | Oracle DATE incluye hora |
| CLOB | TEXT | |
| BLOB | BYTEA | |
| RAW | BYTEA | |
| BOOLEAN | BOOLEAN | Oracle no tiene nativo |

### Funciones

| Oracle | PostgreSQL |
|--------|------------|
| NVL(a,b) | COALESCE(a,b) |
| NVL2(a,b,c) | CASE WHEN a IS NOT NULL THEN b ELSE c END |
| DECODE(a,b,c,d) | CASE WHEN a=b THEN c ELSE d END |
| SYSDATE | CURRENT_TIMESTAMP |
| SYSTIMESTAMP | CURRENT_TIMESTAMP |
| TRUNC(date) | DATE_TRUNC('day', date) |
| ADD_MONTHS(d,n) | d + INTERVAL 'n months' |
| TO_CHAR(date,'YYYYMMDD') | TO_CHAR(date,'YYYYMMDD') |
| SUBSTR(s,p,n) | SUBSTRING(s FROM p FOR n) |
| INSTR(s,sub) | POSITION(sub IN s) |
| TRIM(s) | TRIM(s) |

### Sintaxis SQL

| Oracle | PostgreSQL |
|--------|------------|
| ROWNUM <= 10 | LIMIT 10 |
| table1, table2 WHERE t1.id = t2.id(+) | table1 LEFT JOIN table2 ON t1.id = t2.id |
| CONNECT BY | WITH RECURSIVE |
| MERGE INTO | INSERT ... ON CONFLICT |

### PL/SQL → PL/pgSQL

| Oracle PL/SQL | PostgreSQL PL/pgSQL |
|--------------|---------------------|
| CREATE OR REPLACE PROCEDURE | CREATE OR REPLACE PROCEDURE |
| IS/AS | AS $$ |
| END procedure_name; | END; $$ LANGUAGE plpgsql; |
| VARCHAR2 | VARCHAR o TEXT |
| RAISE_APPLICATION_ERROR(-20001, 'msg') | RAISE EXCEPTION 'msg' |
| DBMS_OUTPUT.PUT_LINE | RAISE NOTICE |
| EXECUTE IMMEDIATE | EXECUTE |

---

**Ver también:**
- [00_index.md](./00_index.md) - Resumen ejecutivo completo
- [01_problem_statement.md](./01_problem_statement.md) - Problema y objetivos
- [02_user_stories.md](./02_user_stories.md) - User Stories detalladas
- [03_architecture.md](./03_architecture.md) - Diseño técnico del sistema
- [05_changelog.md](./05_changelog.md) - Historial de cambios
