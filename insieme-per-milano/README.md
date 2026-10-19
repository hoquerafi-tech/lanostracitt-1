# Insieme per Milano (Flask + MySQL)

## Installazione
1. Avvia MySQL (XAMPP/MAMP o servizio locale).
2. Importa in ordine: `database.sql` poi `aggiornamento.sql`
   (es. `mysql -u root -p < database.sql` e `mysql -u root -p < aggiornamento.sql`).
3. `pip install -r requirements.txt`
4. Imposta email/password dell'admin: `python crea_admin.py`
5. Avvia: `python app.py` e apri http://127.0.0.1:5000

## Configurazione DB
I valori predefiniti puntano a MySQL locale (`localhost:3306`, utente `root`,
password vuota, database `InsiemePerMilano`). Per un database remoto imposta le
variabili d'ambiente `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS` e `DB_NAME`.
Per connessioni TLS imposta anche `DB_SSL=1` e, se necessario, `DB_SSL_CA`.
Non salvare password o certificati nel repository.

`SECRET_KEY` è una variabile d'ambiente opzionale per la chiave delle sessioni.
