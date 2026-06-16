"""
MZI Mesh — Thermal-Optical Coupled Simulation Package
======================================================
Python-based COMSOL surrogate for waveguide-integrated MZI (Mach-Zehnder
Interferometer) mesh networks used in optical matrix multiplication.

Models the full electro-thermal-optical chain:
  Electrical power → Joule heating → temperature distribution
  → thermo-optic Δn → phase shift → optical transfer matrix

Supports:
  - Single MZI: 2×2 unitary matrix U(θ, φ)
  - Clements mesh: N×N arbitrary unitary synthesis
  - SVD engine: general N×M matrix multiplication via M = U Σ V†
  - 2D finite-difference thermal solver with crosstalk
  - Matrix fidelity metrics under thermal crosstalk

Architecture differences from the free-space DiSubPc·C70 thermal sieve:
  - Waveguide-based (Si/SiO₂ SOI platform), not free-space
  - MZI interferometers, not absorption-based thermal modulation
  - Fast weight updates (~μs electro-optic/thermo-optic), not ~30 s thermal
  - 1550 nm C-band, not 850 nm VCSEL
"""

from .params import WaveguideParams, HeaterParams, MZIParams, MeshParams
from .constants import (h, c, kB, q, eps0, sigma_SB,
                        SI_N, SI_DN_DT, SI_K, SI_CP, SI_RHO,
                        SIO2_N, SIO2_K, SIO2_CP, SIO2_RHO,
                        TI_RHO_RES, TI_TCR)
from .mzi import (directional_coupler, phase_shifter_matrix,
                  mzi_transfer_matrix, mzi_params_from_unitary,
                  MZI)
from .phase_shifter import (heater_resistance, thermal_resistance_1d,
                            temperature_rise, phase_shift,
                            phase_shift_from_temperature,
                            p_pi, PhaseShifter)
from .thermal_2d import ThermalGrid2D, ThermalCrosstalkSolver
from .clements_mesh import (clements_decompose, clements_synthesize,
                            clements_mesh_forward, ClementsMesh)
from .svd_engine import SVDEngine, svd_decompose
from .fidelity import (compute_phase_errors, matrix_fidelity,
                       crosstalk_limited_precision, fidelity_vs_spacing)
from .calibration import (phase_voltage_model, fit_phase_voltage,
                         generate_calibration_data)
