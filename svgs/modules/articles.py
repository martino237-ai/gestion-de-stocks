"""
SVGS — Module Gestion des Articles
"""
import tkinter as tk
from tkinter import ttk, messagebox
from constants import COLORS, FONTS
from database import get_connection
from widgets import (StyledButton, DataTable, LabeledEntry,
                     LabeledCombo, SectionHeader, SearchBar,
                     confirm_dialog, info_dialog)


class ArticlesModule(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS["bg_main"])
        self.user = user
        self._categories = []
        self._selected_id = None
        self._build()
        self.load_data()

    def _build(self):
        # ── Titre ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=COLORS["bg_main"])
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="📦  Gestion des Articles",
                 font=FONTS["title"], bg=COLORS["bg_main"],
                 fg=COLORS["primary"]).pack(side="left")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=4)

        # ── Corps principal ───────────────────────────────────────────────
        body = tk.Frame(self, bg=COLORS["bg_main"])
        body.pack(fill="both", expand=True, padx=24, pady=4)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # ── Panneau gauche : tableau ──────────────────────────────────────
        left = tk.Frame(body, bg=COLORS["bg_card"], padx=14, pady=14)
        left.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        # Barre d'outils
        toolbar = tk.Frame(left, bg=COLORS["bg_card"])
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0,8))

        self.search = SearchBar(toolbar, command=self._search)
        self.search.pack(side="left")

        can_edit = self.user["role"] in ("gestionnaire", "admin")

        if can_edit:
            StyledButton(toolbar, "➕ Nouveau", command=self._new_form,
                         style="success").pack(side="right", padx=4)
            StyledButton(toolbar, "🗑 Désactiver", command=self._deactivate,
                         style="danger").pack(side="right", padx=4)

        StyledButton(toolbar, "↺ Actualiser", command=self.load_data,
                     style="outline").pack(side="right", padx=4)

        # Filtre catégorie
        cat_frame = tk.Frame(left, bg=COLORS["bg_card"])
        cat_frame.grid(row=1, column=0, sticky="ew", pady=(0,6))
        tk.Label(cat_frame, text="Filtrer :", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left")
        self._cat_filter = tk.StringVar(value="Toutes")
        self._cat_combo = ttk.Combobox(cat_frame, textvariable=self._cat_filter,
                                        state="readonly", width=18,
                                        font=FONTS["body"])
        self._cat_combo.pack(side="left", padx=6)
        self._cat_combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())

        self._statut_filter = tk.StringVar(value="Actifs")
        ttk.Combobox(cat_frame, textvariable=self._statut_filter,
                     values=["Actifs","Inactifs","Tous"],
                     state="readonly", width=10,
                     font=FONTS["body"]).pack(side="left", padx=4)
        self._statut_filter.trace("w", lambda *a: self.load_data())

        # Tableau
        self.table = DataTable(
            left,
            columns=[
                ("Code",         80, "w"),
                ("Désignation", 200, "w"),
                ("Catégorie",   110, "w"),
                ("P. Achat",     90, "e"),
                ("P. Vente",     90, "e"),
                ("Unité",        70, "center"),
                ("Stock",        70, "center"),
                ("Seuil",        60, "center"),
                ("Statut",       80, "center"),
            ],
            height=18
        )
        self.table.grid(row=2, column=0, sticky="nsew")
        left.rowconfigure(2, weight=1)
        self.table.bind_select(self._on_select)
        self.table.bind_double(self._on_double)

        # ── Panneau droit : formulaire ────────────────────────────────────
        right = tk.Frame(body, bg=COLORS["bg_card"], padx=20, pady=20)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(right, text="Fiche Article",
                 font=FONTS["subtitle"], bg=COLORS["bg_card"],
                 fg=COLORS["primary"]).pack(anchor="w", pady=(0,14))

        # Variables
        self._v_code      = tk.StringVar()
        self._v_desg      = tk.StringVar()
        self._v_cat       = tk.StringVar()
        self._v_pach      = tk.StringVar()
        self._v_pvte      = tk.StringVar()
        self._v_unite     = tk.StringVar()
        self._v_qte       = tk.StringVar(value="0")
        self._v_qte_res   = tk.StringVar(value="0")
        self._v_seuil     = tk.StringVar(value="5")
        self._v_cbar      = tk.StringVar()

        fields = [
            ("Code article *",    self._v_code,  False),
            ("Code-barres",       self._v_cbar,  False),
            ("Désignation *",     self._v_desg,  False),
            ("Prix d'achat *",    self._v_pach,  False),
            ("Prix de vente *",   self._v_pvte,  False),
            ("Unité de mesure",   self._v_unite, False),
            ("Quantité initiale", self._v_qte,   False),
            ("Quantité réservée", self._v_qte_res, False),
            ("Seuil d'alerte",    self._v_seuil, False),
        ]
        for lbl, var, ro in fields:
            frame = tk.Frame(right, bg=COLORS["bg_card"])
            frame.pack(fill="x", pady=3)
            tk.Label(frame, text=lbl, font=FONTS["small"],
                     bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                     width=16, anchor="w").pack(side="left")
            state = "readonly" if ro else "normal"
            tk.Entry(frame, textvariable=var, font=FONTS["body"],
                     relief="solid", bd=1, bg="#FAFAFA",
                     state=state).pack(side="left", fill="x", expand=True, ipady=4)

        # Catégorie
        cat_row = tk.Frame(right, bg=COLORS["bg_card"])
        cat_row.pack(fill="x", pady=3)
        tk.Label(cat_row, text="Catégorie", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                 width=16, anchor="w").pack(side="left")
        self._cat_combo_form = ttk.Combobox(
            cat_row, textvariable=self._v_cat,
            state="readonly", font=FONTS["body"])
        self._cat_combo_form.pack(side="left", fill="x", expand=True)

        # Avertissement prix
        self._price_warn = tk.Label(right, text="", font=FONTS["small"],
                                     bg=COLORS["bg_card"], fg=COLORS["warning"])
        self._price_warn.pack(anchor="w", pady=2)

        self._v_pvte.trace("w", self._check_prices)
        self._v_pach.trace("w", self._check_prices)

        # Boutons
        btn_frame = tk.Frame(right, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x", pady=(16, 4))

        if self.user["role"] in ("gestionnaire", "admin"):
            StyledButton(btn_frame, "💾 Enregistrer",
                         command=self._save, style="success").pack(fill="x", pady=3)
            StyledButton(btn_frame, "🆕 Nouveau",
                         command=self._new_form, style="outline").pack(fill="x", pady=3)

        StyledButton(btn_frame, "✖ Effacer",
                     command=self._clear_form, style="ghost").pack(fill="x", pady=3)

        # Statut stock
        self._stock_lbl = tk.Label(right, text="", font=FONTS["body"],
                                    bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self._stock_lbl.pack(anchor="w", pady=(12, 0))

    def _check_prices(self, *_):
        try:
            pach = float(self._v_pach.get() or 0)
            pvte = float(self._v_pvte.get() or 0)
            if pvte < pach and pach > 0 and pvte > 0:
                self._price_warn.config(
                    text="⚠ Prix vente < prix achat (marge négative)")
            else:
                self._price_warn.config(text="")
        except ValueError:
            self._price_warn.config(text="")

    def load_data(self, *_):
        """Charge/recharge les articles depuis la BDD."""
        self._load_categories()
        self.table.clear()
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Filtres
            where = ["1=1"]
            params = []

            stat = self._statut_filter.get()
            if stat == "Actifs":
                where.append("a.statut='actif'")
            elif stat == "Inactifs":
                where.append("a.statut='inactif'")

            cat = self._cat_filter.get()
            if cat and cat not in ("Toutes", ""):
                where.append("c.libelle=%s")
                params.append(cat)

            search = self.search.get()
            if search:
                where.append("(a.code LIKE %s OR a.designation LIKE %s)")
                params += [f"%{search}%", f"%{search}%"]

            cursor.execute(f"""
                SELECT a.*, c.libelle AS cat_nom,
                       s.quantite_actuelle AS qte,
                       s.quantite_reservee AS qte_res
                FROM articles a
                LEFT JOIN categories c ON c.id = a.categorie_id
                LEFT JOIN stocks s     ON s.article_id = a.id
                WHERE {' AND '.join(where)}
                ORDER BY a.designation
            """, params)

            for r in cursor.fetchall():
                statut = "✅ Actif" if r["statut"] == "actif" else "⛔ Inactif"
                tag = "" if r["statut"] == "actif" else "warning"
                stock = float(r.get("qte") or 0)
                self.table.insert((
                    r["code"], r["designation"],
                    r["cat_nom"] or "—",
                    f"{int(r['prix_achat']):,}".replace(",", " "),
                    f"{int(r['prix_vente']):,}".replace(",", " "),
                    r["unite"],
                    f"{stock:,.0f}".replace(",", " "),
                    r["seuil_alerte"], statut
                ), tag=tag)

            cursor.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _load_categories(self):
        try:
            conn = get_connection()
            c    = conn.cursor()
            c.execute("SELECT id, libelle FROM categories ORDER BY libelle")
            self._categories = c.fetchall()
            c.close(); conn.close()

            cat_names = ["Toutes"] + [r[1] for r in self._categories]
            self._cat_combo.config(values=cat_names)

            form_names = [r[1] for r in self._categories]
            self._cat_combo_form.config(values=form_names)
        except Exception:
            pass

    def _on_select(self, e=None):
        vals = self.table.selected_values()
        if not vals:
            return
        code = vals[0]
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.*, c.libelle AS cat_nom,
                       s.quantite_actuelle, s.quantite_reservee
                FROM articles a
                LEFT JOIN categories c ON c.id = a.categorie_id
                LEFT JOIN stocks s     ON s.article_id = a.id
                WHERE a.code=%s
            """, (code,))
            r = cursor.fetchone()
            cursor.close(); conn.close()
            if r:
                self._selected_id = r["id"]
                self._v_code.set(r["code"])
                self._v_cbar.set(r["code_barre"] or "")
                self._v_desg.set(r["designation"])
                self._v_pach.set(str(r["prix_achat"]))
                self._v_pvte.set(str(r["prix_vente"]))
                self._v_unite.set(r["unite"])
                self._v_qte.set(str(r.get("quantite_actuelle") or 0))
                self._v_qte_res.set(str(r.get("quantite_reservee") or 0))
                self._v_seuil.set(str(r["seuil_alerte"]))
                self._v_cat.set(r["cat_nom"] or "")
                qte = float(r.get("quantite_actuelle") or 0)
                self._stock_lbl.config(
                    text=f"📦 Stock actuel : {qte:.0f} {r['unite']}",
                    fg=COLORS["success"] if qte > r["seuil_alerte"]
                    else COLORS["danger"])
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _on_double(self, e=None):
        self._on_select()

    def _new_form(self):
        self._clear_form()
        self._selected_id = None

    def _clear_form(self):
        self._selected_id = None
        for v in (self._v_code, self._v_cbar, self._v_desg,
                  self._v_pach, self._v_pvte, self._v_unite, self._v_cat):
            v.set("")
        self._v_qte.set("0")
        self._v_qte_res.set("0")
        self._v_seuil.set("5")
        self._stock_lbl.config(text="")
        self._price_warn.config(text="")

    def _save(self):
        code   = self._v_code.get().strip()
        desg   = self._v_desg.get().strip()
        pach   = self._v_pach.get().strip()
        pvte   = self._v_pvte.get().strip()
        unite  = self._v_unite.get().strip() or "unité"
        seuil  = self._v_seuil.get().strip() or "5"
        qte    = self._v_qte.get().strip() or "0"
        qte_res = self._v_qte_res.get().strip() or "0"
        cbar   = self._v_cbar.get().strip()
        cat    = self._v_cat.get().strip()

        if not code or not desg or not pach or not pvte:
            info_dialog(self, "Champs manquants",
                        "Code, désignation, prix achat et prix vente sont obligatoires.",
                        kind="warning")
            return
        try:
            pach_f   = float(pach)
            pvte_f   = float(pvte)
            seuil_i  = int(seuil)
            qte_f    = float(qte)
            qte_res_f = float(qte_res)
        except ValueError:
            info_dialog(self, "Erreur", "Prix, quantité et seuil doivent être des nombres.", kind="error")
            return

        if qte_f < 0 or qte_res_f < 0:
            info_dialog(self, "Erreur", "Les quantités ne peuvent pas être négatives.", kind="error")
            return
        if qte_res_f > qte_f:
            info_dialog(self, "Erreur", "La quantité réservée ne peut pas dépasser la quantité disponible.", kind="error")
            return

        # Trouver l'ID de catégorie
        cat_id = None
        for cid, cname in self._categories:
            if cname == cat:
                cat_id = cid
                break

        try:
            conn   = get_connection()
            cursor = conn.cursor()
            if self._selected_id:
                cursor.execute("""
                    UPDATE articles SET code=%s, code_barre=%s, designation=%s,
                    categorie_id=%s, prix_achat=%s, prix_vente=%s,
                    unite=%s, seuil_alerte=%s
                    WHERE id=%s
                """, (code, cbar or None, desg, cat_id, pach_f, pvte_f,
                      unite, seuil_i, self._selected_id))
                cursor.execute(
                    "UPDATE stocks SET quantite_actuelle=%s, quantite_reservee=%s WHERE article_id=%s",
                    (qte_f, qte_res_f, self._selected_id)
                )
                cursor.execute(
                    "INSERT IGNORE INTO stocks (article_id, quantite_actuelle, quantite_reservee) VALUES (%s, %s, %s)",
                    (self._selected_id, qte_f, qte_res_f)
                )
            else:
                cursor.execute("""
                    INSERT INTO articles
                    (code, code_barre, designation, categorie_id, prix_achat,
                     prix_vente, unite, seuil_alerte)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (code, cbar or None, desg, cat_id, pach_f, pvte_f,
                      unite, seuil_i))
                art_id = cursor.lastrowid
                cursor.execute(
                    "INSERT IGNORE INTO stocks (article_id, quantite_actuelle, quantite_reservee) VALUES (%s, %s, %s)",
                    (art_id, qte_f, qte_res_f)
                )
            conn.commit()
            cursor.close(); conn.close()
            info_dialog(self, "Succès", "Article enregistré avec succès.", kind="success")
            self.load_data()
            self._clear_form()
        except Exception as e:
            info_dialog(self, "Erreur DB", str(e), kind="error")

    def _deactivate(self):
        vals = self.table.selected_values()
        if not vals:
            info_dialog(self, "Sélection requise",
                        "Sélectionnez un article dans le tableau.", kind="warning")
            return
        code = vals[0]
        if confirm_dialog(self, "Désactiver l'article",
                          f"Désactiver l'article '{code}' ?"):
            try:
                conn = get_connection()
                c    = conn.cursor()
                c.execute("UPDATE articles SET statut='inactif' WHERE code=%s", (code,))
                conn.commit()
                c.close(); conn.close()
                self.load_data()
            except Exception as e:
                info_dialog(self, "Erreur", str(e), kind="error")

    def _search(self, term):
        self.load_data()
