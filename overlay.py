# SPDX-License-Identifier: GPL-3.0-only
import tkinter as tk
import time
from tkinter import font as tkfont
from i18n import tr
from metrics import BY_KEY, METRICS, METRIC_KEYS, MODE_BUTTONS, MODE_MENU


def desktop_bounds(window):
    try:
        import ctypes

        metrics = ctypes.windll.user32.GetSystemMetrics
        return (metrics(76), metrics(77), metrics(78), metrics(79))
    except (AttributeError, OSError):
        return (0, 0, window.winfo_screenwidth(), window.winfo_screenheight())


def compact_number(value):
    if value >= 1000000000:
        return f"{value / 1000000000:.1f}B"
    if value >= 1000000:
        return f"{value / 1000000:.1f}M"
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return f"{value:.0f}"


class CompactOverlay:
    ROW_HEIGHT = 24

    def __init__(self, app, preferences):
        self.app = app
        self.width = int(preferences.get("overlay_width", 280))
        self.width = max(220, min(420, self.width))
        self.window = tk.Toplevel(app.root)
        self.window.title("AionPulse · Overlay")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", float(preferences.get("overlay_opacity", 0.92)))
        self.window.configure(bg="#10151f")
        x = int(preferences.get("overlay_x", self.window.winfo_screenwidth() - self.width - 40))
        y = int(preferences.get("overlay_y", 120))
        self.window.geometry(f"{self.width}x76+{x}+{y}")
        self.position_timer = None
        self.saved_position = (x, y)
        self.window.bind("<Configure>", self.position_changed)
        self.canvas = tk.Canvas(
            self.window, bg="#10151f", highlightthickness=1, highlightbackground="#30445e"
        )
        self.canvas.pack(fill="both", expand=True)
        self.metric = tk.StringVar(value="all")
        self.metric.trace_add(
            "write", lambda *_: self.app.save_preferences(overlay_metric=self.metric.get())
        )
        self.mode_buttons = tk.Frame(self.window, bg="#10151f")
        self.reset_button = tk.Button(
            self.window,
            text=tr("Reiniciar"),
            command=self.app.reset,
            bg="#192232",
            fg="#e5edf7",
            activebackground="#30445e",
            activeforeground="#ffffff",
            font=("Segoe UI", 8),
            borderwidth=0,
            cursor="hand2",
            takefocus=False,
        )
        self.reset_button.place(relx=1, x=-122, y=3, width=64, height=22)
        self.mode_buttons.place(x=6, y=27, relwidth=1, width=-12, height=24)
        for value, label in MODE_BUTTONS:
            tk.Radiobutton(
                self.mode_buttons,
                text=tr(label),
                variable=self.metric,
                value=value,
                indicatoron=False,
                bg="#192232",
                fg="#e5edf7",
                selectcolor="#265c50",
                font=("Segoe UI", 8),
                padx=2,
                borderwidth=0,
            ).pack(side="left", fill="both", expand=True, padx=1)
        self.name_font = tkfont.Font(family="Segoe UI", size=9)
        self.drag = None
        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.move)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<Button-3>", self.menu)
        self.canvas.bind("<Double-Button-1>", lambda event: self.show_main())

    def refresh_language(self):
        self.reset_button.configure(text=tr("Reiniciar"))
        for button, (_, label) in zip(self.mode_buttons.winfo_children(), MODE_BUTTONS):
            button.configure(text=tr(label))
        self._frame_signature = None

    def exists(self):
        return bool(self.window.winfo_exists())

    def destroy(self):
        self.save_position()
        self.window.destroy()

    def position_changed(self, event):
        if event.widget != self.window:
            return
        if self.position_timer is not None:
            self.window.after_cancel(self.position_timer)
        self.position_timer = self.window.after(400, self.save_position)

    def save_position(self):
        if self.position_timer is not None:
            self.window.after_cancel(self.position_timer)
            self.position_timer = None
        if self.exists() and self.window.winfo_ismapped():
            position = (self.window.winfo_x(), self.window.winfo_y())
            if position != self.saved_position:
                self.app.save_preferences(overlay_x=position[0], overlay_y=position[1])
                self.saved_position = position

    def press(self, event):
        if event.y < 27 and event.x > self.width - 28:
            self.app.toggle_overlay()
            return
        if event.y < 27 and event.x > self.width - 54:
            self.show_main()
            return
        self.drag = (event.x_root, event.y_root, self.window.winfo_x(), self.window.winfo_y())

    def move(self, event):
        if not self.drag:
            return
        sx, sy, x, y = self.drag
        self.window.geometry(f"+{x + event.x_root - sx}+{y + event.y_root - sy}")

    def release(self, event):
        if self.drag and self.exists():
            self.save_position()
        self.drag = None

    def show_main(self):
        self.app.root.deiconify()
        self.app.root.lift()

    def set_width(self, width):
        self.width = width
        self.app.save_preferences(overlay_width=width)

    def set_opacity(self, opacity):
        self.window.attributes("-alpha", opacity)
        self.app.save_preferences(overlay_opacity=opacity)

    def menu(self, event):
        menu = tk.Menu(self.window, tearoff=False)
        menu.add_command(label=tr("Abrir janela principal"), command=self.show_main)
        menu.add_command(label=tr("Reiniciar"), command=self.app.reset)
        menu.add_checkbutton(label=tr("Só meu grupo"), variable=self.app.group_only)
        menu.add_checkbutton(label=tr("Valores completos"), variable=self.app.full_values)
        if hasattr(self.app, "metric"):
            metrics = tk.Menu(menu, tearoff=False)
            for value, label in MODE_MENU:
                metrics.add_radiobutton(label=tr(label), value=value, variable=self.metric)
            menu.add_cascade(label=tr("Métrica"), menu=metrics)
        sizes = tk.Menu(menu, tearoff=False)
        for width, label in [
            (220, tr("Pequeno · 220 px")),
            (280, tr("Normal · 280 px")),
            (340, tr("Largo · 340 px")),
        ]:
            sizes.add_command(label=tr(label), command=lambda w=width: self.set_width(w))
        menu.add_cascade(label=tr("Largura"), menu=sizes)
        alpha = tk.Menu(menu, tearoff=False)
        for opacity in (0.75, 0.92, 1.0):
            alpha.add_command(
                label=f"{opacity:.0%}", command=lambda value=opacity: self.set_opacity(value)
            )
        menu.add_cascade(label=tr("Opacidade"), menu=alpha)
        menu.add_separator()
        menu.add_command(label=tr("Ocultar overlay"), command=self.app.toggle_overlay)
        menu.add_command(label=tr("Encerrar medidor"), command=self.app.quit)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def clipped_name(self, name, max_width):
        if self.name_font.measure(name) <= max_width:
            return name
        while name and self.name_font.measure(name + "…") > max_width:
            name = name[:-1]
        return name + "…"

    def paint(self, rows, now=None, rates=None):
        now = time.monotonic() if now is None else now
        rates = (
            rates
            if rates is not None
            else {kind: self.app.encounter.current_rate(now, kind) for kind in METRIC_KEYS}
        )
        if self.app.group_only.get():
            rows = list(rows)
            present = {r[0] for r in rows}
            rows.extend(((actor, 0, 0, 0, 0, {}) for actor in sorted(self.app.group - present)))
        metric = self.metric.get()
        row_height = 96 if metric == "all" else self.ROW_HEIGHT
        max_rows = max(1, (self.window.winfo_screenheight() - 135) // row_height)
        visible = rows[:max_rows]
        row_count = max(1, len(visible))
        height = 74 + row_count * row_height + 22
        left, top, desktop_width, desktop_height = desktop_bounds(self.window)
        current_x, current_y = (
            (self.window.winfo_x(), self.window.winfo_y())
            if self.window.winfo_ismapped()
            else self.saved_position
        )
        x = min(max(left, current_x), max(left, left + desktop_width - self.width))
        y = min(max(top, current_y), max(top, top + desktop_height - height - 35))
        geometry = f"{self.width}x{height}+{x}+{y}"
        if getattr(self, "geometry", None) != geometry:
            self.window.geometry(geometry)
            self.geometry = geometry
        canvas = self.canvas
        scope = tr("grupo") if self.app.group_only.get() else tr("vistos")
        kinds = METRIC_KEYS if metric == "all" else (metric,)
        signature = (
            self.app.full_values.get(),
            metric,
            self.width,
            height,
            scope,
            self.app.me,
            len(rows),
            tuple(
                (
                    (
                        row[0],
                        self.app.names.get(row[0]),
                        row[1],
                        tuple(
                            (
                                (
                                    self.app.encounter.players.get(row[0], {}).get(kind, 0),
                                    rates[kind].get(row[0], 0),
                                )
                                for kind in kinds
                            )
                        ),
                    )
                    for row in visible
                )
            ),
        )
        if getattr(self, "_frame_signature", None) == signature:
            return
        self._frame_signature = signature
        canvas.delete("all")
        canvas.create_text(
            9,
            14,
            anchor="w",
            text=self.clipped_name(f"AionPulse · {len(rows)} {scope}", self.width - 135),
            fill="#65dfb5",
            font=("Segoe UI", 9, "bold"),
        )
        canvas.create_text(self.width - 41, 14, text="↗", fill="#a0aec0", font=("Segoe UI", 12))
        canvas.create_text(self.width - 14, 14, text="×", fill="#a0aec0", font=("Segoe UI", 13))
        canvas.create_text(
            12, 64, text=tr("Jogador"), anchor="w", fill="#a0aec0", font=("Segoe UI", 8)
        )
        canvas.create_text(
            self.width - 82, 64, text="Total", anchor="e", fill="#a0aec0", font=("Segoe UI", 8)
        )
        rate_label = tr(BY_KEY["damage" if metric == "all" else metric].rate)
        canvas.create_text(
            self.width - 12,
            64,
            text=tr("Agora/s") if metric == "all" else f"{rate_label}{tr(' agora')}",
            anchor="e",
            fill="#a0aec0",
            font=("Segoe UI", 8),
        )
        current = rates.get("damage" if metric == "all" else metric, {})
        all_rates = rates if metric == "all" else {}
        maxima = {
            kind: max(
                (self.app.encounter.players.get(row[0], {}).get(kind, 0) for row in rows), default=0
            )
            or 1
            for kind in METRIC_KEYS
        }
        max_total = max((row[1] for row in rows), default=0) or 1
        for i, (actor, damage, dps, *_) in enumerate(visible):
            y = 74 + i * row_height
            if metric == "all":
                player = self.app.encounter.players.get(actor, {})
                name = ("★ " if actor == self.app.me else "") + self.app.names.get(
                    actor, f"ID {actor}"
                )
                canvas.create_rectangle(
                    5, y, self.width - 5, y + 92, fill="#10151f", outline="#30445e"
                )
                canvas.create_text(
                    12,
                    y + 10,
                    text=self.clipped_name(name, self.width - 24),
                    anchor="w",
                    fill="#65dfb5" if actor == self.app.me else "#e5edf7",
                    font=("Segoe UI", 9, "bold"),
                )
                for line, (kind, label, fill) in enumerate(
                    ((entry.key, entry.button, entry.color) for entry in METRICS)
                ):
                    top = y + 20 + line * 24
                    canvas.create_rectangle(
                        6, top, self.width - 6, top + 21, fill="#192232", outline=""
                    )
                    fraction = player.get(kind, 0) / maxima[kind]
                    if fraction:
                        canvas.create_rectangle(
                            6,
                            top,
                            6 + (self.width - 12) * fraction,
                            top + 21,
                            fill=fill,
                            outline="",
                            tags=(f"bar-{kind}-{actor}",),
                        )
                    canvas.create_rectangle(6, top, 9, top + 21, fill=fill, outline="")
                    canvas.create_text(
                        12,
                        top + 11,
                        text=tr(label),
                        anchor="w",
                        fill="#f2f8ff",
                        font=self.name_font,
                    )
                    canvas.create_text(
                        self.width - 82,
                        top + 11,
                        text=self.app.display_number(player.get(kind, 0)),
                        anchor="e",
                        fill="#f2f8ff",
                        font=("Segoe UI", 9),
                    )
                    canvas.create_text(
                        self.width - 12,
                        top + 11,
                        text=self.app.display_number(all_rates[kind].get(actor, 0)),
                        anchor="e",
                        fill="#ffffff",
                        font=("Segoe UI", 9, "bold"),
                    )
                continue
            canvas.create_rectangle(6, y, self.width - 6, y + 21, fill="#192232", outline="")
            if damage:
                canvas.create_rectangle(
                    6,
                    y,
                    6 + (self.width - 12) * damage / max_total,
                    y + 21,
                    fill=BY_KEY[metric].color,
                    outline="",
                    tags=(f"bar-{metric}-{actor}",),
                )
            name = self.app.names.get(actor, f"ID {actor}")
            if actor == self.app.me:
                name = "★ " + name
            text = self.clipped_name(name, self.width - 150)
            canvas.create_text(
                12, y + 11, text=text, anchor="w", fill="#e5edf7", font=self.name_font
            )
            canvas.create_text(
                self.width - 82,
                y + 11,
                text=self.app.display_number(damage),
                anchor="e",
                fill="#a0aec0",
                font=("Segoe UI", 9),
            )
            canvas.create_text(
                self.width - 12,
                y + 11,
                text=self.app.display_number(current.get(actor, 0)),
                anchor="e",
                fill="#e5edf7",
                font=("Segoe UI", 9, "bold"),
            )
        if not rows:
            canvas.create_text(
                10,
                86,
                anchor="w",
                text=tr("Aguardando combate…"),
                fill="#a0aec0",
                font=self.name_font,
            )
        footer = (
            tr("Barras: total · Agora/s: últimos 5s")
            if len(rows) <= max_rows
            else f"+{len(rows) - max_rows}{tr(' fora da tela')}"
        )
        canvas.create_text(
            9, height - 11, anchor="w", text=footer, fill="#a0aec0", font=("Segoe UI", 8)
        )
