from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'hope_school_secret_key_2026'

# --- إعداد قاعدة البيانات الدائمة (SQLite) لمدرسة الأمل 2 ---
def init_db():
    conn = sqlite3.connect('hope_school.db')
    cursor = conn.cursor()
    
    # جدول المستخدمين (المدير خضر، السكرتيرة بريتا، والمعلمين)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL
        )
    ''')
    
    # جدول الرسائل والتعاميم
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    
    # إضافة الحسابات الافتراضية إذا مش موجودة
    cursor.execute("SELECT * FROM users WHERE username = 'khader'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, name) VALUES ('khader', '000', 'admin', 'المدير خضر')")
        cursor.execute("INSERT INTO users (username, password, role, name) VALUES ('breeta', '000', 'secretary', 'السكرتيرة بريتا')")
        cursor.execute("INSERT INTO users (username, password, role, name) VALUES ('teacher1', '000', 'teacher', 'المعلم أحمد')")
        cursor.execute("INSERT INTO users (username, password, role, name) VALUES ('teacher2', '000', 'teacher', 'المعلم محمود')")
    
    conn.commit()
    conn.close()

init_db()

# --- الواجهة البرمجية المحدثة (HTML) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مدرسة الأمل 2 - النظام الإداري</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #f0f4f8; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 950px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h1, h2, h3 { color: #1e3a8a; text-align: center; }
        .btn { display: inline-block; background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; margin: 5px 0; border: none; cursor: pointer; font-size: 15px; }
        .btn:hover { background: #1d4ed8; }
        .btn-danger { background: #dc2626; }
        .btn-danger:hover { background: #b91c1c; }
        table { width: 100%%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #cbd5e1; padding: 10px; text-align: center; }
        th { background-color: #1e3a8a; color: white; }
        select, input, textarea { width: 100%%; padding: 10px; margin: 6px 0 15px 0; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; font-family: Tahoma; }
        select[multiple] { height: 130px; background: #f8fafc; }
        .card { background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
        .error { background: #fee2e2; color: #991b1b; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center; }
        .success-msg { background: #dcfce7; color: #166534; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center; }
        .user-bar { display: flex; justify-content: space-between; align-items: center; background: #e2e8f0; padding: 12px 20px; border-radius: 8px; margin-bottom: 25px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏫 نظام مدرسة الأمل 2</h1>
        
        {% if session.get('user') %}
            <div class="user-bar">
                <span>المستخدم الحالي: {{ session.get('name') }} ({{ session.get('role') }})</span>
                <a href="/logout" class="btn btn-danger" style="padding: 5px 15px; margin: 0;">تسجيل خروج</a>
            </div>

            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            {% if success %}<div class="success-msg">{{ success }}</div>{% endif %}

            <!-- قسم إرسال الرسائل (خاص بالمدير والسكرتيرة) -->
            {% if session.get('role') in ['admin', 'secretary'] %}
                <div class="card">
                    <h3>📤 إرسال رسالة / تعميم لمعلم أو أكثر</h3>
                    <form method="POST" action="/send_message">
                        <label>اختر المعلمين (اضغط على Ctrl أو ارفع إصبعك لاختيار أكثر من معلم):</label>
                        <select name="receivers" multiple required>
                            {% for t in teachers %}
                                <option value="{{ t[0] }}">{{ t[3] }} ({{ t[0] }})</option>
                            {% endfor %}
                        </select>
                        
                        <label>نص الرسالة:</label>
                        <textarea name="content" rows="4" required placeholder="اكتب الرسالة هنا..."></textarea>
                        
                        <button type="submit" class="btn">إرسال لجميع المعلمين المختارين</button>
                    </form>
                </div>
            {% endif %}

            <!-- صندوق الوارد -->
            <h2>📥 رسائلي الواردة</h2>
            <table>
                <tr><th>المرسل</th><th>نص الرسالة</th><th>التاريخ</th></tr>
                {% for msg in messages %}
                <tr>
                    <td>{{ msg[1] }}</td>
                    <td style="text-align: right; padding-right: 15px;">{{ msg[3] }}</td>
                    <td>{{ msg[4] }}</td>
                </tr>
                {% else %}
                <tr><td colspan="3">لا توجد رسائل واردة.</td></tr>
                {% endfor %}
            </table>

        {% else %}
            <!-- نافذة تسجيل الدخول -->
            <div class="card" style="max-width: 400px; margin: 40px auto; text-align: center;">
                <h2>تسجيل الدخول للمدرسة</h2>
                {% if error %}<div class="error">{{ error }}</div>{% endif %}
                <form method="POST" action="/login">
                    <label>اسم المستخدم:</label>
                    <input type="text" name="username" required placeholder="مثال: khader">
                    <label>كلمة السر:</label>
                    <input type="password" name="password" required placeholder="000">
                    <button type="submit" class="btn" style="width: 100%%;">دخول</button>
                </form>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect('hope_school.db')
    cursor = conn.cursor()
    
    messages = []
    teachers = []
    
    if session.get('user'):
        # جلب رسائل المستخدم الحالي
        cursor.execute("SELECT * FROM messages WHERE receiver = ? ORDER BY id DESC", (session.get('user'),))
        messages = cursor.fetchall()
        
        # جلب قائمة المعلمين للاختيار من بينهم
        cursor.execute("SELECT * FROM users WHERE role = 'teacher'")
        teachers = cursor.fetchall()
        
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, 
                                  messages=messages, 
                                  teachers=teachers,
                                  error=request.args.get('error'),
                                  success=request.args.get('success'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = sqlite3.connect('hope_school.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user'] = user[0]
        session['role'] = user[2]
        session['name'] = user[3]
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index', error='اسم المستخدم أو كلمة السر خاطئة!'))

@app.route('/send_message', methods=['POST'])
def send_message():
    if session.get('role') in ['admin', 'secretary']:
        receivers = request.form.getlist('receivers') # استلام عدة معلمين بنفس الوقت
        content = request.form.get('content')
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        conn = sqlite3.connect('hope_school.db')
        cursor = conn.cursor()
        
        for receiver in receivers:
            cursor.execute("INSERT INTO messages (sender, receiver, content, date) VALUES (?, ?, ?, ?)",
                           (session.get('name'), receiver, content, date_str))
        
        conn.commit()
        conn.close()
        return redirect(url_for('index', success='تم إرسال الرسالة لجميع المعلمين المختارين بنجاح!'))
    return redirect(url_for('index', error='غير مصرح لك بالإرسال'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
