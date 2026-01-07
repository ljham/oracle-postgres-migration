# Plan de Implementacion Backend - Oracle to PostgreSQL Migration Tool

**Version:** 1.0  
**Fecha:** 2025-12-30  
**Autor:** backend-developer (sub-agente)  
**Estado:** ready-for-implementation

---

## 1. Resumen Ejecutivo

### Objetivo
Diseñar e implementar la logica de negocio completa para la herramienta de migracion Oracle a PostgreSQL, incluyendo:

1. **Infraestructura AWS Lambda** para HTTP client y conversion CSV a XLSX
2. **Sistema de Orquestacion** con manejo de tokens y checkpoints
3. **Integracion con ora2pg** para objetos simples
4. **Base de Conocimiento** con pgvector para busqueda semantica

### Componentes Principales

```
+-------------------------------------------------------------------+
|                    ARQUITECTURA BACKEND                            |
+-------------------------------------------------------------------+
|                                                                   |
|  [1] INFRAESTRUCTURA AWS                                          |
|      +------------------+     +------------------+                |
|      | Lambda HTTP      |     | Lambda CSV->XLSX |                |
|      | Client (Nodejs) |     | (Nodejs)         |                |
|      +--------+---------+     +--------+---------+                |
|               |                        |                          |
|               v                        v                          |
|      +------------------+     +------------------+                |
|      | Wrapper Functions|     | S3 Event Trigger |                |
|      | (PL/pgSQL)       |     | Configuration    |                |
|      +------------------+     +------------------+                |
|                                                                   |
|  [2] ORQUESTACION                                                 |
|      +------------------+     +------------------+                |
|      | Checkpoint       |     | Token Manager    |                |
|      | System           |     | (Reanudacion)    |                |
|      +--------+---------+     +--------+---------+                |
|               |                        |                          |
|               v                        v                          |
|      +------------------+     +------------------+                |
|      | State Persistence|     | Parallel         |                |
|      | (JSON/Markdown)  |     | Sub-agents       |                |
|      +------------------+     +------------------+                |
|                                                                   |
|  [3] CONVERSION                                                   |
|      +------------------+     +------------------+                |
|      | ora2pg           |     | Agentes IA       |                |
|      | (Objetos Simples)|     | (Obj. Complejos) |                |
|      +--------+---------+     +--------+---------+                |
|               |                        |                          |
|               +----------+-------------+                          |
|                          v                                        |
|              +------------------+                                 |
|              | Validacion       |                                 |
|              | PostgreSQL 17.4  |                                 |
|              +------------------+                                 |
|                                                                   |
|  [4] BASE DE CONOCIMIENTO                                         |
|      +------------------+     +------------------+                |
|      | pgvector Schema  |     | Embedding        |                |
|      | (Aurora PG)      |     | Generation       |                |
|      +--------+---------+     +--------+---------+                |
|               |                        |                          |
|               +----------+-------------+                          |
|                          v                                        |
|              +------------------+                                 |
|              | Busqueda         |                                 |
|              | Semantica        |                                 |
|              +------------------+                                 |
|                                                                   |
+-------------------------------------------------------------------+
```

---

## 2. Arquitectura de Infraestructura AWS

### 2.1 Lambda HTTP Client (CRITICO - <100 objetos UTL_HTTP)

#### 2.1.1 Arquitectura de la Solucion

```
+-------------------------------------------------------------------+
|                    FLUJO UTL_HTTP -> Lambda                        |
+-------------------------------------------------------------------+
|                                                                   |
|  Aurora PostgreSQL (VPC)                                          |
|  +---------------------------------------------------------------+
|  |                                                               |
|  |  PL/pgSQL Code (migrado)                                      |
|  |  +-------------------+                                        |
|  |  | DECLARE           |                                        |
|  |  |   req INTEGER;    |                                        |
|  |  |   resp JSON;      |                                        |
|  |  | BEGIN             |                                        |
|  |  |   req := utl_http_utility.begin_request(...);              |
|  |  |   utl_http_utility.set_header(req, ...);                   |
|  |  |   resp := utl_http_utility.get_response(req);              |
|  |  | END;              |                                        |
|  |  +--------+----------+                                        |
|  |           |                                                   |
|  |           v                                                   |
|  |  +-------------------+                                        |
|  |  | utl_http_utility  | <-- Schema con wrapper functions       |
|  |  | Schema            |                                        |
|  |  +--------+----------+                                        |
|  |           |                                                   |
|  |           | aws_lambda.invoke()                               |
|  |           v                                                   |
|  +---------------------------------------------------------------+
|                          |
|                          | VPC Endpoint / NAT Gateway
|                          v
|  +---------------------------------------------------------------+
|  | AWS Lambda (aurora-http-helper)                               |
|  |                                                               |
|  |  +-------------------+     +-------------------+              |
|  |  | Event Handler     |---->| HTTP Request     |              |
|  |  | (Node.js 18+)     |     | (fetch/axios)    |              |
|  |  +-------------------+     +--------+----------+              |
|  |                                     |                         |
|  |                                     v                         |
|  |  +-------------------+     +-------------------+              |
|  |  | Response Builder  |<----| API Endpoint     |              |
|  |  | (JSON)            |     | (REST/SOAP)      |              |
|  |  +--------+----------+     +-------------------+              |
|  |           |                                                   |
|  +---------------------------------------------------------------+
|              |
|              v
|  +------------------+
|  | Return to Aurora |
|  | (JSON response)  |
|  +------------------+
|
+-------------------------------------------------------------------+
```

#### 2.1.2 Componentes Lambda HTTP Client

**Archivo: `lambda/http-client/index.mjs`**

