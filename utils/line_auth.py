import hashlib
import hmac
import base64

from fastapi import HTTPException, Request

from config.settings import LINE_CHANNEL_SECRET


async def verify_line_signature(request: Request):
    """
    FastAPI Dependency：驗證 LINE Webhook 的 X-Line-Signature header。
    使用 HMAC-SHA256 對 raw request body 簽章後比對。
    """
    if not LINE_CHANNEL_SECRET:
        print("[LINE Auth] 警告：LINE_CHANNEL_SECRET 未設定，略過簽章驗證")
        return

    signature = request.headers.get("X-Line-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="缺少 X-Line-Signature header")

    body = await request.body()
    expected = base64.b64encode(
        hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    ).decode()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="LINE Webhook 簽章驗證失敗")
