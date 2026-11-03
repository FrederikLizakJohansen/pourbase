#!/usr/bin/env python3
"""Render looping videos of the periodic table of stable species as pH, potential or temperature change.

Each frame is a ``pourbase.screen_periodic_table`` calculation. Run from the repository root::

    python scripts/animate_periodic_table.py --preview 0 0.3 0.6           # PNG stills, a few seconds
    python scripts/animate_periodic_table.py                               # the default video, a few minutes
    python scripts/animate_periodic_table.py --sweep temperature --format 4x5 --theme dark
    python scripts/animate_periodic_table.py --sweep all --format all --theme all --jobs 3

Files go to ``animations/`` as ``pourbase_<sweep>_<format>_<theme>.mp4``. Videos need ffmpeg on the PATH.
The Inter font and the ``gui`` extra (for the logo) are optional; without them the script uses DejaVu Sans
and writes the logo as text.

The script is meant to be edited. Settings, themes, formats and sweeps are at the top. ``compose`` lists the
parts of the video; each part is a ``draw_`` function that takes the ``Scene``, draws with matplotlib and
returns ``None``, or a function of the frame number if it changes during the loop. ``scene.screens[frame]``
holds the full calculation for a frame. For example, to add a live count, add this to ``compose``::

    def draw_dissolved_count(scene):
        label = scene.canvas.text(60, 195, "", fontsize=14, color=scene.theme.ink)

        def update(frame):
            elements = scene.screens[frame].elements
            label.set_text(f"{sum(e.category is Category.DISSOLVED_OR_GAS for e in elements)} elements dissolved")

        return update

A sweep's path maps ``t`` from 0 to 1 onto pH, potential and temperature. Each ``--jobs`` worker uses about
1 GB of memory.
"""

from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from itertools import product
from multiprocessing import get_context
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib import font_manager
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
from matplotlib.text import Text

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))
import pourbase as pb  # noqa: E402
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, WATER_GIBBS_ENERGY_J_MOL  # noqa: E402
from pourbase.overview import Category  # noqa: E402
from pourbase.temperature import water_gibbs_energy_J_mol  # noqa: E402

# ---------------------------------------------------------------- SETTINGS

TITLE = "The stable species across the periodic table"
# Rounded by hand; the exact counts are in STATISTICS.md.
STATS = "1,700+ species   ·   5,000+ sourced values   ·   75 elemental systems"
INSTALL_LINE = "pip install pourbase"
LOG10_CONCENTRATION = -6  # log10 of the metal concentration in mol/L
FPS = 30
PH_RANGE = (0.0, 14.0)  # axes of the pH–potential panel
U_RANGE = (-1.2, 1.8)
TEMPERATURE_RANGE_C = (0.0, 100.0)  # the range pourbase supports, and the ends of the gauge
MIN_RUN_FRAMES = 4  # a species stable for fewer frames shows as the species before it, which avoids flashes
FONT = "Inter"
ENCODER_THREADS = 3  # ffmpeg threads per video
SHINE_SWEEPS_PER_LOOP = 2  # how many times the highlight crosses the statistics line

# The colours of the desktop application.
CATEGORY_COLORS = {
    Category.DISSOLVED_OR_GAS: "#5b9bd5",
    Category.SOLID_OXIDE: "#ee7d4f",
    Category.HYDROXIDE: "#f5b75a",
    Category.ELEMENTAL_SOLID: "#a0aab5",
    Category.ELEMENTAL_LIQUID: "#b79ddb",
    Category.OTHER_SOLID: "#79c07f",
    Category.INCOMPLETE: "#f2a0a0",
}
LEGEND = (
    (Category.DISSOLVED_OR_GAS, "Dissolved or gas"),
    (Category.SOLID_OXIDE, "Oxide"),
    (Category.HYDROXIDE, "Hydroxide"),
    (Category.ELEMENTAL_SOLID, "Metal"),
    (Category.ELEMENTAL_LIQUID, "Liquid metal"),
    (Category.OTHER_SOLID, "Other solid"),
)
TILE_INK = "#1f2328"
WATER_COLOR = "#5b9bd5"
SHINE_COLORS = ("#ee7d4f", "#f5b75a")  # edge and centre of the highlight
HEAT_COLORS = LinearSegmentedColormap.from_list("heat", ("#5b9bd5", "#b79ddb", "#ee7d4f"))  # cold to hot


@dataclass(frozen=True)
class Theme:
    background: str
    ink: str
    muted: str
    faint: str
    ghost: str  # symbols of elements outside the database
    water_alpha: float
    logo: str  # file in docs/


THEMES = {
    "light": Theme(background="#f5f3ef", ink="#1f2328", muted="#8a8f96", faint="#e4e1db", ghost="#b9bcc0",
                   water_alpha=0.07, logo="logo-wordmark.svg"),
    "dark": Theme(background="#15181c", ink="#e8eaed", muted="#8b929a", faint="#2a2f36", ghost="#4a5058",
                  water_alpha=0.10, logo="logo-wordmark-dark.svg"),
}


