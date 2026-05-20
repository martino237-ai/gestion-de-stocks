"""
SVGS — Module Rapports & Statistiques
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta, datetime
from constants import COLORS, FONTS
from database import get_connection
from widgets import StyledButton, DataTable, info_dialog


class RapportsModule(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS["bg_main"])
        self.user = user
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["bg_main"])
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="📊  Rapports & Statistiques",
                 font=FONTS["title"], bg=COLORS["bg_main"],
                 fg=COLORS["primary"]).pack(side="left")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=4)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=24, pady=4)

        # Onglets
        t1 = tk.Frame(nb, bg=COLORS["bg_main"]); nb.add(t1, text="  Ventes  ")
        t2 = tk.Frame(nb, bg=COLORS["bg_main"]); nb.add(t2, text="  Top Articles  ")
        t3 = tk.Frame(nb, bg=COLORS["bg_main"]); nb.add(t3, text="  État du Stock  ")
        t4 = tk.Frame(nb, bg=COLORS["bg_main"]); nb.add(t4, text="  Clôture de caisse  ")

        self._build_ventes(t1)
        self._build_top(t2)
        self._build_stock_etat(t3)
        self._build_cloture(t4)

    # ─── Onglet 1 : Rapport des ventes ───────────────────────────────────────
    def _build_ventes(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Filtres
        flt = tk.Frame(parent, bg=COLORS["bg_main"])
        flt.grid(row=0, column=0, sticky="ew", pady=8)

        tk.Label(flt, text="Période :", font=FONTS["body"],
                 bg=COLORS["bg_main"], fg=COLORS["text_muted"]).pack(side="left")

        self._vte_periode = tk.StringVar(value="Aujourd'hui")
        periods = ["Aujourd'hui", "Cette semaine", "Ce mois", "Personnalisée"]
        ttk.Combobox(flt, textvariable=self._vte_periode, values=periods,
                     state="readonly", width=16, font=FONTS["body"]).pack(side="left", padx=6)
        self._vte_periode.trace("w", lambda *a: self._toggle_custom_dates())

        self._date_from = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self._date_to   = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))

        tk.Label(flt, text="Du:", font=FONTS["body"],
                 bg=COLORS["bg_main"], fg=COLORS["text_muted"]).pack(side="left", padx=(12, 2))
        self._from_entry = tk.Entry(flt, textvariable=self._date_from,
                                     font=FONTS["body"], width=12, relief="solid", bd=1)
        self._from_entry.pack(side="left")

        tk.Label(flt, text="Au:", font=FONTS["body"],
                 bg=COLORS["bg_main"], fg=COLORS["text_muted"]).pack(side="left", padx=(6, 2))
        self._to_entry = tk.Entry(flt, textvariable=self._date_to,
                                   font=FONTS["body"], width=12, relief="solid", bd=1)
        self._to_entry.pack(side="left")

        StyledButton(flt, "🔍 Filtrer", command=self._load_ventes,
                     style="primary").pack(side="left", padx=10)
        StyledButton(flt, "↺ Tout voir", command=self._load_ventes,
                     style="outline").pack(side="left")

        # KPI bande
        self._vte_kpi = tk.Frame(parent, bg=COLORS["bg_main"])
        self._vte_kpi.grid(row=1, column=0, sticky="ew", pady=4)

        self._kv_nb    = tk.StringVar(value="—")
        self._kv_ttc   = tk.StringVar(value="—")
        self._kv_moy   = tk.StringVar(value="—")
        for var, lbl, col in [
            (self._kv_nb,  "Nb ventes",    COLORS["primary"]),
            (self._kv_ttc, "Total TTC",    COLORS["success"]),
            (self._kv_moy, "Panier moyen", COLORS["accent"]),
        ]:
            card = tk.Frame(self._vte_kpi, bg=col, padx=20, pady=10)
            card.pack(side="left", padx=6, pady=4)
            tk.Label(card, textvariable=var, font=("Segoe UI", 20, "bold"),
                     bg=col, fg="white").pack()
            tk.Label(card, text=lbl, font=FONTS["small"],
                     bg=col, fg="#E3F2FD").pack()

        # Tableau
        self._vte_table = DataTable(
            parent,
            columns=[
                ("Réf.",        120, "w"),
                ("Date/Heure", 140, "center"),
                ("Caissier",   120, "w"),
                ("Client",     120, "w"),
                ("Mode",        90, "center"),
                ("Total HT",    100, "e"),
                ("Remise",       80, "e"),
                ("Total TTC",   110, "e"),
                ("Statut",       90, "center"),
            ],
            height=14
        )
        self._vte_table.grid(row=2, column=0, sticky="nsew")
        parent.rowconfigure(2, weight=1)
        self._load_ventes()

    def _toggle_custom_dates(self):
        state = "normal" if self._vte_periode.get() == "Personnalisée" else "readonly"
        self._from_entry.config(state=state)
        self._to_entry.config(state=state)
        self._load_ventes()

    def _load_ventes(self):
        periode = self._vte_periode.get()
        today   = date.today()

        if periode == "Aujourd'hui":
            d_from = d_to = today
        elif periode == "Cette semaine":
            d_from = today - timedelta(days=today.weekday())
            d_to   = today
        elif periode == "Ce mois":
            d_from = today.replace(day=1)
            d_to   = today
        else:
            try:
                d_from = datetime.strptime(self._date_from.get(), "%Y-%m-%d").date()
                d_to   = datetime.strptime(self._date_to.get(),   "%Y-%m-%d").date()
            except ValueError:
                d_from = d_to = today

        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT v.reference, v.created_at,
                       u.nom AS caissier,
                       CONCAT(COALESCE(c.prenom,''),' ',COALESCE(c.nom,'')) AS client,
                       v.mode_paiement, v.total_ht, v.remise,
                       v.total_ttc, v.statut
                FROM ventes v
                JOIN utilisateurs u ON u.id = v.user_id
                LEFT JOIN clients c ON c.id = v.client_id
                WHERE DATE(v.created_at) BETWEEN %s AND %s
                ORDER BY v.created_at DESC
            """, (d_from, d_to))
            rows = cursor.fetchall()
            cursor.close(); conn.close()

            self._vte_table.clear()
            total_ttc = 0
            for r in rows:
                if r["statut"] == "VALIDEE":
                    total_ttc += float(r["total_ttc"])
                tag = "success" if r["statut"] == "VALIDEE" else \
                      "danger"  if r["statut"] == "ANNULEE" else "warning"
                self._vte_table.insert((
                    r["reference"],
                    r["created_at"].strftime("%d/%m/%Y %H:%M"),
                    r["caissier"],
                    r["client"].strip() or "—",
                    r["mode_paiement"],
                    f"{int(r['total_ht']):,}".replace(",", " "),
                    f"{int(r['remise']):,}".replace(",", " "),
                    f"{int(r['total_ttc']):,} F".replace(",", " "),
                    r["statut"],
                ), tag=tag)

            nb = len(rows)
            moy = int(total_ttc / nb) if nb > 0 else 0
            self._kv_nb.set(str(nb))
            self._kv_ttc.set(f"{int(total_ttc):,} F".replace(",", " "))
            self._kv_moy.set(f"{moy:,} F".replace(",", " "))

        except Exception as e:
            pass

    # ─── Onglet 2 : Top articles ──────────────────────────────────────────────
    def _build_top(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        top_ctrl = tk.Frame(parent, bg=COLORS["bg_main"])
        top_ctrl.grid(row=0, column=0, sticky="ew", pady=8)

        tk.Label(top_ctrl, text="Top N :", font=FONTS["body"],
                 bg=COLORS["bg_main"], fg=COLORS["text_muted"]).pack(side="left")
        self._top_n = tk.IntVar(value=10)
        ttk.Spinbox(top_ctrl, from_=5, to=50, textvariable=self._top_n,
                    width=5, font=FONTS["body"]).pack(side="left", padx=6)

        tk.Label(top_ctrl, text="Période :", font=FONTS["body"],
                 bg=COLORS["bg_main"], fg=COLORS["text_muted"]).pack(side="left", padx=(12,2))
        self._top_periode = tk.StringVar(value="30")
        ttk.Combobox(top_ctrl, textvariable=self._top_periode,
                     values=["7", "30", "90", "365"],
                     state="readonly", width=10,
                     font=FONTS["body"]).pack(side="left")
        tk.Label(top_ctrl, text="jours", font=FONTS["body"],
                 bg=COLORS["bg_main"], fg=COLORS["text_muted"]).pack(side="left", padx=2)

        StyledButton(top_ctrl, "🔍 Générer", command=self._load_top,
                     style="primary").pack(side="left", padx=12)

        self._top_table = DataTable(
            parent,
            columns=[
                ("Rang",         60, "center"),
                ("Code",         80, "w"),
                ("Article",     250, "w"),
                ("Catégorie",   120, "w"),
                ("Qté vendue",  110, "e"),
                ("CA généré",   130, "e"),
                ("Prix moyen",  110, "e"),
            ],
            height=18
        )
        self._top_table.grid(row=1, column=0, sticky="nsew")
        self._load_top()

    def _load_top(self):
        n   = self._top_n.get()
        days = int(self._top_periode.get())
        self._top_table.clear()
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.code, a.designation, c.libelle AS cat,
                       SUM(l.quantite)      AS qte_tot,
                       SUM(l.montant_ligne) AS ca,
                       AVG(l.prix_unitaire) AS prix_moy
                FROM lignes_vente l
                JOIN articles a ON a.id = l.article_id
                LEFT JOIN categories c ON c.id = a.categorie_id
                JOIN ventes v ON v.id = l.vente_id
                WHERE v.statut='VALIDEE'
                  AND v.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY a.id
                ORDER BY qte_tot DESC
                LIMIT %s
            """, (days, n))
            for i, r in enumerate(cursor.fetchall(), 1):
                self._top_table.insert((
                    f"#{i}",
                    r["code"],
                    r["designation"],
                    r["cat"] or "—",
                    f"{r['qte_tot']:.1f}",
                    f"{int(r['ca']):,} F".replace(",", " "),
                    f"{int(r['prix_moy']):,} F".replace(",", " "),
                ))
            cursor.close(); conn.close()
        except Exception:
            pass

    # ─── Onglet 3 : État du stock ─────────────────────────────────────────────
    def _build_stock_etat(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        top = tk.Frame(parent, bg=COLORS["bg_main"])
        top.grid(row=0, column=0, sticky="ew", pady=8)
        StyledButton(top, "↺ Actualiser", command=self._load_stock_etat,
                     style="primary").pack(side="left")

        self._kv_val_tot = tk.StringVar(value="—")
        self._kv_nb_art  = tk.StringVar(value="—")
        self._kv_nb_al   = tk.StringVar(value="—")

        for var, lbl, col in [
            (self._kv_val_tot, "Valeur totale stock", COLORS["kpi_stock"]),
            (self._kv_nb_art,  "Articles actifs",     COLORS["primary"]),
            (self._kv_nb_al,   "Articles en alerte",  COLORS["danger"]),
        ]:
            card = tk.Frame(top, bg=col, padx=16, pady=8)
            card.pack(side="left", padx=8)
            tk.Label(card, textvariable=var, font=("Segoe UI", 18, "bold"),
                     bg=col, fg="white").pack()
            tk.Label(card, text=lbl, font=FONTS["small"],
                     bg=col, fg="#E3F2FD").pack()

        self._etat_table = DataTable(
            parent,
            columns=[
                ("Code",         80, "w"),
                ("Article",     220, "w"),
                ("Catégorie",   110, "w"),
                ("Stock",        90, "e"),
                ("Valeur achat", 120, "e"),
                ("Valeur vente", 120, "e"),
                ("Marge (%)",    90, "center"),
                ("Statut",      110, "center"),
            ],
            height=16
        )
        self._etat_table.grid(row=1, column=0, sticky="nsew")
        self._load_stock_etat()

    def _load_stock_etat(self):
        self._etat_table.clear()
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.code, a.designation, c.libelle AS cat,
                       s.quantite_actuelle, a.prix_achat, a.prix_vente,
                       a.seuil_alerte, a.unite
                FROM stocks s
                JOIN articles a ON a.id = s.article_id
                LEFT JOIN categories c ON c.id = a.categorie_id
                WHERE a.statut='actif'
                ORDER BY a.designation
            """)
            rows = cursor.fetchall()
            cursor.close(); conn.close()

            val_tot = sum(float(r["quantite_actuelle"]) * float(r["prix_achat"])
                          for r in rows)
            nb_al   = sum(1 for r in rows
                          if r["quantite_actuelle"] <= r["seuil_alerte"])

            self._kv_val_tot.set(f"{int(val_tot):,} F".replace(",", " "))
            self._kv_nb_art.set(str(len(rows)))
            self._kv_nb_al.set(str(nb_al))

            for r in rows:
                qte  = float(r["quantite_actuelle"])
                vach = qte * float(r["prix_achat"])
                vvte = qte * float(r["prix_vente"])
                marge = ((float(r["prix_vente"]) - float(r["prix_achat"]))
                         / float(r["prix_achat"]) * 100) if r["prix_achat"] > 0 else 0

                if qte == 0:
                    tag, status = "danger", "🔴 RUPTURE"
                elif qte <= r["seuil_alerte"]:
                    tag, status = "warning", "🟠 FAIBLE"
                else:
                    tag, status = "", "🟢 OK"

                self._etat_table.insert((
                    r["code"], r["designation"], r["cat"] or "—",
                    f"{qte:.1f} {r['unite']}",
                    f"{int(vach):,} F".replace(",", " "),
                    f"{int(vvte):,} F".replace(",", " "),
                    f"{marge:.0f}%",
                    status,
                ), tag=tag)
        except Exception:
            pass

    # ─── Onglet 4 : Clôture de caisse ─────────────────────────────────────────
    def _build_cloture(self, parent):
        frm = tk.Frame(parent, bg=COLORS["bg_card"], padx=30, pady=30)
        frm.pack(padx=40, pady=20, fill="x")

        tk.Label(frm, text="🏦  Clôture de caisse journalière",
                 font=FONTS["subtitle"], bg=COLORS["bg_card"],
                 fg=COLORS["primary"]).pack(anchor="w", pady=(0, 16))

        tk.Label(frm, text="Date :", font=FONTS["body"],
                 bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")
        self._cloture_date = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        tk.Entry(frm, textvariable=self._cloture_date, font=FONTS["body"],
                 width=16, relief="solid", bd=1).pack(anchor="w", pady=(2, 10), ipady=4)

        StyledButton(frm, "📊 Générer le rapport",
                     command=self._load_cloture, style="primary").pack(anchor="w")

        self._cloture_result = tk.Frame(frm, bg=COLORS["bg_card"])
        self._cloture_result.pack(fill="x", pady=16)

    def _load_cloture(self):
        for w in self._cloture_result.winfo_children():
            w.destroy()

        d = self._cloture_date.get()
        try:
            conn   = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT mode_paiement, COUNT(*) AS nb, SUM(total_ttc) AS total
                FROM ventes
                WHERE DATE(created_at)=%s AND statut='VALIDEE'
                GROUP BY mode_paiement
            """, (d,))
            rows = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) AS nb_annul, SUM(total_ttc) AS tot_annul
                FROM ventes WHERE DATE(created_at)=%s AND statut='ANNULEE'
            """, (d,))
            annul = cursor.fetchone()
            cursor.close(); conn.close()

            grand_total = sum(float(r["total"]) for r in rows)

            def ligne(label, val, bold=False):
                f = tk.Frame(self._cloture_result, bg=COLORS["bg_card"])
                f.pack(fill="x", pady=2)
                font = FONTS["heading"] if bold else FONTS["body"]
                tk.Label(f, text=label, font=font, bg=COLORS["bg_card"],
                         fg=COLORS["text_main"], width=25, anchor="w").pack(side="left")
                tk.Label(f, text=val, font=font, bg=COLORS["bg_card"],
                         fg=COLORS["primary"] if bold else COLORS["text_main"]).pack(side="right")

            tk.Label(self._cloture_result,
                     text=f"Rapport du {d}", font=FONTS["heading"],
                     bg=COLORS["bg_card"], fg=COLORS["primary"]).pack(anchor="w", pady=(0,8))
            tk.Frame(self._cloture_result, bg=COLORS["border"], height=1).pack(fill="x", pady=4)

            for r in rows:
                ligne(f"  {r['mode_paiement']} ({r['nb']} ventes)",
                      f"{int(r['total']):,} F".replace(",", " "))

            tk.Frame(self._cloture_result, bg=COLORS["primary"], height=2).pack(fill="x", pady=6)
            ligne("TOTAL TOUTES MODES", f"{int(grand_total):,} F".replace(",", " "), bold=True)
            ligne(f"Ventes annulées ({annul['nb_annul']})",
                  f"{int(annul['tot_annul'] or 0):,} F".replace(",", " "))

        except Exception as e:
            tk.Label(self._cloture_result, text=str(e),
                     font=FONTS["body"], fg=COLORS["danger"],
                     bg=COLORS["bg_card"]).pack()
