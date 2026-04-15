import os

from flask import Flask, jsonify, render_template, request

from services import dum_e_runtime as runtime

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    return jsonify(runtime.get_status())


@app.route("/command", methods=["POST"])
def command():
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    action = data.get("action")
    target = data.get("target")

    if text is not None and str(text).strip() != "":
        result = runtime.parse_and_send_text(str(text), source="web")
        return jsonify(result), 200 if result.get("ok") else 400

    if action is not None and str(action).strip() != "":
        result = runtime.send_command(str(action), target=target, source="web")
        return jsonify(result), 200 if result.get("ok") else 400

    return jsonify({"ok": False, "error": "missing_text_or_action"}), 400


if __name__ == "__main__":
    # Default 5001: macOS often reserves 5000 for AirPlay Receiver.
    port = int(os.environ.get("PORT", "5001"))
    print("DUM-E dashboard: http://127.0.0.1:" + str(port) + "  (set PORT= to override)")
    app.run(host="0.0.0.0", port=port, debug=True)
