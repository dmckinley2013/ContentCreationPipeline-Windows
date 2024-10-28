import subprocess
import time
import os

# Define the base directory where your program is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define the commands with their respective directories
commands = [
    ("docker-compose up --build -d", base_dir),
    ("python parse.py", os.path.join(base_dir, "Parser_Module")),
    ("node server.js", os.path.join(base_dir, "WebSocket_Backend")),
    ("python websocket_server.py", os.path.join(base_dir, "WebSocket_Backend")),
    ("npm start", os.path.join(base_dir, "react_frontend"))
]

# Store processes for shutdown later
processes = []

def run_command(cmd, work_dir, wait_time=0):
    """Runs a command in a specific directory and optionally waits."""
    print(f"\nStarting: {cmd} in {work_dir}")
    process = subprocess.Popen(cmd, shell=True, cwd=work_dir)
    processes.append(process)
    
    # Add a delay if specified
    if wait_time > 0:
        print(f"Waiting for {wait_time} seconds...")
        time.sleep(wait_time)

def shutdown_all():
    """Gracefully shuts down all running processes and Docker containers."""
    print("\nShutting down all processes...")

    # Stop each running process
    for process in processes:
        if process.poll() is None:  # If process is still running
            try:
                process.terminate()  # Try graceful termination
                process.wait(timeout=5)  # Wait for termination
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if not terminated
                print(f"Process {process.pid} killed.")

    # Stop Docker containers
    try:
        subprocess.run("docker-compose down", shell=True, cwd=base_dir, check=True)
        print("Docker containers stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error stopping Docker: {e}")

try:
    # Start Docker containers and wait for 45 seconds
    run_command("docker-compose up --build -d", base_dir, wait_time=45)

    # Run the rest of the commands in sequence
    run_command("python parse.py", os.path.join(base_dir, "Parser_Module"))
    run_command("node server.js", os.path.join(base_dir, "WebSocket_Backend"))
    run_command("python websocket_server.py", os.path.join(base_dir, "WebSocket_Backend"))
    run_command("npm start", os.path.join(base_dir, "react_frontend"))

    # Wait for the React UI process to finish
    processes[-1].wait()

except KeyboardInterrupt:
    print("\nInterrupted by user.")

finally:
    # Graceful shutdown
    shutdown_all()
