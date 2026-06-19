"""
加密工具模块 — Fernet 对称加密存储敏感配置

用于安全存储 DeepSeek API Key 等敏感信息:
  - 主密钥: ~/.finguard/master.key (首次自动生成)
  - 加密存储: ./config/secrets.enc (Fernet 加密后的 JSON)

设计原则:
  - 主密钥文件权限 600 (仅 owner 可读写)
  - API Key 绝不以明文落盘
  - 支持运行时临时注入 (不持久化)
"""

import json
import os
import stat
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


# ─── 路径定义 ────────────────────────────────────

MASTER_KEY_PATH = Path.home() / ".finguard" / "master.key"
SECRETS_PATH = Path(".").resolve() / "config" / "secrets.enc"


# ─── 主密钥管理 ──────────────────────────────────

def _ensure_master_key() -> bytes:
    """确保主密钥存在，不存在则生成新的"""
    if MASTER_KEY_PATH.exists():
        return MASTER_KEY_PATH.read_bytes()

    # 生成 Fernet 密钥
    key = Fernet.generate_key()
    MASTER_KEY_PATH.parent.mkdir(mode=0o700, exist_ok=True)
    MASTER_KEY_PATH.write_bytes(key)

    # 设置文件权限为 600 (仅 owner)
    try:
        os.chmod(MASTER_KEY_PATH, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows 下 chmod 行为不同

    return key


def _get_fernet() -> Fernet:
    return Fernet(_ensure_master_key())


# ─── 加密/解密 API ──────────────────────────────

def encrypt_api_key(api_key: str, persist: bool = True) -> str:
    """
    加密 API Key

    Args:
        api_key: 明文 API Key
        persist: True=持久化到文件, False=仅返回密文(会话级)

    Returns:
        密文
    """
    fernet = _get_fernet()
    encrypted = fernet.encrypt(api_key.encode()).decode()

    if persist:
        # 持久化存储
        SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = _load_secrets_file()
        data["deepseek_api_key"] = encrypted
        _save_secrets_file(data)

    return encrypted


def decrypt_api_key() -> str:
    """
    解密 API Key

    Returns:
        明文 API Key，如果未配置则返回空字符串
    """
    data = _load_secrets_file()
    encrypted = data.get("deepseek_api_key", "")

    if not encrypted:
        return ""

    try:
        fernet = _get_fernet()
        return fernet.decrypt(encrypted.encode()).decode()
    except (InvalidToken, Exception):
        return ""


def has_stored_key() -> bool:
    """检查是否已存储 API Key"""
    return bool(decrypt_api_key())


def clear_api_key() -> bool:
    """删除存储的 API Key"""
    data = _load_secrets_file()
    if "deepseek_api_key" in data:
        del data["deepseek_api_key"]
        _save_secrets_file(data)
        return True
    return False


def _load_secrets_file() -> dict:
    """加载加密的 secrets 文件"""
    if not SECRETS_PATH.exists():
        return {}
    try:
        return json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_secrets_file(data: dict):
    """保存加密的 secrets 文件"""
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SECRETS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
