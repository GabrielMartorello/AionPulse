# SPDX-License-Identifier: GPL-3.0-only
import tkinter as tk


class ValueSwitch(tk.Frame):
    def __init__(self, parent, variable, text, background, foreground):
        super().__init__(parent, bg=background)
        self.variable = variable
        self.label = tk.Label(self, text=text, bg=background, fg=foreground, font=("Segoe UI", 10))
        self.label.pack(side="left", padx=(0, 6))
        self.track = tk.Canvas(
            self,
            width=34,
            height=18,
            bg=background,
            highlightthickness=0,
            cursor="hand2",
            takefocus=True,
        )
        self.track.pack(side="left")
        for widget in (self.label, self.track):
            widget.bind("<Button-1>", self.toggle)
        self.track.bind("<space>", self.toggle)
        self.trace = variable.trace_add("write", self.draw)
        self.bind("<Destroy>", self.remove_trace)
        self.draw()

    def toggle(self, _event=None):
        self.variable.set(not self.variable.get())
        return "break"

    def draw(self, *_args):
        self.track.delete("all")
        active = self.variable.get()
        color = "#268068" if active else "#4b5565"
        self.track.create_oval(0, 0, 18, 18, fill=color, outline="")
        self.track.create_oval(16, 0, 34, 18, fill=color, outline="")
        self.track.create_rectangle(9, 0, 25, 18, fill=color, outline="")
        x = 18 if active else 2
        self.track.create_oval(x, 2, x + 14, 16, fill="#ffffff", outline="")

    def remove_trace(self, event):
        if event.widget == self:
            self.variable.trace_remove("write", self.trace)
