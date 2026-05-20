"""
SVGS — Tableau de bord (Dashboard)
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from constants import COLORS, FONTS
from database import get_connection
from widgets import KPICard, SectionHeader, DataTable, StyledButton


class DashboardModule(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS["bg_main"])
        self.user = user
        self._build()
        self.refresh()

    def _build(self):
        # ── En-tête ──────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["bg_main"])
        header.pack(fill="x", padx=24, pady=(20, 0))

        tk.Label(header, text="📊  Tableau de Bord",
                 font=FONTS["title"], bg=COLORS["bg_main"],
                 fg=COLORS["primary"]).pack(side="left")

        self._date_lbl = tk.Label(header, text="",
                                   font=FONTS["body"],
                                   bg=COLORS["bg_main"],
                                   fg=COLORS["text_muted"])
        self._date_lbl.pack(side="right", pady=4)

        btn_refresh = StyledButton(header, "↺  Actualiser",
                                    command=self.refresh, style="outline")
        btn_refresh.pack(side="right", padx=8)

        # ── Séparateur ────────────────────────────────────────────────────
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=8)

        # ── KPI Cards ─────────────────────────────────────────────────────
        kpi_frame = tk.Frame(self, bg=COLORS["bg_main"])
        kpi_frame.pack(fill="x", padx=24, pady=(0, 16))
        kpi_frame.columnconfigure((0,1,2,3), weight=1, uniform="kpi")

        self.kpi_ventes = KPICard(kpi_frame, "Ventes aujourd'hui", "—",
                                   unit="transactions",
                                   color=COLORS["kpi_ventes"], icon="🛒")
        self.kpi_ventes.grid(row=0, column=0, padx=(0,8), pady=4, sticky="nsew")

        self.kpi_ca = KPICard(kpi_frame, "CA du jour", "—",
                               unit="FCFA",
                               color=COLORS["kpi_ca"], icon="💰")
        self.kpi_ca.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")

        self.kpi_alerte = KPICard(kpi_frame, "Articles en alerte", "—",
                                   unit="articles sous seuil",
                                   color=COLORS["kpi_alerte"], icon="⚠️")
        self.kpi_alerte.grid(row=0, column=2, padx=4, pady=4, sticky="nsew")

        self.kpi_stock = KPICard(kpi_frame, "Valeur du stock", "—",
                                  unit="FCFA estimés",
                                  color=COLORS["kpi_stock"], icon="📦")
        self.kpi_stock.grid(row=0, column=3, padx=(8,0), pady=4, sticky="nsew")

        # ── Section inférieure ────────────────────────────────────────────
        bottom = tk.Frame(self, bg=COLORS["bg_main"])
        bottom.pack(fill="both", expand=True, padx=24, pady=4)
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        bottom.rowconfigure(0, weight=1)

        # Articles en alerte
        left_panel = tk.Frame(bottom, bg=COLORS["bg_card"],
                               relief="flat", padx=16, pady=16)
        left_panel.grid(row=0, column=0, padx=(0,8), pady=4, sticky="nsew")

        tk.Label(left_panel, text="🔴  Articles en alerte de stock",
                 font=FONTS["heading"], bg=COLORS["bg_card"],
                 fg=COLORS["danger"]).pack(anchor="w", pady=(0,8))

        self.alerte_table = DataTable(
            left_panel,
            columns=[
                ("Code",       80,  "w"),
                ("Article",   200,  "w"),
                ("Stock",      70, "center"),
                ("Seuil",      70, "center"),
                ("Statut",    100, "center"),
            ],
            height=10
        )
        self.alerte_table.pack(fill="both", expand=True)

        # Dernières ventes
        right_panel = tk.Frame(bottom, bg=COLORS["bg_card"],
                                relief="flat", padx=16, pady=16)
        right_panel.grid(row=0, column=1, padx=(8,0), pady=4, sticky="nsew")

        tk.Label(right_panel, text="🕐  Dernières ventes",
                 font=FONTS["heading"], bg=COLORS["bg_card"],
                 fg=COLORS["primary"]).pack(anchor="w", pady=(0,8))

        self.ventes_table = DataTable(
            right_panel,
            columns=[
                ("Référence",  110, "w"),
                ("Heure",       70, "center"),
                ("Caissier",   110, "w"),
                ("Total TTC",  100, "e"),
                ("Statut",      90, "center"),
            ],
            height=10
        )
        self.ventes_table.pack(fill="both", expand=True)

    def refresh(self):
        """Recharge toutes les données du tableau de bord."""
        now = datetime.now()
        self._date_lbl.config(
            text=f"📅  {now.strftime('%A %d %B %Y — %H:%M').capitalize()}"
        )

        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)

            # KPI : Ventes du jour
            cursor.execute("""
                SELECT COUNT(*) AS nb, COALESCE(SUM(total_ttc),0) AS ca
                FROM ventes
                WHERE DATE(created_at) = CURDATE() AND statut='VALIDEE'
            """)
            row = cursor.fetchone()
            self.kpi_ventes.update_value(row["nb"])
            ca = int(row["ca"])
            self.kpi_ca.update_value(f"{ca:,}".replace(",", " "))

            # KPI : Articles en alerte
            cursor.execute("""
                SELECT COUNT(*) AS nb FROM stocks s
                JOIN articles a ON a.id = s.article_id
                WHERE s.quantite_actuelle <= a.seuil_alerte AND a.statut='actif'
            """)
            self.kpi_alerte.update_value(cursor.fetchone()["nb"])

            # KPI : Valeur du stock
            cursor.execute("""
                SELECT COALESCE(SUM(s.quantite_actuelle * a.prix_achat), 0) AS val
                FROM stocks s JOIN articles a ON a.id = s.article_id
                WHERE a.statut='actif'
            """)
            val = int(cursor.fetchone()["val"])
            self.kpi_stock.update_value(f"{val:,}".replace(",", " "))

            # Table alertes
            self.alerte_table.clear()
            cursor.execute("""
                SELECT a.code, a.designation, s.quantite_actuelle,
                       a.seuil_alerte
                FROM stocks s JOIN articles a ON a.id = s.article_id
                WHERE s.quantite_actuelle <= a.seuil_alerte AND a.statut='actif'
                ORDER BY (s.quantite_actuelle / a.seuil_alerte) ASC
                LIMIT 15
            """)
            for r in cursor.fetchall():
                if r["quantite_actuelle"] == 0:
                    tag = "danger"
                    status = "🔴 RUPTURE"
                else:
                    tag = "warning"
                    status = "🟠 FAIBLE"
                self.alerte_table.insert(
                    (r["code"], r["designation"],
                     f"{r['quantite_actuelle']:.0f}",
                     r["seuil_alerte"], status),
                    tag=tag
                )

            # Table dernières ventes
            self.ventes_table.clear()
            cursor.execute("""
                SELECT v.reference, v.created_at, u.nom,
                       v.total_ttc, v.statut
                FROM ventes v
                JOIN utilisateurs u ON u.id = v.user_id
                ORDER BY v.created_at DESC LIMIT 15
            """)
            for r in cursor.fetchall():
                tag = "success" if r["statut"] == "VALIDEE" else "danger"
                status_icon = {"VALIDEE": "✅ Validée",
                               "ANNULEE": "❌ Annulée",
                               "CREDIT":  "🕒 Crédit"}.get(r["statut"], r["statut"])
                heure = r["created_at"].strftime("%H:%M") if r["created_at"] else "—"
                self.ventes_table.insert(
                    (r["reference"], heure, r["nom"],
                     f"{int(r['total_ttc']):,} F".replace(",", " "),
                     status_icon),
                    tag=tag
                )

            cursor.close()
            conn.close()

        except Exception as e:
            pass  # Silencieux si pas de BDD
