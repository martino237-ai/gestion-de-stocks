"""
SVGS — Module Caisse / Point de Vente
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from constants import COLORS, FONTS, MODES_PAIEMENT
from database import get_connection
from widgets import StyledButton, LabeledEntry, info_dialog, confirm_dialog


class CaisseModule(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS["bg_main"])
        self.user = user
        self._panier = []          # [{article_id, code, desg, prix, qte, total}]
        self._articles_cache = []  # pour l'autocomplétion
        self._build()
        self._load_articles()

    # ─── Construction de l'interface ─────────────────────────────────────────
    def _build(self):
        # ── Titre
        hdr = tk.Frame(self, bg=COLORS["bg_main"])
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="🛒  Interface de Caisse",
                 font=FONTS["title"], bg=COLORS["bg_main"],
                 fg=COLORS["primary"]).pack(side="left")

        info = tk.Label(hdr,
                        text=f"Caissier : {self.user['prenom']} {self.user['nom']}",
                        font=FONTS["body"], bg=COLORS["bg_main"],
                        fg=COLORS["text_muted"])
        info.pack(side="right")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=4)

        # ── Corps
        body = tk.Frame(self, bg=COLORS["bg_main"])
        body.pack(fill="both", expand=True, padx=24, pady=4)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # ══ Panneau gauche : panier ═══════════════════════════════════════
        left = tk.Frame(body, bg=COLORS["bg_card"], padx=16, pady=16)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        # Barre de recherche article
        search_frame = tk.Frame(left, bg=COLORS["bg_card"])
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        tk.Label(search_frame, text="🔍  Article :",
                 font=FONTS["heading"], bg=COLORS["bg_card"],
                 fg=COLORS["primary"]).pack(side="left", padx=(0, 6))

        self._search_var = tk.StringVar()
        self._search_entry = tk.Entry(
            search_frame, textvariable=self._search_var,
            font=("Segoe UI", 13), relief="solid", bd=2,
            bg="white", fg=COLORS["text_main"], width=28,
        )
        self._search_entry.pack(side="left", padx=(0, 6))
        self._search_var.trace("w", self._on_search_change)
        self._search_entry.bind("<Return>", self._add_first_suggestion)
        self._search_entry.bind("<Down>",   self._focus_suggestions)
        self._search_entry.focus_set()

        # Quantité
        tk.Label(search_frame, text="Qté:", font=FONTS["body"],
                 bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left")
        self._qte_var = tk.StringVar(value="1")
        tk.Entry(search_frame, textvariable=self._qte_var,
                 font=FONTS["body"], width=5, relief="solid", bd=1,
                 bg="white").pack(side="left", padx=(2, 6), ipady=6)

        StyledButton(search_frame, "➕ Ajouter",
                     command=self._add_first_suggestion,
                     style="primary").pack(side="left")

        # Liste de suggestions (autocomplete)
        self._suggest_frame = tk.Frame(left, bg=COLORS["bg_card"])
        self._suggest_frame.grid(row=1, column=0, sticky="ew")
        self._suggest_lb = tk.Listbox(
            self._suggest_frame, font=FONTS["body"], height=4,
            bg="white", fg=COLORS["text_main"],
            selectbackground=COLORS["primary"], selectforeground="white",
            relief="solid", bd=1, activestyle="none",
        )
        self._suggest_lb.pack(fill="x")
        self._suggest_lb.bind("<Return>",          self._add_from_list)
        self._suggest_lb.bind("<Double-Button-1>", self._add_from_list)
        self._suggest_lb.bind("<Escape>",          lambda e: self._hide_suggestions())
        self._hide_suggestions()

        # Tableau panier
        pan_frame = tk.Frame(left, bg=COLORS["bg_card"])
        pan_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        left.rowconfigure(2, weight=1)

        tk.Label(pan_frame, text="Articles dans le panier",
                 font=FONTS["heading"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))

        # En-tête tableau
        cols_frame = tk.Frame(pan_frame, bg=COLORS["primary"])
        cols_frame.pack(fill="x")
        headers = [("Désignation", 250), ("Qté", 60),
                   ("P.U.", 100), ("Total", 110), ("", 50)]
        for h, w in headers:
            tk.Label(cols_frame, text=h, font=FONTS["heading"],
                     bg=COLORS["primary"], fg="white",
                     width=w//8, pady=6).pack(side="left", padx=2)

        # Zone scrollable du panier
        pan_container = tk.Frame(pan_frame, bg=COLORS["bg_main"])
        pan_container.pack(fill="both", expand=True)
        self._pan_canvas = tk.Canvas(pan_container, bg=COLORS["bg_main"],
                                      highlightthickness=0)
        pan_sb = ttk.Scrollbar(pan_container, command=self._pan_canvas.yview)
        self._pan_canvas.configure(yscrollcommand=pan_sb.set)
        pan_sb.pack(side="right", fill="y")
        self._pan_canvas.pack(side="left", fill="both", expand=True)
        self._pan_rows_frame = tk.Frame(self._pan_canvas, bg=COLORS["bg_main"])
        self._pan_canvas_window = self._pan_canvas.create_window(
            (0, 0), window=self._pan_rows_frame, anchor="nw")
        self._pan_rows_frame.bind(
            "<Configure>",
            lambda e: self._pan_canvas.configure(
                scrollregion=self._pan_canvas.bbox("all")))

        # ══ Panneau droit : résumé & paiement ════════════════════════════
        right = tk.Frame(body, bg=COLORS["bg_card"], padx=20, pady=20)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(right, text="Résumé de la vente",
                 font=FONTS["subtitle"], bg=COLORS["bg_card"],
                 fg=COLORS["primary"]).pack(anchor="w", pady=(0, 10))

        tk.Frame(right, bg=COLORS["border"], height=1).pack(fill="x", pady=4)

        def kv(label, var, big=False, color=None):
            f = tk.Frame(right, bg=COLORS["bg_card"])
            f.pack(fill="x", pady=3)
            tk.Label(f, text=label, font=FONTS["body"],
                     bg=COLORS["bg_card"],
                     fg=COLORS["text_muted"]).pack(side="left")
            font = ("Segoe UI", 18, "bold") if big else FONTS["body"]
            tk.Label(f, textvariable=var, font=font,
                     bg=COLORS["bg_card"],
                     fg=color or COLORS["text_main"]).pack(side="right")

        self._v_nbarts  = tk.StringVar(value="0 article(s)")
        self._v_subtot  = tk.StringVar(value="0 F")
        self._v_remise  = tk.StringVar(value="0 F")
        self._v_tva     = tk.StringVar(value="0 F")
        self._v_total   = tk.StringVar(value="0 F")
        self._v_recu    = tk.StringVar(value="0")
        self._v_rendu   = tk.StringVar(value="0 F")

        kv("Nb articles :", self._v_nbarts)
        kv("Sous-total :",  self._v_subtot)

        # Remise
        rem_frame = tk.Frame(right, bg=COLORS["bg_card"])
        rem_frame.pack(fill="x", pady=3)
        tk.Label(rem_frame, text="Remise (%):",
                 font=FONTS["body"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(side="left")
        self._remise_var = tk.StringVar(value="0")
        rem_state = "normal" if self.user["role"] in ("gestionnaire","admin") else "readonly"
        tk.Entry(rem_frame, textvariable=self._remise_var,
                 font=FONTS["body"], width=6, relief="solid", bd=1,
                 state=rem_state).pack(side="right", ipady=3)
        self._remise_var.trace("w", lambda *a: self._recalc())

        kv("Remise :",   self._v_remise,  color=COLORS["warning"])
        kv("TVA (0%) :", self._v_tva,     color=COLORS["text_muted"])

        tk.Frame(right, bg=COLORS["primary"], height=2).pack(fill="x", pady=6)
        kv("TOTAL TTC :", self._v_total, big=True, color=COLORS["primary"])
        tk.Frame(right, bg=COLORS["border"], height=1).pack(fill="x", pady=6)

        # Montant reçu
        recu_frame = tk.Frame(right, bg=COLORS["bg_card"])
        recu_frame.pack(fill="x", pady=4)
        tk.Label(recu_frame, text="Montant reçu (F):",
                 font=FONTS["body"], bg=COLORS["bg_card"],
                 fg=COLORS["text_main"]).pack(side="left")
        tk.Entry(recu_frame, textvariable=self._v_recu,
                 font=("Segoe UI", 14, "bold"), width=12,
                 relief="solid", bd=2,
                 bg="#E3F2FD").pack(side="right", ipady=5)
        self._v_recu.trace("w", lambda *a: self._calc_rendu())

        # Monnaie rendue
        rendu_frame = tk.Frame(right, bg=COLORS["success"],
                               padx=10, pady=8)
        rendu_frame.pack(fill="x", pady=6)
        tk.Label(rendu_frame, text="Monnaie à rendre :",
                 font=FONTS["body"], bg=COLORS["success"],
                 fg="white").pack(side="left")
        tk.Label(rendu_frame, textvariable=self._v_rendu,
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORS["success"], fg="white").pack(side="right")

        # Mode de paiement
        mp_frame = tk.Frame(right, bg=COLORS["bg_card"])
        mp_frame.pack(fill="x", pady=6)
        tk.Label(mp_frame, text="Mode paiement :",
                 font=FONTS["body"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(side="left")
        self._mode_pay = tk.StringVar(value="ESPECES")
        ttk.Combobox(mp_frame, textvariable=self._mode_pay,
                     values=MODES_PAIEMENT, state="readonly",
                     width=14, font=FONTS["body"]).pack(side="right")

        tk.Frame(right, bg=COLORS["border"], height=1).pack(fill="x", pady=8)

        # Boutons d'action
        StyledButton(right, "✅  VALIDER LA VENTE",
                     command=self._valider, style="success",
                     width=24).pack(fill="x", pady=4)

        StyledButton(right, "🗑  Vider le panier",
                     command=self._vider_panier, style="danger").pack(fill="x", pady=2)

        StyledButton(right, "🖨  Dernier reçu",
                     command=self._print_last, style="outline").pack(fill="x", pady=2)

        # Raccourcis clavier
        self.bind_all("<F5>", lambda e: self._valider())
        self.bind_all("<Escape>", lambda e: self._vider_panier())

        # Info raccourcis
        tk.Label(right, text="F5 = Valider  |  Échap = Vider",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(pady=(12, 0))

        # Dernière référence
        self._last_ref = None

    # ─── Chargement des articles ─────────────────────────────────────────────
    def _load_articles(self):
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.id, a.code, a.designation, a.prix_vente,
                       a.unite, s.quantite_actuelle
                FROM articles a
                JOIN stocks s ON s.article_id = a.id
                WHERE a.statut='actif'
                ORDER BY a.designation
            """)
            self._articles_cache = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception:
            self._articles_cache = []

    # ─── Autocomplétion ──────────────────────────────────────────────────────
    def _on_search_change(self, *_):
        term = self._search_var.get().strip().lower()
        self._suggest_lb.delete(0, "end")
        if len(term) < 1:
            self._hide_suggestions()
            return
        matches = [a for a in self._articles_cache
                   if term in a["designation"].lower()
                   or term in a["code"].lower()][:8]
        if matches:
            self._suggest_frame.grid()
            for a in matches:
                self._suggest_lb.insert(
                    "end",
                    f"{a['code']} — {a['designation']}  "
                    f"[{a['prix_vente']:,.0f} F | Stock: {a['quantite_actuelle']:.0f}]"
                )
            self._suggest_data = matches
        else:
            self._hide_suggestions()

    def _hide_suggestions(self):
        self._suggest_frame.grid_remove()
        self._suggest_data = []

    def _focus_suggestions(self, e):
        if self._suggest_lb.size() > 0:
            self._suggest_lb.focus_set()
            self._suggest_lb.selection_set(0)

    def _add_first_suggestion(self, e=None):
        if hasattr(self, "_suggest_data") and self._suggest_data:
            self._add_article(self._suggest_data[0])
        else:
            # Cherche par code exact
            term = self._search_var.get().strip()
            for a in self._articles_cache:
                if a["code"].upper() == term.upper():
                    self._add_article(a)
                    return
            info_dialog(self, "Article non trouvé",
                        f"Aucun article correspondant à '{term}'.", kind="warning")

    def _add_from_list(self, e=None):
        idx = self._suggest_lb.curselection()
        if idx and hasattr(self, "_suggest_data"):
            self._add_article(self._suggest_data[idx[0]])
        self._search_entry.focus_set()

    # ─── Gestion du panier ───────────────────────────────────────────────────
    def _add_article(self, art):
        try:
            qte = float(self._qte_var.get() or 1)
            if qte <= 0:
                qte = 1
        except ValueError:
            qte = 1

        # Vérifier stock
        if qte > art["quantite_actuelle"]:
            info_dialog(self, "Stock insuffisant",
                        f"Stock disponible : {art['quantite_actuelle']:.0f} {art.get('unite','')}",
                        kind="error")
            return

        # Si déjà dans panier, additionner
        for item in self._panier:
            if item["article_id"] == art["id"]:
                new_qte = item["qte"] + qte
                if new_qte > art["quantite_actuelle"]:
                    info_dialog(self, "Stock insuffisant",
                                f"Quantité totale dépasse le stock ({art['quantite_actuelle']:.0f}).",
                                kind="error")
                    return
                item["qte"]   = new_qte
                item["total"] = round(new_qte * item["prix"], 2)
                self._refresh_panier()
                self._recalc()
                self._search_var.set("")
                self._qte_var.set("1")
                self._hide_suggestions()
                return

        self._panier.append({
            "article_id": art["id"],
            "code":       art["code"],
            "desg":       art["designation"],
            "prix":       float(art["prix_vente"]),
            "unite":      art.get("unite", ""),
            "qte":        qte,
            "total":      round(float(art["prix_vente"]) * qte, 2),
        })
        self._refresh_panier()
        self._recalc()
        self._search_var.set("")
        self._qte_var.set("1")
        self._hide_suggestions()
        self._search_entry.focus_set()

    def _refresh_panier(self):
        for w in self._pan_rows_frame.winfo_children():
            w.destroy()

        for i, item in enumerate(self._panier):
            bg = "#F8F9FF" if i % 2 == 0 else "white"
            row = tk.Frame(self._pan_rows_frame, bg=bg, pady=4)
            row.pack(fill="x", padx=2, pady=1)

            # Désignation
            tk.Label(row, text=item["desg"], font=FONTS["body"],
                     bg=bg, fg=COLORS["text_main"], width=28,
                     anchor="w").pack(side="left", padx=4)

            # Qté éditable
            qte_var = tk.StringVar(value=str(item["qte"]))
            qte_e = tk.Entry(row, textvariable=qte_var, font=FONTS["body"],
                             width=5, relief="solid", bd=1, justify="center")
            qte_e.pack(side="left", padx=4)

            def on_qte_change(var=qte_var, it=item):
                try:
                    v = float(var.get())
                    if v > 0:
                        it["qte"]   = v
                        it["total"] = round(v * it["prix"], 2)
                        self._recalc()
                except ValueError:
                    pass
            qte_var.trace("w", lambda *a, v=qte_var, it=item: on_qte_change(v, it))

            # Prix unitaire
            tk.Label(row, text=f"{int(item['prix']):,} F".replace(",", " "),
                     font=FONTS["body"], bg=bg, fg=COLORS["text_muted"],
                     width=12, anchor="e").pack(side="left", padx=4)

            # Total ligne
            tk.Label(row, text=f"{int(item['total']):,} F".replace(",", " "),
                     font=("Segoe UI", 11, "bold"),
                     bg=bg, fg=COLORS["primary"],
                     width=14, anchor="e").pack(side="left", padx=4)

            # Bouton supprimer
            idx_capture = i
            btn_del = tk.Button(row, text="✕", font=FONTS["small"],
                                bg="#FFEBEE", fg=COLORS["danger"],
                                relief="flat", bd=0, cursor="hand2",
                                command=lambda i=idx_capture: self._remove_item(i))
            btn_del.pack(side="left", padx=4)

    def _remove_item(self, idx):
        if 0 <= idx < len(self._panier):
            self._panier.pop(idx)
            self._refresh_panier()
            self._recalc()

    def _vider_panier(self):
        if self._panier:
            self._panier.clear()
            self._refresh_panier()
            self._recalc()

    # ─── Calculs ─────────────────────────────────────────────────────────────
    def _recalc(self):
        subtot = sum(it["total"] for it in self._panier)
        try:
            pct_rem = float(self._remise_var.get() or 0)
        except ValueError:
            pct_rem = 0
        pct_rem = max(0, min(100, pct_rem))
        remise = round(subtot * pct_rem / 100, 2)
        base   = subtot - remise
        tva    = 0  # 0% par défaut
        total  = base + tva

        self._v_nbarts.set(f"{len(self._panier)} article(s)")
        self._v_subtot.set(f"{int(subtot):,} F".replace(",", " "))
        self._v_remise.set(f"{int(remise):,} F".replace(",", " "))
        self._v_tva.set(f"{int(tva):,} F".replace(",", " "))
        self._v_total.set(f"{int(total):,} F".replace(",", " "))
        self._total_ttc = total
        self._calc_rendu()

    def _calc_rendu(self):
        try:
            recu = float(self._v_recu.get() or 0)
        except ValueError:
            recu = 0
        rendu = max(0, recu - getattr(self, "_total_ttc", 0))
        self._v_rendu.set(f"{int(rendu):,} F".replace(",", " "))

    # ─── Validation de la vente ───────────────────────────────────────────────
    def _valider(self):
        if not self._panier:
            info_dialog(self, "Panier vide", "Ajoutez des articles avant de valider.",
                        kind="warning")
            return

        total = getattr(self, "_total_ttc", 0)
        mode  = self._mode_pay.get()

        try:
            recu = float(self._v_recu.get() or 0)
        except ValueError:
            recu = 0

        if mode == "ESPECES" and recu < total:
            info_dialog(self, "Montant insuffisant",
                        f"Montant reçu ({int(recu):,} F) < Total ({int(total):,} F).".replace(",", " "),
                        kind="warning")
            return

        try:
            rem = float(self._remise_var.get() or 0)
        except ValueError:
            rem = 0

        subtot = sum(it["total"] for it in self._panier)
        remise_amt = round(subtot * rem / 100, 2)

        # Générer référence unique
        now = datetime.now()
        ref = f"VTE-{now.strftime('%Y%m%d-%H%M%S')}"

        conn   = get_connection()
        cursor = conn.cursor()
        try:
            conn.autocommit = False
            cursor.execute("""
                INSERT INTO ventes
                (reference, user_id, total_ht, taux_tva, total_ttc,
                 remise, mode_paiement, montant_recu, statut)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'VALIDEE')
            """, (ref, self.user["id"], subtot - remise_amt, 0,
                  total, remise_amt, mode, recu))
            vente_id = cursor.lastrowid

            for item in self._panier:
                cursor.execute("""
                    INSERT INTO lignes_vente
                    (vente_id, article_id, quantite, prix_unitaire, montant_ligne)
                    VALUES (%s,%s,%s,%s,%s)
                """, (vente_id, item["article_id"], item["qte"],
                      item["prix"], item["total"]))
                cursor.execute("""
                    UPDATE stocks SET quantite_actuelle = quantite_actuelle - %s
                    WHERE article_id = %s
                """, (item["qte"], item["article_id"]))
                cursor.execute("""
                    INSERT INTO mouvements_stock
                    (article_id, type_mvt, quantite, reference, user_id)
                    VALUES (%s,'SORTIE',%s,%s,%s)
                """, (item["article_id"], item["qte"], ref, self.user["id"]))

            conn.commit()
            self._last_ref = ref

            rendu = max(0, recu - total)
            info_dialog(
                self, "✅ Vente validée",
                f"Référence : {ref}\n"
                f"Total : {int(total):,} F\n"
                f"Monnaie rendue : {int(rendu):,} F".replace(",", " "),
                kind="success"
            )
            self._vider_panier()
            self._v_recu.set("0")
            self._load_articles()

        except Exception as e:
            conn.rollback()
            info_dialog(self, "Erreur lors de la vente", str(e), kind="error")
        finally:
            cursor.close()
            conn.close()

    def _print_last(self):
        if not self._last_ref:
            info_dialog(self, "Aucun reçu",
                        "Effectuez d'abord une vente.", kind="warning")
            return
        ReceiptWindow(self, self._last_ref)


