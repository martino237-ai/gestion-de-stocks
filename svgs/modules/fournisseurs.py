"""SVGS — Module Fournisseurs & Clients"""
import tkinter as tk
from tkinter import ttk
from constants import COLORS, FONTS
from database import get_connection
from widgets import StyledButton, DataTable, info_dialog, confirm_dialog


class FournisseursModule(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS["bg_main"])
        self.user = user
        self._sel_fourn = None
        self._sel_client = None
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["bg_main"])
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="🤝  Fournisseurs & Clients", font=FONTS["title"],
                 bg=COLORS["bg_main"], fg=COLORS["primary"]).pack(side="left")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=4)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=24, pady=4)

        t1 = tk.Frame(nb, bg=COLORS["bg_main"]); nb.add(t1, text="  Fournisseurs  ")
        t2 = tk.Frame(nb, bg=COLORS["bg_main"]); nb.add(t2, text="  Clients  ")

        self._build_fournisseurs(t1)
        self._build_clients(t2)

    def _build_fournisseurs(self, parent):
        parent.columnconfigure(0, weight=3); parent.columnconfigure(1, weight=2)
        parent.rowconfigure(0, weight=1)

        left = tk.Frame(parent, bg=COLORS["bg_card"], padx=14, pady=14)
        left.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        left.rowconfigure(1, weight=1); left.columnconfigure(0, weight=1)

        tb = tk.Frame(left, bg=COLORS["bg_card"])
        tb.grid(row=0, column=0, sticky="ew", pady=(0,8))
        StyledButton(tb, "➕ Nouveau", command=self._new_fourn, style="success").pack(side="left")
        StyledButton(tb, "↺ Actualiser", command=self._load_fournisseurs, style="outline").pack(side="right")

        self._fourn_table = DataTable(left, columns=[
            ("ID", 50, "center"), ("Raison sociale", 200, "w"),
            ("Contact", 120, "w"), ("Téléphone", 110, "w"), ("Email", 160, "w")
        ], height=18)
        self._fourn_table.grid(row=1, column=0, sticky="nsew")
        self._fourn_table.bind_select(self._on_fourn_select)

        right = tk.Frame(parent, bg=COLORS["bg_card"], padx=20, pady=20)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text="Fiche Fournisseur", font=FONTS["subtitle"],
                 bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(anchor="w", pady=(0,14))

        self._f_raison = tk.StringVar(); self._f_contact = tk.StringVar()
        self._f_tel = tk.StringVar(); self._f_email = tk.StringVar(); self._f_adresse = tk.StringVar()

        for lbl, var in [("Raison sociale *", self._f_raison), ("Contact", self._f_contact),
                          ("Téléphone", self._f_tel), ("Email", self._f_email), ("Adresse", self._f_adresse)]:
            f = tk.Frame(right, bg=COLORS["bg_card"]); f.pack(fill="x", pady=4)
            tk.Label(f, text=lbl, font=FONTS["small"], bg=COLORS["bg_card"],
                     fg=COLORS["text_muted"], width=16, anchor="w").pack(side="left")
            tk.Entry(f, textvariable=var, font=FONTS["body"], relief="solid", bd=1,
                     bg="#FAFAFA").pack(side="left", fill="x", expand=True, ipady=4)

        self._fourn_msg = tk.Label(right, text="", font=FONTS["small"], bg=COLORS["bg_card"])
        self._fourn_msg.pack(anchor="w", pady=4)

        if self.user["role"] in ("gestionnaire", "admin"):
            StyledButton(right, "💾 Enregistrer", command=self._save_fourn, style="success").pack(fill="x", pady=3)
            StyledButton(right, "🗑 Supprimer", command=self._del_fourn, style="danger").pack(fill="x", pady=3)
        StyledButton(right, "🆕 Nouveau", command=self._new_fourn, style="outline").pack(fill="x", pady=3)

        self._load_fournisseurs()

    def _load_fournisseurs(self):
        self._fourn_table.clear()
        try:
            conn = get_connection(); c = conn.cursor(dictionary=True)
            c.execute("SELECT * FROM fournisseurs ORDER BY raison_sociale")
            for r in c.fetchall():
                self._fourn_table.insert((r["id"], r["raison_sociale"], r["contact"] or "—",
                    r["telephone"] or "—", r["email"] or "—"))
            c.close(); conn.close()
        except Exception: pass

    def _on_fourn_select(self, e=None):
        vals = self._fourn_table.selected_values()
        if not vals: return
        fid = vals[0]
        try:
            conn = get_connection(); c = conn.cursor(dictionary=True)
            c.execute("SELECT * FROM fournisseurs WHERE id=%s", (fid,))
            r = c.fetchone(); c.close(); conn.close()
            if r:
                self._sel_fourn = r["id"]
                self._f_raison.set(r["raison_sociale"]); self._f_contact.set(r["contact"] or "")
                self._f_tel.set(r["telephone"] or ""); self._f_email.set(r["email"] or "")
                self._f_adresse.set(r["adresse"] or "")
        except Exception: pass

    def _new_fourn(self):
        self._sel_fourn = None
        for v in (self._f_raison, self._f_contact, self._f_tel, self._f_email, self._f_adresse):
            v.set("")

    def _save_fourn(self):
        raison = self._f_raison.get().strip()
        if not raison:
            self._fourn_msg.config(text="⚠ Raison sociale obligatoire.", fg=COLORS["warning"]); return
        try:
            conn = get_connection(); c = conn.cursor()
            if self._sel_fourn:
                c.execute("UPDATE fournisseurs SET raison_sociale=%s,contact=%s,telephone=%s,email=%s,adresse=%s WHERE id=%s",
                          (raison, self._f_contact.get(), self._f_tel.get(),
                           self._f_email.get(), self._f_adresse.get(), self._sel_fourn))
            else:
                c.execute("INSERT INTO fournisseurs (raison_sociale,contact,telephone,email,adresse) VALUES (%s,%s,%s,%s,%s)",
                          (raison, self._f_contact.get(), self._f_tel.get(),
                           self._f_email.get(), self._f_adresse.get()))
            conn.commit(); c.close(); conn.close()
            self._fourn_msg.config(text="✅ Enregistré.", fg=COLORS["success"])
            self._load_fournisseurs()
        except Exception as e:
            self._fourn_msg.config(text=f"❌ {e}", fg=COLORS["danger"])

    def _del_fourn(self):
        if not self._sel_fourn:
            info_dialog(self, "Sélection requise", "Sélectionnez un fournisseur.", kind="warning"); return
        if confirm_dialog(self, "Supprimer", "Supprimer ce fournisseur ?"):
            try:
                conn = get_connection(); c = conn.cursor()
                c.execute("DELETE FROM fournisseurs WHERE id=%s", (self._sel_fourn,))
                conn.commit(); c.close(); conn.close()
                self._new_fourn(); self._load_fournisseurs()
            except Exception as e:
                info_dialog(self, "Erreur", str(e), kind="error")

    def _build_clients(self, parent):
        parent.columnconfigure(0, weight=3); parent.columnconfigure(1, weight=2)
        parent.rowconfigure(0, weight=1)

        left = tk.Frame(parent, bg=COLORS["bg_card"], padx=14, pady=14)
        left.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        left.rowconfigure(1, weight=1); left.columnconfigure(0, weight=1)

        tb = tk.Frame(left, bg=COLORS["bg_card"])
        tb.grid(row=0, column=0, sticky="ew", pady=(0,8))
        StyledButton(tb, "➕ Nouveau client", command=self._new_client, style="success").pack(side="left")
        StyledButton(tb, "↺ Actualiser", command=self._load_clients, style="outline").pack(side="right")

        self._client_table = DataTable(left, columns=[
            ("ID", 50, "center"), ("Nom", 120, "w"), ("Prénom", 100, "w"),
            ("Téléphone", 110, "w"), ("Solde dû", 110, "e"), ("Inscrit le", 110, "center")
        ], height=18)
        self._client_table.grid(row=1, column=0, sticky="nsew")
        self._client_table.bind_select(self._on_client_select)

        right = tk.Frame(parent, bg=COLORS["bg_card"], padx=20, pady=20)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text="Fiche Client", font=FONTS["subtitle"],
                 bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(anchor="w", pady=(0,14))

        self._c_nom = tk.StringVar(); self._c_prenom = tk.StringVar()
        self._c_tel = tk.StringVar(); self._c_adresse = tk.StringVar()
        self._c_solde = tk.StringVar(value="0")

        for lbl, var in [("Nom *", self._c_nom), ("Prénom", self._c_prenom),
                          ("Téléphone", self._c_tel), ("Adresse", self._c_adresse)]:
            f = tk.Frame(right, bg=COLORS["bg_card"]); f.pack(fill="x", pady=4)
            tk.Label(f, text=lbl, font=FONTS["small"], bg=COLORS["bg_card"],
                     fg=COLORS["text_muted"], width=14, anchor="w").pack(side="left")
            tk.Entry(f, textvariable=var, font=FONTS["body"], relief="solid", bd=1,
                     bg="#FAFAFA").pack(side="left", fill="x", expand=True, ipady=4)

        f_solde = tk.Frame(right, bg=COLORS["bg_card"]); f_solde.pack(fill="x", pady=4)
        tk.Label(f_solde, text="Solde dû (F)", font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["danger"], width=14, anchor="w").pack(side="left")
        tk.Entry(f_solde, textvariable=self._c_solde, font=FONTS["body"],
                 relief="solid", bd=1, bg="#FFF3F3").pack(side="left", fill="x", expand=True, ipady=4)

        self._client_msg = tk.Label(right, text="", font=FONTS["small"], bg=COLORS["bg_card"])
        self._client_msg.pack(anchor="w", pady=4)

        StyledButton(right, "💾 Enregistrer", command=self._save_client, style="success").pack(fill="x", pady=3)
        StyledButton(right, "🆕 Nouveau", command=self._new_client, style="outline").pack(fill="x", pady=3)

        self._load_clients()

    def _load_clients(self):
        self._client_table.clear()
        try:
            conn = get_connection(); c = conn.cursor(dictionary=True)
            c.execute("SELECT * FROM clients ORDER BY nom")
            for r in c.fetchall():
                tag = "warning" if float(r["solde_du"]) > 0 else ""
                self._client_table.insert((r["id"], r["nom"], r["prenom"] or "—",
                    r["telephone"] or "—",
                    f"{int(r['solde_du']):,} F".replace(",", " "),
                    r["created_at"].strftime("%d/%m/%Y") if r["created_at"] else "—"), tag=tag)
            c.close(); conn.close()
        except Exception: pass

    def _on_client_select(self, e=None):
        vals = self._client_table.selected_values()
        if not vals: return
        cid = vals[0]
        try:
            conn = get_connection(); c = conn.cursor(dictionary=True)
            c.execute("SELECT * FROM clients WHERE id=%s", (cid,))
            r = c.fetchone(); c.close(); conn.close()
            if r:
                self._sel_client = r["id"]
                self._c_nom.set(r["nom"]); self._c_prenom.set(r["prenom"] or "")
                self._c_tel.set(r["telephone"] or ""); self._c_adresse.set(r["adresse"] or "")
                self._c_solde.set(str(r["solde_du"]))
        except Exception: pass

    def _new_client(self):
        self._sel_client = None
        for v in (self._c_nom, self._c_prenom, self._c_tel, self._c_adresse):
            v.set("")
        self._c_solde.set("0")

    def _save_client(self):
        nom = self._c_nom.get().strip()
        if not nom:
            self._client_msg.config(text="⚠ Nom obligatoire.", fg=COLORS["warning"]); return
        try:
            solde = float(self._c_solde.get() or 0)
        except ValueError:
            solde = 0
        try:
            conn = get_connection(); c = conn.cursor()
            if self._sel_client:
                c.execute("UPDATE clients SET nom=%s,prenom=%s,telephone=%s,adresse=%s,solde_du=%s WHERE id=%s",
                          (nom, self._c_prenom.get(), self._c_tel.get(),
                           self._c_adresse.get(), solde, self._sel_client))
            else:
                c.execute("INSERT INTO clients (nom,prenom,telephone,adresse,solde_du) VALUES (%s,%s,%s,%s,%s)",
                          (nom, self._c_prenom.get(), self._c_tel.get(), self._c_adresse.get(), solde))
            conn.commit(); c.close(); conn.close()
            self._client_msg.config(text="✅ Enregistré.", fg=COLORS["success"])
            self._load_clients()
        except Exception as e:
            self._client_msg.config(text=f"❌ {e}", fg=COLORS["danger"])
