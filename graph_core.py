from collections import deque
import heapq
from typing import Any, Dict, List, Optional, Tuple


MAX_VERTICES = 20
INF = 10 ** 9


# =========================================================
# ОБЩИЕ УТИЛИТЫ
# =========================================================

class GraphLogger:
    """
    Простой логгер для пошаговой визуализации алгоритмов.

    Каждый алгоритм добавляет сюда шаги, а потом эти шаги можно
    отправить на фронтенд для анимации графа.
    """

    def __init__(self) -> None:
        self.logs: List[Dict[str, Any]] = []
        self.step_counter = 1

    def add_log(
        self,
        active_node: Optional[int],
        visited_nodes: List[int],
        state_data: Dict[str, Any],
        message: str,
    ) -> None:
        """Добавляет один шаг алгоритма в общий список логов."""
        self.logs.append(
            {
                "step": self.step_counter,
                "active_node": active_node,
                "visited_nodes": visited_nodes.copy(),
                "state_data": state_data.copy(),
                "log_message": message,
            }
        )
        self.step_counter += 1

    def get_logs(self) -> List[Dict[str, Any]]:
        """Возвращает все накопленные шаги."""
        return self.logs


class GraphValidator:
    """Проверки, которые нужны почти всем алгоритмам."""

    @staticmethod
    def validate_matrix(matrix: List[List[int]]) -> Tuple[bool, str, int]:
        """
        Проверяет матрицу смежности для простого неориентированного графа.

        Требования:
        - матрица не пустая;
        - матрица квадратная;
        - число вершин не больше 20;
        - значения только 0 или 1;
        - матрица симметричная;
        - на главной диагонали стоят нули.
        """
        if not matrix or not isinstance(matrix, list):
            return False, "Матрица смежности не может быть пустой", 0

        n = len(matrix)

        if n > MAX_VERTICES:
            return False, f"В графе не должно быть больше {MAX_VERTICES} вершин", n

        for row in matrix:
            if not isinstance(row, list) or len(row) != n:
                return False, "Матрица смежности должна быть квадратной", 0

        for i in range(n):
            for j in range(n):
                if matrix[i][j] not in (0, 1):
                    return False, "Матрица должна содержать только 0 и 1", n

                if i == j and matrix[i][j] != 0:
                    return False, "На главной диагонали матрицы должны быть нули", n

                if matrix[i][j] != matrix[j][i]:
                    return False, "Матрица должна быть симметричной для неориентированного графа", n

        return True, "OK", n

    @staticmethod
    def validate_start_node(start_node: int, n: int) -> Tuple[bool, str]:
        """Проверяет, что стартовая вершина существует."""
        if not isinstance(start_node, int):
            return False, "Стартовая вершина должна быть целым числом"

        if start_node < 0 or start_node >= n:
            return False, f"Стартовая вершина {start_node} вне диапазона 0..{n - 1}"

        return True, "OK"

    @staticmethod
    def validate_weight_matrix(matrix: List[List[int]]) -> Tuple[bool, str, int]:
        """
        Проверяет взвешенную матрицу смежности.
        Значения: 0 (нет ребра) или 1–99 (вес ребра).
        """
        if not matrix or not isinstance(matrix, list):
            return False, "Матрица смежности не может быть пустой", 0

        n = len(matrix)
        if n > MAX_VERTICES:
            return False, f"В графе не должно быть больше {MAX_VERTICES} вершин", n

        for row in matrix:
            if not isinstance(row, list) or len(row) != n:
                return False, "Матрица смежности должна быть квадратной", 0

        for i in range(n):
            for j in range(n):
                if not isinstance(matrix[i][j], int) or matrix[i][j] < 0 or matrix[i][j] > 99:
                    return False, "Веса рёбер должны быть целыми числами от 0 до 99", n
                if i == j and matrix[i][j] != 0:
                    return False, "На главной диагонали матрицы должны быть нули", n
                if matrix[i][j] != matrix[j][i]:
                    return False, "Матрица должна быть симметричной", n

        return True, "OK", n

    @staticmethod
    def validate_user_order(user_order: List[int], n: int) -> Tuple[bool, str]:
        """Проверяет пользовательский обход DFS/BFS."""
        if not isinstance(user_order, list):
            return False, "Ответ пользователя должен быть списком вершин"

        for vertex in user_order:
            if not isinstance(vertex, int):
                return False, "Все вершины в ответе должны быть числами"

            if vertex < 0 or vertex >= n:
                return False, f"Вершина {vertex} вне диапазона 0..{n - 1}"

        return True, "OK"


# =========================================================
# ЕДИНЫЙ ФОРМАТ ОТВЕТОВ ДЛЯ API
# =========================================================

