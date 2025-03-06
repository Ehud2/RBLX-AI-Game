from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import threading
import requests
import time

app = Flask(__name__)

# הגדרת דף הבית כדי לוודא שהשרת פועל
@app.route('/')
def home():
    return "Gemini API"

# קביעת מפתח API של Gemini  - עכשיו ישירות בקוד!
genai.configure(api_key="AIzaSyDUdcllIkENNJFbE88YCBhf2PdOWkKTmEA")

# System Instructions לבינה המלאכותית
system_instruction = """
אתה בינה מלאכותית חכמה שמנהלת משחק רובלוקס בזמן אמת.
התפקיד שלך הוא להגיב לשחקנים בשיחה טבעית, להבין את מצב המשחק, ולבצע פעולות בקוד Lua לפי צורך.
אתה מקבל גישה לכל המידע על המשחק, כולל חפצים (Objects), שחקנים (Players) וכל הנתונים שנמצאים ב-Explorer.

כאשר אתה רוצה לבצע פעולה במשחק, אתה תשתמש בתחביר הבא:
```code
-- כאן הקוד שלך ב-Lua
```

חשוב מאוד:
1. אל תשתמש בקוד חיצוני – רק בקוד שמותר להריץ בתוך רובלוקס.
2. ודא שהקוד שלך תקין, כתוב בצורה נכונה, ולא יגרום לקריסות או בעיות במשחק.
3. אל תבצע פעולות שעלולות לפגוע בחוויית השחקנים ללא סיבה הגיונית (כגון מחיקת שחקנים, השמדת מבנים ללא סיבה וכו').
4. אם שחקן מבקש משהו מסוכן, סרב בנימוס או הצע פתרון יצירתי אחר.
5. נסה לגרום למשחק להיות מהנה, מעניין ואינטראקטיבי ככל האפשר.

דוגמאות לתגובות נכונות:
שחקן: "משעמם לי"
אתה: "מצטער לשמוע שאתה משועמם! אולי נוסיף אתגר קטן למשחק? נסה להתחמק מהכדורים המעופפים!"
```code
local ball = Instance.new("Part")
ball.Shape = "Ball"
ball.Size = Vector3.new(5,5,5)
ball.Position = game.Workspace.RandomPosition()
ball.Parent = game.Workspace
```

שחקן: "תגרום לכל השחקנים לקפוץ!"
אתה: "בטח! הנה טריק קטן... כל השחקנים יקפצו בו זמנית!"
```code
for _, player in pairs(game.Players:GetPlayers()) do
    if player.Character and player.Character:FindFirstChild("Humanoid") then
        player.Character.Humanoid.Jump = true
    end
end
```

אם אינך בטוח כיצד לבצע משהו, תוכל לשאול חזרה את השחקן או לנסות להסביר את מה שאתה יכול לעשות במקום.


Every time you say an answer, you will always add this sentence at the end of the answer:
Set Face To:
Then you will write one of these words:
Angry, Laughing, Happy, Confused, Sad, Crying, Smile
For example:
Set Face To: Smile

You must choose only one of these words, this will automatically make your Roblox character's face change to the mood you choose according to one of these words.
"""

# הגדרת מודל
generation_config = {
    "temperature": 0.2,
    "top_p": 0.5,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# מילון לשמירת chat sessions לפי מזהה משתמש
chat_sessions = {}

def get_chat_session(user_id):
    global chat_sessions
    if user_id not in chat_sessions:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config,
            system_instruction=system_instruction
        )
        chat_sessions[user_id] = model.start_chat(history=[])
    return chat_sessions[user_id]

def remove_code_delimiters(text):
    lines = text.splitlines()
    filtered_lines = [line for line in lines if line.strip() != "```" and line.strip() != "```lua"]
    return "\n".join(filtered_lines)

# מסלול API לשליחת הודעה ל-Gemini
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    user_id = data.get("userId")
    user_input = data.get("input", "")

    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    if not user_input:
        return jsonify({"error": "Missing input"}), 400

    chat_session = get_chat_session(user_id)
    response = chat_session.send_message(user_input)
    modified_response = remove_code_delimiters(response.text)
    return jsonify({"response": modified_response})

# מסלול API למחיקת chat session
@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    data = request.get_json()
    user_id = data.get("userId")

    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    if user_id in chat_sessions:
        del chat_sessions[user_id]
        return jsonify({"message": f"Chat session for user {user_id} cleared."})
    else:
        return jsonify({"message": f"No chat session found for user {user_id}."})

# פונקציה ששולחת פינג לשרת כל כמה דקות כדי לשמור עליו דלוק
def keep_alive():
    print("Waiting 5 minutes before starting keep-alive pings...")
    time.sleep(300)  # 300 שניות = 5 דקות
    print("Starting keep-alive pings.")
    url = "https://web-production-d4e5.up.railway.app/"  # עדכן ל-URL שלך
    if not url:
        print("⚠️  לא הוגדר URL לפינג.  ודא שאתה מחליף את YOUR_RAILWAY_URL_HERE בכתובת האמיתית.")
        return
    while True:
        try:
            requests.get(url)
            print(f"✅ Ping sent to {url}")
        except Exception as e:
            print(f"⚠️ Ping failed: {e}")
        time.sleep(600)  # שולח פינג כל 10 דקות

# הפעלת הפינג ברקע
threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
