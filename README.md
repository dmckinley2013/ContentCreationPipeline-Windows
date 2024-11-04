# Installation Guide

## Prerequisites
- Python 3.10 or later
- pip (Python package installer)
- Node.js and npm (for React frontend)
- Docker and Docker Compose

## Setup Instructions

### 1. Create a Virtual Environment

This keeps your project dependencies isolated from other Python projects.

Windows:
```bash
# Create virtual environment
python -m venv dashboard_env

# Activate virtual environment
dashboard_env\Scripts\activate
```

Mac/Linux:
```bash
# Create virtual environment
python -m venv dashboard_env

# Activate virtual environment
source dashboard_env/bin/activate
```

You'll know it's activated when you see `(dashboard_env)` at the start of your terminal line.

### 2. Install Python Dependencies

With your virtual environment activated:
```bash
# Install all required packages
pip install -r requirements.txt

# Install spaCy language model
python -m spacy download en_core_web_lg
```

### 3. Install Node.js Dependencies

For the React frontend:
```bash
cd react_frontend
npm install
cd ..
```

For the WebSocket backend:
```bash
cd WebSocket_Backend
npm install
cd ..
```

### 4. Verify Installation

Test that key packages are installed:
```bash
python -c "import pika; import pymongo; import websockets; import spacy; print('All core packages installed successfully!')"
```

### 5. Running the Application

Use the provided startup script:
```bash
python run_all.py
```

This will:
1. Start Docker containers
2. Launch the Parser Module
3. Start the WebSocket backend
4. Start the React frontend

Important Note: If you see the program start compiling before the Docker containers are fully initialized (before RabbitMQ is ready), stop the program (Ctrl+C) and run it again. Sometimes the 45-second initialization wait time isn't enough for Docker containers to fully start. This is being updated to use dynamic checking instead of a fixed wait time.

### 6. Running Tests with Main Server

After your application is running (Docker containers initialized and all services started), you can run tests using the main server:

```bash
# Navigate to the Main Server directory
cd BuildingTheDashboardModule/DockerFile/Main_Server

# Run the main server
python main_server.py
```

**Important Notes for Testing:**
1. Only run `main_server.py` after all other services are fully initialized and running
2. Make sure:
   - Docker containers are fully initialized (RabbitMQ is ready)
   - Parser Module is running
   - WebSocket servers are running
   - React frontend is running
3. You should see the dashboard update in real-time as tests are processed

If you encounter connection errors:
1. Stop main_server.py (`Ctrl+C`)
2. Verify all other services are running properly
3. Try running main_server.py again

## Troubleshooting Common Issues

### Python/pip Issues

1. **"Package not found" errors:**
   ```bash
   # Try updating pip
   python -m pip install --upgrade pip
   
   # Then reinstall requirements
   pip install -r requirements.txt
   ```

2. **Visual C++ Build Tools error (Windows):**
   - Download and install Build Tools from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Restart your terminal and try installation again

3. **spaCy model download fails:**
   ```bash
   # Alternative download method
   pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.5.0/en_core_web_lg-3.5.0-py3-none-any.whl
   ```

### Docker Issues

1. **Docker containers won't start:**
   ```bash
   # Remove existing containers
   docker-compose down
   
   # Clean up Docker system
   docker system prune
   
   # Try starting again
   docker-compose up --build
   ```

2. **Port conflicts:**
   - Check if ports are in use: `netstat -ano | findstr PORT_NUMBER`
   - Stop conflicting services or modify port numbers in docker-compose.yml

### Node.js/React Issues

1. **npm install fails:**
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Try installation again
   npm install
   ```

2. **Module not found errors:**
   ```bash
   # Remove node_modules and try fresh install
   rm -rf node_modules
   rm package-lock.json
   npm install
   ```

## Virtual Environment Tips

- To deactivate the virtual environment when you're done:
  ```bash
  deactivate
  ```

- If you install new packages, update requirements.txt:
  ```bash
  pip freeze > requirements.txt
  ```

- To completely remove the virtual environment:
  ```bash
  # Windows
  rmdir /s /q dashboard_env
  
  # Mac/Linux
  rm -rf dashboard_env
  ```



