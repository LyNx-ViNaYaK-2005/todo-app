import os
import jwt
from jwt import PyJWTError
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------
# 1. SECURITY & CONFIGURATION
# ---------------------------------------------------------
SECRET_KEY = "TODO_APP_SUPER_SECRET_KEY_CHANGE_IN_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash((Argon2Hasher(),))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ---------------------------------------------------------
# 2. DATABASE SETUP (POSTGRESQL WITH RENDER SUPPORT)
# ---------------------------------------------------------
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todos.db")

# Fix Render's legacy postgres:// scheme prefix for SQLAlchemy 1.4+
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# 3. DATABASE MODELS
# ---------------------------------------------------------
class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    todos = relationship("DBTodo", back_populates="owner")

class DBTodo(Base):
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("DBUser", back_populates="todos")

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# 4. PYDANTIC SCHEMAS
# ---------------------------------------------------------
class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class TodoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    created_at: datetime
    completed_at: Optional[datetime] = None
    owner_id: int

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# ---------------------------------------------------------
# 5. FASTAPI APPLICATION SETUP & CORS CONFIGURATION
# ---------------------------------------------------------
app = FastAPI(
    title="Timestamped To-Do API",
    description="A personal task manager tracking creation and completion timestamps per user.",
    version="1.0.0"
)

origins = [
    "https://todomapper.netlify.app",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
        
    user = db.query(DBUser).filter(DBUser.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ---------------------------------------------------------
# 6. AUTHENTICATION ENDPOINTS
# ---------------------------------------------------------
@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(DBUser).filter(DBUser.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pwd = hash_password(user_data.password)
    new_user = DBUser(username=user_data.username, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/v1/auth/login", response_model=Token, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ---------------------------------------------------------
# 7. ADMIN ENDPOINTS
# ---------------------------------------------------------
@app.get("/api/v1/admin/users", response_model=list[UserResponse], tags=["Admin"])
def get_all_users(
    db: Session = Depends(get_db), 
    current_user: DBUser = Depends(get_current_user)
):
    if current_user.username != "Lynx":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access forbidden: You are not an admin!"
        )
    return db.query(DBUser).all()

# ---------------------------------------------------------
# 8. TIMESTAMPED TO-DO ENDPOINTS
# ---------------------------------------------------------
@app.post("/api/v1/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED, tags=["Todos"])
def create_todo(
    todo_data: TodoCreate, 
    db: Session = Depends(get_db), 
    current_user: DBUser = Depends(get_current_user)
):
    new_todo = DBTodo(
        title=todo_data.title,
        description=todo_data.description,
        owner_id=current_user.id
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo

@app.get("/api/v1/todos", response_model=list[TodoResponse], tags=["Todos"])
def get_user_todos(
    db: Session = Depends(get_db), 
    current_user: DBUser = Depends(get_current_user)
):
    return db.query(DBTodo).filter(DBTodo.owner_id == current_user.id).all()

@app.patch("/api/v1/todos/{todo_id}", response_model=TodoResponse, tags=["Todos"])
def update_todo(
    todo_id: int, 
    todo_update: TodoUpdate, 
    db: Session = Depends(get_db), 
    current_user: DBUser = Depends(get_current_user)
):
    db_todo = db.query(DBTodo).filter(DBTodo.id == todo_id, DBTodo.owner_id == current_user.id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")

    if todo_update.completed is True and not db_todo.completed:
        db_todo.completed = True
        db_todo.completed_at = datetime.now(timezone.utc)
    elif todo_update.completed is False:
        db_todo.completed = False
        db_todo.completed_at = None

    if todo_update.title is not None:
        db_todo.title = todo_update.title
    if todo_update.description is not None:
        db_todo.description = todo_update.description

    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/api/v1/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Todos"])
def delete_todo(
    todo_id: int, 
    db: Session = Depends(get_db), 
    current_user: DBUser = Depends(get_current_user)
):
    db_todo = db.query(DBTodo).filter(DBTodo.id == todo_id, DBTodo.owner_id == current_user.id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")

    db.delete(db_todo)
    db.commit()
    return