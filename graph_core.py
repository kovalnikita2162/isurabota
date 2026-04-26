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
    Тут собираем шаги алгоритма.

    Потом Никита берет эти данные и показывает на странице:
    активную вершину, посещенные вершины и текст лога.
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
        """Добавляем один шаг, чтобы потом показать его в логе справа."""
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
        """Отдаем все шаги, которые успели собрать."""
        return self.logs


class GraphValidator:
    """Здесь лежат общие проверки для графа."""

    @staticmethod
    def validate_matrix(matrix: List[List[int]]) -> Tuple[bool, str, int]:
        """
        Проверяем обычную матрицу смежности.

        Для наших задач нужно, чтобы матрица была квадратной,
        состояла только из 0 и 1, была симметричной и без петель.
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
        """Проверяем, что такая стартовая вершина вообще есть в графе."""
        if not isinstance(start_node, int):
            return False, "Стартовая вершина должна быть целым числом"

        if start_node < 0 or start_node >= n:
            return False, f"Стартовая вершина {start_node} вне диапазона 0..{n - 1}"

        return True, "OK"

    @staticmethod
    def validate_weight_matrix(matrix: List[List[int]]) -> Tuple[bool, str, int]:
        """
        Проверяем матрицу с весами.

        0 значит, что ребра нет. Число больше 0 значит вес ребра.
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
        """Проверяем ответ пользователя для DFS или BFS."""
        if not isinstance(user_order, list):
            return False, "Ответ пользователя должен быть списком вершин"

        for vertex in user_order:
            if not isinstance(vertex, int):
                return False, "Все вершины в ответе должны быть числами"

            if vertex < 0 or vertex >= n:
                return False, f"Вершина {vertex} вне диапазона 0..{n - 1}"

        return True, "OK"


# =========================================================
# ОБЩИЙ ФОРМАТ ОТВЕТА ДЛЯ СТРАНИЦЫ
# =========================================================