@dataclass(frozen=True)
class Format:
    """Positions in pixels from the top left; font sizes in points."""

    width: int
    height: int
    margin: float
    title: tuple[float, float]  # baseline y, font size
    subtitle: tuple[float, float]  # baseline y, font size
    logo: tuple[int, float]  # height, bottom edge y
    table: tuple[float, float]  # top y, distance between tiles
    legend: tuple[float, float]  # gap below the table, font size
    panel: tuple[float, float, float, float]  # left, top, width, height of the pH–potential panel
    panel_font: float
    readout: tuple[float, float, float]  # x, baseline y, font size
    readout_stacked: bool  # one quantity per line
    stats: tuple[float, float]  # y, font size
    install: tuple[float, float, float, str]  # x, y, font size, horizontal alignment


FORMATS = {
    "16x9": Format(width=1920, height=1080, margin=60, title=(118, 28), subtitle=(156, 13.5), logo=(46, 128),
                   table=(215, 64), legend=(42, 13), panel=(1335, 235, 525, 570), panel_font=12,
                   readout=(1335, 190, 19), readout_stacked=False, stats=(968, 27),
                   install=(960, 1022, 14, "center")),
    "1x1": Format(width=1080, height=1080, margin=40, title=(74, 22), subtitle=(106, 11.5), logo=(34, 84),
                  table=(140, 55.5), legend=(34, 11), panel=(545, 735, 495, 225), panel_font=10,
                  readout=(40, 772, 17), readout_stacked=True, stats=(1040, 21),
                  install=(40, 925, 11.5, "left")),
    "4x5": Format(width=1080, height=1350, margin=40, title=(84, 24), subtitle=(118, 12), logo=(38, 92),
                  table=(165, 55.5), legend=(36, 11.5), panel=(125, 815, 915, 345), panel_font=11,
                  readout=(125, 788, 18), readout_stacked=False, stats=(1280, 22),
                  install=(540, 1325, 11.5, "center")),
}


# ---------------------------------------------------------------- SWEEPS
#
# A path maps t, an array from 0 to 1, onto (pH, potential in V vs SHE, temperature in °C). Any of the three
# can be a plain number. The conditions at t = 1 must equal those at t = 0, so that the video loops.

def cycle(t, start: float, end: float):
    """Move smoothly from ``start`` to ``end`` and back as ``t`` goes from 0 to 1."""
    return (start + end) / 2 - (end - start) / 2 * np.cos(2 * np.pi * np.asarray(t))


def orbit(t):
    """pH and potential on a closed path that follows the water window and crosses both water lines."""
    angle = 2 * np.pi * np.asarray(t)
    pH = 7.0 - 5.6 * np.cos(angle) + 0.5 * np.sin(2 * angle)
    return pH, 0.615 - 0.0592 * pH + 0.95 * np.sin(angle) + 0.22 * np.sin(3 * angle + 0.6)


def loop_path(t):
    return *orbit(t), 25.0


def ph_path(t):
    pH = cycle(t, 0.3, 13.7)
    return pH, 0.615 - 0.0592 * pH, 25.0


def potential_path(t):
    return 7.0, cycle(t, -1.0, 1.5), 25.0


def temperature_path(t):
    return 9.0, 0.20, cycle(t, 0.5, 99.5)


def orbit_path(t):
    return *orbit(t), cycle(t, 0.5, 99.5)


def double_orbit_path(t):
    """Two laps during one temperature cycle, so that each point is passed at T and at 100 °C − T."""
    return *orbit(2 * np.asarray(t)), cycle(t, 0.5, 99.5)


@dataclass(frozen=True)
class Sweep:
    path: Callable
    seconds: float
    subtitle: str  # {concentration} becomes, for example, 10⁻⁶ M
    trail: float = 0.2  # share of the video that the trail behind the point covers


SWEEPS = {
    "loop": Sweep(loop_path, 14, "at {concentration} and 25 °C, from experimental standard thermochemistry"),
    "ph": Sweep(ph_path, 12, "at {concentration} and 25 °C, across pH 0 to 14 in the water stability window"),
    "potential": Sweep(potential_path, 12,
                       "at {concentration}, 25 °C and pH 7, cycling the potential from −1.0 to +1.5 V vs SHE"),
    "temperature": Sweep(temperature_path, 12, "at {concentration}, pH 9 and +0.20 V vs SHE, from 0 to 100 °C"),
    "orbit": Sweep(orbit_path, 16,
                   "at {concentration}, sweeping pH, potential and temperature (0 to 100 °C) together"),
    "double_orbit": Sweep(double_orbit_path, 28, "at {concentration}, two laps through pH and potential: "
                                                 "heating from 0 to 100 °C, then cooling back", trail=0.1),
}


