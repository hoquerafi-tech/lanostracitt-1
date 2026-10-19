-- Esegui DOPO database.sql
USE InsiemePerMilano;

ALTER TABLE Utente
  ADD email VARCHAR(100) NULL UNIQUE,
  ADD password_hash VARCHAR(255) NULL;

ALTER TABLE Segnalazione
  ADD stato VARCHAR(20) NOT NULL DEFAULT 'ricevuta',
  -- ricevuta / in_carico / inviata_candidati / rifiutata
  ADD data_creazione DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
