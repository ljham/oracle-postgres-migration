# Plan de Estrategia de Testing - Migracion Oracle a PostgreSQL

**Version:** 1.0  
**Fecha:** 2025-12-30  
**Autor:** backend-test-engineer (sub-agente)  
**Estado:** ready-for-implementation

---

## 1. Resumen Ejecutivo

### 1.1 Alcance del Testing

Este documento define la estrategia comprehensiva de testing para la migracion de **8,122 objetos PL/SQL** de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora), distribuidos como:

| Tipo de Objeto | Cantidad | Prioridad de Testing |
|----------------|----------|---------------------|
| Packages (SPEC + BODY) | 1,158 | CRITICA |
| Procedures | 196 | ALTA |
| Functions | 146 | ALTA |
| Triggers | 87 | ALTA |
| Types | 830 | MEDIA |
| Views | 147 | MEDIA |
| Materialized Views | 3 | MEDIA |
| Directories | 34 | CRITICA (migracion a S3) |

### 1.2 Tipos de Tests a Implementar

```
+-------------------------------------------------------------------+
|                    PIRAMIDE DE TESTING                             |
+-------------------------------------------------------------------+
|                                                                   |
|                        /\                                         |
|                       /  \                                        |
|                      / E2E \  5% - Shadow Testing Oracle vs PG    |
|                     /______\                                      |
|                    /        \                                     |
|                   /Integration\ 25% - Flujos completos, APIs      |
|                  /______________\                                 |
|                 /                \                                |
|                /     Unit Tests   \ 70% - Funciones, validaciones |
|               /____________________\                              |
|                                                                   |
+-------------------------------------------------------------------+
```

### 1.3 Metricas de Exito

| Metrica | Objetivo | Minimo Aceptable |
|---------|----------|------------------|
| **Tasa de Exito Global** | >95% | >90% |
| **Cobertura de Codigo Critico** | >90% | >80% |
| **Tests de Regresion** | 100% objetos COMPLEX | >95% |
| **Shadow Testing Match Rate** | >99% | >95% |
| **Tiempo de Ejecucion Suite** | <30 min | <60 min |

---

## 2. Framework de Shadow Testing

### 2.1 Concepto

El **Shadow Testing** ejecuta el mismo codigo/query tanto en Oracle como en PostgreSQL en paralelo, comparando resultados para validar equivalencia funcional.

```
+-------------------------------------------------------------------+
|                    ARQUITECTURA SHADOW TESTING                     |
+-------------------------------------------------------------------+
|                                                                   |
|  Test Case Input                                                  |
|  +-------------------+                                            |
|  | Test Data         |                                            |
|  | Parameters        |                                            |
|  +--------+----------+                                            |
|           |                                                       |
|           +--------------------+--------------------+             |
|           |                    |                    |             |
|           v                    v                    v             |
|  +----------------+   +----------------+   +----------------+     |
|  | Oracle 19c     |   | PostgreSQL 17.4|   | Comparador     |     |
|  | (Produccion)   |   | (Aurora Dev)   |   | de Resultados  |     |
|  +--------+-------+   +--------+-------+   +--------+-------+     |
|           |                    |                    ^             |
|           v                    v                    |             |
|  +----------------+   +----------------+            |             |
|  | Result Oracle  |-->| Result PG      |------------+             |
|  +----------------+   +----------------+                          |
|                                                                   |
|  Comparador evalua:                                               |
|  - Equivalencia de datos (rows, columns, types)                   |
|  - Performance (tiempo de ejecucion)                              |
|  - Side effects (inserts, updates, deletes)                       |
|  - Excepciones/errores                                            |
|                                                                   |
+-------------------------------------------------------------------+
```

### 2.2 Componentes del Framework Shadow Testing

#### 2.2.1 Schema de Resultados

```sql
-- Archivo: sql/testing/shadow_testing_schema.sql

-- Schema dedicado para shadow testing
CREATE SCHEMA IF NOT EXISTS shadow_testing;

-- Tabla principal de ejecuciones
CREATE TABLE shadow_testing.test_executions (
    execution_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificacion del test
    test_case_id        VARCHAR(100) NOT NULL,
    test_suite          VARCHAR(100) NOT NULL,  -- 'unit', 'integration', 'shadow'
    test_name           VARCHAR(256) NOT NULL,
    
    -- Objeto bajo prueba
    object_type         VARCHAR(50) NOT NULL,   -- FUNCTION, PROCEDURE, PACKAGE
    object_name         VARCHAR(256) NOT NULL,
    schema_name         VARCHAR(128),
    
    -- Parametros de entrada
    input_params        JSONB NOT NULL DEFAULT '{}',
    
    -- Resultados Oracle
    oracle_result       JSONB,
    oracle_error        TEXT,
    oracle_duration_ms  INTEGER,
    oracle_rows_affected INTEGER,
    
    -- Resultados PostgreSQL
    pg_result           JSONB,
    pg_error            TEXT,
    pg_duration_ms      INTEGER,
    pg_rows_affected    INTEGER,
    
    -- Comparacion
    results_match       BOOLEAN,
    match_details       JSONB,      -- Detalles de diferencias si no match
    
    -- Status
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- PENDING, RUNNING, PASSED, FAILED, ERROR, SKIPPED
    
    -- Metadata
    executed_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_by         VARCHAR(100),
    environment         VARCHAR(50),  -- 'dev', 'staging', 'production'
    
    -- Indices
    CONSTRAINT chk_status CHECK (
        status IN ('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'ERROR', 'SKIPPED')
    )
);

-- Tabla de casos de prueba definidos
CREATE TABLE shadow_testing.test_cases (
    test_case_id        VARCHAR(100) PRIMARY KEY,
    
    -- Definicion del test
    test_name           VARCHAR(256) NOT NULL,
    description         TEXT,
    test_type           VARCHAR(50) NOT NULL,  -- 'equivalence', 'regression', 'performance'
    
    -- Objeto a testear
    object_type         VARCHAR(50) NOT NULL,
    object_name         VARCHAR(256) NOT NULL,
    
    -- Datos de prueba
    input_template      JSONB NOT NULL,        -- Template de parametros
    expected_output     JSONB,                 -- Salida esperada (si conocida)
    
    -- Configuracion
    timeout_seconds     INTEGER DEFAULT 30,
    retry_count         INTEGER DEFAULT 3,
    compare_mode        VARCHAR(50) DEFAULT 'strict',  -- 'strict', 'fuzzy', 'type_only'
    
    -- Metadata
    priority            INTEGER DEFAULT 5,     -- 1 (critico) a 10 (opcional)
    tags                TEXT[],
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active           BOOLEAN DEFAULT TRUE
);

-- Tabla de datos de prueba
CREATE TABLE shadow_testing.test_data (
    data_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_case_id        VARCHAR(100) REFERENCES shadow_testing.test_cases(test_case_id),
    
    -- Datos
    data_set_name       VARCHAR(100) NOT NULL,
    input_data          JSONB NOT NULL,
    expected_oracle     JSONB,
    expected_pg         JSONB,
    
    -- Metadata
    is_edge_case        BOOLEAN DEFAULT FALSE,
    is_error_case       BOOLEAN DEFAULT FALSE,
    notes               TEXT,
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vista de resumen de ejecuciones
CREATE OR REPLACE VIEW shadow_testing.execution_summary AS
SELECT 
    test_suite,
    object_type,
    object_name,
    COUNT(*) as total_executions,
    SUM(CASE WHEN status = 'PASSED' THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
    SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as errors,
    ROUND(
        SUM(CASE WHEN status = 'PASSED' THEN 1 ELSE 0 END)::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) as pass_rate,
    AVG(oracle_duration_ms) as avg_oracle_ms,
    AVG(pg_duration_ms) as avg_pg_ms,
    MAX(executed_at) as last_execution
FROM shadow_testing.test_executions
GROUP BY test_suite, object_type, object_name;

-- Indices para performance
CREATE INDEX idx_executions_status ON shadow_testing.test_executions(status);
CREATE INDEX idx_executions_object ON shadow_testing.test_executions(object_name);
CREATE INDEX idx_executions_suite ON shadow_testing.test_executions(test_suite);
CREATE INDEX idx_executions_date ON shadow_testing.test_executions(executed_at DESC);
CREATE INDEX idx_test_cases_active ON shadow_testing.test_cases(is_active) WHERE is_active = TRUE;
```

#### 2.2.2 Comparador de Resultados

