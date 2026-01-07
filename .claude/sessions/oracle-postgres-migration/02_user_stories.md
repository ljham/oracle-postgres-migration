# User Stories - Oracle to PostgreSQL Migration

> **📖 Contexto del Proyecto:** Herramienta basada en agentes IA para migrar 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora) en 3 meses. Ver [00_index.md](./00_index.md) para resumen ejecutivo completo. Ver [01_problem_statement.md](./01_problem_statement.md) para problema y objetivos.

**Versión:** 1.9 | **Fecha:** 2025-12-29 | **Estado:** validated

---

## Épicas del Proyecto

| # | Epic | Prioridad | User Stories | Estado |
|---|------|-----------|--------------|--------|
| 0 | Infraestructura Claude Code Web | Must Have | 2 | Pendiente |
| 1 | Comprensión Semántica del Código | Must Have | 5 | US-1.0 y US-1.5 ✅ |
| 2 | Decisión Estratégica y Migración | Must Have | 8 | Pendiente |
| 3 | Validación | Must Have | 3 | Pendiente |
| 4 | Migración de Backend | Should Have | 4 | Pendiente después de DB |

---

## Epic 0: Infraestructura Claude Code Web (Must Have)

### US-0.1: Orquestación en Claude Code Web
**Como** miembro del equipo de migración
**Quiero** ejecutar la migración en Claude Code Web con sub-agentes paralelos
**Para** aprovechar ejecución en background sin agotar tokens de CLI inmediatamente

**Criterios de Aceptación:**
- [ ] El sistema detecta cuando se acerca al límite de tokens
- [ ] Guarda estado actual (último objeto procesado) antes de pausar
- [ ] Reanuda automáticamente cuando los tokens se restablecen
- [ ] Continúa desde el último objeto procesado (no reinicia)
- [ ] Solo pausa para intervención humana cuando es estrictamente necesario
- [ ] Log indica claramente "pausado por tokens" vs "pausado por decisión requerida"
- [ ] Sub-agentes pueden trabajar en paralelo (hasta 5-10 concurrentes)

### US-0.2: Logging y Trazabilidad Transversal
**Como** miembro del equipo de migración
**Quiero** tener log de todas las acciones realizadas
**Para** auditar, debuggear y reportar progreso

**Criterios de Aceptación:**
- [ ] Cada transformación se registra con: timestamp, objeto, acción, resultado
- [ ] Log diferencia objetos exitosos vs fallidos
- [ ] Se puede filtrar logs por: objeto, fecha, tipo de acción, estado
- [ ] El log incluye el "por qué" de cada decisión tomada por la IA
- [ ] Logs persisten entre sesiones (archivo Markdown)

**Prioridad:** Must Have (transversal a todos los epics)

---

## Epic 1: Comprensión Semántica del Código (Must Have)

**Actualizado:** Los objetos Oracle ya fueron extraídos usando `sql/extract_all_objects.sql` (ejecutado manualmente en sqlplus). Los archivos .sql están en el directorio `extracted/`.

**Sub-agente responsable:** Code Comprehension Agent (comprensión semántica)

### US-1.0: Estado de Extracción (COMPLETADO ✅)
**Como** miembro del equipo de migración
**Quiero** confirmar que tengo todos los objetos Oracle extraídos en formato .sql
**Para** proceder con el análisis de código

**Criterios de Aceptación:**
- [x] ✅ Script `sql/extract_all_objects.sql` ejecutado en sqlplus local
- [x] ✅ Archivos .sql generados en directorio `extracted/`:
  - [x] functions.sql (146 objetos)
  - [x] procedures.sql (196 objetos)
  - [x] packages_spec.sql (569 objetos)
  - [x] packages_body.sql (569 objetos)
  - [x] triggers.sql (87 objetos)
  - [x] tables.sql (estructura de tablas)
  - [x] primary_keys.sql (PKs)
  - [x] foreign_keys.sql (FKs)
  - [x] sequences.sql
  - [x] types.sql
  - [x] views.sql
  - [x] materialized_views.sql
  - [x] directories.sql
  - [x] inventory.md (inventario generado)
- [x] ✅ Total de objetos PL/SQL: 8,122
- [x] ✅ Archivos listos para análisis por Code Comprehension Agent

