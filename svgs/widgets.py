"""
SVGS — Widgets UI réutilisables (boutons, cartes, tableaux, etc.)
"""
import tkinter as tk
from tkinter import ttk
from constants import COLORS, FONTS


# ─── Bouton stylé ─────────────────────────────────────────────────────────────
class StyledButton(tk.Button):
    def __init__(self, parent, text, command=None, style="primary",
                 icon="", width=None, **kwargs):
        color_map = {
            "primary": (COLORS["primary"], COLORS["text_white"], COLORS["primary_dark"]),
            "success": (COLORS["success"], COLORS["text_white"], COLORS["success_light"]),
            "danger": (COLORS["danger"], COLORS["text_white"], COLORS["danger_light"]),
            "warning": (COLORS["warning"], COLORS["text_white"], "#D97706"),
            "accent": (COLORS["accent"], COLORS["text_white"], "#0E7490"),
            "outline": (COLORS["bg_card"], COLORS["primary"], COLORS["bg_card_alt"]),
            "ghost": (COLORS["bg_card_alt"], COLORS["text_main"], COLORS["border"]),
        }
        bg, fg, hover = color_map.get(style, color_map["primary"])
        label = f"{icon}  {text}" if icon else text

        super().__init__(
            parent,
            text=label,
            command=command,
            bg=bg,
            fg=fg,
            font=FONTS["btn"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=16,
            pady=10,
            activebackground=hover,
            activeforeground=fg,
            **kwargs,
        )
        if width:
            self.config(width=width)

        self._bg = bg
        self._hover = hover
        self.bind("<Enter>", lambda e: self.config(bg=hover))
        self.bind("<Leave>", lambda e: self.config(bg=bg))


# ─── Carte KPI ────────────────────────────────────────────────────────────────
class KPICard(tk.Frame):
    def __init__(self, parent, title, value, unit="", color=None, icon="", **kwargs):
        card_bg = COLORS["bg_card"]
        accent = color or COLORS["primary"]
        super().__init__(parent, bg=card_bg, padx=18, pady=16,
                         relief="flat", bd=1, **kwargs)
        self.config(highlightbackground=COLORS["border"], highlightthickness=1)

        edge = tk.Frame(self, bg=accent, width=5)
        edge.pack(side="left", fill="y", padx=(0, 14), pady=4)

        content = tk.Frame(self, bg=card_bg)
        content.pack(side="left", fill="both", expand=True)

        header = tk.Frame(content, bg=card_bg)
        header.pack(fill="x")
        if icon:
            tk.Label(header, text=icon, font=("Segoe UI", 16), bg=card_bg, fg=accent).pack(side="left")
        tk.Label(header, text=title, font=FONTS["kpi_lbl"], bg=card_bg, fg=COLORS["text_muted"]).pack(side="left", padx=(8, 0))

        self._val_var = tk.StringVar(value=str(value))
        tk.Label(content, textvariable=self._val_var, font=FONTS["kpi_val"],
                 bg=card_bg, fg=COLORS["text_main"]).pack(anchor="w", pady=(10, 0))
        if unit:
            tk.Label(content, text=unit, font=FONTS["small"], bg=card_bg,
                     fg=COLORS["text_muted"]).pack(anchor="w", pady=(4, 0))

    def update_value(self, val):
        self._val_var.set(str(val))


# ─── Tableau générique ────────────────────────────────────────────────────────
class DataTable(tk.Frame):
    def __init__(self, parent, columns: list, height=15, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)

        style = ttk.Style()
        style.configure("SVGS.Treeview",
                        background=COLORS["bg_card"],
                        foreground=COLORS["text_main"],
                        rowheight=30,
                        fieldbackground=COLORS["bg_card"],
                        font=FONTS["body"],
                        bordercolor=COLORS["border"],
                        relief="flat")
        style.configure("SVGS.Treeview.Heading",
                        background=COLORS["primary"],
                        foreground=COLORS["text_white"],
                        font=FONTS["heading"],
                        relief="flat",
                        borderwidth=0)
        style.map("SVGS.Treeview",
                  background=[("selected", COLORS["primary_light"])],
                  foreground=[("selected", COLORS["text_white"])])
        style.map("SVGS.Treeview.Heading",
                  background=[("active", COLORS["primary_dark"])])

        vsb = ttk.Scrollbar(self, orient="vertical")
        hsb = ttk.Scrollbar(self, orient="horizontal")

        col_ids = [c[0] for c in columns]
        self.tree = ttk.Treeview(
            self,
            columns=col_ids,
            show="headings",
            height=height,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="SVGS.Treeview",
        )
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        for col, width, anchor in columns:
            self.tree.heading(col, text=col, anchor=anchor)
            self.tree.column(col, width=width, anchor=anchor, minwidth=40)

        self.tree.tag_configure("odd", background=COLORS["bg_card_alt"])
        self.tree.tag_configure("even", background=COLORS["bg_card"])
        self.tree.tag_configure("danger", background="#FFEBEE", foreground=COLORS["danger"])
        self.tree.tag_configure("warning", background="#FFFBEB", foreground=COLORS["warning"])
        self.tree.tag_configure("success", background="#ECFDF5", foreground=COLORS["success"])

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def insert(self, values, tag=""):
        idx = len(self.tree.get_children())
        row_tag = tag or ("odd" if idx % 2 == 0 else "even")
        self.tree.insert("", "end", values=values, tags=(row_tag,))

    def selected_values(self):
        sel = self.tree.selection()
        if sel:
            return self.tree.item(sel[0])["values"]
        return None

    def bind_select(self, callback):
        self.tree.bind("<<TreeviewSelect>>", callback)

    def bind_double(self, callback):
        self.tree.bind("<Double-1>", callback)


# ─── Champ de saisie stylé ────────────────────────────────────────────────────
class LabeledEntry(tk.Frame):
    def __init__(self, parent, label, textvariable=None, width=20,
                 placeholder="", show="", readonly=False, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)

        tk.Label(self, text=label, font=FONTS["body"],
                 bg=COLORS["bg_card"], fg=COLORS["text_main"],
                 anchor="w").pack(anchor="w")

        frame = tk.Frame(self, bg=COLORS["bg_card_alt"], bd=0)
        frame.pack(fill="x", pady=(6, 0))

        self.var = textvariable or tk.StringVar()
        self.entry = tk.Entry(
            frame,
            textvariable=self.var,
            font=FONTS["body"],
            width=width,
            relief="flat",
            bd=0,
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_main"],
            show=show,
            state="readonly" if readonly else "normal",
            insertbackground=COLORS["primary"],
        )
        self.entry.pack(fill="x", ipady=8, padx=10)
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

        if placeholder:
            self._placeholder = placeholder
            self.entry.insert(0, placeholder)
            self.entry.config(fg=COLORS["text_muted"])
            self.entry.bind("<FocusIn>", self._clear_placeholder)
            self.entry.bind("<FocusOut>", self._restore_placeholder)

    def _on_focus_in(self, e):
        self.entry.config(bg=COLORS["bg_card"])

    def _on_focus_out(self, e):
        self.entry.config(bg=COLORS["bg_card_alt"])

    def _clear_placeholder(self, e):
        if self.entry.get() == self._placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=COLORS["text_main"])

    def _restore_placeholder(self, e):
        if not self.entry.get():
            self.entry.insert(0, self._placeholder)
            self.entry.config(fg=COLORS["text_muted"])

    def get(self):
        return self.var.get()

    def set(self, val):
        self.var.set(val)