def success_response(
    final_result: Any,
    logs: List[Dict[str, Any]],
    detailed_results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Формирует успешный ответ в одном стиле для всех алгоритмов."""
    response = {
        "status": "success",
        "final_result": final_result,
        "logs": logs,
    }

    if detailed_results is not None:
        response["detailed_results"] = detailed_results

    return response


def error_response(message: str, logs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Формирует ответ с ошибкой в одном стиле для всех алгоритмов."""
    return {
        "status": "error",
        "final_result": message,
        "logs": logs or [],
    }


def get_visited_nodes(visited: List[bool]) -> List[int]:
    """Возвращает список посещенных вершин по массиву True/False."""
    return [i for i, is_visited in enumerate(visited) if is_visited]


def get_neighbors(matrix: List[List[int]], vertex: int) -> List[int]:
    """
    Возвращает соседей вершины в отсортированном порядке.

    Это важно для детерминированности:
    если соседи 5, 2, 4, то алгоритм пойдет в 2, потом 4, потом 5.
    """
    n = len(matrix)
    return sorted([i for i in range(n) if matrix[vertex][i] == 1])


def get_weighted_neighbors(matrix: List[List[int]], vertex: int) -> List[int]:
    """Возвращает соседей вершины для взвешенной матрицы (вес > 0 означает ребро)."""
    n = len(matrix)
    return sorted([i for i in range(n) if matrix[vertex][i] > 0])


def calculate_degrees(matrix: List[List[int]]) -> List[int]:
    """Считает степень каждой вершины."""
    return [sum(row) for row in matrix]


def count_edges(matrix: List[List[int]]) -> int:
    """Считает количество ребер в неориентированном графе."""
    return sum(sum(row) for row in matrix) // 2


# =========================================================
# 0. БАЗОВЫЙ АНАЛИЗ ГРАФА
# =========================================================

def analyze_basic_graph(matrix: List[List[int]]) -> Dict[str, Any]:
    """
    Задача 0.

    Показывает:
    - степень каждой вершины;
    - число компонент связности;
    - является ли граф эйлеровым или полуэйлеровым;
    - является ли граф двудольным;
    - является ли граф полным двудольным.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    logger = GraphLogger()

    degrees = calculate_degrees(matrix)
    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={"degrees": degrees},
        message=f"Считаем степени вершин: {dict(enumerate(degrees))}.",
    )

    components_response = find_components(matrix)
    components = components_response["detailed_results"]["components"]
    components_count = components_response["detailed_results"]["components_count"]

    for log in components_response["logs"]:
        logger.logs.append(log)
        logger.step_counter = max(logger.step_counter, log["step"] + 1)

    odd_vertices = [i for i, degree in enumerate(degrees) if degree % 2 == 1]

    if components_count == 1 and len(odd_vertices) == 0:
        euler_status = "эйлеровый"
    elif components_count == 1 and len(odd_vertices) == 2:
        euler_status = "полуэйлеровый"
    else:
        euler_status = "не эйлеровый и не полуэйлеровый"

    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={
            "odd_vertices": odd_vertices,
            "components_count": components_count,
            "euler_status": euler_status,
        },
        message=(
            f"Проверяем эйлеровость: нечетные вершины {odd_vertices}. "
            f"Итог: граф {euler_status}."
        ),
    )

    bipartite_info = check_bipartite_internal(matrix, logger)

    final_result = {
        "degrees": {i: degrees[i] for i in range(n)},
        "components_count": components_count,
        "components": components,
        "euler_status": euler_status,
        "is_bipartite": bipartite_info["is_bipartite"],
        "is_complete_bipartite": bipartite_info["is_complete_bipartite"],
        "bipartite_colors": bipartite_info["colors"],
    }

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# 1. DFS, ПОКАЗАТЬ ОБХОД В ГЛУБИНУ
# =========================================================

def run_dfs(matrix: List[List[int]], start_node: int = 0) -> Dict[str, Any]:
    """
    Выполняет обход графа в глубину, DFS.

    Возвращает порядок обхода и подробные шаги для визуализации.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    is_start_valid, start_error = GraphValidator.validate_start_node(start_node, n)
    if not is_start_valid:
        return error_response(start_error)

    logger = GraphLogger()
    visited = [False] * n
    order: List[int] = []
    stack: List[int] = []

    logger.add_log(
        active_node=start_node,
        visited_nodes=[],
        state_data={"start_node": start_node},
        message=f"Начинаем DFS с вершины {start_node}.",
    )

    def dfs(vertex: int, depth: int) -> None:
        visited[vertex] = True
        order.append(vertex)
        stack.append(vertex)

        neighbors = [neighbor for neighbor in get_neighbors(matrix, vertex) if not visited[neighbor]]

        logger.add_log(
            active_node=vertex,
            visited_nodes=order.copy(),
            state_data={
                "stack": stack.copy(),
                "depth": depth,
                "available_neighbors": neighbors,
            },
            message=(
                f"Зашли в вершину {vertex}. "
                f"Непосещенные соседи по возрастанию: {neighbors}."
            ),
        )

        for neighbor in neighbors:
            if not visited[neighbor]:
                logger.add_log(
                    active_node=vertex,
                    visited_nodes=order.copy(),
                    state_data={"stack": stack.copy(), "next_node": neighbor},
                    message=f"Из вершины {vertex} переходим глубже в вершину {neighbor}.",
                )
                dfs(neighbor, depth + 1)

        stack.pop()

        logger.add_log(
            active_node=vertex,
            visited_nodes=order.copy(),
            state_data={"stack": stack.copy()},
            message=f"Все соседи вершины {vertex} обработаны. Возвращаемся назад.",
        )

    dfs(start_node, 0)

    logger.add_log(
        active_node=None,
        visited_nodes=order.copy(),
        state_data={"dfs_order": order.copy()},
        message=f"DFS завершен. Итоговый порядок обхода: {order}.",
    )

    final_result = order.copy()
    detailed_results = {"dfs_order": order.copy()}

    return success_response(final_result, logger.get_logs(), detailed_results)


# =========================================================
# 2. DFS, ПРОВЕРКА ОТВЕТА ПОЛЬЗОВАТЕЛЯ
# =========================================================

def check_dfs_answer(
    matrix: List[List[int]],
    user_order: List[int],
    start_node: int = 0,
) -> Dict[str, Any]:
    """
    Проверяет, правильно ли пользователь ввел DFS-обход.

    Правильный ответ считается по правилу:
    соседи всегда перебираются по возрастанию номера вершины.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    is_start_valid, start_error = GraphValidator.validate_start_node(start_node, n)
    if not is_start_valid:
        return error_response(start_error)

    is_order_valid, order_error = GraphValidator.validate_user_order(user_order, n)
    if not is_order_valid:
        return error_response(order_error)

    dfs_response = run_dfs(matrix, start_node)
    correct_order = dfs_response["final_result"]
    is_correct = user_order == correct_order

    logger = GraphLogger()
    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={
            "user_order": user_order,
            "correct_order": correct_order,
            "is_correct": is_correct,
        },
        message=(
            "Проверяем DFS-обход пользователя. "
            f"Ответ пользователя: {user_order}. Правильный ответ: {correct_order}."
        ),
    )

    final_result = {
        "is_correct": is_correct,
        "user_order": user_order,
        "correct_order": correct_order,
        "message": "DFS введен правильно." if is_correct else "DFS введен неправильно.",
    }

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# 3. BFS, ПОКАЗАТЬ ОБХОД В ШИРИНУ
# =========================================================

def run_bfs(matrix: List[List[int]], start_node: int = 0) -> Dict[str, Any]:
    """
    Выполняет обход графа в ширину, BFS.

    Возвращает порядок обхода и подробные шаги для визуализации.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    is_start_valid, start_error = GraphValidator.validate_start_node(start_node, n)
    if not is_start_valid:
        return error_response(start_error)

    logger = GraphLogger()
    visited = [False] * n
    order: List[int] = []
    queue = deque([start_node])
    visited[start_node] = True

    logger.add_log(
        active_node=start_node,
        visited_nodes=get_visited_nodes(visited),
        state_data={"queue": list(queue)},
        message=f"Начинаем BFS с вершины {start_node}. Добавляем ее в очередь.",
    )

    while queue:
        current = queue.popleft()
        order.append(current)

        new_neighbors: List[int] = []

        for neighbor in get_neighbors(matrix, current):
            if not visited[neighbor]:
                visited[neighbor] = True
                queue.append(neighbor)
                new_neighbors.append(neighbor)

        logger.add_log(
            active_node=current,
            visited_nodes=get_visited_nodes(visited),
            state_data={
                "queue": list(queue),
                "bfs_order": order.copy(),
                "added_neighbors": new_neighbors,
            },
            message=(
                f"Извлекли вершину {current} из очереди. "
                f"Новые соседи по возрастанию: {new_neighbors}. "
                f"Текущая очередь: {list(queue)}."
            ),
        )

    logger.add_log(
        active_node=None,
        visited_nodes=order.copy(),
        state_data={"bfs_order": order.copy()},
        message=f"BFS завершен. Итоговый порядок обхода: {order}.",
    )

    final_result = order.copy()
    detailed_results = {"bfs_order": order.copy()}

    return success_response(final_result, logger.get_logs(), detailed_results)


# =========================================================
# 4. BFS, ПРОВЕРКА ОТВЕТА ПОЛЬЗОВАТЕЛЯ
# =========================================================

def check_bfs_answer(
    matrix: List[List[int]],
    user_order: List[int],
    start_node: int = 0,
) -> Dict[str, Any]:
    """
    Проверяет, правильно ли пользователь ввел BFS-обход.

    Правильный ответ считается по правилу:
    соседи всегда перебираются по возрастанию номера вершины.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    is_start_valid, start_error = GraphValidator.validate_start_node(start_node, n)
    if not is_start_valid:
        return error_response(start_error)

    is_order_valid, order_error = GraphValidator.validate_user_order(user_order, n)
    if not is_order_valid:
        return error_response(order_error)

    bfs_response = run_bfs(matrix, start_node)
    correct_order = bfs_response["final_result"]
    is_correct = user_order == correct_order

    logger = GraphLogger()
    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={
            "user_order": user_order,
            "correct_order": correct_order,
            "is_correct": is_correct,
        },
        message=(
            "Проверяем BFS-обход пользователя. "
            f"Ответ пользователя: {user_order}. Правильный ответ: {correct_order}."
        ),
    )

    final_result = {
        "is_correct": is_correct,
        "user_order": user_order,
        "correct_order": correct_order,
        "message": "BFS введен правильно." if is_correct else "BFS введен неправильно.",
    }

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# 5. ЧИСЛО КОМПОНЕНТ СВЯЗНОСТИ
# =========================================================

def find_components(matrix: List[List[int]]) -> Dict[str, Any]:
    """
    Находит все компоненты связности графа.

    Используется BFS, потому что для компонент он простой и понятный.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    logger = GraphLogger()
    visited = [False] * n
    components: List[List[int]] = []

    for start_node in range(n):
        if visited[start_node]:
            continue

        current_component: List[int] = []
        queue = deque([start_node])
        visited[start_node] = True

        logger.add_log(
            active_node=start_node,
            visited_nodes=get_visited_nodes(visited),
            state_data={
                "queue": list(queue),
                "current_component": current_component.copy(),
                "components_found": components.copy(),
            },
            message=f"Нашли новую компоненту связности. Начинаем с вершины {start_node}.",
        )

        while queue:
            current = queue.popleft()
            current_component.append(current)
            new_neighbors: List[int] = []

            for neighbor in get_neighbors(matrix, current):
                if not visited[neighbor]:
                    visited[neighbor] = True
                    queue.append(neighbor)
                    new_neighbors.append(neighbor)

            logger.add_log(
                active_node=current,
                visited_nodes=get_visited_nodes(visited),
                state_data={
                    "queue": list(queue),
                    "current_component": current_component.copy(),
                    "added_neighbors": new_neighbors,
                },
                message=(
                    f"Обрабатываем вершину {current}. "
                    f"В эту же компоненту добавлены соседи: {new_neighbors}."
                ),
            )

        components.append(current_component)

        logger.add_log(
            active_node=None,
            visited_nodes=get_visited_nodes(visited),
            state_data={
                "finished_component": current_component.copy(),
                "components": components.copy(),
            },
            message=f"Компонента завершена: {current_component}.",
        )

    final_result = len(components)
    detailed_results = {
        "components_count": len(components),
        "components": components,
    }

    logger.add_log(
        active_node=None,
        visited_nodes=get_visited_nodes(visited),
        state_data=detailed_results.copy(),
        message=f"Всего найдено компонент связности: {len(components)}.",
    )

    return success_response(final_result, logger.get_logs(), detailed_results)


# =========================================================
# 6. ПРОВЕРКА ЧИСЛА КОМПОНЕНТ СВЯЗНОСТИ
# =========================================================

def check_components_answer(matrix: List[List[int]], user_count: int) -> Dict[str, Any]:
    """Проверяет ответ пользователя на число компонент связности."""
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    if not isinstance(user_count, int):
        return error_response("Ответ пользователя должен быть целым числом")

    components_response = find_components(matrix)
    correct_count = components_response["final_result"]
    is_correct = user_count == correct_count

    logger = GraphLogger()
    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={
            "user_count": user_count,
            "correct_count": correct_count,
            "is_correct": is_correct,
        },
        message=(
            "Проверяем число компонент связности. "
            f"Пользователь ввел {user_count}, правильный ответ {correct_count}."
        ),
    )

    final_result = {
        "is_correct": is_correct,
        "user_count": user_count,
        "correct_count": correct_count,
        "message": "Ответ правильный." if is_correct else "Ответ неправильный.",
    }

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# 7. МИНИМАЛЬНОЕ ОСТОВНОЕ ДЕРЕВО, АЛГОРИТМ ПРИМА
# =========================================================