def conditions(sweep: Sweep, t) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """pH, potential and temperature in °C as arrays with the shape of ``t``."""
    t = np.asarray(t, dtype=float)
    pH, U, T = (np.broadcast_to(np.asarray(value, dtype=float), t.shape) for value in sweep.path(t))
    return pH, U, T


def check_sweep(name: str, sweep: Sweep) -> None:
    """Raise ValueError for a path that does not close or that leaves the supported temperatures."""
    start, end = (np.array(conditions(sweep, value), dtype=float) for value in (0.0, 1.0))
    if not np.allclose(start, end, atol=1e-6):
        raise ValueError(f"Sweep {name!r} does not loop: (pH, U, T) is {start} at t = 0 and {end} at t = 1.")
    temperature = conditions(sweep, np.linspace(0, 1, 400))[2]
    low, high = TEMPERATURE_RANGE_C
    if temperature.min() < low or temperature.max() > high:
        raise ValueError(f"Sweep {name!r} reaches {temperature.min():g} to {temperature.max():g} °C; "
                         f"pourbase supports {low:g} to {high:g} °C.")


# ---------------------------------------------------------------- DATA

def table_position(atomic_number: int) -> tuple[int, int]:
    """(row, column) of an element; the f-block occupies rows 8 and 9."""
    if 57 <= atomic_number <= 71:
        return 8, atomic_number - 54
    if 89 <= atomic_number <= 103:
        return 9, atomic_number - 86
    for row, (first, last) in enumerate(((1, 2), (3, 10), (11, 18), (19, 36), (37, 54), (55, 86), (87, 118))):
        if first <= atomic_number <= last:
            offset = atomic_number - first
            if row == 0:
                return 0, 0 if offset == 0 else 17
            if row in (1, 2):
                return row, offset if offset < 2 else offset + 10
            if row in (3, 4):
                return row, offset
            return row, offset if offset < 2 else offset - 14
    raise ValueError(f"Unknown atomic number {atomic_number}")


def formula_mathtext(formula_ascii: str, charge: float) -> str:
    """A formula such as ``Fe2O3`` as matplotlib math text with subscripts and a superscript charge."""
    body = re.sub(r"(?<=[A-Za-z)\]])(\d+(?:\.\d+)?)", r"_{\1}", formula_ascii)
    if charge:
        magnitude = "" if abs(charge) == 1 else f"{abs(charge):g}"
        body += "^{" + magnitude + ("+" if charge > 0 else "-") + "}"
    return f"$\\mathregular{{{body}}}$"


def concentration_label(log10_molar: int) -> str:
    return f"10{str(log10_molar).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))} M"


def calculate_screens(sweep: Sweep, fractions: np.ndarray, log10_concentration: int) -> list:
    database = pb.open_database()
    return [pb.screen_periodic_table(database, pH=float(pH), potential_V=float(U), temperature_K=float(T) + 273.15,
                                     concentration=log10_concentration)
            for pH, U, T in zip(*conditions(sweep, fractions))]


def water_lines(pH: np.ndarray, temperature_C: float) -> tuple[np.ndarray, np.ndarray]:
    """Potentials of the H₂O/H₂ and O₂/H₂O lines at the given pH."""
    temperature_K = temperature_C + 273.15
    slope = math.log(10) * GAS_CONSTANT_J_MOL_K * temperature_K / FARADAY_C_MOL
    oxygen = -water_gibbs_energy_J_mol(WATER_GIBBS_ENERGY_J_MOL, temperature_K) / (2 * FARADAY_C_MOL)
    return -slope * pH, oxygen - slope * pH


def heat_share(temperature_C):
    """Position of a temperature on the gauge and in HEAT_COLORS, from 0 to 1."""
    low, high = TEMPERATURE_RANGE_C
    return (temperature_C - low) / (high - low)


def merge_short_runs(keys: list) -> list[int]:
    """Index of the frame whose species each frame shows; runs shorter than MIN_RUN_FRAMES use the frame before."""
    n = len(keys)
    source = list(range(n))
    starts = [i for i in range(n) if keys[i] != keys[i - 1]]
    if not starts:
        return source
    for start, end in zip(starts, [*starts[1:], starts[0] + n]):
        if end - start < MIN_RUN_FRAMES:
            for i in range(start, end):
                source[i % n] = source[(start - 1) % n]
    return source


def blend_colors(colors: list[str], width: int = 5) -> np.ndarray:
    """Per-frame RGB of one tile, smoothed over a circular window so that category changes cross-fade."""
    rgb = np.array([to_rgb(color) for color in colors])
    kernel = np.hanning(2 * width + 3)[1:-1]
    kernel /= kernel.sum()
    padded = np.take(rgb, range(-width, len(rgb) + width), axis=0, mode="wrap")
    return np.stack([np.convolve(padded[:, channel], kernel, mode="valid") for channel in range(3)], axis=1)


