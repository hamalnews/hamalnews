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
        <h2>HamalNews | חדשות</h2>
        <a href='/register'>הרשמה</a> | <a href='/add'>שלח דיווח</a> | <a href='/set_language/ar'>AR</a>
        """
    return """
    <h2>HamalNews | حمّال نيوز</h2>
    <a href='/register'>تسجيل</a> | <a href='/add'>إضافة بلاغ</a> | <a href='/set_language/he'>HE</a>
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
        <form method=post>
        <input name=u placeholder='שם משתמש'>
        <input name=p placeholder='סיסמה' type=password>
        <button>הרשמה</button></form>
        """
    return """
    <form method=post>
    <input name=u placeholder='Username'>
    <input name=p placeholder='Password' type=password>
    <button>Register</button></form>
    """

# معالجة التسجيل
@app.post("/register")
def reg_post(u: str = Form(...), p: str = Form(...), d=Depends(db)):
    # أول مستخدم يصبح أدمن
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
        <form method=post>
        <input name=t placeholder='כותרת'>
        <textarea name=c></textarea>
        <button>שלח</button></form>
        """
    return """
    <form method=post>
    <input name=t placeholder='Title'>
    <textarea name=c></textarea>
    <button>Send</button></form>
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
    html = "<h2>لوحة الأدمن</h2>"
    for r in reports:
        html += f"<div><b>{r.title}</b> - {r.status} \
        <a href='/admin/approve/{r.id}'>✔ موافقة</a> \
        <a href='/admin/reject/{r.id}'>❌ رفض</a></div><hr>"
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