**Estado:** COMPLETADO ✅

### US-1.1: Comprensión Semántica de Código PL/SQL
**Como** miembro del equipo de migración
**Quiero** que el Code Comprehension Agent analice e interprete el código en `extracted/`
**Para** generar una base de conocimiento estructurada del sistema Oracle

**Criterios de Aceptación:**
- [ ] El agente lee TODOS los archivos .sql de `extracted/`
- [ ] Usa razonamiento semántico para COMPRENDER (NO solo parsear):
  - [ ] Relaciones entre tablas (interpretando PKs y FKs)
  - [ ] Reglas de negocio programadas en el código
  - [ ] Validaciones con su contexto y propósito
  - [ ] Cálculos de negocio (fórmulas con su significado)
  - [ ] Dependencias entre objetos (grafo de llamadas)
  - [ ] Features técnicas Oracle-específicas
  - [ ] Know-how implícito en el código
- [ ] Distingue entre lógica de negocio vs código técnico
- [ ] Interpreta la intención del desarrollador original
- [ ] Genera conocimiento estructurado (NO decisiones)
- [ ] Tiempo de análisis: 1-2 horas para 8,122 objetos (con paralelización)

### US-1.2: Extracción e Interpretación de Reglas de Negocio
**Como** arquitecto
**Quiero** que el Code Comprehension Agent extraiga e INTERPRETE las reglas de negocio del código PL/SQL
**Para** documentar el know-how empresarial y alimentar agentes IA

**Criterios de Aceptación:**
- [ ] El agente INTERPRETA (no solo detecta) validaciones:
  - [ ] Identifica IF ... THEN RAISE_APPLICATION_ERROR
  - [ ] Comprende el PROPÓSITO de cada validación
  - [ ] Captura el contexto de negocio
- [ ] El agente COMPRENDE cálculos de negocio:
  - [ ] Identifica fórmulas (porcentajes, descuentos, impuestos)
  - [ ] Interpreta QUÉ representa cada cálculo
  - [ ] Captura las condiciones bajo las cuales se aplica
- [ ] El agente MAPEA flujos de decisión (CASE, IF/ELSIF):
  - [ ] Entiende la lógica de decisión
  - [ ] Documenta en lenguaje natural el flujo
- [ ] Cada regla se documenta en formato estructurado:
  - Nombre de la regla (interpretado, no solo técnico)
  - Condiciones de activación (contexto de negocio)
  - Acciones/consecuencias (significado empresarial)
  - Objeto fuente (procedure/function)
- [ ] Las reglas se guardan en `knowledge/rules/` (Markdown para humanos)
- [ ] Las reglas se indexan en pgvector para búsqueda semántica por agentes

### US-1.3: Almacenamiento en Base de Conocimiento
**Como** arquitecto
**Quiero** almacenar el conocimiento capturado por el Code Comprehension Agent en pgvector
**Para** que sea consultable semánticamente por agentes y herramientas futuras que necesiten utilizar este conocimiento

**Criterios de Aceptación:**
- [ ] Confirmar configuración de pgvector en PostgreSQL 17.4
- [ ] Schema definido para almacenar: reglas, flujos, dependencias, features
- [ ] Embeddings generados para cada pieza de conocimiento interpretado
- [ ] Búsqueda semántica funcional (ej: "¿cómo se calcula el descuento?")
- [ ] Markdown como fuente de verdad en `knowledge/` (Git versionado)
- [ ] pgvector como índice de búsqueda (sincronizado con Markdown)
- [ ] El Migration Strategist puede consultar este conocimiento sin re-analizar código

### US-1.4: Mapeo e Interpretación de Flujos de Proceso
**Como** arquitecto
**Quiero** que el Code Comprehension Agent documente e INTERPRETE los flujos de proceso del sistema
**Para** entender cómo funcionan los procesos de negocio a nivel conceptual

**Criterios de Aceptación:**
- [ ] El agente MAPEA secuencias de llamadas (A llama B, B llama C)
- [ ] El agente INTERPRETA el propósito de cada flujo:
  - [ ] ¿Qué proceso de negocio representa?
  - [ ] ¿Cuál es el objetivo del flujo?
  - [ ] ¿Qué datos procesa?
