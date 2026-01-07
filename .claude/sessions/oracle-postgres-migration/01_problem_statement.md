# Problem Statement - Oracle to PostgreSQL Migration

> **📖 Contexto del Proyecto:** Herramienta basada en agentes IA para migrar 8,122 objetos PL/SQL de Oracle 19c a PostgreSQL 17.4 (Amazon Aurora) en 3 meses, con captura de conocimiento empresarial para uso futuro por agentes IA. Ver [00_index.md](./00_index.md) para resumen ejecutivo completo.

**Versión:** 2.2 | **Fecha:** 2025-12-31 | **Estado:** validated

---

## 1. Initial Request

El usuario necesita una herramienta basada en agentes de IA para migrar:
1. Código PL/SQL (Oracle 19c) a PL/pgSQL (PostgreSQL 17.4)
2. Código backend (Java, JavaScript, TypeScript, Python) que usa conexiones/ORMs de Oracle

---

## 2. Problem Statement (5W1H)

### Why - El Problema Real

**Motivación principal:** Costos de licenciamiento de Oracle son prohibitivos.

**Volumen a migrar:**
- FUNCTION: 146 objetos
- PACKAGE BODY: 569 objetos
- PROCEDURE: 196 objetos
- TRIGGER: 87 objetos
- **Total de objetos PL/SQL: 8,122** (contando procedures y functions dentro de packages)
- **Proyectos backend: ~30** (Java, Node.js, TypeScript, Python)

**Intentos previos:** Ninguno. Esta es la primera migración.

### What - Resultado Esperado

1. **Código migrado listo para producción** (objetos simples)
2. **Código migrado que requiere revisión humana** (objetos complejos)
3. **Reportes de compatibilidad** con sugerencias
4. **Trazabilidad completa** de todas las acciones realizadas
5. **Base de conocimiento** con reglas de negocio extraídas para uso futuro por agentes IA

### Who - Usuarios y Roles

| Rol | Descripción | Necesidades |
|-----|-------------|-------------|
| **Equipo de migración** | Equipo dedicado a ejecutar la migración | Automatización máxima, reportes claros, capacidad de reanudar |
| **Desarrolladores senior** | Entienden Oracle y PostgreSQL | Revisión de objetos complejos, validación de conversiones |
| **Arquitectos** | Diseño de sistema destino | Documentación de conocimiento, flujos de proceso |

**Alcance:** Herramienta interna primero, luego para clientes.

### When - Contexto de Uso

- **Uso:** Una vez para migrar todo, si todo funciona excelente se podría utilizar como herramienta para empresas que tengan la misma necesidad
- **Timeline:** 3 meses
- **Oracle en paralelo:** Sí, seguirá activo durante la migración

### Where - Ubicación en Sistema

**Entorno de ejecución:**
1. **Claude Code CLI** - Máquina local para tareas específicas
2. **Claude Code Web** - Ejecución en background para procesamiento masivo
3. **Repositorios:** AWS CodeCommit (después de completar la migración de objetos de BD)

**Arquitectura de ejecución:**
- Debe manejar/controlar límites de tokens automáticamente en claude code cli y claude code web
- Reanudar trabajo cuando se restablezcan los tokens
- Solo pausar cuando requiera intervención humana (con log del motivo)

### How - Visión de Funcionamiento

**Flujo en 5 fases:**
1. **Escaneo inicial** de todos los objetos Oracle
2. **Análisis profundo** del comportamiento de cada objeto
3. **Captura de conocimiento** en base de datos vectorial (pgvector)
4. **Migración** automática/asistida según complejidad
5. **Validación** con shadow testing

---

## 3. Jobs-to-be-Done

### Job Principal (job de conocimiento)
Cuando **analizo el código PL/SQL**,
Quiero **extraer las reglas de negocio, validaciones y flujos de proceso e identificar complejidad del objeto**,
Para **preservar el conocimiento empresarial y alimentar futuros agentes IA**.

### Job de Migración
Cuando **tengo aproximadamente 8,122 objetos PL/SQL en Oracle que deben funcionar en PostgreSQL**,
Quiero **una herramienta que los convierta automáticamente cuando sea posible y me asista cuando sea complejo**,
Para **completar la migración en 3 meses sin perder funcionalidad ni conocimiento de negocio**.

### Job Secundario
Cuando **tengo 30 proyectos backend que usan Oracle**,
Quiero **que se actualicen para usar PostgreSQL**,
Para **que funcionen con la nueva base de datos sin cambios manuales extensivos**.

