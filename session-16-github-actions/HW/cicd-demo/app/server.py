"""HTTP API around the calculator, so the pipeline has something to deploy."""
import os

from flask import Flask, jsonify, request

from app.calculator import OPERATIONS

app = Flask(__name__)
VERSION = os.environ.get("APP_VERSION", "dev")


@app.get("/health")
def health():
    return jsonify(status="ok", version=VERSION)


@app.get("/<op>")
def calculate(op):
    if op not in OPERATIONS:
        return jsonify(error=f"unknown operation '{op}'"), 404
    try:
        a = float(request.args["a"])
        b = float(request.args["b"])
    except (KeyError, ValueError):
        return jsonify(error="query parameters a and b must be numbers"), 400
    try:
        return jsonify(operation=op, a=a, b=b, result=OPERATIONS[op](a, b))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
