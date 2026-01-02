from fastapi import FastAPI, Depends, Form
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
    role = Column(String, default="user")

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

# الصفحة الرئيسية
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>HamalNews | حمّال نيوز</h2>
    <a href='/register'>تسجيل</a> | <a href='/add'>إضافة بلاغ</a>
    """

# صفحة التسجيل
@app.get("/register", response_class=HTMLResponse)
def reg():
    return """
    <form method=post>
    <input name=u placeholder='Username'>
    <input name=p placeholder='Password' type=password>
    <button>Register</button></form>
    """

# معالجة التسجيل
@app.post("/register")
def reg_post(u: str = Form(...), p: str = Form(...), d=Depends(db)):
    d.add(User(username=u, password=pwd.hash(p)))
    d.commit()
    return RedirectResponse("/", 303)

# صفحة إضافة البلاغ
@app.get("/add", response_class=HTMLResponse)
def add():
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
