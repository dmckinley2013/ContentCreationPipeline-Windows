
import requests
import json
url = "http://10.0.0.26:5002/generate"

# input_text = input("Enter Prompt: ")

payload = {"input_text": "What is your name?"}

response = requests.post(url, json=payload)

if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    generated_text = data.get("generated_text", "No text generated.")

    result = generated_text
    nodesArray = result
    print(nodesArray)   
    print(result)  # Optional: Print it to verify
    
else:
    print(f"Failed to connect to API: {response.status_code}")
   
