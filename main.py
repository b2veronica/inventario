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
                ProductoDB(nombre="Laptop Dell", precio=12000, stock=10, imagen_url="https://www.google.com/imgres?q=laptop%20dell%20png&imgurl=https%3A%2F%2Fe7.pngegg.com%2Fpngimages%2F465%2F338%2Fpng-clipart-laptop-dell-xps-13-9360-intel-core-i7-laptop-electronics-netbook.png&imgrefurl=https%3A%2F%2Fwww.pngegg.com%2Fes%2Fpng-efqho&docid=Rq2YNCVrWsWgNM&tbnid=n63Ydn8qo2WalM&vet=12ahUKEwismJDh2ZmUAxXImWoFHRUVFZQQnPAOegQIHxAB..i&w=900&h=532&hcb=2&ved=2ahUKEwismJDh2ZmUAxXImWoFHRUVFZQQnPAOegQIHxAB"),
                ProductoDB(nombre="Mouse Gamer", precio=450, stock=20, imagen_url="https://www.google.com/imgres?q=mouse.png&imgurl=https%3A%2F%2Fimg.freepik.com%2Fpremium-psd%2Fcomputer-mouse-isolated-transparent-background_191095-18070.jpg%3Fsemt%3Dais_hybrid%26w%3D740%26q%3D80&imgrefurl=https%3A%2F%2Fwww.freepik.com%2Fpsd%2Fcomputer-mouse-png&docid=Zt7E56YV8Cz1AM&tbnid=cq16VL_AAQe3PM&vet=12ahUKEwispKXU2JmUAxXzlWoFHUHXJUwQnPAOegQIGBAB..i&w=740&h=740&hcb=2&ved=2ahUKEwispKXU2JmUAxXzlWoFHUHXJUwQnPAOegQIGBAB"),
                ProductoDB(nombre="Silla Gamer", precio=6500, stock=10, imagen_url="https://www.google.com/imgres?q=gamer%20chair%20png&imgurl=https%3A%2F%2Fp7.hiclipart.com%2Fpreview%2F894%2F180%2F49%2Fgaming-chair-racing-video-game-office-desk-chairs-chair.jpg&imgrefurl=https%3A%2F%2Fwww.hiclipart.com%2Ffree-transparent-background-png-clipart-cllhq&docid=yUOSyuQPIRefkM&tbnid=3z-RwppDSM6dcM&vet=12ahUKEwiayL2L2pmUAxXd4ckDHRPSK5YQnPAOegQIGhAB..i&w=800&h=800&hcb=2&ved=2ahUKEwiayL2L2pmUAxXd4ckDHRPSK5YQnPAOegQIGhAB"),
                ProductoDB(nombre="Juego de Destornilladores", precio=350, stock=25, imagen_url="https://www.google.com/imgres?q=destornilladores%20para%20lap.png&imgurl=https%3A%2F%2Fw7.pngwing.com%2Fpngs%2F941%2F81%2Fpng-transparent-nexus-4-iphone-tool-screwdriver-torx-screwdriver-technic-screw-brush.png&imgrefurl=https%3A%2F%2Fwww.pngwing.com%2Fes%2Ffree-png-zkqpe&docid=3bahkM1FVLrk2M&tbnid=lo8Lr7UyPVQURM&vet=12ahUKEwiJ3pOw2pmUAxXB4skDHQ7YFT0QnPAOegQIYxAB..i&w=920&h=920&hcb=2&ved=2ahUKEwiJ3pOw2pmUAxXB4skDHQ7YFT0QnPAOegQIYxAB"),
                ProductoDB(nombre="Lámpara LED Taller", precio=450, stock=15, imagen_url="https://www.pngwing.com/es/free-png-dnyiy"),
                ProductoDB(nombre="Multímetro Digital", precio=680, stock=8, imagen_url="https://www.google.com/imgres?q=multimetro%20png&imgurl=https%3A%2F%2Fe7.pngegg.com%2Fpngimages%2F180%2F70%2Fpng-clipart-avtoelektrika-electronics-accessory-ooo-n-yu-layn-avto-multimeter-thumbnail.png&imgrefurl=https%3A%2F%2Fwww.pngegg.com%2Fes%2Fsearch%3Fq%3Dmultimetro&docid=cUzJEwSS5KRZaM&tbnid=CVvKv0bBn74bmM&vet=12ahUKEwjg3vTv2pmUAxUh2ckDHdJNGC8QnPAOegQIGBAB..i&w=348&h=348&hcb=2&ved=2ahUKEwjg3vTv2pmUAxUh2ckDHdJNGC8QnPAOegQIGBAB"),
                ProductoDB(nombre="Cable HDMI", precio=120, stock=50, imagen_url="https://www.google.com/imgres?q=cable%20hdmi%20png&imgurl=https%3A%2F%2Fwww.vhv.rs%2Fdpng%2Fd%2F468-4683222_hdtv-hdmi-cable-png-image-hdmi-cable-png.png&imgrefurl=https%3A%2F%2Fwww.vhv.rs%2Fviewpic%2FhxombTw_hdtv-hdmi-cable-png-image-hdmi-cable-png%2F&docid=y5sHohutkvBEZM&tbnid=ezqBm4njlVfnFM&vet=12ahUKEwjXi9f22pmUAxVDHdAFHWGaMi4QnPAOegQIGxAB..i&w=860&h=534&hcb=2&ved=2ahUKEwjXi9f22pmUAxVDHdAFHWGaMi4QnPAOegQIGxAB")
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

@app.put("/completar-pedido/{pedido_id}")
def completar_pedido(pedido_id: int):
    db = SessionLocal()
    try:
        pedido = db.query(PedidoDB).filter(PedidoDB.id == pedido_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        pedido.estado = "entregado"
        db.commit()
        return {"status": "success"}
    finally:
        db.close()

@app.put("/actualizar-stock/{producto_id}")
def actualizar_stock(producto_id: int, data: dict):
    db = SessionLocal()
    try:
        nuevo_valor = data.get("stock")
        if nuevo_valor is None or nuevo_valor < 0:
            raise HTTPException(status_code=400, detail="Valor de stock no puede ser negativo")
        producto = db.query(ProductoDB).filter(ProductoDB.id == producto_id).first()
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        producto.stock = data.get("stock")
        db.commit()
        return {"status": "success"}
    finally:
        db.close()

@app.post("/crear-producto")
def crear_producto(data: dict):
    db = SessionLocal()
    try:
        nuevo_prod = ProductoDB(
            nombre=data.get("nombre"),
            precio=data.get("precio"),
            stock=data.get("stock"),
            imagen_url=data.get("imagen_url")
        )
        db.add(nuevo_prod)
        db.commit()
        return {"status": "success"}
    finally:
        db.close()

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

@app.get("/pedidos")
def obtener_todos_los_pedidos():
    db = SessionLocal()
    try:
        # Trae todos los pedidos de la base de datos sin filtrar
        pedidos = db.query(PedidoDB).all()
        return pedidos
    finally:
        db.close()

@app.get("/")
def home():
    return {"mensaje": "Servidor Local Activo con ngrok"}