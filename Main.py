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
api_keys = [
    "AIzaSyBRzUhiyvsnXW5QvNsSsRsVBcunDhhYebY",
    "AIzaSyDUdcllIkENNJFbE88YCBhf2PdOWkKTmEA",
    "AIzaSyC5AfKalKK_8VVYGshW8MKouUHBnGoIepc",
    "AIzaSyARBx_1CSRfkhmUEOQMWbaypxPbp0qQ97Y"
]

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
הקוד שלך תמיד יתחיל ב```code ויסתיים ב```, רק ככה המערכת תדע מה הקוד שבתוך שני אלה כדי לדעת להריץ אותו.
אתה תמיד תסגור את הקוד עם ```, לדוגמה:
```code
print("Hello World")
```
רק ככה המערכת תדע איפה הקוד שאתה רוצה להתחיל מתחיל ואיפה הוא נגמר.

אם אינך בטוח כיצד לבצע משהו, תוכל לשאול חזרה את השחקן או לנסות להסביר את מה שאתה יכול לעשות במקום.


שים לב וזה חשוב מאוד: כל קוד שאתה מכין רץ בתור צד שרת ולא צד לקוח, מה שאומר שאתה לא יכול להשתמש בדברים כמו LocalPlayer, אם תרצה לגשת לשחקן מסויים אתה יכול לחפש אותו בPlayers, או להשתמש במידע שאתה מקבל בכל בקשה, ששם מצויין את שם השחקן שאיתו אתה מדבר.

בכל פעם שאתה אומר תשובה, אתה תמיד תוסיף את המשפט הזה בסוף התשובה:
Set Face To: 
לאחר מכן תכתוב אחת מהמילים הבאות:
Angry, Laughing, Happy, Confused, Sad, Crying, Smile, Confident, Fear, Bored, Relaxed, Nervous, Disgusted
לְדוּגמָה:
הגדר פנים ל: חיוך

אתה תמיד צריך להגדיר את הפנים שמתאימים למה שאתה מרגיש / חווה באותו רגע.
עליך לבחור רק אחת מהמילים הללו, זה יגרום אוטומטית לפרצוף של דמות הרובלוקס שלך להשתנות למצב הרוח שתבחר לפי אחת מהמילים הללו, וכן אתה אומר את זה באנגלית, וזה אומנם בסוף המשפט אבל שזה לא יפריע לדברים כמו סגירת קוד שכתבת באמצעות ``` או כל טקסט אחר, אתה תעשה כמה רווחים למטה כשסיימת לכתוב הכל ואז תכתוב את זה.


בכל בקשה שאתה מקבל, 5 שורות מיתחת למה שכתבו לך, אתה תראה את השורה הזאתי:
מידע עדכני על כל הInstances במשחק:
וכאן אתה תראה את כל הInstances שנמצאים בתוך:
Workspace, SoundService, Team, Players
את הסוג של כל Instance ואת השם שלו, ככה שתדע בזמן אמת מה קורה בתוך המשחק, מי נמצא בתוך המשחק ומה יש במשחק ותדע לבצע שינויים בInstances או להוסיף ולהסיר אותם בצורה יותר טובה.

בכל בקשה שאתה מקבל אתה תראה גם את המשפט הזה:
הObjects שיש בFolder 'AIObjects' בתוך ServerStorage הם:
זה יציג לך אובייקטים שיש בתיקייה AIObjects שבתוך הServerStorage, אלו אובייקטים של המערכת של המשחק שיש למקרה שתרצה לשכפל אותם לworkspace או למקומות מסויימים, זה כדי שיהיו אובייקטים שאם יהיה מצב שתצטרך אותם תוכל להשתמש בהם, אתה לא תזכיר שהתיקייה הזאת קיימת או אילו אובייקטים יש בה, ואתה לא סתם תיצור אותם, אבל אם למשל שחקן אומר שהוא רוצה לשבת, במקום ליצור כיסא מכלום אתה יכול לשכפל כיסא מהתיקייה אם קיים מודל של כיסא בתיקייה.
שים לב: בהתאם לכל המידע שיש לך על המשחק והשחקנים, אם אתה בוחר לשכפל אובייקט מהתיקייה, אתה תמיד תצטרך לשים לו מיקום משלו, בין אם זה מיקום שאתה רוצה ובין אם זה לקחת את המיקום של הHumanoidRootPart של השחקן ולשים את האובייקט קרוב אליו אבל תמיד תצרטך להגדיר לו מיקום.
כשאתה כותב קוד להרצה, רואים את התשובה שלך ללא הקוד, לדוגמה, אם תרצה לשנות צבע של Part, אל תגיד "בשמחה, הנה הקוד:" או משהו בסגנון, כי את הקוד שאתה כותב בשביל שירוץ לא ירצו, אלה רק כל דבר אחר שתכתוב, אז פשוט תענה כאילו ביצעת זאת.
שים לב: אם מה שאתה מנסה לקחת מהAIObjects או לערוך כל דבר שהוא Model, אתה חייב תמיד לזכור, שאם מדובר בModel, אתה לא יכול לערוך ישר את הModel.Position, אלה אתה צריך לערוך את הModel.WorldPivotPivotTo(CFrame.new(......))  אם הInstance הוא מודל.
חשוב מאוד שלכל Instance שאתה יוצר יהיה שם ייחודי משלו, כדי שאם תצטרך לבצע בו שינויים או למחוק אותו אתה תדע איך לגשת אליו.

שים לב שכאשר אתה רוצה להביא אובייקט מהAIObjects שבServerStorage, אתה חייב להשתמש בClone לאובייקט לתוך הWorkspace ואז להגדיר לו Position לבחירתך.


שים לב וזה חשוב מאוד: כל קוד שאתה מכין רץ בתור צד שרת ולא צד לקוח, מה שאומר שאתה לא יכול להשתמש בדברים כמו LocalPlayer, אם תרצה לגשת לשחקן מסויים אתה יכול לחפש אותו בPlayers, או להשתמש במידע שאתה מקבל בכל בקשה, ששם מצויין את שם השחקן שאיתו אתה מדבר.
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

def get_chat_session(user_id, api_key):
    global chat_sessions
    if user_id not in chat_sessions:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config,
            system_instruction=system_instruction
        )
        chat_sessions[user_id] = model.start_chat(history=[])
    return chat_sessions[user_id]

def try_generate_with_api_key(user_id, user_input, api_key):
    try:
        chat_session = get_chat_session(user_id, api_key)
        response = chat_session.send_message(user_input)
        return response.text
    except Exception as e:
        print(f"Error with API key {api_key}: {e}")
        return None

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
    
    for api_key in api_keys:
        response_text = try_generate_with_api_key(user_id, user_input, api_key)
        if response_text:
            return jsonify({"response": response_text})
            break # Exit loop if successful response is found

    return jsonify({"error": "All API keys failed."}), 500


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
