-- ============================================================
-- CREAZIONE DATABASE
-- ============================================================
DROP DATABASE IF EXISTS InsiemePerMilano;
CREATE DATABASE InsiemePerMilano
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE InsiemePerMilano;


-- ============================================================
-- 1. UTENTE
-- ============================================================
CREATE TABLE Utente (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    nome        VARCHAR(50)  NOT NULL,
    cognome     VARCHAR(50)  NOT NULL,
    stato       VARCHAR(20)  NOT NULL DEFAULT 'attivo',
                -- attivo / sospeso / bannato
    potere      VARCHAR(20)  NOT NULL DEFAULT 'utente',
                -- utente / admin
    zona        VARCHAR(100)
) ENGINE=InnoDB;


-- ============================================================
-- 2. SEGNALAZIONE
-- Relazione "manda": Utente (0,N) — Segnalazione (1,1)
-- ============================================================
CREATE TABLE Segnalazione (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    titolo          VARCHAR(150) NOT NULL,
    descrizione     TEXT,
    id_utente       INT NOT NULL,
    CONSTRAINT fk_segnalazione_utente
        FOREIGN KEY (id_utente) REFERENCES Utente(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- 3. LOG_TRACCIABILITA (con data_inizio e data_fine)
-- Relazione "compie": Log (1,1) — Utente (0,N)
-- ============================================================
CREATE TABLE Log_Tracciabilita (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    tipo_azione     VARCHAR(50) NOT NULL,
    id_utente       INT NOT NULL,
    data_inizio     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_fine       DATETIME NULL,
    CONSTRAINT fk_log_utente
        FOREIGN KEY (id_utente) REFERENCES Utente(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- 4. CATEGORIA
-- ============================================================
CREATE TABLE Categoria (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    nome_categoria  VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;


-- ============================================================
-- 5. MEDIA
-- Relazione "incluso": Segnalazione (0,N) — Media (0,1)
-- ============================================================
CREATE TABLE Media (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    contenuto       VARCHAR(255) NOT NULL,
    longitudine     DECIMAL(9,6),
    latitudine      DECIMAL(9,6),
    id_segnalazione INT NULL,
    CONSTRAINT fk_media_segnalazione
        FOREIGN KEY (id_segnalazione) REFERENCES Segnalazione(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- 6. APPARTIENE (PK composta, niente id_appartiene)
-- Relazione "appartiene": Segnalazione (1,N) — Categoria (0,N)
-- ============================================================
CREATE TABLE Appartiene (
    id_segnalazione INT NOT NULL,
    id_categoria    INT NOT NULL,
    PRIMARY KEY (id_segnalazione, id_categoria),
    CONSTRAINT fk_appartiene_segnalazione
        FOREIGN KEY (id_segnalazione) REFERENCES Segnalazione(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_appartiene_categoria
        FOREIGN KEY (id_categoria) REFERENCES Categoria(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- 7. ASSEGNA
-- Relazione "assegna": Utente (0,N) — Segnalazione (0,N)
-- ============================================================
CREATE TABLE Assegna (
    id_assegna      INT PRIMARY KEY AUTO_INCREMENT,
    id_utente       INT NOT NULL,
    id_segnalazione INT NOT NULL,
    punteggio       INT NOT NULL,
    CONSTRAINT fk_assegna_utente
        FOREIGN KEY (id_utente) REFERENCES Utente(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_assegna_segnalazione
        FOREIGN KEY (id_segnalazione) REFERENCES Segnalazione(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_assegna UNIQUE (id_utente, id_segnalazione)
) ENGINE=InnoDB;


-- ============================================================
-- 8. SUPERVISIONARE (relazione ricorsiva)
-- Relazione "supervisiona": Utente (0,N) — Utente (0,N)
-- ============================================================
CREATE TABLE Supervisionare (
    id_supervisione     INT PRIMARY KEY AUTO_INCREMENT,
    id_supervisore      INT NOT NULL,
    id_supervisionato   INT NOT NULL,
    tipo_azione         VARCHAR(50),
    motivo              TEXT,
    CONSTRAINT fk_sup_supervisore
        FOREIGN KEY (id_supervisore) REFERENCES Utente(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_sup_supervisionato
        FOREIGN KEY (id_supervisionato) REFERENCES Utente(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_supervisione UNIQUE (id_supervisore, id_supervisionato)
) ENGINE=InnoDB;


-- ============================================================
-- POPOLAMENTO INIZIALE
-- ============================================================

-- Categorie di base
INSERT INTO Categoria (nome_categoria) VALUES
('Ambiente'),
('Mobilità Urbana'),
('Politiche Giovanili'),
('Decoro Urbano'),
('Viabilità'),
('Idrogeologia'),
('Movida'),
('Altro');

-- Admin di base
INSERT INTO Utente (nome, cognome, stato, potere, zona) VALUES
('Admin', 'Sistema', 'attivo', 'admin', 'Centro');


-- ============================================================
-- VERIFICA
-- ============================================================
SHOW TABLES;
SELECT * FROM Categoria;
SELECT * FROM Utente;