```javascript
// Especificacion funcional - NO implementar directamente

/**
 * Lambda Function: aurora-http-helper
 * Runtime: Node.js 18.x (ES Modules)
 * Memory: 256 MB (ajustar segun volumen)
 * Timeout: 30 segundos (APIs lentas pueden necesitar mas)
 * 
 * Responsabilidades:
 * 1. Recibir JSON payload con parametros HTTP
 * 2. Construir y ejecutar HTTP request
 * 3. Manejar autenticacion (Basic, Bearer, OAuth)
 * 4. Procesar response (JSON, XML, text)
 * 5. Retornar response estructurado a Aurora
 * 
 * Input (event):
 * {
 *   "url": "https://api.example.com/endpoint",
 *   "method": "POST",
 *   "headers": {
 *     "Content-Type": "application/json",
 *     "Authorization": "Bearer token123"
 *   },
 *   "body": {"key": "value"},
 *   "timeout": 30000,
 *   "auth": {
 *     "type": "basic",
 *     "username": "user",
 *     "password": "pass"
 *   }
 * }
 * 
 * Output:
 * {
 *   "statusCode": 200,
 *   "success": true,
 *   "data": {...},
 *   "headers": {...},
 *   "timing": {
 *     "duration_ms": 150
 *   }
 * }
 */
```

**Configuracion IAM requerida:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:Subnet": ["subnet-xxx", "subnet-yyy"]
        }
      }
    }
  ]
}
```

#### 2.1.3 Wrapper Functions PL/pgSQL

**Archivo: `sql/utl_http_utility/install.sql`**

```sql
-- Especificacion de schema y funciones wrapper
-- Basado en: https://github.com/aws-samples/wrapper-for-utl-http-with-amazon-aurora

-- Schema dedicado para utilidades HTTP
CREATE SCHEMA IF NOT EXISTS utl_http_utility;

-- Tipos personalizados (equivalentes a UTL_HTTP.REQ y UTL_HTTP.RESP)
CREATE TYPE utl_http_utility.req AS (
    request_id      INTEGER,
    url             TEXT,
    method          TEXT,
    http_version    TEXT,
    headers         JSONB,
    body            TEXT,
    auth_type       TEXT,
    auth_username   TEXT,
    auth_password   TEXT,
    timeout         INTEGER
);

CREATE TYPE utl_http_utility.resp AS (
    status_code     INTEGER,
    reason_phrase   TEXT,
    http_version    TEXT,
    headers         JSONB,
    body            TEXT,
    raw_response    JSONB
);

-- Tabla de configuracion
CREATE TABLE utl_http_utility.config (
    key             VARCHAR(100) PRIMARY KEY,
    value           TEXT NOT NULL,
    description     TEXT
);

-- Insertar configuracion inicial
INSERT INTO utl_http_utility.config (key, value, description) VALUES
    ('lambda_arn', 'arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aurora-http-helper', 'ARN de Lambda HTTP client'),
    ('lambda_region', 'us-east-1', 'Region de Lambda'),
    ('default_timeout', '30000', 'Timeout por defecto en ms');

-- Funciones wrapper (especificacion)
-- Cada funcion debe replicar el comportamiento de UTL_HTTP de Oracle

/*
 * Funciones a implementar:
 * 
 * 1. begin_request(url, method, http_version) -> req
 *    - Inicializa un nuevo request
 *    - Genera request_id unico
 *    - Almacena en variable de sesion
 * 
 * 2. set_header(req, name, value) -> req
 *    - Agrega header al request
 *    - Retorna req actualizado
 * 
 * 3. set_authentication(req, username, password, scheme) -> req
 *    - Configura autenticacion (Basic, Bearer)
 *    - Retorna req actualizado
 * 
 * 4. write_text(req, data) -> req
 *    - Agrega body al request
 *    - Retorna req actualizado
 * 
 * 5. get_response(req) -> resp
 *    - Invoca Lambda con payload JSON
 *    - Parsea response de Lambda
 *    - Retorna resp estructurado
 * 
 * 6. read_text(resp) -> TEXT
 *    - Extrae body de response
 * 
 * 7. get_header(resp, name) -> TEXT
 *    - Obtiene valor de header especifico
 * 
 * 8. end_request(req) -> VOID
 *    - Limpia recursos de sesion
 */
```

### 2.2 Lambda CSV a XLSX (Archivos Excel)

#### 2.2.1 Arquitectura

```
+-------------------------------------------------------------------+
|                    FLUJO CSV -> XLSX                               |
+-------------------------------------------------------------------+
|                                                                   |
|  Aurora PostgreSQL                                                |
|  +-------------------+                                            |
|  | aws_s3.query_     |                                            |
|  | export_to_s3()    |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           | Escribe CSV                                           |
|           v                                                       |
|  +-------------------+                                            |
|  | S3 Bucket         |                                            |
|  | /csv/report.csv   |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           | S3 Event Notification                                 |
|           v                                                       |
|  +-------------------+                                            |
|  | Lambda            |                                            |
|  | csv-to-xlsx       |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           | Convierte y guarda                                    |
|           v                                                       |
|  +-------------------+                                            |
|  | S3 Bucket         |                                            |
|  | /xlsx/report.xlsx |                                            |
|  +-------------------+                                            |
|                                                                   |
+-------------------------------------------------------------------+
```

#### 2.2.2 Componentes Lambda CSV-XLSX

**Archivo: `lambda/csv-to-xlsx/handler.py`**

```python
# Especificacion funcional - NO implementar directamente