# ─── ComboBox stylé ───────────────────────────────────────────────────────────
class LabeledCombo(tk.Frame):
    def __init__(self, parent, label, values=(), textvariable=None,
                 width=18, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)

        tk.Label(self, text=label, font=FONTS["body"],
                 bg=COLORS["bg_card"], fg=COLORS["text_main"],
                 anchor="w").pack(anchor="w")

        self.var = textvariable or tk.StringVar()
        self.combo = ttk.Combobox(
            self,
            textvariable=self.var,
            values=list(values),
            width=width,
            font=FONTS["body"],
            state="readonly",
        )
        self.combo.pack(fill="x", pady=(6, 0))

    def get(self):
        return self.var.get()

    def set(self, val):
        self.var.set(val)

    def config_values(self, values):
        self.combo.config(values=list(values))


# ─── Section header ────────────────────────────────────────────────────────────
class SectionHeader(tk.Frame):
    def __init__(self, parent, title, subtitle="", **kwargs):
        super().__init__(parent, bg=COLORS["bg_main"], pady=10, **kwargs)
        tk.Label(self, text=title, font=FONTS["subtitle"],
                 bg=COLORS["bg_main"], fg=COLORS["primary"]).pack(anchor="w")
        if subtitle:
            tk.Label(self, text=subtitle, font=FONTS["small"],
                     bg=COLORS["bg_main"], fg=COLORS["text_muted"]).pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(10, 0))


