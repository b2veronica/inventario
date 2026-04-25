from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base # Importación actualizada
from pydantic import BaseModel

# 1. Configuración de Seguridad y Base de Datos
# Se recomienda usar "bcrypt" específicamente para evitar errores de detección
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SQLALCHEMY_DATABASE_URL = "sqlite:///./inventario.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Modelo de la Base de Datos
class UserDB(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) 

# Crear tablas
Base.metadata.create_all(bind=engine)

# 3. Esquemas de Pydantic
class LoginSchema(BaseModel):
    username: str
    password: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Crear usuarios iniciales
def init_db():
    db = SessionLocal()
    try:
        if db.query(UserDB).count() == 0:
            usuarios = [
                ("admin", "admin123", "admin"),
                ("almacen", "stock456", "almacenista"),
                ("cajera", "venta789", "cajera")
            ]
            for user, pwd, role in usuarios:
                h_pwd = pwd_context.hash(pwd)
                db.add(UserDB(username=user, password_hash=h_pwd, role=role))
            db.commit()
            print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar BD: {e}")
    finally:
        db.close()

# Llamada a la inicialización
init_db()

# 5. Ruta de Login
@app.post("/login")
def login(data: LoginSchema):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.username == data.username).first()
    db.close() # Importante cerrar la sesión
    
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    return {
        "message": "Login exitoso",
        "username": user.username,
        "role": user.role
    }

@app.get("/")
def read_root():
    return {"status": "Backend funcionando"}