def build_minimum_spanning_tree(matrix: List[List[int]], start_node: int = 0) -> Dict[str, Any]:
    """
    Строит минимальное остовное дерево алгоритмом Прима.

    Так как матрица смежности содержит только 0 и 1,
    каждое ребро считается ребром веса 1.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    is_start_valid, start_error = GraphValidator.validate_start_node(start_node, n)
    if not is_start_valid:
        return error_response(start_error)

    components_response = find_components(matrix)
    if components_response["final_result"] != 1:
        return error_response("Минимальное остовное дерево существует только для связного графа")

    logger = GraphLogger()
    in_mst = [False] * n
    min_weight = [INF] * n
    parent = [-1] * n
    min_weight[start_node] = 0

    mst_edges: List[List[int]] = []
    total_weight = 0

    logger.add_log(
        active_node=start_node,
        visited_nodes=[],
        state_data={"start_node": start_node},
        message=f"Начинаем алгоритм Прима с вершины {start_node}.",
    )

    for _ in range(n):
        current = -1

        for vertex in range(n):
            if not in_mst[vertex]:
                if current == -1 or min_weight[vertex] < min_weight[current]:
                    current = vertex

        if current == -1:
            break

        in_mst[current] = True

        if parent[current] != -1:
            mst_edges.append([parent[current], current])
            total_weight += 1
            message = f"Добавляем ребро {parent[current]} - {current} в остовное дерево."
        else:
            message = f"Берем стартовую вершину {current}."

        logger.add_log(
            active_node=current,
            visited_nodes=get_visited_nodes(in_mst),
            state_data={
                "mst_edges": mst_edges.copy(),
                "min_weight": min_weight.copy(),
                "parent": parent.copy(),
                "total_weight": total_weight,
            },
            message=message,
        )

        for neighbor in get_neighbors(matrix, current):
            if not in_mst[neighbor] and 1 < min_weight[neighbor]:
                min_weight[neighbor] = 1
                parent[neighbor] = current

                logger.add_log(
                    active_node=current,
                    visited_nodes=get_visited_nodes(in_mst),
                    state_data={
                        "updated_vertex": neighbor,
                        "new_parent": current,
                        "min_weight": min_weight.copy(),
                    },
                    message=(
                        f"Для вершины {neighbor} найдено лучшее ребро через вершину {current}."
                    ),
                )

    final_result = {
        "mst_edges": mst_edges,
        "total_weight": total_weight,
    }

    logger.add_log(
        active_node=None,
        visited_nodes=get_visited_nodes(in_mst),
        state_data=final_result.copy(),
        message=f"Минимальное остовное дерево построено: {mst_edges}. Вес: {total_weight}.",
    )

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# 8. КРАТЧАЙШИЕ ПУТИ ОТ ЗАДАННОЙ ВЕРШИНЫ
# =========================================================

def find_shortest_paths_from_node(matrix: List[List[int]], start_node: int = 0) -> Dict[str, Any]:
    """
    Находит кратчайшие пути от start_node до всех остальных вершин.

    Используется алгоритм Дейкстры.
    Для нашей матрицы 0/1 каждое существующее ребро имеет вес 1.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    is_start_valid, start_error = GraphValidator.validate_start_node(start_node, n)
    if not is_start_valid:
        return error_response(start_error)

    logger = GraphLogger()
    distances = [INF] * n
    previous = [-1] * n
    visited = [False] * n

    distances[start_node] = 0
    heap: List[Tuple[int, int]] = [(0, start_node)]

    logger.add_log(
        active_node=start_node,
        visited_nodes=[],
        state_data={"distances": distances.copy(), "heap": heap.copy()},
        message=f"Начинаем поиск кратчайших путей от вершины {start_node}.",
    )

    while heap:
        current_distance, current = heapq.heappop(heap)

        if visited[current]:
            continue

        visited[current] = True

        logger.add_log(
            active_node=current,
            visited_nodes=get_visited_nodes(visited),
            state_data={
                "distances": distances.copy(),
                "previous": previous.copy(),
                "heap": heap.copy(),
            },
            message=f"Фиксируем вершину {current}. Текущее расстояние до нее: {current_distance}.",
        )

        for neighbor in get_neighbors(matrix, current):
            if visited[neighbor]:
                continue

            new_distance = distances[current] + 1

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current
                heapq.heappush(heap, (new_distance, neighbor))

                logger.add_log(
                    active_node=current,
                    visited_nodes=get_visited_nodes(visited),
                    state_data={
                        "updated_vertex": neighbor,
                        "new_distance": new_distance,
                        "previous": previous.copy(),
                        "heap": heap.copy(),
                    },
                    message=(
                        f"Нашли более короткий путь к вершине {neighbor}: "
                        f"расстояние {new_distance}, предыдущая вершина {current}."
                    ),
                )

    paths = build_paths_from_previous(previous, distances, start_node)

    final_result = {
        "start_node": start_node,
        "distances": [distance if distance != INF else -1 for distance in distances],
        "paths": paths,
    }

    logger.add_log(
        active_node=None,
        visited_nodes=get_visited_nodes(visited),
        state_data=final_result.copy(),
        message=f"Кратчайшие пути от вершины {start_node} найдены.",
    )

    return success_response(final_result, logger.get_logs(), final_result)


