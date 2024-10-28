import subprocess
import time
import os

# Define the base directory where your program is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define the commands with their respective directories
commands = [
    # Step 1: Build and run Docker container
    ("docker-compose up --build -d", base_dir),

    # Step 2: Run the parse.py script
    ("python parse.py", os.path.join(base_dir, "Parser_Module")),

    # Step 3: Run the Node server
    ("node server.js", os.path.join(base_dir, "WebSocket_Backend")),

    # Step 4: Run the WebSocket server
    ("python websocket_server.py", os.path.join(base_dir, "WebSocket_Backend")),

    # Step 5: Run the React UI
    ("npm start", os.path.join(base_dir, "react_frontend"))
]

# Run each command with delays in between
for i, (cmd, work_dir) in enumerate(commands):
    print(f"Starting: {cmd} in {work_dir}")

    # Start the process
    process = subprocess.Popen(cmd, shell=True, cwd=work_dir)

    # Add delays between steps to allow for initialization
    if i == 0:  # After starting Docker
        time.sleep(10)  # Adjust this based on how long it takes to start Docker
    elif i == 1:  # After parsing
        time.sleep(2)
    elif i == 2:  # After starting Node server
        time.sleep(2)

    # If it's the last command, wait for it to finish
    if i == len(commands) - 1:
        process.wait()