"""
Lambda Function: csv-to-xlsx-converter
Runtime: Python 3.11
Memory: 512 MB (archivos grandes necesitan mas)
Timeout: 60 segundos
Dependencias: openpyxl, boto3

Responsabilidades:
1. Trigger: S3 Event cuando se crea archivo .csv
2. Descargar CSV de S3
3. Convertir a XLSX usando openpyxl
4. Subir XLSX a carpeta /xlsx/ del mismo bucket
5. Opcional: Eliminar CSV original

Trigger Configuration:
- Event: s3:ObjectCreated:*
- Prefix: csv/
- Suffix: .csv

Input (S3 Event):
{
  "Records": [{
    "s3": {
      "bucket": {"name": "efs-veris-compartidos-dev"},
      "object": {"key": "csv/report_2025_01_15.csv"}
    }
  }]
}

Output (XLSX file):
- Ubicacion: s3://efs-veris-compartidos-dev/xlsx/report_2025_01_15.xlsx
- Formato: Excel 2010+ (.xlsx)
- Encoding: UTF-8
"""
```

### 2.3 Configuracion de Red y Seguridad

#### 2.3.1 VPC Configuration

```
+-------------------------------------------------------------------+
|                    ARQUITECTURA VPC                                |
+-------------------------------------------------------------------+
|                                                                   |
|  VPC (10.0.0.0/16)                                                |
|  +---------------------------------------------------------------+
|  |                                                               |
|  |  Private Subnet A (10.0.1.0/24)                               |
|  |  +-------------------+     +-------------------+              |
|  |  | Aurora PostgreSQL |     | Lambda            |              |
|  |  | Primary           |     | (ENI)             |              |
|  |  +-------------------+     +-------------------+              |
|  |                                                               |
|  |  Private Subnet B (10.0.2.0/24)                               |
|  |  +-------------------+     +-------------------+              |
|  |  | Aurora PostgreSQL |     | Lambda            |              |
|  |  | Replica           |     | (ENI)             |              |
|  |  +-------------------+     +-------------------+              |
|  |                                                               |
|  |  Public Subnet (10.0.100.0/24)                                |
|  |  +-------------------+                                        |
|  |  | NAT Gateway       |---> Internet (APIs externas)           |
|  |  +-------------------+                                        |
|  |                                                               |
|  +---------------------------------------------------------------+
|                                                                   |
+-------------------------------------------------------------------+
```

#### 2.3.2 Security Groups

**Security Group: aurora-postgres-sg**
```
Inbound:
- Port 5432 from lambda-sg (PostgreSQL)
- Port 5432 from bastion-sg (Admin access)

Outbound:
- All traffic to 0.0.0.0/0 (para S3 y Lambda)
```

**Security Group: lambda-sg**
```
Inbound:
- None required (Lambda is invoked, not accessed)

Outbound:
- Port 443 to 0.0.0.0/0 (HTTPS for APIs)
- Port 5432 to aurora-postgres-sg (si necesita conectar a DB)
```

#### 2.3.3 IAM Roles

**Role: aurora-lambda-invoke-role**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:us-east-1:*:function:aurora-http-helper",
        "arn:aws:lambda:us-east-1:*:function:csv-to-xlsx-converter"
      ]
    }
  ]
}
```

---

## 3. Sistema de Orquestacion y Manejo de Tokens

### 3.1 Estrategia de Procesamiento para 8,122 Objetos

#### 3.1.1 Problema

- **8,122 objetos PL/SQL** a procesar
- **Limite de tokens** de Claude (contexto + output)
- **Necesidad de reanudacion** automatica sin perder progreso

#### 3.1.2 Solucion: Procesamiento por Lotes con Checkpoints

```
+-------------------------------------------------------------------+
|                    ESTRATEGIA DE PROCESAMIENTO                     |
+-------------------------------------------------------------------+
|                                                                   |
|  Fase 1: Comprension (8,122 objetos)                              |
|  +---------------------------------------------------------------+
|  |                                                               |
|  |  Lote 1        Lote 2        Lote 3        ...    Lote N      |
|  |  (100 obj)     (100 obj)     (100 obj)            (100 obj)   |
|  |     |             |             |                    |        |
|  |     v             v             v                    v        |
|  |  +----------+  +----------+  +----------+      +----------+   |
|  |  |Checkpoint|  |Checkpoint|  |Checkpoint|      |Checkpoint|   |
|  |  |    1     |  |    2     |  |    3     |      |    N     |   |
|  |  +----------+  +----------+  +----------+      +----------+   |
|  |                                                               |
|  +---------------------------------------------------------------+
|                                                                   |
|  Estado persistido en:                                            |
|  - .claude/sessions/migration_state.json                         |
|  - knowledge/ (resultados parciales)                             |
|                                                                   |
+-------------------------------------------------------------------+
```

### 3.2 Schema de Estado (Checkpoint System)

**Archivo: `.claude/sessions/migration_state.json`**

```json
{
  "version": "1.0",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z",
  "current_phase": "comprehension",
  "phases": {
    "comprehension": {
      "status": "in_progress",
      "total_objects": 8122,
      "processed_objects": 3500,
      "current_batch": 36,
      "batch_size": 100,
      "last_object_id": "PKG_VENTAS.CALCULAR_DESCUENTO",
      "started_at": "2025-01-15T10:00:00Z",
      "estimated_completion": "2025-01-15T18:00:00Z",
      "errors": []
    },
    "strategy": {
      "status": "pending",
      "total_objects": 0,
      "processed_objects": 0
    },
    "conversion_simple": {
      "status": "pending"
    },
    "conversion_complex": {
      "status": "pending"
    },
    "validation": {
      "status": "pending"
    }
  },
  "token_usage": {
    "session_tokens_used": 145000,
    "session_limit": 200000,
    "pause_threshold": 180000,
    "last_reset": "2025-01-15T00:00:00Z"
  },
  "recovery": {
    "can_resume": true,
    "resume_from": {
      "phase": "comprehension",
      "batch": 36,
      "object_index": 0
    }
  }
}
```