```python
# Especificacion: src/testing/shadow_comparator.py

"""
Comparador de resultados Shadow Testing

Responsabilidades:
1. Comparar resultados de Oracle vs PostgreSQL
2. Detectar diferencias semanticas vs sintacticas
3. Generar reportes detallados de discrepancias
4. Manejar tipos de datos con precision configurable

Modos de Comparacion:
- strict: Igualdad exacta (tipos, valores, orden)
- fuzzy: Tolerancia en numericos (epsilon), fechas (delta), strings (case-insensitive)
- type_only: Solo valida que los tipos sean equivalentes
- structure: Solo valida estructura (columnas, filas)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta


class CompareMode(Enum):
    STRICT = "strict"
    FUZZY = "fuzzy"
    TYPE_ONLY = "type_only"
    STRUCTURE = "structure"


@dataclass
class ComparisonConfig:
    """Configuracion para comparacion de resultados."""
    
    mode: CompareMode = CompareMode.STRICT
    
    # Tolerancias para modo fuzzy
    numeric_epsilon: Decimal = Decimal("0.0001")
    date_delta_seconds: int = 1
    string_case_sensitive: bool = True
    ignore_trailing_spaces: bool = True
    
    # Columnas a ignorar
    ignore_columns: list[str] = None
    
    # Tipos Oracle -> PostgreSQL mapping
    type_mappings: dict = None


@dataclass
class ComparisonResult:
    """Resultado de comparacion."""
    
    matches: bool
    
    # Detalles de comparacion
    oracle_row_count: int
    pg_row_count: int
    
    # Diferencias encontradas
    differences: list[dict] = None
    
    # Warnings (no-blocking)
    warnings: list[str] = None
    
    # Performance
    comparison_duration_ms: int = 0
    
    def to_json(self) -> dict:
        return {
            "matches": self.matches,
            "oracle_rows": self.oracle_row_count,
            "pg_rows": self.pg_row_count,
            "differences": self.differences or [],
            "warnings": self.warnings or [],
            "duration_ms": self.comparison_duration_ms
        }


class ShadowComparator:
    """
    Comparador de resultados Oracle vs PostgreSQL.
    
    Metodos principales:
    
    compare(oracle_result, pg_result, config) -> ComparisonResult
        Compara dos resultados y retorna diferencias
    
    compare_rows(oracle_rows, pg_rows, config) -> list[dict]
        Compara listas de filas
    
    compare_values(oracle_val, pg_val, oracle_type, pg_type, config) -> tuple[bool, str]
        Compara dos valores individuales
    
    generate_report(results: list[ComparisonResult]) -> str
        Genera reporte Markdown de multiples comparaciones
    """
    
    # Mapeo de tipos Oracle -> PostgreSQL para comparacion
    TYPE_EQUIVALENCE = {
        "VARCHAR2": ["VARCHAR", "TEXT", "CHARACTER VARYING"],
        "NUMBER": ["NUMERIC", "DECIMAL", "INTEGER", "BIGINT", "SMALLINT", "REAL", "DOUBLE PRECISION"],
        "DATE": ["TIMESTAMP", "TIMESTAMP WITHOUT TIME ZONE", "DATE"],
        "CLOB": ["TEXT"],
        "BLOB": ["BYTEA"],
        "RAW": ["BYTEA"],
        "BOOLEAN": ["BOOLEAN"],
        "PLS_INTEGER": ["INTEGER"],
        "BINARY_INTEGER": ["INTEGER"],
    }
    
    def compare(
        self,
        oracle_result: Any,
        pg_result: Any,
        config: ComparisonConfig = None
    ) -> ComparisonResult:
        """
        Compara resultados de Oracle y PostgreSQL.
        
        Args:
            oracle_result: Resultado de Oracle (dict, list, scalar)
            pg_result: Resultado de PostgreSQL (dict, list, scalar)
            config: Configuracion de comparacion
        
        Returns:
            ComparisonResult con detalles de la comparacion
        """
        # Implementacion pendiente
        pass
    
    def compare_scalar(
        self,
        oracle_val: Any,
        pg_val: Any,
        config: ComparisonConfig
    ) -> tuple[bool, Optional[str]]:
        """
        Compara dos valores escalares.
        
        Maneja conversiones de tipo automaticas:
        - NUMBER -> NUMERIC (con epsilon)
        - DATE -> TIMESTAMP (con delta)
        - VARCHAR2 -> TEXT (trim + case)
        
        Returns:
            (matches: bool, difference_description: Optional[str])
        """
        pass
    
    def normalize_value(
        self,
        value: Any,
        source: str,  # 'oracle' or 'pg'
        config: ComparisonConfig
    ) -> Any:
        """
        Normaliza un valor para comparacion.
        
        Transformaciones:
        - None/NULL handling
        - String trimming
        - Date format normalization
        - Numeric precision normalization
        """
        pass
```

#### 2.2.3 Ejecutor de Shadow Tests

```python
# Especificacion: src/testing/shadow_executor.py

"""
Ejecutor de Shadow Tests

Responsabilidades:
1. Conectar a Oracle y PostgreSQL simultaneamente
2. Ejecutar mismos statements en ambas bases
3. Capturar resultados, errores, tiempos
4. Persistir resultados en shadow_testing schema
5. Manejar transacciones y rollback

Modos de ejecucion:
- dry_run: Solo valida sintaxis, no ejecuta
- read_only: Solo SELECT/funciones sin side effects
- full: Ejecuta todo, incluyendo DML (con rollback)
"""

from dataclasses import dataclass
from typing import Optional, Callable
from datetime import datetime
import asyncio


@dataclass
class ExecutionContext:
    """Contexto de ejecucion de shadow test."""
    
    execution_id: str
    test_case_id: str
    
    # Conexiones
    oracle_dsn: str
    pg_dsn: str
    
    # Configuracion
    timeout_seconds: int = 30
    auto_rollback: bool = True
    capture_plan: bool = False  # Capturar explain plan
    
    # Metadata
    environment: str = "dev"
    executed_by: str = "shadow_executor"


@dataclass
class ExecutionResult:
    """Resultado de ejecucion de shadow test."""
    
    execution_id: str
    test_case_id: str
    
    # Resultados
    oracle_result: any
    oracle_error: Optional[str]
    oracle_duration_ms: int
    oracle_rows_affected: int
    
    pg_result: any
    pg_error: Optional[str]
    pg_duration_ms: int
    pg_rows_affected: int
    
    # Comparacion
    comparison_result: 'ComparisonResult'
    
    # Status
    status: str  # PASSED, FAILED, ERROR
    
    executed_at: datetime


class ShadowExecutor:
    """
    Ejecutor de Shadow Tests Oracle vs PostgreSQL.
    
    Uso:
        executor = ShadowExecutor(oracle_dsn, pg_dsn)
        
        # Ejecutar un test
        result = await executor.execute(
            test_case_id="TC001",
            oracle_stmt="SELECT pkg_ventas.calcular_descuento(:cliente_id) FROM dual",
            pg_stmt="SELECT pkg_ventas.calcular_descuento($1)",
            params={"cliente_id": 12345}
        )
        
        # Ejecutar suite completa
        results = await executor.execute_suite("regression_critical")
    
    Metodos:
        execute(test_case_id, oracle_stmt, pg_stmt, params) -> ExecutionResult
        execute_procedure(proc_name, params) -> ExecutionResult
        execute_function(func_name, params) -> ExecutionResult
        execute_suite(suite_name) -> list[ExecutionResult]
        generate_report() -> str
    """
    
    def __init__(
        self,
        oracle_dsn: str,
        pg_dsn: str,
        comparator: 'ShadowComparator' = None,
        config: 'ComparisonConfig' = None
    ):
        """
        Inicializa ejecutor con conexiones.
        
        Args:
            oracle_dsn: DSN de Oracle (cx_Oracle format)
            pg_dsn: DSN de PostgreSQL (asyncpg format)
            comparator: Comparador de resultados (opcional)
            config: Configuracion de comparacion (opcional)
        """
        pass
    
    async def execute(
        self,
        test_case_id: str,
        oracle_stmt: str,
        pg_stmt: str,
        params: dict = None,
        context: ExecutionContext = None
    ) -> ExecutionResult:
        """
        Ejecuta statement en Oracle y PostgreSQL, compara resultados.
        
        Args:
            test_case_id: ID unico del test case
            oracle_stmt: Statement Oracle (usa :param syntax)
            pg_stmt: Statement PostgreSQL (usa $1 syntax)
            params: Parametros para bind variables
            context: Contexto de ejecucion
        
        Returns:
            ExecutionResult con resultados de ambas bases
        """
        pass
    
    async def execute_procedure(
        self,
        proc_name: str,
        params: dict,
        test_case_id: str = None
    ) -> ExecutionResult:
        """
        Ejecuta un procedure en ambas bases.
        
        Genera automaticamente los statements para Oracle y PG.
        Maneja OUT params y INOUT params.
        """
        pass
    
    async def execute_function(
        self,
        func_name: str,
        params: list,
        test_case_id: str = None
    ) -> ExecutionResult:
        """
        Ejecuta una funcion en ambas bases.
        
        Oracle: SELECT func_name(:p1, :p2) FROM dual
        PG: SELECT func_name($1, $2)
        """
        pass
    
    async def execute_suite(
        self,
        suite_name: str,
        parallel: bool = True,
        max_concurrent: int = 10
    ) -> list[ExecutionResult]:
        """
        Ejecuta una suite completa de tests.
        
        Args:
            suite_name: Nombre de la suite (ej: 'regression_critical')
            parallel: Ejecutar tests en paralelo
            max_concurrent: Maximo de tests concurrentes
        
        Returns:
            Lista de resultados de ejecucion
        """
        pass
```

