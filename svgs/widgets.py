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
            "primary": (COLORS["primary"],      COLORS["text_white"], COLORS["primary_dark"]),
            "success": (COLORS["success"],       COLORS["text_white"], COLORS["success_light"]),
            "danger":  (COLORS["danger"],        COLORS["text_white"], COLORS["danger_light"]),
            "warning": (COLORS["warning"],       COLORS["text_white"], "#E65100"),
            "accent":  (COLORS["accent"],        COLORS["text_white"], "#00838F"),
            "outline": (COLORS["bg_card"],       COLORS["primary"],    COLORS["bg_main"]),
            "ghost":   (COLORS["bg_main"],       COLORS["text_main"],  COLORS["border"]),
        }
        bg, fg, hover = color_map.get(style, color_map["primary"])
        lbl = f"{icon}  {text}" if icon else text

        super().__init__(
            parent, text=lbl, command=command,
            bg=bg, fg=fg,
            font=FONTS["btn"],
            relief="flat", bd=0, cursor="hand2",
            padx=14, pady=6,
            activebackground=hover,
            activeforeground=fg,
            **kwargs
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
        color = color or COLORS["primary"]
        super().__init__(parent, bg=color, padx=18, pady=14,
                         relief="flat", bd=0, **kwargs)

        # Icône + titre
        top = tk.Frame(self, bg=color)
        top.pack(fill="x")
        tk.Label(top, text=icon, font=("Segoe UI", 18), bg=color,
                 fg="white").pack(side="left")
        tk.Label(top, text=title, font=FONTS["kpi_lbl"], bg=color,
                 fg="#E3F2FD").pack(side="left", padx=(6, 0))

        # Valeur principale
        self._val_var = tk.StringVar(value=str(value))
        tk.Label(self, textvariable=self._val_var, font=FONTS["kpi_val"],
                 bg=color, fg="white").pack(anchor="w", pady=(4, 0))

        # Unité
        if unit:
            tk.Label(self, text=unit, font=FONTS["small"], bg=color,
                     fg="#BBDEFB").pack(anchor="w")

    def update_value(self, val):
        self._val_var.set(str(val))


# ─── Tableau générique ────────────────────────────────────────────────────────
class DataTable(tk.Frame):
    def __init__(self, parent, columns: list, height=15, **kwargs):
        """
        columns = [("Colonne", width, anchor), ...]
        """
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)

        style = ttk.Style()
        style.configure("SVGS.Treeview",
                        background=COLORS["bg_card"],
                        foreground=COLORS["text_main"],
                        rowheight=28,
                        fieldbackground=COLORS["bg_card"],
                        font=FONTS["body"])
        style.configure("SVGS.Treeview.Heading",
                        background=COLORS["primary"],
                        foreground="white",
                        font=FONTS["heading"],
                        relief="flat")
        style.map("SVGS.Treeview",
                  background=[("selected", COLORS["primary_light"])],
                  foreground=[("selected", "white")])
        style.map("SVGS.Treeview.Heading",
                  background=[("active", COLORS["primary_dark"])])

        # Scrollbars
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
            self.tree.column(col,  width=width, anchor=anchor, minwidth=40)

        # Alternance de couleurs
        self.tree.tag_configure("odd",  background="#F8F9FF")
        self.tree.tag_configure("even", background="#FFFFFF")
        self.tree.tag_configure("danger",  background="#FFEBEE", foreground=COLORS["danger"])
        self.tree.tag_configure("warning", background="#FFF8E1", foreground=COLORS["warning"])
        self.tree.tag_configure("success", background="#E8F5E9", foreground=COLORS["success"])

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0,  column=1, sticky="ns")
        hsb.grid(row=1,  column=0, sticky="ew")
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

        self.var = textvariable or tk.StringVar()
        self.entry = tk.Entry(
            self, textvariable=self.var,
            font=FONTS["body"], width=width,
            relief="solid", bd=1,
            bg="#FAFAFA" if not readonly else COLORS["bg_main"],
            fg=COLORS["text_main"],
            show=show,
            state="readonly" if readonly else "normal",
            insertbackground=COLORS["primary"],
        )
        self.entry.pack(fill="x", pady=(2, 0), ipady=5)

        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, e):
        self.entry.config(bd=2, relief="solid",
                          highlightcolor=COLORS["border_focus"])

    def _on_focus_out(self, e):
        self.entry.config(bd=1)

    def get(self): return self.var.get()
    def set(self, val): self.var.set(val)