def build_paths_from_previous(
    previous: List[int],
    distances: List[int],
    start_node: int,
) -> Dict[int, List[int]]:
    """Восстанавливает пути после алгоритма Дейкстры."""
    paths: Dict[int, List[int]] = {}

    for vertex in range(len(previous)):
        if distances[vertex] == INF:
            paths[vertex] = []
            continue

        path: List[int] = []
        current = vertex

        while current != -1:
            path.append(current)
            current = previous[current]

        path.reverse()
        paths[vertex] = path

    return paths


# =========================================================
# 9. МАТРИЦА КРАТЧАЙШИХ ПУТЕЙ
# =========================================================

def build_shortest_paths_matrix(matrix: List[List[int]]) -> Dict[str, Any]:
    """
    Строит матрицу кратчайших расстояний между всеми парами вершин.

    Используется алгоритм Флойда-Уоршелла.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    logger = GraphLogger()

    dist = [[INF for _ in range(n)] for _ in range(n)]

    for i in range(n):
        dist[i][i] = 0
        for j in range(n):
            if matrix[i][j] == 1:
                dist[i][j] = 1

    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={"distance_matrix": matrix_for_json(dist)},
        message="Создаем начальную матрицу расстояний.",
    )

    for middle in range(n):
        changed_pairs: List[List[int]] = []

        for start in range(n):
            for finish in range(n):
                if dist[start][middle] + dist[middle][finish] < dist[start][finish]:
                    dist[start][finish] = dist[start][middle] + dist[middle][finish]
                    changed_pairs.append([start, finish])

        logger.add_log(
            active_node=middle,
            visited_nodes=list(range(middle + 1)),
            state_data={
                "middle_vertex": middle,
                "changed_pairs": changed_pairs,
                "distance_matrix": matrix_for_json(dist),
            },
            message=(
                f"Пробуем использовать вершину {middle} как промежуточную. "
                f"Обновленные пары: {changed_pairs}."
            ),
        )

    final_result = matrix_for_json(dist)
    detailed_results = {"distance_matrix": final_result}

    logger.add_log(
        active_node=None,
        visited_nodes=list(range(n)),
        state_data=detailed_results.copy(),
        message="Матрица кратчайших путей построена.",
    )

    return success_response(final_result, logger.get_logs(), detailed_results)


def matrix_for_json(matrix: List[List[int]]) -> List[List[int]]:
    """
    Заменяет INF на -1, чтобы результат нормально выглядел в JSON.

    -1 означает, что пути между вершинами нет.
    """
    return [
        [value if value != INF else -1 for value in row]
        for row in matrix
    ]


# =========================================================
# 10. КОДИРОВАНИЕ ПРЮФЕРА
# =========================================================

def encode_prufer(matrix: List[List[int]]) -> Dict[str, Any]:
    """
    Строит код Прюфера для дерева.

    Код Прюфера можно строить только для дерева:
    граф должен быть связным и иметь n - 1 ребро.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    if not is_tree(matrix):
        return error_response("Код Прюфера можно строить только для дерева")

    logger = GraphLogger()
    temp_matrix = [row.copy() for row in matrix]
    degrees = calculate_degrees(temp_matrix)
    code: List[int] = []

    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={"degrees": degrees.copy()},
        message="Граф является деревом. Начинаем кодирование Прюфера.",
    )

    for _ in range(n - 2):
        leaves = [vertex for vertex in range(n) if degrees[vertex] == 1]
        leaf = min(leaves)

        neighbor = -1
        for vertex in range(n):
            if temp_matrix[leaf][vertex] == 1:
                neighbor = vertex
                break

        code.append(neighbor)

        logger.add_log(
            active_node=leaf,
            visited_nodes=[],
            state_data={
                "leaf": leaf,
                "neighbor": neighbor,
                "current_code": code.copy(),
                "degrees": degrees.copy(),
            },
            message=(
                f"Берем самый маленький лист {leaf}. "
                f"Его сосед {neighbor}, добавляем {neighbor} в код Прюфера."
            ),
        )

        temp_matrix[leaf][neighbor] = 0
        temp_matrix[neighbor][leaf] = 0
        degrees[leaf] -= 1
        degrees[neighbor] -= 1

    final_result = code.copy()
    detailed_results = {"prufer_code": code.copy()}

    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data=detailed_results.copy(),
        message=f"Код Прюфера построен: {code}.",
    )

    return success_response(final_result, logger.get_logs(), detailed_results)


