"""
SVGS — Module Gestion des Utilisateurs
"""
import tkinter as tk
from tkinter import ttk
from constants import COLORS, FONTS, ROLES
from database import get_connection, hash_password
from widgets import (StyledButton, DataTable, info_dialog, confirm_dialog)


class UtilisateursModule(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS["bg_main"])
        self.user = user
        self._selected_id = None
        self._build()
        self.load_data()

    def _build(self):
        if self.user["role"] != "admin":
            tk.Label(self, text="⛔  Accès réservé aux administrateurs.",
                     font=FONTS["subtitle"], bg=COLORS["bg_main"],
                     fg=COLORS["danger"]).pack(expand=True)
            return

        hdr = tk.Frame(self, bg=COLORS["bg_main"])
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="👥  Gestion des Utilisateurs",
                 font=FONTS["title"], bg=COLORS["bg_main"],
                 fg=COLORS["primary"]).pack(side="left")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=4)

        body = tk.Frame(self, bg=COLORS["bg_main"])
        body.pack(fill="both", expand=True, padx=24, pady=4)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=COLORS["bg_card"], padx=14, pady=14)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        toolbar = tk.Frame(left, bg=COLORS["bg_card"])
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        StyledButton(toolbar, "➕ Nouvel utilisateur", command=self._new_form, style="success").pack(side="left")
        StyledButton(toolbar, "↺ Actualiser", command=self.load_data, style="outline").pack(side="right")

        self.table = DataTable(left, columns=[
            ("ID", 50, "center"), ("Nom", 130, "w"), ("Prénom", 130, "w"),
            ("Login", 100, "w"), ("Rôle", 120, "center"), ("Statut", 90, "center"), ("Créé le", 120, "center"),
        ], height=18)
        self.table.grid(row=1, column=0, sticky="nsew")
        self.table.bind_select(self._on_select)

        right = tk.Frame(body, bg=COLORS["bg_card"], padx=20, pady=20)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(right, text="Fiche Utilisateur", font=FONTS["subtitle"],
                 bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(anchor="w", pady=(0, 14))

        self._v_nom    = tk.StringVar()
        self._v_prenom = tk.StringVar()
        self._v_login  = tk.StringVar()
        self._v_pw     = tk.StringVar()
        self._v_role   = tk.StringVar(value="caissier")
        self._v_statut = tk.StringVar(value="actif")

        def field(label, var, show=""):
            f = tk.Frame(right, bg=COLORS["bg_card"])
            f.pack(fill="x", pady=4)
            tk.Label(f, text=label, font=FONTS["small"], bg=COLORS["bg_card"],
                     fg=COLORS["text_muted"], width=16, anchor="w").pack(side="left")
            tk.Entry(f, textvariable=var, font=FONTS["body"], relief="solid", bd=1,
                     bg="#FAFAFA", show=show).pack(side="left", fill="x", expand=True, ipady=4)

        field("Nom *", self._v_nom)
        field("Prénom *", self._v_prenom)
        field("Login *", self._v_login)
        field("Mot de passe", self._v_pw, show="●")
        tk.Label(right, text="(laisser vide pour ne pas changer)", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="e", pady=(0, 4))

        role_row = tk.Frame(right, bg=COLORS["bg_card"])
        role_row.pack(fill="x", pady=4)
        tk.Label(role_row, text="Rôle *", font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"], width=16, anchor="w").pack(side="left")
        ttk.Combobox(role_row, textvariable=self._v_role, values=list(ROLES.keys()),
                     state="readonly", font=FONTS["body"]).pack(side="left", fill="x", expand=True)

        stat_row = tk.Frame(right, bg=COLORS["bg_card"])
        stat_row.pack(fill="x", pady=4)
        tk.Label(stat_row, text="Statut", font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"], width=16, anchor="w").pack(side="left")
        ttk.Combobox(stat_row, textvariable=self._v_statut, values=["actif", "inactif"],
                     state="readonly", font=FONTS["body"]).pack(side="left", fill="x", expand=True)

        self._msg = tk.Label(right, text="", font=FONTS["small"], bg=COLORS["bg_card"])
        self._msg.pack(anchor="w", pady=4)

        btn_f = tk.Frame(right, bg=COLORS["bg_card"])
        btn_f.pack(fill="x", pady=8)
        StyledButton(btn_f, "💾 Enregistrer", command=self._save, style="success").pack(fill="x", pady=3)
        StyledButton(btn_f, "🆕 Nouveau", command=self._new_form, style="outline").pack(fill="x", pady=3)
        StyledButton(btn_f, "🗑 Désactiver", command=self._deactivate, style="danger").pack(fill="x", pady=3)

        tk.Frame(right, bg=COLORS["border"], height=1).pack(fill="x", pady=12)
        tk.Label(right, text="Réinitialisation du mot de passe", font=FONTS["heading"],
                 bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(anchor="w")
        self._v_new_pw = tk.StringVar()
        pw_row = tk.Frame(right, bg=COLORS["bg_card"])
        pw_row.pack(fill="x", pady=6)
        tk.Entry(pw_row, textvariable=self._v_new_pw, font=FONTS["body"],
                 show="●", relief="solid", bd=1).pack(side="left", fill="x", expand=True, ipady=4)
        StyledButton(pw_row, "✅ Réinitialiser", command=self._reset_password,
                     style="warning").pack(side="left", padx=6)

    def load_data(self, *_):
        if self.user["role"] != "admin":
            return
        self.table.clear()
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nom, prenom, login, role, statut, created_at FROM utilisateurs ORDER BY nom")
            for r in cursor.fetchall():
                statut = "✅ Actif" if r["statut"] == "actif" else "⛔ Inactif"
                tag = "" if r["statut"] == "actif" else "warning"
                self.table.insert((r["id"], r["nom"], r["prenom"], r["login"],
                    ROLES.get(r["role"], r["role"]), statut,
                    r["created_at"].strftime("%d/%m/%Y") if r["created_at"] else "—"), tag=tag)
            cursor.close(); conn.close()
        except Exception:
            pass

    def _on_select(self, e=None):
        vals = self.table.selected_values()
        if not vals:
            return
        uid = vals[0]
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM utilisateurs WHERE id=%s", (uid,))
            r = cursor.fetchone()
            cursor.close(); conn.close()
            if r:
                self._selected_id = r["id"]
                self._v_nom.set(r["nom"]); self._v_prenom.set(r["prenom"])
                self._v_login.set(r["login"]); self._v_pw.set("")
                self._v_role.set(r["role"]); self._v_statut.set(r["statut"])
                self._msg.config(text="")
        except Exception:
            pass

    def _new_form(self):
        self._selected_id = None
        for v in (self._v_nom, self._v_prenom, self._v_login, self._v_pw):
            v.set("")
        self._v_role.set("caissier"); self._v_statut.set("actif")
        self._msg.config(text="")

    def _save(self):
        nom = self._v_nom.get().strip(); prenom = self._v_prenom.get().strip()
        login = self._v_login.get().strip(); pw = self._v_pw.get().strip()
        role = self._v_role.get(); statut = self._v_statut.get()
        if not nom or not prenom or not login:
            self._msg.config(text="⚠ Nom, prénom et login obligatoires.", fg=COLORS["warning"]); return
        try:
            conn = get_connection(); cursor = conn.cursor()
            if self._selected_id:
                if pw:
                    cursor.execute("UPDATE utilisateurs SET nom=%s,prenom=%s,login=%s,mot_de_passe=%s,role=%s,statut=%s WHERE id=%s",
                                   (nom, prenom, login, hash_password(pw), role, statut, self._selected_id))
                else:
                    cursor.execute("UPDATE utilisateurs SET nom=%s,prenom=%s,login=%s,role=%s,statut=%s WHERE id=%s",
                                   (nom, prenom, login, role, statut, self._selected_id))
            else:
                if not pw:
                    self._msg.config(text="⚠ Mot de passe obligatoire.", fg=COLORS["warning"]); return
                cursor.execute("INSERT INTO utilisateurs (nom,prenom,login,mot_de_passe,role,statut) VALUES (%s,%s,%s,%s,%s,%s)",
                               (nom, prenom, login, hash_password(pw), role, statut))
            conn.commit(); cursor.close(); conn.close()
            self._msg.config(text="✅ Enregistré.", fg=COLORS["success"])
            self.load_data()
        except Exception as e:
            self._msg.config(text=f"❌ {e}", fg=COLORS["danger"])

    def _deactivate(self):
        if not self._selected_id:
            info_dialog(self, "Sélection requise", "Sélectionnez un utilisateur.", kind="warning"); return
        if self._selected_id == self.user["id"]:
            info_dialog(self, "Impossible", "Vous ne pouvez pas vous désactiver.", kind="error"); return
        if confirm_dialog(self, "Désactiver", f"Désactiver '{self._v_login.get()}' ?"):
            try:
                conn = get_connection(); c = conn.cursor()
                c.execute("UPDATE utilisateurs SET statut='inactif' WHERE id=%s", (self._selected_id,))
                conn.commit(); c.close(); conn.close(); self.load_data(); self._new_form()
            except Exception as e:
                info_dialog(self, "Erreur", str(e), kind="error")

    def _reset_password(self):
        if not self._selected_id:
            info_dialog(self, "Sélection requise", "Sélectionnez un utilisateur.", kind="warning"); return
        new_pw = self._v_new_pw.get().strip()
        if not new_pw or len(new_pw) < 4:
            info_dialog(self, "Invalide", "Minimum 4 caractères.", kind="warning"); return
        if confirm_dialog(self, "Réinitialiser", f"Nouveau mot de passe pour '{self._v_login.get()}' ?"):
            try:
                conn = get_connection(); c = conn.cursor()
                c.execute("UPDATE utilisateurs SET mot_de_passe=%s WHERE id=%s",
                          (hash_password(new_pw), self._selected_id))
                conn.commit(); c.close(); conn.close()
                self._v_new_pw.set("")
                info_dialog(self, "Succès", "Mot de passe réinitialisé.", kind="success")
            except Exception as e:
                info_dialog(self, "Erreur", str(e), kind="error")