# ─── Badge coloré ─────────────────────────────────────────────────────────────
class Badge(tk.Label):
    def __init__(self, parent, text, color="primary", **kwargs):
        color_map = {
            "primary": (COLORS["primary"], COLORS["text_white"]),
            "success": (COLORS["success"], COLORS["text_white"]),
            "danger": (COLORS["danger"], COLORS["text_white"]),
            "warning": (COLORS["warning"], COLORS["text_white"]),
            "muted": (COLORS["border"], COLORS["text_main"]),
        }
        bg, fg = color_map.get(color, color_map["primary"])
        super().__init__(parent, text=text, bg=bg, fg=fg,
                         font=FONTS["badge"], padx=10, pady=4,
                         relief="flat", **kwargs)


# ─── Barre de recherche ───────────────────────────────────────────────────────
class SearchBar(tk.Frame):
    def __init__(self, parent, placeholder="🔍  Rechercher...",
                 command=None, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)

        self.var = tk.StringVar()
        self.entry = tk.Entry(
            self,
            textvariable=self.var,
            font=FONTS["body"],
            width=32,
            relief="flat",
            bd=0,
            bg=COLORS["bg_card_alt"],
            fg=COLORS["text_main"],
            insertbackground=COLORS["primary"],
        )
        self.entry.pack(side="left", ipady=10, padx=(0, 8), fill="x", expand=True)
        tk.Frame(self, bg=COLORS["border"], width=1).pack(side="left", fill="y", pady=6)
        self._placeholder = placeholder
        self.entry.insert(0, placeholder)
        self.entry.config(fg=COLORS["text_muted"])
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)

        if command:
            self.entry.bind("<KeyRelease>", lambda e: command(self.get()))
            StyledButton(self, "Chercher", command=lambda: command(self.get()),
                         style="primary", width=10).pack(side="left")

    def _clear_placeholder(self, e):
        if self.entry.get() == self._placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=COLORS["text_main"])

    def _restore_placeholder(self, e):
        if not self.entry.get():
            self.entry.insert(0, self._placeholder)
            self.entry.config(fg=COLORS["text_muted"])

    def get(self):
        val = self.var.get()
        return "" if val == self._placeholder else val


# ─── Dialogue de confirmation ─────────────────────────────────────────────────
def confirm_dialog(parent, title, message):
    result = [False]

    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.configure(bg=COLORS["bg_main"])
    dlg.attributes("-topmost", True)

    dlg.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() // 2 - 200
    y = parent.winfo_rooty() + parent.winfo_height() // 2 - 80
    dlg.geometry(f"400x180+{x}+{y}")

    card = tk.Frame(dlg, bg=COLORS["bg_card"], bd=1, relief="solid")
    card.place(relx=0.5, rely=0.5, anchor="center", width=380, height=160)

    tk.Label(card, text="⚠️  " + title, font=FONTS["heading"],
             bg=COLORS["bg_card"], fg=COLORS["warning"]).pack(pady=(16, 4))
    tk.Label(card, text=message, font=FONTS["body"],
             bg=COLORS["bg_card"], fg=COLORS["text_main"],
             wraplength=340, justify="center").pack(pady=4)

    btn_frame = tk.Frame(card, bg=COLORS["bg_card"])
    btn_frame.pack(pady=12)

    def on_yes():
        result[0] = True
        dlg.destroy()

    StyledButton(btn_frame, "Confirmer", command=on_yes,
                 style="danger").pack(side="left", padx=6)
    StyledButton(btn_frame, "Annuler", command=dlg.destroy,
                 style="ghost").pack(side="left", padx=6)

    dlg.wait_window()
    return result[0]


# ─── Message d'information ────────────────────────────────────────────────────
def info_dialog(parent, title, message, kind="info"):
    icons = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
    colors = {"info": COLORS["primary"], "success": COLORS["success"],
              "error": COLORS["danger"], "warning": COLORS["warning"]}

    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.configure(bg=COLORS["bg_main"])
    dlg.attributes("-topmost", True)

    dlg.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() // 2 - 200
    y = parent.winfo_rooty() + parent.winfo_height() // 2 - 80
    dlg.geometry(f"420x200+{x}+{y}")

    card = tk.Frame(dlg, bg=COLORS["bg_card"], bd=1, relief="solid")
    card.place(relx=0.5, rely=0.5, anchor="center", width=380, height=180)

    tk.Label(card, text=f"{icons.get(kind, 'ℹ️')}  {title}",
             font=FONTS["heading"],
             bg=COLORS["bg_card"],
             fg=colors.get(kind, COLORS["primary"]) ).pack(pady=(16, 6))
    tk.Label(card, text=message, font=FONTS["body"],
             bg=COLORS["bg_card"], fg=COLORS["text_main"],
             wraplength=340, justify="center").pack(pady=4)
    StyledButton(card, "OK", command=dlg.destroy,
                 style="primary").pack(pady=12)
    dlg.wait_window()