def is_tree(matrix: List[List[int]]) -> bool:
    """Проверяет, является ли граф деревом."""
    components_response = find_components(matrix)

    if components_response["status"] != "success":
        return False

    components_count = components_response["final_result"]
    edges_count = count_edges(matrix)
    vertices_count = len(matrix)

    return components_count == 1 and edges_count == vertices_count - 1


# =========================================================
# 11. ДЕКОДИРОВАНИЕ ПРЮФЕРА
# =========================================================

def decode_prufer(prufer_code: List[int]) -> Dict[str, Any]:
    """
    Декодирует код Прюфера обратно в дерево.

    На вход подается список чисел, например [1, 1, 2].
    Если длина кода m, то в дереве будет m + 2 вершины.
    """
    if not isinstance(prufer_code, list):
        return error_response("Код Прюфера должен быть списком чисел")

    n = len(prufer_code) + 2

    for vertex in prufer_code:
        if not isinstance(vertex, int):
            return error_response("Код Прюфера должен содержать только целые числа")

        if vertex < 0 or vertex >= n:
            return error_response(f"Вершина {vertex} вне диапазона 0..{n - 1}")

    logger = GraphLogger()
    degrees = [1] * n

    for vertex in prufer_code:
        degrees[vertex] += 1

    code_copy = prufer_code.copy()
    edges: List[List[int]] = []

    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={"prufer_code": prufer_code.copy(), "degrees": degrees.copy()},
        message=f"Начинаем декодирование кода Прюфера {prufer_code}.",
    )

    for value in code_copy:
        leaf = min([vertex for vertex in range(n) if degrees[vertex] == 1])
        edges.append([leaf, value])

        logger.add_log(
            active_node=leaf,
            visited_nodes=[],
            state_data={
                "leaf": leaf,
                "connected_with": value,
                "edges": edges.copy(),
                "degrees": degrees.copy(),
            },
            message=f"Берем самый маленький лист {leaf} и соединяем его с вершиной {value}.",
        )

        degrees[leaf] -= 1
        degrees[value] -= 1

    last_vertices = [vertex for vertex in range(n) if degrees[vertex] == 1]

    if len(last_vertices) == 2:
        edges.append([last_vertices[0], last_vertices[1]])

        logger.add_log(
            active_node=None,
            visited_nodes=[],
            state_data={"last_edge": [last_vertices[0], last_vertices[1]], "edges": edges.copy()},
            message=f"Соединяем две последние вершины: {last_vertices[0]} и {last_vertices[1]}.",
        )

    decoded_matrix = edges_to_matrix(edges, n)

    final_result = {
        "vertices_count": n,
        "edges": edges,
        "matrix": decoded_matrix,
    }

    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data=final_result.copy(),
        message=f"Декодирование завершено. Ребра дерева: {edges}.",
    )

    return success_response(final_result, logger.get_logs(), final_result)


