"""
Servidor de la plataforma del podoscopio con inicio de sesión.

Dos tipos de acceso:
  Profesional: usuario y contraseña. Registra pacientes, analiza imágenes y guarda exámenes.
  Paciente:    número de documento y clave de acceso de 6 dígitos que le entrega el profesional.
               Solo puede ver sus propios resultados.

El número de documento identifica a la persona, pero no es un secreto, por eso va acompañado de una clave.

Cómo ejecutarlo en Visual Studio Code:
  1. Abre esta carpeta y crea el entorno:
         python -m venv venv
         venv\\Scripts\\activate          (Windows)
         source venv/bin/activate         (Mac o Linux)
  2. Instala las dependencias:
         pip install -r requirements.txt
  3. Crea la primera cuenta de profesional (solo una vez):
         python crear_profesional.py
  4. Ejecuta:
         python app.py
  5. Abre el enlace que aparece en la terminal (Ctrl y clic).
"""

import json
import os
import re
import secrets
import sqlite3
import threading
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (Flask, jsonify, redirect, render_template, request,
                   send_from_directory, session)
from werkzeug.security import check_password_hash, generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.environ.get("PODOSCOPIO_DATOS", os.path.join(BASE, "datos"))
os.makedirs(DATOS, exist_ok=True)
RUTA_BD = os.path.join(DATOS, "podoscopio.db")
CARPETA_PAGINA = os.path.join(BASE, "docs")
HOST = os.environ.get("PODOSCOPIO_HOST", "127.0.0.1")
PUERTO = int(os.environ.get("PODOSCOPIO_PUERTO", "5000"))

MAX_FALLOS = 5          # intentos fallidos antes de bloquear
BLOQUEO_SEGUNDOS = 300  # duración del bloqueo

DOCUMENTO_VALIDO = re.compile(r"^[A-Z0-9]{4,20}$")
CLAVES_PIE = ("longitud_cm", "antepie_cm", "arco_cm", "talon_cm",
              "area_cm2", "csi", "staheli", "indice_arco")


def obtener_clave_secreta():
    """Clave que firma las cookies de sesión. Se guarda en datos/secret.key."""
    desde_entorno = os.environ.get("PODOSCOPIO_SECRET")
    if desde_entorno:
        return desde_entorno
    ruta = os.path.join(DATOS, "secret.key")
    if not os.path.exists(ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(secrets.token_hex(32))
    with open(ruta, encoding="utf-8") as f:
        return f.read().strip()


app = Flask(__name__, static_folder=None)
app.secret_key = obtener_clave_secreta()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("PODOSCOPIO_HTTPS") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=200_000,
)


# ----------------------------------------------------------------------
# Base de datos
# ----------------------------------------------------------------------
def bd(sql, params=(), uno=False, escribir=False):
    con = sqlite3.connect(RUTA_BD)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        cur = con.execute(sql, params)
        if escribir:
            con.commit()
            return cur.lastrowid
        return cur.fetchone() if uno else cur.fetchall()
    finally:
        con.close()