---

## 4. Scope Definition

### In Scope

- [x] Migración de 8,122 objetos PL/SQL (Oracle 19c → PostgreSQL 17.4)
- [x] Conversión de packages a schemas con funciones
- [x] Manejo de variables de estado vía session variables
- [x] Manejo de AUTONOMOUS_TRANSACTION (~40 objetos)
- [x] Manejo de AUTHID CURRENT_USER
- [x] Migración de +8 objetos DIRECTORY a AWS S3 (UTL_FILE → aws_s3)
- [x] Generación de archivos (.txt, .csv, .xlsx) en S3 desde PostgreSQL (evaluar codigo plsql para identificar)
- [x] **Migración de consumo de APIs REST (< 100 objetos con UTL_HTTP → Lambda + wrapper functions)**
- [x] Captura de conocimiento en Markdown + pgvector
- [x] Logging completo y trazabilidad
- [x] Manejo de límites de tokens de claude code cli y claude code web (reanudación automática)
- [x] Shadow testing para validación
- [x] Migración de ~30 proyectos backend (Java, Node.js, TypeScript, Python)
- [x] Integración con ora2pg como preprocesador inicial

### Out of Scope

- [ ] **Agentes de diagnóstico/troubleshooting** - Proyecto separado posterior
- [ ] **Migración de datos** - Ya se han migrado ciertos datos, usar pgLoader si se necesita más
- [ ] **Cambios en la arquitectura de aplicaciones** - Solo conversión, no rediseño
- [ ] **Creación de tests unitarios** - No existen actualmente, no se crearán
- [ ] **Soporte para múltiples versiones de Oracle** - Solo Oracle 19c
- [ ] **Soporte para múltiples versiones de PostgreSQL** - Solo PostgreSQL 17.4

### Assumptions

1. **ora2pg se ejecuta localmente** - Claude Code Web no puede ejecutar ora2pg directamente
2. **Los archivos de código están en repositorios Git** - Accesibles desde Claude Code
3. **Hay acceso a base de datos de prueba** - Para shadow testing
4. **Oracle seguirá activo 3 meses** - Para comparaciones y rollback
5. **El equipo puede tomar decisiones** - Para objetos complejos que requieren intervención
6. **pgvector está disponible en Aurora PostgreSQL** - Extensión pre-compilada por AWS
7. **AWS S3 bucket disponible** - Para almacenar archivos generados desde PostgreSQL
8. **Extensión aws_s3 habilitada** - Nativa en Aurora PostgreSQL (pre-instalada)
9. **Credenciales AWS configuradas** - IAM role o access keys para Aurora→S3

### Constraints

**1. Amazon Aurora PostgreSQL 17.4 - Managed Service (CRÍTICO)**
   - ❌ **NO hay acceso root al servidor** - No se puede modificar postgresql.conf directamente
   - ❌ **NO hay acceso al filesystem del servidor** - No se puede escribir archivos locales
   - ❌ **Solo extensiones pre-compiladas por AWS** - No se puede compilar/instalar extensiones custom
   - ❌ **NO se puede usar COPY TO PROGRAM** - Comandos que requieren shell no funcionan
   - ✅ **Extensiones disponibles:** aws_s3, aws_commons, pgvector (verificar disponibilidad)
   - ✅ **Configuración vía Parameter Groups** - Cambios limitados a parámetros permitidos por AWS
   - ⚠️ **dblink puede tener restricciones** - Verificar si está disponible y sus limitaciones

**2. Timeline: 3 meses** - Fecha límite no negociable

**3. Límites de tokens de Claude** - Requiere manejo automático de reanudación

**4. Sin tests unitarios existentes** - Validación vía shadow testing

**5. Complejidad de packages** - 569 packages con variables de estado y dependencias

