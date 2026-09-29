"""Command-line interface for pourbase."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from .database import ThermodynamicDatabase
from .mp_thermochemistry import write_mp_thermochemistry_bundle
from .service import calculate, calculate_sweep_with_image, render_grid_csv, render_png


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pourbase")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("systems", help="list available elemental systems")
    gui = commands.add_parser("gui", help="open the desktop application")
    gui.add_argument("symbol", nargs="?", help="element to open, for example Fe")
    mp_figures = commands.add_parser(
        "mp-thermo-figures", help="write phase-matched MP thermochemistry figures"
    )
    mp_figures.add_argument(
        "--output-dir", type=Path, default=Path("mp-thermochemistry")
    )
    plot = commands.add_parser("plot", help="write an experimental Pourbaix diagram")
    plot.add_argument("symbol")
    plot.add_argument("--mode", choices=("fixed_activity", "mass_balance"), default="fixed_activity")
    plot.add_argument("--log10-activity", type=float, default=-6.0)
    plot.add_argument("--concentration", type=float)
    plot.add_argument(
        "--unit", choices=("log10_molar", "molar", "ppm", "wt_percent"),
        default="log10_molar",
    )
    plot.add_argument("--solution-density", type=float, default=1.0)
    plot.add_argument("--total-metal", type=float, default=1e-6)
    plot.add_argument("--davies-ionic-strength", type=float)
    plot.add_argument("--allow-incomplete", action="store_true")
    plot.add_argument(
        "--use-mp-fallbacks", action="store_true",
        help="fill six missing solid Gibbs values with labelled MP 300 K estimates",
    )
    plot.add_argument(
        "--boltzmann-scale", type=float,
        help="plot fixed-activity Boltzmann-like soft-min weights",
    )
    plot.add_argument("--output", type=Path, default=Path("pourbaix.png"))
    plot.add_argument("--grid-csv", type=Path)
    sweep = commands.add_parser("sweep", help="write a concentration-sweep figure")
    sweep.add_argument("symbol")
    sweep.add_argument("--minimum", type=float, default=-10.0)
    sweep.add_argument("--maximum", type=float, default=0.0)
    sweep.add_argument("--points", type=int, default=7)
    sweep.add_argument("--probe-pH", type=float, default=7.0)
    sweep.add_argument("--probe-eh", type=float, default=0.0)
    sweep.add_argument("--allow-incomplete", action="store_true")
    sweep.add_argument("--use-mp-fallbacks", action="store_true")
    sweep.add_argument("--output", type=Path, default=Path("pourbaix-sweep.png"))
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "gui":
        from .gui import main as gui_main  # noqa: PLC0415

        raise SystemExit(gui_main([args.symbol] if args.symbol else []))
    database = ThermodynamicDatabase.bundled()
    if args.command == "systems":
        for symbol, name in database.available_systems():
            print(f"{symbol}\t{name}")
        return
    if args.command == "mp-thermo-figures":
        metadata = write_mp_thermochemistry_bundle(database, args.output_dir)
        print(json.dumps(metadata, indent=2))
        print(f"Wrote {args.output_dir.resolve()}")
        return
    if args.command == "sweep":
        result = calculate_sweep_with_image(
            {
                "symbol": args.symbol,
                "sweep_log10_min": args.minimum,
                "sweep_log10_max": args.maximum,
                "sweep_points": args.points,
                "probe_pH": args.probe_pH,
                "probe_eh_V": args.probe_eh,
                "allow_incomplete": args.allow_incomplete,
                "energy_policy": (
                    "experimental_then_mp" if args.use_mp_fallbacks
                    else "experimental_only"
                ),
            },
            database,
        )
        args.output.write_bytes(base64.b64decode(result.pop("image_png_base64")))
        print(json.dumps(result, indent=2))
        print(f"Wrote {args.output.resolve()}")
        return
    payload = {
        "symbol": args.symbol,
        "mode": args.mode,
        "log10_activity": args.log10_activity,
        "total_metal_mol_L": args.total_metal,
        "allow_incomplete": args.allow_incomplete,
        "energy_policy": (
            "experimental_then_mp" if args.use_mp_fallbacks
            else "experimental_only"
        ),
        "boltzmann_scale": args.boltzmann_scale,
        "activity_coefficient_model": "davies" if args.davies_ionic_strength is not None else "ideal",
        "ionic_strength_mol_L": args.davies_ionic_strength or 0.01,
    }
    if args.mode == "mass_balance" and args.boltzmann_scale is not None:
        raise SystemExit("--boltzmann-scale applies to fixed_activity mode")
    if args.concentration is not None:
        payload.update(
            concentration_value=args.concentration,
            concentration_unit=args.unit,
            solution_density_kg_L=args.solution_density,
        )
    diagram, result = calculate(payload, database)
    args.output.write_bytes(
        render_png(diagram, args.mode, boltzmann_scale=args.boltzmann_scale)
    )
    if args.grid_csv is not None:
        args.grid_csv.write_bytes(render_grid_csv(diagram))
    print(json.dumps({key: value for key, value in result.items()}, indent=2))
    print(f"Wrote {args.output.resolve()}")


if __name__ == "__main__":
    main()