### 2.3 Estrategia de Datos de Prueba

#### 2.3.1 Generacion de Datos

```python
# Especificacion: src/testing/test_data_generator.py

"""
Generador de Datos de Prueba

Estrategias:
1. Snapshot de produccion (anonimizado)
2. Generacion sintetica basada en constraints
3. Edge cases automaticos
4. Datos de regresion de bugs historicos

IMPORTANTE: Cumplir con regulaciones de privacidad
- PII debe ser anonimizada
- Datos sensibles de salud (PHI) requieren tratamiento especial
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DataGenerationConfig:
    """Configuracion de generacion de datos."""
    
    source: str = "synthetic"  # "synthetic", "snapshot", "fixture"
    
    # Anonimizacion
    anonymize_pii: bool = True
    anonymize_phi: bool = True
    
    # Volumenes
    small_dataset_rows: int = 100
    medium_dataset_rows: int = 1000
    large_dataset_rows: int = 10000
    
    # Seed para reproducibilidad
    random_seed: int = 42


class TestDataGenerator:
    """
    Generador de datos de prueba.
    
    Metodos:
        generate_for_procedure(proc_name) -> list[dict]
        generate_for_function(func_name) -> list[dict]
        generate_edge_cases(object_name) -> list[dict]
        snapshot_from_production(table_name, sample_size) -> list[dict]
        anonymize(data) -> list[dict]
    """
    
    # Patrones de anonimizacion
    PII_PATTERNS = {
        "nombre": lambda: fake.name(),
        "email": lambda: fake.email(),
        "telefono": lambda: fake.phone_number(),
        "direccion": lambda: fake.address(),
        "cedula": lambda: fake.ssn(),
        "ruc": lambda: f"09{fake.numerify('##########')}001",
    }
    
    def generate_for_object(
        self,
        object_name: str,
        object_type: str,
        count: int = 10
    ) -> list[dict]:
        """
        Genera datos de prueba para un objeto.
        
        Analiza la firma del objeto (parametros) y genera
        datos validos automaticamente.
        """
        pass
    
    def generate_edge_cases(
        self,
        object_name: str
    ) -> list[dict]:
        """
        Genera casos edge automaticamente.
        
        Incluye:
        - NULL values en cada parametro
        - Valores limite (min/max)
        - Strings vacios vs NULL
        - Fechas limite
        - Numeros negativos
        - Caracteres especiales
        """
        pass
```

#### 2.3.2 Fixtures Predefinidos

```python
# Especificacion: tests/fixtures/migration_fixtures.py

"""
Fixtures predefinidos para testing de migracion.

Organizacion:
- fixtures/procedures/ - Datos para procedures
- fixtures/functions/ - Datos para functions
- fixtures/packages/ - Datos para packages
- fixtures/regression/ - Datos de bugs corregidos

Formato: JSON o Python dataclasses
"""

import pytest
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal


# ============================================================
# FIXTURES DE CLIENTE/PACIENTE
# ============================================================

@dataclass
class ClienteTestData:
    """Datos de prueba para operaciones de cliente."""
    cliente_id: int
    tipo_documento: str
    numero_documento: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    email: str
    telefono: str
    
    @classmethod
    def valido(cls) -> 'ClienteTestData':
        """Cliente valido standard."""
        return cls(
            cliente_id=1001,
            tipo_documento="CED",
            numero_documento="0912345678",
            nombres="Juan Carlos",
            apellidos="Perez Garcia",
            fecha_nacimiento=date(1985, 5, 15),
            email="jperez@test.com",
            telefono="0999888777"
        )
    
    @classmethod
    def menor_edad(cls) -> 'ClienteTestData':
        """Cliente menor de edad."""
        return cls(
            cliente_id=1002,
            tipo_documento="CED",
            numero_documento="0956789012",
            nombres="Maria Jose",
            apellidos="Lopez",
            fecha_nacimiento=date(2010, 8, 20),
            email=None,
            telefono="0999111222"
        )


# ============================================================
# FIXTURES DE ORDEN/FACTURACION
# ============================================================

@dataclass
class OrdenTestData:
    """Datos de prueba para ordenes."""
    orden_id: int
    cliente_id: int
    fecha_orden: datetime
    sucursal_id: int
    total: Decimal
    estado: str
    
    @classmethod
    def orden_pendiente(cls) -> 'OrdenTestData':
        return cls(
            orden_id=50001,
            cliente_id=1001,
            fecha_orden=datetime.now(),
            sucursal_id=1,
            total=Decimal("150.00"),
            estado="PENDIENTE"
        )
    
    @classmethod
    def orden_facturada(cls) -> 'OrdenTestData':
        return cls(
            orden_id=50002,
            cliente_id=1001,
            fecha_orden=datetime(2024, 1, 15, 10, 30),
            sucursal_id=1,
            total=Decimal("250.50"),
            estado="FACTURADO"
        )


# ============================================================
# PYTEST FIXTURES
# ============================================================

@pytest.fixture
def cliente_valido():
    """Fixture: cliente valido para tests."""
    return ClienteTestData.valido()


@pytest.fixture
def orden_pendiente():
    """Fixture: orden pendiente para tests."""
    return OrdenTestData.orden_pendiente()


@pytest.fixture
def pg_connection(request):
    """
    Fixture: conexion a PostgreSQL de prueba.
    
    Uso:
        def test_function(pg_connection):
            result = pg_connection.execute("SELECT 1")
    """
    import asyncpg
    
    conn = asyncpg.connect(
        host=os.getenv("PG_TEST_HOST", "localhost"),
        database=os.getenv("PG_TEST_DB", "migration_test"),
        user=os.getenv("PG_TEST_USER", "test_user"),
        password=os.getenv("PG_TEST_PASS", "test_pass")
    )
    
    yield conn
    
    # Cleanup
    conn.close()


@pytest.fixture
def shadow_executor(pg_connection):
    """
    Fixture: ejecutor de shadow tests.
    
    Uso:
        async def test_shadow(shadow_executor):
            result = await shadow_executor.execute_function(
                "calcular_descuento", [cliente_id]
            )
            assert result.comparison_result.matches
    """
    from src.testing.shadow_executor import ShadowExecutor
    
    return ShadowExecutor(
        oracle_dsn=os.getenv("ORACLE_TEST_DSN"),
        pg_dsn=os.getenv("PG_TEST_DSN")
    )
```

---

## 3. Validacion de Sintaxis PostgreSQL 17.4

### 3.1 Validador de Sintaxis

```python
# Especificacion: src/testing/pg_syntax_validator.py

"""
Validador de Sintaxis PostgreSQL 17.4

Responsabilidades:
1. Validar sintaxis PL/pgSQL sin ejecutar
2. Detectar features no soportadas en Aurora
3. Verificar compatibilidad de tipos
4. Generar reporte de errores de sintaxis

Metodos de validacion:
- parse_only: Solo parsea, no crea objetos
- dry_run: Crea en transaccion, hace rollback
- validate_extension: Verifica extensiones requeridas
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ValidationLevel(Enum):
    SYNTAX = "syntax"       # Solo sintaxis
    SEMANTIC = "semantic"   # Tipos y referencias
    RUNTIME = "runtime"     # Ejecutable (dry run)


@dataclass
class SyntaxError:
    """Error de sintaxis detectado."""
    line: int
    column: int
    message: str
    severity: str  # ERROR, WARNING, NOTICE
    hint: Optional[str] = None
    
    # Contexto
    source_line: str = ""
    suggested_fix: Optional[str] = None


@dataclass
class ValidationResult:
    """Resultado de validacion de sintaxis."""
    
    object_name: str
    object_type: str
    
    is_valid: bool
    errors: list[SyntaxError]
    warnings: list[SyntaxError]
    
    # Dependencias detectadas
    referenced_objects: list[str]
    referenced_types: list[str]
    required_extensions: list[str]
    
    # Metadata
    validation_level: ValidationLevel
    validation_duration_ms: int


class PgSyntaxValidator:
    """
    Validador de sintaxis PostgreSQL 17.4.
    
    Uso:
        validator = PgSyntaxValidator(pg_connection)
        
        # Validar un archivo SQL
        result = validator.validate_file("migrated/functions/calc_descuento.sql")
        
        # Validar string SQL
        result = validator.validate_sql(sql_code, object_type="FUNCTION")
        
        # Validar batch de archivos
        results = validator.validate_batch(["file1.sql", "file2.sql"])
        
        # Generar reporte
        report = validator.generate_report(results)
    """
    
    # Features no soportados en Aurora PostgreSQL 17.4
    UNSUPPORTED_FEATURES = [
        "CREATE EXTENSION IF NOT EXISTS plpython3u",  # No trusted languages
        "COPY ... FROM PROGRAM",                       # No shell access
        "lo_import", "lo_export",                      # Limited large object
    ]
    
    # Extensiones disponibles en Aurora (verificar en cada version)
    AVAILABLE_EXTENSIONS = [
        "aws_s3",
        "aws_lambda",
        "aws_commons",
        "dblink",
        "pg_cron",
        "vector",
        "postgis",
        "pg_stat_statements",
    ]
    
    def __init__(self, pg_dsn: str):
        """
        Inicializa validador.
        
        Args:
            pg_dsn: DSN de PostgreSQL (base de datos de validacion)
        """
        pass
    
    def validate_sql(
        self,
        sql: str,
        object_type: str = None,
        level: ValidationLevel = ValidationLevel.SYNTAX
    ) -> ValidationResult:
        """
        Valida codigo SQL/PL/pgSQL.
        
        Args:
            sql: Codigo SQL a validar
            object_type: Tipo de objeto (FUNCTION, PROCEDURE, etc.)
            level: Nivel de validacion
        
        Returns:
            ValidationResult con errores y warnings
        """
        pass
    
    def validate_file(
        self,
        file_path: str,
        level: ValidationLevel = ValidationLevel.SYNTAX
    ) -> ValidationResult:
        """
        Valida archivo SQL.
        """
        pass
    
    def validate_batch(
        self,
        files: list[str],
        parallel: bool = True,
        level: ValidationLevel = ValidationLevel.SYNTAX
    ) -> list[ValidationResult]:
        """
        Valida batch de archivos en paralelo.
        """
        pass
    
    def check_extensions(
        self,
        sql: str
    ) -> list[str]:
        """
        Detecta extensiones requeridas en el codigo.
        
        Returns:
            Lista de extensiones necesarias
        """
        pass
    
    def suggest_fixes(
        self,
        error: SyntaxError
    ) -> list[str]:
        """
        Sugiere correcciones para errores comunes.
        
        Patrones conocidos:
        - VARCHAR2 -> VARCHAR
        - NVL -> COALESCE
        - SYSDATE -> CURRENT_TIMESTAMP
        - (+) join -> LEFT/RIGHT JOIN
        """
        pass
```

