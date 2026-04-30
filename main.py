# -*- coding: utf-8 -*-
import os
import asyncio
import re
import requests
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MY_USER = os.getenv("MY_USER")
MY_PASS = os.getenv("MY_PASS")

TARGET_URL = "http://51.210.208.26/ints/client/SMSCDRStats"
LOGIN_URL = "http://51.210.208.26/ints/login"

FB_URL = "https://family-adc9d-default-rtdb.firebaseio.com/bot"

ADMIN_LINK = "https://t.me/jisansheikh"
BOT_LINK = "https://t.me/Paradox_Number_Bot"
DV_LINK = "https://t.me/jisansheikh"
CN_LINK = "https://t.me/The_Peradox_Tips"

sent_msgs = {}
START_TIME = time.time()

def update_firebase(num, msg, date_str):
    try:
        url = f"{FB_URL}/sms_logs/{num}.json"
        payload = {
            "number": num,
            "message": msg,
            "time": date_str,
            "paid": False
        }
        requests.put(url, json=payload, timeout=5)
    except:
        pass

def extract_otp(msg):
    match = re.search(r'\b(\d{3,8}|\d{3}-\d{3}|\d{4}\s\d{4})\b', msg)
    return match.group(0) if match else "N/A"

def send_telegram(date_str, num, sms_text, otp, cli_source, is_update=False):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    masked = num[:4] + "PD" + num[-4:] if len(num) > 8 else num

    header = "🔄🛎️ <b>UPDATED SMS RECEIVED</b>" if is_update else "🛎️ <b>NEW SMS RECEIVED</b>"

    text = f"{header}\n\n" \
           f"📞 <b>Number:</b> <code>{masked}</code>\n" \
           f"🌐 <b>Service:</b> <code>{cli_source}</code>\n\n" \
           f"🔑 <b>OTP:</b> <code>{otp}</code>\n\n" \
           f"📩 <b>Full Message:</b><blockquote>{sms_text}</blockquote>\n"

    keyboard = [
        [
            {"text": "👨‍🦲Admin", "url": ADMIN_LINK},
            {"text": "🔢Number bot", "url": BOT_LINK}
        ],
        [
            {"text": "💥Channel", "url": CN_LINK},
            {"text": "💻 Developer", "url": DV_LINK}
        ]
    ]

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": keyboard}
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except:
        return False

