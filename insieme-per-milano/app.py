import os
import uuid
from functools import wraps

import pymysql
from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_from_directory, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, get_conn, query

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cambiami-in-produzione")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

ESTENSIONI = {"jpg", "jpeg", "png", "webp", "mp4", "mov", "webm"}
STATI_SEGNALAZIONE = ["in_revisione", "ricevuta", "in_carico", "inviata_candidati", "rifiutata"]
STATI_UTENTE = ["attivo", "sospeso", "bannato"]


# ---------- utilità ----------
def log(tipo_azione, id_utente=None):
    """Registra un'azione in Log_Tracciabilita; restituisce l'id del log."""
    uid = id_utente or session.get("id_utente")
    if uid:
        return execute(
            "INSERT INTO Log_Tracciabilita (tipo_azione, id_utente) VALUES (%s,%s)",
            (tipo_azione, uid))


def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if "id_utente" not in session:
            flash("Devi accedere per continuare.", "err")
            return redirect(url_for("login"))
        return f(*a, **k)
    return w


def admin_required(f):
    @wraps(f)
    @login_required
    def w(*a, **k):
        if session.get("potere") != "admin":
            abort(403)
        return f(*a, **k)
    return w


@app.context_processor
def inject_user():
    return dict(sessione=session)


# ---------- pagine utente ----------
@app.route("/")
@login_required
def index():
    return redirect(url_for("mie_segnalazioni"))


@app.route("/registrazione", methods=["GET", "POST"])
def registrazione():
    if request.method == "POST":
        f = request.form
        if len(f["password"]) < 8:
            flash("La password deve avere almeno 8 caratteri.", "err")
        else:
            try:
                uid = execute(
                    "INSERT INTO Utente (nome, cognome, email, password_hash, zona)"
                    " VALUES (%s,%s,%s,%s,%s)",
                    (f["nome"].strip(), f["cognome"].strip(),
                     f["email"].strip().lower(),
                     generate_password_hash(f["password"]), f["zona"].strip()))
                log("registrazione", uid)
                flash("Registrazione completata, ora puoi accedere.", "ok")
                return redirect(url_for("login"))
            except pymysql.err.IntegrityError:
                flash("Email già registrata.", "err")
    return render_template("registrazione.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = query("SELECT * FROM Utente WHERE email=%s",
                  (request.form["email"].strip().lower(),), one=True)
        if not u or not check_password_hash(u["password_hash"] or "", request.form["password"]):
            flash("Credenziali errate.", "err")
        elif u["stato"] != "attivo":
            flash(f"Account {u['stato']}: non puoi accedere.", "err")
        else:
            session.clear()
            session.update(id_utente=u["id"], nome=u["nome"], potere=u["potere"])
            # data_inizio = login, data_fine = logout
            session["id_log"] = log("sessione")
            return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    if session.get("id_log"):
        execute("UPDATE Log_Tracciabilita SET data_fine=NOW() WHERE id=%s",
                (session["id_log"],))
    session.clear()
    return redirect(url_for("login"))


@app.route("/uploads/<path:nome>")
@login_required
def uploads(nome):
    media = query("""SELECT s.id_utente FROM Media m
                     JOIN Segnalazione s ON s.id=m.id_segnalazione
                     WHERE m.contenuto=%s""", (nome,), one=True)
    if not media:
        abort(404)
    if media["id_utente"] != session["id_utente"] and session.get("potere") != "admin":
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], nome)


@app.route("/mie-segnalazioni")
@login_required
def mie_segnalazioni():
    segnalazioni = query(
        "SELECT id, titolo, stato, data_creazione FROM Segnalazione "
        "WHERE id_utente=%s ORDER BY data_creazione DESC",
        (session["id_utente"],))
    return render_template("mie_segnalazioni.html", segnalazioni=segnalazioni)