- [ ] Genera diagramas de flujo en formato Mermaid (visualización)
- [ ] Cada flujo tiene descripción en lenguaje natural (comprensión humana)
- [ ] Los flujos se categorizan por dominio/módulo (organización)
- [ ] Output en `knowledge/flows/` (Markdown + Mermaid)

### US-1.5: Conversión de DDL a PostgreSQL (COMPLETADO ✅)
**Como** miembro del equipo de migración
**Quiero** confirmar que los scripts DDL convertidos a PostgreSQL son válidos
**Para** proceder con la ejecución de la estructura en PostgreSQL 17.4

**Criterios de Aceptación:**
- [x] ✅ Conversión DDL ejecutada con ora2pg
- [x] ✅ Scripts DDL PostgreSQL generados en `sql/exported/`:
  - [x] tables.sql (estructura completa de tablas convertida)
  - [x] sequences.sql (sintaxis PostgreSQL)
  - [x] types.sql (tipos personalizados convertidos)
- [x] ✅ Conversiones aplicadas por ora2pg:
  - [x] VARCHAR2(n) → VARCHAR(n) o TEXT
  - [x] NUMBER → NUMERIC
  - [x] DATE → TIMESTAMP
  - [x] CLOB → TEXT, BLOB → BYTEA
  - [x] Sequences: sintaxis PostgreSQL
- [x] ✅ Scripts listos para ejecutar en PostgreSQL 17.4

**Estado:** COMPLETADO ✅

**Nota:** La conversión DDL se realizó con ora2pg (herramienta especializada), no requiere sub-agente Claude.

---

## Epic 2: Decisión Estratégica y Migración (Must Have)

**Actualizado:** Este epic se ejecuta DESPUÉS de Epic 1 (comprensión semántica completada).

**Sub-agente responsable:** Migration Strategist (decisión estratégica)

### US-2.1: Evaluación y Clasificación de Complejidad de Migración
**Como** miembro del equipo de migración
**Quiero** que el Migration Strategist EVALÚE cada objeto y DECIDA la estrategia óptima de migración tomando en consideración los aspectos importantes de la base de datos en Amazon Aurora y la complejidad del objeto.
**Para** saber qué herramienta usar (ora2pg vs agentes IA) y optimizar el uso de tokens para la conversión

**Criterios de Aceptación:**
- [ ] El Migration Strategist lee el conocimiento del Code Comprehension Agent:
  - [ ] `knowledge/features_detected.json` (features técnicas identificadas)
  - [ ] `knowledge/rules/` (reglas de negocio interpretadas)
  - [ ] `knowledge/dependencies/` (dependencias mapeadas)
  - [ ] `extracted/*.sql` (código fuente como contexto adicional)
- [ ] Usa RAZONAMIENTO (NO reglas fijas) para evaluar:
  - [ ] ¿Por qué este objeto es complejo para migrar?
  - [ ] ¿Qué impacto arquitectónico tiene?
  - [ ] ¿Qué riesgos hay con conversión automática (ora2pg)?
  - [ ] ¿Requiere decisiones arquitectónicas humanas?
  - [ ] ¿Cuál es la criticidad del objeto para el negocio?
- [ ] Clasifica con JUSTIFICACIÓN razonada:
  - **Simple:** ora2pg puede convertir sin riesgo significativo (~70%)
  - **Complejo:** Requiere agentes IA por decisiones arquitectónicas (~30%)
- [ ] Genera outputs:
  - [ ] `complexity/complexity_report.md` (análisis detallado con razonamiento)
  - [ ] `complexity/simple_objects.txt` (lista para ora2pg)
  - [ ] `complexity/complex_objects.txt` (lista para agentes IA)
- [ ] Reporte muestra distribución: X% simple, Y% complejo
- [ ] Usuario puede override clasificación manualmente (con justificación)

### US-2.2: Conversión de Packages a Schemas
**Como** miembro del equipo de migración
**Quiero** que los packages Oracle se conviertan a schemas PostgreSQL
**Para** mantener la organización lógica del código

