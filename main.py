from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel
from typing import List

# 1. CONFIGURACIÓN DE BASE DE DATOS
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SQLALCHEMY_DATABASE_URL = "sqlite:///./inventario.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. MODELOS DE LA BASE DE DATOS
class UserDB(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)

class ProductoDB(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio = Column(Integer)
    stock = Column(Integer, default=0)
    imagen_url = Column(String)

class ClienteDB(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    telefono = Column(String)

class PedidoDB(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer)
    total = Column(Integer)
    estado = Column(String, default="pendiente") # pendiente, entregado


# Crear todas las tablas nuevas
Base.metadata.create_all(bind=engine)

# 3. ESQUEMAS PARA RECIBIR DATOS (PYDANTIC)
class LoginSchema(BaseModel):
    username: str
    password: str

class PedidoSchema(BaseModel):
    nombre_cliente: str
    telefono_cliente: str
    producto_id: int
    cantidad: int

# 4. INICIALIZACIÓN DE LA APP Y CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. POBLAR DATOS INICIALES
def init_db():
    Base.metadata.create_all(bind=engine) # Esto crea las tablas si no existen
    db = SessionLocal()
    try:
        # Crear usuarios si no existen
        if db.query(UserDB).count() == 0:
            usuarios = [
                ("admin", "admin123", "admin"),
                ("almacen", "stock456", "almacenista"),
                ("cajera", "venta789", "cajera")
            ]
            for user, pwd, role in usuarios:
                db.add(UserDB(username=user, password_hash=pwd_context.hash(pwd), role=role))
        
        # Crear productos iniciales si no existen
        if db.query(ProductoDB).count() == 0:
            prods = [
                ProductoDB(nombre="Laptop Dell", precio=12000, stock=10, imagen_url="https://m.media-amazon.com/images/I/61vG6H9G-RL._AC_SL1500_.jpg"),
                ProductoDB(nombre="Mouse Gamer", precio=450, stock=20, imagen_url="https://resource.logitechg.com/w_692,c_limit,q_auto,f_auto,dpr_1.0/d_transparent.gif/content/dam/gaming/en/products/g502-lightspeed/g502-lightspeed-gallery-1.png"),
                ProductoDB(nombre="Silla Gamer", precio=6500, stock=10, imagen_url="https://www.amazon.com.mx/s?k=silla+gamer&adgrpid=1169880793798142&hvadid=73117793944728&hvbmt=be&hvdev=c&hvlocphy=151332&hvnetw=o&hvqmt=e&hvtargid=kwd-73117901294316%3Aloc-119&hydadcr=26974_11687084&mcid=1d35df4e09d3317f9ef35ca70bf5c700&msclkid=f694cb597592157d723da2ac62053fd7&tag=msndeskstdmx-20&ref=pd_sl_6dklsv9tje_e"),
                ProductoDB(nombre="Juego de Destornilladores", precio=350, stock=25, imagen_url="https://m.media-amazon.com/images/I/81z9R-hU6LL._AC_SL1500_.jpg"),
                ProductoDB(nombre="Lámpara LED Taller", precio=450, stock=15, imagen_url="https://m.media-amazon.com/images/I/61m6XpYv7AL._AC_SL1500_.jpg"),
                ProductoDB(nombre="Multímetro Digital", precio=680, stock=8, imagen_url="https://m.media-amazon.com/images/I/61S6h9uXG1L._AC_SL1500_.jpg"),
                ProductoDB(nombre="Cable HDMI", precio=120, stock=50, imagen_url="https://m.media-amazon.com/images/I/71I3u7U6SML._AC_SL1500_.jpg")
            ]
            db.add_all(prods)
        db.commit()
        print("productos insertados")
    except Exception as e:
        print(f"Hubo un error: {e}")
    
    finally:
        db.close()

init_db()

# 6. RUTAS (ENDPOINTS)

@app.post("/login")
def login(data: LoginSchema):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.username == data.username).first()
    db.close()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Error de login")
    return {"message": "OK", "username": user.username, "role": user.role}

@app.get("/productos")
def listar_productos():
    db = SessionLocal()
    prods = db.query(ProductoDB).all()
    db.close()
    return prods

@app.post("/crear-pedido")
def crear_pedido(data: PedidoSchema):
    db = SessionLocal()
    try:
        # 1. Buscar o crear cliente
        cliente = db.query(ClienteDB).filter(ClienteDB.nombre == data.nombre_cliente).first()
        if not cliente:
            cliente = ClienteDB(nombre=data.nombre_cliente, telefono=data.telefono_cliente)
            db.add(cliente)
            db.flush() # Para obtener el ID del nuevo cliente

        # 2. Verificar producto y stock
        producto = db.query(ProductoDB).filter(ProductoDB.id == data.producto_id).first()
        if not producto or producto.stock < data.cantidad:
            raise HTTPException(status_code=400, detail="No hay suficiente stock")

        # 3. Registrar el Pedido
        total_pago = producto.precio * data.cantidad
        nuevo_pedido = PedidoDB(
            cliente_id=cliente.id,
            producto_id=producto.id,
            cantidad=data.cantidad,
            total=total_pago
        )
        
        # 4. Actualizar Stock
        producto.stock -= data.cantidad
        
        db.add(nuevo_pedido)
        db.commit()
        return {"status": "success", "pedido_id": nuevo_pedido.id, "total": total_pago}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/pedidos-pendientes")
def listar_pedidos():
    db = SessionLocal()
    # Esta ruta es para que el almacenista vea qué clientes compraron
    pedidos = db.query(PedidoDB).filter(PedidoDB.estado == "pendiente").all()
    db.close()
    return pedidos

@app.get("/")
def home():
    return {"mensaje": "Servidor Local Activo con ngrok"}