### 3.2 Reglas de Validacion Especificas

```python
# Especificacion: src/testing/pg_validation_rules.py

"""
Reglas de Validacion Especificas para Migracion Oracle -> PostgreSQL

Categorias:
1. Sintaxis basica (keywords, operators)
2. Tipos de datos
3. Funciones y operadores
4. PL/pgSQL vs PL/SQL
5. Features Aurora-especificos
"""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ValidationRule:
    """Regla de validacion."""
    
    rule_id: str
    category: str
    description: str
    
    # Pattern para detectar
    oracle_pattern: str       # Regex para Oracle syntax
    pg_equivalent: str        # Equivalente PostgreSQL
    
    # Severidad
    severity: str = "ERROR"   # ERROR, WARNING, INFO
    
    # Accion
    auto_fix: bool = False
    fix_function: Optional[Callable] = None


# ============================================================
# REGLAS DE TIPOS DE DATOS
# ============================================================

DATA_TYPE_RULES = [
    ValidationRule(
        rule_id="DT001",
        category="data_types",
        description="VARCHAR2 debe ser VARCHAR o TEXT",
        oracle_pattern=r"\bVARCHAR2\s*\(\s*(\d+)\s*(BYTE|CHAR)?\s*\)",
        pg_equivalent="VARCHAR(\\1)",
        severity="ERROR",
        auto_fix=True
    ),
    ValidationRule(
        rule_id="DT002",
        category="data_types",
        description="NUMBER sin precision debe ser NUMERIC",
        oracle_pattern=r"\bNUMBER\b(?!\s*\()",
        pg_equivalent="NUMERIC",
        severity="ERROR",
        auto_fix=True
    ),
    ValidationRule(
        rule_id="DT003",
        category="data_types",
        description="NUMBER(p,s) debe ser NUMERIC(p,s)",
        oracle_pattern=r"\bNUMBER\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)",
        pg_equivalent="NUMERIC(\\1,\\2)",
        severity="ERROR",
        auto_fix=True
    ),
    ValidationRule(
        rule_id="DT004",
        category="data_types",
        description="CLOB debe ser TEXT",
        oracle_pattern=r"\bCLOB\b",
        pg_equivalent="TEXT",
        severity="ERROR",
        auto_fix=True
    ),
    ValidationRule(
        rule_id="DT005",
        category="data_types",
        description="BLOB debe ser BYTEA",
        oracle_pattern=r"\bBLOB\b",
        pg_equivalent="BYTEA",
        severity="ERROR",
        auto_fix=True
    ),
    ValidationRule(
        rule_id="DT006",
        category="data_types",
        description="PLS_INTEGER debe ser INTEGER",
        oracle_pattern=r"\bPLS_INTEGER\b",
        pg_equivalent="INTEGER",
        severity="ERROR",
        auto_fix=True
    ),
]


# ============================================================
# REGLAS DE FUNCIONES
# ============================================================

FUNCTION_RULES = [
    ValidationRule(
        rule_id="FN001",
        category="functions",
        description="NVL debe ser COALESCE",
        oracle_pattern=r"\bNVL\s*\(",
        pg_equivalent="COALESCE(",
        severity="ERROR",
        auto_fix=True
    ),
    ValidationRule(
        rule_id="FN002",
        category="functions",
        description="NVL2(expr, val_not_null, val_null) no existe en PostgreSQL",
        oracle_pattern=r"\bNVL2\s*\(",
        pg_equivalent="CASE WHEN expr IS NOT NULL THEN val_not_null ELSE val_null END",
        severity="ERROR",
        auto_fix=False  # Requiere analisis manual
    ),
    ValidationRule(
        rule_id="FN003",
        category="functions",
        description="DECODE debe ser CASE",
        oracle_pattern=r"\bDECODE\s*\(",
        pg_equivalent="CASE expression",
        severity="ERROR",
        auto_fix=False  # Requiere analisis de argumentos
    ),
    ValidationRule(
        rule_id="FN004",
        category="functions",
        description="SYSDATE debe ser CURRENT_TIMESTAMP o CURRENT_DATE",
        oracle_pattern=r"\bSYSDATE\b",
        pg_equivalent="CURRENT_TIMESTAMP",
        severity="ERROR",
        auto_fix=True
    ),
    ValidationRule(
        rule_id="FN005",
        category="functions",
        description="SYSTIMESTAMP debe ser CURRENT_TIMESTAMP",
        oracle_pattern=r"\bSYSTIMESTAMP\b",
        pg_equivalent="CURRENT_TIMESTAMP",
        severity="ERROR",
        auto_fix=True
    ),
    ValidationRule(
        rule_id="FN006",
        category="functions",
        description="TO_DATE con formato Oracle",
        oracle_pattern=r"\bTO_DATE\s*\(\s*'[^']*'\s*,\s*'([^']*)'\s*\)",
        pg_equivalent="TO_TIMESTAMP con formato PostgreSQL",
        severity="WARNING",
        auto_fix=False  # Formato necesita conversion
    ),
]


# ============================================================
# REGLAS DE SINTAXIS PL/pgSQL
# ============================================================

PLPGSQL_RULES = [
    ValidationRule(
        rule_id="PL001",
        category="plpgsql",
        description="EXCEPTION debe usar formato PostgreSQL",
        oracle_pattern=r"\bEXCEPTION\s+WHEN\s+([A-Z_]+)\s+THEN",
        pg_equivalent="EXCEPTION WHEN exception_name THEN",
        severity="ERROR",
        auto_fix=False
    ),
    ValidationRule(
        rule_id="PL002",
        category="plpgsql",
        description="RAISE_APPLICATION_ERROR no existe en PostgreSQL",
        oracle_pattern=r"\bRAISE_APPLICATION_ERROR\s*\(\s*(-?\d+)\s*,",
        pg_equivalent="RAISE EXCEPTION USING ERRCODE = 'P0001'",
        severity="ERROR",
        auto_fix=False
    ),
    ValidationRule(
        rule_id="PL003",
        category="plpgsql",
        description="PRAGMA AUTONOMOUS_TRANSACTION requiere dblink",
        oracle_pattern=r"\bPRAGMA\s+AUTONOMOUS_TRANSACTION\b",
        pg_equivalent="dblink o funcion separada",
        severity="CRITICAL",
        auto_fix=False
    ),
    ValidationRule(
        rule_id="PL004",
        category="plpgsql",
        description="Cursores implicitos FOR UPDATE requieren ajuste",
        oracle_pattern=r"\bFOR\s+UPDATE\s+OF\b",
        pg_equivalent="FOR UPDATE",
        severity="WARNING",
        auto_fix=True
    ),
    ValidationRule(
        rule_id="PL005",
        category="plpgsql",
        description="Variables de paquete requieren session variables",
        oracle_pattern=r"(\w+)\.(\w+)\s*:=",  # pkg.variable := value
        pg_equivalent="SET session.var / current_setting()",
        severity="CRITICAL",
        auto_fix=False
    ),
]


# ============================================================
# REGLAS AURORA-ESPECIFICAS
# ============================================================

AURORA_RULES = [
    ValidationRule(
        rule_id="AU001",
        category="aurora",
        description="UTL_FILE requiere aws_s3",
        oracle_pattern=r"\bUTL_FILE\.",
        pg_equivalent="aws_s3 extension",
        severity="CRITICAL",
        auto_fix=False
    ),
    ValidationRule(
        rule_id="AU002",
        category="aurora",
        description="UTL_HTTP requiere Lambda + wrapper",
        oracle_pattern=r"\bUTL_HTTP\.",
        pg_equivalent="aws_lambda + utl_http_utility schema",
        severity="CRITICAL",
        auto_fix=False
    ),
    ValidationRule(
        rule_id="AU003",
        category="aurora",
        description="DBMS_SCHEDULER requiere pg_cron",
        oracle_pattern=r"\bDBMS_SCHEDULER\.",
        pg_equivalent="pg_cron extension",
        severity="CRITICAL",
        auto_fix=False
    ),
    ValidationRule(
        rule_id="AU004",
        category="aurora",
        description="DBMS_JOB requiere pg_cron",
        oracle_pattern=r"\bDBMS_JOB\.",
        pg_equivalent="pg_cron extension",
        severity="CRITICAL",
        auto_fix=False
    ),
    ValidationRule(
        rule_id="AU005",
        category="aurora",
        description="DIRECTORY objects migran a S3 buckets",
        oracle_pattern=r"\bCREATE\s+(OR\s+REPLACE\s+)?DIRECTORY\b",
        pg_equivalent="S3 bucket + aws_s3 extension",
        severity="CRITICAL",
        auto_fix=False
    ),
]


# Consolidar todas las reglas
ALL_VALIDATION_RULES = (
    DATA_TYPE_RULES + 
    FUNCTION_RULES + 
    PLPGSQL_RULES + 
    AURORA_RULES
)
```