def iniciar_bd():
    con = sqlite3.connect(RUTA_BD)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS profesionales (
            id INTEGER PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            clave_hash TEXT NOT NULL,
            creado TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY,
            documento TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            edad INTEGER,
            sexo TEXT,
            peso REAL,
            estatura REAL,
            clave_hash TEXT NOT NULL,
            creado TEXT NOT NULL,
            creado_por INTEGER REFERENCES profesionales(id)
        );
        CREATE TABLE IF NOT EXISTS examenes (
            id INTEGER PRIMARY KEY,
            paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
            profesional_id INTEGER NOT NULL REFERENCES profesionales(id),
            fecha TEXT NOT NULL,
            escala REAL,
            calibrada INTEGER,
            metricas TEXT NOT NULL,
            observaciones TEXT
        );
    """)
    con.commit()
    con.close()


iniciar_bd()


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalizar_documento(texto):
    """Quita puntos, guiones y espacios: 1.234.567-890 queda como 1234567890."""
    return re.sub(r"[^A-Za-z0-9]", "", str(texto or "")).upper()


def generar_clave_paciente():
    return f"{secrets.randbelow(10**6):06d}"


def paciente_publico(fila):
    return {k: fila[k] for k in ("documento", "nombre", "edad", "sexo", "peso", "estatura")}


# ----------------------------------------------------------------------
# Protección contra adivinar claves (varios intentos fallidos bloquean la cuenta unos minutos)
# ----------------------------------------------------------------------
_fallos = {}
_cerrojo = threading.Lock()


def segundos_de_bloqueo(llave):
    with _cerrojo:
        _, hasta = _fallos.get(llave, (0, 0))
    return max(0, int(hasta - time.time()))


def registrar_fallo(llave):
    ahora_s = time.time()
    with _cerrojo:
        n, hasta = _fallos.get(llave, (0, 0))
        if hasta and hasta <= ahora_s:
            n = 0
        n += 1
        _fallos[llave] = (n, ahora_s + BLOQUEO_SEGUNDOS if n >= MAX_FALLOS else 0)


def limpiar_fallos(llave):
    with _cerrojo:
        _fallos.pop(llave, None)


CLAVE_FALSA = generate_password_hash("clave-que-no-existe")


# ----------------------------------------------------------------------
# Control de acceso
# ----------------------------------------------------------------------
def requiere(rol):
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            if session.get("rol") != rol:
                if request.path.startswith("/api/"):
                    return jsonify(error="No autorizado"), 401
                return redirect("/login")
            return funcion(*args, **kwargs)
        return envoltura
    return decorador


@app.after_request
def cabeceras(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    if request.path.startswith(("/api/", "/app", "/paciente")):
        resp.headers["Cache-Control"] = "no-store"
    return resp


# ----------------------------------------------------------------------
# Páginas
# ----------------------------------------------------------------------
@app.get("/")
def inicio():
    if session.get("rol") == "profesional":
        return redirect("/app")
    if session.get("rol") == "paciente":
        return redirect("/paciente")
    return redirect("/login")


@app.get("/login")
def login():
    if session.get("rol"):
        return redirect("/")
    return render_template("login.html")


@app.get("/app")
@requiere("profesional")
def aplicacion():
    return send_from_directory(CARPETA_PAGINA, "index.html")


@app.get("/paciente")
@requiere("paciente")
def portal_paciente():
    return render_template("paciente.html")


# ----------------------------------------------------------------------
# Sesión
# ----------------------------------------------------------------------
@app.post("/api/login")
def api_login():
    datos = request.get_json(silent=True) or {}
    tipo = datos.get("tipo")
    identificador = str(datos.get("identificador", "")).strip()
    clave = str(datos.get("clave", ""))
    if tipo not in ("paciente", "profesional") or not identificador or not clave:
        return jsonify(error="Completa los dos campos."), 400

    if tipo == "paciente":
        identificador = normalizar_documento(identificador)
        fila = bd("SELECT * FROM pacientes WHERE documento = ?", (identificador,), uno=True)
        mensaje = "Documento o clave incorrectos."
    else:
        identificador = identificador.lower()
        fila = bd("SELECT * FROM profesionales WHERE usuario = ?", (identificador,), uno=True)
        mensaje = "Usuario o contraseña incorrectos."

    llave = f"{tipo}:{identificador}"
    espera = segundos_de_bloqueo(llave)
    if espera:
        minutos = espera // 60 + 1
        return jsonify(error=f"Demasiados intentos. Espera {minutos} minuto(s) e inténtalo de nuevo."), 429

    valida = check_password_hash(fila["clave_hash"] if fila else CLAVE_FALSA, clave) and fila is not None
    if not valida:
        registrar_fallo(llave)
        return jsonify(error=mensaje), 401

    limpiar_fallos(llave)
    session.clear()
    session.permanent = True
    session.update(rol=tipo, uid=fila["id"], nombre=fila["nombre"])
    return jsonify(rol=tipo, destino="/app" if tipo == "profesional" else "/paciente")


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/yo")
def api_yo():
    if not session.get("rol"):
        return jsonify(error="No autorizado"), 401
    return jsonify(rol=session["rol"], nombre=session["nombre"])


# ----------------------------------------------------------------------
# Pacientes (solo profesionales)
# ----------------------------------------------------------------------
def leer_datos_paciente(datos):
    """Valida los datos del paciente. Devuelve (diccionario, error)."""
    nombre = str(datos.get("nombre", "")).strip()
    if len(nombre) < 3 or len(nombre) > 120:
        return None, "Escribe el nombre completo del paciente."

    def numero(clave, minimo, maximo, entero=False):
        valor = datos.get(clave)
        if valor in (None, ""):
            return None
        try:
            valor = int(valor) if entero else float(valor)
        except (TypeError, ValueError):
            raise ValueError(f"El dato {clave} no es válido.")
        if not (minimo <= valor <= maximo):
            raise ValueError(f"El dato {clave} está fuera de rango.")
        return valor

    try:
        edad = numero("edad", 0, 120, entero=True)
        peso = numero("peso", 1, 400)
        estatura = numero("estatura", 30, 250)
    except ValueError as e:
        return None, str(e)
    sexo = str(datos.get("sexo", "")).strip()
    if sexo not in ("", "Femenino", "Masculino", "Otro"):
        return None, "El dato sexo no es válido."
    return dict(nombre=nombre, edad=edad, sexo=sexo, peso=peso, estatura=estatura), None


@app.get("/api/pacientes/<documento>")
@requiere("profesional")
def api_buscar_paciente(documento):
    fila = bd("SELECT * FROM pacientes WHERE documento = ?", (normalizar_documento(documento),), uno=True)
    if not fila:
        return jsonify(error="No existe un paciente con ese documento."), 404
    return jsonify(paciente_publico(fila))


@app.post("/api/pacientes")
@requiere("profesional")
def api_crear_paciente():
    datos = request.get_json(silent=True) or {}
    documento = normalizar_documento(datos.get("documento"))
    if not DOCUMENTO_VALIDO.match(documento):
        return jsonify(error="El número de documento debe tener entre 4 y 20 caracteres."), 400
    campos, error = leer_datos_paciente(datos)
    if error:
        return jsonify(error=error), 400
    if bd("SELECT id FROM pacientes WHERE documento = ?", (documento,), uno=True):
        return jsonify(error="Ya existe un paciente con ese documento."), 409

    clave = generar_clave_paciente()
    bd("""INSERT INTO pacientes (documento, nombre, edad, sexo, peso, estatura, clave_hash, creado, creado_por)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
       (documento, campos["nombre"], campos["edad"], campos["sexo"], campos["peso"], campos["estatura"],
        generate_password_hash(clave), ahora(), session["uid"]), escribir=True)
    fila = bd("SELECT * FROM pacientes WHERE documento = ?", (documento,), uno=True)
    return jsonify(paciente=paciente_publico(fila), clave=clave), 201