# ---------- segnalazioni ----------
@app.route("/nuova", methods=["GET", "POST"])
@login_required
def nuova():
    categorie = query("SELECT * FROM Categoria ORDER BY nome_categoria")
    if request.method == "POST":
        f = request.form
        file = request.files.get("media")
        cats = f.getlist("categorie")
        if not file or not file.filename:
            flash("La prova foto/video è obbligatoria.", "err")
        elif file.filename.rsplit(".", 1)[-1].lower() not in ESTENSIONI:
            flash("Formato non consentito (jpg, png, webp, mp4, mov, webm).", "err")
        elif not cats:
            flash("Scegli almeno una categoria.", "err")
        else:
            nome_file = f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[-1].lower()}"
            lat = f.get("latitudine") or None
            lng = f.get("longitudine") or None
            conn = get_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO Segnalazione (titolo, descrizione, id_utente, stato)"
                        " VALUES (%s,%s,%s,'in_revisione')",
                        (f["titolo"].strip(), f["descrizione"].strip(), session["id_utente"]))
                    id_seg = cur.lastrowid
                    cur.execute(
                        "INSERT INTO Media (contenuto, latitudine, longitudine, id_segnalazione)"
                        " VALUES (%s,%s,%s,%s)", (nome_file, lat, lng, id_seg))
                    for c in cats:
                        cur.execute("INSERT INTO Appartiene (id_segnalazione, id_categoria)"
                                    " VALUES (%s,%s)", (id_seg, int(c)))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], nome_file))
            log("nuova_segnalazione")
            flash("Segnalazione inviata: è in attesa di revisione dell'admin.", "ok")
            return redirect(url_for("dettaglio", id=id_seg))
    return render_template("nuova.html", categorie=categorie)


@app.route("/segnalazione/<int:id>")
@login_required
def dettaglio(id):
    s = query("""SELECT s.*, u.nome, u.cognome, u.zona FROM Segnalazione s
                 JOIN Utente u ON u.id=s.id_utente WHERE s.id=%s""", (id,), one=True)
    if not s:
        abort(404)
    if s["id_utente"] != session["id_utente"] and session.get("potere") != "admin":
        abort(404)
    media = query("SELECT * FROM Media WHERE id_segnalazione=%s", (id,))
    cats = query("""SELECT c.nome_categoria FROM Appartiene a
                    JOIN Categoria c ON c.id=a.id_categoria
                    WHERE a.id_segnalazione=%s""", (id,))
    sostegni = query("SELECT COUNT(*) n FROM Assegna WHERE id_segnalazione=%s",
                     (id,), one=True)["n"]
    gia = False
    if "id_utente" in session:
        gia = bool(query("SELECT 1 FROM Assegna WHERE id_utente=%s AND id_segnalazione=%s",
                         (session["id_utente"], id), one=True))
    return render_template("dettaglio.html", s=s, media=media, cats=cats,
                           sostegni=sostegni, gia=gia)


@app.route("/segnalazione/<int:id>/sostieni", methods=["POST"])
@login_required
def sostieni(id):
    try:
        execute("INSERT INTO Assegna (id_utente, id_segnalazione, punteggio)"
                " VALUES (%s,%s,1)", (session["id_utente"], id))
        log("sostegno")
    except pymysql.err.IntegrityError:
        flash("Hai già sostenuto questa segnalazione.", "err")
    return redirect(url_for("dettaglio", id=id))


# ---------- area admin ----------
@app.route("/admin")
@admin_required
def admin():
    return render_template(
        "admin/dashboard.html",
        segnalazioni=query("""SELECT s.id, s.titolo, s.stato, u.nome, u.cognome
                              FROM Segnalazione s JOIN Utente u ON u.id=s.id_utente
                              ORDER BY s.data_creazione DESC"""),
        utenti=query("SELECT id, nome, cognome, email, stato, potere, zona FROM Utente"),
        log=query("""SELECT l.*, u.nome, u.cognome FROM Log_Tracciabilita l
                     JOIN Utente u ON u.id=l.id_utente ORDER BY l.id DESC LIMIT 30"""),
        stati_s=STATI_SEGNALAZIONE, stati_u=STATI_UTENTE)


@app.route("/admin/segnalazione/<int:id>/stato", methods=["POST"])
@admin_required
def admin_stato_segnalazione(id):
    stato = request.form["stato"]
    if stato in STATI_SEGNALAZIONE:
        execute("UPDATE Segnalazione SET stato=%s WHERE id=%s", (stato, id))
        log(f"stato_segnalazione_{id}_{stato}")
    return redirect(url_for("admin"))


@app.route("/admin/utente/<int:id>/stato", methods=["POST"])
@admin_required
def admin_stato_utente(id):
    stato = request.form["stato"]
    if stato in STATI_UTENTE and id != session["id_utente"]:
        execute("UPDATE Utente SET stato=%s WHERE id=%s", (stato, id))
        # traccia chi ha supervisionato chi (relazione ricorsiva)
        execute("""INSERT INTO Supervisionare (id_supervisore, id_supervisionato, tipo_azione, motivo)
                   VALUES (%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE tipo_azione=VALUES(tipo_azione), motivo=VALUES(motivo)""",
                (session["id_utente"], id, stato, request.form.get("motivo", "")))
        log(f"utente_{id}_{stato}")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
