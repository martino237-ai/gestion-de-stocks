"""SVGS — Constantes, couleurs et configuration de thème"""

APP_NAME    = "SVGS — Système de Vente & Gestion des Stocks"
APP_VERSION = "v1.0"
ETABLISSEMENT = "Commerce MBOLONG"
VILLE = "Yaoundé, Cameroun"

COLORS = {
    "primary":       "#1565C0",
    "primary_light": "#1E88E5",
    "primary_dark":  "#0D47A1",
    "accent":        "#00ACC1",
    "success":       "#2E7D32",
    "success_light": "#43A047",
    "warning":       "#F57F17",
    "danger":        "#C62828",
    "danger_light":  "#E53935",
    "bg_main":       "#F5F7FA",
    "bg_sidebar":    "#1A237E",
    "bg_card":       "#FFFFFF",
    "bg_header":     "#1565C0",
    "text_main":     "#212121",
    "text_muted":    "#757575",
    "text_white":    "#FFFFFF",
    "text_sidebar":  "#E8EAF6",
    "border":        "#E0E0E0",
    "border_focus":  "#1E88E5",
    "kpi_ventes":    "#1565C0",
    "kpi_ca":        "#2E7D32",
    "kpi_alerte":    "#C62828",
    "kpi_stock":     "#6A1B9A",
}

FONTS = {
    "title":    ("Segoe UI", 20, "bold"),
    "subtitle": ("Segoe UI", 14, "bold"),
    "heading":  ("Segoe UI", 12, "bold"),
    "body":     ("Segoe UI", 11),
    "small":    ("Segoe UI", 9),
    "mono":     ("Courier New", 10),
    "kpi_val":  ("Segoe UI", 28, "bold"),
    "kpi_lbl":  ("Segoe UI", 10),
    "sidebar":  ("Segoe UI", 11, "bold"),
    "btn":      ("Segoe UI", 10, "bold"),
}

SIDEBAR_WIDTH = 220

ROLES = {
    "admin":        "Administrateur",
    "gestionnaire": "Gestionnaire",
    "caissier":     "Caissier",
}

MODES_PAIEMENT = ["ESPECES", "MOBILE_MONEY", "CREDIT", "CHEQUE"]
