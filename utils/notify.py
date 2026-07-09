import os
import logging
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# Replace original 'push' with 'broadcast' to send messages to all users
LINE_MESSAGING_API_URL = "https://api.line.me/v2/bot/message/broadcast"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_API_URL = "https://api.line.me/v2/bot/message/reply"

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
            logger.error("LINE broadcast request failed: %s", e, exc_info=True)
            return
        # Add key to the redis cache

    except Exception as e:
        logger.error("LINE broadcast unexpected error: %s", e, exc_info=True)
        return

    finally:
        session.close()
        return True

def send_line_reply(reply_token: str, reply_text: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": reply_text
            }
        ]
    }
    # 發送 POST 請求給 LINE 
    response = requests.post(LINE_API_URL, headers=headers, json=payload)
    return


def send_line_push(user_id: str, message: str):
    """主動推播 LINE 訊息給指定 user_id（不需 reply_token）"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(LINE_PUSH_URL, headers=headers, json=payload)
    return


# if __name__ == "__main__":
#     load_dotenv()  # Load environment variables from .env file
#     test_message = "This is a test message from the LINE bot."
#     broadcast_line_bot_message(test_message)