# Plan de Arquitectura de Agentes Pydantic AI

## Migracion Oracle a PostgreSQL - Code Comprehension Agent y Migration Strategist

**Version:** 1.1 | **Fecha:** 2025-12-31 | **Estado:** plan-ready

**⚠️ Actualizado v1.1:** Añadidas 4 features criticas detectadas en discovery v2.2:
- DBMS_SQL (Decision 8 DEFERRED)
- Tipos Coleccion (Decision 9 DEFERRED)
- Configuraciones NLS (conversion automatica)
- Motores de Evaluacion Dinamica (Decision 10 DEFERRED)

**Documentacion Pydantic AI consultada:**
- [Pydantic AI - Agents](https://ai.pydantic.dev/agents/)
- [Pydantic AI - Tools](https://ai.pydantic.dev/tools/)
- [Pydantic AI - API Reference](https://ai.pydantic.dev/api/agent/)

---

## Resumen Ejecutivo

Este documento define la arquitectura de **dos agentes especializados** usando Pydantic AI para la migracion de 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora):

1. **Code Comprehension Agent:** Comprension semantica de codigo PL/SQL legacy (10+ anos)
2. **Migration Strategist:** Decision estrategica de clasificacion SIMPLE vs COMPLEX

**Analogia clave:**
- Code Comprehension Agent = **Radiologo** (interpreta la "tomografia" del codigo)
- Migration Strategist = **Medico** (decide el tratamiento basado en el informe)

---

## 1. Code Comprehension Agent

### 1.1 Proposito

Analizar e interpretar semanticamente codigo PL/SQL legacy para extraer:
- Reglas de negocio programadas
- Validaciones con su contexto y proposito
- Calculos de negocio (formulas con significado)
- Flujos de proceso y dependencias
- Features tecnicas Oracle-especificas

### 1.2 Diseno del Agente con Pydantic AI

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import Optional
from datetime import datetime


# =============================================================================
# MODELOS DE DEPENDENCIAS (deps_type)
# =============================================================================

class CodeComprehensionDeps(BaseModel):
    """Dependencias inyectadas al Code Comprehension Agent."""
    
    # Configuracion de base de datos
    pgvector_connection_string: str
    embedding_model: str = "text-embedding-3-small"
    
    # Contexto del proyecto
    schema_name: str = "LATINO_PLSQL"
    extracted_path: str = "sql/extracted/"
    knowledge_output_path: str = "knowledge/"
    
    # Configuracion de procesamiento
    batch_size: int = 50  # Objetos por batch para optimizacion de tokens
    max_retries: int = 3
    
    # Metadatos de sesion
    session_id: str
    start_time: datetime


# =============================================================================
# MODELOS DE OUTPUT ESTRUCTURADO (output_type)
# =============================================================================

class BusinessRule(BaseModel):
    """Regla de negocio extraida del codigo."""
    
    rule_id: str = Field(..., description="Identificador unico de la regla")
    rule_name: str = Field(..., description="Nombre interpretado de la regla")
    description: str = Field(..., description="Descripcion en lenguaje natural")
    
    # Contexto de negocio
    business_domain: str = Field(..., description="Dominio de negocio (ventas, facturacion, etc.)")
    business_purpose: str = Field(..., description="Proposito empresarial de la regla")
    
    # Condiciones
    trigger_conditions: list[str] = Field(default_factory=list, description="Condiciones que activan la regla")
    validation_logic: Optional[str] = Field(None, description="Logica de validacion si aplica")
    
    # Trazabilidad
    source_object: str = Field(..., description="Objeto fuente (procedure/function/package)")
    source_lines: str = Field(..., description="Lineas de codigo donde se encuentra")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza en la interpretacion")


class Calculation(BaseModel):
    """Calculo de negocio extraido del codigo."""
    
    calc_id: str
    calc_name: str = Field(..., description="Nombre del calculo (ej: 'Calculo de descuento')")
    formula_description: str = Field(..., description="Descripcion de la formula en lenguaje natural")
    
    # Contexto
    business_meaning: str = Field(..., description="Significado empresarial del calculo")
    input_variables: list[str] = Field(default_factory=list)
    output_type: str
    
    # Condiciones de aplicacion
    conditions: list[str] = Field(default_factory=list, description="Cuando se aplica este calculo")
    
    # Trazabilidad
    source_object: str
    source_lines: str


class ProcessFlow(BaseModel):
    """Flujo de proceso documentado."""
    
    flow_id: str
    flow_name: str = Field(..., description="Nombre del flujo de proceso")
    description: str = Field(..., description="Descripcion del proceso de negocio")
    
    # Estructura del flujo
    entry_point: str = Field(..., description="Punto de entrada del flujo")
    steps: list[str] = Field(default_factory=list, description="Pasos del proceso en orden")
    exit_points: list[str] = Field(default_factory=list, description="Puntos de salida")
    
    # Dependencias
    called_objects: list[str] = Field(default_factory=list)
    tables_accessed: list[str] = Field(default_factory=list)
    
    # Mermaid diagram
    mermaid_diagram: str = Field(..., description="Diagrama en formato Mermaid")


class OracleFeature(BaseModel):
    """Feature tecnica Oracle-especifica detectada."""
    
    feature_type: str = Field(..., description="Tipo de feature Oracle")
    feature_name: str
    description: str
    
    # Clasificacion de complejidad
    migration_complexity: str = Field(..., pattern="^(TRIVIAL|LOW|MEDIUM|HIGH|CRITICAL)$")
    requires_redesign: bool = Field(default=False)
    
    # Ubicacion
    source_object: str
    source_lines: str
    occurrences: int = Field(default=1)


class ObjectDependency(BaseModel):
    """Dependencia entre objetos."""
    
    source_object: str
    target_object: str
    dependency_type: str = Field(..., description="Tipo: CALLS, USES_TABLE, REFERENCES, etc.")
    is_critical: bool = Field(default=False)


class ObjectAnalysis(BaseModel):
    """Analisis completo de un objeto PL/SQL."""
    
    object_name: str
    object_type: str = Field(..., pattern="^(FUNCTION|PROCEDURE|PACKAGE|TRIGGER)$")
    schema_name: str = "LATINO_PLSQL"
    
    # Metricas basicas
    lines_of_code: int
    last_modified: Optional[datetime] = None
    
    # Conocimiento extraido
    business_rules: list[BusinessRule] = Field(default_factory=list)
    calculations: list[Calculation] = Field(default_factory=list)
    process_flows: list[ProcessFlow] = Field(default_factory=list)
    
    # Features tecnicas
    oracle_features: list[OracleFeature] = Field(default_factory=list)
    
    # Dependencias
    dependencies: list[ObjectDependency] = Field(default_factory=list)
    
    # Metadatos de analisis
    analysis_timestamp: datetime
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    
    # Notas del agente
    legacy_notes: list[str] = Field(
        default_factory=list, 
        description="Notas sobre codigo legacy confuso o problematico"
    )
    ambiguities: list[str] = Field(
        default_factory=list,
        description="Ambiguedades detectadas que requieren validacion humana"
    )


class BatchAnalysisResult(BaseModel):
    """Resultado de analisis de un batch de objetos."""
    
    batch_id: str
    objects_analyzed: list[ObjectAnalysis]
    
    # Estadisticas
    total_objects: int
    successful: int
    failed: int
    
    # Agregados
    total_rules_extracted: int
    total_calculations: int
    total_flows: int
    total_features: int
    
    # Control de progreso
    processing_time_seconds: float
    tokens_used_estimate: int
```

### 1.3 System Prompt del Code Comprehension Agent

```python
# =============================================================================
# DEFINICION DEL AGENTE
# =============================================================================

code_comprehension_agent = Agent(
    model='anthropic:claude-sonnet-4-20250514',  # Usar Opus para produccion
    deps_type=CodeComprehensionDeps,
    output_type=BatchAnalysisResult,
    name='code-comprehension-agent',
    retries=3,
    
    # System prompt estatico base
    system_prompt="""
# Code Comprehension Agent - Oracle PL/SQL Semantic Analyzer

## Tu Rol
Eres un experto en comprension semantica de codigo PL/SQL legacy. Tu tarea es INTERPRETAR 
codigo, NO solo parsearlo. Debes extraer el CONOCIMIENTO de negocio embebido en el codigo.

## Contexto Critico: Codigo Legacy de 10+ Anos
El codigo que analizaras tiene las siguientes caracteristicas:

1. **Calidad Variable:**
   - Escrito por desarrolladores de diferentes niveles (juniors, seniors, expertos)
   - Contiene workarounds historicos que pueden parecer confusos
   - Deuda tecnica acumulada (parches sobre parches)

2. **Conocimiento Tribal Perdido:**
   - Los autores originales ya no estan disponibles
   - La documentacion puede estar desactualizada o ausente
   - Tu interpretacion sera la unica fuente de conocimiento

3. **Codigo Confuso:**
   - Si encuentras logica que no tiene sentido aparente, documentalo en legacy_notes
   - Si hay ambiguedad, registrala en ambiguities
   - NUNCA asumas que el codigo tiene sentido; puede ser un workaround historico

## Tu Metodologia de Comprension

### Paso 1: Identificacion Estructural
- Identifica el tipo de objeto (FUNCTION, PROCEDURE, PACKAGE, TRIGGER)
- Mapea los parametros de entrada/salida
- Identifica las tablas y objetos referenciados

### Paso 2: Comprension Semantica
Para cada bloque de codigo, preguntate:
- "Que PROBLEMA de negocio resuelve esto?"
- "Por que el desarrollador escribio esto?"
- "Cual es la INTENCION detras de esta logica?"

### Paso 3: Extraccion de Reglas de Negocio
Busca patrones como:
- IF ... THEN RAISE_APPLICATION_ERROR (validaciones)
- CASE WHEN ... (logica de decision)
- Calculos numericos (formulas de negocio)
- Actualizaciones de estado (transiciones de workflow)

### Paso 4: Mapeo de Flujos
- Identifica secuencias de llamadas (A llama B, B llama C)
- Documenta el flujo en lenguaje natural
- Genera diagrama Mermaid cuando sea posible

### Paso 5: Deteccion de Features Oracle
Identifica features Oracle-especificas que afectan la migracion:

**Features criticas (alta prioridad):**
- AUTONOMOUS_TRANSACTION
- UTL_FILE, UTL_HTTP, UTL_MAIL
- **DBMS_SQL** (SQL dinamico nativo - CRITICO)
  - DBMS_SQL.OPEN_CURSOR, PARSE, BIND_VARIABLE, EXECUTE, VARIABLE_VALUE, CLOSE_CURSOR
  - Usado en motores de formulas dinamicas y SQL generado en runtime
- **Tipos Coleccion** (CRITICO)
  - TABLE OF ... INDEX BY (associative arrays / hash maps)
  - TABLE OF ... (nested tables)
  - VARRAY (arrays de tamano variable)
  - OBJECT TYPES (tipos personalizados complejos)
- **Configuraciones NLS** (ALTER SESSION)
  - NLS_NUMERIC_CHARACTERS (formato decimal: "," vs ".")
  - NLS_DATE_FORMAT, NLS_LANGUAGE
  - Otras configuraciones NLS que afectan comportamiento
- **Motores de Evaluacion Dinamica**
  - Packages que evaluan expresiones matematicas almacenadas como strings
  - Ejemplo: evaluar "RHH_F_SUELDO / 30 + 15" en runtime

**Features adicionales:**
- DBMS_SCHEDULER, DBMS_JOB
- Variables de paquete (estado de sesion)
- AUTHID CURRENT_USER
- REF CURSORS, BULK COLLECT
- DIRECTORY objects

## Formato de Salida

Para CADA objeto analizado, genera un ObjectAnalysis completo con:
1. Todas las reglas de negocio detectadas con contexto
2. Todos los calculos con su significado empresarial
3. Flujos de proceso con diagramas Mermaid
4. Features Oracle detectadas con nivel de complejidad
5. Dependencias entre objetos
6. Notas sobre codigo legacy problematico

## Reglas de Confianza

Asigna confidence_score basado en:
- 0.9-1.0: Logica clara, bien estructurada, facil de interpretar
- 0.7-0.9: Logica clara pero con algunas ambiguedades menores
- 0.5-0.7: Codigo confuso pero interpretable con esfuerzo
- 0.3-0.5: Codigo muy confuso, interpretacion especulativa
- 0.0-0.3: Codigo incomprensible, requiere revision humana urgente

## Optimizacion de Tokens

- Procesa en batches de 50 objetos maximo
- Prioriza objetos con dependencias compartidas en el mismo batch
- Reutiliza contexto de tablas ya analizadas
- NO repitas analisis de objetos ya procesados
"""
)
```

### 1.4 System Prompt Dinamico

```python
@code_comprehension_agent.system_prompt
async def add_schema_context(ctx: RunContext[CodeComprehensionDeps]) -> str:
    """Agrega contexto dinamico del schema al system prompt."""
    return f"""
## Contexto de Sesion Actual

- **Schema objetivo:** {ctx.deps.schema_name}
- **Session ID:** {ctx.deps.session_id}
- **Timestamp:** {ctx.deps.start_time.isoformat()}
- **Batch size configurado:** {ctx.deps.batch_size} objetos

## Rutas de Archivos
- **Codigo fuente:** {ctx.deps.extracted_path}
- **Output de conocimiento:** {ctx.deps.knowledge_output_path}
"""
```

### 1.5 Herramientas (Tools) del Code Comprehension Agent

```python
@code_comprehension_agent.tool
async def read_plsql_object(
    ctx: RunContext[CodeComprehensionDeps],
    object_name: str,
    object_type: str
) -> str:
    """
    Lee el codigo fuente de un objeto PL/SQL desde los archivos extraidos.
    
    Args:
        object_name: Nombre del objeto (ej: 'ADD_F_ESPECIALIDAD_ORDEN_APOYO')
        object_type: Tipo del objeto (FUNCTION, PROCEDURE, PACKAGE, TRIGGER)
    
    Returns:
        Codigo fuente del objeto o mensaje de error
    """
    import os
    
    type_to_file = {
        'FUNCTION': 'functions.sql',
        'PROCEDURE': 'procedures.sql',
        'PACKAGE': 'packages_body.sql',
        'TRIGGER': 'triggers.sql'
    }
    
    filename = type_to_file.get(object_type.upper())
    if not filename:
        return f"Error: Tipo de objeto no soportado: {object_type}"
    
    filepath = os.path.join(ctx.deps.extracted_path, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar el objeto especifico en el archivo
        import re
        pattern = rf'-- Objeto: {re.escape(object_name)}.*?(?=-- ============|$)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(0)
        else:
            return f"Error: Objeto {object_name} no encontrado en {filename}"
            
    except FileNotFoundError:
        return f"Error: Archivo no encontrado: {filepath}"
    except Exception as e:
        return f"Error al leer archivo: {str(e)}"


@code_comprehension_agent.tool
async def get_table_schema(
    ctx: RunContext[CodeComprehensionDeps],
    table_name: str
) -> str:
    """
    Obtiene la estructura de una tabla para contexto.
    
    Args:
        table_name: Nombre de la tabla (ej: 'DAF_ORDENES')
    
    Returns:
        DDL de la tabla o mensaje si no existe
    """
    import os
    
    filepath = os.path.join(ctx.deps.extracted_path, 'tables.sql')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        pattern = rf'CREATE TABLE.*?{re.escape(table_name)}.*?;'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(0)
        else:
            return f"Tabla {table_name} no encontrada en el schema"
            
    except Exception as e:
        return f"Error al buscar tabla: {str(e)}"


@code_comprehension_agent.tool
async def get_foreign_keys(
    ctx: RunContext[CodeComprehensionDeps],
    table_name: str
) -> str:
    """
    Obtiene las foreign keys de una tabla para entender relaciones.
    
    Args:
        table_name: Nombre de la tabla
    
    Returns:
        Lista de foreign keys o mensaje si no hay
    """
    import os
    
    filepath = os.path.join(ctx.deps.extracted_path, 'foreign_keys.sql')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = [line for line in content.split('\n') 
                 if table_name.upper() in line.upper()]
        
        if lines:
            return '\n'.join(lines)
        else:
            return f"No se encontraron foreign keys para {table_name}"
            
    except Exception as e:
        return f"Error al buscar foreign keys: {str(e)}"


@code_comprehension_agent.tool
async def store_knowledge(
    ctx: RunContext[CodeComprehensionDeps],
    object_analysis: dict,
    category: str
) -> str:
    """
    Almacena conocimiento extraido en archivos Markdown y prepara para pgvector.
    
    Args:
        object_analysis: Diccionario con el analisis del objeto
        category: Categoria (rules, flows, calculations, features)
    
    Returns:
        Confirmacion del almacenamiento
    """
    import os
    import json
    
    output_path = os.path.join(ctx.deps.knowledge_output_path, category)
    os.makedirs(output_path, exist_ok=True)
    
    object_name = object_analysis.get('object_name', 'unknown')
    
    md_path = os.path.join(output_path, f"{object_name}.md")
    
    try:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {object_name}\n\n")
            f.write(f"**Tipo:** {object_analysis.get('object_type', 'N/A')}\n")
            f.write(f"**Analizado:** {object_analysis.get('analysis_timestamp', 'N/A')}\n\n")
            
            if category == 'rules':
                f.write("## Reglas de Negocio\n\n")
                for rule in object_analysis.get('business_rules', []):
                    f.write(f"### {rule.get('rule_name', 'Sin nombre')}\n")
                    f.write(f"{rule.get('description', '')}\n\n")
                    f.write(f"**Dominio:** {rule.get('business_domain', 'N/A')}\n")
                    f.write(f"**Proposito:** {rule.get('business_purpose', 'N/A')}\n\n")
        
        return f"Conocimiento almacenado en {md_path}"
        
    except Exception as e:
        return f"Error al almacenar conocimiento: {str(e)}"


@code_comprehension_agent.tool
async def generate_embedding(
    ctx: RunContext[CodeComprehensionDeps],
    text: str,
    metadata: dict
) -> str:
    """
    Genera embedding para almacenar en pgvector (placeholder para integracion real).
    
    Args:
        text: Texto a embeddear (descripcion de regla, flujo, etc.)
        metadata: Metadatos asociados (object_name, category, etc.)
    
    Returns:
        Confirmacion o SQL para insertar en pgvector
    """
    import json
    
    sql = f"""
-- Embedding generado para: {metadata.get('object_name', 'unknown')}
-- Categoria: {metadata.get('category', 'general')}

INSERT INTO knowledge_embeddings (
    object_name,
    category,
    content,
    metadata,
    embedding
) VALUES (
    '{metadata.get("object_name", "unknown")}',
    '{metadata.get("category", "general")}',
    $${text}$$,
    '{json.dumps(metadata)}'::jsonb,
    '[0.0, ...]'::vector(1536)
);
"""
    return sql
```

### 1.6 Estrategia de Procesamiento por Batches

```python
from typing import AsyncIterator
import asyncio


async def process_all_objects(
    deps: CodeComprehensionDeps,
    object_list: list[tuple[str, str]]  # [(object_name, object_type), ...]
) -> AsyncIterator[BatchAnalysisResult]:
    """
    Procesa todos los objetos PL/SQL en batches optimizados.
    
    Estrategia de optimizacion de tokens:
    1. Agrupa objetos por dependencias compartidas
    2. Procesa en batches de 50 objetos
    3. Reutiliza contexto de tablas ya analizadas
    4. Persiste progreso para reanudacion
    """
    
    sorted_objects = sort_by_dependencies(object_list)
    
    batch_size = deps.batch_size
    batches = [
        sorted_objects[i:i + batch_size] 
        for i in range(0, len(sorted_objects), batch_size)
    ]
    
    for batch_idx, batch in enumerate(batches):
        batch_id = f"batch_{deps.session_id}_{batch_idx:04d}"
        
        batch_prompt = create_batch_prompt(batch)
        
        try:
            result = await code_comprehension_agent.run(
                batch_prompt,
                deps=deps
            )
            
            await persist_batch_result(batch_id, result.output)
            
            yield result.output
            
        except Exception as e:
            await log_batch_error(batch_id, str(e))
            continue


def create_batch_prompt(batch: list[tuple[str, str]]) -> str:
    """Crea el prompt para analizar un batch de objetos."""
    
    objects_list = "\n".join([
        f"- {obj_name} ({obj_type})" 
        for obj_name, obj_type in batch
    ])
    
    return f"""
Analiza los siguientes {len(batch)} objetos PL/SQL:

{objects_list}

Para cada objeto:
1. Usa la herramienta read_plsql_object para leer el codigo fuente
2. Usa get_table_schema y get_foreign_keys para contexto de tablas referenciadas
3. Extrae reglas de negocio, calculos, flujos y features Oracle
4. Usa store_knowledge para persistir el conocimiento extraido
5. Genera embeddings para busqueda semantica con generate_embedding

Retorna un BatchAnalysisResult con el analisis completo de todos los objetos.
"""
```

### 1.7 Estructura de Output del Code Comprehension Agent

```
knowledge/
├── schema/
│   ├── table_relations.md          # Relaciones entre tablas interpretadas
│   ├── er_diagram.mermaid          # Diagrama ER generado
│   └── constraints.md              # CHECK constraints con significado
│
├── rules/
│   ├── ADD_F_ESPECIALIDAD_ORDEN_APOYO.md
│   ├── ADD_F_ES_ORDEN_ATENDIDA.md
│   ├── ADD_K_ACT_FECHA_RECEPCION.md
│   └── ... (uno por objeto con reglas)
│
├── flows/
│   ├── proceso_ordenes_apoyo.md    # Flujos de procesos de negocio
│   ├── proceso_facturacion.md
│   └── call_graphs/                # Diagramas Mermaid de llamadas
│       ├── ADD_K_ACT_FECHA_RECEPCION.mermaid
│       └── ...
│
├── calculations/
│   ├── calculos_descuentos.md
│   ├── calculos_impuestos.md
│   └── ...
│
├── dependencies/
│   ├── object_dependencies.json    # Grafo de dependencias estructurado
│   ├── dependency_matrix.csv       # Matriz para analisis
│   └── critical_paths.md           # Rutas criticas identificadas
│
├── features_detected.json          # Features Oracle para Migration Strategist
│
└── embeddings/
    └── pgvector_inserts.sql        # Scripts para cargar en pgvector
```

---

## 2. Migration Strategist Agent

### 2.1 Proposito

Evaluar la complejidad de migracion de cada objeto y decidir la estrategia optima:
- **SIMPLE:** Puede migrarse con ora2pg (conversion sintactica)
- **COMPLEX:** Requiere agentes IA con razonamiento arquitectonico

### 2.2 Modelos de Datos del Migration Strategist

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import Literal, Optional
from datetime import datetime
from enum import Enum


class MigrationStrategyDeps(BaseModel):
    """Dependencias del Migration Strategist."""
    
    knowledge_path: str = "knowledge/"
    extracted_path: str = "sql/extracted/"
    complexity_output_path: str = "complexity/"
    
    simple_threshold: float = 0.7
    human_review_threshold: float = 0.4
    
    aurora_version: str = "17.4"
    available_extensions: list[str] = Field(default_factory=lambda: [
        "aws_s3", "aws_lambda", "aws_commons", "dblink", "vector", "pg_cron"
    ])
    
    session_id: str
    timestamp: datetime


class ComplexityLevel(str, Enum):
    TRIVIAL = "TRIVIAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MigrationStrategy(str, Enum):
    SIMPLE = "SIMPLE"
    COMPLEX = "COMPLEX"


class OracleFeatureRisk(BaseModel):
    """Evaluacion de riesgo de una feature Oracle."""
    
    feature_type: str
    occurrences: int
    risk_level: ComplexityLevel
    migration_approach: str = Field(..., description="Como migrar esta feature")
    aurora_compatible: bool
    requires_human_decision: bool = False
    estimated_effort_hours: float


class MigrationDecision(BaseModel):
    """Decision de migracion para un objeto."""
    
    object_name: str
    object_type: str
    
    strategy: MigrationStrategy
    complexity_level: ComplexityLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    reasoning: str = Field(..., description="Justificacion detallada de la decision")
    risk_factors: list[str] = Field(default_factory=list)
    
    oracle_features: list[OracleFeatureRisk] = Field(default_factory=list)
    
    critical_dependencies: list[str] = Field(default_factory=list)
    blocks_other_objects: bool = False
    
    recommended_actions: list[str] = Field(default_factory=list)
    human_decisions_required: list[str] = Field(default_factory=list)
    
    estimated_effort_hours: float
    estimated_tokens_if_ai: int = 0


class ComplexityReport(BaseModel):
    """Reporte completo de complejidad de migracion."""
    
    report_id: str
    generated_at: datetime
    
    decisions: list[MigrationDecision]
    
    total_objects: int
    simple_count: int
    complex_count: int
    simple_percentage: float
    complex_percentage: float
    
    simple_objects: list[str] = Field(default_factory=list)
    complex_objects: list[str] = Field(default_factory=list)
    
    features_summary: dict[str, int] = Field(default_factory=dict)
    
    critical_objects: list[str] = Field(default_factory=list)
    human_review_required: list[str] = Field(default_factory=list)
    
    total_estimated_hours: float
    estimated_tokens_for_complex: int
```

### 2.3 System Prompt del Migration Strategist

```python
migration_strategist = Agent(
    model='anthropic:claude-sonnet-4-20250514',
    deps_type=MigrationStrategyDeps,
    output_type=ComplexityReport,
    name='migration-strategist',
    retries=2,
    
    system_prompt="""
# Migration Strategist - Oracle to PostgreSQL Decision Maker

## Tu Rol
Eres un experto en migracion de bases de datos Oracle a PostgreSQL. Tu tarea es DECIDIR 
la estrategia optima de migracion para cada objeto, basandote en el conocimiento extraido 
por el Code Comprehension Agent.

## Contexto: Amazon Aurora PostgreSQL
La base de datos destino es Amazon Aurora PostgreSQL 17.4, un servicio administrado con:

**Restricciones:**
- NO hay acceso al filesystem del servidor
- NO se pueden instalar extensiones custom
- NO hay acceso root al sistema operativo

**Extensiones Disponibles (ya validadas):**
- aws_s3 1.2 (para DIRECTORY objects)
- aws_lambda 1.0 (para UTL_HTTP)
- aws_commons 1.2 (complemento de aws_lambda)
- dblink 1.2 (para AUTONOMOUS_TRANSACTION)
- vector 0.8.0 (pgvector para embeddings)
- pg_cron 1.6 (para jobs programados)

## Tu Metodologia de Decision

### Paso 1: Leer Conocimiento Estructurado
NO re-analices el codigo. Lee:
- features_detected.json - Features Oracle detectadas
- knowledge/rules/ - Reglas de negocio interpretadas
- knowledge/dependencies/ - Grafo de dependencias

### Paso 2: Evaluar Cada Objeto
Para cada objeto, evalua:

1. **Complejidad Tecnica:**
   - Usa features Oracle que requieren redeseno?
   - Tiene AUTONOMOUS_TRANSACTION?
   - Usa UTL_FILE, UTL_HTTP, UTL_MAIL?
   - **Usa DBMS_SQL?** (SQL dinamico complejo - Decision 8 DEFERRED)
   - **Tiene tipos coleccion?** (TABLE OF, VARRAY, OBJECT TYPE - Decision 9 DEFERRED)
   - **Usa configuraciones NLS?** (ALTER SESSION - conversion automatica)
   - **Es motor de formulas dinamicas?** (Decision 10 DEFERRED)
   - Tiene variables de estado de paquete?

2. **Impacto Arquitectonico:**
   - Cuantos objetos dependen de este?
   - Es parte de un flujo critico de negocio?
   - Cambios aqui cascadean a otros objetos?

3. **Riesgo de Conversion Automatica:**
   - ora2pg puede manejarlo sin errores?
   - Hay logica de negocio que podria perderse?
   - El resultado requiere validacion humana?

### Paso 3: Clasificar Estrategia

**SIMPLE (ora2pg)** cuando:
- Solo tiene conversiones sintacticas (VARCHAR2 -> VARCHAR, NVL -> COALESCE)
- NO tiene features Oracle problematicas
- NO tiene logica de negocio critica
- Confianza de conversion > 70%

**COMPLEX (Agentes IA)** cuando:
- Tiene AUTONOMOUS_TRANSACTION, UTL_HTTP, UTL_FILE
- **Tiene DBMS_SQL** (requiere conversion especializada - Decision 8 DEFERRED)
- **Tiene tipos coleccion** (TABLE OF INDEX BY, VARRAY, OBJECT TYPE - Decision 9 DEFERRED)
- **Es motor de formulas dinamicas** (requiere analisis especifico - Decision 10 DEFERRED)
- Tiene variables de estado de paquete
- Tiene logica de negocio critica que no debe perderse
- Requiere decisiones arquitectonicas (dblink vs Lambda)
- El Code Comprehension Agent marco baja confianza (<0.7)

### Paso 4: Justificar Cada Decision
Para CADA objeto, documenta:
- POR QUE elegiste esa estrategia
- QUE riesgos identificaste
- QUE decisiones humanas se requieren (si aplica)

## Formato de Salida

Genera un ComplexityReport con:
1. Decision detallada para cada objeto
2. Listas separadas: simple_objects.txt y complex_objects.txt
3. Estadisticas de distribucion
4. Objetos que requieren revision humana urgente

## Reglas de Negocio para Clasificacion

### Features que SIEMPRE son COMPLEX:
- AUTONOMOUS_TRANSACTION (requiere dblink o redeseno)
- UTL_HTTP (requiere Lambda + wrapper functions)
- UTL_FILE con DIRECTORY (requiere aws_s3)
- Variables de estado de paquete (requiere session variables)
- DBMS_SCHEDULER/DBMS_JOB (requiere pg_cron)

### Features que PUEDEN ser SIMPLE:
- NVL, NVL2, DECODE (conversion sintactica directa)
- SYSDATE, SYSTIMESTAMP (CURRENT_TIMESTAMP)
- ROWNUM (LIMIT)
- (+) outer join (LEFT/RIGHT JOIN)
- CONNECT BY (WITH RECURSIVE) - depende de complejidad

### Codigo Legacy Confuso
Si el Code Comprehension Agent marco:
- confidence_score < 0.5 -> Automaticamente COMPLEX
- ambiguities no vacio -> COMPLEX con human_review_required
- legacy_notes con "workaround" -> Revisar cuidadosamente

## Optimizacion de Tokens

Tu objetivo secundario es MINIMIZAR tokens de Claude para objetos simples:
- ~70% deberia ser SIMPLE (ora2pg, 0 tokens Claude)
- ~30% deberia ser COMPLEX (justifica uso de tokens)

Si clasificas mas del 40% como COMPLEX, revisa tu criterio.
"""
)
```

### 2.4 System Prompt Dinamico del Migration Strategist

```python
@migration_strategist.system_prompt
async def add_aurora_context(ctx: RunContext[MigrationStrategyDeps]) -> str:
    """Agrega contexto de Aurora PostgreSQL al prompt."""
    
    extensions = ", ".join(ctx.deps.available_extensions)
    
    return f"""
## Contexto de Destino

- **Version Aurora:** PostgreSQL {ctx.deps.aurora_version}
- **Extensiones disponibles:** {extensions}
- **Threshold para SIMPLE:** {ctx.deps.simple_threshold}
- **Threshold para revision humana:** {ctx.deps.human_review_threshold}

## Rutas de Entrada
- **Conocimiento:** {ctx.deps.knowledge_path}
- **Codigo fuente:** {ctx.deps.extracted_path}

## Session
- **ID:** {ctx.deps.session_id}
- **Timestamp:** {ctx.deps.timestamp.isoformat()}
"""
```

### 2.5 Herramientas (Tools) del Migration Strategist

```python
@migration_strategist.tool
async def read_features_detected(
    ctx: RunContext[MigrationStrategyDeps]
) -> str:
    """
    Lee el archivo features_detected.json generado por Code Comprehension Agent.
    
    Returns:
        Contenido JSON con todas las features Oracle detectadas
    """
    import os
    import json
    
    filepath = os.path.join(ctx.deps.knowledge_path, 'features_detected.json')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except FileNotFoundError:
        return "Error: features_detected.json no encontrado. Ejecutar Code Comprehension Agent primero."
    except Exception as e:
        return f"Error al leer features: {str(e)}"


@migration_strategist.tool
async def get_object_knowledge(
    ctx: RunContext[MigrationStrategyDeps],
    object_name: str
) -> str:
    """
    Obtiene el conocimiento extraido para un objeto especifico.
    
    Args:
        object_name: Nombre del objeto PL/SQL
    
    Returns:
        Conocimiento agregado del objeto (reglas, flujos, dependencias)
    """
    import os
    
    knowledge = []
    
    categories = ['rules', 'flows', 'calculations']
    for category in categories:
        filepath = os.path.join(ctx.deps.knowledge_path, category, f"{object_name}.md")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                knowledge.append(f"## {category.upper()}\n{f.read()}")
    
    if knowledge:
        return "\n\n".join(knowledge)
    else:
        return f"No se encontro conocimiento para {object_name}"


@migration_strategist.tool
async def get_dependency_graph(
    ctx: RunContext[MigrationStrategyDeps],
    object_name: str
) -> str:
    """
    Obtiene el grafo de dependencias de un objeto.
    
    Args:
        object_name: Nombre del objeto PL/SQL
    
    Returns:
        Lista de objetos que dependen de este y de los que este depende
    """
    import os
    import json
    
    filepath = os.path.join(ctx.deps.knowledge_path, 'dependencies', 'object_dependencies.json')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            all_deps = json.load(f)
        
        obj_deps = all_deps.get(object_name, {})
        
        return f"""
Dependencias de {object_name}:

Llama a (depends_on):
{json.dumps(obj_deps.get('depends_on', []), indent=2)}

Es llamado por (dependents):
{json.dumps(obj_deps.get('dependents', []), indent=2)}

Tablas accedidas:
{json.dumps(obj_deps.get('tables', []), indent=2)}
"""
    except Exception as e:
        return f"Error al obtener dependencias: {str(e)}"


@migration_strategist.tool
async def evaluate_ora2pg_compatibility(
    ctx: RunContext[MigrationStrategyDeps],
    object_name: str,
    features: list[str]
) -> str:
    """
    Evalua si un objeto puede ser procesado por ora2pg.
    
    Args:
        object_name: Nombre del objeto
        features: Lista de features Oracle detectadas en el objeto
    
    Returns:
        Evaluacion de compatibilidad con ora2pg
    """
    import json
    
    ora2pg_incompatible = {
        # Features criticas (Decision 8, 9, 10 - v2.2)
        'DBMS_SQL': 'Requiere conversion a EXECUTE + format() (Decision 8 DEFERRED)',
        'TABLE_OF_INDEX_BY': 'Requiere conversion a arrays o hstore (Decision 9 DEFERRED)',
        'TABLE_OF': 'Requiere conversion a arrays PostgreSQL (Decision 9 DEFERRED)',
        'VARRAY': 'Requiere conversion a arrays con constraints (Decision 9 DEFERRED)',
        'OBJECT_TYPE': 'Requiere conversion a Composite Types o JSON (Decision 9 DEFERRED)',
        'NLS_SESSION_CONFIG': 'Requiere SET lc_numeric/datestyle/lc_messages (conversion automatica)',
        'DYNAMIC_FORMULA_ENGINE': 'Requiere analisis especifico (Decision 10 DEFERRED)',

        # Features ya conocidas
        'AUTONOMOUS_TRANSACTION': 'Requiere dblink o redeseno arquitectonico',
        'UTL_HTTP': 'Requiere Lambda + wrapper functions',
        'UTL_FILE': 'Requiere aws_s3 extension',
        'UTL_MAIL': 'No migrar logica de email',
        'UTL_SMTP': 'No migrar logica de email',
        'DBMS_SCHEDULER': 'Requiere pg_cron con redeseno',
        'DBMS_JOB': 'Requiere pg_cron con redeseno',
        'PACKAGE_STATE_VARIABLE': 'Requiere session variables (SET/current_setting)',
        'REF_CURSOR_COMPLEX': 'Puede requerir ajustes manuales',
        'BULK_COLLECT_FORALL': 'Puede requerir ajustes manuales',
    }
    
    incompatible_found = []
    for feature in features:
        if feature in ora2pg_incompatible:
            incompatible_found.append({
                'feature': feature,
                'reason': ora2pg_incompatible[feature]
            })
    
    if not incompatible_found:
        return f"""
{object_name} es COMPATIBLE con ora2pg.

Features detectadas: {features}
Todas son convertibles automaticamente.
Recomendacion: SIMPLE
"""
    else:
        return f"""
{object_name} NO es compatible con ora2pg.

Features problematicas:
{json.dumps(incompatible_found, indent=2)}

Recomendacion: COMPLEX
"""


@migration_strategist.tool
async def write_complexity_report(
    ctx: RunContext[MigrationStrategyDeps],
    report: dict
) -> str:
    """
    Escribe el reporte de complejidad y las listas de objetos.
    
    Args:
        report: Diccionario con el ComplexityReport completo
    
    Returns:
        Confirmacion de archivos escritos
    """
    import os
    import json
    
    output_path = ctx.deps.complexity_output_path
    os.makedirs(output_path, exist_ok=True)
    
    files_written = []
    
    # 1. Escribir complexity_report.md
    md_path = os.path.join(output_path, 'complexity_report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Reporte de Complejidad de Migracion\n\n")
        f.write(f"**Generado:** {report.get('generated_at', 'N/A')}\n")
        f.write(f"**Total objetos:** {report.get('total_objects', 0)}\n\n")
        
        f.write("## Estadisticas\n\n")
        f.write(f"- SIMPLE (ora2pg): {report.get('simple_count', 0)} ({report.get('simple_percentage', 0):.1f}%)\n")
        f.write(f"- COMPLEX (IA): {report.get('complex_count', 0)} ({report.get('complex_percentage', 0):.1f}%)\n\n")
        
        f.write("## Objetos que Requieren Revision Humana\n\n")
        for obj in report.get('human_review_required', []):
            f.write(f"- {obj}\n")
        
        f.write("\n## Decisiones Detalladas\n\n")
        for decision in report.get('decisions', []):
            f.write(f"### {decision.get('object_name')}\n")
            f.write(f"**Estrategia:** {decision.get('strategy')}\n")
            f.write(f"**Complejidad:** {decision.get('complexity_level')}\n")
            f.write(f"**Razonamiento:** {decision.get('reasoning')}\n\n")
    
    files_written.append(md_path)
    
    # 2. Escribir simple_objects.txt
    simple_path = os.path.join(output_path, 'simple_objects.txt')
    with open(simple_path, 'w', encoding='utf-8') as f:
        for obj in report.get('simple_objects', []):
            f.write(f"{obj}\n")
    files_written.append(simple_path)
    
    # 3. Escribir complex_objects.txt
    complex_path = os.path.join(output_path, 'complex_objects.txt')
    with open(complex_path, 'w', encoding='utf-8') as f:
        for obj in report.get('complex_objects', []):
            f.write(f"{obj}\n")
    files_written.append(complex_path)
    
    # 4. Escribir JSON para procesamiento programatico
    json_path = os.path.join(output_path, 'complexity_report.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    files_written.append(json_path)
    
    return f"Archivos escritos:\n" + "\n".join(files_written)
```

### 2.6 Estructura de Output del Migration Strategist

```
complexity/
├── complexity_report.md       # Reporte legible para humanos
├── complexity_report.json     # Datos estructurados para procesamiento
├── simple_objects.txt         # Lista para ora2pg (~70%)
├── complex_objects.txt        # Lista para agentes IA (~30%)
└── human_review_required.txt  # Objetos que necesitan atencion inmediata
```

---

## 3. Estrategia de Paralelizacion

### 3.1 Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FASE 1: COMPRENSION SEMANTICA                     │
│                  (Code Comprehension Agent - Paralelo)               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   extracted/                                                         │
│   ├── functions.sql ──────┐                                          │
│   ├── procedures.sql ─────┼──► Worker 1 (Batch 1-50)    ─┐          │
│   ├── packages_body.sql ──┤                               │          │
│   └── triggers.sql ───────┘                               │          │
│                            ├──► Worker 2 (Batch 51-100)  ─┼──► knowledge/
│                            ├──► Worker 3 (Batch 101-150) ─┤          │
│                            └──► Worker N (Batch N)       ─┘          │
│                                                                      │
│   Tiempo estimado: 1-2 horas (con 5 workers paralelos)              │
│   Tokens: Moderado (~2-3M tokens para 8,122 objetos)                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASE 2: DECISION ESTRATEGICA                      │
│                  (Migration Strategist - Secuencial)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Input:                                                             │
│   ├── knowledge/features_detected.json                               │
│   ├── knowledge/rules/                                               │
│   ├── knowledge/dependencies/                                        │
│   └── knowledge/flows/                                               │
│                                                                      │
│   Proceso: Secuencial (necesita vista global de dependencias)       │
│                                                                      │
│   Output:                                                            │
│   └── complexity/                                                    │
│       ├── simple_objects.txt (~5,700 objetos = 70%)                 │
│       ├── complex_objects.txt (~2,400 objetos = 30%)                │
│       └── complexity_report.md                                       │
│                                                                      │
│   Tiempo estimado: 30-45 minutos                                    │
│   Tokens: Moderado (~500K-1M tokens)                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Configuracion de Workers Paralelos

```python
import asyncio
from typing import List


class ParallelProcessor:
    """Procesador paralelo para Code Comprehension Agent."""
    
    def __init__(
        self,
        max_workers: int = 5,
        batch_size: int = 50
    ):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def process_batch(
        self,
        batch_id: str,
        objects: List[tuple[str, str]],
        deps: CodeComprehensionDeps
    ) -> BatchAnalysisResult:
        """Procesa un batch con control de concurrencia."""
        
        async with self.semaphore:
            result = await code_comprehension_agent.run(
                create_batch_prompt(objects),
                deps=deps
            )
            
            await self.save_checkpoint(batch_id, result.output)
            
            return result.output
    
    async def process_all(
        self,
        all_objects: List[tuple[str, str]],
        deps: CodeComprehensionDeps
    ) -> List[BatchAnalysisResult]:
        """Procesa todos los objetos en paralelo con batches."""
        
        batches = [
            all_objects[i:i + self.batch_size]
            for i in range(0, len(all_objects), self.batch_size)
        ]
        
        tasks = [
            self.process_batch(f"batch_{idx:04d}", batch, deps)
            for idx, batch in enumerate(batches)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]
        
        if failed:
            await self.log_failures(failed)
        
        return successful
    
    async def save_checkpoint(self, batch_id: str, result: BatchAnalysisResult):
        """Guarda checkpoint para recuperacion."""
        import json
        
        checkpoint_path = f"checkpoints/{batch_id}.json"
        with open(checkpoint_path, 'w') as f:
            json.dump(result.model_dump(), f, default=str)
    
    async def resume_from_checkpoint(self) -> set[str]:
        """Retorna IDs de batches ya procesados."""
        import os
        import glob
        
        checkpoints = glob.glob("checkpoints/batch_*.json")
        return {os.path.basename(c).replace('.json', '') for c in checkpoints}
```

---

## 4. Optimizacion de Tokens

### 4.1 Estrategias Implementadas

| Estrategia | Descripcion | Ahorro Estimado |
|------------|-------------|-----------------|
| **Batching** | Procesar 50 objetos por llamada vs 1 | ~40% |
| **Reutilizacion de contexto** | Tablas ya analizadas no se re-procesan | ~15% |
| **Conocimiento estructurado** | Migration Strategist lee JSON, no codigo | ~30% |
| **ora2pg para simples** | 70% objetos sin tokens Claude | ~70% de 70% |
| **Checkpoints** | No re-procesar batches completados | Variable |

### 4.2 Estimacion de Tokens

```
Total objetos: 8,122

FASE 1 - Code Comprehension Agent:
- Promedio tokens por objeto: ~300 (input) + ~500 (output) = 800
- Batches de 50: overhead reducido ~600 tokens/batch
- Total estimado: 8,122 * 800 / 50 * 1.2 = ~1.5M tokens

FASE 2 - Migration Strategist:
- Input: features_detected.json (~50K tokens)
- Procesamiento: ~200 tokens/decision * 8,122 = ~1.6M tokens
- Output: reporte + listas = ~100K tokens
- Total estimado: ~1.8M tokens

FASE 3 - Conversion:
- SIMPLE (ora2pg): 0 tokens (5,700 objetos)
- COMPLEX (agentes): ~2,000 tokens/objeto * 2,400 = ~4.8M tokens

TOTAL ESTIMADO: ~8.1M tokens
vs SIN OPTIMIZACION: ~24M tokens
AHORRO: ~66%
```

---

## 5. Manejo de Codigo Legacy

### 5.1 Patrones de Codigo Problematico

El Code Comprehension Agent esta disenado para detectar y documentar:

```python
LEGACY_PATTERNS = {
    "dead_code": {
        "indicators": ["codigo comentado", "variables no usadas", "branches inalcanzables"],
        "action": "Evaluar si eliminar o mantener por seguridad"
    },
    "magic_numbers": {
        "indicators": ["numeros sin constantes", "codigos de estado hardcodeados"],
        "action": "Documentar significado, considerar constantes"
    },
    "copy_paste_code": {
        "indicators": ["bloques identicos", "ligeras variaciones"],
        "action": "Considerar refactorizacion post-migracion"
    },
    "workaround_historico": {
        "indicators": ["comentarios con fechas antiguas", "TODO/FIXME/HACK"],
        "action": "Documentar contexto, mantener comportamiento"
    },
    "exception_swallowing": {
        "indicators": ["WHEN OTHERS THEN NULL", "EXCEPTION sin log"],
        "action": "Agregar logging minimo, mantener comportamiento"
    },
    "implicit_conversion": {
        "indicators": ["comparacion tipos mixtos", "TO_DATE sin formato"],
        "action": "Hacer explicito en PostgreSQL"
    }
}
```

### 5.2 Heuristicas de Confidence Score

```python
def calculate_confidence(object_analysis: dict) -> float:
    """
    Calcula el confidence score basado en heuristicas.
    """
    score = 1.0
    
    if object_analysis.get('legacy_notes'):
        score -= 0.1 * len(object_analysis['legacy_notes'])
    
    if object_analysis.get('ambiguities'):
        score -= 0.15 * len(object_analysis['ambiguities'])
    
    for feature in object_analysis.get('oracle_features', []):
        if feature['migration_complexity'] == 'CRITICAL':
            score -= 0.2
        elif feature['migration_complexity'] == 'HIGH':
            score -= 0.1
    
    if 'WHEN OTHERS THEN NULL' in object_analysis.get('raw_code', ''):
        score -= 0.1
    
    if object_analysis.get('lines_of_code', 0) > 500:
        score -= 0.1
    
    return max(0.0, min(1.0, score))
```

---

## 6. Integracion con pgvector

### 6.1 Schema para Embeddings

```sql
-- Crear extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de embeddings de conocimiento
CREATE TABLE knowledge_embeddings (
    id SERIAL PRIMARY KEY,
    
    object_name VARCHAR(128) NOT NULL,
    category VARCHAR(50) NOT NULL,
    
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    
    embedding vector(1536),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(36)
);

-- Indice para busqueda semantica
CREATE INDEX ON knowledge_embeddings 
USING hnsw (embedding vector_cosine_ops);

-- Funcion de busqueda semantica
CREATE OR REPLACE FUNCTION search_knowledge(
    query_embedding vector(1536),
    limit_results INT DEFAULT 10
)
RETURNS TABLE (
    object_name VARCHAR,
    category VARCHAR,
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ke.object_name,
        ke.category,
        ke.content,
        1 - (ke.embedding <=> query_embedding) as similarity
    FROM knowledge_embeddings ke
    ORDER BY ke.embedding <=> query_embedding
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;
```

### 6.2 Uso por Agentes Futuros

```python
async def query_knowledge_base(
    question: str,
    embedding_model: str = "text-embedding-3-small"
) -> list[dict]:
    """
    Busqueda semantica en la base de conocimiento.
    Util para agentes de conversion en Fase 3.
    """
    
    embedding = await generate_embedding(question, embedding_model)
    
    query = """
    SELECT object_name, category, content, 
           1 - (embedding <=> $1::vector) as similarity
    FROM knowledge_embeddings
    ORDER BY embedding <=> $1::vector
    LIMIT 10
    """
    
    results = await db.fetch(query, embedding)
    
    return [dict(r) for r in results]
```

---

## 7. Errores Comunes y Mitigaciones

| Error | Causa | Mitigacion |
|-------|-------|------------|
| **Timeout en batch grande** | Objetos muy complejos | Reducir batch_size a 25 |
| **Output truncado** | Excede limite de tokens output | Dividir analisis en multiples llamadas |
| **Embedding dimension mismatch** | Modelo cambiado | Verificar dimension en config |
| **Checkpoint corrupto** | Interrupcion durante escritura | Usar escritura atomica con temp file |
| **Dependencia circular** | Paquetes que se llaman mutuamente | Detectar ciclos, procesar juntos |
| **Memoria insuficiente** | Demasiados workers paralelos | Reducir max_workers |

### Protocolo de Retry

```python
async def robust_agent_call(
    agent: Agent,
    prompt: str,
    deps: BaseModel,
    max_retries: int = 3
) -> Any:
    """
    Llamada robusta con reintentos y backoff exponencial.
    """
    import asyncio
    
    for attempt in range(max_retries):
        try:
            result = await agent.run(prompt, deps=deps)
            return result.output
            
        except RateLimitError:
            wait_time = 2 ** attempt * 10
            await asyncio.sleep(wait_time)
            
        except TokenLimitError:
            prompt = truncate_prompt(prompt, ratio=0.8)
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(5)
    
    raise MaxRetriesExceeded(f"Failed after {max_retries} attempts")
```

---

## 8. Consideraciones de Rendimiento

### 8.1 Benchmarks Esperados

| Metrica | Objetivo | Aceptable |
|---------|----------|-----------|
| **Throughput Code Comprehension** | 100 obj/min | 50 obj/min |
| **Throughput Migration Strategist** | 500 obj/min | 200 obj/min |
| **Latencia por batch (50 obj)** | < 30s | < 60s |
| **Uso de memoria** | < 2GB | < 4GB |
| **Tasa de exito** | > 98% | > 95% |

### 8.2 Monitoreo

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentMetrics:
    """Metricas de ejecucion de agentes."""
    
    agent_name: str
    batch_id: str
    
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    objects_processed: int
    objects_successful: int
    objects_failed: int
    
    tokens_input: int
    tokens_output: int
    tokens_total: int
    
    cost_usd: float
    
    def log(self):
        """Registra metricas en formato estructurado."""
        import json
        
        print(json.dumps({
            "agent": self.agent_name,
            "batch": self.batch_id,
            "duration_s": self.duration_seconds,
            "objects": self.objects_processed,
            "success_rate": self.objects_successful / max(1, self.objects_processed),
            "tokens": self.tokens_total,
            "cost_usd": self.cost_usd
        }))
```

---

## 9. Estrategia de Testing

### 9.1 Tests Unitarios de Agentes

```python
import pytest
from pydantic_ai.testing import TestModel


@pytest.fixture
def test_model():
    """Modelo mock para testing determinista."""
    return TestModel()


@pytest.fixture
def test_deps():
    """Dependencias de prueba."""
    return CodeComprehensionDeps(
        pgvector_connection_string="postgresql://test:test@localhost/test",
        schema_name="TEST_SCHEMA",
        extracted_path="tests/fixtures/extracted/",
        knowledge_output_path="tests/output/knowledge/",
        batch_size=5,
        session_id="test-session-001",
        start_time=datetime.now()
    )


async def test_code_comprehension_simple_function(test_model, test_deps):
    """Test analisis de funcion simple."""
    
    test_agent = code_comprehension_agent.override(model=test_model)
    
    test_model.set_response(BatchAnalysisResult(
        batch_id="test-batch",
        objects_analyzed=[
            ObjectAnalysis(
                object_name="TEST_FUNCTION",
                object_type="FUNCTION",
                lines_of_code=50,
                business_rules=[],
                oracle_features=[],
                dependencies=[],
                analysis_timestamp=datetime.now(),
                confidence_score=0.9
            )
        ],
        total_objects=1,
        successful=1,
        failed=0,
        total_rules_extracted=0,
        total_calculations=0,
        total_flows=0,
        total_features=0,
        processing_time_seconds=1.5,
        tokens_used_estimate=500
    ))
    
    result = await test_agent.run(
        "Analiza TEST_FUNCTION",
        deps=test_deps
    )
    
    assert result.output.successful == 1
    assert result.output.objects_analyzed[0].confidence_score == 0.9


async def test_migration_strategist_classification(test_model, test_deps):
    """Test clasificacion SIMPLE vs COMPLEX."""
    
    strategist_deps = MigrationStrategyDeps(
        knowledge_path="tests/fixtures/knowledge/",
        extracted_path="tests/fixtures/extracted/",
        session_id="test-session-001",
        timestamp=datetime.now()
    )
    
    test_agent = migration_strategist.override(model=test_model)
    
    test_model.set_response(ComplexityReport(
        report_id="test-report",
        generated_at=datetime.now(),
        decisions=[
            MigrationDecision(
                object_name="PKG_AUDITORIA",
                object_type="PACKAGE",
                strategy=MigrationStrategy.COMPLEX,
                complexity_level=ComplexityLevel.HIGH,
                confidence=0.95,
                reasoning="Contiene AUTONOMOUS_TRANSACTION que requiere dblink",
                oracle_features=[
                    OracleFeatureRisk(
                        feature_type="AUTONOMOUS_TRANSACTION",
                        occurrences=3,
                        risk_level=ComplexityLevel.HIGH,
                        migration_approach="dblink",
                        aurora_compatible=True
                    )
                ],
                estimated_effort_hours=4.0
            )
        ],
        total_objects=1,
        simple_count=0,
        complex_count=1,
        simple_percentage=0.0,
        complex_percentage=100.0,
        simple_objects=[],
        complex_objects=["PKG_AUDITORIA"],
        total_estimated_hours=4.0,
        estimated_tokens_for_complex=2000
    ))
    
    result = await test_agent.run(
        "Evalua PKG_AUDITORIA",
        deps=strategist_deps
    )
    
    assert result.output.complex_count == 1
    assert "PKG_AUDITORIA" in result.output.complex_objects
```

---

## 10. Proximos Pasos de Implementacion

### 10.1 Orden de Implementacion

1. **Semana 1:**
   - [ ] Implementar modelos Pydantic (deps, outputs)
   - [ ] Crear agente Code Comprehension con tools basicos
   - [ ] Test con 10 objetos de prueba

2. **Semana 2:**
   - [ ] Implementar procesamiento por batches
   - [ ] Agregar paralelizacion con semaphore
   - [ ] Implementar checkpoints

3. **Semana 3:**
   - [ ] Implementar Migration Strategist
   - [ ] Integracion con conocimiento de Fase 1
   - [ ] Generacion de listas SIMPLE/COMPLEX

4. **Semana 4:**
   - [ ] Integracion con pgvector
   - [ ] Testing end-to-end
   - [ ] Optimizacion de tokens

### 10.2 Dependencias de Infraestructura

```bash
# Dependencias Python
poetry add pydantic-ai pydantic asyncpg pgvector openai

# Extensiones PostgreSQL (Aurora)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS aws_lambda;
CREATE EXTENSION IF NOT EXISTS aws_commons;
```

---

## 11. Ejemplo de features_detected.json (Actualizado v1.1)

### Estructura Completa con Nuevas Features

```json
{
  "generation_timestamp": "2025-12-31T10:30:00Z",
  "total_objects_analyzed": 8122,
  "features_summary": {
    "total_features": 1247,
    "critical_features": 453,
    "deferred_decisions": 3
  },

  "features_by_type": {
    "AUTONOMOUS_TRANSACTION": {
      "count": 42,
      "objects": ["PKG_AUDITORIA", "PKG_LOG_EVENTOS", ...],
      "decision_status": "Validated (Decision 2)"
    },

    "UTL_HTTP": {
      "count": 87,
      "objects": ["PKG_INTEGRACION_SAP", "PKG_WS_CLIENTE", ...],
      "decision_status": "Validated (Decision 7)"
    },

    "DBMS_SQL": {
      "count": 18,
      "objects": [
        "RHH_K_ADMINISTRA_FORMULA",
        "PKG_DINAMICO_REPORTES",
        "PKG_CONSTRUCCION_SQL"
      ],
      "methods_used": [
        "OPEN_CURSOR",
        "PARSE",
        "BIND_VARIABLE",
        "EXECUTE",
        "VARIABLE_VALUE",
        "CLOSE_CURSOR"
      ],
      "decision_status": "DEFERRED (Decision 8 - post-scan)",
      "notes": "Motor de formulas dinamicas detectado. Requiere analisis de complejidad."
    },

    "TABLE_OF_INDEX_BY": {
      "count": 234,
      "objects": [
        "RHH_K_ADMINISTRA_FORMULA",
        "PKG_PROCESAMIENTO_MASIVO",
        ...
      ],
      "example_declarations": [
        "TYPE T_Gt_Variables IS TABLE OF Varchar2(61) INDEX BY BINARY_INTEGER",
        "TYPE T_Empleados IS TABLE OF NUMBER INDEX BY VARCHAR2(50)"
      ],
      "decision_status": "DEFERRED (Decision 9 - post-scan)",
      "notes": "Hash maps. Requiere mapeo a arrays[] o hstore."
    },

    "TABLE_OF": {
      "count": 156,
      "objects": ["PKG_VENTAS", "PKG_INVENTARIO", ...],
      "decision_status": "DEFERRED (Decision 9 - post-scan)",
      "notes": "Nested tables. Conversion directa a arrays[]."
    },

    "VARRAY": {
      "count": 23,
      "objects": ["PKG_CONFIGURACION", ...],
      "decision_status": "DEFERRED (Decision 9 - post-scan)",
      "notes": "Arrays con limite. Conversion a arrays[] con constraint."
    },

    "OBJECT_TYPE": {
      "count": 67,
      "objects": ["PKG_TIPOS_COMPLEJOS", "PKG_FACTURACION", ...],
      "decision_status": "DEFERRED (Decision 9 - post-scan)",
      "notes": "Tipos personalizados. Evaluar Composite Types vs JSON."
    },

    "NLS_SESSION_CONFIG": {
      "count": 145,
      "settings": {
        "NLS_NUMERIC_CHARACTERS": 89,
        "NLS_DATE_FORMAT": 34,
        "NLS_LANGUAGE": 22
      },
      "decision_status": "Auto-conversion",
      "notes": "Conversion automatica a SET lc_numeric, datestyle, lc_messages."
    },

    "DYNAMIC_FORMULA_ENGINE": {
      "count": 3,
      "objects": [
        "RHH_K_ADMINISTRA_FORMULA",
        "PKG_CALCULO_COMISIONES",
        "PKG_EVALUA_DESCUENTOS"
      ],
      "decision_status": "DEFERRED (Decision 10 - post-scan)",
      "notes": "Motores que evaluan expresiones matematicas almacenadas como strings.",
      "example_expressions": [
        "RHH_F_SUELDO / 30 + 15",
        "BASE * (1 + TASA_IVA) - DESCUENTO"
      ]
    },

    "UTL_FILE": {
      "count": 12,
      "objects": ["PKG_REPORTES_EXCEL", ...],
      "decision_status": "Validated (Decision 6 - aws_s3)"
    },

    "DIRECTORY": {
      "count": 8,
      "decision_status": "Validated (Decision 6 - S3 bucket)"
    },

    "PACKAGE_STATE_VARIABLE": {
      "count": 189,
      "decision_status": "Validated (Decision 1 - session variables)"
    }
  },

  "complexity_impact": {
    "objects_with_dbms_sql": 18,
    "objects_with_collections": 423,
    "objects_with_nls_config": 145,
    "objects_with_formula_engine": 3,
    "estimated_complex_rate": "38%"
  }
}
```

**Notas importantes v1.1:**
- **Decisions 8, 9, 10 DEFERRED:** Se tomaran despues del scan completo basado en metricas reales
- **Impacto estimado:** ~38% de objetos pueden ser COMPLEX debido a las nuevas features
- **Prioridad de analisis:** DBMS_SQL y motores de formulas dinamicas son criticos

---

## Referencias

- [Pydantic AI - Documentacion Oficial](https://ai.pydantic.dev/)
- [Pydantic AI - Agents](https://ai.pydantic.dev/agents/)
- [Pydantic AI - Tools](https://ai.pydantic.dev/tools/)
- [Pydantic AI - API Reference](https://ai.pydantic.dev/api/agent/)
- [pgvector - GitHub](https://github.com/pgvector/pgvector)
- [AWS Aurora PostgreSQL Extensions](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Extensions.html)

---

**Documento creado por:** pydantic-ai-architect (sub-agente)
**Fecha creacion:** 2025-12-30
**Ultima actualizacion:** 2025-12-31
**Version:** 1.1
**Estado:** plan-ready

**Cambios v1.1:**
- Añadidas 4 features criticas detectadas en discovery v2.2
- Actualizado system prompt del Code Comprehension Agent
- Actualizada logica de evaluacion del Migration Strategist
- Añadido ejemplo completo de features_detected.json

**Proxima accion:** Proceder a implementacion en Fase 2 con deteccion ampliada de features Oracle.
