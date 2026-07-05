#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 配置加密工具
使用 Fernet (AES-128-CBC + HMAC) 对称加密
加密内容：API Key、Base URL、Model
"""

import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".llm_config.enc")
SALT = b"diviner_llm_salt_2026"


def _derive_key(master_password: str) -> bytes:
    """从主密码派生加密密钥"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode("utf-8")))


def _encrypt(data: dict, master_password: str) -> str:
    """加密整个配置字典"""
    key = _derive_key(master_password)
    f = Fernet(key)
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return f.encrypt(raw).decode("utf-8")


def _decrypt(master_password: str) -> dict | None:
    """解密配置"""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r") as f:
            saved = json.load(f)
        encrypted = saved.get("encrypted_config", "")
        if not encrypted:
            return None
        key = _derive_key(master_password)
        f = Fernet(key)
        raw = f.decrypt(encrypted.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def save_encrypted_config(api_key: str, base_url: str, model: str,
                          master_password: str = "diviner_default"):
    """加密保存完整 LLM 配置"""
    config = {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
    }
    encrypted = _encrypt(config, master_password)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"encrypted_config": encrypted}, f, ensure_ascii=False)
    os.chmod(CONFIG_FILE, 0o600)
    print(f"✓ LLM 配置已加密保存到 {CONFIG_FILE}")
    print(f"  Provider: {base_url}")
    print(f"  Model: {model}")


def get_llm_config(master_password: str | None = None) -> dict:
    """
    获取 LLM 配置（优先级：环境变量 > 加密文件）
    返回 {"api_key": ..., "base_url": ..., "model": ...}
    """
    # 1. 环境变量优先
    env_key = os.environ.get("LLM_API_KEY")
    env_url = os.environ.get("LLM_BASE_URL")
    env_model = os.environ.get("LLM_MODEL")

    if env_key:
        return {
            "api_key": env_key,
            "base_url": env_url or "https://api.openai.com/v1",
            "model": env_model or "gpt-4o-mini",
        }

    # 2. 加密文件
    if master_password:
        config = _decrypt(master_password)
        if config:
            return config

    # 3. 默认主密码
    default_pw = os.environ.get("LLM_MASTER_PASSWORD", "diviner_default")
    config = _decrypt(default_pw)
    if config:
        return config

    return {}


def get_api_key(master_password: str | None = None) -> str | None:
    """便捷方法：只获取 API Key"""
    return get_llm_config(master_password).get("api_key")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法：")
        print("  加密保存：python crypto_utils.py encrypt <api_key> <base_url> <model> [master_password]")
        print("  解密查看：python crypto_utils.py decrypt [master_password]")
        print("  环境变量：export LLM_API_KEY=your_key  （推荐）")
        sys.exit(1)

    action = sys.argv[1]
    if action == "encrypt":
        if len(sys.argv) < 5:
            print("缺少参数: python crypto_utils.py encrypt <api_key> <base_url> <model>")
            sys.exit(1)
        api_key = sys.argv[2]
        base_url = sys.argv[3]
        model = sys.argv[4]
        master_pw = sys.argv[5] if len(sys.argv) > 5 else "diviner_default"
        save_encrypted_config(api_key, base_url, model, master_pw)
    elif action == "decrypt":
        master_pw = sys.argv[2] if len(sys.argv) > 2 else "diviner_default"
        config = get_llm_config(master_pw)
        if config:
            print(f"Provider: {config.get('base_url')}")
            print(f"Model: {config.get('model')}")
            k = config.get('api_key', '')
            print(f"API Key: {k[:8]}...{k[-4:] if len(k)>4 else ''}")
        else:
            print("解密失败或未配置")