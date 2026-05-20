"""
SVGS — Écran de connexion
"""
import tkinter as tk
from tkinter import messagebox
from constants import COLORS, FONTS, APP_NAME, ETABLISSEMENT
from database import get_connection, hash_password, DB_CONFIG
import mysql.connector


class LoginScreen(tk.Frame):
    def __init__(self, parent, on_success):
        super().__init__(parent, bg=COLORS["bg_sidebar"])
        self.on_success = on_success
        self._build()

    def _build(self):
        self.pack(fill="both", expand=True)

        # ── Côté gauche : branding ──────────────────────────────────────
        left = tk.Frame(self, bg=COLORS["primary_dark"], width=400)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="🛒", font=("Segoe UI", 64),
                 bg=COLORS["primary_dark"], fg="white").pack(pady=(80, 10))
        tk.Label(left, text="SVGS", font=("Segoe UI", 32, "bold"),
                 bg=COLORS["primary_dark"], fg="white").pack()
        tk.Label(left, text="Système de Vente &\nGestion des Stocks",
                 font=("Segoe UI", 13), bg=COLORS["primary_dark"],
                 fg="#90CAF9", justify="center").pack(pady=(4, 0))

        tk.Frame(left, bg="#1E40AF", height=2).pack(fill="x", padx=40, pady=30)

        for feat in ["✅  Ventes & Caisse", "✅  Gestion des stocks",
                     "✅  Rapports & Statistiques", "✅  Multi-utilisateurs"]:
            tk.Label(left, text=feat, font=("Segoe UI", 11),
                     bg=COLORS["primary_dark"], fg="#BBDEFB",
                     anchor="w").pack(padx=50, pady=3, fill="x")

        tk.Label(left, text=ETABLISSEMENT, font=("Segoe UI", 10, "italic"),
                 bg=COLORS["primary_dark"], fg="#64B5F6").pack(side="bottom", pady=20)

        # ── Côté droit : formulaire ──────────────────────────────────────
        right = tk.Frame(self, bg=COLORS["bg_main"])
        right.pack(side="right", fill="both", expand=True)

        # Centrer verticalement
        spacer = tk.Frame(right, bg=COLORS["bg_main"])
        spacer.pack(expand=True)

        card = tk.Frame(right, bg=COLORS["bg_card"],
                        padx=50, pady=40, relief="flat")
        card.pack(padx=60, pady=20, fill="x")

        tk.Label(card, text="Connexion", font=("Segoe UI", 22, "bold"),
                 bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(anchor="w")
        tk.Label(card, text="Entrez vos identifiants pour accéder au système",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(anchor="w", pady=(2, 20))

        # Serveur MySQL
        tk.Label(card, text="Serveur MySQL", font=FONTS["body"],
                 bg=COLORS["bg_card"], fg=COLORS["text_main"],
                 anchor="w").pack(fill="x")
        self._host_var = tk.StringVar(value="localhost")
        tk.Entry(card, textvariable=self._host_var, font=FONTS["body"],
                 relief="solid", bd=1, bg="#FAFAFA").pack(fill="x", pady=(2, 14), ipady=5)

        # Login
        tk.Label(card, text="Identifiant", font=FONTS["body"],
                 bg=COLORS["bg_card"], fg=COLORS["text_main"],
                 anchor="w").pack(fill="x")
        self._login_var = tk.StringVar()
        self._login_entry = tk.Entry(
            card, textvariable=self._login_var, font=FONTS["body"],
            relief="solid", bd=1, bg="#FAFAFA")
        self._login_entry.pack(fill="x", pady=(2, 14))

        # Mot de passe
        tk.Label(card, text="Mot de passe", font=FONTS["body"],
                 bg=COLORS["bg_card"], fg=COLORS["text_main"],
                 anchor="w").pack(fill="x")

        pw_frame = tk.Frame(card, bg=COLORS["bg_card"])
        pw_frame.pack(fill="x", pady=(2, 4))
        self._pw_var = tk.StringVar()
        self._pw_entry = tk.Entry(
            pw_frame, textvariable=self._pw_var, font=FONTS["body"],
            relief="solid", bd=1, bg="#FAFAFA", show="●")
        self._pw_entry.pack(side="left", fill="x", expand=True)

        self._show_pw = tk.BooleanVar(value=False)
        tk.Checkbutton(
            pw_frame, text="👁", variable=self._show_pw,
            command=self._toggle_pw, bg=COLORS["bg_card"],
            activebackground=COLORS["bg_card"], bd=0, cursor="hand2"
        ).pack(side="left", padx=(4, 0))

        # Message erreur
        self._err_lbl = tk.Label(card, text="", font=FONTS["small"],
                                  bg=COLORS["bg_card"], fg=COLORS["danger"])
        self._err_lbl.pack(anchor="w", pady=(4, 0))

        # Bouton connexion
        btn = tk.Button(
            card, text="  SE CONNECTER →", font=("Segoe UI", 12, "bold"),
            bg=COLORS["primary"], fg="white",
            relief="flat", bd=0, cursor="hand2",
            padx=20, pady=10,
            command=self._login,
            activebackground=COLORS["primary_dark"],
            activeforeground="white",
        )
        btn.pack(fill="x", pady=(16, 0))
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["primary_dark"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=COLORS["primary"]))

        # Comptes de démo
        tk.Frame(card, bg=COLORS["border"], height=1).pack(fill="x", pady=20)
        tk.Label(card, text="Comptes de démonstration :",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(anchor="w")

        demo_frame = tk.Frame(card, bg=COLORS["bg_main"], padx=10, pady=8)
        demo_frame.pack(fill="x", pady=(4, 0))
        demos = [
            ("admin", "admin123", "Administrateur"),
            ("gestionnaire", "gest123", "Gestionnaire"),
            ("caissier", "caisse123", "Caissier"),
        ]
        for login, pw, role in demos:
            row = tk.Frame(demo_frame, bg=COLORS["bg_main"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"• {role}:", font=FONTS["small"],
                     bg=COLORS["bg_main"], fg=COLORS["text_muted"],
                     width=14, anchor="w").pack(side="left")
            lnk = tk.Label(row,
                           text=f"{login} / {pw}",
                           font=("Segoe UI", 9, "underline"),
                           bg=COLORS["bg_main"], fg=COLORS["primary"],
                           cursor="hand2")
            lnk.pack(side="left")
            lnk.bind("<Button-1>", lambda e, l=login, p=pw: self._fill(l, p))

        tk.Label(right, bg=COLORS["bg_main"]).pack(expand=True)

        # Focus
        self._login_entry.focus_set()
        self._pw_entry.bind("<Return>", lambda e: self._login())
        self._login_entry.bind("<Return>", lambda e: self._pw_entry.focus())

    def _fill(self, login, pw):
        self._login_var.set(login)
        self._pw_var.set(pw)

    def _toggle_pw(self):
        self._pw_entry.config(show="" if self._show_pw.get() else "●")

    def _login(self):
        login = self._login_var.get().strip()
        pw    = self._pw_var.get().strip()
        host  = self._host_var.get().strip() or "localhost"

        if not login or not pw:
            self._err_lbl.config(text="⚠ Veuillez remplir tous les champs.")
            return

        # Mise à jour config
        DB_CONFIG["host"] = host

        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM utilisateurs WHERE login=%s AND statut='actif'",
                (login,)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and user["mot_de_passe"] == hash_password(pw):
                self._err_lbl.config(text="")
                self.destroy()
                self.on_success(user)
            else:
                self._err_lbl.config(text="❌ Identifiants incorrects.")
                self._pw_var.set("")

        except Exception as e:
            self._err_lbl.config(text=f"❌ Erreur DB : {e}")