---

## 4. Testing de Objetos Complejos

### 4.1 AUTONOMOUS_TRANSACTION

```python
# Especificacion: tests/complex/test_autonomous_transaction.py

"""
Tests para objetos con AUTONOMOUS_TRANSACTION

Estrategia de migracion:
- Oracle: PRAGMA AUTONOMOUS_TRANSACTION
- PostgreSQL: dblink a si mismo (loopback connection)

Casos de prueba:
1. Logging en transacciones que hacen rollback
2. Auditoria independiente de la transaccion principal
3. Secuencias de commits parciales

IMPORTANTE: dblink tiene overhead de conexion
"""

import pytest
from src.testing.shadow_executor import ShadowExecutor


class TestAutonomousTransaction:
    """Tests para AUTONOMOUS_TRANSACTION."""
    
    @pytest.fixture
    def dblink_connection_string(self):
        """Connection string para dblink loopback."""
        return "host=localhost dbname=testdb user=test password=test"
    
    async def test_logging_survives_rollback(
        self, 
        shadow_executor: ShadowExecutor
    ):
        """
        Verifica que logging con AUTONOMOUS_TRANSACTION
        persiste aunque la transaccion principal haga rollback.
        
        Escenario:
        1. Iniciar transaccion
        2. Insertar registro en tabla principal
        3. Llamar procedure de logging (autonomous)
        4. ROLLBACK de transaccion principal
        5. Verificar que log existe
        
        Oracle:
            BEGIN
                INSERT INTO tabla_principal VALUES (...);
                pkg_log.registrar_evento('INSERT', ...);  -- AUTONOMOUS
                ROLLBACK;
            END;
            -- Log debe existir, registro no
        
        PostgreSQL (con dblink):
            DO $$
            DECLARE
                v_result TEXT;
            BEGIN
                INSERT INTO tabla_principal VALUES (...);
                SELECT dblink_exec(
                    'connection_name',
                    'SELECT pkg_log.registrar_evento(...)'
                ) INTO v_result;
                ROLLBACK;
            END;
            $$;
        """
        pass
    
    async def test_audit_independent_transaction(
        self,
        shadow_executor: ShadowExecutor
    ):
        """
        Verifica auditoria independiente.
        
        Caso: Procedure que hace audit de cada intento,
        incluso si el intento falla.
        """
        pass
    
    async def test_dblink_connection_overhead(
        self,
        shadow_executor: ShadowExecutor
    ):
        """
        Mide overhead de dblink vs transaccion normal.
        
        Objetivo: dblink no debe agregar >50ms por llamada.
        """
        pass


# ============================================================
# FIXTURES PARA AUTONOMOUS_TRANSACTION
# ============================================================

@pytest.fixture
def autonomous_test_schema(pg_connection):
    """
    Crea schema de prueba para AUTONOMOUS_TRANSACTION.
    """
    sql = """
    -- Tabla principal
    CREATE TABLE IF NOT EXISTS test_at.operaciones (
        id SERIAL PRIMARY KEY,
        descripcion TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Tabla de logs (debe persistir en rollback)
    CREATE TABLE IF NOT EXISTS test_at.logs (
        id SERIAL PRIMARY KEY,
        operacion_id INTEGER,
        mensaje TEXT,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Funcion de logging usando dblink (simula AUTONOMOUS)
    CREATE OR REPLACE FUNCTION test_at.log_autonomous(
        p_operacion_id INTEGER,
        p_mensaje TEXT
    ) RETURNS VOID AS $$
    DECLARE
        v_conn_str TEXT := 'dbname=' || current_database();
    BEGIN
        PERFORM dblink_connect('log_conn', v_conn_str);
        PERFORM dblink_exec('log_conn', format(
            'INSERT INTO test_at.logs (operacion_id, mensaje) VALUES (%L, %L)',
            p_operacion_id, p_mensaje
        ));
        PERFORM dblink_disconnect('log_conn');
    END;
    $$ LANGUAGE plpgsql;
    """
    pg_connection.execute(sql)
    yield
    pg_connection.execute("DROP SCHEMA IF EXISTS test_at CASCADE")
```

### 4.2 UTL_HTTP (Lambda Integration)

```python
# Especificacion: tests/complex/test_utl_http_wrapper.py

"""
Tests para UTL_HTTP migrado a Lambda

Arquitectura:
- Oracle: UTL_HTTP.REQUEST, UTL_HTTP.BEGIN_REQUEST, etc.
- PostgreSQL: Schema utl_http_utility + Lambda aws-http-helper

Casos de prueba:
1. GET request simple
2. POST con body JSON
3. Autenticacion Basic y Bearer
4. Manejo de errores HTTP (4xx, 5xx)
5. Timeout handling
6. Headers customizados
"""

import pytest
from unittest.mock import MagicMock, patch
from src.testing.shadow_executor import ShadowExecutor


class TestUtlHttpWrapper:
    """Tests para wrapper functions de UTL_HTTP."""
    
    @pytest.fixture
    def mock_lambda_response(self):
        """Mock de respuesta Lambda."""
        return {
            "statusCode": 200,
            "success": True,
            "data": {"result": "OK"},
            "headers": {"Content-Type": "application/json"},
            "timing": {"duration_ms": 150}
        }
    
    async def test_simple_get_request(
        self,
        pg_connection,
        mock_lambda_response
    ):
        """
        Test GET request simple.
        
        Oracle equivalente:
            DECLARE
                req  UTL_HTTP.REQ;
                resp UTL_HTTP.RESP;
            BEGIN
                req := UTL_HTTP.BEGIN_REQUEST('https://api.example.com/status');
                resp := UTL_HTTP.GET_RESPONSE(req);
                DBMS_OUTPUT.PUT_LINE(resp.status_code);
                UTL_HTTP.END_RESPONSE(resp);
            END;
        
        PostgreSQL con wrapper:
            DO $$
            DECLARE
                v_req utl_http_utility.req;
                v_resp utl_http_utility.resp;
            BEGIN
                v_req := utl_http_utility.begin_request('https://api.example.com/status');
                v_resp := utl_http_utility.get_response(v_req);
                RAISE NOTICE 'Status: %', v_resp.status_code;
            END;
            $$;
        """
        pass
    
    async def test_post_with_json_body(
        self,
        pg_connection,
        mock_lambda_response
    ):
        """
        Test POST con body JSON.
        
        Verifica:
        - Serializacion correcta de body
        - Content-Type header
        - Parsing de respuesta JSON
        """
        pass
    
    async def test_authentication_basic(
        self,
        pg_connection,
        mock_lambda_response
    ):
        """
        Test autenticacion Basic.
        
        Oracle:
            UTL_HTTP.SET_AUTHENTICATION(req, 'user', 'pass', 'Basic', FALSE);
        
        PostgreSQL wrapper:
            utl_http_utility.set_authentication(req, 'user', 'pass', 'basic');
        """
        pass
    
    async def test_http_error_handling(
        self,
        pg_connection
    ):
        """
        Test manejo de errores HTTP (4xx, 5xx).
        
        Verifica que errores se propagan correctamente
        como excepciones PL/pgSQL.
        """
        pass
    
    async def test_timeout_handling(
        self,
        pg_connection
    ):
        """
        Test timeout en requests.
        
        Lambda tiene timeout configurable.
        Verificar que timeout se respeta y genera excepcion apropiada.
        """
        pass


# ============================================================
# TESTS DE INTEGRACION CON LAMBDA REAL
# ============================================================

@pytest.mark.integration
@pytest.mark.slow
class TestUtlHttpLambdaIntegration:
    """
    Tests de integracion con Lambda real.
    
    Requiere:
    - Lambda aurora-http-helper deployed
    - VPC configurado
    - IAM roles correctos
    
    Ejecutar con: pytest -m integration
    """
    
    @pytest.fixture
    def lambda_arn(self):
        """ARN de Lambda HTTP helper."""
        return os.getenv(
            "LAMBDA_HTTP_ARN",
            "arn:aws:lambda:us-east-1:123456789:function:aurora-http-helper"
        )
    
    async def test_real_http_request(
        self,
        pg_connection,
        lambda_arn
    ):
        """
        Test con Lambda real haciendo request a API publica.
        
        Usa httpbin.org para testing.
        """
        sql = """
        DO $$
        DECLARE
            v_req utl_http_utility.req;
            v_resp utl_http_utility.resp;
        BEGIN
            v_req := utl_http_utility.begin_request(
                'https://httpbin.org/get',
                'GET'
            );
            v_resp := utl_http_utility.get_response(v_req);
            
            IF v_resp.status_code != 200 THEN
                RAISE EXCEPTION 'Expected 200, got %', v_resp.status_code;
            END IF;
        END;
        $$;
        """
        result = await pg_connection.execute(sql)
        assert result is not None
```