@app.post("/api/pacientes/<documento>/clave")
@requiere("profesional")
def api_nueva_clave(documento):
    documento = normalizar_documento(documento)
    if not bd("SELECT id FROM pacientes WHERE documento = ?", (documento,), uno=True):
        return jsonify(error="No existe un paciente con ese documento."), 404
    clave = generar_clave_paciente()
    bd("UPDATE pacientes SET clave_hash = ? WHERE documento = ?",
       (generate_password_hash(clave), documento), escribir=True)
    limpiar_fallos(f"paciente:{documento}")
    return jsonify(clave=clave)


# ----------------------------------------------------------------------
# Exámenes
# ----------------------------------------------------------------------
def limpiar_pie(pie):
    """Conserva solo los números esperados de un pie. Devuelve None si algo no es válido."""
    if not isinstance(pie, dict):
        return None
    salida = {}
    for clave in CLAVES_PIE:
        valor = pie.get(clave)
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor != valor or abs(valor) > 1e6:
            return None
        salida[clave] = round(float(valor), 3)
    clasificacion = pie.get("clasificacion")
    salida["clasificacion"] = clasificacion if clasificacion in ("cavo", "normal", "plano") else None
    return salida


def examen_publico(fila):
    return {
        "id": fila["id"],
        "fecha": fila["fecha"],
        "escala": fila["escala"],
        "calibrada": bool(fila["calibrada"]),
        "metricas": json.loads(fila["metricas"]),
        "observaciones": fila["observaciones"] or "",
    }


@app.post("/api/examenes")
@requiere("profesional")
def api_guardar_examen():
    datos = request.get_json(silent=True) or {}
    documento = normalizar_documento(datos.get("documento"))
    paciente = bd("SELECT id FROM pacientes WHERE documento = ?", (documento,), uno=True)
    if not paciente:
        return jsonify(error="Registra primero al paciente con su número de documento."), 404

    metricas = datos.get("metricas") or {}
    derecho = limpiar_pie(metricas.get("derecho"))
    izquierdo = limpiar_pie(metricas.get("izquierdo"))
    if not derecho and not izquierdo:
        return jsonify(error="No hay métricas válidas para guardar."), 400

    escala = datos.get("escala")
    escala = float(escala) if isinstance(escala, (int, float)) and not isinstance(escala, bool) and 0 < escala < 1e5 else None
    observaciones = str(datos.get("observaciones", ""))[:2000]
    nuevo = bd("""INSERT INTO examenes (paciente_id, profesional_id, fecha, escala, calibrada, metricas, observaciones)
                  VALUES (?, ?, ?, ?, ?, ?, ?)""",
               (paciente["id"], session["uid"], ahora(), escala, 1 if datos.get("calibrada") else 0,
                json.dumps({"derecho": derecho, "izquierdo": izquierdo}), observaciones), escribir=True)
    return jsonify(id=nuevo), 201


@app.get("/api/pacientes/<documento>/examenes")
@requiere("profesional")
def api_examenes_de_paciente(documento):
    paciente = bd("SELECT id FROM pacientes WHERE documento = ?", (normalizar_documento(documento),), uno=True)
    if not paciente:
        return jsonify(error="No existe un paciente con ese documento."), 404
    filas = bd("SELECT * FROM examenes WHERE paciente_id = ? ORDER BY fecha DESC, id DESC", (paciente["id"],))
    return jsonify(examenes=[examen_publico(f) for f in filas])


@app.get("/api/mis-examenes")
@requiere("paciente")
def api_mis_examenes():
    filas = bd("SELECT * FROM examenes WHERE paciente_id = ? ORDER BY fecha DESC, id DESC", (session["uid"],))
    return jsonify(nombre=session["nombre"], examenes=[examen_publico(f) for f in filas])


if __name__ == "__main__":
    if not bd("SELECT id FROM profesionales LIMIT 1", uno=True):
        print("\nAún no hay ninguna cuenta de profesional. Créala con:  python crear_profesional.py\n")
    url = f"http://localhost:{PUERTO}"
    print("=" * 62)
    print("Plataforma del podoscopio lista")
    print(f"Abre este enlace en el navegador: {url}")
    print("Para detener el servidor presiona Ctrl+C")
    print("=" * 62)
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(host=HOST, port=PUERTO, debug=False)