def edges_to_matrix(edges: List[List[int]], n: int) -> List[List[int]]:
    """Строит матрицу смежности по списку ребер."""
    matrix = [[0 for _ in range(n)] for _ in range(n)]

    for u, v in edges:
        matrix[u][v] = 1
        matrix[v][u] = 1

    return matrix


# =========================================================
# 12. РАСКРАСКА ГРАФА
# =========================================================

def color_graph_greedy(matrix: List[List[int]]) -> Dict[str, Any]:
    """
    Выполняет жадную раскраску графа.

    Вершины обрабатываются по убыванию степени.
    Если степени одинаковые, раньше идет вершина с меньшим номером.
    """
    is_valid, error_msg, n = GraphValidator.validate_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    logger = GraphLogger()
    degrees = calculate_degrees(matrix)
    colors = [-1] * n

    vertices_order = sorted(range(n), key=lambda vertex: (-degrees[vertex], vertex))

    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={"vertices_order": vertices_order, "degrees": degrees},
        message=(
            "Начинаем жадную раскраску. "
            f"Порядок вершин по убыванию степени: {vertices_order}."
        ),
    )

    for vertex in vertices_order:
        used_colors = set()

        for neighbor in get_neighbors(matrix, vertex):
            if colors[neighbor] != -1:
                used_colors.add(colors[neighbor])

        color = 0
        while color in used_colors:
            color += 1

        colors[vertex] = color

        logger.add_log(
            active_node=vertex,
            visited_nodes=[v for v in range(n) if colors[v] != -1],
            state_data={
                "colors": {i: colors[i] for i in range(n)},
                "used_neighbor_colors": sorted(list(used_colors)),
                "chosen_color": color,
            },
            message=(
                f"Красим вершину {vertex}. "
                f"Цвета соседей: {sorted(list(used_colors))}. "
                f"Выбран самый маленький доступный цвет: {color}."
            ),
        )

    chromatic_number = max(colors) + 1 if colors else 0

    final_result = {
        "colors": {i: colors[i] for i in range(n)},
        "colors_count": chromatic_number,
    }

    logger.add_log(
        active_node=None,
        visited_nodes=list(range(n)),
        state_data=final_result.copy(),
        message=f"Раскраска завершена. Использовано цветов: {chromatic_number}.",
    )

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# ВСПОМОГАТЕЛЬНАЯ ПРОВЕРКА ДВУДОЛЬНОСТИ
# =========================================================

