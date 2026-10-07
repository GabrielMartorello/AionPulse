# SPDX-License-Identifier: GPL-3.0-only
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Metric:
    key: str
    button: str
    label: str
    rate: str
    color: str


METRICS = (
    Metric("damage", "DPS", "Dano causado", "DPS", "#3269a1"),
    Metric("healing", "Cura", "Cura realizada", "HPS", "#268068"),
    Metric("received", "Recebido", "Dano recebido", "Dano/s", "#926b34"),
)
BY_KEY = {metric.key: metric for metric in METRICS}
METRIC_KEYS = tuple(BY_KEY)
MODES = METRIC_KEYS + ("all",)
MODE_BUTTONS = tuple((metric.key, metric.button) for metric in METRICS) + (("all", "Tudo"),)
MODE_MENU = tuple((metric.key, metric.label) for metric in METRICS) + (("all", "Tudo"),)


def normalize_mode(value):
    value = {"recovery": "healing", "absorbed": "received", "defenses": "received"}.get(
        value, value
    )
    return value if value in MODES else "all"