**Criterios de Aceptación:**
- [ ] Cada package se convierte en un schema PostgreSQL con mismo nombre
- [ ] Las funciones/procedures del package se crean dentro del schema
- [ ] Las variables de estado se manejan con session variables (SET/current_setting)
- [ ] Ejemplo de conversión de estado:
  ```sql
  -- Oracle: g_usuario_actual VARCHAR2(100) en package
  -- PostgreSQL: SET pkg_name.usuario_actual = 'valor'
  --             SELECT current_setting('pkg_name.usuario_actual')
  ```
- [ ] Las dependencias entre packages se resuelven creando schemas en orden correcto
- [ ] El código que llamaba PKG_VENTAS.GET_DESCUENTO() ahora llama pkg_ventas.get_descuento()

### US-2.3: Manejo de AUTONOMOUS_TRANSACTION
**Como** miembro del equipo de migración
**Quiero** que las ~40 transacciones autónomas tengan una solución funcional
**Para** preservar el comportamiento tal cual funciona en Oracle

**Criterios de Aceptación:**
- [ ] El sistema identifica todos los usos de AUTONOMOUS_TRANSACTION (~40 objetos)
- [ ] Para cada caso, el sistema propone:
  - Opción A: Implementación vía dblink (preserva comportamiento exacto)
  - Opción B: Rediseño del flujo (mejor arquitectura, más trabajo)
- [ ] Usuario decide por cada caso cuál opción aplicar
- [ ] Se documenta cada conversión con advertencia sobre overhead (dblink)
- [ ] Se valida que el comportamiento es equivalente (commit independiente)

### US-2.4: Manejo de AUTHID CURRENT_USER
**Como** miembro del equipo de migración
**Quiero** que las funciones con AUTHID CURRENT_USER se migren correctamente
**Para** preservar el modelo de seguridad

**Criterios de Aceptación:**
- [ ] El sistema identifica todos los usos de AUTHID CURRENT_USER
- [ ] Conversión: AUTHID CURRENT_USER → SECURITY INVOKER
- [ ] Conversión: AUTHID DEFINER (default) → SECURITY DEFINER
- [ ] Se valida que los permisos funcionan igual en PostgreSQL

### US-2.5: Migración Automática de Objetos Simples
**Como** miembro del equipo de migración
**Quiero** que los objetos simples se migren automáticamente
**Para** reducir el trabajo manual y acelerar el proceso

**Criterios de Aceptación:**
- [ ] Objetos clasificados como "simples" se migran sin intervención humana
- [ ] Conversiones de sintaxis aplicadas (ver [04_decisions.md](./04_decisions.md) para tabla completa)
- [ ] El código generado compila sin errores en PostgreSQL 17.4
- [ ] Se genera log de cada transformación realizada (trazabilidad)
- [ ] Tasa de éxito > 80% para objetos simples
- [ ] Se puede usar ora2pg como preprocesador (opcional)

### US-2.6: Migración Asistida de Objetos Complejos
**Como** miembro del equipo de migración
**Quiero** que los objetos complejos se migren con asistencia de IA
**Para** manejar casos que requieren decisión humana

**Criterios de Aceptación:**
- [ ] El sistema identifica objetos que requieren decisión humana
- [ ] Para cada objeto complejo, el sistema presenta:
  - Código original Oracle
  - Propuesta de código PostgreSQL
  - Lista de decisiones requeridas (ej: "¿Cómo manejar variable de estado X?")
  - Opciones con pros/contras
- [ ] El usuario puede aprobar, modificar o rechazar cada propuesta
- [ ] Las decisiones del usuario se guardan para aplicar a casos similares
- [ ] El sistema pausa automáticamente cuando requiere intervención
- [ ] La decisión se documenta para trazabilidad

**Prioridad:** Must Have

### US-2.7: Migración de Objetos DIRECTORY a AWS S3
**Como** miembro del equipo de migración
**Quiero** que el código que usa DIRECTORY objects de Oracle se migre a escribir archivos en AWS S3
**Para** preservar la funcionalidad de generación de archivos (.txt, .csv, .xlsx) desde la base de datos sin depender del sistema de archivos local

**Contexto:**
- Oracle: 8 objetos DIRECTORY que apuntan a rutas locales (`/compartidos/*`)
- Oracle PL/SQL usa UTL_FILE para escribir archivos a estos directorios
- PostgreSQL: NO soporta objetos DIRECTORY nativamente
- Solución: Escribir archivos a AWS S3 usando extensión `aws_s3` o función personalizada