**6. Código Legacy de 10+ Años (CRÍTICO para Estrategia de Análisis)**
   - ⚠️ **Código evolutivo:** 10+ años de desarrollo continuo sin refactorización completa
   - ⚠️ **Múltiples niveles de experiencia:** Programado por juniors, seniors y expertos
   - ⚠️ **Calidad variable esperada:**
     - Lógica redundante (código duplicado, validaciones repetidas)
     - Lógica confusa (sin documentación, nombres poco claros, flujos complejos)
     - Lógica sin sentido aparente (workarounds, parches históricos)
     - Lógica avanzada (optimizaciones complejas, algoritmos sofisticados)
   - ⚠️ **Inconsistencias de estilo:** Diferentes convenciones de nombres, estructuras, patrones
   - ⚠️ **Deuda técnica acumulada:** Workarounds que se volvieron permanentes, parches sobre parches
   - ⚠️ **Conocimiento tribal perdido:** Algunos autores originales ya no están en la empresa
   - ✅ **Implicación para sub-agentes:**
     - Code Comprehension Agent debe interpretar sin asumir calidad consistente
     - Migration Strategist debe marcar código confuso como COMPLEX (requiere revisión humana)
     - Documentación de conocimiento es CRÍTICA (preservar lógica antes de que se pierda)

**7. Features Oracle Críticas NO Documentadas Inicialmente (ALTO IMPACTO - Detectadas Post-Discovery)**

   **⚠️ ESTADO:** PENDIENTE - Requiere análisis detallado post-scan de Code Comprehension Agent

   **7.1 DBMS_SQL (SQL Dinámico Nativo Oracle)**
   - 🔍 **Cantidad estimada:** < 20 objetos (confirmación pendiente en Fase 1)
   - ⚠️ **Impacto:** MEDIO-ALTO
   - 🔧 **Conversión PostgreSQL:** EXECUTE + format() / EXECUTE USING
   - 📊 **Uso detectado:** Motor de evaluación de fórmulas dinámicas (ej: RHH_K_ADMINISTRA_FORMULA)
   - ⚙️ **Métodos Oracle usados:**
     - `DBMS_SQL.OPEN_CURSOR` → Crear cursor dinámico
     - `DBMS_SQL.PARSE` → Analizar SQL statement
     - `DBMS_SQL.BIND_VARIABLE` → Asociar variables a SQL
     - `DBMS_SQL.EXECUTE` → Ejecutar statement
     - `DBMS_SQL.VARIABLE_VALUE` → Leer valor de variable OUT
     - `DBMS_SQL.CLOSE_CURSOR` → Cerrar cursor
   - ✅ **Estrategia:** Decision 8 (DEFERRED - post-scan)
   - 🎯 **Ejemplo real:** Package RHH_K_ADMINISTRA_FORMULA evalúa fórmulas matemáticas dinámicas almacenadas como strings

   **7.2 Tipos Colección (TABLE OF, VARRAY, OBJECT TYPES)**
   - 🔍 **Tipos usados:** TODOS (confirmación de volumetría pendiente)
     - `TABLE OF ... INDEX BY` - Asociative arrays / hash maps
     - `TABLE OF ...` - Nested tables
     - `VARRAY` - Arrays de tamaño variable
     - `OBJECT TYPES` - Tipos personalizados complejos
   - ⚠️ **Impacto:** ALTO (afecta arquitectura de conversión)
   - 🔧 **Conversión PostgreSQL:**
     - `TABLE OF INDEX BY` → Arrays `tipo[]` o `hstore`
     - `TABLE OF` → Arrays `tipo[]`
     - `VARRAY` → Arrays `tipo[]` con límite
     - `OBJECT TYPES` → Composite Types o JSON
   - ✅ **Estrategia:** Decision 9 (DEFERRED - post-scan)
   - 🎯 **Ejemplo real:** `TYPE T_Gt_Variables IS TABLE OF Varchar2(61) INDEX BY BINARY_INTEGER;`

   **7.3 Configuraciones NLS (Sesión Oracle - ALTER SESSION)**
   - 🔍 **Configuraciones detectadas:** TODAS (confirmación de uso real pendiente)
     - `NLS_NUMERIC_CHARACTERS` - Formato decimal: "," vs "."
     - `NLS_DATE_FORMAT` - Formato de fechas
     - `NLS_LANGUAGE` - Idioma de mensajes
     - Otras configuraciones NLS
   - ⚠️ **Impacto:** MEDIO (afecta comportamiento en runtime)
   - 🔧 **Conversión PostgreSQL:**
     - `ALTER SESSION SET NLS_NUMERIC_CHARACTERS='.,''` → `SET lc_numeric = 'es_ES.UTF-8'`
     - `NLS_DATE_FORMAT` → `SET datestyle = 'ISO, DMY'`
     - `NLS_LANGUAGE` → `SET lc_messages = 'es_ES.UTF-8'`
   - ✅ **Estrategia:** Incluir en conversión automática (validación per-object)
   - 🎯 **Ejemplo real:** `EXECUTE IMMEDIATE 'ALTER SESSION SET NLS_NUMERIC_CHARACTERS=''.,''';`

   **7.4 Motor de Evaluación de Fórmulas Dinámicas**
   - 🔍 **Packages críticos detectados:** RHH_K_ADMINISTRA_FORMULA (+ otros pendientes)
   - 📝 **Funcionalidad:** Evalúa expresiones matemáticas con variables/funciones en runtime
   - 🎯 **Ejemplo de uso:**
     ```sql
     -- Expresión almacenada como string: "RHH_F_SUELDO / 30 + 15"
     -- Sistema Oracle:
     --   1. Ejecuta RHH_F_SUELDO (obtiene valor numérico)
     --   2. Evalúa: valor / 30 + 15
     --   3. Retorna resultado final
     ```
   - ⚠️ **Impacto:** ALTO (lógica de negocio crítica en sistemas de nómina)
   - 🔧 **Opciones de conversión PostgreSQL:**
     - **Opción A (Preferida):** EXECUTE + format() nativo PL/pgSQL
     - **Opción B:** Parser seguro con validación explícita
     - **Opción C (Futura):** AWS Lambda + Python AST (sandbox aislado)
   - ✅ **Estrategia:** Decision 10 (DEFERRED - post-scan)
   - 📊 **Decisión final:** Se tomará después del scan basado en:
     - Cantidad real de packages que usan este patrón
     - Complejidad de las expresiones
     - Frecuencia de uso en producción

   **🎯 Plan de Acción:**
   1. ✅ Documentar en discovery (COMPLETADO)
   2. ⏳ Actualizar Code Comprehension Agent para detectar estos patterns (Fase 1)
   3. ⏳ Ejecutar scan completo de 8,122 objetos (Fase 1)
   4. ⏳ Analizar estadísticas reales generadas
   5. ⏳ Tomar decisiones técnicas definitivas (Decisions 8, 9, 10)
   6. ⏳ Implementar estrategias de conversión

