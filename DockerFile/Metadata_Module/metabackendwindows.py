from flask import Flask, request, jsonify
import requests
import time
import sys

app = Flask(__name__)

MODEL_NAME = "llama2:7b"  # Define model name as a constant


def list_models():
    """Check what models are currently downloaded"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking models: {e}")
        return None


def pull_model(model_name=MODEL_NAME):
    """Pull a specific model"""
    print(f"Downloading {model_name}...")
    try:
        response = requests.post(
            "http://localhost:11434/api/pull", json={"name": model_name}
        )
        print("Model downloaded successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error pulling model: {e}")
        return False


def ensure_model_available():
    """Check if model is available and download if not"""
    models = list_models()
    if not models:
        print("Could not fetch model list. Ollama may not be running.")
        sys.exit(1)

    if not any(MODEL_NAME in str(m) for m in models.get("models", [])):
        print(f"Model {MODEL_NAME} not found, downloading...")
        if not pull_model():
            print("Failed to download model. Exiting.")
            sys.exit(1)
        print(f"Successfully downloaded {MODEL_NAME}")
    else:
        print(f"Model {MODEL_NAME} is already available")


@app.route("/generate", methods=["POST"])
def generate_text():
    print("Called generate text")
    data = request.json
    input_text = data.get("input_text", "")

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": MODEL_NAME, "prompt": input_text, "stream": False},
        )
        response.raise_for_status()
        return jsonify({"generated_text": response.json()["response"]})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Starting server...")
    print("Checking available models...")
    ensure_model_available()
    app.run(host="0.0.0.0", port=5002)
