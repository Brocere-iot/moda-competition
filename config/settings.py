import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", 8000))
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# LLM 服務設定：預設接 Groq，改 env var 即可切換其他 OpenAI-compatible 服務
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3-32b")

# Token 限制：system_prompt + user_content 合計上限，超過則拒絕呼叫
LLM_MAX_INPUT_TOKENS = int(os.getenv("LLM_MAX_INPUT_TOKENS", 2048))
