import requests
import time
import json
import os

# ================== 必填 ==================
ETHERSCAN_API_KEY = "JYYBAFSGKCJ3EBAH95XANYUNA4861MCHEV"
BOT_TOKEN = "8535508785:AAFhFhGO25JuEgt82irYUl_3C9HZVRWa4zc"
CHAT_ID = "7110719754"
# =========================================

USDT_ERC20 = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
USDT_TRC20 = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"

ETHERSCAN_API = "https://api.etherscan.io/api"
TRONSCAN_API = "https://apilist.tronscan.org/api"

STATE_FILE = "seen_tx.json"
SUMMARY_FILE = "hour_summary.json"
SUMMARY_INTERVAL = 3600


def send_telegram(text):
    url = f"https://api.telegram.org/bot8535508785:AAFhFhGO25JuEgt82irYUl_3C9HZVRWa4zc/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)


def load_addresses(file):
    if not os.path.exists(file):
        return []
    with open(file) as f:
        return [i.strip().lower() for i in f if i.strip()]


def safe_get_json(url, params):
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200 or not r.text.strip():
            return None
        return r.json()
    except Exception:
        return None


# ================= 启动时统计余额 =================

# def get_erc20_balance(addr):
#     data = safe_get_json(ETHERSCAN_API, {
#         "module": "account",
#         "action": "tokenbalance",
#         "contractaddress": USDT_ERC20,
#         "address": addr,
#         "tag": "latest"
#     })
#     if not data or "result" not in data:
#         return 0
#     return int(data["result"]) / 1e6

def get_erc20_balance(addr):
    data = safe_get_json(
        "https://api.etherscan.io/v2/api",
        {
            "chainid": 1,
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": USDT_ERC20,
            "address": addr,
            "tag": "latest",
            "apikey": ETHERSCAN_API_KEY
        }
    )

    if not data:
        return 0

    result = data.get("result")
    if not result or not str(result).isdigit():
        return 0

    return int(result) / 1e6


def get_trc20_balance(addr):
    data = safe_get_json(f"{TRONSCAN_API}/account/tokens", {
        "address": addr
    })
    if not data or "data" not in data:
        return 0

    for token in data["data"]:
        if token.get("tokenId") == USDT_TRC20:
            return float(token.get("balance", 0)) / 1e6
    return 0


def startup_balance_report(erc20, trc20):
    erc_total = sum(get_erc20_balance(a) for a in erc20)
    trc_total = sum(get_trc20_balance(a) for a in trc20)

    send_telegram(
        "🚀 监听启动 · 当前 USDT 总额\n"
        f"ERC20 总额: {erc_total:.2f}\n"
        f"TRC20 总额: {trc_total:.2f}\n"
        f"合计: {(erc_total + trc_total):.2f}"
    )


# ================= 监听相关 =================

def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen), f)


def load_summary():
    if os.path.exists(SUMMARY_FILE):
        with open(SUMMARY_FILE) as f:
            return json.load(f)
    return {
        "start": time.time(),
        "erc20_in": 0.0,
        "erc20_out": 0.0,
        "trc20_in": 0.0,
        "trc20_out": 0.0
    }


def save_summary(s):
    with open(SUMMARY_FILE, "w") as f:
        json.dump(s, f)


def check_and_send_summary(s):
    if time.time() - s["start"] >= SUMMARY_INTERVAL:
        send_telegram(
            "⏰ 近 1 小时 USDT 汇总\n"
            f"ERC20 转入: {s['erc20_in']:.2f}\n"
            f"ERC20 转出: {s['erc20_out']:.2f}\n"
            f"TRC20 转入: {s['trc20_in']:.2f}\n"
            f"TRC20 转出: {s['trc20_out']:.2f}"
        )
        s.update({
            "start": time.time(),
            "erc20_in": 0,
            "erc20_out": 0,
            "trc20_in": 0,
            "trc20_out": 0
        })


# ================= 主程序 =================

def main():
    erc20 = load_addresses("erc20.txt")
    trc20 = load_addresses("trc20.txt")

    startup_balance_report(erc20, trc20)

    seen = load_seen()
    summary = load_summary()

    send_telegram("✅ 转入 / 转出监听已启动")

    while True:
        try:
            check_and_send_summary(summary)
            save_seen(seen)
            save_summary(summary)
        except Exception as e:
            send_telegram(f"⚠️ 异常: {e}")

        time.sleep(120)


if __name__ == "__main__":
    main()