---

## 5. Success Metrics

### Quantitative

| Métrica | Target | Medición |
|---------|--------|----------|
| Objetos migrados exitosamente | > 95% | (objetos que compilan / total) * 100 |
| Tasa de migración automática | > 70% | (objetos sin intervención / total) * 100 |
| Shadow testing pass rate | > 95% | (tests passed / tests run) * 100 |
| Tiempo total de migración | <= 3 meses | Fecha inicio a fecha fin |
| Objetos por día | > 100/día | Total objetos / días trabajados |
| Conocimiento capturado | 100% | (objetos documentados / total) * 100 |

### Qualitative

| Métrica | Target | Validación |
|---------|--------|------------|
| Trazabilidad | Completa | Cada acción tiene log con timestamp y razón |
| Documentación de conocimiento | Clara | Equipo puede buscar y entender reglas de negocio |
| Proceso reproducible | Sí | Otro equipo podría seguir el mismo proceso |
| Intervención humana mínima | Solo cuando necesario | < 30% de objetos requieren decisión manual |

---

## 6. Dependencies & Risks

### Dependencies

| Dependencia | Owner | Status |
|-------------|-------|--------|
| Acceso a Oracle 19c (lectura) | DBA Team | ✅ **Disponible** |
| **Amazon Aurora PostgreSQL 17.4** | Infra Team | ✅ **Disponible (managed)** |
| ~~Validar extensiones Aurora disponibles~~ | DBA/Infra Team | ✅ **COMPLETADO - Ver tabla abajo** |
| Extensión vector 0.8.0 habilitada en Aurora | DBA Team | ✅ **COMPLETADO** |
| Extensión aws_s3 1.2 | DBA Team | ✅ **Instalada y lista** |
| Extensión aws_commons 1.2 | DBA Team | ✅ **Instalada y lista** |
| Extensión dblink 1.2 | DBA Team | ✅ **Instalada y lista** |
| Extensión aws_lambda 1.0 | DBA Team | ✅ **Instalada y lista** |
| Extensión pg_cron 1.6 (opcional) | DBA Team | ⚠️ **Disponible - Falta ejecutar CREATE EXTENSION** |
| **Bucket S3: `efs-veris-compartidos-dev` (us-east-1)** | DevOps/Infra | ✅ **COMPLETADO** |
| **AWS Lambda para conversión CSV → XLSX** | DevOps | ⚠️ **CRÍTICO - Requerido para archivos Excel** |
| S3 Event Notification → Lambda trigger | DevOps | ⚠️ Configurar después de crear Lambda |
| **AWS Lambda HTTP client (Python + Requests)** | DevOps | ⚠️ **CRÍTICO - > 100 objetos UTL_HTTP** |
| **Wrapper functions PL/pgSQL para UTL_HTTP API** | Migration Team | ⚠️ **CRÍTICO - Replicar API Oracle** |
| Lambda VPC configuration (APIs internas) | DevOps/Network | Pendiente configurar |
| Lambda Internet access (NAT Gateway para APIs externas) | DevOps/Network | Pendiente configurar |
| Security groups Aurora → APIs (internas + externas) | DevOps/Network | Pendiente configurar |
| IAM role/credentials para Aurora→S3 | DevOps/Security | Pendiente configurar |
| IAM role para Aurora invoke Lambda | DevOps/Security | Pendiente configurar |
| Repositorios en AWS CodeCommit | DevOps | Disponible |
| Datos de prueba migrados | Data Team | Parcialmente migrado |
| ora2pg instalado localmente | Migration Team | ✅ **Disponible** |

