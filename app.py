# SPDX-License-Identifier: GPL-3.0-only
import sys
import csv
import json
import queue
import time
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog
from capture import Capture
from stats import Encounter
from overlay import CompactOverlay, compact_number
from identity_cache import IdentityCache
from party import resolve_party_roster
from config import APP_ROOT as BASE, DATA_ROOT, Preferences
from i18n import LANGUAGES, set_language, tr
from metadata import VERSION, AUTHOR, AUTHOR_URL
from widgets import ValueSwitch
from metrics import BY_KEY, METRIC_KEYS, MODE_BUTTONS, MODE_MENU

BG = "#10151f"
PANEL = "#192232"
TEXT = "#e5edf7"
MUTED = "#a0aec0"
ACCENT = "#65dfb5"


class App:
    def __init__(self, root):
        self.root = root
        root.title(f"AionPulse · {VERSION}")
        self.window_icon = tk.PhotoImage(file=str(BASE / "assets" / "aionpulse-256.png"))
        self.header_icon = tk.PhotoImage(file=str(BASE / "assets" / "aionpulse-64.png"))
        root.iconphoto(True, self.window_icon)
        if sys.platform == "win32":
            root.iconbitmap(default=str(BASE / "assets" / "aionpulse.ico"))
            root.iconbitmap(str(BASE / "assets" / "aionpulse.ico"))
            from branding import apply_window_icon

            root.after(250, lambda: apply_window_icon(root, BASE / "assets" / "aionpulse.ico"))
        root.geometry("880x800")
        root.minsize(850, 780)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.events = queue.Queue(maxsize=20000)
        self.capture = Capture(self.events)
        self.encounter = Encounter()
        self.names = {}
        self.preferences = Preferences()
        self.language = tk.StringVar(
            value=LANGUAGES.get(self.preferences.values.get("language"), LANGUAGES["pt-BR"])
        )
        set_language(self.preferences.values.get("language"))
        self.full_values = tk.BooleanVar(
            value=bool(self.preferences.values.get("full_values", False))
        )
        self.full_values.trace_add(
            "write", lambda *_: self.save_preferences(full_values=self.full_values.get())
        )
        self.connected_region = "aguardando conexão"
        self.region_text = tk.StringVar()
        self.identity_cache = IdentityCache(DATA_ROOT / "identity-cache.json")
        self.connection = None
        self.cache_written = 0
        self.cache_dirty = False
        self.state_written = 0
        self.me = None
        self.identity = tk.StringVar(
            value="Meu personagem: aguardando pacote de identidade do jogo"
        )
        self.group = set()
        self.roster_confirmed = False
        self.status_members = set()
        self.group_only = tk.BooleanVar(value=True)
        self.metric = tk.StringVar(value="all")
        self.metric.trace_add(
            "write", lambda *_: self.save_preferences(main_metric=self.metric.get())
        )
        self.overlay = None
        self.status = tk.StringVar(value=tr("Pronto. Escolha a interface e inicie a captura."))
        self.port = tk.StringVar(value="13328")
        self.summary = tk.StringVar(value=tr("Aguardando combate"))
        self.identification = tk.StringVar()
        self.diagnostics = tk.StringVar(value=tr("Nenhum pacote capturado"))
        self.configure_style()
        self.build()
        self.root.after(250, self.tick)

    def configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("TButton", padding=(12, 7), background=PANEL, foreground=TEXT)
        style.map("TButton", background=[("active", "#263750")])
        style.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=TEXT)
        style.map(
            "TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TEXT)]
        )
        style.configure("TEntry", fieldbackground=PANEL, foreground=TEXT)
        style.configure(
            "Treeview",
            background=PANEL,
            fieldbackground=PANEL,
            foreground=TEXT,
            rowheight=30,
            borderwidth=0,
        )
        style.configure("Treeview.Heading", background="#253247", foreground=TEXT, padding=8)
        style.map("Treeview", background=[("selected", "#30445e")])
        style.configure("TCheckbutton", background=BG, foreground=TEXT)

    def label(self, parent, text, size=10, color=TEXT):
        return tk.Label(parent, text=text, bg=BG, fg=color, font=("Segoe UI", size))

    def build(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=22, pady=(18, 10))
        tk.Label(header, image=self.header_icon, bg=BG).pack(side="left", padx=(0, 14), anchor="n")
        self.label(header, "AionPulse", 24, ACCENT).pack(anchor="w")
        self.region_text.set(f"AION2 · {tr('Região')}: {tr(self.connected_region)}")
        tk.Label(
            header, textvariable=self.region_text, bg=BG, fg=MUTED, font=("Segoe UI", 11)
        ).pack(anchor="w")
        self.label(header, f"v{VERSION}", 10, MUTED).pack(anchor="w", pady=(4, 0))
        credits = self.label(header, f"{tr('Créditos')} · GitHub: {AUTHOR}", 10, ACCENT)
        credits.configure(cursor="hand2", font=("Segoe UI", 10, "underline"))
        credits.pack(anchor="w", pady=(2, 0))
        credits.bind("<Button-1>", lambda _event: webbrowser.open(AUTHOR_URL))
        languages = ttk.Combobox(
            header,
            state="readonly",
            width=18,
            textvariable=self.language,
            values=list(LANGUAGES.values()),
        )
        languages.pack(anchor="e")
        languages.bind("<<ComboboxSelected>>", self.change_language)
        controls = tk.Frame(self.root, bg=BG)
        controls.pack(fill="x", padx=22, pady=8)
        try:
            self.interfaces = Capture.interfaces()
        except Exception as error:
            self.interfaces = []
            self.status.set(f"{tr('Npcap indisponível: ')}{error}")
        self.interface = ttk.Combobox(
            controls, state="readonly", width=27, values=[name for name, _ in self.interfaces]
        )
        self.interface.pack(side="left")
        if self.interfaces:
            default = next(
                (
                    i
                    for i, (_, iface) in enumerate(self.interfaces)
                    if iface.ip and (not iface.ip.startswith(("127.", "169.254.")))
                ),
                0,
            )
            self.interface.current(default)
        self.label(controls, tr(" Porta ")).pack(side="left")
        ttk.Entry(controls, textvariable=self.port, width=7).pack(side="left", padx=(0, 8))
        self.start_button = ttk.Button(controls, text=tr("Iniciar"), command=self.start)
        self.start_button.pack(side="left", padx=4)
        ttk.Button(controls, text=tr("Pausar"), command=self.pause).pack(side="left", padx=4)
        ttk.Button(controls, text=tr("Reiniciar"), command=self.reset).pack(side="left", padx=4)
        self.label(self.root, "").pack()
        tk.Label(self.root, textvariable=self.summary, bg=BG, fg=TEXT, font=("Segoe UI", 14)).pack(
            anchor="w", padx=22
        )
        tk.Label(
            self.root,
            textvariable=self.identification,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
            wraplength=810,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=22, pady=(4, 0))
        mode_buttons = tk.Frame(self.root, bg=BG)
        mode_buttons.pack(fill="x", padx=22, pady=5)
        for value, label in MODE_BUTTONS:
            tk.Radiobutton(
                mode_buttons,
                text=tr(label),
                variable=self.metric,
                value=value,
                indicatoron=False,
                bg=PANEL,
                fg=TEXT,
                selectcolor="#265c50",
                padx=15,
                pady=6,
            ).pack(side="left", padx=3)
        columns = (
            "name",
            "damage",
            "dps",
            "current",
            "hits",
            "crit",
            "heal_total",
            "hps",
            "received_total",
            "received_rate",
        )
        self.table = ttk.Treeview(
            self.root, columns=columns, show="headings", selectmode="extended"
        )
        for column, title, width in [
            ("name", tr("Jogadores vistos"), 260),
            ("damage", tr("Dano total"), 125),
            ("dps", tr("DPS médio"), 100),
            ("current", tr("DPS agora (5s)"), 110),
            ("hits", tr("Eventos"), 65),
            ("crit", tr("Críticos"), 70),
        ]:
            self.table.heading(column, text=tr(title))
            self.table.column(column, width=width, anchor="w" if column == "name" else "e")
        self.table.tag_configure("me", foreground=ACCENT)
        for column, title in [
            ("heal_total", tr("Cura total")),
            ("hps", tr("HPS agora")),
            ("received_total", tr("Recebido total")),
            ("received_rate", tr("Recebido/s")),
        ]:
            self.table.heading(column, text=tr(title))
            self.table.column(column, width=100, anchor="e")
        self.table.pack(fill="both", expand=True, padx=22, pady=12)
        table_scroll = ttk.Scrollbar(self.root, orient="horizontal", command=self.table.xview)
        table_scroll.pack(fill="x", padx=22)
        self.table.configure(xscrollcommand=table_scroll.set)
        self.table.bind("<Double-1>", self.skill_details)
        self.comparison = tk.Canvas(self.root, bg=PANEL, height=56, highlightthickness=0)
        self.comparison.pack(fill="x", padx=22, pady=(0, 6))
        group_controls = tk.Frame(self.root, bg=BG)
        group_controls.pack(fill="x", padx=22, pady=3)
        self.label(group_controls, tr("Party detectada pelo jogo"), color=MUTED).pack(
            side="left", padx=8
        )
        metric_menu = ttk.Menubutton(group_controls, text=tr("Métrica"))
        metric_choices = tk.Menu(metric_menu, tearoff=False)
        for value, label in MODE_MENU:
            metric_choices.add_radiobutton(label=tr(label), value=value, variable=self.metric)
        metric_menu.configure(menu=metric_choices)
        metric_menu.pack(side="left", padx=5)
        ttk.Checkbutton(group_controls, text=tr("Só meu grupo"), variable=self.group_only).pack(
            side="left", padx=8
        )
        ValueSwitch(group_controls, self.full_values, tr("Valores completos"), BG, TEXT).pack(
            side="left", padx=8
        )
        tools = tk.Frame(self.root, bg=BG)
        tools.pack(fill="x", padx=22, pady=8)
        ttk.Button(tools, text="Overlay", command=self.toggle_overlay).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(tools, text=tr("Exportar CSV"), command=self.export).pack(side="left", padx=6)
        ttk.Button(tools, text=tr("Diagnóstico local"), command=self.save_diagnostics).pack(
            side="left", padx=6
        )
        tk.Label(
            self.root, textvariable=self.status, bg=BG, fg=ACCENT, anchor="w", wraplength=770
        ).pack(fill="x", padx=22)
        tk.Label(
            self.root,
            textvariable=self.diagnostics,
            bg=BG,
            fg=MUTED,
            anchor="w",
            font=("Segoe UI", 9),
        ).pack(fill="x", padx=22, pady=(3, 12))

    def start(self):
        if self.capture.thread and self.capture.thread.is_alive():
            self.status.set(tr("A captura já está ativa; aguarde ao pausar antes de reiniciar."))
            return
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError()
            index = self.interface.current()
            if index < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                tr("Configuração"), tr("Selecione uma interface e uma porta entre 1 e 65535.")
            )
            return
        self.reset()
        self.capture.start(self.interfaces[index][1], port)

    def pause(self):
        self.capture.stop()
        self.status.set(tr("Captura pausada. Os totais permanecem na tela."))

    def reset(self):
        for _ in range(5):
            self._drain_events()
            if self.events.empty():
                break
        self.encounter.clear()

    def selected(self):
        return {int(item) for item in self.table.selection()}

    def change_language(self, _event=None):
        code = next(
            (code for code, label in LANGUAGES.items() if label == self.language.get()), "pt-BR"
        )
        self.save_preferences(language=code)
        set_language(code)
        index = self.interface.current()
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Toplevel):
                widget.destroy()
        self._table_mode = None
        self._comparison_signature = None
        self.build()
        if 0 <= index < len(self.interfaces):
            self.interface.current(index)
        self.status.set(tr("Aguardando combate"))
        if self.overlay and self.overlay.exists():
            self.overlay.refresh_language()

    def display_number(self, value):
        if self.full_values.get():
            separator = "." if self.language.get() == LANGUAGES["pt-BR"] else ","
            return f"{value:,.0f}".replace(",", separator)
        return compact_number(value)

    def rows(self, metric=None, now=None):
        now = time.monotonic() if now is None else now
        metric = metric or self.metric.get()
        rows = self.encounter.rows(
            now,
            self.group if self.group_only.get() else None,
            "damage" if metric == "all" else metric,
        )
        if self.group_only.get():
            present = {row[0] for row in rows}
            rows.extend(((actor, 0, 0, 0, 0, {}) for actor in sorted(self.group - present)))
        return rows

    def actor_name(self, actor):
        return (tr("VOCÊ · ") if actor == self.me else "") + self.names.get(actor, f"ID {actor}")

    def paint_comparison(self, rows):
        canvas = self.comparison
        width = max(700, canvas.winfo_width())
        kinds = METRIC_KEYS if self.metric.get() == "all" else (self.metric.get(),)
        signature = (
            self.full_values.get(),
            width,
            kinds,
            self.me,
            tuple(
                (
                    (
                        row[0],
                        self.names.get(row[0]),
                        tuple(
                            (self.encounter.players.get(row[0], {}).get(kind, 0) for kind in kinds)
                        ),
                    )
                    for row in rows
                )
            ),
        )
        if getattr(self, "_comparison_signature", None) == signature:
            return
        self._comparison_signature = signature
        canvas.delete("all")
        canvas.configure(height=24 + 24 * len(rows))
        cell = width / len(kinds)
        labels = {key: tr(metric.button) for key, metric in BY_KEY.items()}
        colors = {key: metric.color for key, metric in BY_KEY.items()}
        for index, kind in enumerate(kinds):
            left = index * cell
            maximum = (
                max(
                    (self.encounter.players.get(row[0], {}).get(kind, 0) for row in rows), default=0
                )
                or 1
            )
            canvas.create_text(
                left + 4,
                11,
                text=f"{labels[kind]} · total",
                anchor="w",
                fill=MUTED,
                font=("Segoe UI", 9),
            )
            for rank, row in enumerate(rows):
                value = self.encounter.players.get(row[0], {}).get(kind, 0)
                y = 24 + rank * 24
                canvas.create_rectangle(left + 4, y, left + cell - 5, y + 19, fill=BG, outline="")
                if value:
                    canvas.create_rectangle(
                        left + 4,
                        y,
                        left + 4 + (cell - 9) * value / maximum,
                        y + 19,
                        fill=colors[kind],
                        outline="",
                    )
                name = ("★ " if row[0] == self.me else "") + self.names.get(row[0], f"ID {row[0]}")
                canvas.create_text(
                    left + 10, y + 10, text=name[:19], anchor="w", fill=TEXT, font=("Segoe UI", 9)
                )
                canvas.create_text(
                    left + cell - 10,
                    y + 10,
                    text=self.display_number(value),
                    anchor="e",
                    fill=TEXT,
                    font=("Segoe UI", 9),
                )

    def tick(self):
        self._drain_events()
        self.identification.set(self.identification_message())
        now = time.monotonic()
        self._save_identity(now)
        rows = self.rows(now=now)
        rates = {kind: self.encounter.current_rate(now, kind) for kind in METRIC_KEYS}
        self._render_table(rows, now, rates)
        diag = self.capture.diagnostics()
        self.paint_comparison(rows)
        self.diagnostics.set(
            f"{tr('Pacotes ')}{diag['packets']:,}{tr(' · quadros ')}{diag['frames']:,}{tr(' · danos ')}{diag['damage_events']:,} · perdas {diag['queue_dropped'] + diag['kernel_dropped']}{tr(' · erros ')}{diag['parse_errors']}{tr(' · ressincronizações ')}{diag['sync_skipped']}"
        )
        if (
            diag["queue_dropped"]
            or diag["kernel_dropped"]
            or diag["tcp_resets"]
            or diag["parse_errors"]
        ):
            self.status.set(
                tr(
                    "Captura incompleta: houve descartes/erros; não confie nos totais deste combate."
                )
            )
        if self.overlay and self.overlay.exists():
            self.overlay.paint(self.rows(self.overlay.metric.get(), now), now, rates)
        self._save_state(rows, diag, now)
        self.root.after(250, self.tick)

    def identification_message(self):
        if not self.group:
            return tr(
                "Aguardando identificação. Abra o medidor antes de entrar no jogo ou trocar de área. Não é necessário combater."
            )
        if self.me is None or any(actor not in self.names for actor in self.group):
            return tr(
                "Identificação parcial. Para receber os nomes, mantenha o medidor aberto e troque de área/canal; aproxime-se dos integrantes. Não é necessário combater."
            )
        return tr(
            "Nomes dos integrantes observados identificados. A party é atualizada conforme os pacotes recebidos."
        )

    def _drain_events(self):
        for _ in range(5000):
            try:
                kind, data = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "connection":
                connection, is_new = data
                if connection != self.connection or is_new:
                    self.connection = connection
                    self.names, self.me, self.group = (
                        ({}, None, set()) if is_new else self.identity_cache.restore(connection)
                    )
                    self.roster_confirmed = (
                        False if is_new else self.identity_cache.roster_confirmed
                    )
                    self.status_members.clear()
                    if self.me is not None:
                        self.group.add(self.me)
                        self.identity.set(
                            f"Meu personagem: {self.names[self.me]} · identidade restaurada nesta conexão"
                        )
                    else:
                        self.identity.set("Meu personagem: aguardando pacote de identidade do jogo")
                    self.cache_dirty = True
                    self.pending_roster = None
            elif kind == "region":
                self.connected_region = data
                self.region_text.set(f"AION2 · {tr('Região')}: {tr(data)}")
            elif kind == "hit":
                self.encounter.add(*data)
            elif kind == "incoming":
                self.encounter.add_received(*data)
            elif kind == "heal":
                self.encounter.add_heal(*data)
            elif kind == "tank":
                self.encounter.add_tank(*data)
            elif kind == "party":
                actor, name, slot = data
                if slot == 0:
                    if not self.roster_confirmed:
                        if len(self.status_members) < 6:
                            self.status_members.add(actor)
                        self.group.update(self.status_members)
                        self.cache_dirty = True
                    continue
                if slot > 0:
                    self.pending_roster = None
                self.group.add(actor)
                self.cache_dirty = True
                if name:
                    self.names[actor] = name
                    self.cache_dirty = True
            elif kind == "party_snapshot":
                members = {actor for actor, _, _ in data}
                if self.me in members:
                    self.roster_confirmed = True
                    self.status_members.clear()
                    self.group.clear()
                    self.group.update(members)
                    self.cache_dirty = True
                    self.status.set(
                        f"{tr('Party atualizada pelo jogo: ')}{len(members)}{tr(' membro(s).')}"
                    )
            elif kind == "party_roster":
                self.pending_roster = data
                self.apply_pending_roster()
            elif kind == "name":
                actor, name, is_me = data
                self.names[actor] = name
                self.cache_dirty = True
                if is_me:
                    self.me = actor
                    self.group.add(actor)
                    if not self.roster_confirmed:
                        self.group.update(self.status_members)
                    self.identity.set(f"Meu personagem: {name} · identificado pelo jogo")
                self.apply_pending_roster()
            elif kind == "status":
                self.status.set(data)
            elif kind == "error":
                self.status.set(f"{tr('Falha: ')}{data}")

    def _save_identity(self, now):
        if self.connection and self.cache_dirty and (now - self.cache_written >= 2):
            try:
                self.identity_cache.save(
                    self.connection,
                    self.names,
                    self_id=self.me,
                    group=self.group,
                    roster_confirmed=self.roster_confirmed,
                )
                self.cache_dirty = False
                self.cache_written = now
            except OSError:
                pass

    def _render_table(self, rows, now, rates):
        selected_metric = self.metric.get()
        current = rates["damage" if selected_metric == "all" else selected_metric]
        healing_rate = rates["healing"]
        received_rate = rates["received"]
        definition = BY_KEY["damage" if selected_metric == "all" else selected_metric]
        metric_label, rate_label = (tr(definition.label), tr(definition.rate))
        if getattr(self, "_table_mode", None) != selected_metric:
            self.table.configure(
                displaycolumns=(
                    "name",
                    "damage",
                    "current",
                    "heal_total",
                    "hps",
                    "received_total",
                    "received_rate",
                )
                if selected_metric == "all"
                else ("name", "damage", "dps", "current", "hits", "crit")
            )
            self.table.column("name", width=190 if selected_metric == "all" else 260)
            self.table.heading("damage", text=f"{metric_label}{tr(' total')}")
            self.table.heading("dps", text=f"{rate_label}{tr(' médio')}")
            self.table.heading("current", text=f"{rate_label}{tr(' agora (5s)')}")
            self._table_mode = selected_metric
        ids = {str(row[0]) for row in rows}
        for item in self.table.get_children():
            if item not in ids:
                self.table.delete(item)
        for index, (actor, damage, dps, hits, crit, skills) in enumerate(rows):
            values = (
                self.actor_name(actor),
                f"{damage:,}",
                f"{dps:,.0f}",
                f"{current.get(actor, 0):,.0f}",
                hits,
                f"{crit / hits:.0%}" if hits else "0%",
            )
            player = self.encounter.players.get(actor, {})
            values += (
                f"{player.get('healing', 0):,}",
                f"{healing_rate.get(actor, 0):,.0f}",
                f"{player.get('received', 0):,}",
                f"{received_rate.get(actor, 0):,.0f}",
            )
            if self.table.exists(str(actor)):
                self.table.item(str(actor), values=values, tags=("me",) if actor == self.me else ())
                self.table.move(str(actor), "", index)
            else:
                self.table.insert(
                    "",
                    index,
                    iid=str(actor),
                    values=values,
                    tags=("me",) if actor == self.me else (),
                )
        seconds = self.encounter.duration(now, self.group if self.group_only.get() else None)
        total = sum((row[1] for row in rows))
        current_total = sum((current.get(row[0], 0) for row in rows))
        self.summary.set(
            f"{metric_label} · {seconds:.1f}s · total {total:,} · {rate_label}{tr(' médio ')}{total / max(1, seconds):,.0f}{tr(' · agora ')}{current_total:,.0f}"
        )
        if selected_metric == "all":
            self.summary.set(
                f"Todas as métricas · {seconds:.1f}s · DPS {current_total:,.0f} · HPS {sum((healing_rate.get(r[0], 0) for r in rows)):,.0f}{tr(' · recebido/s ')}{sum((received_rate.get(r[0], 0) for r in rows)):,.0f}"
            )

    def _save_state(self, rows, diag, now):
        if "--diagnostic-state" in sys.argv and now - self.state_written >= 1:
            try:
                state = {
                    "version": VERSION,
                    "region": self.connected_region,
                    "language": self.preferences.values.get("language", "pt-BR"),
                    "updated": time.time(),
                    "me": self.me,
                    "status": self.status.get(),
                    "capturing": bool(self.capture.thread and self.capture.thread.is_alive()),
                    "group": sorted(self.group),
                    "group_only": self.group_only.get(),
                    "rows": [
                        {
                            "id": row[0],
                            "name": self.names.get(row[0], ""),
                            "total": row[1],
                            "damage": self.encounter.players.get(row[0], {}).get("damage", 0),
                            "received": self.encounter.players.get(row[0], {}).get("received", 0),
                            "healing": self.encounter.players.get(row[0], {}).get("healing", 0),
                            "health_received": self.encounter.players.get(row[0], {}).get(
                                "health_received", 0
                            ),
                            "mitigated": self.encounter.players.get(row[0], {}).get("mitigated", 0),
                            "absorbed": self.encounter.players.get(row[0], {}).get("absorbed", 0),
                            "defenses": self.encounter.players.get(row[0], {}).get("defenses", 0),
                            "block": self.encounter.players.get(row[0], {}).get("block", 0),
                            "parry": self.encounter.players.get(row[0], {}).get("parry", 0),
                            "recovery": self.encounter.players.get(row[0], {}).get("recovery", 0),
                        }
                        for row in rows
                    ],
                    "capture": diag,
                }
                (DATA_ROOT / "runtime-state.json").write_text(
                    json.dumps(state, ensure_ascii=False), encoding="utf-8"
                )
                self.state_written = now
            except OSError:
                pass

    def apply_pending_roster(self):
        resolved = resolve_party_roster(getattr(self, "pending_roster", None), self.names, self.me)
        if resolved is not None:
            self.roster_confirmed = True
            self.status_members.clear()
            self.group = {actor for actor, _, _ in resolved}
            self.names.update({actor: name for actor, name, _ in resolved})
            self.pending_roster = None
            self.cache_dirty = True
            self.status.set(
                f"{tr('Party atualizada pelo jogo: ')}{len(self.group)}{tr(' membro(s).')}"
            )

    def toggle_overlay(self):
        if self.overlay and self.overlay.exists():
            self.overlay.destroy()
            self.overlay = None
            self.root.deiconify()
            return
        self.overlay = CompactOverlay(self, self.preferences.values)
        self.overlay.paint(self.rows(self.overlay.metric.get()))

    def save_preferences(self, **changes):
        self.preferences.update(**changes)

    def skill_details(self, _event=None):
        actors = self.selected()
        if len(actors) != 1:
            return
        actor = next(iter(actors))
        stats = self.encounter.players.get(actor)
        if not stats:
            messagebox.showinfo(tr("Detalhes"), tr("Ainda não há eventos para este membro."))
            return
        detail = tk.Toplevel(self.root)
        detail.title(f"{tr('Habilidades · ')}{self.actor_name(actor)}")
        detail.geometry("440x350")
        tree = ttk.Treeview(detail, columns=("id", "damage", "share"), show="headings")
        for column, label in [
            ("id", tr("ID da habilidade")),
            ("damage", tr("Dano")),
            ("share", tr("Participação")),
        ]:
            tree.heading(column, text=label)
            tree.column(column, width=140)
        tree.pack(fill="both", expand=True)
        metric = "damage" if self.metric.get() == "all" else self.metric.get()
        skills = stats["skills"] if metric == "damage" else stats["support_skills"][metric]
        tree.heading("damage", text="Total")
        for skill, amount in sorted(skills.items(), key=lambda item: item[1], reverse=True):
            tree.insert(
                "", "end", values=(skill, f"{amount:,}", f"{amount / max(1, stats[metric]):.1%}")
            )

    def export(self):
        path = filedialog.asksaveasfilename(
            title=tr("Salvar relatório local"),
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            if self.metric.get() == "all":
                writer.writerow(
                    [
                        "actor_id",
                        "nome",
                        "dano_total",
                        "dps_5s",
                        "cura_total",
                        "hps_5s",
                        "recebido_total",
                        "recebido_s_5s",
                    ]
                )
                rates = {
                    kind: self.encounter.current_rate(time.monotonic(), kind)
                    for kind in METRIC_KEYS
                }
                for actor, *_ in self.rows():
                    player = self.encounter.players.get(actor, {})
                    values = [actor, self.names.get(actor, "")]
                    for kind in METRIC_KEYS:
                        values.extend((player.get(kind, 0), round(rates[kind].get(actor, 0), 2)))
                    writer.writerow(values)
                self.status.set(tr("Todas as métricas salvas no CSV local."))
                return
            writer.writerow(
                [
                    "actor_id",
                    "nome",
                    "metrica",
                    "total",
                    "media_por_s",
                    "agora_por_s_5s",
                    "eventos",
                    "criticos",
                    "duracao_s",
                    "experimental",
                ]
            )
            seconds = self.encounter.duration(
                time.monotonic(), self.group if self.group_only.get() else None
            )
            current = self.encounter.current_rate(time.monotonic(), self.metric.get())
            for actor, damage, dps, hits, crit, _ in self.rows():
                writer.writerow(
                    [
                        actor,
                        self.names.get(actor, ""),
                        self.metric.get(),
                        damage,
                        round(dps, 2),
                        round(current.get(actor, 0), 2),
                        hits,
                        crit,
                        round(seconds, 2),
                        True,
                    ]
                )
        self.status.set(tr("Relatório salvo localmente."))

    def save_diagnostics(self):
        path = filedialog.asksaveasfilename(
            title=tr("Salvar contadores locais"),
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if path:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(self.capture.diagnostics(), file, indent=2)
            self.status.set(tr("Diagnóstico salvo; contém apenas contadores, sem pacotes brutos."))

    def close(self):
        if self.overlay and self.overlay.exists():
            self.overlay.destroy()
            self.overlay = None
        self.root.withdraw()

    def show_overlay(self):
        if not self.overlay or not self.overlay.exists():
            self.toggle_overlay()
        self.root.withdraw()
        self.overlay.window.lift()

    def quit(self):
        if self.overlay and self.overlay.exists():
            self.overlay.save_position()
        self.capture.stop()
        self.root.update_idletasks()
        for timer in self.root.tk.call("after", "info"):
            self.root.after_cancel(timer)
        self.root.destroy()


def main():
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AionPulse.Meter")
    from instance import Instance

    instance = Instance(DATA_ROOT.resolve())
    if instance.existing:
        sys.exit(0)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    sys.stderr = open(DATA_ROOT / "inicializacao.log", "a", encoding="utf-8")
    root = tk.Tk()
    application = App(root)
    instance.poll(root, application.show_overlay)
    if "--capture" in sys.argv:
        root.after(400, application.start)
    if "--overlay" in sys.argv:
        root.after(600, application.toggle_overlay)
        if "--show-main" not in sys.argv:
            root.after(700, root.withdraw)
    root.mainloop()


if __name__ == "__main__":
    main()