# ─── ComboBox stylé ───────────────────────────────────────────────────────────
class LabeledCombo(tk.Frame):
    def __init__(self, parent, label, values=(), textvariable=None,
                 width=18, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)

        tk.Label(self, text=label, font=FONTS["body"],
                 bg=COLORS["bg_card"], fg=COLORS["text_main"],
                 anchor="w").pack(anchor="w")

        self.var = textvariable or tk.StringVar()
        style = ttk.Style()
        style.configure("SVGS.TCombobox", padding=5)

        self.combo = ttk.Combobox(
            self, textvariable=self.var,
            values=list(values), width=width,
            font=FONTS["body"], state="readonly",
        )
        self.combo.pack(fill="x", pady=(2, 0))

    def get(self): return self.var.get()
    def set(self, val): self.var.set(val)
    def config_values(self, values): self.combo.config(values=list(values))


# ─── Section header ────────────────────────────────────────────────────────────
class SectionHeader(tk.Frame):
    def __init__(self, parent, title, subtitle="", **kwargs):
        super().__init__(parent, bg=COLORS["bg_main"], pady=8, **kwargs)
        tk.Label(self, text=title, font=FONTS["subtitle"],
                 bg=COLORS["bg_main"], fg=COLORS["primary"]).pack(anchor="w")
        if subtitle:
            tk.Label(self, text=subtitle, font=FONTS["small"],
                     bg=COLORS["bg_main"], fg=COLORS["text_muted"]).pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(4, 0))


# ─── Badge coloré ─────────────────────────────────────────────────────────────
class Badge(tk.Label):
    def __init__(self, parent, text, color="primary", **kwargs):
        color_map = {
            "primary": (COLORS["primary"],  "white"),
            "success": (COLORS["success"],  "white"),
            "danger":  (COLORS["danger"],   "white"),
            "warning": (COLORS["warning"],  "white"),
            "muted":   (COLORS["border"],   COLORS["text_main"]),
        }
        bg, fg = color_map.get(color, color_map["primary"])
        super().__init__(parent, text=text, bg=bg, fg=fg,
                         font=FONTS["small"], padx=8, pady=2,
                         relief="flat", **kwargs)


# ─── Barre de recherche ───────────────────────────────────────────────────────
class SearchBar(tk.Frame):
    def __init__(self, parent, placeholder="🔍  Rechercher...",
                 command=None, **kwargs):
        super().__init__(parent, bg=COLORS["bg_main"], **kwargs)

        self.var = tk.StringVar()
        self.entry = tk.Entry(
            self, textvariable=self.var,
            font=FONTS["body"], width=30,
            relief="solid", bd=1,
            bg="white", fg=COLORS["text_main"],
            insertbackground=COLORS["primary"],
        )
        self.entry.pack(side="left", ipady=6, padx=(0, 6))
        self.entry.insert(0, placeholder)
        self.entry.config(fg=COLORS["text_muted"])

        self.entry.bind("<FocusIn>",  self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)
        self._placeholder = placeholder

        if command:
            self.entry.bind("<KeyRelease>", lambda e: command(self.get()))
            StyledButton(self, "Chercher", command=lambda: command(self.get()),
                         style="primary").pack(side="left")

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
    dlg.configure(bg=COLORS["bg_card"])

    # Centrer
    dlg.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() // 2 - 200
    y = parent.winfo_rooty() + parent.winfo_height() // 2 - 80
    dlg.geometry(f"400x160+{x}+{y}")

    tk.Label(dlg, text="⚠️  " + title, font=FONTS["heading"],
             bg=COLORS["bg_card"], fg=COLORS["warning"]).pack(pady=(16, 4))
    tk.Label(dlg, text=message, font=FONTS["body"],
             bg=COLORS["bg_card"], fg=COLORS["text_main"],
             wraplength=360).pack(pady=4)

    btn_frame = tk.Frame(dlg, bg=COLORS["bg_card"])
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
    dlg.configure(bg=COLORS["bg_card"])

    dlg.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() // 2 - 200
    y = parent.winfo_rooty() + parent.winfo_height() // 2 - 80
    dlg.geometry(f"420x180+{x}+{y}")

    tk.Label(dlg, text=f"{icons.get(kind, 'ℹ️')}  {title}",
             font=FONTS["heading"],
             bg=COLORS["bg_card"],
             fg=colors.get(kind, COLORS["primary"])).pack(pady=(16, 6))
    tk.Label(dlg, text=message, font=FONTS["body"],
             bg=COLORS["bg_card"], fg=COLORS["text_main"],
             wraplength=380, justify="center").pack(pady=4)
    StyledButton(dlg, "OK", command=dlg.destroy,
                 style="primary").pack(pady=12)
    dlg.wait_window()
