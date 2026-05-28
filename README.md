# FastAPI Server

A lightweight FastAPI application featuring Swagger UI documentation, environment variable configuration, and a mock database for sensor data.

---

## Prerequisites

Before starting, make sure you have a `.env` file created in the root directory:

```env
PORT=8000
LINE_CHANNEL_ACCESS_TOKEN=Your_LINE_Channel_Access_Token
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

NOTE: port can be changed inside the 'run' command. E.g. 3000:3000
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

---

# Option 3: LINE Webhook + ngrok Integration

Expose your local FastAPI server to the internet so LINE can deliver webhook events to your `/notify` endpoint.

<p align="center"><img src="output.gif" width="300" /></p>

## Architecture

```
LINE User sends a message
    ↓
LINE Platform
    ↓ webhook POST
ngrok public URL (https://xxxx.ngrok-free.app/notify)
    ↓ tunnels to
Local FastAPI (localhost:8000/notify)
    ↓ processes + replies
LINE User receives the response
```

## 1. Install ngrok

```bash
brew install ngrok
```

Sign up at [https://ngrok.com](https://ngrok.com) to get your Auth Token, then:

```bash
ngrok config add-authtoken <YOUR_TOKEN>
```

## 2. Start Both Services

Open two separate terminals:

```bash
# Terminal 1 - Start FastAPI
python3 main.py
```

```bash
# Terminal 2 - Start ngrok
ngrok http 8000
```

ngrok will display a public URL, for example:

```
Forwarding  https://xxxx.ngrok-free.app -> localhost:8000
```

## 3. Configure LINE Webhook

1. Go to [LINE Developers Console](https://developers.line.biz/)
2. Select your Messaging API Channel
3. Set the **Webhook URL** to:
   ```
   https://xxxx.ngrok-free.app/notify
   ```
4. Enable **Use webhook**
5. Click **Verify** to confirm the connection
