# SVGS — Système de Vente et Gestion des Stocks
**Projet de Fin d'Études | MBOLONG | Encadreur : Mr FOUDA BARTHÉLEMY**

## 🚀 Installation rapide

### Prérequis
- Python 3.10+ installé
- MySQL/XAMPP démarré
- Packages : `pip install mysql-connector-python ttkbootstrap`

### Démarrage
```bash
cd svgs
python main.py
```

### Comptes de démonstration
| Rôle | Login | Mot de passe |
|------|-------|--------------|
| Administrateur | admin | admin123 |
| Gestionnaire | gestionnaire | gest123 |
| Caissier | caissier | caisse123 |

## 📁 Structure du projet
```
svgs/
├── main.py              # Application principale
├── database.py          # Connexion & initialisation MySQL
├── constants.py         # Couleurs, polices, constantes
├── widgets.py           # Composants UI réutilisables
└── modules/
    ├── login.py         # Écran de connexion
    ├── dashboard.py     # Tableau de bord & KPIs
    ├── caisse.py        # Point de vente / caisse
    ├── articles.py      # Gestion des articles
    ├── stock.py         # Gestion des stocks
    ├── rapports.py      # Rapports & statistiques
    ├── fournisseurs.py  # Fournisseurs & clients
    └── utilisateurs.py  # Gestion des utilisateurs
```

## 🔧 Stack technique
- **Backend** : Python 3.12 + mysql-connector-python
- **Interface** : Tkinter (UI native)
- **Base de données** : MySQL 8 (via XAMPP)
- **Rapports PDF** : reportlab

## 📦 Fonctionnalités
- ✅ Authentification multi-rôles (Admin / Gestionnaire / Caissier)
- ✅ Interface de caisse avec autocomplétion
- ✅ Gestion complète des articles et catégories
- ✅ Suivi des stocks en temps réel avec alertes
- ✅ Rapports de ventes (jour / semaine / mois)
- ✅ Top articles vendus
- ✅ Gestion fournisseurs & clients
- ✅ Journal d'audit
- ✅ Génération de reçus

---
*Version 1.0 — 2026 | Yaoundé, Cameroun*
