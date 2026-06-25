import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import plotly.express as px

DB = "provicheck.db"
ARCHIVO_EXCEL = "data/PROVICHECK_Base_Datos.xlsx"

# =====================
# BASE DE DATOS
# =====================
def conn():
    return sqlite3.connect(DB, check_same_thread=False)

def sql(query, params=()):
    c = conn()
    cur = c.cursor()
    cur.execute(query, params)
    c.commit()
    c.close()

def tabla(nombre):
    c = conn()
    df = pd.read_sql(f"SELECT * FROM {nombre}", c)
    c.close()
    return df

def crear_bd():
    c = conn()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        clave TEXT,
        nombre TEXT,
        perfil TEXT,
        estado TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS laboratorios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE,
        nombre TEXT,
        responsable TEXT,
        estado TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS equipos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE,
        nombre TEXT,
        laboratorio TEXT,
        area TEXT,
        marca TEXT,
        modelo TEXT,
        serial TEXT,
        responsable TEXT,
        criticidad TEXT,
        estado TEXT,
        ultima_calibracion TEXT,
        proxima_calibracion TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS configuracion_checkeo(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_equipo TEXT,
        frecuencia TEXT,
        punto_evaluacion TEXT,
        variable TEXT,
        unidad TEXT,
        limite_inferior REAL,
        limite_superior REAL,
        obligatorio TEXT,
        estado TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS registros_checkeo(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        usuario TEXT,
        codigo_equipo TEXT,
        laboratorio TEXT,
        resultado_general TEXT,
        observacion TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS detalle_checkeo(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_registro INTEGER,
        variable TEXT,
        punto_evaluacion TEXT,
        valor REAL,
        limite_inferior REAL,
        limite_superior REAL,
        cumple TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bitacora(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        codigo_equipo TEXT,
        laboratorio TEXT,
        tipo_evento TEXT,
        descripcion TEXT,
        responsable TEXT,
        estado TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS auditoria(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        usuario TEXT,
        accion TEXT,
        detalle TEXT
    )
    """)

    c.commit()
    c.close()

def auditar(usuario, accion, detalle):
    sql("""
    INSERT INTO auditoria(fecha, usuario, accion, detalle)
    VALUES (?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, accion, detalle))

def datos_iniciales():
    if tabla("usuarios").empty:
        sql("INSERT OR IGNORE INTO usuarios(usuario, clave, nombre, perfil, estado) VALUES(?,?,?,?,?)",
            ("admin", "1234", "Administrador PROVICHECK", "Administrador", "Activo"))
        sql("INSERT OR IGNORE INTO usuarios(usuario, clave, nombre, perfil, estado) VALUES(?,?,?,?,?)",
            ("analista", "1234", "Analista Laboratorio", "Analista", "Activo"))

    if tabla("laboratorios").empty:
        labs = [
            ("LAB01", "Caña", "Responsable Caña", "Activo"),
            ("LAB02", "Fábrica", "Responsable Fábrica", "Activo"),
            ("LAB03", "Microbiología", "Responsable Microbiología", "Activo"),
            ("LAB04", "Insumos", "Responsable Insumos", "Activo"),
            ("LAB05", "Combustibles", "Responsable Combustibles", "Activo")
        ]
        for x in labs:
            sql("INSERT OR IGNORE INTO laboratorios(codigo,nombre,responsable,estado) VALUES(?,?,?,?)", x)

    if tabla("equipos").empty:
        equipos = [
            ("63065", "Balanza Analítica", "Insumos", "Metrología", "Mettler Toledo", "XS204", "S/N", "Analista", "Alta", "Activo", "2026-01-01", "2027-01-01"),
            ("63469", "Espectrofotómetro UV5", "Insumos", "Fisicoquímico", "Mettler Toledo", "UV5", "S/N", "Analista", "Alta", "Activo", "2026-01-01", "2027-01-01"),
            ("634003", "pH Metro Seven Compact", "Insumos", "Fisicoquímico", "Mettler Toledo", "Seven Compact", "S/N", "Analista", "Alta", "Activo", "2026-01-01", "2027-01-01")
        ]
        for e in equipos:
            sql("""
            INSERT OR IGNORE INTO equipos(codigo,nombre,laboratorio,area,marca,modelo,serial,responsable,criticidad,estado,ultima_calibracion,proxima_calibracion)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, e)

    if tabla("configuracion_checkeo").empty:
        configs = [
            ("63065","Diaria","1 g","Pesa patrón 1 g","g",0.9998,1.0002,"Sí","Activo"),
            ("63065","Diaria","10 g","Pesa patrón 10 g","g",9.9998,10.0002,"Sí","Activo"),
            ("63065","Diaria","100 g","Pesa patrón 100 g","g",99.9995,100.0005,"Sí","Activo"),

            ("634003","Diaria","Buffer 4","Lectura pH 4","pH",3.95,4.05,"Sí","Activo"),
            ("634003","Diaria","Buffer 7","Lectura pH 7","pH",6.95,7.05,"Sí","Activo"),
            ("634003","Diaria","Buffer 10","Lectura pH 10","pH",9.95,10.05,"Sí","Activo"),

            ("63469","Semanal","Blanco","Absorbancia blanco","Abs",-0.005,0.005,"Sí","Activo"),
            ("63469","Semanal","Patrón","Absorbancia patrón","Abs",0.498,0.502,"Sí","Activo")
        ]
        for cfg in configs:
            sql("""
            INSERT INTO configuracion_checkeo(codigo_equipo,frecuencia,punto_evaluacion,variable,unidad,limite_inferior,limite_superior,obligatorio,estado)
            VALUES(?,?,?,?,?,?,?,?,?)
            """, cfg)

crear_bd()
datos_iniciales()

# =====================
# INTERFAZ
# =====================
st.set_page_config(page_title="PROVICHECK", layout="wide")
st.title("✅ PROVICHECK")
st.caption("Sistema Inteligente de Verificación y Trazabilidad de Equipos de Laboratorio")

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.subheader("Ingreso al sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")

    if st.button("Ingresar"):
        c = conn()
        df = pd.read_sql("SELECT * FROM usuarios WHERE usuario=? AND clave=? AND estado='Activo'", c, params=(u,p))
        c.close()

        if not df.empty:
            st.session_state.login = True
            st.session_state.usuario = df.iloc[0]["usuario"]
            st.session_state.nombre = df.iloc[0]["nombre"]
            st.session_state.perfil = df.iloc[0]["perfil"]
            st.rerun()
        else:
            st.error("Usuario o clave incorrectos")

    st.info("Usuarios iniciales: admin / 1234  |  analista / 1234")
    st.stop()

usuario = st.session_state.usuario
perfil = st.session_state.perfil

st.sidebar.success(st.session_state.nombre)
st.sidebar.write(f"Perfil: **{perfil}**")

menu = st.sidebar.radio("Menú", [
    "Inicio",
    "Equipos",
    "Configurar chequeos",
    "Realizar chequeo",
    "Bitácora por equipo",
    "Dashboard",
    "Auditoría",
    "Administración"
])

if st.sidebar.button("Cerrar sesión"):
    st.session_state.login = False
    st.rerun()

# =====================
# INICIO
# =====================
if menu == "Inicio":
    equipos = tabla("equipos")
    registros = tabla("registros_checkeo")
    bit = tabla("bitacora")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Equipos", len(equipos))
    c2.metric("Activos", len(equipos[equipos.estado=="Activo"]))
    c3.metric("Fuera servicio", len(equipos[equipos.estado=="Fuera de servicio"]))
    c4.metric("Chequeos", len(registros))

    st.subheader("Equipos por laboratorio")
    st.dataframe(equipos, use_container_width=True)

# =====================
# EQUIPOS
# =====================
elif menu == "Equipos":
    st.subheader("Maestro de equipos")
    st.dataframe(tabla("equipos"), use_container_width=True)

    if perfil == "Administrador":
        st.markdown("### Crear nuevo equipo")
        labs = tabla("laboratorios")["nombre"].tolist()

        with st.form("nuevo_equipo"):
            codigo = st.text_input("Código")
            nombre = st.text_input("Nombre")
            laboratorio = st.selectbox("Laboratorio", labs)
            area = st.text_input("Área")
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            serial = st.text_input("Serial")
            responsable = st.text_input("Responsable")
            criticidad = st.selectbox("Criticidad", ["Baja","Media","Alta"])
            estado = st.selectbox("Estado", ["Activo","Inactivo","Fuera de servicio"])
            ultima = st.date_input("Última calibración")
            proxima = st.date_input("Próxima calibración")
            guardar = st.form_submit_button("Guardar")

        if guardar:
            try:
                sql("""
                INSERT INTO equipos(codigo,nombre,laboratorio,area,marca,modelo,serial,responsable,criticidad,estado,ultima_calibracion,proxima_calibracion)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """, (codigo,nombre,laboratorio,area,marca,modelo,serial,responsable,criticidad,estado,str(ultima),str(proxima)))
                auditar(usuario, "Crear equipo", f"{codigo} - {nombre}")
                st.success("Equipo creado.")
                st.rerun()
            except Exception as e:
                st.error("No se pudo crear. Puede que el código ya exista.")
    else:
        st.warning("Solo administrador puede crear equipos.")

# =====================
# CONFIGURAR CHEQUEOS
# =====================
elif menu == "Configurar chequeos":
    st.subheader("Configuración de chequeos")
    st.dataframe(tabla("configuracion_checkeo"), use_container_width=True)

    if perfil == "Administrador":
        equipos = tabla("equipos")
        opciones = equipos["codigo"] + " - " + equipos["nombre"]

        with st.form("config"):
            sel = st.selectbox("Equipo", opciones)
            codigo = sel.split(" - ")[0]
            frecuencia = st.selectbox("Frecuencia", ["Diaria","Semanal","Mensual","Trimestral","Semestral","Anual"])
            punto = st.text_input("Punto de evaluación")
            variable = st.text_input("Variable")
            unidad = st.text_input("Unidad")
            li = st.number_input("Límite inferior", format="%.6f")
            ls = st.number_input("Límite superior", format="%.6f")
            obligatorio = st.selectbox("Obligatorio", ["Sí","No"])
            guardar = st.form_submit_button("Guardar variable")

        if guardar:
            sql("""
            INSERT INTO configuracion_checkeo(codigo_equipo,frecuencia,punto_evaluacion,variable,unidad,limite_inferior,limite_superior,obligatorio,estado)
            VALUES(?,?,?,?,?,?,?,?,?)
            """, (codigo,frecuencia,punto,variable,unidad,li,ls,obligatorio,"Activo"))
            auditar(usuario, "Crear variable chequeo", f"{codigo} - {variable}")
            st.success("Variable creada.")
            st.rerun()
    else:
        st.warning("Solo administrador puede configurar chequeos.")

# =====================
# REALIZAR CHEQUEO
# =====================
elif menu == "Realizar chequeo":
    st.subheader("Realizar chequeo")

    equipos = tabla("equipos")
    activos = equipos[equipos.estado=="Activo"]

    if activos.empty:
        st.warning("No hay equipos activos.")
        st.stop()

    sel = st.selectbox("Equipo", activos["codigo"] + " - " + activos["nombre"])
    codigo = sel.split(" - ")[0]
    eq = activos[activos.codigo==codigo].iloc[0]

    st.info(f"{eq['nombre']} | {eq['laboratorio']} | {eq['marca']} {eq['modelo']}")

    cfg = tabla("configuracion_checkeo")
    cfg = cfg[(cfg.codigo_equipo==codigo) & (cfg.estado=="Activo")]

    if cfg.empty:
        st.warning("Este equipo no tiene checklist configurado.")
        st.stop()

    resultados = []

    with st.form("chequeo"):
        for _, r in cfg.iterrows():
            valor = st.number_input(
                f"{r['punto_evaluacion']} - {r['variable']} ({r['unidad']}) | {r['limite_inferior']} a {r['limite_superior']}",
                format="%.6f",
                key=f"v{r['id']}"
            )
            cumple = "Sí" if r["limite_inferior"] <= valor <= r["limite_superior"] else "No"
            resultados.append([r["variable"], r["punto_evaluacion"], valor, r["limite_inferior"], r["limite_superior"], cumple])

        obs = st.text_area("Observaciones")
        guardar = st.form_submit_button("Guardar chequeo")

    if guardar:
        resultado = "Apto" if all(x[5]=="Sí" for x in resultados) else "No Apto"

        c = conn()
        cur = c.cursor()
        cur.execute("""
        INSERT INTO registros_checkeo(fecha,usuario,codigo_equipo,laboratorio,resultado_general,observacion)
        VALUES(?,?,?,?,?,?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, codigo, eq["laboratorio"], resultado, obs))

        rid = cur.lastrowid

        for x in resultados:
            cur.execute("""
            INSERT INTO detalle_checkeo(id_registro,variable,punto_evaluacion,valor,limite_inferior,limite_superior,cumple)
            VALUES(?,?,?,?,?,?,?)
            """, (rid,x[0],x[1],x[2],x[3],x[4],x[5]))

        if resultado == "No Apto":
            cur.execute("UPDATE equipos SET estado='Fuera de servicio' WHERE codigo=?", (codigo,))
            cur.execute("""
            INSERT INTO bitacora(fecha,codigo_equipo,laboratorio,tipo_evento,descripcion,responsable,estado)
            VALUES(?,?,?,?,?,?,?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), codigo, eq["laboratorio"], "Bloqueo automático", "Equipo fuera de tolerancia.", usuario, "Abierto"))

        c.commit()
        c.close()

        auditar(usuario, "Chequeo", f"{codigo} - {resultado}")

        if resultado == "Apto":
            st.success("Chequeo guardado. Equipo APTO.")
        else:
            st.error("Chequeo guardado. Equipo NO APTO y bloqueado.")

# =====================
# BITÁCORA
# =====================
elif menu == "Bitácora por equipo":
    st.subheader("Bitácora individual")

    equipos = tabla("equipos")
    sel = st.selectbox("Equipo", equipos["codigo"] + " - " + equipos["nombre"])
    codigo = sel.split(" - ")[0]
    eq = equipos[equipos.codigo==codigo].iloc[0]

    bit = tabla("bitacora")
    st.dataframe(bit[bit.codigo_equipo==codigo], use_container_width=True)

    with st.form("bit"):
        tipo = st.selectbox("Tipo evento", ["Calibración","Mantenimiento","Limpieza","Reparación","No conformidad","Cambio ubicación","Otro"])
        desc = st.text_area("Descripción")
        estado = st.selectbox("Estado", ["Abierto","En seguimiento","Cerrado"])
        guardar = st.form_submit_button("Guardar novedad")

    if guardar:
        sql("""
        INSERT INTO bitacora(fecha,codigo_equipo,laboratorio,tipo_evento,descripcion,responsable,estado)
        VALUES(?,?,?,?,?,?,?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), codigo, eq["laboratorio"], tipo, desc, usuario, estado))
        auditar(usuario, "Bitácora", f"{codigo} - {tipo}")
        st.success("Novedad registrada.")
        st.rerun()

# =====================
# DASHBOARD
# =====================
elif menu == "Dashboard":
    st.subheader("Dashboard PROVICHECK")

    equipos = tabla("equipos")
    registros = tabla("registros_checkeo")

    c1,c2,c3 = st.columns(3)
    c1.metric("Total equipos", len(equipos))
    c2.metric("Equipos activos", len(equipos[equipos.estado=="Activo"]))
    c3.metric("Equipos bloqueados", len(equipos[equipos.estado=="Fuera de servicio"]))

    fig = px.histogram(equipos, x="laboratorio", color="estado", title="Estado de equipos por laboratorio")
    st.plotly_chart(fig, use_container_width=True)

    if not registros.empty:
        fig2 = px.histogram(registros, x="laboratorio", color="resultado_general", title="Chequeos por laboratorio")
        st.plotly_chart(fig2, use_container_width=True)

# =====================
# AUDITORÍA
# =====================
elif menu == "Auditoría":
    st.subheader("Auditoría de cambios")

    if perfil == "Administrador":
        st.dataframe(tabla("auditoria"), use_container_width=True)
    else:
        st.warning("Solo administrador puede ver auditoría.")

elif menu == "Administración":

    st.subheader("Administración PROVICHECK")

    if perfil != "Administrador":
        st.warning("Solo administradores.")
        st.stop()

    st.info("Importar información desde PROVICHECK_Base_Datos.xlsx")

    if st.button("Importar Base Excel"):

        equipos_excel = pd.read_excel(
            ARCHIVO_EXCEL,
            sheet_name="Equipos"
        )

        equipos_excel.columns = equipos_excel.columns.str.strip()

        conn = sqlite3.connect("data/provicheck.db")
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT,
            laboratorio TEXT,
            area TEXT,
            marca TEXT,
            modelo TEXT,
            serial TEXT,
            responsable TEXT,
            criticidad TEXT,
            estado TEXT,
            ultima_calibracion TEXT,
            proxima_calibracion TEXT
        )
        """)

        cursor.execute("DELETE FROM equipos")

        for _, fila in equipos_excel.iterrows():
            cursor.execute("""
                INSERT INTO equipos (
                    codigo,
                    nombre,
                    laboratorio,
                    area,
                    marca,
                    modelo,
                    serial,
                    responsable,
                    criticidad,
                    estado,
                    ultima_calibracion,
                    proxima_calibracion
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(fila["codigo"]),
                str(fila["nombre"]),
                str(fila["laboratorio"]),
                str(fila["area"]),
                str(fila["marca"]),
                str(fila["modelo"]),
                str(fila["serial"]),
                str(fila["responsable"]),
                str(fila["criticidad"]),
                str(fila["estado"]),
                str(fila["ultima_calibracion"]),
                str(fila["proxima_calibracion"])
            ))

        conn.commit()
        conn.close()

        st.success(f"Importación exitosa. Equipos cargados: {len(equipos_excel)}")
        st.dataframe(equipos_excel)
