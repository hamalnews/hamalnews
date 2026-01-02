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

# إعداد قاعدة البيانات
engine = create_engine("sqlite:///./db.sqlite", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# نموذج المستخدم
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="user")  # user أو admin

# نموذج البلاغ
class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    status = Column(String, default="pending")

Base.metadata.create_all(engine)

# دالة لجلسة قاعدة البيانات
def db():
    s = Session()
    try:
        yield s
    finally:
        s.close()

# دالة لتحديد اللغة
def get_language(request: Request):
    lang = request.cookies.get("lang")
    return lang if lang in ["ar", "he"] else "ar"

# الصفحة الرئيسية
@app.get("/", response_class=HTMLResponse)
def home(request: Request, d=Depends(db)):
    lang = get_language(request)
    if lang == "he":
        return """
        <html lang="he" dir="rtl">
        <head>
        <style>
            body { font-family: Arial, sans-serif; background:#f7f7f7; padding:20px; text-align:center;}
            h1 { color:#2c3e50; }
            a.button { display:inline-block; margin:10px; padding:10px 20px; background:#3498db; color:white; text-decoration:none; border-radius:10px; }
            a.button:hover { background:#2980b9; }
        </style>
        </head>
        <body>
        <h1>HamalNews | חדשות</h1>
        <a class='button' href='/register'>הרשמה</a>
        <a class='button' href='/add'>שלח דיווח</a>
        <a class='button' href='/set_language/ar'>AR</a>
        </body></html>
        """
    return """
    <html lang="ar" dir="rtl">
    <head>
    <style>
        body { font-family: Arial, sans-serif; background:#f7f7f7; padding:20px; text-align:center;}
        h1 { color:#2c3e50; }
        a.button { display:inline-block; margin:10px; padding:10px 20px; background:#3498db; color:white; text-decoration:none; border-radius:10px; }
        a.button:hover { background:#2980b9; }
    </style>
    </head>
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
        return """
        <html lang="he" dir="rtl">
        <head>
        <style>
            body{ font-family:Arial; background:#ecf0f1; text-align:center; padding:30px;}
            input, button { padding:10px; margin:5px; border-radius:8px; border:1px solid #bdc3c7; width:200px;}
            button { background:#27ae60; color:white; border:none;}
            button:hover { background:#2ecc71; cursor:pointer;}
        </style>
        </head>
        <body>
        <h2>הרשמה</h2>
        <form method=post>
        <input name=u placeholder='שם משתמש'><br>
        <input name=p placeholder='סיסמה' type=password><br>
        <button>הרשמה</button></form>
        </body></html>
        """
    return """
    <html lang="ar" dir="rtl">
    <head>
    <style>
        body{ font-family:Arial; background:#ecf0f1; text-align:center; padding:30px;}
        input, button { padding:10px; margin:5px; border-radius:8px; border:1px solid #bdc3c7; width:200px;}
        button { background:#27ae60; color:white; border:none;}
        button:hover { background:#2ecc71; cursor:pointer;}
    </style>
    </head>
    <body>
    <h2>تسجيل</h2>
    <form method=post>
    <input name=u placeholder='Username'><br>
    <input name=p placeholder='Password' type=password><br>
    <button>Register</button></form>
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
        return """
        <html lang="he" dir="rtl">
        <head>
        <style>
            body{ font-family:Arial; background:#fefefe; padding:30px; text-align:center;}
            input, textarea, button { padding:10px; margin:5px; border-radius:8px; border:1px solid #bdc3c7; width:250px;}
            button { background:#e67e22; color:white; border:none;}
            button:hover { background:#d35400; cursor:pointer;}
        </style>
        </head>
        <body>
        <h2>שלח דיווח</h2>
        <form method=post>
        <input name=t placeholder='כותרת'><br>
        <textarea name=c rows=5 placeholder='תוכן'></textarea><br>
        <button>שלח</button></form>
        </body></html>
        """
    return """
    <html lang="ar" dir="rtl">
    <head>
    <style>
        body{ font-family:Arial; background:#fefefe; padding:30px; text-align:center;}
        input, textarea, button { padding:10px; margin:5px; border-radius:8px; border:1px solid #bdc3c7; width:250px;}
        button { background:#e67e22; color:white; border:none;}
        button:hover { background:#d35400; cursor:pointer;}
    </style>
    </head>
    <body>
    <h2>إضافة بلاغ</h2>
    <form method=post>
    <input name=t placeholder='Title'><br>
    <textarea name=c rows=5 placeholder='Content'></textarea><br>
    <button>Send</button></form>
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
    html = """
    <html lang="ar" dir="rtl">
    <head>
    <style>
        body{ font-family:Arial; background:#f7f7f7; padding:20px;}
        h2{ color:#2c3e50; text-align:center;}
        .report{background:white; padding:10px; margin:10px auto; border-radius:8px; width:300px;}
        a.button{padding:5px 10px; margin:5px; text-decoration:none; color:white; border-radius:8px;}
        a.approve{background:#27ae60;} a.reject{background:#c0392b;}
        a.approve:hover{background:#2ecc71;} a.reject:hover{background:#e74c3c;}
    </style>
    </head>
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

@app.get("/admin/approve/{report_id}")
def approve(report_id: int, d=Depends(db)):
    report = d.query(Report).filter(Report.id == report_id).first()
    report.status = "approved"
    d.commit()
    return RedirectResponse("/admin", 303)

@app.get("/admin/reject/{report_id}")
def reject(report_id: int, d=Depends(db)):
    report = d.query(Report.id == report_id).first()
    report.status = "rejected"
    d.commit()
    return RedirectResponse("/admin", 303)
