"""
SVGS - Système de Vente et Gestion des Stocks
Module: Connexion et initialisation de la base de données MySQL
"""
import mysql.connector
from mysql.connector import Error
import hashlib
import os


# ─── Configuration de connexion MySQL ────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "svgs_db",
    "charset": "utf8mb4",
    "autocommit": False,
}


def get_connection():
    """Retourne une connexion active à la base de données."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"Impossible de se connecter à MySQL :\n{e}")


def hash_password(password: str) -> str:
    """Hache un mot de passe avec SHA-256 (compatible sans bcrypt)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ─── Script SQL de création de la base ───────────────────────────────────────
SQL_INIT = """
CREATE DATABASE IF NOT EXISTS svgs_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE svgs_db;

-- ══════════════════════════════════════════════════
--  TABLE : utilisateurs
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS utilisateurs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL,
    prenom      VARCHAR(100) NOT NULL,
    login       VARCHAR(50)  UNIQUE NOT NULL,
    mot_de_passe VARCHAR(255) NOT NULL,
    role        ENUM('caissier','gestionnaire','admin') NOT NULL DEFAULT 'caissier',
    statut      ENUM('actif','inactif') DEFAULT 'actif',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  TABLE : categories
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    libelle     VARCHAR(100) NOT NULL,
    description TEXT
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  TABLE : articles
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS articles (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    code         VARCHAR(50)  UNIQUE NOT NULL,
    code_barre   VARCHAR(100),
    designation  VARCHAR(255) NOT NULL,
    categorie_id INT,
    prix_achat   DECIMAL(12,2) NOT NULL DEFAULT 0,
    prix_vente   DECIMAL(12,2) NOT NULL,
    unite        VARCHAR(20)  DEFAULT 'unité',
    seuil_alerte INT DEFAULT 5,
    statut       ENUM('actif','inactif') DEFAULT 'actif',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (categorie_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  TABLE : stocks
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS stocks (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    article_id        INT NOT NULL UNIQUE,
    quantite_actuelle DECIMAL(12,3) DEFAULT 0,
    quantite_reservee DECIMAL(12,3) DEFAULT 0,
    date_maj          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  TABLE : mouvements_stock
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS mouvements_stock (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    article_id     INT NOT NULL,
    type_mvt       ENUM('ENTREE','SORTIE','INVENTAIRE','CORRECTION') NOT NULL,
    quantite       DECIMAL(12,3) NOT NULL,
    prix_unitaire  DECIMAL(12,2),
    motif          VARCHAR(255),
    reference      VARCHAR(100),
    user_id        INT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(id),
    FOREIGN KEY (user_id)    REFERENCES utilisateurs(id)
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  TABLE : clients
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS clients (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    nom        VARCHAR(100) NOT NULL,
    prenom     VARCHAR(100),
    telephone  VARCHAR(20),
    adresse    TEXT,
    solde_du   DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  TABLE : fournisseurs
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fournisseurs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    raison_sociale VARCHAR(200) NOT NULL,
    contact       VARCHAR(100),
    telephone     VARCHAR(20),
    adresse       TEXT,
    email         VARCHAR(150)
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  TABLE : ventes
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ventes (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    reference      VARCHAR(30) UNIQUE NOT NULL,
    user_id        INT NOT NULL,
    client_id      INT,
    total_ht       DECIMAL(12,2) NOT NULL,
    taux_tva       DECIMAL(5,2)  DEFAULT 0,
    total_ttc      DECIMAL(12,2) NOT NULL,
    remise         DECIMAL(12,2) DEFAULT 0,
    mode_paiement  ENUM('ESPECES','MOBILE_MONEY','CREDIT','CHEQUE') DEFAULT 'ESPECES',
    montant_recu   DECIMAL(12,2),
    statut         ENUM('VALIDEE','ANNULEE','CREDIT') DEFAULT 'VALIDEE',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES utilisateurs(id),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  TABLE : lignes_vente
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS lignes_vente (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    vente_id      INT NOT NULL,
    article_id    INT NOT NULL,
    quantite      DECIMAL(12,3) NOT NULL,
    prix_unitaire DECIMAL(12,2) NOT NULL,
    montant_ligne DECIMAL(12,2) NOT NULL,
    remise_ligne  DECIMAL(12,2) DEFAULT 0,
    FOREIGN KEY (vente_id)   REFERENCES ventes(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(id)
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  TABLE : audit_logs
-- ══════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS audit_logs (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT,
    action           VARCHAR(50) NOT NULL,
    table_cible      VARCHAR(100),
    enregistrement_id INT,
    details          TEXT,
    ip_adresse       VARCHAR(45),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE SET NULL
) ENGINE=InnoDB;
"""

