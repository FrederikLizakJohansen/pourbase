"""Physical constants and package-wide numerical tolerances."""

from __future__ import annotations

import math

from scipy import constants


FARADAY_C_MOL = constants.physical_constants["Faraday constant"][0]
GAS_CONSTANT_J_MOL_K = constants.R
LN_10 = math.log(10)
REFERENCE_STATE_ABSOLUTE_TOLERANCE = 1e-9
WATER_GIBBS_ENERGY_J_MOL = -237129.0
