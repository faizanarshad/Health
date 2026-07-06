from __future__ import annotations

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from src.healthagent import database as db
from src.healthagent.agent import ClinicAgent

load_dotenv()
db.init_db()
agent = ClinicAgent()

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index() -> str:
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat() -> tuple[dict, int]:
    data = request.get_json(silent=True) or {}
    user_input = (data.get("user_input") or "").strip()
    if not user_input:
        return {"error": "No user input provided."}, 400

    try:
        reply = agent.send(user_input)
    except Exception as exc:
        return {"error": str(exc)}, 500

    return {"reply": reply}, 200

if __name__ == "__main__":
    app.run(debug=True)