def success_response(
    final_result: Any,
    logs: List[Dict[str, Any]],
    detailed_results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Собираем успешный ответ в одном формате.

    Так Никите проще выводить результат: везде есть status,
    final_result и logs.
    """
    response = {
        "status": "success",
        "final_result": final_result,
        "logs": logs,
    }

    if detailed_results is not None:
        response["detailed_results"] = detailed_results

    return response


def error_response(message: str, logs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Возвращаем ошибку в таком же формате.

    Никита может просто проверить status == "error"
    и вывести сообщение пользователю.
    """
    return {
        "status": "error",
        "final_result": message,
        "logs": logs or [],
    }


def get_visited_nodes(visited: List[bool]) -> List[int]:
    """Из массива True/False делаем обычный список посещенных вершин."""
    return [i for i, is_visited in enumerate(visited) if is_visited]


def get_neighbors(matrix: List[List[int]], vertex: int) -> List[int]:
    """
    Возвращаем соседей вершины.

    Сортировка нужна, чтобы обход всегда шел одинаково:
    сначала меньшие номера вершин, потом большие.
    """
    n = len(matrix)
    return sorted([i for i in range(n) if matrix[vertex][i] == 1])


def get_weighted_neighbors(matrix: List[List[int]], vertex: int) -> List[int]:
    """Ищем соседей во взвешенном графе: если вес больше 0, ребро есть."""
    n = len(matrix)
    return sorted([i for i in range(n) if matrix[vertex][i] > 0])


def calculate_degrees(matrix: List[List[int]]) -> List[int]:
    """Считаем степень каждой вершины, то есть сколько у нее ребер."""
    return [sum(row) for row in matrix]


def count_edges(matrix: List[List[int]]) -> int:
    """Считаем ребра графа. Делим на 2, потому что матрица симметричная."""
    return sum(sum(row) for row in matrix) // 2


# =========================================================
# 0. БАЗОВЫЙ АНАЛИЗ ГРАФА
# =========================================================

def analyze_basic_graph(matrix: List[List[int]]) -> Dict[str, Any]:
    """
    Задача 0: базовый анализ графа.

    Тут сразу считаем несколько простых характеристик:
    степени вершин, компоненты связности, эйлеровость и двудольность.
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
        message=f"Вычисляем степени вершин: {dict(enumerate(degrees))}.",
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
            f"Проверяем эйлеровость: вершины нечётной степени — {odd_vertices}. "
            f"Вывод: граф {euler_status}."
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
    Запускаем DFS, то есть обход в глубину.

    Кроме ответа сохраняем шаги, чтобы Никита мог показать процесс на странице.
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
        message=f"Начинаем обход в глубину с вершины <b>{start_node}</b>.",
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
                f"Погружаемся в вершину <b>{vertex}</b>, отмечаем как посещённую. "
                f"Непосещённые соседи: {neighbors}."
            ),
        )

        for neighbor in neighbors:
            if not visited[neighbor]:
                logger.add_log(
                    active_node=vertex,
                    visited_nodes=order.copy(),
                    state_data={"stack": stack.copy(), "next_node": neighbor},
                    message=f"Из вершины <b>{vertex}</b> переходим в вершину <b>{neighbor}</b>.",
                )
                dfs(neighbor, depth + 1)

        stack.pop()

        logger.add_log(
            active_node=vertex,
            visited_nodes=order.copy(),
            state_data={"stack": stack.copy()},
            message=f"Все соседи вершины <b>{vertex}</b> обработаны — возвращаемся на уровень выше.",
        )

    dfs(start_node, 0)

    logger.add_log(
        active_node=None,
        visited_nodes=order.copy(),
        state_data={"dfs_order": order.copy()},
        message=f"Обход в глубину завершён. Порядок посещения вершин: {order}.",
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
    Проверяем, совпал ли ответ пользователя с правильным DFS.

    Соседей всегда берем по возрастанию, чтобы не было разных вариантов ответа.
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
            "Сравниваем ответ с эталонным порядком обхода в глубину. "
            f"Ваш вариант: {user_order}. Правильный: {correct_order}."
        ),
    )

    final_result = {
        "is_correct": is_correct,
        "user_order": user_order,
        "correct_order": correct_order,
        "message": "Обход введён правильно." if is_correct else "Обход введён неправильно.",
    }

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# 3. BFS, ПОКАЗАТЬ ОБХОД В ШИРИНУ
# =========================================================

def run_bfs(matrix: List[List[int]], start_node: int = 0) -> Dict[str, Any]:
    """
    Запускаем BFS, то есть обход в ширину.

    Сохраняем и итоговый порядок, и шаги для отображения на странице.
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
        message=f"Начинаем обход в ширину с вершины <b>{start_node}</b> — помещаем её в очередь.",
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
                f"Извлекаем вершину <b>{current}</b> из очереди. "
                f"Добавляем непосещённых соседей: {new_neighbors}. "
                f"Очередь: {list(queue)}."
            ),
        )

    logger.add_log(
        active_node=None,
        visited_nodes=order.copy(),
        state_data={"bfs_order": order.copy()},
        message=f"Обход в ширину завершён. Порядок посещения вершин: {order}.",
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
    Проверяем, совпал ли ответ пользователя с правильным BFS.

    Здесь тоже сортируем соседей, чтобы правильный ответ был один.
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
            "Сравниваем ответ с эталонным порядком обхода в ширину. "
            f"Ваш вариант: {user_order}. Правильный: {correct_order}."
        ),
    )

    final_result = {
        "is_correct": is_correct,
        "user_order": user_order,
        "correct_order": correct_order,
        "message": "Обход введён правильно." if is_correct else "Обход введён неправильно.",
    }

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# 5. ЧИСЛО КОМПОНЕНТ СВЯЗНОСТИ
# =========================================================

