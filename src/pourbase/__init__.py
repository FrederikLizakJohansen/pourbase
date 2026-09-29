"""Experimental Gibbs-energy data and Pourbaix calculations."""

from .activity_coefficients import (
    DaviesActivityCoefficientModel,
    IdealActivityCoefficientModel,
)
from .database import ThermodynamicDatabase
from .boltzmann import BoltzmannSmoothedDiagram, boltzmann_smooth
from .conversions import (
    ATOMIC_WEIGHT_G_MOL,
    ConcentrationConversion,
    convert_concentration,
    metal_molarity_from_mass,
)
from .convenience import calculate_pourbaix, open_database
from .engine import PourbaixDiagram, PourbaixEngine
from .equilibria import BoundaryEquation, PlatingPotential, boundary_equations, plating_potentials
from .mass_balance import (
    IdealMassBalanceEngine,
    MassBalanceEngine,
    MassBalancedPourbaixDiagram,
    MassBalancedState,
)
from .materials_project import (
    OfficialMaterialsProjectClient,
    OfficialMaterialsProjectComparator,
    OfficialMaterialsProjectComparison,
    OfficialMaterialsProjectDiagram,
    OfficialMaterialsProjectPhase,
    evaluate_official_materials_project_entries,
    thermodynamic_species_equivalence_key,
)
from .mp_thermochemistry import (
    comparison_metrics,
    plot_mp_thermochemistry_comparison,
    write_mp_thermochemistry_bundle,
)
from .models import (
    AqueousActivityModel,
    ElementSystem,
    GasFugacityModel,
    GibbsEnergyPolicy,
    LigandActivity,
    LigandActivityModel,
    PourbaixConditions,
    TotalMetalConcentration,
    TotalElementConcentration,
)
from .plotting import (
    plot_boltzmann_diagram,
    plot_diagram,
    plot_mass_balance_summary,
    plot_official_materials_project_comparison,
    plot_official_materials_project_diagram,
)
from .speciation import (
    SpeciationProfile,
    metal_fraction_grid,
    plot_speciation_profile,
    speciation_at,
    speciation_profile,
)
from .service import calculate_periodic_table
from .sweeps import ConcentrationSweep, ConcentrationSweepEngine, plot_concentration_sweep

__version__ = "1.0.0rc2"

__all__ = [
    "AqueousActivityModel",
    "ElementSystem",
    "GasFugacityModel",
    "GibbsEnergyPolicy",
    "ATOMIC_WEIGHT_G_MOL",
    "BoundaryEquation",
    "BoltzmannSmoothedDiagram",
    "ConcentrationConversion",
    "ConcentrationSweep",
    "ConcentrationSweepEngine",
    "DaviesActivityCoefficientModel",
    "IdealActivityCoefficientModel",
    "IdealMassBalanceEngine",
    "LigandActivity",
    "LigandActivityModel",
    "MassBalanceEngine",
    "MassBalancedPourbaixDiagram",
    "MassBalancedState",
    "OfficialMaterialsProjectClient",
    "OfficialMaterialsProjectComparator",
    "OfficialMaterialsProjectComparison",
    "OfficialMaterialsProjectDiagram",
    "OfficialMaterialsProjectPhase",
    "PlatingPotential",
    "PourbaixConditions",
    "PourbaixDiagram",
    "PourbaixEngine",
    "ThermodynamicDatabase",
    "TotalMetalConcentration",
    "TotalElementConcentration",
    "SpeciationProfile",
    "boundary_equations",
    "boltzmann_smooth",
    "comparison_metrics",
    "calculate_periodic_table",
    "calculate_pourbaix",
    "convert_concentration",
    "evaluate_official_materials_project_entries",
    "metal_fraction_grid",
    "metal_molarity_from_mass",
    "open_database",
    "plating_potentials",
    "plot_concentration_sweep",
    "plot_boltzmann_diagram",
    "plot_diagram",
    "plot_mass_balance_summary",
    "plot_mp_thermochemistry_comparison",
    "plot_official_materials_project_comparison",
    "plot_official_materials_project_diagram",
    "plot_speciation_profile",
    "speciation_at",
    "speciation_profile",
    "thermodynamic_species_equivalence_key",
    "write_mp_thermochemistry_bundle",
]
