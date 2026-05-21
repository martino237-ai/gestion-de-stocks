"""
SVGS — Application principale
Système de Vente et Gestion des Stocks
Auteur : MBOLONG | Encadreur : Mr FOUDA BARTHÉLEMY
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from constants import COLORS, FONTS, APP_NAME, ETABLISSEMENT, SIDEBAR_WIDTH, ROLES
from database import init_database, DB_CONFIG, get_connection
from widgets import StyledButton


class SetupWindow(tk.Toplevel):
    """Fenêtre de première configuration MySQL."""
    def __init__(self, parent, on_done):
        super().__init__(parent)
        self.title("Configuration MySQL — SVGS")
        self.geometry("480x380")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_card"])
        self.grab_set()
        self.on_done = on_done
        self._build()

    def _build(self):
        tk.Label(self, text="⚙️  Configuration de la base de données",
                 font=FONTS["subtitle"], bg=COLORS["bg_card"],
                 fg=COLORS["primary"]).pack(pady=(24, 4))
        tk.Label(self, text="Entrez les paramètres MySQL de votre serveur XAMPP",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(pady=(0, 20))

        frm = tk.Frame(self, bg=COLORS["bg_card"], padx=40)
        frm.pack(fill="x")

        def row(label, default=""):
            f = tk.Frame(frm, bg=COLORS["bg_card"]); f.pack(fill="x", pady=6)
            tk.Label(f, text=label, font=FONTS["body"], bg=COLORS["bg_card"],
                     fg=COLORS["text_muted"], width=16, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            tk.Entry(f, textvariable=var, font=FONTS["body"], relief="solid",
                     bd=1, bg="#FAFAFA").pack(side="left", fill="x", expand=True, ipady=5)
            return var

        self._host = row("Hôte MySQL", "localhost")
        self._port = row("Port", "3306")
        self._user = row("Utilisateur", "root")
        self._pw_var = tk.StringVar(value="")
        f = tk.Frame(frm, bg=COLORS["bg_card"]); f.pack(fill="x", pady=6)
        tk.Label(f, text="Mot de passe", font=FONTS["body"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"], width=16, anchor="w").pack(side="left")
        tk.Entry(f, textvariable=self._pw_var, font=FONTS["body"], show="●",
                 relief="solid", bd=1, bg="#FAFAFA").pack(side="left", fill="x", expand=True, ipady=5)

        self._msg = tk.Label(self, text="", font=FONTS["small"], bg=COLORS["bg_card"])
        self._msg.pack(pady=8)

        btn = tk.Button(self, text="🚀  Initialiser la base de données",
                        font=FONTS["btn"], bg=COLORS["primary"], fg="white",
                        relief="flat", bd=0, padx=20, pady=10, cursor="hand2",
                        command=self._init)
        btn.pack(pady=8)

        tk.Label(self, text="💡 XAMPP doit être démarré avec Apache et MySQL actifs.",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["accent"]).pack(pady=4)

    def _init(self):
        host = self._host.get().strip() or "localhost"
        try:
            port = int(self._port.get() or 3306)
        except ValueError:
            port = 3306
        user = self._user.get().strip() or "root"
        pw   = self._pw_var.get()

        self._msg.config(text="⏳ Connexion en cours...", fg=COLORS["primary"])
        self.update()
        try:
            init_database(host=host, port=port, user=user, password=pw)
            self._msg.config(text="✅ Base de données initialisée !", fg=COLORS["success"])
            self.after(1200, lambda: (self.destroy(), self.on_done()))
        except Exception as e:
            self._msg.config(text=f"❌ Erreur : {e}", fg=COLORS["danger"])


class SVGSApp(tk.Tk):
    """Application principale SVGS."""

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.state("zoomed")           # Plein écran Windows
        self.configure(bg=COLORS["bg_main"])
        self.minsize(1100, 650)

        # Style global ttk
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=COLORS["bg_main"], borderwidth=0)
        style.configure("TNotebook.Tab", font=FONTS["body"], padding=[14, 8],
                        background=COLORS["bg_main"], foreground=COLORS["text_muted"])
        style.map("TNotebook.Tab",
                  background=[("selected", COLORS["bg_card"])],
                  foreground=[("selected", COLORS["primary"])])
        style.configure("TSeparator", background=COLORS["border"])
        style.configure("TSpinbox", padding=4)

        self._user = None
        self._current_module = None
        self._modules_cache = {}

        self._show_login()

    # ─── Écran de connexion ───────────────────────────────────────────────────
    def _show_login(self):
        for w in self.winfo_children():
            w.destroy()
        self._modules_cache.clear()

        # Vérifier si la BDD est accessible
        try:
            conn = get_connection()
            conn.close()
            from modules.login import LoginScreen
            LoginScreen(self, self._on_login_success)
        except Exception:
            # BDD non accessible → setup
            self._show_setup_first()

    def _show_setup_first(self):
        """Affiche la configuration si c'est la première fois."""
        for w in self.winfo_children():
            w.destroy()

        container = tk.Frame(self, bg=COLORS["bg_main"])
        container.pack(fill="both", expand=True)

        card = tk.Frame(container, bg=COLORS["bg_card"], bd=1, relief="solid")
        card.place(relx=0.5, rely=0.5, anchor="center", width=520, height=420)

        tk.Label(card, text="🛠️  Configuration MySQL requise",
                 font=FONTS["title"], bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(pady=(24, 8))
        tk.Label(card, text="Aucune connexion à la base de données n'a pu être établie.",
                 font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"], justify="center").pack(padx=28)
        tk.Label(card, text="Démarrez XAMPP, puis configurez vos paramètres MySQL.",
                 font=FONTS["body"], bg=COLORS["bg_card"], fg=COLORS["text_muted"], justify="center").pack(padx=28, pady=(0, 20))

        StyledButton(card, "⚙️  Configurer la base de données",
                     style="primary", command=lambda: SetupWindow(self, self._show_login)).pack(pady=12)
        StyledButton(card, "↺  Réessayer", style="outline",
                     command=self._show_login).pack(pady=4)

        tk.Label(card, text="💡 Assurez-vous qu'Apache et MySQL sont actifs dans XAMPP.",
                 font=FONTS["small"], bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(pady=(16, 0))

    def _on_login_success(self, user):
        self._user = user
        self._build_main_ui()

    # ─── Interface principale ─────────────────────────────────────────────────
    def _build_main_ui(self):
        for w in self.winfo_children():
            w.destroy()
        self._modules_cache.clear()

        # ── Root layout
        root_frame = tk.Frame(self, bg=COLORS["bg_main"])
        root_frame.pack(fill="both", expand=True)

        # ── Sidebar
        sidebar = tk.Frame(root_frame, bg=COLORS["bg_sidebar"],
                           width=SIDEBAR_WIDTH)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        self._build_sidebar(sidebar)

        # ── Zone contenu principale
        main_area = tk.Frame(root_frame, bg=COLORS["bg_main"])
        main_area.pack(side="left", fill="both", expand=True)

        # En-tête barre du haut
        self._build_topbar(main_area)

        # Conteneur des modules
        self._content = tk.Frame(main_area, bg=COLORS["bg_main"])
        self._content.pack(fill="both", expand=True)

        # Afficher le tableau de bord par défaut
        self._show_module("dashboard")

    def _build_sidebar(self, parent):
        # Logo & marque
        logo_frame = tk.Frame(parent, bg=COLORS["primary_dark"], pady=24)
        logo_frame.pack(fill="x")
        tk.Label(logo_frame, text="🛒", font=("Segoe UI", 30),
                 bg=COLORS["primary_dark"], fg="white").pack()
        tk.Label(logo_frame, text="SVGS", font=("Segoe UI", 18, "bold"),
                 bg=COLORS["primary_dark"], fg="white").pack()
        tk.Label(logo_frame, text=ETABLISSEMENT, font=FONTS["small"],
                 bg=COLORS["primary_dark"], fg=COLORS["bg_card_alt"]).pack(pady=(4, 0))

        tk.Frame(parent, bg=COLORS["primary"], height=2).pack(fill="x")

        # Profil utilisateur
        user_frame = tk.Frame(parent, bg=COLORS["bg_sidebar"], pady=16, padx=16)
        user_frame.pack(fill="x")
        tk.Label(user_frame, text=f"{self._user['prenom']} {self._user['nom']}",
                 font=FONTS["sidebar"], bg=COLORS["bg_sidebar"],
                 fg=COLORS["text_sidebar"], anchor="w").pack(fill="x")
        tk.Label(user_frame, text=ROLES.get(self._user["role"], self._user["role"]),
                 font=FONTS["small"], bg=COLORS["bg_sidebar"],
                 fg=COLORS["accent"], anchor="w").pack(fill="x", pady=(2, 0))

        tk.Frame(parent, bg=COLORS["primary_dark"], height=1).pack(fill="x", padx=16)

        # Menu items
        role = self._user["role"]
        menu_items = [
            ("dashboard",      "📊",  "Tableau de bord",    ["caissier","gestionnaire","admin"]),
            ("caisse",         "🛒",  "Caisse / Vente",     ["caissier","gestionnaire","admin"]),
            ("articles",       "📦",  "Articles",           ["caissier","gestionnaire","admin"]),
            ("stock",          "🏭",  "Gestion des stocks", ["gestionnaire","admin"]),
            ("rapports",       "📈",  "Rapports",           ["gestionnaire","admin"]),
            ("fournisseurs",   "🤝",  "Fournisseurs & Clients", ["gestionnaire","admin"]),
            ("utilisateurs",   "👥",  "Utilisateurs",       ["admin"]),
        ]

        self._sidebar_buttons = {}
        for key, icon, label, roles in menu_items:
            if role not in roles:
                continue
            item = tk.Frame(parent, bg=COLORS["bg_sidebar"])
            item.pack(fill="x")
            btn = tk.Button(
                item,
                text=f"  {icon}   {label}",
                font=FONTS["sidebar"],
                bg=COLORS["bg_sidebar"],
                fg=COLORS["text_sidebar"],
                activebackground=COLORS["primary_light"],
                activeforeground="white",
                relief="flat", bd=0, cursor="hand2",
                anchor="w", padx=12, pady=12,
                command=lambda k=key: self._show_module(k),
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["primary_light"]))
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.config(
                bg=COLORS["primary"] if self._current_module == k else COLORS["bg_sidebar"]))
            self._sidebar_buttons[key] = btn

        tk.Frame(parent, bg=COLORS["primary_dark"], height=1).pack(fill="x", padx=16, pady=12)

        logout_btn = tk.Button(parent, text="  🔓   Déconnexion",
                                font=FONTS["sidebar"],
                                bg=COLORS["bg_sidebar"], fg=COLORS["danger"],
                                activebackground=COLORS["danger_light"],
                                activeforeground=COLORS["text_white"],
                                relief="flat", bd=0, cursor="hand2",
                                anchor="w", padx=12, pady=12,
                                command=self._logout)
        logout_btn.pack(fill="x", side="bottom", pady=(4, 12), padx=12)

        self._clock_lbl = tk.Label(parent, text="", font=FONTS["small"],
                                    bg=COLORS["bg_sidebar"], fg=COLORS["text_muted"])
        self._clock_lbl.pack(side="bottom", pady=6)
        self._update_clock()

    def _update_clock(self):
        now = datetime.now().strftime("%H:%M:%S\n%d/%m/%Y")
        self._clock_lbl.config(text=now)
        self.after(1000, self._update_clock)

    def _build_topbar(self, parent):
        top_line = tk.Frame(parent, bg=COLORS["primary"], height=4)
        top_line.pack(fill="x")

        bar = tk.Frame(parent, bg=COLORS["bg_card"], pady=12, padx=20)
        bar.pack(fill="x", side="top")

        self._topbar_title = tk.Label(bar, text="Tableau de bord",
                                       font=FONTS["heading"],
                                       bg=COLORS["bg_card"], fg=COLORS["text_main"])
        self._topbar_title.pack(side="left")

        tk.Label(bar, text=f"🏪 {ETABLISSEMENT}",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(side="right", padx=12)

        self._alert_badge = tk.Label(bar, text="", font=FONTS["small"],
                                      bg=COLORS["danger"], fg=COLORS["text_white"],
                                      padx=10, pady=4)
        self._alert_badge.pack(side="right", padx=(0, 12))
        self._update_alert_badge()

        badge = tk.Label(bar, text="Notifications", font=FONTS["small"],
                        bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        badge.pack(side="right")

    def _update_alert_badge(self):
        try:
            conn = get_connection()
            c    = conn.cursor()
            c.execute("""
                SELECT COUNT(*) FROM stocks s JOIN articles a ON a.id=s.article_id
                WHERE s.quantite_actuelle <= a.seuil_alerte AND a.statut='actif'
            """)
            nb = c.fetchone()[0]
            c.close(); conn.close()
            if nb > 0:
                self._alert_badge.config(text=f"⚠ {nb} alerte(s) stock")
            else:
                self._alert_badge.config(text="")
        except Exception:
            pass
        self.after(30000, self._update_alert_badge)  # toutes les 30s

    def _show_module(self, key):
        # Réinitialiser couleurs sidebar
        for k, b in self._sidebar_buttons.items():
            b.config(bg=COLORS["primary"] if k == key else COLORS["bg_sidebar"])

        self._current_module = key

        titles = {
            "dashboard":    "📊  Tableau de bord",
            "caisse":       "🛒  Interface de Caisse",
            "articles":     "📦  Gestion des Articles",
            "stock":        "🏭  Gestion des Stocks",
            "rapports":     "📈  Rapports & Statistiques",
            "fournisseurs": "🤝  Fournisseurs & Clients",
            "utilisateurs": "👥  Gestion des Utilisateurs",
        }
        self._topbar_title.config(text=titles.get(key, key))

        # Vider le contenu
        for w in self._content.winfo_children():
            w.pack_forget()

        # Charger ou récupérer le module du cache
        if key not in self._modules_cache:
            module = self._create_module(key)
            self._modules_cache[key] = module
        else:
            module = self._modules_cache[key]

        module.pack(fill="both", expand=True)

        # Rafraîchir si le module a une méthode refresh/load_data
        if hasattr(module, "refresh"):
            module.refresh()

    def _create_module(self, key):
        from modules.dashboard     import DashboardModule
        from modules.caisse        import CaisseModule
        from modules.articles      import ArticlesModule
        from modules.stock         import StockModule
        from modules.rapports      import RapportsModule
        from modules.fournisseurs  import FournisseursModule
        from modules.utilisateurs  import UtilisateursModule

        mapping = {
            "dashboard":    DashboardModule,
            "caisse":       CaisseModule,
            "articles":     ArticlesModule,
            "stock":        StockModule,
            "rapports":     RapportsModule,
            "fournisseurs": FournisseursModule,
            "utilisateurs": UtilisateursModule,
        }
        cls = mapping.get(key)
        if cls:
            return cls(self._content, self._user)
        return tk.Label(self._content, text=f"Module '{key}' introuvable.",
                        font=FONTS["body"], bg=COLORS["bg_main"])

    def _logout(self):
        if messagebox.askyesno("Déconnexion", "Voulez-vous vous déconnecter ?"):
            self._user = None
            self._show_login()


# ─── Point d'entrée ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SVGSApp()
    app.mainloop()
