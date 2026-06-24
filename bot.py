import os, requests, time

TOKEN = os.environ["BOT_TOKEN"]
BASE  = f"https://api.telegram.org/bot{TOKEN}"
APP_URL = "https://lkzit.github.io/pusheen-slicer/"

stats = {"players": set(), "payments": 0, "stars": 0, "shield": 0, "energy": 0}

def api(method, **kwargs):
    try:
        return requests.post(f"{BASE}/{method}", json=kwargs, timeout=8).json()
    except Exception as e:
        print(f"api error {method}: {e}", flush=True)
        return {}

def set_menu_button(chat_id=None):
    payload = {"type": "web_app", "text": "🔪 Резать", "web_app": {"url": APP_URL}}
    if chat_id:
        api("setChatMenuButton", chat_id=chat_id, menu_button=payload)
    else:
        api("setChatMenuButton", menu_button=payload)

def send(chat_id, text, markup=None):
    kwargs = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if markup:
        kwargs["reply_markup"] = markup
    api("sendMessage", **kwargs)

def handle_message(msg):
    uid  = msg["from"]["id"]
    text = msg.get("text", "")
    stats["players"].add(uid)

    if text == "/start":
        set_menu_button(uid)
        send(uid,
            "🔪 <b>PUSHEEN SLICER</b>\n\n"
            "Режь Пун Пуна и зарабатывай мясо 🥩\n"
            "Щит спасёт Пун Пуна на 60 секунд 🛡\n\n"
            "Жми кнопку <b>🔪 Резать</b> внизу 👇",
            markup={"inline_keyboard": [[
                {"text": "🔪 Играть", "web_app": {"url": APP_URL}}
            ]]}
        )
    elif text == "/stats":
        send(uid,
            f"📊 <b>Статистика Pusheen Slicer</b>\n\n"
            f"👥 Игроков: <b>{len(stats['players'])}</b>\n"
            f"💫 Покупок: <b>{stats['payments']}</b>\n"
            f"⭐ Stars собрано: <b>{stats['stars']}</b>\n"
            f"🛡 Щитов куплено: <b>{stats['shield']}</b>\n"
            f"⚡ Энергий куплено: <b>{stats['energy']}</b>"
        )

def handle_payment(msg):
    sp  = msg["successful_payment"]
    uid = msg["from"]["id"]
    payload = sp.get("invoice_payload", "")
    amount  = sp["total_amount"]
    stats["payments"] += 1
    stats["stars"]    += amount
    if payload == "shield_60":
        stats["shield"] += 1
    elif payload == "energy_refill":
        stats["energy"] += 1
    print(f"Payment {amount} XTR ({payload}) from {uid}", flush=True)

def main():
    set_menu_button()
    offset = 0
    print("Bot started", flush=True)
    while True:
        try:
            r = requests.get(f"{BASE}/getUpdates",
                             params={"offset": offset, "timeout": 30,
                                     "allowed_updates": ["message", "pre_checkout_query"]},
                             timeout=35)
            for u in r.json().get("result", []):
                offset = u["update_id"] + 1
                if "pre_checkout_query" in u:
                    pcq = u["pre_checkout_query"]
                    print(f"PCQ from {pcq['from']['id']}", flush=True)
                    api("answerPreCheckoutQuery", pre_checkout_query_id=pcq["id"], ok=True)
                elif "message" in u:
                    msg = u["message"]
                    if msg.get("successful_payment"):
                        handle_payment(msg)
                    else:
                        handle_message(msg)
        except Exception as e:
            print(f"Error: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main()