**DIRECTORY objects identificados:**
1. DIR_DOC_APOYOS → /compartidos/doc_apoyos
2. DIR_DOC_COMPRAS → /compartidos/doc_compras
3. DIR_DOC_FINANZAS → /compartidos/doc_finanzas
4. DIR_DOC_FOTOS → /compartidos/doc_fotos
5. DIR_DOC_NOMINA → /compartidos/doc_nomina
6. DIR_DOC_PAPERLESS → /compartidos/doc_paperless
7. DIR_DOC_PORTAL → /compartidos/portal
8. DIR_DOC_PORTAL_CONVENIOS → /compartidos/doc_portal_convenios

**Criterios de Aceptación:**
- [ ] Sistema identifica TODOS los usos de UTL_FILE en el código PL/SQL
- [ ] Cada DIRECTORY object Oracle debe formar parte de un bucket S3 llamado `efs-veris-compartidos-dev` para desarrollo y `efs-veris-compartidos-prd` para producción. Debe haber alguna forma de configurar el nombre del bucket como entorno global para poder cambiar entre diferentes entornos
- [ ] Código PL/SQL que usa UTL_FILE se convierte a PL/pgSQL con aws_s3
- [ ] Formatos soportados: .txt (texto plano), .csv (delimitado), .xlsx (Excel)
- [ ] Configuración de credenciales AWS (IAM role o access keys) documentada
- [ ] Permisos S3 bucket configurados (write access para PostgreSQL)
- [ ] Mapeo de DIRECTORY → S3 bucket documentado en `knowledge/infrastructure/`
- [ ] Código convertido valida permisos S3 antes de escribir
- [ ] Manejo de errores: si S3 no disponible, error claro al usuario
- [ ] Log de escrituras a S3 para auditoría

**Prioridad:** Must Have

### US-2.8: Envío de Correos Electrónicos desde Base de Datos
**Como** miembro del equipo de migración
**Quiero** que el código que envía correos electrónicos desde Oracle no se migre, solamente debe migrar la estructura del procedure
**Para** preservar la estructura y que los demás procedimientos o funciones compilen sin problemas

**Contexto:**
- Oracle: Usa UTL_MAIL / UTL_SMTP para enviar emails directamente desde PL/SQL
- Aurora PostgreSQL: **NO permite conexiones salientes directas** (managed service sin acceso a red)
- Solución: no migrar la lógica de envío de emails

**Criterios de Aceptación:**
- [ ] Sistema identifica TODOS los usos de UTL_MAIL y UTL_SMTP en código PL/SQL
- [ ] Para cada caso de envío de email, se migra la estructura del procedure/function

### US-2.9: Consumo de APIs REST desde Base de Datos
**Como** miembro del equipo de migración
**Quiero** que el código que consume APIs REST usando UTL_HTTP se migre a usar AWS Lambda + wrapper functions
**Para** preservar la funcionalidad crítica de integración con servicios externos sin la cual el sistema no funciona

**Contexto:**
- **Oracle:** Usa UTL_HTTP para hacer requests HTTP a APIs REST desde PL/SQL
- **Cantidad afectada:** **> 100 objetos** (procedures/functions/packages)
- **Criticidad:** MUST HAVE - Sin esto el sistema no funciona
- **APIs:** Mixtas (algunas internas VPC, algunas externas internet público)
- **Aurora PostgreSQL:** NO soporta extensión `pgsql-http` (managed service)
- **Solución AWS:** aws_lambda + aws_commons (YA instaladas) + wrapper functions PL/pgSQL

**Estrategia:**
```
Oracle PL/SQL (UTL_HTTP)
↓
PostgreSQL PL/pgSQL (Wrapper Functions)
  ├─ utl_http.begin_request()  → Construye JSON request
  ├─ utl_http.set_header()     → Agrega headers
  ├─ utl_http.set_authentication() → Agrega auth
  ├─ utl_http.write_text()     → Agrega body
  └─ utl_http.get_response()   → Invoca Lambda → retorna respuesta
↓
AWS Lambda Function (Nodejs + Axios)
  ├─ Recibe JSON con parámetros HTTP
  ├─ Hace HTTP request real a API (REST)
  └─ Retorna respuesta a PostgreSQL
```