# ─── Fenêtre de reçu ─────────────────────────────────────────────────────────
class ReceiptWindow(tk.Toplevel):
    def __init__(self, parent, reference):
        super().__init__(parent)
        self.title(f"Reçu — {reference}")
        self.configure(bg="white")
        self.resizable(False, False)
        self.geometry("360x600")
        self._build(reference)

    def _build(self, ref):
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT v.*, u.nom AS caissier
                FROM ventes v JOIN utilisateurs u ON u.id = v.user_id
                WHERE v.reference = %s
            """, (ref,))
            vente = cursor.fetchone()

            cursor.execute("""
                SELECT l.*, a.designation, a.code
                FROM lignes_vente l JOIN articles a ON a.id = l.article_id
                WHERE l.vente_id = %s
            """, (vente["id"],))
            lignes = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as e:
            tk.Label(self, text=str(e)).pack()
            return

        from constants import ETABLISSEMENT, VILLE

        f = tk.Frame(self, bg="white", padx=20)
        f.pack(fill="both", expand=True, pady=10)

        def lbl(text, font=None, fg="black", anchor="center"):
            tk.Label(f, text=text, font=font or ("Courier New", 10),
                     bg="white", fg=fg, anchor=anchor,
                     justify="center").pack(fill="x")

        lbl("=" * 38, ("Courier New", 9))
        lbl(ETABLISSEMENT, ("Courier New", 12, "bold"))
        lbl(VILLE, ("Courier New", 9))
        lbl("=" * 38, ("Courier New", 9))
        lbl(f"REÇU DE VENTE", ("Courier New", 11, "bold"))
        lbl(f"Réf : {vente['reference']}", ("Courier New", 9))
        lbl(f"Date : {vente['created_at'].strftime('%d/%m/%Y %H:%M')}", ("Courier New", 9))
        lbl(f"Caissier : {vente['caissier']}", ("Courier New", 9))
        lbl(f"Mode : {vente['mode_paiement']}", ("Courier New", 9))
        lbl("-" * 38, ("Courier New", 9))
        lbl(f"{'Article':<22}{'Qté':>4}{'Prix':>6}{'Total':>6}", ("Courier New", 9))
        lbl("-" * 38, ("Courier New", 9))

        for l in lignes:
            desg = l["designation"][:20]
            line = f"{desg:<22}{l['quantite']:>4.0f}{int(l['prix_unitaire']):>6}{int(l['montant_ligne']):>6}"
            lbl(line, ("Courier New", 9))

        lbl("-" * 38, ("Courier New", 9))
        if vente["remise"] > 0:
            lbl(f"{'Remise :':<30}{int(vente['remise']):>8} F", ("Courier New", 9))
        lbl(f"{'TOTAL TTC :':<26}{int(vente['total_ttc']):>12} F",
            ("Courier New", 11, "bold"))
        if vente["montant_recu"]:
            recu  = int(vente["montant_recu"])
            rendu = max(0, recu - int(vente["total_ttc"]))
            lbl(f"{'Reçu :':<30}{recu:>8} F", ("Courier New", 9))
            lbl(f"{'Rendu :':<30}{rendu:>8} F", ("Courier New", 9))
        lbl("=" * 38, ("Courier New", 9))
        lbl("Merci de votre visite !", ("Courier New", 10, "italic"))
        lbl("=" * 38, ("Courier New", 9))

        StyledButton(f, "🖨 Imprimer", command=self._print,
                     style="primary").pack(pady=10)
        StyledButton(f, "✖ Fermer", command=self.destroy,
                     style="ghost").pack()

    def _print(self):
        try:
            import subprocess
            self.update()
            # Impression via Ctrl+P navigateur ou imprimante système
            info_dialog(self, "Impression",
                        "Utilisez Ctrl+P de votre navigateur ou\nimprimer depuis votre système.",
                        kind="info")
        except Exception:
            pass
