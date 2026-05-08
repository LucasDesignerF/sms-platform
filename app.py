"""
SMS Platform - Plataforma de Números Temporários
FastAPI + SQLite + TailwindCSS
"""

import asyncio
import aiohttp
import random
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from contextlib import asynccontextmanager
from jose import JWTError, jwt
from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
import secrets
import uvicorn
import os
from hashlib import sha256
import base64

# =================================================================================
# CONFIGURAÇÃO DE LOGGING
# =================================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('SMS-Platform')

# =================================================================================
# FUNÇÕES DE HASH DE SENHA (SHA256)
# =================================================================================

def hash_password(password: str) -> str:
    """Gera hash da senha usando SHA256 com salt"""
    salt = secrets.token_bytes(32)
    password_bytes = password.encode('utf-8')
    hash_obj = sha256(salt + password_bytes)
    hash_bytes = salt + hash_obj.digest()
    return base64.b64encode(hash_bytes).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifica a senha com o hash"""
    try:
        hash_bytes = base64.b64decode(hashed.encode('utf-8'))
        salt = hash_bytes[:32]
        stored_hash = hash_bytes[32:]
        password_bytes = password.encode('utf-8')
        computed_hash = sha256(salt + password_bytes).digest()
        return computed_hash == stored_hash
    except Exception:
        return False

# =================================================================================
# CONFIGURAÇÕES
# =================================================================================

SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dias

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =================================================================================
# MODELOS DO BANCO DE DADOS
# =================================================================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    premium_expires_at = Column(DateTime, nullable=True)
    
    numbers = relationship("PhoneNumber", back_populates="owner", cascade="all, delete-orphan")
    
    def verify_password(self, password: str) -> bool:
        return verify_password(password, self.hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return hash_password(password)


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), unique=True, index=True, nullable=False)
    country = Column(String(5), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_check = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    owner = relationship("User", back_populates="numbers")
    messages = relationship("SMSMessage", back_populates="number", cascade="all, delete-orphan")


class SMSMessage(Base):
    __tablename__ = "sms_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    number_id = Column(Integer, ForeignKey("phone_numbers.id"), nullable=False)
    sender = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    number = relationship("PhoneNumber", back_populates="messages")


# Criar tabelas
Base.metadata.create_all(bind=engine)

# =================================================================================
# FUNÇÕES DE AUTENTICAÇÃO
# =================================================================================

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Cookie(None), db: Session = None):
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    user = db.query(User).filter(User.username == username).first()
    return user

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================================
# CLIENTE DA API OnlineSMS
# =================================================================================

@dataclass
class SMSData:
    sender: str
    message: str
    timestamp: datetime

class OnlineSMSClient:
    BASE_URL = "https://online-sms.org"
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def get_random_number(self, country: str = "US") -> tuple[bool, Optional[str], Optional[str]]:
        # Simula número aleatório para teste
        number = ''.join([str(random.randint(0, 9)) for _ in range(11)])
        return True, number, None
    
    async def get_messages(self, phone_number: str) -> tuple[bool, List[SMSData], Optional[str]]:
        # Simula mensagens vazias para teste
        return True, [], None
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

# =================================================================================
# APLICAÇÃO FASTAPI
# =================================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando SMS Platform...")
    app.state.sms_client = OnlineSMSClient()
    yield
    await app.state.sms_client.close()
    logger.info("👋 SMS Platform finalizada")

app = FastAPI(title="SMS Platform", lifespan=lifespan)

# Função para ler arquivos HTML
def read_html_file(filename: str) -> str:
    filepath = os.path.join("templates", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Erro ao ler {filename}: {e}")
        return f"<h1>Erro ao carregar {filename}</h1>"

# =================================================================================
# ROTAS PÚBLICAS
# =================================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=read_html_file("index.html"))

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return HTMLResponse(content=read_html_file("register.html"))

@app.post("/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        html = read_html_file("register.html")
        html = html.replace('<div class="error-message" style="display: none;"></div>', 
                           '<div class="bg-error/20 border border-error rounded-xl p-4 mb-4 flex items-center gap-3">'
                           '<i class="bx bx-error-circle text-error text-xl"></i>'
                           '<span class="text-error">As senhas não coincidem</span></div>')
        return HTMLResponse(content=html)
    
    if len(password) < 6:
        html = read_html_file("register.html")
        html = html.replace('<div class="error-message" style="display: none;"></div>', 
                           '<div class="bg-error/20 border border-error rounded-xl p-4 mb-4 flex items-center gap-3">'
                           '<i class="bx bx-error-circle text-error text-xl"></i>'
                           '<span class="text-error">A senha deve ter pelo menos 6 caracteres</span></div>')
        return HTMLResponse(content=html)
    
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        html = read_html_file("register.html")
        html = html.replace('<div class="error-message" style="display: none;"></div>', 
                           '<div class="bg-error/20 border border-error rounded-xl p-4 mb-4 flex items-center gap-3">'
                           '<i class="bx bx-error-circle text-error text-xl"></i>'
                           '<span class="text-error">Usuário ou email já existe</span></div>')
        return HTMLResponse(content=html)
    
    try:
        hashed_password = User.get_password_hash(password)
        user = User(username=username, email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        html = read_html_file("register.html")
        html = html.replace('<div class="error-message" style="display: none;"></div>', 
                           '<div class="bg-error/20 border border-error rounded-xl p-4 mb-4 flex items-center gap-3">'
                           '<i class="bx bx-error-circle text-error text-xl"></i>'
                           '<span class="text-error">Erro ao criar conta. Tente novamente.</span></div>')
        return HTMLResponse(content=html)
    
    access_token = create_access_token(data={"sub": username})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    return response

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(content=read_html_file("login.html"))

@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not user.verify_password(password):
        html = read_html_file("login.html")
        html = html.replace('<div class="error-message" style="display: none;"></div>', 
                           '<div class="bg-error/20 border border-error rounded-xl p-4 mb-4 flex items-center gap-3">'
                           '<i class="bx bx-error-circle text-error text-xl"></i>'
                           '<span class="text-error">Usuário ou senha inválidos</span></div>')
        return HTMLResponse(content=html)
    
    access_token = create_access_token(data={"sub": username})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("token")
    return response

# =================================================================================
# ROTAS PROTEGIDAS
# =================================================================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, token: str = Cookie(None), db: Session = Depends(get_db)):
    user = await get_current_user(token, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    total_numbers = db.query(PhoneNumber).filter(PhoneNumber.user_id == user.id, PhoneNumber.is_active == True).count()
    total_messages = db.query(SMSMessage).join(PhoneNumber).filter(PhoneNumber.user_id == user.id).count()
    unread_messages = db.query(SMSMessage).join(PhoneNumber).filter(PhoneNumber.user_id == user.id, SMSMessage.is_read == False).count()
    
    html = read_html_file("dashboard.html")
    html = html.replace("{{ username }}", user.username)
    html = html.replace("{{ total_numbers }}", str(total_numbers))
    html = html.replace("{{ total_messages }}", str(total_messages))
    html = html.replace("{{ unread_messages }}", str(unread_messages))
    html = html.replace("{{ plan }}", "Premium" if user.is_premium else "Gratuito")
    html = html.replace("{{ member_since }}", user.created_at.strftime('%d/%m/%Y'))
    html = html.replace("{{ plan_expires }}", user.premium_expires_at.strftime('%d/%m/%Y') if user.premium_expires_at else "")
    
    # Recent numbers
    recent_numbers = db.query(PhoneNumber).filter(PhoneNumber.user_id == user.id, PhoneNumber.is_active == True).order_by(PhoneNumber.assigned_at.desc()).limit(5).all()
    numbers_html = ""
    for num in recent_numbers:
        numbers_html += f"""
        <tr class="table-row-hover transition">
            <td class="px-4 md:px-6 py-4 font-mono text-white text-sm">+{num.number}</td>
            <td class="px-4 md:px-6 py-4 text-gray-300">{num.country}</td>
            <td class="px-4 md:px-6 py-4 text-gray-400 text-sm hidden sm:table-cell">{num.assigned_at.strftime('%d/%m/%Y %H:%M')}</td>
            <td class="px-4 md:px-6 py-4 text-gray-400 text-sm hidden md:table-cell">{num.expires_at.strftime('%d/%m/%Y') if num.expires_at else 'Nunca'}</td>
            <td class="px-4 md:px-6 py-4">
                <a href="/messages?number_id={num.id}" class="text-primary-600 hover:text-primary-500 transition">
                    <i class='bx bx-message-detail text-xl'></i>
                </a>
            </td>
        </tr>
        """
    html = html.replace("{{ recent_numbers }}", numbers_html if recent_numbers else '<tr><td colspan="5" class="px-6 py-12 text-center text-gray-500">Nenhum número adquirido ainda</td></tr>')
    
    # Recent messages
    recent_messages = db.query(SMSMessage).join(PhoneNumber).filter(PhoneNumber.user_id == user.id).order_by(SMSMessage.received_at.desc()).limit(10).all()
    messages_html = ""
    for msg in recent_messages:
        messages_html += f"""
        <div class="px-5 md:px-6 py-4 hover:bg-surface-200 transition">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex flex-wrap items-center gap-2 mb-2">
                        <i class='bx bx-user-circle text-gray-500 text-xl'></i>
                        <span class="font-medium text-white">{msg.sender}</span>
                        <span class="text-xs text-gray-500">{msg.received_at.strftime('%d/%m/%Y %H:%M:%S')}</span>
                        {('<span class="bg-primary-600/20 text-primary-400 text-xs px-2 py-0.5 rounded-full">Nova</span>' if not msg.is_read else '')}
                    </div>
                    <p class="text-gray-400 text-sm">{msg.content[:80]}{'...' if len(msg.content) > 80 else ''}</p>
                </div>
                <a href="/messages?number_id={msg.number_id}" class="text-primary-600 hover:text-primary-500 ml-4">
                    <i class='bx bx-message-detail text-xl'></i>
                </a>
            </div>
        </div>
        """
    html = html.replace("{{ recent_messages }}", messages_html if recent_messages else '<div class="px-6 py-12 text-center text-gray-500">Nenhuma mensagem recebida ainda</div>')
    
    return HTMLResponse(content=html)

@app.get("/numbers", response_class=HTMLResponse)
async def numbers_page(request: Request, token: str = Cookie(None), db: Session = Depends(get_db)):
    user = await get_current_user(token, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_numbers = db.query(PhoneNumber).filter(PhoneNumber.user_id == user.id).order_by(PhoneNumber.assigned_at.desc()).all()
    
    html = read_html_file("numbers.html")
    html = html.replace("{{ username }}", user.username)
    
    numbers_html = ""
    for num in user_numbers:
        numbers_html += f"""
        <div class="bg-dark-400 rounded-xl shadow-lg overflow-hidden card-hover border border-surface-200">
            <div class="number-card-header px-4 py-3 text-white">
                <div class="flex justify-between items-center">
                    <span class="font-mono text-lg font-bold">+{num.number}</span>
                    <span class="text-xs bg-white/20 px-2 py-1 rounded">{num.country}</span>
                </div>
            </div>
            <div class="p-4">
                <div class="space-y-2 mb-4">
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Adquirido:</span>
                        <span class="text-gray-300">{num.assigned_at.strftime('%d/%m/%Y %H:%M')}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-400">Status:</span>
                        <span class="text-primary-600 font-medium">Ativo</span>
                    </div>
                    {f'<div class="flex justify-between text-sm"><span class="text-gray-400">Expira:</span><span class="text-gray-300">{num.expires_at.strftime("%d/%m/%Y") if num.expires_at else "Nunca"}</span></div>' if num.expires_at else ''}
                </div>
                <div class="flex gap-2">
                    <a href="/messages?number_id={num.id}" class="flex-1 bg-primary-600/20 text-primary-600 text-center py-2 rounded-lg hover:bg-primary-600/30 transition">Ver SMS</a>
                    <button onclick="checkMessages({num.id})" class="flex-1 bg-surface-200 text-gray-300 py-2 rounded-lg hover:bg-surface-100 transition">Verificar</button>
                    <button onclick="deleteNumber({num.id})" class="bg-error/20 text-error w-10 rounded-lg hover:bg-error/30 transition"><i class="bx bx-trash"></i></button>
                </div>
            </div>
        </div>
        """
    
    html = html.replace("{{ numbers_list }}", numbers_html if user_numbers else '<div class="text-center py-8 text-gray-400">Nenhum número adquirido ainda. Clique em "Adquirir Número" para começar.</div>')
    
    return HTMLResponse(content=html)

@app.post("/numbers/acquire")
async def acquire_number(
    country: str = Form(...),
    token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    if not user:
        return JSONResponse({"error": "Não autenticado"}, status_code=401)
    
    user_numbers_count = db.query(PhoneNumber).filter(PhoneNumber.user_id == user.id, PhoneNumber.is_active == True).count()
    max_numbers = 5 if not user.is_premium else 20
    
    if user_numbers_count >= max_numbers:
        return JSONResponse({"error": f"Limite de {max_numbers} números atingido"}, status_code=400)
    
    client = app.state.sms_client
    success, number, error = await client.get_random_number(country)
    
    if not success:
        return JSONResponse({"error": error or "Não foi possível obter número"}, status_code=400)
    
    expires_at = datetime.utcnow() + timedelta(days=7 if not user.is_premium else 30)
    phone_number = PhoneNumber(
        number=number,
        country=country.upper(),
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(phone_number)
    db.commit()
    
    return JSONResponse({
        "success": True,
        "number": number,
        "country": country,
        "expires_at": expires_at.isoformat()
    })

@app.post("/numbers/{number_id}/delete")
async def delete_number(number_id: int, token: str = Cookie(None), db: Session = Depends(get_db)):
    user = await get_current_user(token, db)
    if not user:
        return JSONResponse({"error": "Não autenticado"}, status_code=401)
    
    phone_number = db.query(PhoneNumber).filter(
        PhoneNumber.id == number_id,
        PhoneNumber.user_id == user.id
    ).first()
    
    if not phone_number:
        return JSONResponse({"error": "Número não encontrado"}, status_code=404)
    
    db.delete(phone_number)
    db.commit()
    
    return JSONResponse({"success": True})

@app.get("/messages", response_class=HTMLResponse)
async def messages_page(request: Request, token: str = Cookie(None), db: Session = Depends(get_db)):
    user = await get_current_user(token, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    number_id = request.query_params.get("number_id")
    html = read_html_file("messages.html")
    html = html.replace("{{ username }}", user.username)
    
    if number_id:
        phone_number = db.query(PhoneNumber).filter(
            PhoneNumber.id == number_id,
            PhoneNumber.user_id == user.id
        ).first()
        
        if phone_number:
            messages = db.query(SMSMessage).filter(SMSMessage.number_id == number_id).order_by(SMSMessage.received_at.desc()).all()
            for msg in messages:
                msg.is_read = True
            db.commit()
            
            messages_html = ""
            for msg in messages:
                messages_html += f"""
                <div class="px-5 md:px-6 py-4 message-hover transition message-enter">
                    <div class="flex items-start gap-3">
                        <div class="flex-shrink-0">
                            <div class="w-10 h-10 bg-primary-600/20 rounded-full flex items-center justify-center">
                                <i class='bx bx-user-circle text-2xl text-primary-600'></i>
                            </div>
                        </div>
                        <div class="flex-1">
                            <div class="flex flex-wrap items-center gap-2 mb-2">
                                <span class="font-semibold text-white">{msg.sender}</span>
                                <span class="text-xs text-gray-500">{msg.received_at.strftime('%d/%m/%Y %H:%M:%S')}</span>
                                {('<span class="bg-primary-600/20 text-primary-400 text-xs px-2 py-0.5 rounded-full">Nova</span>' if not msg.is_read else '')}
                            </div>
                            <div class="message-bubble p-4 mt-2">
                                <p class="text-gray-300 whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                            </div>
                        </div>
                    </div>
                </div>
                """
            
            html = html.replace("{{ current_number.number }}", phone_number.number)
            html = html.replace("{{ current_number.country }}", phone_number.country)
            html = html.replace("{{ current_number.id }}", str(phone_number.id))
            html = html.replace("{{ messages_list }}", messages_html if messages else '<div class="text-center py-8 text-gray-400">Nenhuma mensagem recebida ainda</div>')
            html = html.replace("{{ show_number_select }}", "none")
            html = html.replace("{{ show_messages }}", "block")
        else:
            html = html.replace("{{ show_number_select }}", "block")
            html = html.replace("{{ show_messages }}", "none")
    else:
        numbers_html = ""
        for num in db.query(PhoneNumber).filter(PhoneNumber.user_id == user.id, PhoneNumber.is_active == True).all():
            numbers_html += f"""
            <a href="/messages?number_id={num.id}" class="bg-dark-500 hover:bg-surface-200 border border-surface-200 rounded-lg p-3 text-center transition number-card-hover">
                <i class='bx bx-phone text-2xl text-primary-600 mb-1 block'></i>
                <span class="font-mono text-sm text-white">+{num.number}</span>
            </a>
            """
        html = html.replace("{{ numbers_grid }}", numbers_html)
        html = html.replace("{{ show_number_select }}", "block")
        html = html.replace("{{ show_messages }}", "none")
    
    return HTMLResponse(content=html)

@app.post("/messages/check/{number_id}")
async def check_messages(number_id: int, token: str = Cookie(None), db: Session = Depends(get_db)):
    user = await get_current_user(token, db)
    if not user:
        return JSONResponse({"error": "Não autenticado"}, status_code=401)
    
    phone_number = db.query(PhoneNumber).filter(
        PhoneNumber.id == number_id,
        PhoneNumber.user_id == user.id
    ).first()
    
    if not phone_number:
        return JSONResponse({"error": "Número não encontrado"}, status_code=404)
    
    client = app.state.sms_client
    success, messages, error = await client.get_messages(phone_number.number)
    
    new_messages = []
    if success:
        for msg in messages:
            existing = db.query(SMSMessage).filter(
                SMSMessage.number_id == number_id,
                SMSMessage.sender == msg.sender,
                SMSMessage.content == msg.message
            ).first()
            
            if not existing:
                new_msg = SMSMessage(
                    number_id=number_id,
                    sender=msg.sender,
                    content=msg.message,
                    received_at=datetime.utcnow()
                )
                db.add(new_msg)
                new_messages.append(new_msg)
        db.commit()
    
    return JSONResponse({
        "success": True,
        "new_messages": len(new_messages)
    })

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, token: str = Cookie(None), db: Session = Depends(get_db)):
    user = await get_current_user(token, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    html = read_html_file("profile.html")
    html = html.replace("{{ username }}", user.username)
    html = html.replace("{{ email }}", user.email)
    html = html.replace("{{ plan }}", "Premium" if user.is_premium else "Gratuito")
    html = html.replace("{{ member_since }}", user.created_at.strftime('%d/%m/%Y'))
    html = html.replace("{{ plan_expires }}", user.premium_expires_at.strftime('%d/%m/%Y') if user.premium_expires_at else "")
    
    return HTMLResponse(content=html)

@app.post("/profile/update")
async def update_profile(
    email: str = Form(None),
    current_password: str = Form(None),
    new_password: str = Form(None),
    token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    user = await get_current_user(token, db)
    if not user:
        return JSONResponse({"error": "Não autenticado"}, status_code=401)
    
    if email:
        user.email = email
    
    if current_password and new_password:
        if len(new_password) < 6:
            return JSONResponse({"error": "A nova senha deve ter pelo menos 6 caracteres"}, status_code=400)
        if user.verify_password(current_password):
            user.hashed_password = User.get_password_hash(new_password)
        else:
            return JSONResponse({"error": "Senha atual incorreta"}, status_code=400)
    
    db.commit()
    return JSONResponse({"success": True})

@app.get("/api/countries")
async def get_countries():
    return {"countries": [
        {"code": "US", "name": "Estados Unidos", "flag": "🇺🇸"},
        {"code": "UK", "name": "Reino Unido", "flag": "🇬🇧"},
        {"code": "BR", "name": "Brasil", "flag": "🇧🇷"},
        {"code": "CA", "name": "Canadá", "flag": "🇨🇦"},
        {"code": "AU", "name": "Austrália", "flag": "🇦🇺"},
        {"code": "DE", "name": "Alemanha", "flag": "🇩🇪"},
        {"code": "FR", "name": "França", "flag": "🇫🇷"},
        {"code": "ES", "name": "Espanha", "flag": "🇪🇸"},
        {"code": "IT", "name": "Itália", "flag": "🇮🇹"},
    ]}

# =================================================================================
# PONTO DE ENTRADA
# =================================================================================

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)