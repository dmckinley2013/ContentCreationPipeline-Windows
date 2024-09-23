# Content Creation Pipeline
## Setting up the environment

1. **Create a virtual environment** (in the main project directory):
   ```bash
   python -m venv env
   ```

2. **Activate the virtual environment**:
   - On **Windows**:
     ```bash
     env\Scripts\activate
     ```
   - On **Mac/Linux**:
     ```bash
     source env/bin/activate
     ```

3. **Install dependencies** in the local environment:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Docker Containers

Ensure **Docker Desktop** is running if you are on Windows.

1. **Start the Docker containers**:
   ```bash
   docker-compose up --build -d
   ```
## Run the UI
1. **Navigate to the directory where 'dashboard_receiver.py' is located and run:**
   ```bash
   python dashboard_receiver.py
   ```

## Running the Python Scripts

1. **Start listening on port 12345**:
   Navigate to the directory where `parse.py` is located and run:
   ```bash
   python parse.py
   ```

2. **Send data to port 12345** (open a new terminal):
   Navigate to the directory where `main_server.py` is located and run:
   ```bash
   python main_server.py
   ```