**Criterios de Aceptación:**
- [ ] **Fase 1 - Análisis:** Sistema identifica TODOS los usos de UTL_HTTP en código PL/SQL (> 100 objetos)
- [ ] Sistema detecta para cada uso:
  - [ ] URL destino de la API (interna VPC vs externa internet)
  - [ ] Método HTTP (GET, POST, PUT, DELETE, etc.)
  - [ ] Headers usados (Authorization, Content-Type, etc.)
  - [ ] Tipo de autenticación (Basic, Bearer, OAuth, etc.)
  - [ ] Formato request/response (JSON, XML/SOAP, form-data, etc.)
- [ ] **Fase 2 - Infraestructura:**
  - [ ] Lambda function HTTP client creada (Nodejs + Axios)
  - [ ] Lambda configurada con:
    - [ ] Timeout adecuado (mayor que APIs más lentas)
    - [ ] Memory allocation según volumen de requests
    - [ ] VPC configuration para acceder APIs internas
    - [ ] Internet access (NAT Gateway) para APIs externas
  - [ ] IAM role con permisos para invocar Lambda desde Aurora
  - [ ] Security groups configurados para Aurora → APIs
- [ ] **Fase 3 - Wrapper Functions:**
  - [ ] Wrapper functions PL/pgSQL creadas que replican API de UTL_HTTP:
    - [ ] `utl_http.begin_request(url, method)` → retorna request_id
    - [ ] `utl_http.set_header(request_id, name, value)`
    - [ ] `utl_http.set_authentication(request_id, username, password, scheme)`
    - [ ] `utl_http.write_text(request_id, data)`
    - [ ] `utl_http.get_response(request_id)` → retorna response object
    - [ ] `utl_http.read_text(response)` → retorna body
    - [ ] `utl_http.get_header(response, name)` → retorna header value
    - [ ] `utl_http.end_request(request_id)` → cleanup
  - [ ] Wrapper functions construyen JSON con todos los parámetros HTTP
  - [ ] Wrapper functions invocan Lambda vía `aws_lambda.invoke()`
  - [ ] Manejo de errores: timeout, network errors, HTTP errors (4xx, 5xx)
- [ ] **Fase 4 - Conversión de Código:**
  - [ ] Código Oracle que usa UTL_HTTP se convierte mínimamente (API compatible)
  - [ ] Conversión valida que URL/endpoints sigan siendo válidos
- [ ] **Fase 5 - Testing:**
  - [ ] Shadow testing: comparar respuestas Oracle vs PostgreSQL para mismos requests
  - [ ] Validar latencia adicional (Lambda invoke overhead)
  - [ ] Validar manejo de errores (timeouts, network failures)
  - [ ] Validar autenticación (Basic, Bearer, OAuth)
- [ ] **Documentación:**
  - [ ] Mapeo completo de UTL_HTTP → wrapper functions documentado
  - [ ] Lista de APIs consumidas catalogada en `knowledge/infrastructure/apis.md`
  - [ ] Configuración de Lambda y security groups documentada
  - [ ] Troubleshooting guide para errores comunes