# ─── Données de démonstration ─────────────────────────────────────────────────
SQL_SEED = """
USE svgs_db;

-- Utilisateurs (mot de passe = 'admin123' hashé)
INSERT IGNORE INTO utilisateurs (nom, prenom, login, mot_de_passe, role) VALUES
('MBOLONG', 'Administrateur', 'admin',       SHA2('admin123',256),       'admin'),
('FOUDA',   'Gestionnaire',   'gestionnaire', SHA2('gest123',256), 'gestionnaire'),
('DUPONT',  'Jean',           'caissier',     SHA2('caisse123',256), 'caissier');

-- Catégories
INSERT IGNORE INTO categories (libelle, description) VALUES
('Alimentation',  'Produits alimentaires et boissons'),
('Hygiène',       'Produits d''hygiène et beauté'),
('Électronique',  'Appareils et accessoires électroniques'),
('Papeterie',     'Fournitures scolaires et de bureau'),
('Divers',        'Articles divers');

-- Articles
INSERT IGNORE INTO articles (code, designation, categorie_id, prix_achat, prix_vente, unite, seuil_alerte) VALUES
('ART001', 'Riz parfumé 25kg',        1, 15000, 18000, 'sac',    3),
('ART002', 'Huile végétale 5L',       1,  4500,  5500, 'bidon',  5),
('ART003', 'Sucre 50kg',              1, 22000, 26000, 'sac',    2),
('ART004', 'Lait concentré Nestlé',   1,   350,   500, 'boîte', 20),
('ART005', 'Savon de ménage OMO',     2,   250,   350, 'barre', 15),
('ART006', 'Dentifrice Signal 75ml',  2,   450,   600, 'tube',  10),
('ART007', 'Téléphone Samsung A05',   3, 45000, 55000, 'pièce',  2),
('ART008', 'Chargeur universel',      3,  2000,  3500, 'pièce',  5),
('ART009', 'Cahier 100 pages',        4,   150,   250, 'pièce', 30),
('ART010', 'Stylo BIC noir',          4,    50,   100, 'pièce', 50),
('ART011', 'Eau minérale Tangui 1.5L',1,   250,   350, 'bouteille',25),
('ART012', 'Bière Beaufort 65cl',     1,   500,   700, 'bouteille',10),
('ART013', 'Farine de blé 5kg',       1,  2800,  3500, 'paquet',  5),
('ART014', 'Tomate concentrée',       1,   150,   250, 'boîte',  20),
('ART015', 'Sardine en boîte',        1,   400,   600, 'boîte',  15),
('ART016', 'Huile de palme 1L',       1,   900,  1200, 'bouteille', 8),
('ART017', 'Pâtes alimentaires 500g', 1,   450,   650, 'paquet', 12),
('ART018', 'Sel iodé 1kg',            1,   200,   300, 'paquet', 20),
('ART019', 'Lessive Omo 500g',        2,   750,  1000, 'paquet', 10),
('ART020', 'Papier hygiénique x6',    2,   900,  1300, 'paquet',  8);

-- Stocks initiaux
INSERT IGNORE INTO stocks (article_id, quantite_actuelle) VALUES
(1, 10),(2, 8),(3, 5),(4, 50),(5, 30),(6, 25),(7, 3),(8, 10),
(9, 60),(10,100),(11,40),(12,20),(13,15),(14,45),(15,30),
(16,12),(17,25),(18,35),(19,15),(20,12);

-- Fournisseurs
INSERT IGNORE INTO fournisseurs (raison_sociale, contact, telephone) VALUES
('SCTM Yaoundé',       'M. ATEBA',   '677123456'),
('ORCA Cameroun',      'Mme BIKOE',  '699234567'),
('Express Wholesale',  'M. NGUELE',  '655345678');

-- Clients
INSERT IGNORE INTO clients (nom, prenom, telephone) VALUES
('ESSAMA', 'Pierre',   '675000001'),
('BIYONG', 'Marie',    '699000002'),
('NKOLO',  'François', '655000003');
"""


def init_database(host="localhost", port=3306, user="root", password=""):
    """Initialise la base de données SVGS (à appeler une seule fois)."""
    global DB_CONFIG
    DB_CONFIG.update({"host": host, "port": port, "user": user, "password": password})

    # Connexion sans base de données spécifique pour la créer
    cfg_no_db = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    cfg_no_db["autocommit"] = True

    conn = mysql.connector.connect(**cfg_no_db)
    cursor = conn.cursor()

    for statement in SQL_INIT.strip().split(";"):
        s = statement.strip()
        if not s:
            continue
        try:
            cursor.execute(s)
        except Error:
            pass

    # S'assurer que la base est bien sélectionnée avant l'insertion des données
    try:
        cursor.execute("USE svgs_db")
    except Error:
        pass

    # Seed données de démo
    for statement in SQL_SEED.strip().split(";"):
        s = statement.strip()
        if not s:
            continue
        try:
            cursor.execute(s)
        except Error:
            pass

    conn.commit()
    cursor.close()
    conn.close()
