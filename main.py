from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel

# 1. Configuración de Seguridad y Base de Datos
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SQLALCHEMY_DATABASE_URL = "sqlite:///./inventario.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Modelos de la Base de Datos
class UserDB(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # ¡Importante! Descomentado

class ProductoDB(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio = Column(Integer)
    stock = Column(Integer, default=0)
    imagen_url = Column(String)

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

# 4. Función de inicialización unificada (Usuarios + Productos)
def init_db():
    db = SessionLocal()
    try:
        # Inicializar Usuarios
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
            print("Usuarios creados.")

        # Inicializar Productos
        if db.query(ProductoDB).count() == 0:
            ejemplos = [
                ProductoDB(nombre="Laptop Dell", precio=12000, stock=5, imagen_url="https://m.media-amazon.com/images/I/61vG6H9G-RL._AC_SL1500_.jpg"),
                ProductoDB(nombre="Mouse Gamer", precio=450, stock=15, imagen_url="https://resource.logitechg.com/w_692,c_limit,q_auto,f_auto,dpr_1.0/d_transparent.gif/content/dam/gaming/en/products/g502-lightspeed/g502-lightspeed-gallery-1.png")
            ]
            db.add_all(ejemplos)
            db.commit()
            print("Productos creados.")
            
    except Exception as e:
        print(f"Error al inicializar BD: {e}")
    finally:
        db.close()

init_db()

# 5. Rutas (Endpoints)

@app.post("/login")
def login(data: LoginSchema):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.username == data.username).first()
    db.close()
    
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    return {
        "message": "Login exitoso",
        "username": user.username,
        "role": user.role  # <-- Tu compañera necesita esto
    }

@app.get("/productos")
def listar_productos():
    db = SessionLocal()
    productos = db.query(ProductoDB).all()
    db.close()
    return productos

@app.post("/productos/vender/{prod_id}")
def vender_producto(prod_id: int):
    db = SessionLocal()
    producto = db.query(ProductoDB).filter(ProductoDB.id == prod_id).first()
    
    if not producto:
        db.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if producto.stock <= 0:
        db.close()
        raise HTTPException(status_code=400, detail="Sin existencias (Stock agotado)")
    
    producto.stock -= 1
    db.commit()
    db.close()
    return {"message": "Venta realizada", "quedan": producto.stock}

@app.get("/")
def read_root():
    return {"status": "Backend funcionando correctamente"}