**Referencias:**
- [AWS Blog - Build custom HTTP client for Aurora PostgreSQL](https://aws.amazon.com/blogs/database/build-a-custom-http-client-in-amazon-aurora-postgresql-and-amazon-rds-for-postgresql-an-alternative-to-oracles-utl_http/)
- [GitHub - aws-samples/wrapper-for-utl-http-with-amazon-aurora](https://github.com/aws-samples/wrapper-for-utl-http-with-amazon-aurora)

**Prioridad:** MUST HAVE (CRÍTICO - Sin esto el sistema no funciona)

---

## Epic 3: Validación (Must Have)

### US-3.1: Validación de Sintaxis
**Como** miembro del equipo de migración
**Quiero** validar que el código migrado compila
**Para** detectar errores de sintaxis antes de testing funcional

**Criterios de Aceptación:**
- [ ] Todo código generado se valida contra PostgreSQL 17.4
- [ ] Errores de compilación se reportan con: archivo, línea, mensaje
- [ ] Código con errores se marca para revisión
- [ ] Tasa de compilación exitosa > 95%

### US-3.2: Diseño de Testing Comparativo
**Como** QA
**Quiero** un framework para ejecutar el mismo procedure en ambas DBs
**Para** validar que el resultado es idéntico

**Criterios de Aceptación:**
- [ ] Framework permite definir casos de prueba: procedure + parámetros
- [ ] Ejecuta en Oracle y captura resultado
- [ ] Ejecuta en PostgreSQL y captura resultado
- [ ] Compara resultados automáticamente
- [ ] Reporta diferencias claramente (valores, tipos, orden)
- [ ] Soporta comparación de:
  - Valores escalares
  - Resultsets (cursores)
  - Efectos secundarios (inserts/updates)

### US-3.3: Shadow Testing
**Como** QA
**Quiero** ejecutar shadow testing automatizado
**Para** validar comportamiento idéntico a escala

**Criterios de Aceptación:**
- [ ] Se puede configurar lista de procedures a validar
- [ ] Usa datos de prueba existentes (ya migrados a PostgreSQL)
- [ ] Ejecuta batch de comparaciones
- [ ] Genera reporte de validación por objeto:
  - PASS: Resultados idénticos
  - FAIL: Diferencias detectadas (con detalle)
  - SKIP: No se pudo ejecutar (con razón)
- [ ] Porcentaje de PASS > 95% antes de ir a producción

**Prioridad:** Must Have

---

## Epic 4: Migración de Backend (Should Have)

**Nota:** Esta fase se ejecuta DESPUÉS de completar la migración de base de datos.

### US-4.1: Escaneo de Proyectos Backend
**Como** miembro del equipo de migración
**Quiero** escanear los 30 proyectos backend
**Para** identificar todo el código que interactúa con Oracle

**Criterios de Aceptación:**
- [ ] El sistema detecta configuraciones de conexión Oracle:
  - jdbc:oracle URLs
  - Connection strings en config files
  - Environment variables
- [ ] El sistema identifica llamadas a stored procedures
- [ ] El sistema encuentra queries SQL nativas (raw queries)
- [ ] El sistema detecta uso de tipos Oracle específicos en ORMs
- [ ] Se genera reporte por proyecto con hallazgos

### US-4.2: Actualización de Configuraciones ORM
**Como** desarrollador
**Quiero** que las configuraciones de ORM se actualicen a PostgreSQL
**Para** que los proyectos conecten a la nueva base de datos

**Criterios de Aceptación:**
- [ ] Hibernate: dialecto Oracle → PostgreSQL, driver actualizado
- [ ] Spring Data JPA: driver y URL actualizados
- [ ] TypeORM: type: "oracle" → type: "postgres", configuración de conexión
- [ ] SQLAlchemy: engine URL oracle:// → postgresql://
- [ ] Se preservan configuraciones de connection pooling (HikariCP)
- [ ] Se genera diff de cambios para revisión

### US-4.3: Conversión de Queries SQL Nativas
**Como** desarrollador
**Quiero** que los queries SQL nativos se conviertan a sintaxis PostgreSQL
**Para** que funcionen con la nueva base de datos

**Criterios de Aceptación:**
- [ ] Mismas conversiones de sintaxis que US-2.5
- [ ] Llamadas a stored procedures actualizan nombre de schema
- [ ] Ejemplo: CALL PKG_VENTAS.PROCESAR() → CALL pkg_ventas.procesar()
- [ ] Se genera lista de queries que requieren revisión manual
- [ ] Se preservan prepared statements y parámetros

### US-4.4: Validación de Backend
**Como** QA
**Quiero** validar que el backend funciona con PostgreSQL
**Para** asegurar que la migración fue exitosa

**Criterios de Aceptación:**
- [ ] El proyecto compila/transpila sin errores
- [ ] Los tests existentes pasan (si hay tests)
- [ ] Endpoints que usan stored procedures funcionan
- [ ] Queries nativas retornan resultados correctos

**Prioridad:** Should Have

---

**Ver también:**
- [00_index.md](./00_index.md) - Resumen ejecutivo completo
- [01_problem_statement.md](./01_problem_statement.md) - Problema y objetivos
- [03_architecture.md](./03_architecture.md) - Diseño técnico del sistema
- [04_decisions.md](./04_decisions.md) - Decisiones técnicas clave