def label_alpha(labels: list[str], fade: int = 4) -> np.ndarray:
    """Opacity of a tile's species label, which fades out and in around each change."""
    n = len(labels)
    changes = [i for i in range(n) if labels[i] != labels[i - 1]]
    alpha = np.ones(n)
    if not changes:
        return alpha
    for i in range(n):
        # frame c is the first frame of the new label
        before = min(((c - i) % n for c in changes if (c - i) % n), default=n)
        after = min((i - c) % n for c in changes)
        alpha[i] = min(1.0, min(before - 0.5, after + 0.5) / fade)
    return np.clip(alpha, 0.0, 1.0)


# ---------------------------------------------------------------- DRAWING

@dataclass
class Scene:
    """Everything a part can use. Add fields here when parts need to share something new."""

    figure: Figure
    canvas: Axes  # covers the figure, in pixels from the top left
    renderer: object
    sweep: Sweep
    layout: Format
    theme: Theme
    fractions: np.ndarray  # position in the loop of each frame, from 0 to 1
    screens: list  # the PeriodicScreen of each frame, with every element's stable species and margin
    concentration: int
    shows_temperature: bool
    moves: bool
    panel: Axes | None = None  # the pH–potential axes, in pH and volts
    shine_text: Text | None = None  # the text that apply_shine highlights

    def conditions(self, frame: int) -> tuple[float, float, float]:
        """pH, potential and temperature in °C at a frame."""
        pH, U, T = conditions(self.sweep, self.fractions[frame])
        return float(pH), float(U), float(T)

    @property
    def tile_scale(self) -> float:
        return self.layout.table[1] / 64

    def text_width(self, text: str, **style) -> float:
        probe = self.canvas.text(0, 0, text, **style)
        width = probe.get_window_extent(self.renderer).width
        probe.remove()
        return width


def compose(scene: Scene) -> list:
    """The parts of the video in drawing order. Add, remove or reorder parts here."""
    return [
        draw_table(scene),
        draw_panel(scene),
        draw_water_lines(scene),
        draw_point(scene),
        draw_gauge(scene),
        draw_readout(scene),
        draw_header(scene),
        draw_legend(scene),
        draw_footer(scene),
    ]


def draw_table(scene: Scene):
    canvas, theme, scale = scene.canvas, scene.theme, scene.tile_scale
    top, pitch = scene.layout.table
    tile = pitch - 5 * scale
    updates = []
    first = scene.screens[0]
    calculated = {element.symbol for element in first.elements if element.stable is not None}
    history = {symbol: [] for symbol in calculated}
    for screen in scene.screens:
        for element in screen.elements:
            if element.symbol in calculated:
                history[element.symbol].append(element)

    for element in first.elements:
        row, column = table_position(element.atomic_number)
        x, y = scene.layout.margin + column * pitch, top + row * pitch + (18 * scale - pitch if row >= 8 else 0)
        active = element.symbol in calculated
        patch = FancyBboxPatch((x, y), tile, tile, boxstyle=f"round,pad=0,rounding_size={7 * scale}",
                               linewidth=0 if active else 1.0, edgecolor=theme.faint,
                               facecolor=theme.faint if active else theme.background, zorder=2)
        canvas.add_patch(patch)
        canvas.text(x + 5 * scale, y + 5 * scale, str(element.atomic_number), fontsize=6.5 * scale, va="top",
                    ha="left", color=TILE_INK if active else theme.muted, alpha=0.6, zorder=3)
        canvas.text(x + tile / 2, y + tile * 0.47, element.symbol, fontsize=(16 if active else 12.5) * scale,
                    fontweight="semibold" if active else "normal", ha="center", va="center",
                    color=TILE_INK if active else theme.ghost, zorder=3)
        if not active:
            continue
        species = canvas.text(x + tile / 2, y + tile - 6 * scale, "", fontsize=7.5 * scale, ha="center",
                              va="bottom", color=TILE_INK, zorder=3)
        states = history[element.symbol]
        states = [states[i] for i in merge_short_runs([state.stable.record_id for state in states])]
        labels = [formula_mathtext(state.stable.formula_ascii, state.stable.charge) for state in states]
        colors = blend_colors([CATEGORY_COLORS.get(state.category, theme.faint) for state in states])
        updates.append((patch, species, labels, colors, label_alpha(labels)))

    def update(frame: int) -> None:
        for patch, species, labels, colors, alpha in updates:
            patch.set_facecolor(colors[frame])
            species.set_text(labels[frame])
            species.set_alpha(alpha[frame])

    return update


