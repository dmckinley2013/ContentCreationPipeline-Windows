from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)


def list_models():
    """Check what models are currently downloaded"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking models: {e}")
        return None


def pull_model(model_name="llama2:7b"):
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


@app.route("/generate", methods=["POST"])
def generate_text():
    print("called gen text")
    data = request.json
    input_text = data.get("input_text", "")
    model_name = "llama2:7b"  # Using a smaller model for testing (use mistral if that's the mac default im not really sure what the default on mac is)

    # Check if we have any models
    models = list_models()
    if not models or not any(model_name in str(m) for m in models.get("models", [])):
        print(f"Model {model_name} not found, downloading...")
        pull_model(model_name)

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model_name, "prompt": input_text, "stream": False},
        )
        response.raise_for_status()
        return jsonify({"generated_text": response.json()["response"]})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Starting server...")
    print("Checking available models...")
    models = list_models()
    print(f"Currently available models: {models}")
    app.run(host="0.0.0.0", port=5002)