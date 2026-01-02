from fastapi import FastAPI, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# قاعدة البيانات
engine = create_engine("sqlite:///./db.sqlite", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# جدول المستخدمين
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="user")  # user أو admin

# جدول البلاغات
class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    status = Column(String, default="pending")

Base.metadata.create_all(engine)

# جلسة قاعدة البيانات
def db():
    s = Session()
    try:
        yield s
    finally:
        s.close()

# تحديد اللغة
def get_language(request: Request):
    lang = request.cookies.get("lang")
    return lang if lang in ["ar", "he"] else "ar"

# CSS عالمي لكل الصفحات (تحسين UX للموبايل)
css_style = """
<style>
body {
    font-family: Arial, sans-serif;
    background: #f7f7f7;
    padding: 15px;
    margin: 0;
    text-align: center;
}
h1, h2 { color: #2c3e50; margin-bottom: 20px; }
input, textarea, button, a.button {
    width: 90%;
    max-width: 320px;
    padding: 12px;
    margin: 8px auto;
    border-radius: 10px;
    border: 1px solid #bdc3c7;
    font-size: 1em;
    box-sizing: border-box;
}
button, a.button {
    background-color: #3498db;
    color: white;
    text-decoration: none;
    display: inline-block;
    border: none;
}
button:hover, a.button:hover {
    background-color: #2980b9;
    cursor: pointer;
}
textarea { height: 100px; }
.report {
    background: white;
    padding: 12px;
    margin: 12px auto;
    border-radius: 10px;
    max-width: 360px;
    word-wrap: break-word;
}
a.approve { background: #27ae60; }
a.reject { background: #c0392b; }
a.approve:hover { background: #2ecc71; }
a.reject:hover { background: #e74c3c; }
@media (max-width: 400px) {
    h1, h2 { font-size: 1.5em; }
    input, textarea, button, a.button { width: 95%; }
}
</style>
"""

# الصفحة الرئيسية
@app.get("/", response_class=HTMLResponse)
def home(request: Request, d=Depends(db)):
    lang = get_language(request)
    if lang == "he":
        return f"""
        <html lang="he" dir="rtl">
        <head>{css_style}</head>
        <body>
        <h1>HamalNews | חדשות</h1>
        <a class='button' href='/register'>הרשמה</a>
        <a class='button' href='/add'>שלח דיווח</a>
        <a class='button' href='/set_language/ar'>AR</a>
        </body></html>
        """
    return f"""
    <html lang="ar" dir="rtl">
    <head>{css_style}</head>
    <body>
    <h1>HamalNews | حمّال نيوز</h1>
    <a class='button' href='/register'>تسجيل</a>
    <a class='button' href='/add'>إضافة بلاغ</a>
    <a class='button' href='/set_language/he'>HE</a>
    </body></html>
    """

# تغيير اللغة
@app.get("/set_language/{lang}", response_class=HTMLResponse)
def set_language(lang: str):
    response = RedirectResponse("/")
    response.set_cookie(key="lang", value=lang)
    return response

# صفحة التسجيل
@app.get("/register", response_class=HTMLResponse)
def reg(request: Request):
    lang = get_language(request)
    if lang == "he":
        return f"""
        <html lang="he" dir="rtl">
        <head>{css_style}</head>
        <body>
        <h2>הרשמה</h2>
        <form method=post>
        <input name=u placeholder='שם משתמש' required><br>
        <input name=p placeholder='סיסמה' type=password required><br>
        <button>הרשמה</button></form>
        </body></html>
        """
    return f"""
    <html lang="ar" dir="rtl">
    <head>{css_style}</head>
    <body>
    <h2>تسجيل</h2>
    <form method=post>
    <input name=u placeholder='Username' required><br>
    <input name=p placeholder='Password' type=password required><br>
    <button>تسجيل</button></form>
    </body></html>
    """

# معالجة التسجيل
@app.post("/register")
def reg_post(u: str = Form(...), p: str = Form(...), d=Depends(db)):
    user_count = d.query(User).count()
    role = "admin" if user_count == 0 else "user"
    d.add(User(username=u, password=pwd.hash(p), role=role))
    d.commit()
    return RedirectResponse("/", 303)

# صفحة إضافة البلاغ
@app.get("/add", response_class=HTMLResponse)
def add(request: Request):
    lang = get_language(request)
    if lang == "he":
        return f"""
        <html lang="he" dir="rtl">
        <head>{css_style}</head>
        <body>
        <h2>שלח דיווח</h2>
        <form method=post>
        <input name=t placeholder='כותרת' required><br>
        <textarea name=c rows=5 placeholder='תוכן' required></textarea><br>
        <button>שלח</button></form>
        </body></html>
        """
    return f"""
    <html lang="ar" dir="rtl">
    <head>{css_style}</head>
    <body>
    <h2>إضافة بلاغ</h2>
    <form method=post>
    <input name=t placeholder='عنوان' required><br>
    <textarea name=c rows=5 placeholder='محتوى' required></textarea><br>
    <button>إرسال</button></form>
    </body></html>
    """

# معالجة إضافة البلاغ
@app.post("/add")
def add_post(t: str = Form(...), c: str = Form(...), d=Depends(db)):
    d.add(Report(title=t, content=c))
    d.commit()
    return "تم الإرسال – بانتظار موافقة الأدمن"

# لوحة الأدمن
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(d=Depends(db)):
    reports = d.query(Report).all()
    html = f"""
    <html lang="ar" dir="rtl">
    <head>{css_style}</head>
    <body>
    <h2>لوحة الأدمن</h2>
    """
    for r in reports:
        html += f"""
        <div class='report'>
        <b>{r.title}</b> - {r.status}<br>
        <a class='button approve' href='/admin/approve/{r.id}'>✔ موافقة</a>
        <a class='button reject' href='/admin/reject/{r.id}'>❌ رفض</a>
        </div>
        """
    html += "</body></html>"
    return html

# الموافقة على البلاغ
@app.get("/admin/approve/{report_id}")
def approve(report_id: int, d=Depends(db)):
    report = d.query(Report).filter(Report.id == report_id).first()
    report.status = "approved"
    d.commit()
    return RedirectResponse("/admin", 303)

# رفض البلاغ
@app.get("/admin/reject/{report_id}")
def reject(report_id: int, d=Depends(db)):
    report = d.query(Report).filter(Report.id == report_id).first()
    report.status = "rejected"
    d.commit()
    return RedirectResponse("/admin", 303)