### 3.3 Logica de Reanudacion Automatica

```python
# Pseudocodigo - Logica de reanudacion

class MigrationOrchestrator:
    """
    Orquestador principal de la migracion.
    Maneja checkpoints, tokens y reanudacion.
    """
    
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state = self.load_state()
        self.batch_size = 100
        self.token_pause_threshold = 0.9  # 90% del limite
    
    def load_state(self) -> dict:
        """Carga estado desde archivo o crea nuevo."""
        if exists(self.state_file):
            return load_json(self.state_file)
        return self.create_initial_state()
    
    def save_checkpoint(self):
        """Guarda estado actual para reanudacion."""
        self.state['updated_at'] = now()
        save_json(self.state_file, self.state)
        log(f"Checkpoint guardado: {self.state['current_phase']}")
    
    def should_pause_for_tokens(self) -> bool:
        """Verifica si se acerca al limite de tokens."""
        usage = self.state['token_usage']
        ratio = usage['session_tokens_used'] / usage['session_limit']
        return ratio >= self.token_pause_threshold
    
    def process_batch(self, objects: list) -> list:
        """
        Procesa un lote de objetos.
        Guarda checkpoint despues de cada lote.
        """
        results = []
        for obj in objects:
            if self.should_pause_for_tokens():
                self.save_checkpoint()
                raise TokenLimitApproaching(
                    "Pausando: 90% de tokens usados. "
                    f"Reanudar desde: {obj.name}"
                )
            
            result = self.process_object(obj)
            results.append(result)
            self.update_progress(obj)
        
        self.save_checkpoint()
        return results
    
    def resume(self):
        """Reanuda desde el ultimo checkpoint."""
        if not self.state['recovery']['can_resume']:
            raise CannotResumeError("Estado invalido para reanudar")
        
        resume_point = self.state['recovery']['resume_from']
        log(f"Reanudando desde fase={resume_point['phase']}, "
            f"batch={resume_point['batch']}")
        
        return self.continue_from(resume_point)
```

### 3.4 Logging y Trazabilidad

**Archivo: `.claude/sessions/migration_log.md`**

```markdown
# Migration Log - Oracle to PostgreSQL

## Session: 2025-01-15

### 10:00:00 - Inicio de sesion
- **Fase:** Comprension Semantica
- **Objetos pendientes:** 8,122
- **Token budget:** 200,000

### 10:05:23 - Batch 1 completado
- **Objetos procesados:** 100
- **Tokens usados:** 4,500
- **Resultado:** 98 exitosos, 2 con warnings

### 14:28:45 - Pausa por tokens
- **Razon:** Token usage at 90% (180,000/200,000)
- **Ultimo objeto:** PKG_VENTAS.CALCULAR_DESCUENTO
- **Estado guardado:** migration_state.json
- **Accion requerida:** Esperar reset de tokens o continuar manualmente

### 14:30:00 - Checkpoint guardado
- **Fase:** comprehension
- **Batch:** 36
- **Progreso:** 3,500 / 8,122 (43.1%)
```

### 3.5 Paralelizacion de Sub-agentes

```
+-------------------------------------------------------------------+
|                    PARALELIZACION                                  |
+-------------------------------------------------------------------+
|                                                                   |
|  Orquestador Principal                                            |
|  +---------------------------------------------------------------+
|  |                                                               |
|  |  [Fase 1: Comprension]                                        |
|  |                                                               |
|  |  Sub-agente 1        Sub-agente 2        Sub-agente 3         |
|  |  (Functions)         (Packages 1-200)   (Packages 201-400)    |
|  |       |                    |                   |              |
|  |       v                    v                   v              |
|  |  +-----------+       +-----------+       +-----------+        |
|  |  | knowledge/|       | knowledge/|       | knowledge/|        |
|  |  | func/     |       | pkg/1-200/|       | pkg/201+/ |        |
|  |  +-----------+       +-----------+       +-----------+        |
|  |                                                               |
|  +---------------------------------------------------------------+
|                          |
|                          v
|  +---------------------------------------------------------------+
|  |  [Fase 2: Decision Estrategica]                               |
|  |                                                               |
|  |  Migration Strategist (secuencial - necesita todo el          |
|  |  conocimiento consolidado)                                    |
|  |                                                               |
|  +---------------------------------------------------------------+
|                          |
|                          v
|  +---------------------------------------------------------------+
|  |  [Fase 3: Conversion]                                         |
|  |                                                               |
|  |  RUTA A (Paralelo)              RUTA B (Paralelo)             |
|  |  +------------------+           +------------------+          |
|  |  | ora2pg Worker 1  |           | IA Agent 1       |          |
|  |  | (Functions)      |           | (Complex Pkg 1)  |          |
|  |  +------------------+           +------------------+          |
|  |  +------------------+           +------------------+          |
|  |  | ora2pg Worker 2  |           | IA Agent 2       |          |
|  |  | (Procedures)     |           | (Complex Pkg 2)  |          |
|  |  +------------------+           +------------------+          |
|  |                                                               |
|  +---------------------------------------------------------------+
|                                                                   |
+-------------------------------------------------------------------+
```

---

## 4. Integracion con ora2pg

### 4.1 Flujo de Conversion de Objetos Simples