### 4.3 DIRECTORY a S3

```python
# Especificacion: tests/complex/test_directory_s3.py

"""
Tests para migracion DIRECTORY -> S3

Arquitectura:
- Oracle: CREATE DIRECTORY, UTL_FILE.FOPEN, etc.
- PostgreSQL: aws_s3 extension, S3 buckets

Objetos detectados usando DIRECTORY: 34

Casos de prueba:
1. Lectura de archivos (UTL_FILE.GET_LINE -> aws_s3.get_object)
2. Escritura de archivos (UTL_FILE.PUT_LINE -> aws_s3.put_object)
3. Existencia de archivos
4. Listado de archivos en directorio
"""

import pytest
import boto3
from moto import mock_s3


class TestDirectoryToS3:
    """Tests para migracion de DIRECTORY a S3."""
    
    @pytest.fixture
    def s3_bucket(self):
        """Bucket S3 de prueba."""
        return "efs-veris-compartidos-dev"
    
    @pytest.fixture
    def mock_s3_files(self, s3_bucket):
        """Mock de archivos en S3."""
        with mock_s3():
            s3 = boto3.client("s3", region_name="us-east-1")
            s3.create_bucket(Bucket=s3_bucket)
            
            # Crear archivos de prueba
            s3.put_object(
                Bucket=s3_bucket,
                Key="reportes/reporte_2024_01.csv",
                Body=b"col1,col2\nval1,val2\n"
            )
            s3.put_object(
                Bucket=s3_bucket,
                Key="facturas/factura_001.xml",
                Body=b"<factura><total>100.00</total></factura>"
            )
            
            yield s3
    
    async def test_read_file_from_s3(
        self,
        pg_connection,
        mock_s3_files,
        s3_bucket
    ):
        """
        Test lectura de archivo desde S3.
        
        Oracle:
            DECLARE
                v_file UTL_FILE.FILE_TYPE;
                v_line VARCHAR2(4000);
            BEGIN
                v_file := UTL_FILE.FOPEN('REPORTES_DIR', 'reporte.csv', 'R');
                UTL_FILE.GET_LINE(v_file, v_line);
                UTL_FILE.FCLOSE(v_file);
            END;
        
        PostgreSQL (aws_s3):
            SELECT aws_s3.get_object(
                'reportes/reporte.csv',
                'efs-veris-compartidos-dev',
                'us-east-1'
            );
        """
        pass
    
    async def test_write_file_to_s3(
        self,
        pg_connection,
        mock_s3_files,
        s3_bucket
    ):
        """
        Test escritura de archivo a S3.
        
        Oracle:
            DECLARE
                v_file UTL_FILE.FILE_TYPE;
            BEGIN
                v_file := UTL_FILE.FOPEN('REPORTES_DIR', 'output.csv', 'W');
                UTL_FILE.PUT_LINE(v_file, 'header1,header2');
                UTL_FILE.PUT_LINE(v_file, 'value1,value2');
                UTL_FILE.FCLOSE(v_file);
            END;
        
        PostgreSQL (aws_s3):
            SELECT aws_s3.put_object(
                'reportes/output.csv',
                'efs-veris-compartidos-dev',
                'us-east-1',
                E'header1,header2\nvalue1,value2\n'
            );
        """
        pass
    
    async def test_file_exists(
        self,
        pg_connection,
        mock_s3_files,
        s3_bucket
    ):
        """
        Test verificacion de existencia de archivo.
        
        Oracle:
            UTL_FILE.FGETATTR(...)
        
        PostgreSQL:
            Usar head_object o listar con prefijo
        """
        pass


# ============================================================
# MAPEO DE DIRECTORIOS
# ============================================================

DIRECTORY_MAPPING = {
    # Oracle DIRECTORY -> S3 path prefix
    "REPORTES_DIR": "reportes/",
    "FACTURAS_DIR": "facturas/",
    "TEMP_DIR": "temp/",
    "LOGS_DIR": "logs/",
    "EXPORT_DIR": "exports/",
    # ... agregar los 34 directories detectados
}
```

---

## 5. Automatizacion y Reportes

### 5.1 Test Runner Automatizado

```python
# Especificacion: src/testing/test_runner.py

"""
Test Runner Automatizado para Migracion

Responsabilidades:
1. Descubrir y ejecutar tests automaticamente
2. Generar reportes en multiples formatos
3. Integracion con CI/CD
4. Notificaciones de resultados

Formatos de reporte:
- Markdown (para documentacion)
- HTML (para visualizacion)
- JSON (para integracion)
- JUnit XML (para CI/CD)
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class ReportFormat(Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    JUNIT_XML = "junit"


@dataclass
class TestSuiteConfig:
    """Configuracion de suite de tests."""
    
    suite_name: str
    description: str
    
    # Filtros
    include_patterns: list[str] = None  # ["test_*.py"]
    exclude_patterns: list[str] = None  # ["test_slow_*.py"]
    tags: list[str] = None              # ["critical", "regression"]
    
    # Ejecucion
    parallel: bool = True
    max_workers: int = 4
    timeout_seconds: int = 300
    fail_fast: bool = False
    
    # Reportes
    report_formats: list[ReportFormat] = None
    report_output_dir: str = "reports/"


@dataclass
class TestResult:
    """Resultado de un test individual."""
    
    test_id: str
    test_name: str
    test_file: str
    
    status: str  # PASSED, FAILED, ERROR, SKIPPED
    duration_ms: int
    
    # Detalles
    message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Shadow testing
    oracle_result: Optional[dict] = None
    pg_result: Optional[dict] = None
    comparison: Optional[dict] = None


@dataclass
class SuiteResult:
    """Resultado de una suite completa."""
    
    suite_name: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    
    # Estadisticas
    total_tests: int
    passed: int
    failed: int
    errors: int
    skipped: int
    
    # Tasa de exito
    pass_rate: float
    
    # Tests individuales
    test_results: list[TestResult]
    
    # Metadata
    environment: str
    executed_by: str


class MigrationTestRunner:
    """
    Runner de tests para migracion.
    
    Uso:
        runner = MigrationTestRunner(config)
        
        # Ejecutar suite especifica
        result = await runner.run_suite("regression_critical")
        
        # Ejecutar todos los tests
        result = await runner.run_all()
        
        # Generar reportes
        runner.generate_reports(result, formats=[ReportFormat.MARKDOWN, ReportFormat.HTML])
    """
    
    def __init__(self, config: TestSuiteConfig):
        self.config = config
        self.results: list[SuiteResult] = []
    
    async def run_suite(
        self,
        suite_name: str,
        tags: list[str] = None
    ) -> SuiteResult:
        """
        Ejecuta una suite de tests.
        
        Args:
            suite_name: Nombre de la suite
            tags: Tags para filtrar tests
        
        Returns:
            SuiteResult con resultados
        """
        pass
    
    async def run_shadow_tests(
        self,
        objects: list[str] = None
    ) -> SuiteResult:
        """
        Ejecuta shadow tests para objetos especificados.
        
        Si objects es None, ejecuta para todos los objetos migrados.
        """
        pass
    
    def generate_reports(
        self,
        result: SuiteResult,
        formats: list[ReportFormat] = None
    ) -> dict[str, str]:
        """
        Genera reportes en multiples formatos.
        
        Returns:
            Dict de formato -> path del archivo generado
        """
        pass
    
    def generate_markdown_report(
        self,
        result: SuiteResult
    ) -> str:
        """Genera reporte en formato Markdown."""
        pass
    
    def generate_html_report(
        self,
        result: SuiteResult
    ) -> str:
        """Genera reporte HTML con visualizacion."""
        pass
```

