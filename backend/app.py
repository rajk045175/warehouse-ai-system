
from flask import Flask, request, jsonify, render_template
import sqlite3
import requests
from deep_translator import GoogleTranslator
from langdetect import detect


app = Flask(__name__)

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("incidents.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS incidents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        severity TEXT,
        action TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= TELEGRAM ROUTER =================
def send_telegram_alert(severity, text, action):

    BOT_TOKEN = "8315860700:AAGQ9mdN02YEbMfzQRGHgf0cG0lgtia2cyY"

    SUPERVISOR_ID = "5254530533"
    TECHNICIAN_ID = "1510957180"

    # decide who receives message
    if severity == "HIGH":
        chat_id = SUPERVISOR_ID
        role = "SUPERVISOR 🚨"

    elif severity == "MEDIUM":
        chat_id = TECHNICIAN_ID
        role = "TECHNICIAN 🔧"

    else:
        return   # LOW priority → no message

    message = f"""
🏭 Warehouse Incident Alert

👤 Send To: {role}
📝 Issue: {text}
⚠ Priority: {severity}
📌 Action: {action}
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}

    try:
        requests.post(url, data=data)
        print("Telegram sent to", role)
    except Exception as e:
        print("Telegram Error:", e)
        
def translate_to_english(text):
    try:
        if not text.strip():
            return ""

        translated = GoogleTranslator(
            source='auto',   # auto detect language
            target='en'
        ).translate(text)

        print("Original:", text)
        print("Translated:", translated)

        return translated.lower()

    except Exception as e:
        print("Translation error:", e)
        return text.lower()

# ================= AI ANALYSIS =================
def analyze_text(text):
    text = text.lower()

    HIGH_KEYWORDS = [
        "fire","flame","burn","burning","smoke","gas","explosion","blast",
        "injured","injury","bleeding","unconscious","fainted","accident",
        "short circuit","sparking","shock","electrical shock","died","dead","hurt"
    ]

    MEDIUM_KEYWORDS = [
        "fell","fall","slipped","broken","damage","damaged","crack",
        "leak","leaking","spilling","oil spill","machine stopped",
        "not working","malfunction","overheat","overheating","noise"
    ]

    # check HIGH
    for word in HIGH_KEYWORDS:
        if word in text:
            return "HIGH", "Call emergency & alert supervisor immediately"

    # check MEDIUM
    for word in MEDIUM_KEYWORDS:
        if word in text:
            return "MEDIUM", "Send technician to inspect area"

    return "LOW", "Log and monitor"

# ================= WEB ROUTES =================
@app.route("/")
def home():
    return render_template("index.html")

# receive voice text from website
@app.route("/report", methods=["POST"])
def report():

    data = request.get_json()
    if not data:
        return jsonify({"severity":"LOW","action":"No speech detected"})

    # 1. Get speech text
    text = data.get("text", "")
    print("VOICE INPUT:", text)

    # 2. Translate to English
    text = translate_to_english(text)
    print("AFTER TRANSLATION:", text)

    # 3. Analyze severity
    severity, action = analyze_text(text)
    print("DETECTED:", severity, action)

    # 4. Save in database
    conn = sqlite3.connect("incidents.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO incidents(description,severity,action) VALUES(?,?,?)",
        (text, severity, action)
    )
    conn.commit()
    conn.close()

    # 5. Send telegram alert
    send_telegram_alert(severity, text, action)

    # 6. Always return JSON (VERY IMPORTANT)
    return jsonify({"severity": severity, "action": action})
    


# get all incidents (for graph later)
@app.route("/incidents")
def incidents():
    conn = sqlite3.connect("incidents.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidents ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    return jsonify(rows)



# ================= RUN SERVER =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)