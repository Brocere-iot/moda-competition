# FastAPI Server

A lightweight FastAPI application featuring Swagger UI documentation, environment variable configuration, and a mock database for sensor data.

---

## Prerequisites

Before starting, make sure you have a `.env` file created in the root directory:

```env
APP_ENV=development
PORT=8000
HOST=0.0.0.0
```

# Option 1: Local Development (Without Container)
Follow these steps to run the application directly on your local machine using a Python virtual environment.

## 1. Create a Virtual Environment
Open your terminal in the project root directory and create a virtual environment named venv:


``` Bash
python3 -m venv venv
```

## 2. Activate the Virtual Environment
On macOS / Linux:

Bash
source venv/bin/activate
On Windows (Command Prompt):

```
venv\Scripts\activate.bat
```

```
.\venv\Scripts\Activate.ps1
```

## 3. Install Dependencies
Upgrade pip and install all the required Python packages:

```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

## 4. Run the Application
Start the development server using the FastAPI CLI (port 8000):

```bash
fastapi dev main.py
```
OR use custom port from the .env file

```bash
python3 main.py
```

## 5. Access the App
Live API: Open http://localhost:8000 in your browser.

Interactive Swagger UI: Open http://localhost:8000/docs to test the endpoints.

# Option 2: Production Setup (Using Docker Container)
Follow these steps to build and run the application inside an isolated Docker container.

## 1. Build the Docker Image
Build the container image and tag it as fastapi-app:

```bash
docker build -t fastapi-app .
```

## 2. Run the Docker Container
Launch the container in detached mode (-d), exposing port 8000 and injecting your local .env configuration file:

```bash
docker run -d --name fastapi_container -p 8000:8000 --env-file .env fastapi-app
```

3. Access the App Inside Docker
Live API: Open http://localhost:8000

Interactive Swagger UI: Open http://localhost:8000/docs

Useful Docker Commands
View running container logs: docker logs fastapi_container

Stop the container: docker stop fastapi_container

Start the container again: docker start fastapi_container

Remove the container: docker rm -f fastapi_container