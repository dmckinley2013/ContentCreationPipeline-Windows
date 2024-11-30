import subprocess
from flask import Flask, request, jsonify

# Initialize the Flask app
app = Flask(__name__)

# Function to interact with Ollama via CLI
def generate_with_ollama(prompt):
    # Use subprocess to call the Ollama CLI
    result = subprocess.run(
        ["ollama", "run", "llama2", prompt],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

@app.route('/generate', methods=['POST'])
def generate_text():
    # Get input from the request
    data = request.json
    input_text = data.get("input_text", "")

    # Call Ollama to generate the response
    generated_text = generate_with_ollama(input_text)

    # Return the generated text as JSON
    return jsonify({"generated_text": generated_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
