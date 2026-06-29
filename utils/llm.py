import re
import json
import httpx
from datetime import datetime, timedelta

from config.settings import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
from config.prompts import NOTIFY_SYSTEM_PROMPT, ANALYZE_SYSTEM_PROMPT


async def _call_llm(system_prompt: str, user_content: str, max_tokens: int = 1024) -> str:
    """
    統一的 LLM 呼叫介面，回傳解析後的純文字內容。
    目前串接 Groq，若要替換其他服務（OpenAI、Ollama 等）只需修改此函式。
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            LLM_BASE_URL,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.1,
                "max_tokens": max_tokens,
            },
        )

    if response.status_code != 200:
        raise Exception(f"LLM API 錯誤: {response.status_code}")

    content = (response.json()["choices"][0]["message"]["content"] or "{}").strip()
    content = re.sub(r"<think>[\s\S]*?</think>", "", content)
    content = re.sub(r"<think>[\s\S]*$", "", content)
    content = content.strip()
    if content.startswith("```"):
        content = "\n".join(content.split("\n")[1:])
        content = content.rstrip("`").strip()
    return content


async def parse_disaster_message(text: str) -> dict:
    """呼叫 LLM 解析來自 LINE 的訊息文字，精煉出關鍵防災欄位"""
    fallback = {
        "location": "未知",
        "primary_hazard": "General_Incident",
        "secondary_hazard": None,
        "severity": "INFO",
        "needs_rescue": False,
        "confidence_score": 0.5,
        "extracted_keywords": [],
        "impact_objects": [],
        "urgent_requests": []
    }
    if not LLM_API_KEY:
        return fallback
    try:
        content = await _call_llm(NOTIFY_SYSTEM_PROMPT, text, max_tokens=512)
        return json.loads(content)
    except Exception as e:
        print(f"[parse_disaster_message] 失敗: {e}")
        return fallback


async def _run_analyze(input_summary: dict) -> dict:
    """核心分析邏輯：呼叫 LLM 判斷災害，回傳 analysis dict"""
    content = await _call_llm(ANALYZE_SYSTEM_PROMPT, json.dumps(input_summary, ensure_ascii=False), max_tokens=512)
    return json.loads(content)


def _build_alert_message(analysis: dict) -> str:
    report_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    return (
        f"🚨 [防災警報] {analysis.get('threat_level', 'WARNING')}\n"
        f"🕐 時間：{report_time}\n"
        f"⚡ 災害類型：{analysis.get('disaster_type', '未知')}\n"
        f"📊 威脅分數：{analysis.get('threat_score', 0)}/100\n"
        f"📋 摘要：{analysis.get('summary', '')}\n"
        f"🆘 建議行動：{analysis.get('recommended_action', '')}"
    )