```
+-------------------------------------------------------------------+
|                    FLUJO ora2pg                                    |
+-------------------------------------------------------------------+
|                                                                   |
|  Input                                                            |
|  +-------------------+                                            |
|  | complexity/       |                                            |
|  | simple_objects.txt|  <-- Lista del Migration Strategist        |
|  +--------+----------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  | ora2pg.conf       |                                            |
|  | (configurado)     |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  | ora2pg CLI        |                                            |
|  | (ejecucion local) |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  | migrated/simple/  |                                            |
|  | *.sql             |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           v                                                       |
|  +-------------------+                                            |
|  | Validacion        |                                            |
|  | psql -f *.sql     |                                            |
|  +-------------------+                                            |
|                                                                   |
+-------------------------------------------------------------------+
```

### 4.2 Configuracion ora2pg

**Archivo: `config/ora2pg.conf`**

```perl
# Configuracion para Oracle 19c -> PostgreSQL 17.4
# NOTA: NO conectar a Oracle - usar archivos extraidos

##########################
# ORACLE CONNECTION
##########################
# Comentado - no conectar a Oracle
# ORACLE_DSN  dbi:Oracle:host=localhost;sid=ORCL;port=1521
# ORACLE_USER system
# ORACLE_PWD  manager

##########################
# INPUT MODE (Archivos Locales)
##########################
# Usar archivos PL/SQL ya extraidos
INPUT_FILE  extracted/

# Solo procesar objetos de la lista "simple"
# ALLOW acepta archivo con lista de nombres
ALLOW       complexity/simple_objects.txt

##########################
# OUTPUT CONFIGURATION
##########################
OUTPUT_DIR  migrated/simple/
OUTPUT      plpgsql_converted.sql

# Separar por tipo de objeto
FILE_PER_FUNCTION    1
FILE_PER_TABLE       0
FILE_PER_CONSTRAINT  0
FILE_PER_INDEX       0
FILE_PER_FKEYS       0

##########################
# POSTGRESQL TARGET
##########################
PG_VERSION  17.4
PG_SCHEMA   public

# Formato de output
PLSQL_PGSQL 1
EXPORT_SCHEMA 0
COMPILE_SCHEMA 0

##########################
# TYPE CONVERSION
##########################
# Tipos Oracle -> PostgreSQL
DATA_TYPE   VARCHAR2:TEXT,NUMBER:NUMERIC,DATE:TIMESTAMP,CLOB:TEXT,BLOB:BYTEA

##########################
# PLSQL CONVERSION
##########################
# Convertir sintaxis PL/SQL a PL/pgSQL
PLSQL_PGSQL 1

# Funciones Oracle a PostgreSQL
NULL_EQUAL_EMPTY 1
NLS_LANG    AMERICAN_AMERICA.UTF8

##########################
# LOGGING
##########################
DEBUG       0
LOGFILE     logs/ora2pg.log
```

### 4.3 Script de Ejecucion

**Archivo: `scripts/run_ora2pg.sh`**

```bash
#!/bin/bash
# Script para ejecutar ora2pg en objetos simples
# Ejecutar DESPUES de que Migration Strategist genere simple_objects.txt

set -e

# Directorio base
BASE_DIR="$(dirname "$0")/.."
cd "$BASE_DIR"

# Verificar prereqs
if [ ! -f "complexity/simple_objects.txt" ]; then
    echo "ERROR: simple_objects.txt no existe. Ejecutar Migration Strategist primero."
    exit 1
fi

# Crear directorio output
mkdir -p migrated/simple

# Ejecutar ora2pg por tipo de objeto
echo "[1/4] Convirtiendo FUNCTIONS..."
ora2pg -c config/ora2pg.conf -t FUNCTION -o migrated/simple/functions.sql

echo "[2/4] Convirtiendo PROCEDURES..."
ora2pg -c config/ora2pg.conf -t PROCEDURE -o migrated/simple/procedures.sql

echo "[3/4] Convirtiendo PACKAGES..."
ora2pg -c config/ora2pg.conf -t PACKAGE -o migrated/simple/packages.sql

echo "[4/4] Convirtiendo TRIGGERS..."
ora2pg -c config/ora2pg.conf -t TRIGGER -o migrated/simple/triggers.sql

echo ""
echo "Conversion completada. Archivos en migrated/simple/"
echo ""
echo "Siguiente paso: validar sintaxis con PostgreSQL"
echo "  psql -h <host> -U <user> -d <db> -f migrated/simple/functions.sql"
```

---

## 5. Base de Conocimiento (pgvector)

### 5.1 Schema de Base de Datos

**Archivo: `sql/knowledge_base/schema.sql`**

