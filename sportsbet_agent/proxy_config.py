#!/usr/bin/env python3
"""
智慧代理與組態管理模組 (proxy_config.py)
支援 M1 Mac mini Surfshark AU Docker 隧道 (192.168.68.118:8888) 與本機代理自動偵測切換。
"""

import json
import socket
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"


def load_agent_config() -> Dict[str, Any]:
    """讀取 sportsbet_agent/config.json"""
    defaults = {
        "proxy_server": "http://192.168.68.118:8888",
        "fallback_proxies": ["http://127.0.0.1:8888", "http://192.168.68.118:8888"],
        "telegram_bot_token": "",
        "allowed_chat_id": "",
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def save_agent_config(new_cfg: Dict[str, Any]) -> bool:
    """儲存組態至 sportsbet_agent/config.json"""
    try:
        current = load_agent_config()
        current.update(new_cfg)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def is_proxy_reachable(proxy_url: Optional[str], timeout: float = 0.4) -> bool:
    """快速 TCP 探測代理伺服器是否可連線"""
    if not proxy_url:
        return False
    try:
        parsed = urlparse(proxy_url)
        host = parsed.hostname
        port = parsed.port or 8888
        if not host:
            return False
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def get_active_proxy() -> Optional[str]:
    """
    依序探測並回傳目前可用的澳洲代理伺服器 URL；
    優先檢查本機 loopback (M1 本機直連最快)，其次檢查 config.json 設定之區網節點 (M4 跨機連線)。
    """
    cfg = load_agent_config()
    candidates = ["http://127.0.0.1:8888"]
    primary = cfg.get("proxy_server")
    if primary and primary not in candidates:
        candidates.append(primary)
    for fb in cfg.get("fallback_proxies", []):
        if fb and fb not in candidates:
            candidates.append(fb)

    for proxy_url in candidates:
        if is_proxy_reachable(proxy_url):
            return proxy_url
    return None


def check_proxy_exit_ip(proxy_url: Optional[str] = None) -> Dict[str, Any]:
    """檢查目前出口 IP 與所在地 (驗證是否為澳洲 AU)"""
    import requests

    target_proxy = proxy_url if proxy_url is not None else get_active_proxy()
    proxies = {"http": target_proxy, "https": target_proxy} if target_proxy else None
    try:
        resp = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        data["proxy_used"] = target_proxy or "Direct (無獨立代理)"
        data["ok"] = True
        return data
    except Exception as e:
        return {
            "ok": False,
            "proxy_used": target_proxy or "Direct (無獨立代理)",
            "error": str(e),
        }


def telegram_send_message(text: str) -> bool:
    """只讀通知輔助函式：透過 Telegram Bot 傳送比價報告"""
    import urllib.parse
    import urllib.request

    cfg = load_agent_config()
    token = cfg.get("telegram_bot_token", "")
    chat_id = cfg.get("allowed_chat_id", "")
    if not token or not chat_id:
        return False
    try:
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
        urllib.request.urlopen(req, timeout=8)
        return True
    except Exception:
        return False
