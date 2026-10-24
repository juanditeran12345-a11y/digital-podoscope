"""
Crea (o reinicia la contraseña de) una cuenta de profesional.

Uso normal, con preguntas en la terminal:
    python crear_profesional.py

Las opciones --usuario, --nombre y --clave existen para automatizar pruebas.
En un uso real escribe la contraseña cuando la pida, para que no quede en el historial de la terminal.
"""

import argparse
import getpass
import re
import sys

from werkzeug.security import generate_password_hash

import app as plataforma


def main():
    parser = argparse.ArgumentParser(description="Crear una cuenta de profesional")
    parser.add_argument("--usuario")
    parser.add_argument("--nombre")
    parser.add_argument("--clave")
    args = parser.parse_args()

    usuario = (args.usuario or input("Usuario (sin espacios): ")).strip().lower()
    if not re.fullmatch(r"[a-z0-9._-]{3,30}", usuario):
        sys.exit("El usuario debe tener entre 3 y 30 caracteres: letras, números, punto, guion o guion bajo.")

    existente = plataforma.bd("SELECT id, nombre FROM profesionales WHERE usuario = ?", (usuario,), uno=True)
    nombre = (args.nombre or (existente["nombre"] if existente else input("Nombre completo: "))).strip()
    if len(nombre) < 3:
        sys.exit("Escribe el nombre completo.")

    if args.clave:
        clave = args.clave
    else:
        clave = getpass.getpass("Contraseña (mínimo 10 caracteres): ")
        if clave != getpass.getpass("Repite la contraseña: "):
            sys.exit("Las contraseñas no coinciden.")
    if len(clave) < 10:
        sys.exit("La contraseña debe tener al menos 10 caracteres.")

    clave_hash = generate_password_hash(clave)
    if existente:
        plataforma.bd("UPDATE profesionales SET clave_hash = ?, nombre = ? WHERE usuario = ?",
                      (clave_hash, nombre, usuario), escribir=True)
        plataforma.limpiar_fallos(f"profesional:{usuario}")
        print(f"Contraseña actualizada para {usuario}.")
    else:
        plataforma.bd("INSERT INTO profesionales (usuario, nombre, clave_hash, creado) VALUES (?, ?, ?, ?)",
                      (usuario, nombre, clave_hash, plataforma.ahora()), escribir=True)
        print(f"Cuenta creada. Ya puedes entrar con el usuario {usuario}.")


if __name__ == "__main__":
    main()