### 5.2 Plantilla de Reporte Markdown

```markdown
# Reporte de Testing - Migracion Oracle a PostgreSQL

**Suite:** {{suite_name}}
**Fecha:** {{execution_date}}
**Ambiente:** {{environment}}
**Ejecutado por:** {{executed_by}}

---

## Resumen Ejecutivo

| Metrica | Valor |
|---------|-------|
| Total Tests | {{total_tests}} |
| Exitosos | {{passed}} ({{pass_rate}}%) |
| Fallidos | {{failed}} |
| Errores | {{errors}} |
| Omitidos | {{skipped}} |
| Duracion | {{duration}} |

### Indicador de Salud

{{#if pass_rate >= 95}}
**VERDE** - La migracion cumple con los criterios de aceptacion
{{else if pass_rate >= 90}}
**AMARILLO** - La migracion requiere atencion en algunos objetos
{{else}}
**ROJO** - La migracion tiene problemas criticos que resolver
{{/if}}

---

## Tests Fallidos (Accion Requerida)

{{#each failed_tests}}
### {{test_name}}

**Archivo:** `{{test_file}}`
**Duracion:** {{duration_ms}}ms

**Error:**
```
{{message}}
```

**Stack Trace:**
```
{{stack_trace}}
```

{{#if oracle_result}}
**Resultado Oracle:**
```json
{{oracle_result}}
```
{{/if}}

{{#if pg_result}}
**Resultado PostgreSQL:**
```json
{{pg_result}}
```
{{/if}}

{{#if comparison}}
**Diferencias:**
```json
{{comparison}}
```
{{/if}}

---
{{/each}}

## Tests Exitosos

| Test | Duracion | Oracle (ms) | PG (ms) |
|------|----------|-------------|---------|
{{#each passed_tests}}
| {{test_name}} | {{duration_ms}}ms | {{oracle_duration}} | {{pg_duration}} |
{{/each}}

---

## Cobertura por Tipo de Objeto

| Tipo | Total | Testeados | Cobertura |
|------|-------|-----------|-----------|
{{#each coverage_by_type}}
| {{type}} | {{total}} | {{tested}} | {{percentage}}% |
{{/each}}

---

## Metricas de Performance

### Comparacion Oracle vs PostgreSQL

| Objeto | Oracle (ms) | PG (ms) | Diferencia |
|--------|-------------|---------|------------|
{{#each performance_comparison}}
| {{object_name}} | {{oracle_ms}} | {{pg_ms}} | {{diff_ms}} ({{diff_percent}}%) |
{{/each}}

---

## Proximos Pasos

1. [ ] Resolver tests fallidos de severidad CRITICA
2. [ ] Revisar objetos con diferencia de performance >50%
3. [ ] Completar cobertura de objetos COMPLEX
4. [ ] Re-ejecutar suite de regresion

---

**Generado automaticamente por MigrationTestRunner v1.0**
```

### 5.3 Integracion CI/CD

```yaml
# Especificacion: .github/workflows/migration-tests.yml

name: Migration Tests

on:
  push:
    branches: [main, develop]
    paths:
      - 'sql/**'
      - 'src/**'
      - 'tests/**'
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      test_suite:
        description: 'Test suite to run'
        required: false
        default: 'all'
        type: choice
        options:
          - all
          - unit
          - integration
          - shadow
          - regression

env:
  PYTHON_VERSION: '3.11'
  PG_VERSION: '17'

jobs:
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: migration_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.7.1
      
      - name: Install dependencies
        run: poetry install --with dev
      
      - name: Install PostgreSQL extensions
        run: |
          PGPASSWORD=test psql -h localhost -U test -d migration_test -c "CREATE EXTENSION IF NOT EXISTS dblink;"
          PGPASSWORD=test psql -h localhost -U test -d migration_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
      
      - name: Run unit tests
        run: |
          poetry run pytest tests/unit/ \
            --junitxml=reports/unit-tests.xml \
            --cov=src \
            --cov-report=xml:reports/coverage.xml \
            --cov-report=html:reports/coverage-html \
            -v
      
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: unit-test-results
          path: reports/

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.event_name == 'push' || github.event.inputs.test_suite == 'integration' || github.event.inputs.test_suite == 'all'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
      
      - name: Install dependencies
        run: poetry install --with dev
      
      - name: Run integration tests
        env:
          PG_TEST_DSN: ${{ secrets.AURORA_TEST_DSN }}
          LAMBDA_HTTP_ARN: ${{ secrets.LAMBDA_HTTP_ARN }}
          S3_TEST_BUCKET: ${{ secrets.S3_TEST_BUCKET }}
        run: |
          poetry run pytest tests/integration/ \
            -m integration \
            --junitxml=reports/integration-tests.xml \
            -v
      
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: integration-test-results
          path: reports/

  shadow-tests:
    name: Shadow Tests (Oracle vs PostgreSQL)
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main' || github.event.inputs.test_suite == 'shadow'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Poetry and dependencies
        run: |
          pip install poetry
          poetry install --with dev
      
      - name: Run shadow tests
        env:
          ORACLE_TEST_DSN: ${{ secrets.ORACLE_TEST_DSN }}
          PG_TEST_DSN: ${{ secrets.AURORA_TEST_DSN }}
        run: |
          poetry run python -m src.testing.test_runner \
            --suite shadow \
            --report-format markdown \
            --report-format html \
            --output-dir reports/shadow/
      
      - name: Upload shadow test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: shadow-test-results
          path: reports/shadow/
      
      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('reports/shadow/report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });

  test-summary:
    name: Test Summary
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests, shadow-tests]
    if: always()
    
    steps:
      - name: Download all test results
        uses: actions/download-artifact@v4
        with:
          path: all-results
      
      - name: Publish Test Summary
        uses: EnricoMi/publish-unit-test-result-action@v2
        with:
          files: |
            all-results/**/*.xml
```

---

## 6. Estructura de Archivos de Tests

```
proyecto/
+-- tests/
|   +-- conftest.py                      # Configuracion global pytest
|   +-- pytest.ini                       # Configuracion pytest
|   |
|   +-- unit/                            # Tests unitarios (70%)
|   |   +-- test_syntax_validator.py     # Tests del validador de sintaxis
|   |   +-- test_shadow_comparator.py    # Tests del comparador
|   |   +-- test_data_generator.py       # Tests del generador de datos
|   |   +-- test_validation_rules.py     # Tests de reglas de validacion
|   |   +-- agents/
|   |   |   +-- test_code_comprehension.py
|   |   |   +-- test_migration_strategist.py
|   |   +-- converters/
|   |       +-- test_type_converter.py
|   |       +-- test_function_converter.py
|   |
|   +-- integration/                     # Tests de integracion (25%)
|   |   +-- test_ora2pg_integration.py   # Tests con ora2pg
|   |   +-- test_knowledge_base.py       # Tests de pgvector
|   |   +-- test_checkpoint_system.py    # Tests del sistema de checkpoints
|   |   +-- test_lambda_http.py          # Tests de Lambda HTTP
|   |   +-- test_lambda_csv_xlsx.py      # Tests de Lambda CSV->XLSX
|   |
|   +-- complex/                         # Tests de objetos complejos
|   |   +-- test_autonomous_transaction.py
|   |   +-- test_utl_http_wrapper.py
|   |   +-- test_directory_s3.py
|   |   +-- test_package_variables.py
|   |   +-- test_dbms_scheduler.py
|   |
|   +-- shadow/                          # Shadow tests (5%)
|   |   +-- test_shadow_functions.py
|   |   +-- test_shadow_procedures.py
|   |   +-- test_shadow_packages.py
|   |   +-- test_shadow_triggers.py
|   |
|   +-- regression/                      # Tests de regresion
|   |   +-- test_critical_objects.py     # Objetos criticos (FAC_*, RHH_*)
|   |   +-- test_high_volume_tables.py   # Tablas con >100M filas
|   |   +-- test_complex_packages.py     # Packages >10k lineas
|   |
|   +-- fixtures/                        # Datos de prueba
|   |   +-- migration_fixtures.py        # Fixtures Python
|   |   +-- sample_data/
|   |   |   +-- clientes.json
|   |   |   +-- ordenes.json
|   |   |   +-- facturas.json
|   |   +-- oracle_responses/
|   |   |   +-- pkg_ventas_calcular_descuento.json
|   |   |   +-- ...
|   |   +-- expected_pg/
|   |       +-- pkg_ventas_calcular_descuento.json
|   |       +-- ...
|   |
|   +-- sql/                             # Scripts SQL de prueba
|       +-- shadow_testing_schema.sql
|       +-- test_data_setup.sql
|       +-- test_data_cleanup.sql
|
+-- src/
|   +-- testing/
|       +-- __init__.py
|       +-- shadow_comparator.py
|       +-- shadow_executor.py
|       +-- pg_syntax_validator.py
|       +-- pg_validation_rules.py
|       +-- test_data_generator.py
|       +-- test_runner.py
|
+-- reports/                             # Reportes generados
|   +-- unit/
|   +-- integration/
|   +-- shadow/
|   +-- coverage/
|
+-- .github/
    +-- workflows/
        +-- migration-tests.yml
```