def find_components(matrix: List[List[int]]) -> Dict[str, Any]:
    """
    Ищем компоненты связности.

    Если из одной вершины нельзя добраться до другой, значит они в разных компонентах.
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
            message=f"Вершина <b>{start_node}</b> не посещена — начинаем обход новой компоненты связности.",
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
                    f"Посещаем вершину <b>{current}</b>. "
                    f"Добавляем в компоненту смежные непосещённые вершины: {new_neighbors}."
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
            message=f"Компонента завершена. Вершины: {current_component}.",
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
        message=f"Все компоненты найдены. Итого компонент связности: {len(components)}.",
    )

    return success_response(final_result, logger.get_logs(), detailed_results)


# =========================================================
# 6. ПРОВЕРКА ЧИСЛА КОМПОНЕНТ СВЯЗНОСТИ
# =========================================================

def check_components_answer(matrix: List[List[int]], user_count: int) -> Dict[str, Any]:
    """Проверяем, правильно ли пользователь указал число компонент."""
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
            f"Ваш ответ: {user_count}. Правильный: {correct_count}."
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
    Строим минимальное остовное дерево алгоритмом Прима.

    В обычной матрице все существующие ребра считаем одинаковыми, с весом 1.
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
        message=f"Запускаем алгоритм Прима. Начальная вершина: <b>{start_node}</b>.",
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
            message = f"Добавляем ребро (<b>{parent[current]}</b>, <b>{current}</b>) в остовное дерево."
        else:
            message = f"Включаем начальную вершину <b>{current}</b> в остовное дерево."

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
                        f"Обновляем минимальный вес вершины <b>{neighbor}</b>: "
                        f"лучшее ребро теперь через <b>{current}</b>."
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
        message=f"Минимальное остовное дерево построено. Рёбра: {mst_edges}. Суммарный вес: {total_weight}.",
    )

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# 8. КРАТЧАЙШИЕ ПУТИ ОТ ЗАДАННОЙ ВЕРШИНЫ
# =========================================================

def find_shortest_paths_from_node(matrix: List[List[int]], start_node: int = 0) -> Dict[str, Any]:
    """
    Ищем кратчайшие пути от выбранной вершины до всех остальных.

    Используем Дейкстру. В обычном графе каждое ребро считаем весом 1.
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
        message=f"Запускаем алгоритм Дейкстры из вершины <b>{start_node}</b>. Расстояние до <b>{start_node}</b> = 0.",
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
            message=f"Фиксируем кратчайшее расстояние до вершины <b>{current}</b>: d = {current_distance}.",
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
                        f"Обновляем расстояние до вершины <b>{neighbor}</b>: "
                        f"d = {new_distance} через вершину <b>{current}</b>."
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
        message=f"Алгоритм Дейкстры завершён. Все кратчайшие расстояния от вершины <b>{start_node}</b> найдены.",
    )

    return success_response(final_result, logger.get_logs(), final_result)


def build_paths_from_previous(
    previous: List[int],
    distances: List[int],
    start_node: int,
) -> Dict[int, List[int]]:
    """По массиву previous собираем сами пути после Дейкстры."""
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
    Строим матрицу кратчайших расстояний между всеми вершинами.

    Для этого используем алгоритм Флойда-Уоршелла.
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
        message="Инициализируем матрицу расстояний: d[i][i] = 0, d[i][j] = 1 если ребро есть, иначе ∞.",
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
                f"Рассматриваем вершину <b>{middle}</b> как промежуточную. "
                f"Обновлены пары: {changed_pairs}."
            ),
        )

    final_result = matrix_for_json(dist)
    detailed_results = {"distance_matrix": final_result}

    logger.add_log(
        active_node=None,
        visited_nodes=list(range(n)),
        state_data=detailed_results.copy(),
        message="Алгоритм Флойда–Уоршелла завершён. Матрица кратчайших расстояний построена.",
    )

    return success_response(final_result, logger.get_logs(), detailed_results)


