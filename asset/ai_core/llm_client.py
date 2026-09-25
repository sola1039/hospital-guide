# -*- coding: utf-8 -*-
"""大模型调用封装: OpenAI 兼容接口(小米 MiMo), 配置从项目根目录 .env 读取。

只用标准库 urllib, 不引入额外依赖。
"""
import json
import os
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE, ".env")


def load_env() -> dict:
    env = {}
    if not os.path.exists(ENV_PATH):
        return env
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def get_config() -> dict:
    env = load_env()
    return {
        "base_url": env.get("LLM_BASE_URL", ""),
        "api_key": env.get("LLM_API_KEY", ""),
        "model": env.get("LLM_MODEL", ""),
    }


def chat(messages: list, temperature: float = 0.5, max_tokens: int = 1024, timeout: int = 60) -> str:
    """调用对话接口, 返回助手文本。失败抛出 RuntimeError, 错误信息不带表情符号。"""
    cfg = get_config()
    if not cfg["base_url"] or not cfg["api_key"]:
        raise RuntimeError("未配置 LLM_BASE_URL 或 LLM_API_KEY, 请检查 .env 文件")
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg["api_key"],
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"大模型接口返回 {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"大模型接口连接失败: {e.reason}")
    except TimeoutError:
        raise RuntimeError("大模型接口超时, 请稍后重试")
    try:
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise RuntimeError("大模型接口响应格式异常")


def chat_with_system(system_prompt: str, user_prompt: str, **kwargs) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return chat(messages, **kwargs)