def draw_panel(scene: Scene):
    """The axes of the pH–potential panel, which draw_water_lines, draw_point and draw_gauge draw on."""
    layout, theme = scene.layout, scene.theme
    left, top, width, height = layout.panel
    font = layout.panel_font
    ax = scene.panel = scene.figure.add_axes((left / layout.width, 1 - (top + height) / layout.height,
                                              width / layout.width, height / layout.height))
    ax.set_facecolor(theme.background)
    ax.set_xlim(*PH_RANGE)
    ax.set_ylim(*U_RANGE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(theme.muted)
    ax.set_xlabel("pH", fontsize=font + 1, color=theme.ink, labelpad=2)
    ax.set_ylabel("U  (V vs SHE)", fontsize=font + 1, color=theme.ink, labelpad=4)
    ax.tick_params(labelsize=font - 1.5, length=4, colors=theme.muted)
    ax.set_xticks(range(0, 15, 2))
    ax.set_yticks([-1, -0.5, 0, 0.5, 1, 1.5])


def draw_water_lines(scene: Scene):
    ax, theme, font = scene.panel, scene.theme, scene.layout.panel_font
    ends = np.array(PH_RANGE)
    lower, upper = water_lines(ends, 25.0)
    fill = ax.fill_between(ends, lower, upper, color=WATER_COLOR, alpha=theme.water_alpha, lw=0)
    (lower_line,) = ax.plot(ends, lower, color=WATER_COLOR, lw=1.2, ls=(0, (5, 4)), alpha=0.8)
    (upper_line,) = ax.plot(ends, upper, color=WATER_COLOR, lw=1.2, ls=(0, (5, 4)), alpha=0.8)
    oxygen_label = ax.text(13.8, upper[1] + 0.12, "O₂ / H₂O", fontsize=font - 1, color=WATER_COLOR, ha="right")
    hydrogen_label = ax.text(13.8, lower[1] - 0.2, "H₂O / H₂", fontsize=font - 1, color=WATER_COLOR, ha="right")
    ax.text(0.3, 1.70, "oxidising", fontsize=font - 2, color=theme.muted, va="top")
    ax.text(0.3, -1.12, "reducing", fontsize=font - 2, color=theme.muted, va="bottom")

    def update(frame: int) -> None:
        lower, upper = water_lines(ends, scene.conditions(frame)[2])
        fill.set_data(ends, lower, upper)
        lower_line.set_ydata(lower)
        upper_line.set_ydata(upper)
        oxygen_label.set_y(upper[1] + 0.12)
        hydrogen_label.set_y(lower[1] - 0.2)

    return update if scene.shows_temperature else None


def draw_point(scene: Scene):
    """The current conditions as a dot with a halo, guide lines and a fading trail."""
    ax, theme, sweep, scale = scene.panel, scene.theme, scene.sweep, scene.tile_scale
    trail = LineCollection([], capstyle="round", zorder=4)
    ax.add_collection(trail)
    halo = ax.scatter([], [], s=520 * scale, color=theme.ink, alpha=0.1, lw=0, zorder=5)
    dot = ax.scatter([], [], s=110 * scale, color=theme.ink, edgecolor=theme.background, linewidth=2.2 * scale,
                     zorder=6)
    guide_x = ax.axvline(0, color=theme.ink, lw=0.6, alpha=0.18, zorder=1)
    guide_y = ax.axhline(0, color=theme.ink, lw=0.6, alpha=0.18, zorder=1)

    def update(frame: int) -> None:
        fraction = scene.fractions[frame]
        pH, U, T = scene.conditions(frame)
        if scene.shows_temperature:
            dot.set_facecolor(HEAT_COLORS(heat_share(T)))
            halo.set_facecolor(HEAT_COLORS(heat_share(T)))
        if scene.moves:
            trail_pH, trail_U, trail_T = conditions(sweep, np.linspace(fraction - sweep.trail, fraction, 260))
            points = np.column_stack([trail_pH, trail_U]).reshape(-1, 1, 2)
            age = np.linspace(0, 1, len(points) - 1)
            colors = np.zeros((len(age), 4))
            colors[:, :3] = HEAT_COLORS(heat_share(trail_T[1:]))[:, :3] if scene.shows_temperature \
                else to_rgb(theme.ink)
            colors[:, 3] = 0.6 * age ** 1.8
            trail.set_segments(np.concatenate([points[:-1], points[1:]], axis=1))
            trail.set_color(colors)
            trail.set_linewidth((0.4 + 5.0 * age ** 1.3) * scale)
        dot.set_offsets([[pH, U]])
        halo.set_offsets([[pH, U]])
        halo.set_sizes([(520 + 260 * np.sin(2 * np.pi * 4 * fraction) ** 2) * scale])
        guide_x.set_xdata([pH, pH])
        guide_y.set_ydata([U, U])

    return update


def draw_gauge(scene: Scene):
    """A temperature bar inside the panel, for sweeps that change temperature."""
    if not scene.shows_temperature:
        return None
    ax, theme, font, scale = scene.panel, scene.theme, scene.layout.panel_font, scene.tile_scale
    (start, end), y = (5.0, 12.7), 1.58  # in pH and volts
    shares = np.linspace(0, 1, 200)
    x = start + shares * (end - start)
    ax.plot((start, end), (y, y), color=theme.faint, lw=7 * scale, solid_capstyle="round", zorder=2)
    gauge = LineCollection(np.stack([np.column_stack([x[:-1], np.full(199, y)]),
                                     np.column_stack([x[1:], np.full(199, y)])], axis=1),
                           linewidths=7 * scale, zorder=3)
    ax.add_collection(gauge)
    low, high = TEMPERATURE_RANGE_C
    ax.text(start - 0.25, y, f"{low:g} °C", fontsize=font - 2, color=theme.muted, ha="right", va="center")
    ax.text(end + 0.25, y, f"{high:g} °C", fontsize=font - 2, color=theme.muted, ha="left", va="center")
    knob = ax.scatter([], [], s=70 * scale, color=theme.background, edgecolor=theme.ink, linewidth=1.8 * scale,
                      zorder=4)

    def update(frame: int) -> None:
        heat = heat_share(scene.conditions(frame)[2])
        gauge.set_color([(*HEAT_COLORS(share)[:3], 1.0 if share <= heat else 0.0) for share in shares[:-1]])
        knob.set_offsets([[start + heat * (end - start), y]])

    return update


def draw_readout(scene: Scene):
    """The current conditions as text: a label, a right-aligned value of fixed width and a unit for each."""
    canvas, layout, theme = scene.canvas, scene.layout, scene.theme
    x, y, size = layout.readout
    style = dict(fontsize=size, va="baseline", fontweight="medium")
    groups = [("pH", "14.00", ""), ("U", "+1.80", "V vs SHE")]
    if scene.shows_temperature:
        groups.append(("T", "100.0", "°C"))
    stacked = layout.readout_stacked
    label_width = max(scene.text_width(group[0], **style) for group in groups) if stacked else None
    value_width = max(scene.text_width(group[1], **style) for group in groups) if stacked else None
    values = []
    start = x
    for label, widest, unit in groups:
        canvas.text(x, y, label, color=theme.muted, **style)
        x += (label_width or scene.text_width(label, **style)) + size * 0.55
        x += value_width or scene.text_width(widest, **style)
        values.append(canvas.text(x, y, "", ha="right", color=theme.ink, **style))
        if unit:
            canvas.text(x + size * 0.4, y, unit, color=theme.muted, **style)
            x += size * 0.4 + scene.text_width(unit, **style)
        if stacked:
            x, y = start, y + size * 2.6
        else:
            x += size * 1.6

    def update(frame: int) -> None:
        pH, U, T = scene.conditions(frame)
        values[0].set_text(f"{pH:.2f}")
        values[1].set_text(f"{U:+.2f}".replace("-", "−"))
        if scene.shows_temperature:
            values[2].set_text(f"{T:.1f}")

    return update


def draw_header(scene: Scene):
    canvas, layout, theme = scene.canvas, scene.layout, scene.theme
    subtitle = scene.sweep.subtitle.format(concentration=concentration_label(scene.concentration))
    canvas.text(layout.margin, layout.title[0], TITLE, fontsize=layout.title[1], fontweight="semibold",
                color=theme.ink, va="baseline")
    canvas.text(layout.margin, layout.subtitle[0], subtitle, fontsize=layout.subtitle[1], color=theme.muted,
                va="baseline")
    logo = render_logo(theme, layout.logo[0])
    if logo is None:
        canvas.text(layout.width - layout.margin, layout.logo[1], "pourbase", fontsize=layout.title[1] * 0.8,
                    fontweight="semibold", color=theme.ink, ha="right", va="baseline")
    else:
        scene.figure.figimage(logo, xo=int(layout.width - layout.margin - logo.shape[1]),
                              yo=int(layout.height - layout.logo[1]), zorder=10)


def draw_legend(scene: Scene):
    canvas, layout = scene.canvas, scene.layout
    top, pitch = layout.table
    gap, size = layout.legend
    chip = size * 1.4
    x, y = layout.margin, top + 9 * pitch + 13 * scene.tile_scale + gap  # below the f-block
    for category, label in LEGEND:
        text = canvas.text(0, y, label, fontsize=size, color=scene.theme.ink, va="center")
        width = 1.5 * chip + text.get_window_extent(scene.renderer).width
        if x + width > layout.margin + 18 * pitch:
            x, y = layout.margin, y + chip * 1.9
            text.set_y(y)
        canvas.add_patch(FancyBboxPatch((x, y - chip / 2), chip, chip,
                                        boxstyle=f"round,pad=0,rounding_size={chip / 4}", linewidth=0,
                                        facecolor=CATEGORY_COLORS[category]))
        text.set_x(x + 1.5 * chip)
        x += width + 2.2 * chip


def draw_footer(scene: Scene):
    canvas, layout, theme = scene.canvas, scene.layout, scene.theme
    scene.shine_text = canvas.text(layout.width / 2, layout.stats[0], STATS, fontsize=layout.stats[1],
                                   fontweight="semibold", color=theme.ink, ha="center", va="center")
    x, y, size, alignment = layout.install
    canvas.text(x, y, INSTALL_LINE, fontsize=size, color=theme.muted, ha=alignment, va="center",
                family="DejaVu Sans Mono")


def render_logo(theme: Theme, height: int) -> np.ndarray | None:
    """The wordmark as an RGBA array, or None without PySide6 or the logo file."""
    path = REPOSITORY / "docs" / theme.logo
    try:
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QGuiApplication, QImage, QPainter
        from PySide6.QtSvg import QSvgRenderer
    except ImportError:
        return None
    if not path.exists():
        return None
    QGuiApplication.instance() or QGuiApplication(["pourbase", "-platform", "offscreen"])
    renderer = QSvgRenderer(str(path))
    size = renderer.defaultSize()
    width = round(size.width() * height / size.height())
    image = QImage(width, height, QImage.Format.Format_RGBA8888)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, width, height))
    painter.end()
    pixels = np.frombuffer(image.constBits(), np.uint8).reshape(height, image.bytesPerLine() // 4, 4)[:, :width]
    return pixels.astype(float) / 255.0


# ---------------------------------------------------------------- EFFECTS ON THE FINISHED FRAME

def text_mask(scene: Scene, artist: Text) -> np.ndarray:
    """Opacity of one text artist at full-frame resolution."""
    figure, canvas = scene.figure, scene.canvas
    others = [item for item in [*canvas.get_children(), *figure.axes[1:], *figure.images]
              if item is not artist and item.get_visible()]
    for item in others:
        item.set_visible(False)
    figure.patch.set_visible(False)
    figure.canvas.draw()
    rgba = np.asarray(figure.canvas.buffer_rgba()).copy()
    for item in others:
        item.set_visible(True)
    figure.patch.set_visible(True)
    return rgba[..., 3].astype(float) / 255.0


def apply_shine(rgb: np.ndarray, mask: np.ndarray, fraction: float) -> np.ndarray:
    """Tint the masked text with a highlight that crosses it SHINE_SWEEPS_PER_LOOP times per loop."""
    phase = (fraction * SHINE_SWEEPS_PER_LOOP) % 1.0
    if phase >= 0.55:  # the highlight is off for the rest of each sweep
        return rgb
    columns = np.where(mask.any(axis=0))[0]
    first, last = columns.min(), columns.max()
    reach = 0.12 * (last - first)
    centre = first - reach + phase / 0.55 * (last - first + 2 * reach)
    x = np.arange(rgb.shape[1])
    band = np.exp(-0.5 * ((x - centre) / (0.04 * (last - first))) ** 2)
    core = np.exp(-0.5 * ((x - centre) / (0.013 * (last - first))) ** 2)
    weight = (mask * band[None, :])[..., None]
    edge, centre_color = (np.array(to_rgb(color)) * 255 for color in SHINE_COLORS)
    tint = edge + (centre_color - edge) * core[None, :, None]
    return rgb * (1 - weight) + tint * weight


# ---------------------------------------------------------------- RENDERING

@dataclass(frozen=True)
class Job:
    sweep: str
    format: str
    theme: str
    output_dir: Path
    preview: tuple[float, ...] | None = None  # loop fractions to save as PNG in place of a video
    seconds: float | None = None
    fps: int = FPS
    concentration: int = LOG10_CONCENTRATION

    @property
    def name(self) -> str:
        return f"pourbase_{self.sweep}_{self.format}_{self.theme}"


def font_settings() -> dict:
    available = {font.name for font in font_manager.fontManager.ttflist}
    if FONT not in available:
        for path in font_manager.findSystemFonts():
            if Path(path).name.startswith(FONT):
                font_manager.fontManager.addfont(path)
        available = {font.name for font in font_manager.fontManager.ttflist}
    if FONT not in available:
        print(f"Font {FONT} not found; using DejaVu Sans.", file=sys.stderr)
        return {"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans"}
    return {"font.family": FONT, "mathtext.fontset": "custom", "mathtext.rm": FONT, "mathtext.it": f"{FONT}:italic",
            "mathtext.bf": f"{FONT}:bold", "mathtext.cal": FONT, "mathtext.sf": FONT, "mathtext.tt": FONT}


def render(job: Job) -> list[Path]:
    """Render one video, or its preview stills, and return the files written."""
    sweep = SWEEPS[job.sweep]
    check_sweep(job.sweep, sweep)
    frames = round((job.seconds or sweep.seconds) * job.fps)
    if frames < 12:
        raise ValueError(f"{job.name} needs at least 12 frames for its cross-fades; it has {frames}.")
    with matplotlib.rc_context(font_settings()):
        fractions = np.arange(frames) / frames
        layout, theme = FORMATS[job.format], THEMES[job.theme]
        figure = Figure(figsize=(layout.width / 100, layout.height / 100), dpi=100, facecolor=theme.background)
        agg = FigureCanvasAgg(figure)
        canvas = figure.add_axes((0, 0, 1, 1))
        canvas.set_xlim(0, layout.width)
        canvas.set_ylim(layout.height, 0)
        canvas.axis("off")
        pH, U, T = conditions(sweep, np.linspace(0, 1, 100))
        scene = Scene(figure, canvas, agg.get_renderer(), sweep, layout, theme, fractions,
                      calculate_screens(sweep, fractions, job.concentration), job.concentration,
                      shows_temperature=bool(np.ptp(T) > 0), moves=bool(np.ptp(pH) > 0 or np.ptp(U) > 0))
        updates = [update for update in compose(scene) if update is not None]
        mask = text_mask(scene, scene.shine_text) if scene.shine_text is not None else None

        def frame_pixels(frame: int) -> np.ndarray:
            for update in updates:
                update(frame)
            agg.draw()
            rgb = np.asarray(agg.buffer_rgba())[..., :3].astype(float)
            if mask is not None:
                rgb = apply_shine(rgb, mask, fractions[frame])
            return rgb.astype(np.uint8)

        job.output_dir.mkdir(parents=True, exist_ok=True)
        if job.preview is not None:
            return _save_stills(job, frame_pixels, frames)
        return [_encode_video(job, frame_pixels, frames, layout)]


def _save_stills(job: Job, frame_pixels: Callable, frames: int) -> list[Path]:
    from PIL import Image

    written = []
    for value in job.preview:
        path = job.output_dir / f"{job.name}_{value:.2f}.png"
        Image.fromarray(frame_pixels(round(value * frames) % frames)).save(path)
        written.append(path)
    return written


def _encode_video(job: Job, frame_pixels: Callable, frames: int, layout: Format) -> Path:
    output = job.output_dir / f"{job.name}.mp4"
    partial = job.output_dir / f".{job.name}.partial.mp4"  # renamed on success, so a stopped run leaves no bad video
    encoder = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{layout.width}x{layout.height}",
         "-r", str(job.fps), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
         "-threads", str(ENCODER_THREADS), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(partial)],
        stdin=subprocess.PIPE)
    for frame in range(frames):
        encoder.stdin.write(frame_pixels(frame).tobytes())
        if frame % 60 == 0:
            print(f"{job.name}: frame {frame}/{frames}", file=sys.stderr)
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for {job.name}")
    partial.replace(output)
    return output