def matrix_for_json(matrix: List[List[int]]) -> List[List[int]]:
    """
    Меняем INF на -1, чтобы нормально отдать результат на страницу.

    -1 значит, что пути между вершинами нет.
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
    Строим код Прюфера для дерева.

    Важно: код Прюфера работает именно для дерева, а не для любого графа.
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
        message="Граф является деревом. Начинаем построение кода Прюфера.",
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
                f"Минимальный лист — вершина <b>{leaf}</b>. "
                f"Смежная с ней вершина: <b>{neighbor}</b> — записываем <b>{neighbor}</b> в код."
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
        message=f"Кодирование завершено. Код Прюфера: {code}.",
    )

    return success_response(final_result, logger.get_logs(), detailed_results)


def is_tree(matrix: List[List[int]]) -> bool:
    """Проверяем, является ли граф деревом."""
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
    По коду Прюфера восстанавливаем дерево.

    Например, если в коде m чисел, то в дереве будет m + 2 вершины.
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
        message=f"Начинаем восстановление дерева по коду Прюфера {prufer_code}. Число вершин: {n}.",
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
            message=f"Минимальный лист: вершина <b>{leaf}</b>. Добавляем ребро (<b>{leaf}</b>, <b>{value}</b>), удаляем лист.",
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
            message=f"Добавляем последнее ребро: соединяем оставшиеся вершины <b>{last_vertices[0]}</b> и <b>{last_vertices[1]}</b>.",
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
        message=f"Дерево восстановлено. Рёбра: {edges}.",
    )

    return success_response(final_result, logger.get_logs(), final_result)


def edges_to_matrix(edges: List[List[int]], n: int) -> List[List[int]]:
    """Из списка ребер делаем матрицу смежности."""
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
    Раскрашиваем граф жадным способом.

    Сначала берем вершины с большей степенью, а при равенстве - с меньшим номером.
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
                f"Раскрашиваем вершину <b>{vertex}</b>. "
                f"Цвета смежных вершин: {sorted(list(used_colors))}. "
                f"Назначаем наименьший доступный цвет: {color}."
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
        message=f"Раскраска завершена. Хроматическое число: {chromatic_number}.",
    )

    return success_response(final_result, logger.get_logs(), final_result)


# =========================================================
# ВСПОМОГАТЕЛЬНАЯ ПРОВЕРКА ДВУДОЛЬНОСТИ
# =========================================================

def check_bipartite_internal(matrix: List[List[int]], logger: Optional[GraphLogger] = None) -> Dict[str, Any]:
    """
    Проверяем, можно ли разбить граф на две доли.

    Заодно сохраняем цвета вершин и проверяем полный двудольный граф.
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
                message=f"Проверяем двудольность. Относим вершину <b>{start_node}</b> к доле 0.",
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
                                f"Вершина <b>{neighbor}</b> смежна с <b>{current}</b> "
                                f"— относим к доле {colors[neighbor]}."
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
                                f"Противоречие: вершины <b>{current}</b> и <b>{neighbor}</b> смежны, "
                                "но принадлежат одной доле — граф не двудольный."
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
    """Дейкстра для графа, где у ребер есть настоящие веса."""
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
        message=f"Запускаем алгоритм Дейкстры из вершины <b>{start_node}</b>. Расстояние до <b>{start_node}</b> = 0.",
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
            message=f"Фиксируем кратчайшее расстояние до вершины <b>{current}</b>: d = {current_distance}.",
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
                        f"Обновляем расстояние до вершины <b>{neighbor}</b>: "
                        f"d = {new_distance} через вершину <b>{current}</b>."
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
        message=f"Алгоритм Дейкстры завершён. Все кратчайшие расстояния от вершины <b>{start_node}</b> найдены.",
    )
    return success_response(final_result, logger.get_logs(), final_result)


def build_shortest_paths_matrix_weighted(matrix: List[List[int]]) -> Dict[str, Any]:
    """Флойд-Уоршелл для графа с настоящими весами ребер."""
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
        message="Инициализируем матрицу расстояний: d[i][i] = 0, d[i][j] = вес ребра если оно есть, иначе ∞.",
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
                f"Рассматриваем вершину <b>{middle}</b> как промежуточную. "
                f"Обновлены пары: {changed_pairs}."
            ),
        )

    final_result = matrix_for_json(dist)
    detailed_results = {"distance_matrix": final_result}
    logger.add_log(
        active_node=None,
        visited_nodes=list(range(n)),
        state_data=detailed_results.copy(),
        message="Алгоритм Флойда–Уоршелла завершён. Матрица кратчайших расстояний построена.",
    )
    return success_response(final_result, logger.get_logs(), detailed_results)


def build_minimum_spanning_tree_weighted(matrix: List[List[int]], start_node: int = 0) -> Dict[str, Any]:
    """Алгоритм Прима для графа с настоящими весами ребер."""
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
        message=f"Запускаем алгоритм Прима. Начальная вершина: <b>{start_node}</b>.",
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
            message = f"Добавляем ребро (<b>{parent[current]}</b>, <b>{current}</b>) в остовное дерево. Вес ребра: {edge_w}."
        else:
            message = f"Включаем начальную вершину <b>{current}</b> в остовное дерево."

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
                        f"Обновляем минимальный вес вершины <b>{neighbor}</b>: "
                        f"новый вес = {matrix[current][neighbor]} через вершину <b>{current}</b>."
                    ),
                )

    final_result = {"mst_edges": mst_edges, "total_weight": total_weight}
    logger.add_log(
        active_node=None,
        visited_nodes=get_visited_nodes(in_mst),
        state_data=final_result.copy(),
        message=f"Минимальное остовное дерево построено. Рёбра: {mst_edges}. Суммарный вес: {total_weight}.",
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
    Общая функция для запуска нужной задачи.

    Никита отправляет со страницы название алгоритма, а здесь мы выбираем,
    какую функцию надо запустить.

    Основные варианты algorithm_name:
    basic, dfs, check_dfs, bfs, check_bfs, components,
    check_components, mst, shortest_paths, shortest_matrix,
    prufer_encode, prufer_decode, coloring.
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