```sql
-- Schema para Base de Conocimiento con pgvector
-- Amazon Aurora PostgreSQL 17.4

-- Habilitar extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Schema dedicado
CREATE SCHEMA IF NOT EXISTS knowledge_base;

-- Tabla principal de conocimiento
CREATE TABLE knowledge_base.knowledge_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificacion del objeto fuente
    object_type     VARCHAR(50) NOT NULL,  -- FUNCTION, PROCEDURE, PACKAGE, TRIGGER
    object_name     VARCHAR(256) NOT NULL,
    schema_name     VARCHAR(128),
    
    -- Tipo de conocimiento
    knowledge_type  VARCHAR(50) NOT NULL,  -- RULE, FLOW, DEPENDENCY, FEATURE
    
    -- Contenido
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    content_raw     TEXT,  -- Contenido original (codigo)
    content_structured JSONB,  -- Contenido estructurado
    
    -- Embedding para busqueda semantica
    -- Dimension 1024 para Amazon Titan v2 model
    embedding       vector(1024),
    
    -- Metadata
    confidence      FLOAT DEFAULT 1.0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(100) DEFAULT 'code_comprehension_agent',
    
    -- Indices
    CONSTRAINT fk_knowledge_type CHECK (
        knowledge_type IN ('RULE', 'FLOW', 'DEPENDENCY', 'FEATURE', 'VALIDATION', 'CALCULATION')
    )
);

-- Tabla de reglas de negocio
CREATE TABLE knowledge_base.business_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_id    UUID REFERENCES knowledge_base.knowledge_items(id),
    
    rule_name       TEXT NOT NULL,
    rule_category   VARCHAR(100),  -- VALIDATION, CALCULATION, WORKFLOW
    
    -- Condiciones y acciones
    conditions      JSONB NOT NULL,
    actions         JSONB NOT NULL,
    exceptions      JSONB,
    
    -- Contexto de negocio
    business_context TEXT,
    applies_to      TEXT[],  -- Entidades afectadas
    
    -- Source tracking
    source_code     TEXT,
    source_line     INTEGER,
    
    embedding       vector(1024),
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de dependencias
CREATE TABLE knowledge_base.dependencies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    source_object   VARCHAR(256) NOT NULL,
    source_type     VARCHAR(50) NOT NULL,
    
    target_object   VARCHAR(256) NOT NULL,
    target_type     VARCHAR(50) NOT NULL,
    
    dependency_type VARCHAR(50) NOT NULL,  -- CALLS, READS, WRITES, REFERENCES
    
    call_count      INTEGER DEFAULT 1,
    is_critical     BOOLEAN DEFAULT FALSE,
    
    metadata        JSONB,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source_object, target_object, dependency_type)
);

-- Tabla de features tecnicas detectadas
CREATE TABLE knowledge_base.technical_features (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    object_name     VARCHAR(256) NOT NULL,
    object_type     VARCHAR(50) NOT NULL,
    
    feature_name    VARCHAR(100) NOT NULL,  -- UTL_HTTP, AUTONOMOUS_TRANSACTION, etc.
    feature_category VARCHAR(50),
    
    occurrences     INTEGER DEFAULT 1,
    complexity_impact VARCHAR(20),  -- LOW, MEDIUM, HIGH
    migration_strategy TEXT,
    
    details         JSONB,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices para busqueda
CREATE INDEX idx_knowledge_items_type ON knowledge_base.knowledge_items(knowledge_type);
CREATE INDEX idx_knowledge_items_object ON knowledge_base.knowledge_items(object_name);
CREATE INDEX idx_business_rules_category ON knowledge_base.business_rules(rule_category);
CREATE INDEX idx_dependencies_source ON knowledge_base.dependencies(source_object);
CREATE INDEX idx_dependencies_target ON knowledge_base.dependencies(target_object);
CREATE INDEX idx_technical_features_feature ON knowledge_base.technical_features(feature_name);

-- Indice HNSW para busqueda semantica (pgvector 0.6+)
CREATE INDEX idx_knowledge_embedding ON knowledge_base.knowledge_items 
    USING hnsw (embedding vector_cosine_ops) WITH (ef_construction=256);

CREATE INDEX idx_rules_embedding ON knowledge_base.business_rules 
    USING hnsw (embedding vector_cosine_ops) WITH (ef_construction=256);

-- Funcion de busqueda semantica
CREATE OR REPLACE FUNCTION knowledge_base.semantic_search(
    query_embedding vector(1024),
    limit_results INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    description TEXT,
    knowledge_type VARCHAR(50),
    object_name VARCHAR(256),
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ki.id,
        ki.title,
        ki.description,
        ki.knowledge_type,
        ki.object_name,
        1 - (ki.embedding <=> query_embedding) as similarity
    FROM knowledge_base.knowledge_items ki
    WHERE 1 - (ki.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY ki.embedding <=> query_embedding
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Vista consolidada de complejidad
CREATE OR REPLACE VIEW knowledge_base.object_complexity AS
SELECT 
    tf.object_name,
    tf.object_type,
    COUNT(DISTINCT tf.feature_name) as feature_count,
    ARRAY_AGG(DISTINCT tf.feature_name) as features,
    MAX(CASE 
        WHEN tf.complexity_impact = 'HIGH' THEN 3
        WHEN tf.complexity_impact = 'MEDIUM' THEN 2
        ELSE 1
    END) as max_complexity_score,
    COUNT(DISTINCT d.target_object) as dependency_count
FROM knowledge_base.technical_features tf
LEFT JOIN knowledge_base.dependencies d ON tf.object_name = d.source_object
GROUP BY tf.object_name, tf.object_type;
```

### 5.2 Generacion de Embeddings

**Archivo: `src/knowledge/embedding_generator.py`**

```python
# Especificacion - NO implementar directamente

"""
Generador de Embeddings para Base de Conocimiento

Responsabilidades:
1. Generar embeddings de texto usando Amazon Bedrock (Titan)
2. Insertar/actualizar embeddings en pgvector
3. Batch processing para eficiencia

Modelo: Amazon Titan Text Embeddings V2
Dimension: 1024 (configurable: 256, 512, 1024)

Ejemplo de uso:
    generator = EmbeddingGenerator(
        bedrock_client=bedrock,
        pg_connection=conn,
        model_id='amazon.titan-embed-text-v2:0'
    )
    
    # Generar embeddings para reglas de negocio
    generator.process_knowledge_items(batch_size=100)
"""

from dataclasses import dataclass
from typing import List, Optional
import boto3
import psycopg2
from pgvector.psycopg2 import register_vector

@dataclass
class EmbeddingConfig:
    """Configuracion para generacion de embeddings."""
    model_id: str = 'amazon.titan-embed-text-v2:0'
    dimensions: int = 1024
    batch_size: int = 100
    normalize: bool = True


class EmbeddingGenerator:
    """
    Generador de embeddings para base de conocimiento.
    
    Atributos:
        bedrock: Cliente de Amazon Bedrock
        connection: Conexion a PostgreSQL
        config: Configuracion de embeddings
    
    Metodos:
        generate_embedding(text: str) -> List[float]
            Genera embedding para un texto
        
        process_knowledge_items(batch_size: int = 100)
            Procesa items de knowledge_items sin embedding
        
        process_business_rules(batch_size: int = 100)
            Procesa reglas de negocio sin embedding
        
        search(query: str, limit: int = 10) -> List[dict]
            Busqueda semantica por texto
    """
    pass  # Implementacion en fase de desarrollo
```