def check_bipartite_internal(matrix: List[List[int]], logger: Optional[GraphLogger] = None) -> Dict[str, Any]:
    """
    Проверяет двудольность графа.

    Возвращает:
    - is_bipartite;
    - colors;
    - is_complete_bipartite.
    """
    n = len(matrix)
    colors = [-1] * n
    is_bipartite = True

    for start_node in range(n):
        if colors[start_node] != -1:
            continue

        colors[start_node] = 0
        queue = deque([start_node])

        if logger:
            logger.add_log(
                active_node=start_node,
                visited_nodes=[start_node],
                state_data={"colors": colors.copy(), "queue": list(queue)},
                message=f"Начинаем проверку двудольности с вершины {start_node}. Красим ее в цвет 0.",
            )

        while queue and is_bipartite:
            current = queue.popleft()

            for neighbor in get_neighbors(matrix, current):
                if colors[neighbor] == -1:
                    colors[neighbor] = 1 - colors[current]
                    queue.append(neighbor)

                    if logger:
                        logger.add_log(
                            active_node=current,
                            visited_nodes=[i for i in range(n) if colors[i] != -1],
                            state_data={"colors": colors.copy(), "queue": list(queue)},
                            message=(
                                f"Вершина {neighbor} соседствует с {current}, "
                                f"поэтому красим ее в другой цвет: {colors[neighbor]}."
                            ),
                        )

                elif colors[neighbor] == colors[current]:
                    is_bipartite = False

                    if logger:
                        logger.add_log(
                            active_node=current,
                            visited_nodes=[i for i in range(n) if colors[i] != -1],
                            state_data={
                                "colors": colors.copy(),
                                "conflict_edge": [current, neighbor],
                            },
                            message=(
                                f"Найден конфликт: вершины {current} и {neighbor} "
                                "имеют один цвет. Граф не двудольный."
                            ),
                        )
                    break

    is_complete_bipartite = False

    if is_bipartite:
        left_part = [i for i in range(n) if colors[i] == 0]
        right_part = [i for i in range(n) if colors[i] == 1]

        is_complete_bipartite = len(left_part) > 0 and len(right_part) > 0

        for left_vertex in left_part:
            for right_vertex in right_part:
                if matrix[left_vertex][right_vertex] != 1:
                    is_complete_bipartite = False
                    break
            if not is_complete_bipartite:
                break

        if logger:
            logger.add_log(
                active_node=None,
                visited_nodes=list(range(n)),
                state_data={
                    "left_part": left_part,
                    "right_part": right_part,
                    "is_complete_bipartite": is_complete_bipartite,
                },
                message=(
                    "Граф двудольный. "
                    f"Доли: {left_part} и {right_part}. "
                    f"Полный двудольный: {is_complete_bipartite}."
                ),
            )

    return {
        "is_bipartite": is_bipartite,
        "colors": {i: colors[i] for i in range(n)},
        "is_complete_bipartite": is_complete_bipartite,
    }


# =========================================================
# ВЗВЕШЕННЫЕ АЛГОРИТМЫ (веса рёбер из матрицы)
# =========================================================

def find_shortest_paths_weighted(matrix: List[List[int]], start_node: int = 0) -> Dict[str, Any]:
    """Дейкстра с реальными весами рёбер."""
    is_valid, error_msg, n = GraphValidator.validate_weight_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    is_start_valid, start_error = GraphValidator.validate_start_node(start_node, n)
    if not is_start_valid:
        return error_response(start_error)

    logger = GraphLogger()
    distances = [INF] * n
    previous = [-1] * n
    visited = [False] * n
    distances[start_node] = 0
    heap: List[Tuple[int, int]] = [(0, start_node)]

    logger.add_log(
        active_node=start_node,
        visited_nodes=[],
        state_data={"distances": distances.copy(), "heap": heap.copy()},
        message=f"Начинаем поиск кратчайших путей от вершины {start_node}.",
    )

    while heap:
        current_distance, current = heapq.heappop(heap)
        if visited[current]:
            continue
        visited[current] = True

        logger.add_log(
            active_node=current,
            visited_nodes=get_visited_nodes(visited),
            state_data={"distances": distances.copy(), "previous": previous.copy()},
            message=f"Фиксируем вершину {current}. Расстояние: {current_distance}.",
        )

        for neighbor in get_weighted_neighbors(matrix, current):
            if visited[neighbor]:
                continue
            new_distance = distances[current] + matrix[current][neighbor]
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current
                heapq.heappush(heap, (new_distance, neighbor))
                logger.add_log(
                    active_node=current,
                    visited_nodes=get_visited_nodes(visited),
                    state_data={"updated_vertex": neighbor, "new_distance": new_distance},
                    message=(
                        f"Нашли более короткий путь к вершине {neighbor}: "
                        f"расстояние {new_distance} через вершину {current}."
                    ),
                )

    paths = build_paths_from_previous(previous, distances, start_node)
    final_result = {
        "start_node": start_node,
        "distances": [d if d != INF else -1 for d in distances],
        "paths": paths,
    }
    logger.add_log(
        active_node=None,
        visited_nodes=get_visited_nodes(visited),
        state_data=final_result.copy(),
        message=f"Кратчайшие пути от вершины {start_node} найдены.",
    )
    return success_response(final_result, logger.get_logs(), final_result)