def _expand(values: list[str], options) -> list[str]:
    return list(options) if "all" in values else values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sweep", nargs="+", default=["loop"], choices=[*SWEEPS, "all"])
    parser.add_argument("--format", nargs="+", default=["16x9"], choices=[*FORMATS, "all"])
    parser.add_argument("--theme", nargs="+", default=["light"], choices=[*THEMES, "all"])
    parser.add_argument("--preview", type=float, nargs="+", metavar="FRACTION",
                        help="save PNG stills at these points of the loop, from 0 to 1, and no video")
    parser.add_argument("--output-dir", type=Path, default=Path("animations"))
    parser.add_argument("--seconds", type=float, help="length of the loop; the default depends on the sweep")
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--concentration", type=int, default=LOG10_CONCENTRATION, metavar="LOG10_M",
                        help="log10 of the metal concentration in mol/L")
    parser.add_argument("--jobs", type=int, default=1,
                        help="videos to render at once; each uses about 1 GB of memory (default: %(default)s)")
    args = parser.parse_args(argv)
    if args.preview is None and shutil.which("ffmpeg") is None:
        parser.error("videos need ffmpeg on the PATH; --preview works without it")

    jobs = [Job(sweep, layout, theme, args.output_dir, tuple(args.preview) if args.preview else None, args.seconds,
                args.fps, args.concentration)
            for sweep, layout, theme in product(_expand(args.sweep, SWEEPS), _expand(args.format, FORMATS),
                                                _expand(args.theme, THEMES))]
    failures = 0
    with ProcessPoolExecutor(max_workers=args.jobs, mp_context=get_context("spawn")) as pool:
        running = {pool.submit(render, job): job for job in jobs}
        for future in as_completed(running):
            try:
                for path in future.result():
                    print(path)
            except Exception as error:  # report the failure and let the other videos finish
                failures += 1
                print(f"{running[future].name} failed: {error}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
