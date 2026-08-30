
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

pd.set_option("display.max_columns", None)

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
load_dotenv()  # Carga las variables definidas en el archivo .env

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "TT")
DB_SSLMODE = os.getenv("DB_SSLMODE", "disable")
DB_PG_OPTIONS = os.getenv("DB_PG_OPTIONS", "-c lc_messages=C")
RUTA_CSV = "dataset_sucio_tienda_tecnologia.csv"


# ---------------------------------------------------------------------------
# Funciones de limpieza
# ---------------------------------------------------------------------------
def normalizar_texto(serie: pd.Series, correcciones: dict | None = None) -> pd.Series:
    serie_limpia = serie.astype(str).str.strip()
    clave = serie_limpia.str.upper()
    if correcciones:
        return clave.map(correcciones).fillna(serie_limpia.str.title())
    return serie_limpia.str.title()


def quitar_simbolos_dinero(serie: pd.Series) -> pd.Series:
    return (
        serie.astype(str)
        .str.replace(r"[\$\.,\s]", "", regex=True)
        .astype(float)
    )


def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

# --- Duplicados por id_venta: conservar la fila con más información ---
    df = df.replace(r'^\s*$', pd.NA, regex=True)
    df["nulos"] = df.isna().sum(axis=1)
    df = df.sort_values("nulos").drop_duplicates(subset=["id_venta"], keep="first")
    df = df.drop(columns=["nulos"])
    df["id_num"] = df["id_venta"].str.extract(r'(\d+)').astype(int)
    df = df.sort_values(by="id_num").drop(columns=["id_num"]).reset_index(drop=True)

    # --- Texto libre: nombre y correo ---
    df["cliente_nombre"] = df["cliente_nombre"].astype(str).str.strip()
    df["cliente_nombre"] = df["cliente_nombre"].replace(["nan", "none", "null"], pd.NA).fillna("NoRegistrado")
    df["cliente_email"] = df["cliente_email"].astype(str).str.strip().str.lower()
    df["cliente_email"] = df["cliente_email"].replace({"nan": pd.NA}).fillna("NoRegistrado")

    # --- Categorias simples (sin problema de tildes, solo mayus/minus y espacios) ---
    
    correccion_tipo_cliente = {
        "PARTICULAR": "Particular",
        "EMPRESA": "Empresa",
    }
    df["cliente_tipo"] = normalizar_texto(df["cliente_tipo"], correccion_tipo_cliente)
    df["cliente_tipo"] = df["cliente_tipo"].replace(["Nan", "None", "Null"], pd.NA).fillna("NoRegistrado")
    df["metodo_pago"] = normalizar_texto(df["metodo_pago"])

    # --- Categorias con inconsistencia de tildes: se corrigen con diccionario ---
    correccion_vendedor = {
        "ANDRES DIAZ": "Andrés Díaz",
        "ANDRÉS DÍAZ": "Andrés Díaz",
        "MARIA LOPEZ": "Maria Lopez",
        "CARLOS PEREZ": "Carlos Perez",
    }
    df["vendedor"] = normalizar_texto(df["vendedor"], correccion_vendedor)
    correccion_ciudad = {
        "BOGOTA": "Bogotá",
        "CARTAGENA": "Cartagena",
        "BARRANQUILLA": "Barranquilla",
        "SANTA MARTA": "Santa Marta",
        "MONTERIA": "Montería",
    }
    df["ciudad"] = normalizar_texto(df["ciudad"], correccion_ciudad)

    correccion_categoria = {
        "PERIFERICOS": "Periféricos",
        "COMPUTADORES": "Computadores",
        "MONITORES": "Monitores",
        "AUDIO": "Audio",
        "ALMACENAMIENTO": "Almacenamiento",
        "REDES": "Redes",
        "CELULARES": "Celulares",
        "VIDEOJUEGOS": "Videojuegos",
        "IMPRESORAS": "Impresoras",
    }
    
    diccionario_categorias = {
        "AirPods 2" : "Audio",
        "Audífonos JBL Tune 760": "Audio",
        "Audífonos Sony WH-CH520" : "Audio",
        "Impresora Epson EcoTank": "Impresoras",
        "Impresora HP Smart Tank": "Impresoras",
        "Laptop Asus Vivobook" : "Computadores",
        "Laptop HP 15": "Computadores",
        "Laptop Lenovo IdeaPad": "Computadores",
        "MacBook Air M1": "Computadores",
        "MacBook Air M2": "Computadores",
        "Monitor LG 27": "Monitores",
        "Monitor Samsung 24" : "Monitores",
        "Monitor Samsung 27" : "Monitores",
        "Mouse Logitech G203": "Periféricos",
        "Mouse Logitech MX Master": "Periféricos",
        "PlayStation 5 Slim" : "Videojuegos",
        "Nintendo Switch OLED" : "Videojuegos",
        "Router TP-Link AX1500": "Redes",
        "Router TP-Link AX3000": "Redes",
        "SSD Kingston 1TB" : "Almacenamiento",
        "SSD Kingston 480GB" : "Almacenamiento",
        "SSD Samsung 1TB" : "Almacenamiento",
        "Samsung Galaxy A55" : "Celulares",
        "Teclado Mecánico HyperX": "Periféricos",
        "Teclado Redragon K552": "Periféricos",
        "Webcam Logitech C920": "Periféricos",
        "Xbox Series S": "Videojuegos",
        "iPhone 13" : "Celulares"
    }
    df["categoria_producto"] = normalizar_texto(df["categoria_producto"], correccion_categoria)
    df["categoria_producto"] = df['producto'].map(diccionario_categorias).fillna(df["categoria_producto"])
    
    df["producto"] = df["producto"].astype(str).str.strip()
    df["region"] = normalizar_texto(df["region"])

    # --- Numeros ---
    df["cantidad"] = df["cantidad"].astype(str).str.strip().astype(int)

    columna_limpia= (
        df["descuento_pct"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.strip()
        .astype(float))
    
    df["descuento_pct"] = np.where(columna_limpia > 1, columna_limpia / 100.0, columna_limpia)

    df["precio_unitario"] = quitar_simbolos_dinero(df["precio_unitario"])
    df["total_venta"] = quitar_simbolos_dinero(df["total_venta"])

    # --- Fechas: todo el archivo usa dd/mm/aaaa, se fija el formato para evitar ambiguedad ---
    df["fecha_venta"] = pd.to_datetime(df["fecha_venta"], format="mixed", errors="coerce")
    fechas_invalidas = df["fecha_venta"].isna().sum()
    if fechas_invalidas:
        print(f"Aviso: {fechas_invalidas} fechas no se pudieron interpretar y quedaron como NaT.")

    # --- Validacion cruzada: total_venta debe ser ~ precio * cantidad * (1 - descuento) ---
    total_calculado = df["precio_unitario"] * df["cantidad"] * (1 - df["descuento_pct"])
    diferencia = (df["total_venta"] - total_calculado).abs()
    inconsistentes = df[diferencia > 1]  # margen de 1 peso por redondeo
    if not inconsistentes.empty:
        print(f"Aviso: {len(inconsistentes)} filas con total_venta que no cuadra con precio*cantidad*(1-descuento):")
        print(inconsistentes[["id_venta", "precio_unitario", "cantidad", "descuento_pct", "total_venta"]].to_string(index=False))

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Modelo dimensional
# ---------------------------------------------------------------------------
def construir_modelo_dimensional(df: pd.DataFrame):
    dim_cliente = (
        df[["cliente_nombre", "cliente_email", "cliente_tipo"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_cliente.insert(0, "id_cliente", dim_cliente.index + 1)

    dim_producto = (
        df[["producto", "categoria_producto", "precio_unitario"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_producto.insert(0, "id_producto", dim_producto.index + 1)

    dim_vendedor = df[["vendedor"]].drop_duplicates().reset_index(drop=True)
    dim_vendedor.insert(0, "id_vendedor", dim_vendedor.index + 1)

    dim_ubicacion = df[["ciudad", "region"]].drop_duplicates().reset_index(drop=True)
    dim_ubicacion.insert(0, "id_ubicacion", dim_ubicacion.index + 1)

    ft_ventas = (
        df.merge(dim_cliente, on=["cliente_nombre", "cliente_email", "cliente_tipo"])
        .merge(dim_producto, on=["producto", "categoria_producto", "precio_unitario"])
        .merge(dim_vendedor, on=["vendedor"])
        .merge(dim_ubicacion, on=["ciudad", "region"])
        [[
            "id_venta", "id_cliente", "id_producto", "id_vendedor", "id_ubicacion",
            "fecha_venta", "cantidad", "descuento_pct", "metodo_pago", "total_venta",
        ]]
    )

    return dim_cliente, dim_producto, dim_vendedor, dim_ubicacion, ft_ventas


# ---------------------------------------------------------------------------
# Carga a PostgreSQL
# ---------------------------------------------------------------------------
def cargar_a_postgres(dim_cliente, dim_producto, dim_vendedor, dim_ubicacion, ft_ventas, engine):
    with engine.begin() as conn:
        conn.execute(text(
            "DROP TABLE IF EXISTS ft_ventas, dim_cliente, dim_producto, dim_vendedor, dim_ubicacion CASCADE;"
        ))

    dim_cliente.to_sql("dim_cliente", engine, if_exists="replace", index=False)
    dim_producto.to_sql("dim_producto", engine, if_exists="replace", index=False)
    dim_vendedor.to_sql("dim_vendedor", engine, if_exists="replace", index=False)
    dim_ubicacion.to_sql("dim_ubicacion", engine, if_exists="replace", index=False)
    ft_ventas.to_sql("ft_ventas", engine, if_exists="replace", index=False)

    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE dim_cliente ADD PRIMARY KEY (id_cliente);
            ALTER TABLE dim_producto ADD PRIMARY KEY (id_producto);
            ALTER TABLE dim_vendedor ADD PRIMARY KEY (id_vendedor);
            ALTER TABLE dim_ubicacion ADD PRIMARY KEY (id_ubicacion);
        """))

    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE ft_ventas
                ADD CONSTRAINT fk_cliente FOREIGN KEY (id_cliente) REFERENCES dim_cliente(id_cliente),
                ADD CONSTRAINT fk_producto FOREIGN KEY (id_producto) REFERENCES dim_producto(id_producto),
                ADD CONSTRAINT fk_vendedor FOREIGN KEY (id_vendedor) REFERENCES dim_vendedor(id_vendedor),
                ADD CONSTRAINT fk_ubicacion FOREIGN KEY (id_ubicacion) REFERENCES dim_ubicacion(id_ubicacion);
        """))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    df_crudo = pd.read_csv(RUTA_CSV)
    print(f"Filas leidas del CSV: {len(df_crudo)}")

    df = limpiar_datos(df_crudo)

    dim_cliente, dim_producto, dim_vendedor, dim_ubicacion, ft_ventas = construir_modelo_dimensional(df)
    print(f"dim_cliente: {len(dim_cliente)} filas")
    print(f"dim_producto: {len(dim_producto)} filas")
    print(f"dim_vendedor: {len(dim_vendedor)} filas")
    print(f"dim_ubicacion: {len(dim_ubicacion)} filas")
    print(f"ft_ventas: {len(ft_ventas)} filas")

    connect_args = {"sslmode": DB_SSLMODE}
    if DB_PG_OPTIONS:
        connect_args["options"] = DB_PG_OPTIONS

    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        connect_args=connect_args,
    )
    cargar_a_postgres(dim_cliente, dim_producto, dim_vendedor, dim_ubicacion, ft_ventas, engine)


    verificacion = pd.read_sql("SELECT * FROM ft_ventas LIMIT 5", engine)
    if verificacion.empty:
        print("No se encontraron registros en la tabla ft_ventas.")
    else:
        print("Se encontraron registros en la tabla ft_ventas.")
    
    df.to_csv("dataset_limpio_tienda_tecnologia.csv", index=False)


if __name__ == "__main__":
    main()
