from flask import Flask, jsonify, request

app = Flask(__name__)


tasks = []


@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to TaskFlow",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    }), 200


@app.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify(tasks), 200


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({
            "error": "Task title is required"
        }), 400

    task = {
        "id": len(tasks) + 1,
        "title": data["title"]
    }

    tasks.append(task)

    return jsonify(task), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
