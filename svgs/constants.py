"""SVGS — Constantes, couleurs et configuration de thème"""

APP_NAME    = "SVGS — Système de Vente & Gestion des Stocks"
APP_VERSION = "v1.0"
ETABLISSEMENT = "Commerce MBOLONG"
VILLE = "Yaoundé, Cameroun"

COLORS = {
    "primary":       "#6366F1",
    "primary_light": "#818CF8",
    "primary_dark":  "#4F46E5",
    "accent":        "#06B6D4",
    "success":       "#10B981",
    "success_light": "#34D399",
    "warning":       "#F59E0B",
    "danger":        "#EF4444",
    "danger_light":  "#FB7185",
    "bg_main":       "#F1F5F9",
    "bg_sidebar":    "#0F172A",
    "bg_card":       "#FFFFFF",
    "bg_card_alt":   "#F8FAFC",
    "bg_header":     "#FFFFFF",
    "text_main":     "#111827",
    "text_muted":    "#6B7280",
    "text_white":    "#FFFFFF",
    "text_sidebar":  "#E2E8F0",
    "border":        "#E5E7EB",
    "border_focus":  "#6366F1",
    "shadow":        "#CBD5E1",
    "kpi_ventes":    "#6366F1",
    "kpi_ca":        "#10B981",
    "kpi_alerte":    "#EF4444",
    "kpi_stock":     "#06B6D4",
}

FONTS = {
    "title":    ("Segoe UI", 22, "bold"),
    "subtitle": ("Segoe UI", 16, "bold"),
    "heading":  ("Segoe UI", 12, "bold"),
    "body":     ("Segoe UI", 11),
    "small":    ("Segoe UI", 9),
    "mono":     ("Courier New", 10),
    "kpi_val":  ("Segoe UI", 28, "bold"),
    "kpi_lbl":  ("Segoe UI", 10, "bold"),
    "sidebar":  ("Segoe UI", 11, "bold"),
    "btn":      ("Segoe UI", 10, "bold"),
    "badge":    ("Segoe UI", 9, "bold"),
}

SIDEBAR_WIDTH = 240

ROLES = {
    "admin":        "Administrateur",
    "gestionnaire": "Gestionnaire",
    "caissier":     "Caissier",
}

MODES_PAIEMENT = ["ESPECES", "MOBILE_MONEY", "CREDIT", "CHEQUE"]
