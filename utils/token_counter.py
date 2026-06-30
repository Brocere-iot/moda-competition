import os
import sys

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

try:
    from transformers import AutoTokenizer
    _TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
except Exception as e:
    _TOKENIZER = None


def count_tokens(text: str) -> int:
    """
    在本地端計算輸入文字的 Token 數量（防止呼叫 API 前超額）
    """
    if not text:
        return 0

    if _TOKENIZER:
        try:
            return len(_TOKENIZER.encode(text))
        except Exception:
            pass

    try:
        import tiktoken
        import unicodedata
        encoding = tiktoken.get_encoding("cl100k_base")
        cjk_chars = [c for c in text if unicodedata.category(c).startswith("Lo")]
        non_cjk = "".join(c for c in text if not unicodedata.category(c).startswith("Lo"))
        cjk_tokens = int(len(cjk_chars) * 0.65)
        non_cjk_tokens = len(encoding.encode(non_cjk)) if non_cjk else 0
        return cjk_tokens + non_cjk_tokens
    except Exception:
        return int(len(text) * 0.8)
