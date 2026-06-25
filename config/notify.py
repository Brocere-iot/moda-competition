import os
import requests
from dotenv import load_dotenv


LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# Replace original 'push' with 'broadcast' to send messages to all users
LINE_MESSAGING_API_URL = "https://api.line.me/v2/bot/message/broadcast"

def broadcast_line_bot_message(message: str):
    try:
        session = requests.Session()
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [
                {
                    "type": "text", 
                    "text": message
                }
            ]
    }

        try:
            r = session.post(LINE_MESSAGING_API_URL, headers=headers, json=payload)
            r.raise_for_status()  
        except requests.exceptions.RequestException as e:
            print(f"LINE messaging API failed: {str(e)}")
        # Add key to the redis cache

    except Exception as e:
        print(f"LINE notify failed: {str(e)}")

    finally:
        session.close()
        return True

if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    test_message = "This is a test message from the LINE bot."
    broadcast_line_bot_message(test_message)