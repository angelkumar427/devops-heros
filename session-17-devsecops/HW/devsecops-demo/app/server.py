"""Small notes API used as the subject of the DevSecOps pipeline."""
import os

from flask import Flask, abort, jsonify, request

app = Flask(__name__)
VERSION = os.environ.get("APP_VERSION", "dev")
MAX_NOTE_LENGTH = 500

_notes: dict[int, str] = {}
_next_id = 1


@app.get("/health")
def health():
    return jsonify(status="ok", version=VERSION)


@app.get("/notes")
def list_notes():
    return jsonify([{"id": i, "text": t} for i, t in sorted(_notes.items())])


@app.post("/notes")
def create_note():
    global _next_id
    payload = request.get_json(silent=True) or {}
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        abort(400, description="'text' must be a non-empty string")
    if len(text) > MAX_NOTE_LENGTH:
        abort(400, description=f"'text' must be at most {MAX_NOTE_LENGTH} characters")
    note_id = _next_id
    _notes[note_id] = text.strip()
    _next_id += 1
    return jsonify(id=note_id, text=_notes[note_id]), 201


@app.get("/notes/<int:note_id>")
def get_note(note_id):
    if note_id not in _notes:
        abort(404, description="note not found")
    return jsonify(id=note_id, text=_notes[note_id])


@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(err):
    return jsonify(error=err.description), err.code


def reset():
    """Test helper: clear in-memory state."""
    global _next_id
    _notes.clear()
    _next_id = 1


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))  # nosec B104 - container listens on all interfaces by design