def build_shortest_paths_matrix_weighted(matrix: List[List[int]]) -> Dict[str, Any]:
    """Флойд-Уоршелл с реальными весами рёбер."""
    is_valid, error_msg, n = GraphValidator.validate_weight_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    logger = GraphLogger()
    dist = [[INF for _ in range(n)] for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
        for j in range(n):
            if matrix[i][j] > 0:
                dist[i][j] = matrix[i][j]

    logger.add_log(
        active_node=None,
        visited_nodes=[],
        state_data={"distance_matrix": matrix_for_json(dist)},
        message="Создаём начальную матрицу расстояний из весов рёбер.",
    )

    for middle in range(n):
        changed_pairs: List[List[int]] = []
        for start in range(n):
            for finish in range(n):
                if dist[start][middle] + dist[middle][finish] < dist[start][finish]:
                    dist[start][finish] = dist[start][middle] + dist[middle][finish]
                    changed_pairs.append([start, finish])

        logger.add_log(
            active_node=middle,
            visited_nodes=list(range(middle + 1)),
            state_data={"middle_vertex": middle, "changed_pairs": changed_pairs,
                        "distance_matrix": matrix_for_json(dist)},
            message=(
                f"Вершина {middle} как промежуточная. "
                f"Обновлённые пары: {changed_pairs}."
            ),
        )

    final_result = matrix_for_json(dist)
    detailed_results = {"distance_matrix": final_result}
    logger.add_log(
        active_node=None,
        visited_nodes=list(range(n)),
        state_data=detailed_results.copy(),
        message="Матрица кратчайших путей (с весами) построена.",
    )
    return success_response(final_result, logger.get_logs(), detailed_results)


def build_minimum_spanning_tree_weighted(matrix: List[List[int]], start_node: int = 0) -> Dict[str, Any]:
    """Алгоритм Прима с реальными весами рёбер."""
    is_valid, error_msg, n = GraphValidator.validate_weight_matrix(matrix)
    if not is_valid:
        return error_response(error_msg)

    is_start_valid, start_error = GraphValidator.validate_start_node(start_node, n)
    if not is_start_valid:
        return error_response(start_error)

    binary_matrix = [[1 if v > 0 else 0 for v in row] for row in matrix]
    if find_components(binary_matrix)["final_result"] != 1:
        return error_response("Минимальное остовное дерево существует только для связного графа")

    logger = GraphLogger()
    in_mst = [False] * n
    min_weight = [INF] * n
    parent = [-1] * n
    min_weight[start_node] = 0
    mst_edges: List[List[int]] = []
    total_weight = 0

    logger.add_log(
        active_node=start_node,
        visited_nodes=[],
        state_data={"start_node": start_node},
        message=f"Начинаем алгоритм Прима (взвешенный) с вершины {start_node}.",
    )

    for _ in range(n):
        current = -1
        for vertex in range(n):
            if not in_mst[vertex]:
                if current == -1 or min_weight[vertex] < min_weight[current]:
                    current = vertex

        if current == -1:
            break

        in_mst[current] = True

        if parent[current] != -1:
            edge_w = matrix[parent[current]][current]
            mst_edges.append([parent[current], current])
            total_weight += edge_w
            message = f"Добавляем ребро {parent[current]}–{current} (вес {edge_w})."
        else:
            message = f"Берём стартовую вершину {current}."

        logger.add_log(
            active_node=current,
            visited_nodes=get_visited_nodes(in_mst),
            state_data={"mst_edges": mst_edges.copy(), "min_weight": min_weight.copy(),
                        "total_weight": total_weight},
            message=message,
        )

        for neighbor in get_weighted_neighbors(matrix, current):
            if not in_mst[neighbor] and matrix[current][neighbor] < min_weight[neighbor]:
                min_weight[neighbor] = matrix[current][neighbor]
                parent[neighbor] = current
                logger.add_log(
                    active_node=current,
                    visited_nodes=get_visited_nodes(in_mst),
                    state_data={"updated_vertex": neighbor, "new_weight": matrix[current][neighbor]},
                    message=(
                        f"Для вершины {neighbor} лучший вес: "
                        f"{matrix[current][neighbor]} через вершину {current}."
                    ),
                )

    final_result = {"mst_edges": mst_edges, "total_weight": total_weight}
    logger.add_log(
        active_node=None,
        visited_nodes=get_visited_nodes(in_mst),
        state_data=final_result.copy(),
        message=f"МОД построено: {mst_edges}. Суммарный вес: {total_weight}.",
    )
    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# НЕБОЛЬШОЙ ДИСПЕТЧЕР ДЛЯ BACKEND-А
# =========================================================

def run_graph_algorithm(
    algorithm_name: str,
    matrix: Optional[List[List[int]]] = None,
    start_node: int = 0,
    user_order: Optional[List[int]] = None,
    user_components_count: Optional[int] = None,
    prufer_code: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Общая функция-диспетчер.

    Ее удобно дергать с backend-а, если фронтенд передает название алгоритма.

    Доступные algorithm_name:
    - "basic"
    - "dfs"
    - "check_dfs"
    - "bfs"
    - "check_bfs"
    - "components"
    - "check_components"
    - "mst"
    - "shortest_paths"
    - "shortest_matrix"
    - "prufer_encode"
    - "prufer_decode"
    - "coloring"
    """
    if algorithm_name == "prufer_decode":
        if prufer_code is None:
            return error_response("Для декодирования Прюфера нужно передать prufer_code")
        return decode_prufer(prufer_code)

    if matrix is None:
        return error_response("Для этого алгоритма нужно передать matrix")

    if algorithm_name == "basic":
        return analyze_basic_graph(matrix)

    if algorithm_name == "dfs":
        return run_dfs(matrix, start_node)

    if algorithm_name == "check_dfs":
        if user_order is None:
            return error_response("Для проверки DFS нужно передать user_order")
        return check_dfs_answer(matrix, user_order, start_node)

    if algorithm_name == "bfs":
        return run_bfs(matrix, start_node)

    if algorithm_name == "check_bfs":
        if user_order is None:
            return error_response("Для проверки BFS нужно передать user_order")
        return check_bfs_answer(matrix, user_order, start_node)

    if algorithm_name == "components":
        return find_components(matrix)

    if algorithm_name == "check_components":
        if user_components_count is None:
            return error_response("Для проверки компонент нужно передать user_components_count")
        return check_components_answer(matrix, user_components_count)

    if algorithm_name == "mst":
        return build_minimum_spanning_tree(matrix, start_node)

    if algorithm_name == "shortest_paths":
        return find_shortest_paths_from_node(matrix, start_node)

    if algorithm_name == "shortest_matrix":
        return build_shortest_paths_matrix(matrix)

    if algorithm_name == "prufer_encode":
        return encode_prufer(matrix)

    if algorithm_name == "coloring":
        return color_graph_greedy(matrix)

    if algorithm_name == "mst_weighted":
        return build_minimum_spanning_tree_weighted(matrix, start_node)

    if algorithm_name == "shortest_paths_weighted":
        return find_shortest_paths_weighted(matrix, start_node)

    if algorithm_name == "shortest_matrix_weighted":
        return build_shortest_paths_matrix_weighted(matrix)

    return error_response(f"Неизвестный алгоритм: {algorithm_name}")