async def start_bot():
    print("🚀 Bot started...")

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        async def login():
            try:
                print("[LOGIN] Navigating to login page...")
                await page.goto(LOGIN_URL, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)
                
                # Debug: print page title and url
                print(f"[LOGIN] Current URL: {page.url}")
                print(f"[LOGIN] Page title: {await page.title()}")
                
                # Check if already logged in
                if "login" not in page.url.lower():
                    print("[LOGIN] Already logged in (no login in URL)")
                    return True
                
                login_result = await page.evaluate(f"""() => {{
                    const myUser = "{MY_USER}";
                    const myPass = "{MY_PASS}";
                    let userField, passField, ansField;

                    document.querySelectorAll('input').forEach(inp => {{
                        let p = (inp.placeholder || "").toLowerCase();

                        if (inp.type === 'password') passField = inp;
                        else if (p.includes('user') || inp.type === 'text') {{
                            if (!userField && !p.includes('answer')) userField = inp;
                        }}

                        if (p.includes('answer') || (inp.name || "").includes('ans')) ansField = inp;
                    }});

                    let match = document.body.innerText.match(/What is\\s+(\\d+)\\s*\\+\\s*(\\d+)/i);
                    let sum = match ? (parseInt(match[1]) + parseInt(match[2])) : "";

                    return {{
                        userFound: !!userField,
                        passFound: !!passField,
                        ansFound: !!ansField,
                        sum: sum,
                        bodyText: document.body.innerText.substring(0, 500)
                    }};
                }}""")
                
                print(f"[LOGIN] Fields found - User: {login_result['userFound']}, Pass: {login_result['passFound']}, Ans: {login_result['ansFound']}")
                print(f"[LOGIN] Captcha sum: {login_result['sum']}")
                print(f"[LOGIN] Body preview: {login_result['bodyText'][:200]}")

                if not login_result['userFound'] or not login_result['passFound']:
                    print("[LOGIN] ⚠️ Required fields not found!")
                    # Screenshot for debug
                    await page.screenshot(path="/tmp/login_debug.png")
                    print("[LOGIN] Screenshot saved to /tmp/login_debug.png")
                    return False

                await page.evaluate(f"""() => {{
                    const myUser = "{MY_USER}";
                    const myPass = "{MY_PASS}";
                    let userField, passField, ansField;

                    document.querySelectorAll('input').forEach(inp => {{
                        let p = (inp.placeholder || "").toLowerCase();
                        if (inp.type === 'password') passField = inp;
                        else if (p.includes('user') || inp.type === 'text') {{
                            if (!userField && !p.includes('answer')) userField = inp;
                        }}
                        if (p.includes('answer') || (inp.name || "").includes('ans')) ansField = inp;
                    }});

                    let match = document.body.innerText.match(/What is\\s+(\\d+)\\s*\\+\\s*(\\d+)/i);
                    let sum = match ? (parseInt(match[1]) + parseInt(match[2])) : "";

                    userField.value = myUser;
                    passField.value = myPass;
                    if (ansField && sum !== "") {{
                        ansField.value = sum;
                        ansField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}

                    userField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    passField.dispatchEvent(new Event('input', {{ bubbles: true }}));

                    // Try all buttons that could be login/sign in
                    let clicked = false;
                    for (let b of document.querySelectorAll('button, input[type="submit"]')) {{
                        let btnText = (b.innerText || b.value || "").toLowerCase();
                        if (btnText.includes('login') || btnText.includes('sign in') || btnText.includes('signin')) {{
                            b.click();
                            clicked = true;
                            break;
                        }}
                    }}
                    if (!clicked) {{
                        let fb = document.querySelector('button[type="submit"], input[type="submit"]');
                        if (fb) fb.click();
                    }}
                }}""")
                
                await page.wait_for_timeout(5000)
                print(f"[LOGIN] After submit URL: {page.url}")
                
                if "login" in page.url.lower():
                    print("[LOGIN] ⚠️ Still on login page - login failed!")
                    await page.screenshot(path="/tmp/login_failed.png")
                    return False
                
                print("[LOGIN] ✅ Login successful!")
                return True
            except Exception as e:
                print(f"[LOGIN] ❌ Error: {e}")
                return False

        login_success = await login()
        print(f"[MAIN] Login result: {login_success}")
        
        if not login_success:
            print("[MAIN] ❌ Cannot proceed without login. Exiting loop.")
            # Keep browser alive to inspect
            await asyncio.sleep(60)
            return

        is_first_scan = True
        loop_count = 0

        while True:
            try:
                loop_count += 1
                if loop_count % 300 == 0:
                    print(f"[MAIN] Loop #{loop_count} - still running...")
                
                await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(2000)

                if "login" in page.url.lower():
                    print(f"[MAIN] ⚠️ Session expired, re-logging in...")
                    await login()
                    continue

                valid_rows = []
                rows = await page.query_selector_all("table tbody tr")
                
                if loop_count == 1 or loop_count % 60 == 0:
                    print(f"[MAIN] Found {len(rows)} table rows")

                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) >= 6:
                        d = (await cols[0].inner_text()).strip()
                        n = (await cols[2].inner_text()).strip()
                        s = (await cols[4].inner_text()).strip()
                        cli = (await cols[3].inner_text()).strip()

                        if d and len(re.sub(r'\D', '', n)) >= 8:
                            valid_rows.append({
                                "date": d,
                                "num": n,
                                "sms": s,
                                "cli": cli
                            })

                if loop_count == 1:
                    print(f"[MAIN] First scan: {len(valid_rows)} valid entries found")
                    if valid_rows:
                        print(f"[MAIN] First entry: {valid_rows[0]['date'][:19]} | {valid_rows[0]['num']} | {valid_rows[0]['cli']} | {valid_rows[0]['sms'][:50]}")

                if valid_rows:
                    latest = valid_rows[0]

                    if is_first_scan:
                        print(f"[MAIN] Sending first notification...")
                        otp = extract_otp(latest['sms'])
                        result = send_telegram(latest['date'], latest['num'], latest['sms'], otp, latest['cli'])
                        print(f"[MAIN] Telegram result: {result}")
                        
                        if result:
                            update_firebase(latest['num'], latest['sms'], latest['date'])

                        sent_msgs[f"{latest['num']}|{latest['sms']}"] = latest['date']
                        is_first_scan = False

                        for item in valid_rows[1:]:
                            sent_msgs[f"{item['num']}|{item['sms']}"] = item['date']

                    else:
                        for item in reversed(valid_rows):
                            uid = f"{item['num']}|{item['sms']}"
                            otp = extract_otp(item['sms'])

                            if uid not in sent_msgs:
                                print(f"[MAIN] New SMS! {item['num']}")
                                if send_telegram(item['date'], item['num'], item['sms'], otp, item['cli']):
                                    update_firebase(item['num'], item['sms'], item['date'])
                                sent_msgs[uid] = item['date']

                if len(sent_msgs) > 2000:
                    print("[MAIN] Clearing sent_msgs cache")
                    sent_msgs.clear()

            except Exception as e:
                print(f"[MAIN] ⚠️ Error in main loop: {e}")

            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(start_bot())
