"""
Physical constants and Si-photonics material properties.

Reuses fundamental constants from comprehensive_validation.py and adds
silicon photonics-specific material data for the SOI platform.

All values sourced from well-established literature.
"""

import numpy as np

# ============================================================
# Fundamental Physical Constants
# (from comprehensive_validation.py)
# ============================================================
h = 6.62607015e-34       # Planck constant (J·s)
c = 2.99792458e8          # Speed of light in vacuum (m/s)
kB = 1.380649e-23         # Boltzmann constant (J/K)
q = 1.602176634e-19       # Elementary charge (C)
eps0 = 8.854187817e-12    # Vacuum permittivity (F/m)
sigma_SB = 5.670374419e-8 # Stefan-Boltzmann constant (W/m²·K⁴)

# ============================================================
# Silicon (Si) — Waveguide Core Material
# Sources:
#   n @1550nm: Palik, Handbook of Optical Constants of Solids (1985)
#   dn/dT: Komma et al., Opt. Lett. 37(9), 2012
#   k: Glassbrenner & Slack, Phys. Rev. 134(4A), 1964
# ============================================================
SI_N = 3.476              # Refractive index @1550nm, 300K
SI_DN_DT = 1.80e-4        # Thermo-optic coefficient (K⁻¹)
SI_K = 148.0              # Thermal conductivity (W/m·K) — bulk, 300K
SI_CP = 700.0             # Specific heat capacity (J/kg·K)
SI_RHO = 2329.0           # Density (kg/m³)

# Temperature-dependent thermal conductivity (K⁻¹, approximate linear coefficient)
SI_K_DKDT = -0.30         # dk/dT for Si around 300K (W/m·K²)

def si_thermal_conductivity(T_K: float) -> float:
    """Si thermal conductivity at temperature T (K).

    Fits Glassbrenner & Slack (1964) data around 300-500K.
    """
    return SI_K + SI_K_DKDT * (T_K - 300.0)

# ============================================================
# Silicon Dioxide (SiO₂) — Cladding and Spacer
# Sources:
#   n @1550nm: Malitson, JOSA 55(10), 1965
#   k: Cahill, Rev. Sci. Instrum. 61(2), 1990 (thin film)
# ============================================================
SIO2_N = 1.444             # Refractive index @1550nm
SIO2_K = 1.38              # Thermal conductivity (W/m·K) — PECVD thin film
SIO2_CP = 730.0            # Specific heat capacity (J/kg·K)
SIO2_RHO = 2200.0          # Density (kg/m³)

# ============================================================
# Titanium (Ti) — Microheater Material
# Sources:
#   Resistivity: Harris et al., IEEE TCPMT 5(4), 2015 (thin film Ti)
#   TCR: measured for e-beam evaporated Ti thin film
# ============================================================
TI_RHO_RES = 4.20e-7       # Electrical resistivity (Ω·m) — thin film Ti
TI_TCR = 0.0038            # Temperature coefficient of resistance (K⁻¹)
TI_K = 21.9                # Thermal conductivity (W/m·K) — bulk Ti
TI_CP = 520.0              # Specific heat capacity (J/kg·K)
TI_RHO = 4506.0            # Density (kg/m³)

# ============================================================
# Thermal Boundary / Interface Values
# ============================================================
# Convective heat transfer coefficient at chip top surface (natural convection)
H_CONV_TOP = 10.0          # W/m²·K

# Si-SiO2 interface thermal boundary resistance (negligible for our scale)
TBR_SI_SIO2 = 2.0e-9       # K·m²/W (approximate from literature)

# ============================================================
# Optical / Telecom C-band
# ============================================================
LAMBDA_1550 = 1550.0       # nm, standard telecom wavelength
LAMBDA_1310 = 1310.0       # nm, O-band alternative

# ============================================================
# Derived Quantities
# ============================================================
def photon_energy(wavelength_nm: float) -> float:
    """Photon energy in Joules for a given wavelength in nm."""
    return h * c / (wavelength_nm * 1e-9)


def thermal_voltage(kT_J: float | None = None, T_K: float = 300.0) -> float:
    """Thermal voltage kT/q in Volts."""
    E = kT_J if kT_J is not None else kB * T_K
    return E / q


def thermal_diffusivity(k: float, rho: float, cp: float) -> float:
    """Thermal diffusivity α = k/(ρ·cp) in m²/s."""
    return k / (rho * cp)