### 5.3 API de Busqueda

**Archivo: `src/knowledge/search_api.py`**

```python
# Especificacion - NO implementar directamente

"""
API de Busqueda Semantica para Base de Conocimiento

Endpoints:
1. POST /search
   - Body: {"query": "como se calcula el descuento?", "limit": 10}
   - Response: Lista de conocimiento relevante
   
2. GET /rules/{category}
   - Retorna reglas de negocio por categoria
   
3. GET /dependencies/{object_name}
   - Retorna grafo de dependencias de un objeto
   
4. GET /features/{feature_name}
   - Retorna todos los objetos que usan una feature

Implementacion con FastAPI:
    
    @app.post("/search")
    async def semantic_search(request: SearchRequest):
        embedding = generator.generate_embedding(request.query)
        results = await db.execute(
            "SELECT * FROM knowledge_base.semantic_search($1, $2, $3)",
            [embedding, request.limit, request.threshold]
        )
        return results
"""
```

---

## 6. Archivos a Crear/Modificar

### 6.1 Estructura de Directorios

```
proyecto/
+-- .claude/
|   +-- doc/
|   |   +-- oracle-postgres-migration/
|   |       +-- plan_backend_logic.md          # Este archivo
|   +-- sessions/
|       +-- migration_state.json               # Estado de checkpoints
|       +-- migration_log.md                   # Log de trazabilidad
|
+-- lambda/
|   +-- http-client/
|   |   +-- index.mjs                          # Lambda HTTP client
|   |   +-- package.json                       # Dependencias Node.js
|   |   +-- test/
|   |       +-- test_handler.mjs               # Tests unitarios
|   +-- csv-to-xlsx/
|       +-- handler.py                         # Lambda CSV->XLSX
|       +-- requirements.txt                   # Dependencias Python
|       +-- test/
|           +-- test_handler.py                # Tests unitarios
|
+-- sql/
|   +-- utl_http_utility/
|   |   +-- install.sql                        # Schema + wrapper functions
|   |   +-- uninstall.sql                      # Cleanup
|   |   +-- test/
|   |       +-- test_http_requests.sql         # Tests
|   +-- knowledge_base/
|       +-- schema.sql                         # Schema pgvector
|       +-- functions.sql                      # Funciones de busqueda
|       +-- seed_data.sql                      # Datos iniciales (si aplica)
|
+-- config/
|   +-- ora2pg.conf                            # Configuracion ora2pg
|   +-- aws/
|       +-- lambda-http-client.yaml            # SAM template
|       +-- lambda-csv-xlsx.yaml               # SAM template
|       +-- iam-policies.json                  # Politicas IAM
|
+-- scripts/
|   +-- run_ora2pg.sh                          # Ejecutar conversion ora2pg
|   +-- deploy_lambda.sh                       # Deploy lambdas
|   +-- setup_knowledge_base.sh                # Inicializar pgvector
|
+-- src/
|   +-- orchestration/
|   |   +-- __init__.py
|   |   +-- orchestrator.py                    # Orquestador principal
|   |   +-- checkpoint.py                      # Sistema de checkpoints
|   |   +-- token_manager.py                   # Manejo de tokens
|   +-- knowledge/
|       +-- __init__.py
|       +-- embedding_generator.py             # Generador embeddings
|       +-- search_api.py                      # API de busqueda
|
+-- tests/
    +-- integration/
        +-- test_http_wrapper.py               # Test wrapper functions
        +-- test_knowledge_base.py             # Test pgvector queries
```

### 6.2 Dependencias (pyproject.toml)

```toml
[tool.poetry]
name = "oracle-postgres-migration"
version = "0.1.0"
description = "Herramienta de migracion Oracle a PostgreSQL con agentes IA"

[tool.poetry.dependencies]
python = "^3.11"

# AWS SDK
boto3 = "^1.34"
botocore = "^1.34"

# PostgreSQL
psycopg2-binary = "^2.9"
pgvector = "^0.2"
asyncpg = "^0.29"

# API Framework
fastapi = "^0.109"
uvicorn = "^0.27"
pydantic = "^2.5"

# Utilities
python-dotenv = "^1.0"
rich = "^13.7"  # Logging bonito
tenacity = "^8.2"  # Retry logic

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.23"
httpx = "^0.26"  # Testing async HTTP
moto = "^4.2"  # Mock AWS services

[tool.poetry.group.lambda]
# Dependencias para Lambda functions (packaging separado)
openpyxl = "^3.1"  # CSV to XLSX
requests = "^2.31"  # HTTP client (Python version)
```

---

## 7. Plan de Testing

### 7.1 Tests Unitarios

| Componente | Que testear | Framework |
|------------|-------------|-----------|
| Lambda HTTP Client | Request building, response parsing, error handling | Jest (Node.js) |
| Lambda CSV-XLSX | Conversion correcta, manejo de encoding | pytest |
| Wrapper Functions | Cada funcion UTL_HTTP equivalente | pgTAP |
| Checkpoint System | Save/load state, resume logic | pytest |
| Embedding Generator | Dimension correcta, batch processing | pytest |

