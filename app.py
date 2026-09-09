from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'hope_school_secret_key_2026'

# --- بيانات النظام الأساسية والصلاحيات ---
ROLES = {
    'المدير': 'خضر',
    'السكرتيرة': 'بريتا',
    'المرشد الاجتماعي': 'فؤاد'
}

STAFF_MALES = ['نزار', 'مايك', 'احمد', 'سابا', 'اندريس', 'وليد']
STAFF_FEMALES = ['لانا', 'نقول', 'ايفا', 'لورد', 'نوها', 'منال', 'خيلاء', 'دعاء', 'سلستي', 'نور', 'رزان', 'داليا', 'هايدي', 'نانسي', 'ميري', 'ريتا']

ALL_STAFF = list(ROLES.values()) + STAFF_MALES + STAFF_FEMALES

DAYS = ['السبت', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']

CLASSES = [
    'صف 1', 'صف 2', 'صف 3',
    'صف 4أ', 'صف 4ب',
    'صف 5أ', 'صف 5ب',
    'صف 6أ', 'صف 6ب',
    'صف 7أ', 'صف 7ب',
    'صف 8أ', 'صف 8ب',
    'صف 9',
    'صف 10أ', 'صف 10ب',
    'صف 11', 'صف 12'
]

# قاعدة بيانات مؤقتة في الذاكرة
SCHEDULES = {} # "اليوم-الصف" -> اسم المربي
MESSAGES = []  # قائمة الرسائل

# تخزين كلمات السر (افتراضياً الجميع كلمة سرهم '0000')
PASSWORDS = {user: '0000' for user in ALL_STAFF}

# --- الواجهات البرمجية (HTML داخلي مرتب) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام مراسلة وجداول مدرسة أمل</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 900px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #2c3e50; text-align: center; }
        .btn { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; border: none; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #219653; }
        table { width: 100%%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: center; }
        th { background-color: #2c3e50; color: white; }
        select, input, textarea { width: 100%%; padding: 8px; margin: 5px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-family: Tahoma; }
        select[multiple] { height: 130px; background: #f8fafc; }
        .card { background: #ecf0f1; padding: 15px; border-radius: 6px; margin-bottom: 15px; }
        .error { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center; }
        .success-msg { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏫 نظام مراسلة وجداول مدرسة أمل</h1>
        
        {% if session.get('user') %}
            <div style="display: flex; justify-content: space-between; align-items: center; background: #e2e8f0; padding: 10px 15px; border-radius: 5px; margin-bottom: 20px;">
                <span>مرحباً بك، <strong>{{ session.get('user') }}</strong></span>
                <a href="/logout" class="btn btn-danger" style="padding: 5px 10px; margin: 0;">تسجيل خروج</a>
            </div>

            {% if error %}
                <div class="error">{{ error }}</div>
            {% endif %}
            {% if success %}
                <div class="success-msg">{{ success }}</div>
            {% endif %}

            <!-- قسم تغيير كلمة السر لأي مستخدم -->
            <div class="card" style="background: #eef2f3;">
                <h4>🔐 تغيير كلمة السر الخاصة بك (الافتراضية: 0000)</h4>
                <form method="POST" action="/change_password" style="display: flex; gap: 10px; align-items: flex-end;">
                    <div style="flex: 1; margin: 0;">
                        <label>كلمة السر الجديدة:</label>
                        <input type="password" name="new_password" required placeholder="أدخل كلمة السر الجديدة">
                    </div>
                    <button type="submit" class="btn btn-success" style="height: 38px; margin: 0;">تحديث كلمة السر</button>
                </form>
            </div>

            <!-- لوحة المدير: خضر (مع ميزة الاختيار المتعدد للرسائل) -->
            {% if session.get('user') == 'خضر' %}
                <div class="card" style="border-right: 5px solid #27ae60;">
                    <h3>👑 لوحة تحكم المدير (خضر) - مراقبة شاملة</h3>
                    <p>يمكنك الاطلاع على كافة الجداول وتحركات المراسلات، وإرسال رسائل فردية أو جماعية لأكثر من معلم دفعة واحدة.</p>
                    
                    <form method="POST" action="/send_message">
                        <label>إرسال رسالة إلى (اضغط مطولاً أو استمر بالضغط لاختيار أكثر من معلم أو الكل):</label>
                        <select name="receivers" multiple required>
                            <option value="الكل">--- إرسال إلى الجميع (الكل) ---</option>
                            {% for staff in all_staff %}
                                {% if staff != 'خضر' %}
                                    <option value="{{ staff }}">{{ staff }}</option>
                                {% endif %}
                            {% endfor %}
                        </select>
                        <label>نص الرسالة:</label>
                        <textarea name="msg_text" rows="3" required placeholder="اكتب رسالتك هنا..."></textarea>
                        <button type="submit" class="btn">إرسال الرسالة للمعلمين المختارين</button>
                    </form>

                    <h4 style="margin-top: 20px;">📨 سجل المراسلات العامة والواردة:</h4>
                    <table>
                        <tr><th>المرسل</th><th>المستقبل</th><th>النص</th></tr>
                        {% for m in messages %}
                        <tr>
                            <td>{{ m.sender }}</td>
                            <td>{{ m.receiver }}</td>
                            <td>{{ m.text }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
            {% endif %}

            <!-- لوحة السكرتيرة: بريتا -->
            {% if session.get('user') == 'بريتا' %}
                <div class="card" style="border-right: 5px solid #2980b9;">
                    <h3>📋 لوحة السكرتيرة (بريتا) - إدارة الجداول</h3>
                    <p>تحديد أماكن وجود المربين والمربيات في الصفوف والشعب حسب أيام الأسبوع.</p>
                    
                    <form method="POST" action="/update_schedule">
                        <label>اختر اليوم:</label>
                        <select name="day">
                            {% for d in days %}
                                <option value="{{ d }}">{{ d }}</option>
                            {% endfor %}
                        </select>

                        <label>اختر الصف / الشعبة:</label>
                        <select name="class_name">
                            {% for c in classes %}
                                <option value="{{ c }}">{{ c }}</option>
                            {% endfor %}
                        </select>

                        <label>اختر المربي / المربية:</label>
                        <select name="teacher">
                            {% for t in staff_males + staff_females %}
                                <option value="{{ t }}">{{ t }}</option>
                            {% endfor %}
                        </select>

                        <button type="submit" class="btn">حفظ وتحديث الجدول</button>
                    </form>
                </div>
            {% endif %}

            <!-- عرض الجداول العامة للجميع -->
            <h2>📅 جدول الحصص وتواجد المربين بالأيام والشعب</h2>
            <table>
                <tr>
                    <th>اليوم</th>
                    <th>الصف / الشعبة</th>
                    <th>المربي / المربية المسؤول</th>
                </tr>
                {% for key, teacher in schedules.items() %}
                    {% set parts = key.split('-') %}
                    <tr>
                        <td>{{ parts[0] }}</td>
                        <td>{{ parts[1] }}</td>
                        <td><strong>{{ teacher }}</strong></td>
                    </tr>
                {% else %}
                    <tr><td colspan="3">لم تقم السكرتيرة بإدخال أي جداول بعد.</td></tr>
                {%- endfor %}
            </table>

            <!-- قسم الرسائل الخاصة للمعلمين والآخرين -->
            {% if session.get('user') != 'خضر' %}
                <div class="card" style="margin-top: 20px;">
                    <h3>📥 صندوق الوارد (رسائلي)</h3>
                    <table>
                        <tr><th>من المرُسل</th><th>الرسالة</th></tr>
                        {% for m in messages %}
                            {% if m.receiver == 'الكل' or session.get('user') in m.receiver.split(', ') %}
                            <tr>
                                <td>{{ m.sender }}</td>
                                <td>{{ m.text }}</td>
                            </tr>
                            {% endif %}
                        {% endfor %}
                    </table>
                </div>
            {% endif %}

        {% else %}
            <!-- صفحة تسجيل الدخول -->
            <div class="card" style="max-width: 400px; margin: 40px auto; text-align: center;">
                <h2>تسجيل الدخول للنظام</h2>
                {% if error %}
                    <div class="error">{{ error }}</div>
                {% endif %}
                <form method="POST" action="/login">
                    <label>اختر اسمك أو صلاحيتك:</label>
                    <select name="username">
                        <optgroup label="الإدارة والإرشاد">
                            <option value="خضر">المدير: خضر</option>
                            <option value="بريتا">السكرتيرة: بريتا</option>
                            <option value="فؤاد">المرشد الاجتماعي: فؤاد</option>
                        </optgroup>
                        <optgroup label="المربون">
                            {% for t in staff_males %}
                                <option value="{{ t }}">{{ t }}</option>
                            {% endfor %}
                        </optgroup>
                        <optgroup label="المربيات">
                            {% for t in staff_females %}
                                <option value="{{ t }}">{{ t }}</option>
                            {% endfor %}
                        </optgroup>
                    </select>

                    <label>كلمة السر (الافتراضية: 0000):</label>
                    <input type="password" name="password" required placeholder="أدخل كلمة السر">

                    <button type="submit" class="btn" style="width: 100%%;">دخول للنظام</button>
                </form>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                  days=DAYS, 
                                  classes=CLASSES, 
                                  staff_males=STAFF_MALES, 
                                  staff_females=STAFF_FEMALES,
                                  all_staff=ALL_STAFF,
                                  schedules=SCHEDULES,
                                  messages=MESSAGES,
                                  error=request.args.get('error'),
                                  success=request.args.get('success'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username in ALL_STAFF and PASSWORDS.get(username) == password:
        session['user'] = username
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index', error='كلمة السر غير صحيحة! كلمة السر الافتراضية للجميع هي 0000'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if session.get('user'):
        new_pass = request.form.get('new_password')
        if new_pass:
            PASSWORDS[session['user']] = new_pass
            return redirect(url_for('index', success='تم تحديث كلمة السر بنجاح!'))
    return redirect(url_for('index', error='حدث خطأ أثناء تغيير كلمة السر'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/update_schedule', methods=['POST'])
def update_schedule():
    if session.get('user') == 'بريتا':
        day = request.form.get('day')
        class_name = request.form.get('class_name')
        teacher = request.form.get('teacher')
        key = f"{day}-{class_name}"
        SCHEDULES[key] = teacher
    return redirect(url_for('index'))

@app.route('/send_message', methods=['POST'])
def send_message():
    if session.get('user') == 'خضر':
        receivers_list = request.form.getlist('receivers')
        text = request.form.get('msg_text')
        receiver_str = ", ".join(receivers_list)
        MESSAGES.insert(0, {'sender': 'المدير (خضر)', 'receiver': receiver_str, 'text': text})
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
