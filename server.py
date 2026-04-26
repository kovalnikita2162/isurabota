from flask import Flask, request, jsonify
from flask_cors import CORS

# Импортируем движок из первого файла
from graph_core import analyze_graph

app = Flask(__name__)
# Разрешаем фронтенду общаться с сервером
CORS(app)

@app.route('/api/analyze', methods=['POST'])
def analyze_my_graph():
    # Получаем JSON от твоего интерфейса
    data = request.get_json()
    
    # Забираем данные (если чего-то нет, берем умолчания)
    matrix = data.get('matrix')
    start_vertex = data.get('start_vertex', 0)
    user_dfs_order = data.get('user_dfs_order')
    user_bfs_order = data.get('user_bfs_order')
    user_components_count = data.get('user_components_count')

    # Если матрицу забыли прислать - ругаемся
    if not matrix:
        return jsonify({"status": "error", "message": "Матрица не предоставлена"}), 400

    # Вызываем математику
    result = analyze_graph(
        matrix=matrix,
        start_vertex=start_vertex,
        user_dfs_order=user_dfs_order,
        user_bfs_order=user_bfs_order,
        user_components_count=user_components_count
    )
    
    # Отправляем JSON обратно в браузер
    return jsonify(result)

if __name__ == '__main__':
    # Запускаем сервер на порту 8000
    app.run(debug=True, port=8000)