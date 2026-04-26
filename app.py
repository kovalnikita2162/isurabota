from flask import Flask, render_template, request, jsonify
from graph_core import run_graph_algorithm

app = Flask(__name__)

TASKS = [
    {
        "id": 0,
        "title": "Базовый анализ графа",
        "description": "Задайте граф матрицей смежности. Система покажет степени вершин, число компонент связности, эйлеровость и двудольность.",
        "algorithm": "basic",
        "input_type": "matrix",
        "needs_start_node": False,
    },
    {
        "id": 1,
        "title": "Обход в глубину (DFS) — показать",
        "description": "Задайте граф и начальную вершину. Система покажет обход в глубину с пошаговой визуализацией.",
        "algorithm": "dfs",
        "input_type": "matrix",
        "needs_start_node": True,
    },
    {
        "id": 2,
        "title": "Обход в глубину (DFS) — проверка",
        "description": "Система предлагает граф. Введите порядок обхода DFS, система проверит правильность.",
        "algorithm": "check_dfs",
        "input_type": "matrix",
        "needs_start_node": True,
        "needs_user_order": True,
    },
    {
        "id": 3,
        "title": "Обход в ширину (BFS) — показать",
        "description": "Задайте граф и начальную вершину. Система покажет обход в ширину с пошаговой визуализацией.",
        "algorithm": "bfs",
        "input_type": "matrix",
        "needs_start_node": True,
    },
    {
        "id": 4,
        "title": "Обход в ширину (BFS) — проверка",
        "description": "Система предлагает граф. Введите порядок обхода BFS, система проверит правильность.",
        "algorithm": "check_bfs",
        "input_type": "matrix",
        "needs_start_node": True,
        "needs_user_order": True,
    },
    {
        "id": 5,
        "title": "Компоненты связности — показать",
        "description": "Задайте граф. Система найдёт и покажет все компоненты связности.",
        "algorithm": "components",
        "input_type": "matrix",
        "needs_start_node": False,
    },
    {
        "id": 6,
        "title": "Компоненты связности — проверка",
        "description": "Система предлагает граф. Введите число компонент связности, система проверит ответ.",
        "algorithm": "check_components",
        "input_type": "matrix",
        "needs_start_node": False,
        "needs_components_count": True,
    },
    {
        "id": 7,
        "title": "Минимальное остовное дерево (Прим)",
        "description": "Задайте взвешенный связный граф. Система построит МОД алгоритмом Прима, минимизируя суммарный вес рёбер.",
        "algorithm": "mst_weighted",
        "input_type": "weighted_matrix",
        "needs_start_node": True,
    },
    {
        "id": 8,
        "title": "Кратчайшие пути от вершины (Дейкстра)",
        "description": "Задайте взвешенный граф и начальную вершину. Дейкстра найдёт пути с минимальной суммой весов рёбер.",
        "algorithm": "shortest_paths_weighted",
        "input_type": "weighted_matrix",
        "needs_start_node": True,
    },
    {
        "id": 9,
        "title": "Матрица кратчайших путей (Флойд-Уоршелл)",
        "description": "Задайте взвешенный граф. Флойд-Уоршелл построит матрицу минимальных расстояний между всеми парами вершин.",
        "algorithm": "shortest_matrix_weighted",
        "input_type": "weighted_matrix",
        "needs_start_node": False,
    },
    {
        "id": 10,
        "title": "Кодирование Прюфера",
        "description": "Задайте дерево матрицей смежности. Система построит код Прюфера.",
        "algorithm": "prufer_encode",
        "input_type": "matrix",
        "needs_start_node": False,
    },
    {
        "id": 11,
        "title": "Декодирование Прюфера",
        "description": "Введите код Прюфера (список чисел через пробел). Система восстановит дерево.",
        "algorithm": "prufer_decode",
        "input_type": "prufer",
        "needs_start_node": False,
    },
    {
        "id": 12,
        "title": "Раскраска графа (жадный алгоритм)",
        "description": "Задайте граф. Система выполнит жадную раскраску вершин с минимальным числом цветов.",
        "algorithm": "coloring",
        "input_type": "matrix",
        "needs_start_node": False,
    },
]

TASK_BY_ID = {t["id"]: t for t in TASKS}


@app.route("/")
def index():
    return render_template("index.html", tasks=TASKS)


@app.route("/task/<int:task_id>")
def task_page(task_id):
    task = TASK_BY_ID.get(task_id)
    if task is None:
        return render_template("index.html", tasks=TASKS, error=f"Задача {task_id} не найдена"), 404
    return render_template("task.html", task=task, tasks=TASKS)


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"status": "error", "final_result": "Пустой запрос", "logs": []}), 400

    algorithm = data.get("algorithm")
    matrix = data.get("matrix")
    start_node = data.get("start_node", 0)
    user_order = data.get("user_order")
    user_components_count = data.get("user_components_count")
    prufer_code = data.get("prufer_code")

    result = run_graph_algorithm(
        algorithm_name=algorithm,
        matrix=matrix,
        start_node=start_node,
        user_order=user_order,
        user_components_count=user_components_count,
        prufer_code=prufer_code,
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
