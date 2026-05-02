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
                ProductoDB(nombre="Laptop Dell", precio=12000, stock=10, imagen_url="https://w7.pngwing.com/pngs/314/974/png-transparent-dell-xps-laptop-intel-dell-inspiron-laptop-gadget-electronics-netbook.png"),
                ProductoDB(nombre="Mouse Gamer", precio=450, stock=20, imagen_url="https://png.pngtree.com/png-clipart/20211118/ourmid/pngtree-gaming-mouse-png-image_4035672.png"),
                ProductoDB(nombre="Silla Gamer", precio=6500, stock=10, imagen_url="https://png.pngtree.com/png-vector/20240709/ourlarge/pngtree-black-gaming-chair-png-image_13050960.png"),
                ProductoDB(nombre="Juego de Destornilladores", precio=350, stock=25, imagen_url="https://i5.walmartimages.com/asr/ca9363dd-14a2-4bd9-8acf-8bb1bdaf5f0d.bc2062a28ff16583ed33232e45575f3a.png?odnHeight=612&odnWidth=612&odnBg=FFFFFF"),
                ProductoDB(nombre="Lámpara LED Taller", precio=450, stock=15, imagen_url="https://w7.pngwing.com/pngs/640/646/png-transparent-headlamp-light-emitting-diode-flashlight-flashlight-white-electronics-headlamp.png"),
                ProductoDB(nombre="Multímetro Digital", precio=680, stock=8, imagen_url="https://png.pngtree.com/png-vector/20240507/ourlarge/pngtree-digital-multimeter-a-on-white-background-png-image_12371373.png"),
                ProductoDB(nombre="Cable HDMI", precio=120, stock=50, imagen_url="https://png.pngtree.com/png-clipart/20250807/original/pngtree-coiled-hdmi-cable-with-male-connectors-at-each-end-isolated-on-png-image_21522812.png")
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
        
        resultados = []
        for pedido in pedidos:
            resultados.append({
                "id": pedido.id,
                "cantidad": pedido.cantidad,
                "total": pedido.total,
                "estado": pedido.estado,
                "producto_id": pedido.producto_id,
                "nombre_cliente": db.query(ClienteDB).filter(ClienteDB.id == pedido.cliente_id).first().nombre
            })
        return resultados
    finally:
        db.close()

@app.get("/")
def home():
    return {"mensaje": "Servidor Local Activo con ngrok"}