"""
SVGS — Module Gestion des Stocks
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from constants import COLORS, FONTS
from database import get_connection
from widgets import (StyledButton, DataTable, SectionHeader,
                     SearchBar, info_dialog, confirm_dialog)


class StockModule(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS["bg_main"])
        self.user = user
        self._articles_cache = []
        self._build()
        self.load_data()

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["bg_main"])
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="📦  Gestion des Stocks",
                 font=FONTS["title"], bg=COLORS["bg_main"],
                 fg=COLORS["primary"]).pack(side="left")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=4)

        # Notebook pour les sous-onglets
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=24, pady=4)

        # Onglet 1 : Niveaux de stock
        tab1 = tk.Frame(nb, bg=COLORS["bg_main"])
        nb.add(tab1, text="  Niveaux de stock  ")
        self._build_niveaux(tab1)

        # Onglet 2 : Entrée de stock
        tab2 = tk.Frame(nb, bg=COLORS["bg_main"])
        nb.add(tab2, text="  Entrée de stock  ")
        self._build_entree(tab2)

        # Onglet 3 : Historique mouvements
        tab3 = tk.Frame(nb, bg=COLORS["bg_main"])
        nb.add(tab3, text="  Historique des mouvements  ")
        self._build_historique(tab3)

        # Onglet 4 : Inventaire
        tab4 = tk.Frame(nb, bg=COLORS["bg_main"])
        nb.add(tab4, text="  Inventaire  ")
        self._build_inventaire(tab4)

    # ─── Onglet 1 : Niveaux de stock ─────────────────────────────────────────
    def _build_niveaux(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        toolbar = tk.Frame(parent, bg=COLORS["bg_main"])
        toolbar.grid(row=0, column=0, sticky="ew", pady=8)

        self._niv_search = SearchBar(toolbar, command=self._search_niveaux)
        self._niv_search.pack(side="left")

        self._niv_filtre = tk.StringVar(value="Tous")
        ttk.Combobox(toolbar, textvariable=self._niv_filtre,
                     values=["Tous", "En alerte", "En rupture", "OK"],
                     state="readonly", width=14, font=FONTS["body"]).pack(side="left", padx=8)
        self._niv_filtre.trace("w", lambda *a: self.load_data())

        StyledButton(toolbar, "↺ Actualiser", command=self.load_data,
                     style="outline").pack(side="right")

        self._niv_table = DataTable(
            parent,
            columns=[
                ("Code",        80, "w"),
                ("Désignation", 220, "w"),
                ("Catégorie",   110, "w"),
                ("Stock actuel", 100, "e"),
                ("Réservé",      80, "e"),
                ("Seuil alerte", 100, "center"),
                ("Statut",       120, "center"),
                ("Mise à jour",  120, "center"),
            ],
            height=20
        )
        self._niv_table.grid(row=1, column=0, sticky="nsew")

    def load_data(self, *_):
        self._load_articles_cache()
        self._niv_table.clear()
        filtre = self._niv_filtre.get()
        search = self._niv_search.get()

        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)

            where = ["a.statut='actif'"]
            params = []

            if filtre == "En alerte":
                where.append("s.quantite_actuelle <= a.seuil_alerte AND s.quantite_actuelle > 0")
            elif filtre == "En rupture":
                where.append("s.quantite_actuelle = 0")
            elif filtre == "OK":
                where.append("s.quantite_actuelle > a.seuil_alerte")

            if search:
                where.append("(a.code LIKE %s OR a.designation LIKE %s)")
                params += [f"%{search}%", f"%{search}%"]

            cursor.execute(f"""
                SELECT a.code, a.designation, c.libelle AS cat,
                       s.quantite_actuelle, s.quantite_reservee,
                       a.seuil_alerte, s.date_maj, a.unite
                FROM stocks s
                JOIN articles a ON a.id = s.article_id
                LEFT JOIN categories c ON c.id = a.categorie_id
                WHERE {' AND '.join(where)}
                ORDER BY (s.quantite_actuelle / GREATEST(a.seuil_alerte,1)) ASC
            """, params)

            for r in cursor.fetchall():
                qte   = float(r["quantite_actuelle"])
                seuil = r["seuil_alerte"]

                if qte == 0:
                    tag, status = "danger", "🔴 RUPTURE"
                elif qte <= seuil:
                    tag, status = "warning", "🟠 FAIBLE"
                else:
                    tag, status = "success", "🟢 OK"

                maj = r["date_maj"].strftime("%d/%m %H:%M") if r["date_maj"] else "—"

                self._niv_table.insert((
                    r["code"], r["designation"], r["cat"] or "—",
                    f"{qte:.1f} {r['unite']}",
                    f"{r['quantite_reservee']:.1f}",
                    seuil, status, maj
                ), tag=tag)

            cursor.close(); conn.close()
        except Exception as e:
            pass

    def _search_niveaux(self, term):
        self.load_data()

    # ─── Onglet 2 : Entrée de stock ───────────────────────────────────────────
    def _build_entree(self, parent):
        if self.user["role"] not in ("gestionnaire", "admin"):
            tk.Label(parent, text="⛔ Accès réservé aux gestionnaires et administrateurs.",
                     font=FONTS["subtitle"], bg=COLORS["bg_main"],
                     fg=COLORS["danger"]).pack(expand=True)
            return

        frm = tk.Frame(parent, bg=COLORS["bg_card"], padx=30, pady=30)
        frm.pack(padx=40, pady=20, fill="x")

        tk.Label(frm, text="➕  Entrée de stock fournisseur",
                 font=FONTS["subtitle"], bg=COLORS["bg_card"],
                 fg=COLORS["primary"]).pack(anchor="w", pady=(0, 16))

        def row(label):
            f = tk.Frame(frm, bg=COLORS["bg_card"])
            f.pack(fill="x", pady=5)
            tk.Label(f, text=label, font=FONTS["body"],
                     bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                     width=20, anchor="w").pack(side="left")
            return f

        # Article
        r1 = row("Article *")
        self._e_art = tk.StringVar()
        self._e_art_combo = ttk.Combobox(r1, textvariable=self._e_art,
                                          font=FONTS["body"], width=30)
        self._e_art_combo.pack(side="left", padx=4)

        # Quantité
        r2 = row("Quantité *")
        self._e_qte = tk.StringVar()
        tk.Entry(r2, textvariable=self._e_qte, font=FONTS["body"],
                 width=12, relief="solid", bd=1).pack(side="left", padx=4, ipady=4)

        # Prix achat
        r3 = row("Prix achat unitaire")
        self._e_prix = tk.StringVar()
        tk.Entry(r3, textvariable=self._e_prix, font=FONTS["body"],
                 width=12, relief="solid", bd=1).pack(side="left", padx=4, ipady=4)

        # Motif / référence BL
        r4 = row("Référence BL / motif")
        self._e_motif = tk.StringVar()
        tk.Entry(r4, textvariable=self._e_motif, font=FONTS["body"],
                 width=30, relief="solid", bd=1).pack(side="left", padx=4, ipady=4)

        # Fournisseur
        r5 = row("Fournisseur")
        self._e_fourn = tk.StringVar()
        self._e_fourn_combo = ttk.Combobox(r5, textvariable=self._e_fourn,
                                            font=FONTS["body"], width=25)
        self._e_fourn_combo.pack(side="left", padx=4)

        self._msg_entree = tk.Label(frm, text="", font=FONTS["body"],
                                     bg=COLORS["bg_card"])
        self._msg_entree.pack(anchor="w", pady=6)

        StyledButton(frm, "✅ Valider l'entrée de stock",
                     command=self._valider_entree, style="success",
                     width=30).pack(pady=8)

        self._load_articles_cache()
        self._load_fournisseurs()

    def _load_articles_cache(self):
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.id, a.code, a.designation
                FROM articles a WHERE a.statut='actif'
                ORDER BY a.designation
            """)
            self._articles_cache = cursor.fetchall()
            cursor.close(); conn.close()

            names = [f"{a['code']} — {a['designation']}" for a in self._articles_cache]
            if hasattr(self, "_e_art_combo"):
                self._e_art_combo.config(values=names)
        except Exception:
            pass

    def _load_fournisseurs(self):
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, raison_sociale FROM fournisseurs ORDER BY raison_sociale")
            self._fourns = cursor.fetchall()
            cursor.close(); conn.close()
            names = [r[1] for r in self._fourns]
            if hasattr(self, "_e_fourn_combo"):
                self._e_fourn_combo.config(values=names)
        except Exception:
            pass

    def _valider_entree(self):
        art_str = self._e_art.get().strip()
        qte_str = self._e_qte.get().strip()
        motif   = self._e_motif.get().strip()

        if not art_str or not qte_str:
            self._msg_entree.config(text="⚠ Article et quantité obligatoires.",
                                     fg=COLORS["warning"])
            return
        try:
            qte = float(qte_str)
            if qte <= 0: raise ValueError
        except ValueError:
            self._msg_entree.config(text="⚠ Quantité invalide.", fg=COLORS["warning"])
            return

        # Retrouver l'article
        art = None
        for a in self._articles_cache:
            if f"{a['code']} — {a['designation']}" == art_str:
                art = a; break
        if not art:
            self._msg_entree.config(text="⚠ Article non trouvé.", fg=COLORS["warning"])
            return

        prix_str = self._e_prix.get().strip()
        prix = float(prix_str) if prix_str else None

        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE stocks SET quantite_actuelle = quantite_actuelle + %s
                WHERE article_id = %s
            """, (qte, art["id"]))
            cursor.execute("""
                INSERT INTO mouvements_stock
                (article_id, type_mvt, quantite, prix_unitaire, motif, user_id)
                VALUES (%s,'ENTREE',%s,%s,%s,%s)
            """, (art["id"], qte, prix, motif or "Réception fournisseur", self.user["id"]))
            conn.commit()
            cursor.close(); conn.close()
            self._msg_entree.config(
                text=f"✅ {qte:.0f} unité(s) de '{art['designation']}' ajoutée(s).",
                fg=COLORS["success"])
            self._e_qte.set("")
            self._e_prix.set("")
            self._e_motif.set("")
            self.load_data()
        except Exception as e:
            self._msg_entree.config(text=f"❌ Erreur : {e}", fg=COLORS["danger"])

    # ─── Onglet 3 : Historique mouvements ────────────────────────────────────
    def _build_historique(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        toolbar = tk.Frame(parent, bg=COLORS["bg_main"])
        toolbar.grid(row=0, column=0, sticky="ew", pady=8)

        self._mvt_type = tk.StringVar(value="Tous")
        ttk.Combobox(toolbar, textvariable=self._mvt_type,
                     values=["Tous", "ENTREE", "SORTIE", "INVENTAIRE", "CORRECTION"],
                     state="readonly", width=14, font=FONTS["body"]).pack(side="left", padx=4)
        self._mvt_type.trace("w", lambda *a: self._load_historique())

        StyledButton(toolbar, "↺ Actualiser", command=self._load_historique,
                     style="outline").pack(side="right")

        self._mvt_table = DataTable(
            parent,
            columns=[
                ("Date",        130, "center"),
                ("Type",         90, "center"),
                ("Article",     200, "w"),
                ("Quantité",     90, "e"),
                ("Prix unit.",   90, "e"),
                ("Référence",   130, "w"),
                ("Utilisateur",  120, "w"),
                ("Motif",        180, "w"),
            ],
            height=20
        )
        self._mvt_table.grid(row=1, column=0, sticky="nsew")
        self._load_historique()

    def _load_historique(self):
        self._mvt_table.clear()
        filtre = self._mvt_type.get()
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            where  = "1=1"
            params = []
            if filtre != "Tous":
                where = "m.type_mvt=%s"
                params.append(filtre)
            cursor.execute(f"""
                SELECT m.created_at, m.type_mvt, a.designation,
                       m.quantite, m.prix_unitaire, m.reference,
                       u.nom, m.motif
                FROM mouvements_stock m
                JOIN articles a    ON a.id = m.article_id
                LEFT JOIN utilisateurs u ON u.id = m.user_id
                WHERE {where}
                ORDER BY m.created_at DESC LIMIT 200
            """, params)
            for r in cursor.fetchall():
                tag = "success" if r["type_mvt"] == "ENTREE" else \
                      "danger"  if r["type_mvt"] == "SORTIE" else ""
                icon = {"ENTREE": "⬆", "SORTIE": "⬇",
                        "INVENTAIRE": "🔄", "CORRECTION": "✏"}.get(r["type_mvt"], "")
                self._mvt_table.insert((
                    r["created_at"].strftime("%d/%m/%Y %H:%M"),
                    f"{icon} {r['type_mvt']}",
                    r["designation"],
                    f"{r['quantite']:.1f}",
                    f"{int(r['prix_unitaire']):,} F".replace(",", " ") if r["prix_unitaire"] else "—",
                    r["reference"] or "—",
                    r["nom"] or "—",
                    r["motif"] or "—",
                ), tag=tag)
            cursor.close(); conn.close()
        except Exception:
            pass

    # ─── Onglet 4 : Inventaire ────────────────────────────────────────────────
    def _build_inventaire(self, parent):
        if self.user["role"] not in ("gestionnaire", "admin"):
            tk.Label(parent, text="⛔ Accès réservé aux gestionnaires.",
                     font=FONTS["subtitle"], bg=COLORS["bg_main"],
                     fg=COLORS["danger"]).pack(expand=True)
            return

        top = tk.Frame(parent, bg=COLORS["bg_main"])
        top.pack(fill="x", pady=8)
        tk.Label(top, text="Saisie de l'inventaire physique",
                 font=FONTS["heading"], bg=COLORS["bg_main"],
                 fg=COLORS["primary"]).pack(side="left")
        StyledButton(top, "↺ Charger les articles",
                     command=self._load_inventaire, style="primary").pack(side="right")
        StyledButton(top, "💾 Valider l'inventaire",
                     command=self._save_inventaire, style="success").pack(side="right", padx=8)

        tk.Label(parent,
                 text="Saisissez les quantités physiques réelles. "
                      "Les écarts seront enregistrés automatiquement.",
                 font=FONTS["small"], bg=COLORS["bg_main"],
                 fg=COLORS["text_muted"]).pack(anchor="w")

        self._inv_frame = tk.Frame(parent, bg=COLORS["bg_main"])
        self._inv_frame.pack(fill="both", expand=True, pady=8)
        self._inv_rows = []

    def _load_inventaire(self):
        for w in self._inv_frame.winfo_children():
            w.destroy()
        self._inv_rows = []

        # En-tête
        hdr = tk.Frame(self._inv_frame, bg=COLORS["primary"])
        hdr.pack(fill="x")
        for txt, w in [("Code", 80), ("Article", 220), ("Stock théorique", 110),
                       ("Qté physique réelle", 150), ("Écart", 80)]:
            tk.Label(hdr, text=txt, font=FONTS["heading"], bg=COLORS["primary"],
                     fg="white", width=w//7, pady=6).pack(side="left", padx=2)

        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.id, a.code, a.designation, s.quantite_actuelle, a.unite
                FROM articles a JOIN stocks s ON s.article_id = a.id
                WHERE a.statut='actif' ORDER BY a.designation
            """)
            rows = cursor.fetchall()
            cursor.close(); conn.close()

            canvas = tk.Canvas(self._inv_frame, bg=COLORS["bg_main"],
                               highlightthickness=0)
            sb = ttk.Scrollbar(self._inv_frame, command=canvas.yview)
            canvas.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            rows_frame = tk.Frame(canvas, bg=COLORS["bg_main"])
            canvas.create_window((0, 0), window=rows_frame, anchor="nw")
            rows_frame.bind("<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

            for i, r in enumerate(rows):
                bg = "#F8F9FF" if i % 2 == 0 else "white"
                row_f = tk.Frame(rows_frame, bg=bg, pady=3)
                row_f.pack(fill="x", padx=2, pady=1)

                tk.Label(row_f, text=r["code"], font=FONTS["small"],
                         bg=bg, width=11).pack(side="left", padx=2)
                tk.Label(row_f, text=r["designation"][:30], font=FONTS["body"],
                         bg=bg, anchor="w", width=28).pack(side="left", padx=2)
                tk.Label(row_f,
                         text=f"{r['quantite_actuelle']:.1f} {r['unite']}",
                         font=FONTS["body"], bg=bg, width=14).pack(side="left", padx=2)

                qte_var = tk.StringVar(value=f"{r['quantite_actuelle']:.1f}")
                e = tk.Entry(row_f, textvariable=qte_var, font=FONTS["body"],
                             width=12, relief="solid", bd=1)
                e.pack(side="left", padx=4, ipady=3)

                ecart_lbl = tk.Label(row_f, text="0", font=FONTS["body"], bg=bg, width=8)
                ecart_lbl.pack(side="left", padx=2)

                def update_ecart(var=qte_var, theorique=r["quantite_actuelle"],
                                  lbl=ecart_lbl):
                    try:
                        reel  = float(var.get())
                        ecart = reel - theorique
                        lbl.config(
                            text=f"{ecart:+.1f}",
                            fg=COLORS["success"] if ecart >= 0 else COLORS["danger"])
                    except ValueError:
                        lbl.config(text="?", fg=COLORS["warning"])

                qte_var.trace("w", lambda *a, f=update_ecart: f())
                self._inv_rows.append({"article_id": r["id"], "theorique": r["quantite_actuelle"],
                                        "var": qte_var, "designation": r["designation"]})
        except Exception as e:
            tk.Label(self._inv_frame, text=str(e)).pack()

    def _save_inventaire(self):
        if not self._inv_rows:
            info_dialog(self, "Inventaire vide",
                        "Chargez d'abord les articles.", kind="warning")
            return
        if not confirm_dialog(self, "Valider l'inventaire",
                              "Enregistrer les quantités réelles ?\nLes écarts seront tracés."):
            return
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            for r in self._inv_rows:
                try:
                    reel  = float(r["var"].get())
                    ecart = reel - r["theorique"]
                    if abs(ecart) > 0.001:
                        cursor.execute("""
                            UPDATE stocks SET quantite_actuelle=%s
                            WHERE article_id=%s
                        """, (reel, r["article_id"]))
                        cursor.execute("""
                            INSERT INTO mouvements_stock
                            (article_id, type_mvt, quantite, motif, user_id)
                            VALUES (%s,'INVENTAIRE',%s,%s,%s)
                        """, (r["article_id"], abs(ecart),
                              f"Inventaire physique — écart {ecart:+.1f}",
                              self.user["id"]))
                except ValueError:
                    pass
            conn.commit()
            cursor.close(); conn.close()
            info_dialog(self, "Succès", "Inventaire enregistré avec succès.", kind="success")
            self.load_data()
        except Exception as e:
            info_dialog(self, "Erreur", str(e), kind="error")