---

## 7. Configuracion de Pytest

### 7.1 pytest.ini

```ini
# pytest.ini

[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (require database/AWS)
    shadow: Shadow tests (Oracle vs PostgreSQL comparison)
    slow: Slow tests (>10 seconds)
    critical: Critical path tests (must pass for deployment)
    regression: Regression tests for known bugs

# Async mode
asyncio_mode = auto

# Coverage
addopts = 
    --strict-markers
    -ra
    --tb=short

# Logging
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)s] %(message)s
log_cli_date_format = %H:%M:%S

# Timeout
timeout = 60
timeout_method = thread

# Filtering
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### 7.2 conftest.py Global

```python
# tests/conftest.py

"""
Configuracion global de pytest para tests de migracion.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator
from datetime import datetime


# ============================================================
# CONFIGURACION DE AMBIENTE
# ============================================================

def pytest_configure(config):
    """Configuracion inicial de pytest."""
    # Verificar variables de entorno requeridas
    required_env = []
    
    if config.option.markexpr and 'integration' in config.option.markexpr:
        required_env.extend(['PG_TEST_DSN'])
    
    if config.option.markexpr and 'shadow' in config.option.markexpr:
        required_env.extend(['ORACLE_TEST_DSN', 'PG_TEST_DSN'])
    
    missing = [env for env in required_env if not os.getenv(env)]
    if missing:
        pytest.exit(f"Missing required environment variables: {missing}")


# ============================================================
# FIXTURES GLOBALES
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def pg_test_dsn():
    """PostgreSQL test DSN."""
    return os.getenv("PG_TEST_DSN", "postgresql://test:test@localhost/migration_test")


@pytest.fixture(scope="session")
def oracle_test_dsn():
    """Oracle test DSN."""
    return os.getenv("ORACLE_TEST_DSN")


@pytest.fixture(scope="session")
async def pg_connection_pool(pg_test_dsn):
    """Connection pool para PostgreSQL."""
    import asyncpg
    
    pool = await asyncpg.create_pool(
        pg_test_dsn,
        min_size=2,
        max_size=10
    )
    yield pool
    await pool.close()


@pytest.fixture
async def pg_connection(pg_connection_pool) -> AsyncGenerator:
    """Conexion individual de PostgreSQL."""
    async with pg_connection_pool.acquire() as conn:
        yield conn


@pytest.fixture
async def pg_transaction(pg_connection) -> AsyncGenerator:
    """Transaccion con rollback automatico."""
    tr = pg_connection.transaction()
    await tr.start()
    yield pg_connection
    await tr.rollback()


# ============================================================
# FIXTURES DE TESTING
# ============================================================

@pytest.fixture
def shadow_comparator():
    """Instancia de ShadowComparator."""
    from src.testing.shadow_comparator import ShadowComparator, ComparisonConfig
    return ShadowComparator(ComparisonConfig())


@pytest.fixture
def syntax_validator(pg_connection):
    """Instancia de PgSyntaxValidator."""
    from src.testing.pg_syntax_validator import PgSyntaxValidator
    return PgSyntaxValidator(pg_connection)


@pytest.fixture
def test_data_generator():
    """Instancia de TestDataGenerator."""
    from src.testing.test_data_generator import TestDataGenerator, DataGenerationConfig
    return TestDataGenerator(DataGenerationConfig(random_seed=42))


# ============================================================
# HOOKS
# ============================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    # Skip integration tests if no DSN configured
    if not os.getenv("PG_TEST_DSN"):
        skip_integration = pytest.mark.skip(reason="PG_TEST_DSN not configured")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
    
    # Skip shadow tests if no Oracle DSN
    if not os.getenv("ORACLE_TEST_DSN"):
        skip_shadow = pytest.mark.skip(reason="ORACLE_TEST_DSN not configured")
        for item in items:
            if "shadow" in item.keywords:
                item.add_marker(skip_shadow)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Custom summary at end of test run."""
    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    errors = len(terminalreporter.stats.get('error', []))
    total = passed + failed + errors
    
    if total > 0:
        pass_rate = (passed / total) * 100
        terminalreporter.write_sep("=", "Migration Test Summary")
        terminalreporter.write_line(f"Pass Rate: {pass_rate:.1f}%")
        terminalreporter.write_line(f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
        
        if pass_rate >= 95:
            terminalreporter.write_line("Status: GREEN - Ready for deployment")
        elif pass_rate >= 90:
            terminalreporter.write_line("Status: YELLOW - Review required")
        else:
            terminalreporter.write_line("Status: RED - Critical issues detected")
```

---

## 8. Cronograma de Implementacion de Tests

| Semana | Componente | Entregable | Dependencias |
|--------|------------|------------|--------------|
| 1 | Framework Shadow Testing | Schema + Comparador + Executor | PostgreSQL local |
| 1 | Validador de Sintaxis | Validator + Rules base | - |
| 2 | Tests Unitarios Base | 50+ tests unitarios | Framework Shadow |
| 2 | Fixtures y Datos | Generador + Fixtures predefinidos | - |
| 3 | Tests Complejos | AUTONOMOUS, UTL_HTTP, DIRECTORY | Lambda deployed |
| 3 | Tests de Integracion | 30+ tests integracion | Aurora dev |
| 4 | Shadow Tests Criticos | 100+ shadow tests objetos criticos | Oracle + Aurora |
| 4 | Automatizacion CI/CD | GitHub Actions workflow | Todo lo anterior |
| 5 | Tests de Regresion | Suite completa de regresion | Suite shadow |
| 5 | Reportes y Dashboards | Templates + generacion automatica | Test runner |

---

## 9. Metricas de Exito Detalladas

### 9.1 Criterios de Aceptacion

| Criterio | Umbral Minimo | Objetivo | Critico |
|----------|---------------|----------|---------|
| **Pass Rate Global** | 90% | 95% | Si |
| **Pass Rate SIMPLE objects** | 95% | 99% | Si |
| **Pass Rate COMPLEX objects** | 85% | 95% | Si |
| **Shadow Match Rate** | 95% | 99% | Si |
| **Cobertura Codigo Critico** | 80% | 90% | Si |
| **Tiempo Ejecucion Suite** | 60 min | 30 min | No |
| **Errores Sintaxis Post-Migration** | 0 | 0 | Si |
| **Regresiones Detectadas** | <5 | 0 | Si |

### 9.2 Objetos Criticos (Prioridad 1)

Los siguientes objetos DEBEN tener cobertura 100%:

**Packages de Facturacion (FAC_*):**
- FAC_K_EGRESO_X_FACT (41,732 lineas)
- FAC_K_TRX (14,938 lineas)
- FAC_K_GUIAS_DESPACHO (18,098 lineas)

**Packages de Pagos (DIG_*):**
- DIG_K_PAGO (35,498 lineas)
- DIG_K_PAGO_2 (30,350 lineas)

**Packages de Nomina (RHH_*):**
- RHH_K_NOMINA (20,430 lineas)
- RHH_K_IMPUESTO_RENTA (16,708 lineas)

**Procedures Criticos:**
- FAC_P_FACTURA_RESERVA (1,525 lineas)
- FAC_P_FACTURACION_M (1,302 lineas)
- RHH_P_MAIL_ROL_ELECTRONICO (712 lineas)

---

## 10. Referencias

### Documentacion Oficial
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [PostgreSQL 17 Documentation](https://www.postgresql.org/docs/17/)
- [Aurora PostgreSQL Testing Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.BestPractices.html)

### Herramientas de Testing
- [pgTAP - Unit testing for PostgreSQL](https://pgtap.org/)
- [Moto - Mock AWS Services](https://github.com/getmoto/moto)
- [Faker - Generate fake data](https://faker.readthedocs.io/)

### Shadow Testing
- [Shadow Testing Best Practices](https://martinfowler.com/bliki/ShadowTraffic.html)
- [Database Migration Testing Strategies](https://www.thoughtworks.com/insights/blog/database-migration-testing)

---

**Documento creado por:** backend-test-engineer (sub-agente)  
**Fecha:** 2025-12-30  
**Version:** 1.0  
**Estado:** ready-for-implementation

**Proxima accion:** Revisar plan con equipo y proceder a implementacion del framework de testing.
