"""Imposta email e password dell'admin di base (id=1). Uso: python crea_admin.py"""
import getpass
from werkzeug.security import generate_password_hash
from db import execute

email = input("Email admin: ").strip()
pw = getpass.getpass("Password admin: ")
execute("UPDATE Utente SET email=%s, password_hash=%s WHERE id=1",
        (email, generate_password_hash(pw)))
print("Admin aggiornato.")
