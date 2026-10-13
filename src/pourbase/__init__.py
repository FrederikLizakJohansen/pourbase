"""Source-linked experimental thermochemistry and Pourbaix diagrams."""

from .activity_coefficients import DaviesActivityCoefficientModel, IdealActivityCoefficientModel
from .boltzmann import BoltzmannSmoothedDiagram, boltzmann_smooth
from .convenience import calculate_pourbaix, open_database
from .conversions import (
    ATOMIC_WEIGHT_G_MOL,
    ConcentrationConversion,
    convert_concentration,
    express_concentration,
    metal_molarity_from_mass,
)
from .database import ThermodynamicDatabase
from .engine import PourbaixDiagram, PourbaixEngine
from .equilibria import BoundaryEquation, PlatingPotential, boundary_equations, plating_potentials
from .exceptions import (
    CalculationCancelled,
    DatabaseSchemaError,
    IncompleteSystemError,
    MaterialsProjectUnavailableError,
    MetalSystemNotFoundError,
    PourbaseError,
    UnsupportedConditionError,
)
from .export import diagram_figure, grid_csv, save_figure
from .grid import phase_boundary_segments
from .mass_balance import MassBalancedPourbaixDiagram, MassBalancedState, MassBalanceEngine
from .materials_project import (
    OfficialMaterialsProjectClient,
    OfficialMaterialsProjectComparator,
    OfficialMaterialsProjectComparison,
    OfficialMaterialsProjectDiagram,
    OfficialMaterialsProjectPhase,
    evaluate_official_materials_project_entries,
    thermodynamic_species_equivalence_key,
)
from .models import (
    AqueousActivityModel,
    EvidenceStatus,
    ExclusionReason,
    GasFugacityModel,
    GibbsEnergyPolicy,
    LigandActivity,
    LigandActivityModel,
    MetalSystem,
    PourbaixConditions,
    ThermodynamicSpecies,
    TotalMetalConcentration,
)
from .mp_thermochemistry import comparison_metrics, plot_mp_thermochemistry_comparison, write_mp_thermochemistry_bundle
from .overview import Category, ElementResult, ElementStatus, PeriodicScreen, screen_periodic_table
from .sensitivity import SelectionSensitivity, selection_sensitivity
from .plotting import (
    plot_boltzmann_diagram,
    plot_diagram,
    plot_mass_balance_summary,
    plot_official_materials_project_comparison,
    plot_official_materials_project_diagram,
    species_colors, plot_uncertainty)
from .records import SourceReference, SpeciesRecord
from .scenario import Calculation, Mode, Probe, Scenario, calculate
from .speciation import SpeciationProfile, dissolved_blend_weights, metal_fraction_grid, plot_speciation_profile, speciation_at, speciation_profile
from .sweeps import ConcentrationSweep, ConcentrationSweepEngine, plot_concentration_sweep
from .user_data import (
    UserSpecies, UserSpeciesDatabase, dataset_from_csv, open_dataset, read_user_species, with_user_species,
)
from .selection import PolicyDatabase, SelectionPolicy, compare_policies, select, with_policy
from .uncertainty import StabilityMargin, StabilityUncertainty, stability_margin, stability_uncertainty

__version__ = "1.0.0rc2"


def __getattr__(name: str) -> str:
    if name == "__data_version__":
        return ThermodynamicDatabase.bundled().data_version
    raise AttributeError(f"module 'pourbase' has no attribute {name!r}")


__all__ = [
    "ATOMIC_WEIGHT_G_MOL",
    "AqueousActivityModel",
    "BoltzmannSmoothedDiagram",
    "BoundaryEquation",
    "Calculation",
    "CalculationCancelled",
    "Category",
    "ConcentrationConversion",
    "ConcentrationSweep",
    "ConcentrationSweepEngine",
    "DatabaseSchemaError",
    "DaviesActivityCoefficientModel",
    "ElementResult",
    "ElementStatus",
    "EvidenceStatus",
    "ExclusionReason",
    "GasFugacityModel",
    "GibbsEnergyPolicy",
    "IdealActivityCoefficientModel",
    "IncompleteSystemError",
    "LigandActivity",
    "LigandActivityModel",
    "MassBalanceEngine",
    "MassBalancedPourbaixDiagram",
    "MassBalancedState",
    "MaterialsProjectUnavailableError",
    "MetalSystem",
    "MetalSystemNotFoundError",
    "Mode",
    "OfficialMaterialsProjectClient",
    "OfficialMaterialsProjectComparator",
    "OfficialMaterialsProjectComparison",
    "OfficialMaterialsProjectDiagram",
    "OfficialMaterialsProjectPhase",
    "PeriodicScreen",
    "PlatingPotential",
    "PolicyDatabase",
    "PourbaixConditions",
    "PourbaixDiagram",
    "PourbaixEngine",
    "PourbaseError",
    "Probe",
    "Scenario",
    "SelectionPolicy",
    "SourceReference",
    "SpeciationProfile",
    "SpeciesRecord",
    "StabilityMargin",
    "StabilityUncertainty",
    "ThermodynamicDatabase",
    "ThermodynamicSpecies",
    "TotalMetalConcentration",
    "UnsupportedConditionError",
    "UserSpecies",
    "UserSpeciesDatabase",
    "boltzmann_smooth",
    "boundary_equations",
    "calculate",
    "calculate_pourbaix",
    "compare_policies",
    "comparison_metrics",
    "convert_concentration",
    "dataset_from_csv",
    "diagram_figure",
    "dissolved_blend_weights",
    "evaluate_official_materials_project_entries",
    "express_concentration",
    "grid_csv",
    "metal_fraction_grid",
    "metal_molarity_from_mass",
    "open_database",
    "open_dataset",
    "phase_boundary_segments",
    "plating_potentials",
    "plot_boltzmann_diagram",
    "plot_concentration_sweep",
    "plot_diagram",
    "plot_mass_balance_summary",
    "plot_mp_thermochemistry_comparison",
    "plot_official_materials_project_comparison",
    "plot_official_materials_project_diagram",
    "plot_speciation_profile",
    "plot_uncertainty",
    "selection_sensitivity",
    "SelectionSensitivity",
    "read_user_species",
    "save_figure",
    "screen_periodic_table",
    "select",
    "speciation_at",
    "speciation_profile",
    "stability_margin",
    "stability_uncertainty",
    "species_colors",
    "thermodynamic_species_equivalence_key",
    "with_policy",
    "with_user_species",
    "write_mp_thermochemistry_bundle",
]
