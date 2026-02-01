#!/usr/bin/env python3
"""
Script para construir dependency graph y migration order óptimo (Topological Sort).

PROPÓSITO:
    Analiza dependencias entre 8,122 objetos PL/SQL extraídos por plsql-analyzer (Fase 1)
    y genera un orden de conversión óptimo usando Kahn's algorithm con detección de niveles.

BENEFICIOS:
    ✅ Compilación en orden correcto (reduce errores de dependencia)
    ✅ Detección temprana de circular dependencies
    ✅ Conversión en paralelo por niveles (objetos independientes)
    ✅ Forward declaration strategy automática para circular deps

ENTRADA:
    - knowledge/json/batch_XXX/*.json (todos los análisis de plsql-analyzer)
    - sql/extracted/manifest.json (manifest actual)

SALIDA:
    - dependency_graph.json (grafo completo con adjacency list)
    - migration_order.json (orden topológico por niveles)
    - manifest.json actualizado (nuevos campos: migration_order, dependency_level, depends_on, depended_by)

USO:
    cd /path/to/phantomx-nexus
    python scripts/build_dependency_graph.py [--dry-run]

ALGORITMO:
    Kahn's Topological Sort O(V + E) con detección de niveles
    V = 8,122 objetos
    E = ~20,000 dependencias (estimado)

VERSIÓN: 1.0.0
FECHA: 2026-01-31
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime
from collections import defaultdict, deque


# Configuración
BASE_DIR = Path.cwd()
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
JSON_DIR = KNOWLEDGE_DIR / "json"
MANIFEST_FILE = BASE_DIR / "sql" / "extracted" / "manifest.json"
DEPENDENCY_GRAPH_FILE = BASE_DIR / "dependency_graph.json"
MIGRATION_ORDER_FILE = BASE_DIR / "migration_order.json"


def load_all_dependencies() -> Dict[str, Dict]:
    """
    Lee dependencies de todos los JSONs en knowledge/json/batch_XXX/*.

    Returns:
        Dict mapeando object_id -> objeto completo con dependencies
    """
    print("\n📖 Cargando dependencias desde knowledge/json/...\n")

    if not JSON_DIR.exists():
        print(f"❌ Error: {JSON_DIR} no existe")
        print("   Ejecuta Fase 1 (plsql-analyzer) primero")
        sys.exit(1)

    all_objects = {}
    batch_dirs = sorted([d for d in JSON_DIR.iterdir() if d.is_dir() and d.name.startswith("batch_")])

    if not batch_dirs:
        print(f"❌ Error: No se encontraron directorios batch_XXX en {JSON_DIR}")
        sys.exit(1)

    print(f"   Encontrados {len(batch_dirs)} batches")

    for batch_dir in batch_dirs:
        json_files = list(batch_dir.glob("*.json"))
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    obj_data = json.load(f)

                object_id = obj_data.get("object_id")
                if not object_id:
                    print(f"   ⚠️  {json_file.name}: Sin object_id, skip")
                    continue

                # Extraer dependencias de executable_objects
                dependencies = obj_data.get("dependencies", {})
                executable_deps = dependencies.get("executable_objects", [])

                all_objects[object_id] = {
                    "object_id": object_id,
                    "object_name": obj_data.get("object_name", "UNKNOWN"),
                    "object_type": obj_data.get("object_type", "UNKNOWN"),
                    "depends_on": executable_deps  # Lista de nombres de objetos (no IDs)
                }

            except Exception as e:
                print(f"   ⚠️  Error leyendo {json_file.name}: {e}")
                continue

    print(f"   ✅ Cargados {len(all_objects)} objetos con dependencias\n")
    return all_objects


def resolve_dependency_names_to_ids(objects: Dict[str, Dict], manifest_objects: List[Dict]) -> Dict[str, List[str]]:
    """
    Resuelve nombres de dependencias a object_ids usando el manifest.

    Args:
        objects: Dict de objetos cargados (object_id -> data)
        manifest_objects: Lista de objetos del manifest con object_id y object_name

    Returns:
        Dict mapeando object_id -> [lista de object_ids que depende]
    """
    print("🔗 Resolviendo nombres de dependencias a object_ids...\n")

    # Crear índice: object_name -> object_id
    name_to_id = {}
    for obj in manifest_objects:
        obj_name = obj["object_name"].upper()
        obj_id = obj["object_id"]
        name_to_id[obj_name] = obj_id

    resolved_dependencies = {}
    unresolved_count = 0
    external_deps = set()

    for object_id, obj_data in objects.items():
        dep_names = obj_data.get("depends_on", [])
        resolved_deps = []

        for dep_name in dep_names:
            dep_name_upper = dep_name.upper()

            # Intentar resolver el nombre a un ID
            if dep_name_upper in name_to_id:
                resolved_deps.append(name_to_id[dep_name_upper])
            else:
                # Dependencia externa (no en nuestro manifest)
                external_deps.add(dep_name_upper)
                unresolved_count += 1

        resolved_dependencies[object_id] = resolved_deps

    print(f"   ✅ Dependencias resueltas")
    print(f"   📊 {unresolved_count} dependencias externas (no en manifest)")
    if external_deps:
        print(f"      Ejemplos: {', '.join(list(external_deps)[:5])}")
        if len(external_deps) > 5:
            print(f"      ... y {len(external_deps) - 5} más")
    print()

    return resolved_dependencies


def build_adjacency_list(objects: Dict[str, Dict], resolved_deps: Dict[str, List[str]]) -> Tuple[Dict, Dict]:
    """
    Construye grafo dirigido desde dependencias.

    Args:
        objects: Dict de objetos (object_id -> data)
        resolved_deps: Dict de dependencias resueltas (object_id -> [dep_ids])

    Returns:
        Tupla (adj_list, reverse_adj_list)
        - adj_list[A] = [B, C] significa "A depende de B y C"
        - reverse_adj_list[B] = [A, D] significa "B es dependido por A y D"
    """
    print("🔧 Construyendo adjacency list...\n")

    adj_list = defaultdict(list)
    reverse_adj_list = defaultdict(list)

    for object_id in objects.keys():
        deps = resolved_deps.get(object_id, [])
        adj_list[object_id] = deps

        for dep_id in deps:
            reverse_adj_list[dep_id].append(object_id)

    total_edges = sum(len(deps) for deps in adj_list.values())

    print(f"   ✅ Grafo construido")
    print(f"   📊 Nodos (objetos): {len(objects)}")
    print(f"   📊 Aristas (dependencias): {total_edges}\n")

    return dict(adj_list), dict(reverse_adj_list)


def topological_sort_with_levels(nodes: List[str], adj_list: Dict[str, List[str]]) -> Tuple[List[List[str]], List[str]]:
    """
    Kahn's algorithm adaptado para retornar niveles de dependencia.

    Args:
        nodes: Lista de object_ids
        adj_list: Adjacency list (object_id -> [dep_ids])

    Returns:
        Tupla (levels, circular)
        - levels: Lista de niveles [[obj_0001, obj_0005], [obj_0010], ...]
        - circular: Lista de object_ids en dependencias circulares
    """
    print("🔄 Aplicando Kahn's Topological Sort...\n")

    # 1. Construir in-degree map (cuántas dependencias tiene cada nodo)
    in_degree = {node: 0 for node in nodes}
    reverse_adj = defaultdict(list)

    for node in nodes:
        deps = adj_list.get(node, [])
        for dep in deps:
            if dep in in_degree:  # Solo contar deps dentro del manifest
                reverse_adj[dep].append(node)
                in_degree[node] += 1

    # 2. Cola con nodos sin dependencias (in-degree = 0)
    queue = deque([node for node in nodes if in_degree[node] == 0])
    levels = []
    processed = set()

    print(f"   🎯 Nivel 0 (sin dependencias): {len(queue)} objetos")

    # 3. Procesar por niveles
    level_num = 0
    while queue:
        current_level = list(queue)
        levels.append(current_level)
        queue.clear()

        for node in current_level:
            processed.add(node)

            # Reducir in-degree de vecinos
            for neighbor in reverse_adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if queue:
            level_num += 1
            print(f"   🎯 Nivel {level_num}: {len(queue)} objetos")

    # 4. Detectar circular dependencies (nodos no procesados)
    circular = [node for node in nodes if node not in processed]

    print(f"\n   ✅ Topological sort completado")
    print(f"   📊 Total niveles: {len(levels)}")
    print(f"   📊 Objetos procesados: {len(processed)}")
    print(f"   ⚠️  Circular dependencies: {len(circular)}\n")

    return levels, circular


def detect_circular_groups(circular_nodes: List[str], adj_list: Dict[str, List[str]], objects: Dict[str, Dict]) -> List[Dict]:
    """
    Detecta grupos de dependencias circulares usando DFS.

    Args:
        circular_nodes: Lista de object_ids en dependencias circulares
        adj_list: Adjacency list
        objects: Dict de objetos

    Returns:
        Lista de grupos de dependencias circulares con descripción
    """
    if not circular_nodes:
        return []

    print("🔍 Detectando grupos de circular dependencies...\n")

    visited = set()
    groups = []

    def dfs(node, current_group):
        if node in visited:
            return
        visited.add(node)
        current_group.append(node)

        # Visitar dependencias
        for dep in adj_list.get(node, []):
            if dep in circular_nodes:
                dfs(dep, current_group)

    for node in circular_nodes:
        if node not in visited:
            current_group = []
            dfs(node, current_group)
            if current_group:
                # Generar descripción
                obj_names = [objects[obj_id]["object_name"] for obj_id in current_group[:3]]
                description = f"{', '.join(obj_names)}"
                if len(current_group) > 3:
                    description += f" (y {len(current_group) - 3} más)"

                groups.append({
                    "group_id": len(groups) + 1,
                    "size": len(current_group),
                    "objects": current_group,
                    "description": description
                })

    print(f"   ✅ Detectados {len(groups)} grupos circulares\n")
    return groups


def generate_dependency_graph(objects: Dict[str, Dict], adj_list: Dict[str, List[str]],
                               reverse_adj_list: Dict[str, List[str]], circular_groups: List[Dict]) -> Dict:
    """
    Genera dependency_graph.json (grafo completo).

    Returns:
        Dict con estructura completa del grafo
    """
    print("📝 Generando dependency_graph.json...\n")

    graph = {}
    for object_id, obj_data in objects.items():
        graph[object_id] = {
            "object_name": obj_data["object_name"],
            "object_type": obj_data["object_type"],
            "depends_on": adj_list.get(object_id, []),
            "depended_by": reverse_adj_list.get(object_id, [])
        }

    total_deps = sum(len(v["depends_on"]) for v in graph.values())

    dependency_graph = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "total_objects": len(objects),
        "total_dependencies": total_deps,
        "circular_dependencies_detected": sum(g["size"] for g in circular_groups),
        "circular_groups_count": len(circular_groups),
        "graph": graph,
        "circular_groups": circular_groups
    }

    print(f"   ✅ Dependency graph generado\n")
    return dependency_graph


def generate_migration_order(levels: List[List[str]], circular_nodes: List[str],
                              objects: Dict[str, Dict], circular_groups: List[Dict]) -> Dict:
    """
    Genera migration_order.json (orden topológico por niveles).

    Returns:
        Dict con orden de migración óptimo
    """
    print("📝 Generando migration_order.json...\n")

    levels_info = []
    total_in_levels = 0

    for level_num, level_objects in enumerate(levels):
        total_in_levels += len(level_objects)
        description = "Sin dependencias - pueden convertirse en paralelo" if level_num == 0 else \
                      f"Dependen solo de niveles 0-{level_num - 1}"

        levels_info.append({
            "level": level_num,
            "count": len(level_objects),
            "description": description,
            "objects": level_objects
        })

    # Agregar circular dependencies como último nivel especial
    if circular_nodes:
        levels_info.append({
            "level": len(levels),
            "count": len(circular_nodes),
            "description": "Circular dependencies - requieren forward declarations",
            "objects": circular_nodes,
            "is_circular": True
        })

    # Generar lista de circular dependencies con resolución
    circular_deps_info = []
    for node in circular_nodes:
        obj_data = objects[node]
        # Encontrar grupo al que pertenece
        group_id = None
        for group in circular_groups:
            if node in group["objects"]:
                group_id = group["group_id"]
                break

        circular_deps_info.append({
            "object_id": node,
            "object_name": obj_data["object_name"],
            "object_type": obj_data["object_type"],
            "circular_group": group_id,
            "resolution_strategy": "forward_declaration_required"
        })

    migration_order = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "total_levels": len(levels_info),
        "total_objects": len(objects),
        "objects_in_topological_order": total_in_levels,
        "circular_dependencies_count": len(circular_nodes),
        "levels": levels_info,
        "circular_dependencies": circular_deps_info
    }

    print(f"   ✅ Migration order generado\n")
    return migration_order


def update_manifest(manifest_path: Path, objects: Dict[str, Dict], adj_list: Dict[str, List[str]],
                    reverse_adj_list: Dict[str, List[str]], levels: List[List[str]],
                    circular_nodes: List[str], dry_run: bool = False) -> None:
    """
    Actualiza manifest.json con campos nuevos de dependency resolution.

    Nuevos campos agregados a cada objeto:
        - migration_order: Orden topológico (1, 2, 3, ...)
        - dependency_level: Nivel en el grafo (0=sin deps, 1=depende de nivel 0, ...)
        - depends_on: [object_ids] que este objeto depende
        - depended_by: [object_ids] que dependen de este objeto
    """
    print("📝 Actualizando manifest.json...\n")

    if not manifest_path.exists():
        print(f"❌ Error: {manifest_path} no existe")
        sys.exit(1)

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # Crear mapeo: object_id -> migration_order
    migration_order_map = {}
    order_counter = 1

    for level_num, level_objects in enumerate(levels):
        for obj_id in level_objects:
            migration_order_map[obj_id] = {
                "migration_order": order_counter,
                "dependency_level": level_num
            }
            order_counter += 1

    # Circular dependencies en último nivel
    circular_level = len(levels)
    for obj_id in circular_nodes:
        migration_order_map[obj_id] = {
            "migration_order": order_counter,
            "dependency_level": circular_level
        }
        order_counter += 1

    # Actualizar objetos del manifest
    updated_count = 0
    not_found_count = 0

    for obj in manifest["objects"]:
        obj_id = obj["object_id"]

        if obj_id in migration_order_map:
            # Agregar campos nuevos
            obj["migration_order"] = migration_order_map[obj_id]["migration_order"]
            obj["dependency_level"] = migration_order_map[obj_id]["dependency_level"]
            obj["depends_on"] = adj_list.get(obj_id, [])
            obj["depended_by"] = reverse_adj_list.get(obj_id, [])
            updated_count += 1
        else:
            # Objeto no encontrado en análisis (posiblemente REFERENCE)
            obj["migration_order"] = obj.get("processing_order", 9999)
            obj["dependency_level"] = -1  # No aplica
            obj["depends_on"] = []
            obj["depended_by"] = []
            not_found_count += 1

    # Actualizar metadata del manifest
    manifest["dependency_resolution"] = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "total_levels": len(levels) + (1 if circular_nodes else 0),
        "circular_dependencies_count": len(circular_nodes),
        "objects_with_dependencies": updated_count,
        "objects_without_analysis": not_found_count
    }

    if not dry_run:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print(f"   ✅ Manifest actualizado: {manifest_path}")
        print(f"   📊 {updated_count} objetos actualizados con dependency info")
        if not_found_count > 0:
            print(f"   ⚠️  {not_found_count} objetos sin análisis (posiblemente REFERENCE)\n")
    else:
        print(f"   🔍 DRY-RUN: Manifest NO actualizado\n")


def main():
    """Función principal"""
    dry_run = '--dry-run' in sys.argv

    print("=" * 80)
    print("DEPENDENCY RESOLUTION & TOPOLOGICAL SORT")
    print("=" * 80)
    print(f"Directorio: {BASE_DIR}")
    print(f"Modo: {'DRY-RUN (sin guardar archivos)' if dry_run else 'PRODUCCIÓN'}")
    print("=" * 80)

    # 1. Cargar todas las dependencias de knowledge/json/
    objects = load_all_dependencies()

    # 2. Cargar manifest para resolver nombres a IDs
    if not MANIFEST_FILE.exists():
        print(f"❌ Error: {MANIFEST_FILE} no existe")
        print("   Ejecuta prepare_migration.py primero")
        sys.exit(1)

    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    manifest_objects = manifest.get("objects", [])
    print(f"📖 Manifest cargado: {len(manifest_objects)} objetos\n")

    # 3. Resolver nombres de dependencias a object_ids
    resolved_deps = resolve_dependency_names_to_ids(objects, manifest_objects)

    # 4. Construir adjacency list
    adj_list, reverse_adj_list = build_adjacency_list(objects, resolved_deps)

    # 5. Aplicar topological sort con niveles
    nodes = list(objects.keys())
    levels, circular_nodes = topological_sort_with_levels(nodes, adj_list)

    # 6. Detectar grupos de circular dependencies
    circular_groups = detect_circular_groups(circular_nodes, adj_list, objects)

    # 7. Generar dependency_graph.json
    dependency_graph = generate_dependency_graph(objects, adj_list, reverse_adj_list, circular_groups)

    if not dry_run:
        with open(DEPENDENCY_GRAPH_FILE, 'w', encoding='utf-8') as f:
            json.dump(dependency_graph, f, indent=2, ensure_ascii=False)
        print(f"✅ Guardado: {DEPENDENCY_GRAPH_FILE}\n")
    else:
        print(f"🔍 DRY-RUN: {DEPENDENCY_GRAPH_FILE} NO guardado\n")

    # 8. Generar migration_order.json
    migration_order = generate_migration_order(levels, circular_nodes, objects, circular_groups)

    if not dry_run:
        with open(MIGRATION_ORDER_FILE, 'w', encoding='utf-8') as f:
            json.dump(migration_order, f, indent=2, ensure_ascii=False)
        print(f"✅ Guardado: {MIGRATION_ORDER_FILE}\n")
    else:
        print(f"🔍 DRY-RUN: {MIGRATION_ORDER_FILE} NO guardado\n")

    # 9. Actualizar manifest.json
    update_manifest(MANIFEST_FILE, objects, adj_list, reverse_adj_list, levels, circular_nodes, dry_run)

    # 10. Resumen final
    print("=" * 80)
    print("📊 RESUMEN DE DEPENDENCY RESOLUTION")
    print("=" * 80)
    print(f"Total objetos: {len(objects)}")
    print(f"Total dependencias: {dependency_graph['total_dependencies']}")
    print(f"Niveles de dependencia: {len(levels)}")
    print(f"Circular dependencies: {len(circular_nodes)}")
    if circular_groups:
        print(f"Grupos circulares: {len(circular_groups)}")
        for group in circular_groups[:3]:
            print(f"   - Grupo {group['group_id']}: {group['size']} objetos ({group['description']})")
        if len(circular_groups) > 3:
            print(f"   ... y {len(circular_groups) - 3} grupos más")

    print("\n" + "=" * 80)
    print("✅ DEPENDENCY RESOLUTION COMPLETADO")
    print("=" * 80)

    if dry_run:
        print("\n🔍 DRY-RUN: Archivos NO guardados")
    else:
        print("\nArchivos generados:")
        print(f"  - {DEPENDENCY_GRAPH_FILE}")
        print(f"  - {MIGRATION_ORDER_FILE}")
        print(f"  - {MANIFEST_FILE} (actualizado)")


if __name__ == "__main__":
    main()
