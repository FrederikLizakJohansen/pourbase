"""Command-line interface for pourbase."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .database import ThermodynamicDatabase
from .exceptions import PourbaseError
from .export import diagram_figure, grid_csv, save_figure
from .models import GibbsEnergyPolicy
from .mp_thermochemistry import write_mp_thermochemistry_bundle
from .scenario import Mode, Scenario, calculate
from .sweeps import ConcentrationSweepEngine, plot_concentration_sweep

UNITS = ("log10_molar", "molar", "ppm", "wt_percent")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pourbase")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("systems", help="list available elemental systems")
    gui = commands.add_parser("gui", help="open the desktop application")
    gui.add_argument("symbol", nargs="?", help="element to open, for example Fe")
    figures = commands.add_parser("mp-thermo-figures", help="write phase-matched MP thermochemistry figures")
    figures.add_argument("--output-dir", type=Path, default=Path("mp-thermochemistry"))

    def evidence(command: argparse.ArgumentParser) -> None:
        command.add_argument("--require-complete", action="store_true",
                             help="stop when a species of the system has no recommended Gibbs energy "
                                  "(by default such species are left out and reported)")
        command.add_argument("--allow-incomplete", action="store_true", help=argparse.SUPPRESS)
        command.add_argument("--use-mp-fallbacks", action="store_true",
                             help="fill missing solid Gibbs values with labelled MP 300 K estimates")

    plot = commands.add_parser("plot", help="write an experimental Pourbaix diagram")
    plot.add_argument("symbol")
    plot.add_argument("--mode", choices=[item.value for item in Mode], default=Mode.FIXED_ACTIVITY.value)
    plot.add_argument("--concentration", type=float, default=-6.0,
                      help="metal concentration in --unit (default: -6 log10 mol/L)")
    plot.add_argument("--unit", choices=UNITS, default="log10_molar")
    plot.add_argument("--solution-density", type=float, default=1.0)
    plot.add_argument("--davies-ionic-strength", type=float,
                      help="Davies activity coefficients at this ionic strength (mass balance)")
    plot.add_argument("--blend-width", type=float, metavar="KJ_MOL",
                      help="draw soft-minimum weights of this width in kJ/mol (fixed activity)")
    plot.add_argument("--boltzmann-scale", type=float, help=argparse.SUPPRESS)
    plot.add_argument("--output", type=Path, default=Path("pourbaix.png"))
    plot.add_argument("--grid-csv", type=Path)
    evidence(plot)
    sweep = commands.add_parser("sweep", help="write a concentration-sweep figure")
    sweep.add_argument("symbol")
    sweep.add_argument("--minimum", type=float, default=-10.0)
    sweep.add_argument("--maximum", type=float, default=0.0)
    sweep.add_argument("--points", type=int, default=7)
    sweep.add_argument("--probe-pH", type=float, default=7.0)
    sweep.add_argument("--probe-eh", type=float, default=0.0)
    sweep.add_argument("--output", type=Path, default=Path("pourbaix-sweep.png"))
    evidence(sweep)
    return root


def _policy(args: argparse.Namespace) -> GibbsEnergyPolicy:
    return GibbsEnergyPolicy.EXPERIMENTAL_THEN_MP if args.use_mp_fallbacks else GibbsEnergyPolicy.EXPERIMENTAL_ONLY


def main() -> None:
    try:
        run(parser().parse_args())
    except (PourbaseError, ValueError) as error:
        raise SystemExit(f"pourbase: {error}") from None


def run(args: argparse.Namespace) -> None:
    if args.command == "gui":
        from .gui import main as gui_main

        raise SystemExit(gui_main([args.symbol] if args.symbol else []))
    database = ThermodynamicDatabase.bundled()
    if args.command == "systems":
        for symbol, name in database.available_systems():
            print(f"{symbol}\t{name}")
    elif args.command == "mp-thermo-figures":
        print(json.dumps(write_mp_thermochemistry_bundle(database, args.output_dir), indent=2))
        print(f"Wrote {args.output_dir.resolve()}")
    elif args.command == "sweep":
        conditions = Scenario(args.symbol).conditions()
        result = ConcentrationSweepEngine(database).calculate(
            args.symbol, conditions, args.minimum, args.maximum, args.points,
            allow_incomplete=not args.require_complete, energy_policy=_policy(args),
        )
        figure, _ = plot_concentration_sweep(result, probe_pH=args.probe_pH, probe_eh_V=args.probe_eh)
        print(f"Wrote {save_figure(figure, args.output, dpi=150).resolve()}")
    else:
        if args.mode == Mode.MASS_BALANCE.value and (args.blend_width or args.boltzmann_scale) is not None:
            raise SystemExit("--blend-width applies to fixed_activity mode")
        calculation = calculate(Scenario(
            args.symbol, mode=args.mode, concentration=args.concentration, concentration_unit=args.unit,
            solution_density_kg_L=args.solution_density,
            davies_ionic_strength_mol_L=args.davies_ionic_strength,
            allow_incomplete=not args.require_complete, energy_policy=_policy(args),
        ), database)
        figure = diagram_figure(calculation.diagram, blend_width_kJ_mol=args.blend_width,
                                boltzmann_scale=args.boltzmann_scale)
        save_figure(figure, args.output, dpi=150)
        if args.grid_csv is not None:
            args.grid_csv.write_text(grid_csv(calculation.diagram))
        print(json.dumps(calculation.as_dict(), indent=2, ensure_ascii=False))
        print(f"Wrote {args.output.resolve()}")


if __name__ == "__main__":
    main()
