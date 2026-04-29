from __future__ import annotations

import json
import os
import subprocess
import tkinter as tk
from dataclasses import dataclass, asdict
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

CONFIG_PATH = Path.home() / ".Winlauncher.json"
CARD_WIDTH = 210
CARD_HEIGHT = 160


@dataclass
class LauncherEntry:
    name: str
    executable: str
    image_path: str


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WinLunch")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg="#1e1f22")

        self.entries: list[LauncherEntry] = []
        self.image_cache: list[tk.PhotoImage] = []

        self._build_layout()
        self._load_entries()
        self._render_cards()

    def _build_layout(self) -> None:
        sidebar = tk.Frame(self, bg="#2b2d31", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="LIBRARY",
            bg="#2b2d31",
            fg="#b5bac1",
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=20,
            anchor="w",
        ).pack(fill="x")

        tk.Button(
            sidebar,
            text="+ Add App/Game",
            bg="#5865f2",
            fg="white",
            activebackground="#4752c4",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            command=self._open_add_dialog,
            padx=14,
            pady=10,
        ).pack(fill="x", padx=14, pady=6)

        tk.Label(
            sidebar,
            text="add any EXE + image",
            bg="#2b2d31",
            fg="#949ba4",
            font=("Segoe UI", 9),
            justify="left",
            padx=14,
            pady=10,
            anchor="w",
        ).pack(fill="x")

        main = tk.Frame(self, bg="#313338")
        main.pack(side="right", fill="both", expand=True)

        topbar = tk.Frame(main, bg="#232428", height=70)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(
            topbar,
            text="WinLauncher",
            bg="#232428",
            fg="#f2f3f5",
            font=("Segoe UI", 17, "bold"),
            padx=20,
            pady=18,
            anchor="w",
        ).pack(side="left")

        grid_shell = tk.Frame(main, bg="#313338")
        grid_shell.pack(fill="both", expand=True, padx=20, pady=20)

        self.canvas = tk.Canvas(
            grid_shell,
            bg="#313338",
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        scrollbar = tk.Scrollbar(grid_shell, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.cards_container = tk.Frame(self.canvas, bg="#313338")
        self.cards_container.bind(
            "<Configure>",
            lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.cards_container, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _open_add_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Game/Application")
        dialog.geometry("520x280")
        dialog.configure(bg="#2b2d31")
        dialog.resizable(False, False)
        dialog.grab_set()

        name_var = tk.StringVar()
        exe_var = tk.StringVar()
        image_var = tk.StringVar()

        def row(label: str, var: tk.StringVar, browse_cmd) -> None:
            frame = tk.Frame(dialog, bg="#2b2d31")
            frame.pack(fill="x", padx=18, pady=10)
            tk.Label(frame, text=label, bg="#2b2d31", fg="#f2f3f5", width=12, anchor="w").pack(side="left")
            tk.Entry(frame, textvariable=var, bg="#1e1f22", fg="#dcddde", insertbackground="#dcddde", relief="flat").pack(side="left", fill="x", expand=True, padx=8)
            tk.Button(frame, text="Browse", command=browse_cmd, relief="flat", bg="#4e5058", fg="white").pack(side="right")

        tk.Label(dialog, text="Name", bg="#2b2d31", fg="#f2f3f5", anchor="w").pack(fill="x", padx=18, pady=(16, 0))
        tk.Entry(dialog, textvariable=name_var, bg="#1e1f22", fg="#dcddde", insertbackground="#dcddde", relief="flat").pack(fill="x", padx=18, pady=4)

        row("Executable", exe_var, lambda: exe_var.set(filedialog.askopenfilename(title="Select executable")))
        row("Picture", image_var, lambda: image_var.set(filedialog.askopenfilename(title="Select image", filetypes=[("Image", "*.png *.gif *.ppm *.pgm") ,("All files", "*.*")])))

        def add() -> None:
            name = name_var.get().strip()
            exe = exe_var.get().strip()
            img = image_var.get().strip()
            if not name or not exe:
                messagebox.showerror("Missing fields", "Name and executable are required.")
                return
            if not os.path.exists(exe):
                messagebox.showerror("Invalid path", "Executable path does not exist.")
                return
            if img and not os.path.exists(img):
                messagebox.showerror("Invalid path", "Image path does not exist.")
                return

            self.entries.append(LauncherEntry(name=name, executable=exe, image_path=img))
            self._save_entries()
            self._render_cards()
            dialog.destroy()

        tk.Button(
            dialog,
            text="Add to Library",
            command=add,
            bg="#5865f2",
            fg="white",
            activebackground="#4752c4",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
        ).pack(pady=20)

    def _render_cards(self) -> None:
        for widget in self.cards_container.winfo_children():
            widget.destroy()
        self.image_cache.clear()

        if not self.entries:
            tk.Label(
                self.cards_container,
                text="No games/apps yet. Click '+ Add App/Game'",
                bg="#313338",
                fg="#b5bac1",
                font=("Segoe UI", 12),
            ).grid(row=0, column=0, padx=8, pady=8, sticky="w")
            return

        columns = 4
        for idx, entry in enumerate(self.entries):
            row, col = divmod(idx, columns)
            card = tk.Frame(self.cards_container, bg="#232428", width=CARD_WIDTH, height=CARD_HEIGHT)
            card.grid(row=row, column=col, padx=10, pady=10)
            card.grid_propagate(False)

            preview = self._load_preview(entry.image_path)
            preview_label = tk.Label(card, image=preview, bg="#232428")
            preview_label.image = preview
            self.image_cache.append(preview)
            preview_label.pack(fill="x", padx=6, pady=(6, 2))

            tk.Label(card, text=entry.name, bg="#232428", fg="#f2f3f5", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(2, 4))

            buttons = tk.Frame(card, bg="#232428")
            buttons.pack(fill="x", padx=8, pady=(0, 8))

            tk.Button(buttons, text="Launch", bg="#3ba55d", fg="white", relief="flat", command=lambda e=entry: self._launch(e)).pack(side="left")
            tk.Button(buttons, text="Remove", bg="#da373c", fg="white", relief="flat", command=lambda e=entry: self._remove(e)).pack(side="right")

    def _load_preview(self, image_path: str) -> tk.PhotoImage:
        if image_path and os.path.exists(image_path):
            try:
                return tk.PhotoImage(file=image_path).subsample(2, 2)
            except tk.TclError:
                pass

        placeholder = tk.PhotoImage(width=190, height=95)
        placeholder.put("#404249", to=(0, 0, 190, 95))
        placeholder.put("#5865f2", to=(0, 70, 190, 95))
        return placeholder

    def _launch(self, entry: LauncherEntry) -> None:
        try:
            subprocess.Popen([entry.executable], shell=False)
        except OSError as exc:
            messagebox.showerror("Launch failed", f"Could not launch:\n{entry.executable}\n\n{exc}")

    def _remove(self, entry: LauncherEntry) -> None:
        if messagebox.askyesno("Remove", f"Remove '{entry.name}' from library?"):
            self.entries = [e for e in self.entries if e != entry]
            self._save_entries()
            self._render_cards()

    def _load_entries(self) -> None:
        if not CONFIG_PATH.exists():
            return
        try:
            raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            self.entries = [LauncherEntry(**item) for item in raw]
        except (json.JSONDecodeError, OSError, TypeError):
            messagebox.showwarning("Config issue", "Could not read existing launcher config. Starting fresh.")
            self.entries = []

    def _save_entries(self) -> None:
        CONFIG_PATH.write_text(
            json.dumps([asdict(entry) for entry in self.entries], indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