### 7.2 Tests de Integracion

| Escenario | Descripcion | Prerequisitos |
|-----------|-------------|---------------|
| HTTP Request E2E | Aurora -> Lambda -> API externa -> Aurora | Lambda deployed, VPC configured |
| CSV to XLSX E2E | Query -> S3 CSV -> Lambda trigger -> S3 XLSX | S3 bucket, Lambda trigger |
| Knowledge Search | Insert item -> Generate embedding -> Search | pgvector enabled |
| Checkpoint Resume | Process 50% -> Interrupt -> Resume -> Complete | State file accessible |

### 7.3 Shadow Testing (Validacion de Migracion)

```sql
-- Framework de shadow testing
-- Ejecuta mismo procedure en Oracle y PostgreSQL, compara resultados

-- Oracle
DECLARE
    v_result_oracle VARCHAR2(4000);
BEGIN
    PKG_VENTAS.CALCULAR_DESCUENTO(p_cliente_id => 123, p_resultado => v_result_oracle);
    INSERT INTO shadow_test_results (test_id, source, result) 
    VALUES ('test_001', 'ORACLE', v_result_oracle);
END;

-- PostgreSQL
DO $$
DECLARE
    v_result_pg TEXT;
BEGIN
    v_result_pg := pkg_ventas.calcular_descuento(p_cliente_id => 123);
    INSERT INTO shadow_test_results (test_id, source, result) 
    VALUES ('test_001', 'POSTGRESQL', v_result_pg);
END;
$$;

-- Comparacion
SELECT 
    t1.test_id,
    t1.result as oracle_result,
    t2.result as pg_result,
    CASE WHEN t1.result = t2.result THEN 'PASS' ELSE 'FAIL' END as status
FROM shadow_test_results t1
JOIN shadow_test_results t2 ON t1.test_id = t2.test_id
WHERE t1.source = 'ORACLE' AND t2.source = 'POSTGRESQL';
```

---

## 8. Consideraciones Adicionales

### 8.1 Migraciones de Base de Datos

1. **Orden de ejecucion de scripts SQL:**
   ```
   1. sql/knowledge_base/schema.sql (crear schema pgvector)
   2. sql/utl_http_utility/install.sql (crear wrapper functions)
   3. Configurar Lambda ARN en utl_http_utility.config
   ```

2. **Rollback:**
   ```
   1. sql/utl_http_utility/uninstall.sql
   2. DROP SCHEMA knowledge_base CASCADE;
   ```

### 8.2 Variables de Entorno

```bash
# .env.example

# AWS
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Lambda ARNs
LAMBDA_HTTP_CLIENT_ARN=arn:aws:lambda:us-east-1:123456789012:function:aurora-http-helper
LAMBDA_CSV_XLSX_ARN=arn:aws:lambda:us-east-1:123456789012:function:csv-to-xlsx-converter

# S3
S3_BUCKET_DEV=efs-veris-compartidos-dev
S3_BUCKET_PRD=efs-veris-compartidos-prd

# Aurora PostgreSQL
AURORA_HOST=your-cluster.cluster-xxx.us-east-1.rds.amazonaws.com
AURORA_PORT=5432
AURORA_DATABASE=veris
AURORA_USER=migration_user

# Bedrock (para embeddings)
BEDROCK_MODEL_ID=amazon.titan-embed-text-v2:0
EMBEDDING_DIMENSIONS=1024

# Migration
BATCH_SIZE=100
TOKEN_PAUSE_THRESHOLD=0.9
```

### 8.3 Configuraciones Especiales

**Parameter Group de Aurora (si se requiere):**
```
# Permitir session variables para packages
# Aumentar shared_preload_libraries si es necesario
shared_preload_libraries = 'pg_stat_statements,aws_lambda'
```

---

## 9. Cronograma de Implementacion Sugerido

| Semana | Componente | Entregable | Dependencias |
|--------|------------|------------|--------------|
| 1 | Lambda HTTP Client | Function deployed + tests | VPC, IAM roles |
| 1 | Wrapper Functions | install.sql funcional | Lambda deployed |
| 2 | Lambda CSV-XLSX | Function + S3 trigger | S3 bucket |
| 2 | pgvector Schema | Tables + indices | Extension habilitada |
| 3 | Orchestrator | Checkpoint system | - |
| 3 | ora2pg Config | Configuracion validada | ora2pg instalado |
| 4 | Embedding Generator | Integracion Bedrock | Bedrock access |
| 4 | Integration Tests | Suite completa | Todo lo anterior |

---

## 10. Referencias

### Documentacion Oficial
- [AWS Blog - Build custom HTTP client for Aurora PostgreSQL](https://aws.amazon.com/blogs/database/build-a-custom-http-client-in-amazon-aurora-postgresql-and-amazon-rds-for-postgresql-an-alternative-to-oracles-utl_http/)
- [GitHub - aws-samples/wrapper-for-utl-http-with-amazon-aurora](https://github.com/aws-samples/wrapper-for-utl-http-with-amazon-aurora)
- [Invoking Lambda from Aurora PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/PostgreSQL-Lambda.html)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Aurora PostgreSQL as Knowledge Base](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.VectorDB.html)
- [Ora2Pg Documentation](https://ora2pg.darold.net/documentation.html)

### Repositorios de Ejemplo
- [aws-samples/amazon-aurora-http-client](https://github.com/aws-samples/amazon-aurora-http-client)
- [build-on-aws/langchain-embeddings](https://github.com/build-on-aws/langchain-embeddings)

---

**Documento creado por:** backend-developer (sub-agente)  
**Fecha:** 2025-12-30  
**Siguiente paso:** Revisar plan con arquitecto y proceder a implementacion

