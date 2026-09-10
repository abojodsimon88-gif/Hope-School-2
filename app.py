from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'hope_school_secret_key_2026'

# جعل الجلسة تنتهي بمجرد إغلاق المتصفح لضمان طلب كلمة السر دائماً
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# --- بيانات النظام الأساسية والصلاحيات ---
ROLES = {
    'المدير': 'خضر',
    'السكرتيرة': 'بريتا',
    'المرشد الاجتماعي': 'فؤاد'
}

STAFF_MALES = ['نزار', 'مايك', 'احمد', 'سابا', 'اندريس', 'وليد']
# أضفنا المعلمة "ليلى" ضمن قائمة المعلمات المربيات
STAFF_FEMALES = ['ليلى', 'لانا', 'نقول', 'ايفا', 'لورد', 'نوها', 'منال', 'خيلاء', 'دعاء', 'سلستي', 'نور', 'رزان', 'داليا', 'هايدي', 'نانسي', 'ميري', 'ريتا']

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

# المواد الدراسية
SUBJECTS = [
    'إنجليزي', 'جغرافيا', 'تاريخ', 'رياضيات', 'رياضة', 
    'تكنولوجيا', 'عربي', 'علوم', 'تربية مسيحية', 'تربية إسلامية'
]

# قاعدة بيانات مؤقتة في الذاكرة
SCHEDULES = {} # مفتاحها "اليوم-الصف" -> يخزن (المربي والمادة)
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
        .container { max-width: 950px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #2c3e50; text-align: center; }
        .btn { display: inline-block; background: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; margin: 3px; border: none; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #219653; }
        .btn-warning { background: #f39c12; color: white; }
        .btn-warning:hover { background: #d68910; }
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

            <!-- قسم تغيير كلمة السر -->
            <div class="card" style="background: #eef2f3;">
                <h4>🔐 تغيير كلمة السر الخاصة بك (الافتراضية: 0000)</h4>
                <form method="POST" action="/change_password" style="display: flex; gap: 10px; align-items: flex-end;">
                    <div style="flex: 1; margin: 0;">
                        <label>كلمة السر الجديدة:</label>
                        <input type="password" name="new_password" required placeholder="أدخل كلمة السر الجديدة">
                    </div>
                    <button type="submit" class="btn btn-success" style="height: 38px; margin-bottom: 15px;">تحديث</button>
                </form>
            </div>

            <!-- لوحة التحكم للمدير (إدارة الجداول) -->
            {% if session.get('user') == 'خضر' %}
                <div class="card" style="background: #e8f8f5; border-right: 5px solid #27ae60;">
                    <h3>🛠️ لوحة تحكم المدير (توزيع الحصص والجداول)</h3>
                    <form method="POST" action="/save_schedule">
                        <label>اختر اليوم:</label>
                        <select name="day" required>
                            {% for d in days %}
                                <option value="{{ d }}">{{ d }}</option>
                            {% endfor %}
                        </select>

                        <label>اختر الصف:</label>
                        <select name="class_name" required>
                            {% for c in classes %}
                                <option value="{{ c }}">{{ c }}</option>
                            {% endfor %}
                        </select>

                        <label>اختر المعلم المربي:</label>
                        <select name="teacher" required>
                            {% for t in all_staff %}
                                <option value="{{ t }}">{{ t }}</option>
                            {% endfor %}
                        </select>

                        <label>المادة الدراسية:</label>
                        <select name="subject" required>
                            {% for s in subjects %}
                                <option value="{{ s }}">{{ s }}</option>
                            {% endfor %}
                        </select>

                        <button type="submit" class="btn btn-success">حفظ وتحديث الجدول</button>
                    </form>
                </div>
            {% endif %}

            <!-- قسم إرسال الرسائل -->
            <div class="card">
                <h3>💬 لوحة المراسلة الجماعية والفردية</h3>
                <form method="POST" action="/send_message">
                    <label>اختر المرسل إليهم (حدد عدة أسماء بالضغط مع الاستمرار):</label>
                    <select name="recipients" multiple required>
                        <option value="ALL_STAFF">📢 جميع الهيئة التدريسية والإدارية</option>
                        {% for t in all_staff %}
                            {% if t != session.get('user') %}
                                <option value="{{ t }}">{{ t }}</option>
                            {% endif %}
                        {% endfor %}
                    </select>

                    <label>نص الرسالة أو التنبيه:</label>
                    <textarea name="message_text" rows="3" required placeholder="اكتب رسالتك أو التنبيه هنا..."></textarea>

                    <button type="submit" class="btn">إرسال الرسالة</button>
                </form>
            </div>

            <!-- صندوق الوارد (الرسائل الواردة للمستخدم) -->
            <h2>📥 صندوق الوارد الخاص بك</h2>
            <table>
                <tr>
                    <th>من المرسل</th>
                    <th>محتوى الرسالة</th>
                    <th>الوقت</th>
                </tr>
                {% for msg in messages %}
                    {% if msg.to == session.get('user') or msg.to == 'ALL_STAFF' %}
                        <tr>
                            <td><strong>{{ msg.from }}</strong></td>
                            <td>{{ msg.text }}</td>
                            <td>{{ msg.time }}</td>
                        </tr>
                    {% endif %}
                {% endfor %}
            </table>

            <!-- جدول الحصص العام -->
            <h2 style="margin-top: 30px;">📅 جدول الحصص المدرسي</h2>
            <table>
                <tr>
                    <th>اليوم / الصف</th>
                    {% for c in classes %}
                        <th>{{ c }}</th>
                    {% endfor %}
                </tr>
                {% for d in days %}
                    <tr>
                        <td><strong>{{ d }}</strong></td>
                        {% for c in classes %}
                            <td>
                                {% set key = d ~ '-' ~ c %}
                                {% if key in schedules %}
                                    <span style="color: #2980b9; font-weight: bold;">{{ schedules[key].teacher }}</span><br>
                                    <span style="font-size: 12px; color: #555;">({{ schedules[key].subject }})</span>
                                {% else %}
                                    <span style="color: #999;">-</span>
                                {% endif %}
                            </td>
                        {% endfor %}
                    </tr>
                {% endfor %}
            </table>

        {% else %}
            <!-- صفحة تسجيل الدخول -->
            <div class="card" style="max-width: 350px; margin: 40px auto; text-align: center;">
                <h2>تسجيل الدخول</h2>
                {% if error %}
                    <div class="error">{{ error }}</div>
                {% endif %}
                <form method="POST" action="/login">
                    <label>اختر اسمك (المستخدم):</label>
                    <select name="username" required>
                        <option value="">--- اختر اسم المستخدم ---</option>
                        {% for u in all_staff %}
                            <option value="{{ u }}">{{ u }}</option>
                        {% endfor %}
                    </select>

                    <label>كلمة السر (الافتراضية: 0000):</label>
                    <input type="password" name="password" required placeholder="أدخل كلمة السر">

                    <button type="submit" class="btn" style="width: 100%;">دخول للنظام</button>
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
                                  all_staff=ALL_STAFF, 
                                  days=DAYS, 
                                  classes=CLASSES, 
                                  subjects=SUBJECTS,
                                  schedules=SCHEDULES,
                                  messages=MESSAGES,
                                  error=request.args.get('error'),
                                  success=request.args.get('success'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username in PASSWORDS and PASSWORDS[username] == password:
        session.permanent = True
        session['user'] = username
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index', error='خطأ في اسم المستخدم أو كلمة السر!'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if session.get('user'):
        new_pass = request.form.get('new_password')
        current_user = session.get('user')
        if new_pass:
            PASSWORDS[current_user] = new_pass
            return redirect(url_for('index', success='تم تحديث كلمة السر بنجاح!'))
    return redirect(url_for('index', error='حدث خطأ أثناء تحديث كلمة السر'))

@app.route('/save_schedule', methods=['POST'])
def save_schedule():
    if session.get('user') == 'خضر':
        day = request.form.get('day')
        class_name = request.form.get('class_name')
        teacher = request.form.get('teacher')
        subject = request.form.get('subject')
        
        key = f"{day}-{class_name}"
        SCHEDULES[key] = {
            'teacher': teacher,
            'subject': subject
        }
        return redirect(url_for('index', success='تم تحديث جدول الحصص بنجاح!'))
    return redirect(url_for('index', error='غير مسموح لك بهذا الإجراء!'))

@app.route('/send_message', methods=['POST'])
def send_message():
    if session.get('user'):
        sender = session.get('user')
        recipients = request.form.getlist('recipients')
        message_text = request.form.get('message_text')
        
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        for rec in recipients:
            MESSAGES.insert(0, {
                'from': sender,
                'to': rec,
                'text': message_text,
                'time': current_time
            })
        return redirect(url_for('index', success='تم إرسال الرسالة بنجاح!'))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