**Validación de Extensiones Aurora (COMPLETADA ✅):**

| Extensión | Versión | Estado | Uso en Proyecto |
|-----------|---------|--------|-----------------|
| **aws_s3** | 1.2 | ✅ Instalada | DIRECTORY → S3 (CRÍTICO) |
| **aws_commons** | 1.2 | ✅ Instalada | Soporte para aws_s3 (CRÍTICO) |
| **dblink** | 1.2 | ✅ Instalada | AUTONOMOUS_TRANSACTION Opción B |
| **aws_lambda** | 1.0 | ✅ Instalada | AUTONOMOUS_TRANSACTION Opción C |
| **vector** | 0.8.0 | ✅ Instalada | Base de conocimiento (pgvector) |

### Risks

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Timeline de 3 meses insuficiente | Media | Alto | Priorizar objetos críticos, paralelizar con sub-agentes |
| Variables de estado en packages dificultan migración | Alta | Alto | Session variables (ya decidido), documentar cada caso |
| AUTONOMOUS_TRANSACTION no funciona igual con dblink | Media | Medio | Probar primero con objetos menos críticos |
| Límites de tokens frenan progreso | Alta | Medio | Reanudación automática, checkpoints frecuentes |
| Diferencias sutiles en comportamiento numérico | Media | Alto | Shadow testing exhaustivo, documentar diferencias |
| NUMBER con precisión > 1000 no soportado | Baja | Alto | Investigar si realmente se usa, alternativas |
| DIRECTORY→S3: latencia mayor afecta performance | Media | Medio | Medir latencia real, optimizar batch writes, usar pre-signed URLs |
| Generación de archivos Excel (.xlsx) requiere Lambda | Media | Medio | ✅ **Estrategia definida:** PostgreSQL→CSV→S3→Lambda→XLSX (Opción A) |
| Lambda para Excel: lógica Oracle compleja difícil de replicar | Media | Medio | Analizar código Oracle en Fase 1, determinar si usa formato avanzado (múltiples hojas, fórmulas) |
| **< 100 objetos con UTL_HTTP aumentan complejidad** | **Alta** | **Alto** | ✅ **Estrategia definida:** Lambda + wrapper functions (AWS oficial). Fase 1 identificará volumen exacto |
| **Latencia Lambda afecta performance de llamadas API** | Media | Medio | Medir overhead Lambda invoke, optimizar timeout/memory, considerar Lambda SnapStart |
| **Conversión UTL_HTTP no es 1:1 (wrapper API diferente)** | Media | Alto | Wrapper functions replicarán API UTL_HTTP lo más posible, shadow testing para validar comportamiento |
| **APIs externas pueden estar bloqueadas por firewall/WAF** | Media | Alto | Identificar todas las APIs en Fase 1, validar accesibilidad desde Aurora VPC, coordinar con equipos de red |
| Aurora: Restricciones managed service bloquean soluciones técnicas | Baja | Bajo | ✅ **MITIGADO - Extensiones aws_s3/dblink/aws_lambda confirman viabilidad** |

---

**Ver también:**
- [00_index.md](./00_index.md) - Resumen ejecutivo completo
- [02_user_stories.md](./02_user_stories.md) - User Stories detalladas por Epic
- [03_architecture.md](./03_architecture.md) - Diseño técnico del sistema
- [04_decisions.md](./04_decisions.md) - Decisiones técnicas clave
