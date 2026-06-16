"""
Thermo-Optic Phase Shifter Model
=================================
Electro-thermal-optical chain for a Ti microheater on an SOI waveguide.

Physics chain:
  1. Electrical:    P = V² / R
  2. Thermal:       ΔT = P · R_th  (1D analytical, validated against 2D FD)
  3. Thermo-optic:  Δn = dn/dT · ΔT
  4. Phase shift:   Δφ = (2π/λ) · Δn · L_heated

This module provides the 1D analytical model (fast, good for exploration)
and serves as validation baseline for the 2D finite-difference thermal solver.

Key metric: Pπ — electrical power required for π phase shift.
  Standard SOI: Pπ ≈ 12–25 mW (Harris et al., Opt. Express 2014)
"""

import numpy as np
from .params import HeaterParams, WaveguideParams


def heater_resistance(heater: HeaterParams) -> float:
    """DC electrical resistance of the Ti microheater.

    R = ρ · L / A = ρ · L / (W · t)

    Args:
        heater: heater geometry and material parameters

    Returns:
        Resistance in Ohms
    """
    L = heater.length_um * 1e-6       # m
    A = heater.width_um * heater.thickness_um * 1e-12  # m²
    return heater.resistivity_Ohm_m * L / A


def heater_resistance_at_T(heater: HeaterParams, T_K: float,
                           TCR: float = 0.0038) -> float:
    """Resistance at elevated temperature including TCR.

    R(T) = R₀ · (1 + TCR · (T - T_amb))

    Args:
        heater: heater parameters
        T_K: operating temperature (K)
        TCR: temperature coefficient of resistance (K⁻¹)

    Returns:
        Resistance in Ohms at temperature T
    """
    R0 = heater_resistance(heater)
    return R0 * (1 + TCR * (T_K - heater.T_amb))


def thermal_resistance_1d(heater: HeaterParams,
                           waveguide: WaveguideParams) -> float:
    """1D analytical thermal resistance from heater to substrate.

    Uses a cylindrical heat-spreading model. The heat generated in the
    Ti heater flows down through the SiO₂ spacer into the Si waveguide
    and Si substrate (which acts as a heat sink).

    Geometry (cross-section):
         Ti heater  ─┐
         SiO₂ spacer │ ← vertical heat flow
         Si waveguide│
         BOX SiO₂    │
         Si substrate (T = T_amb) ← heat sink

    Approximate as series thermal resistances:
      R_th ≈ R_spacer + R_wg + R_box
    where each layer's resistance is:
      R = ln(r_outer / r_inner) / (2π · k · L)   (cylindrical)

    For a more practical approximation, use the linear heat flow model:
      R_th ≈ d / (k · A_eff)

    With effective area A_eff ≈ heater_width · heater_length and
    effective distance from heater center to substrate ≈ 10-20 μm.

    Args:
        heater: heater parameters
        waveguide: waveguide parameters

    Returns:
        Thermal resistance in K/W
    """
    L = heater.length_um * 1e-6  # Length in m

    # Effective heat spreading width (μm): heater width + 2× spacer
    w_eff = (heater.width_um + 2 * heater.spacer_um) * 1e-6
    A_eff = w_eff * L  # m²

    # SiO₂ spacer: direct vertical path
    d_spacer = heater.spacer_um * 1e-6  # m
    R_spacer = d_spacer / (heater.k_sio2 * A_eff)

    # Si waveguide (thin, high k → low R)
    d_wg = waveguide.height_um * 1e-6  # m
    R_wg = d_wg / (heater.k_si * A_eff)

    # BOX SiO₂ (typically 2 μm)
    d_box = 2.0e-6  # m (typical buried oxide thickness)
    R_box = d_box / (heater.k_sio2 * A_eff)

    # Si substrate spreading resistance
    # Heat spreads spherically into the thick Si substrate
    # R_sub ≈ 1 / (4 · k_si · r_eff)   (spreading resistance to half-space)
    r_eff = w_eff / 2
    R_sub = 1.0 / (4.0 * heater.k_si * r_eff) if r_eff > 0 else 0

    return R_spacer + R_wg + R_box + R_sub


def temperature_rise(voltage: float, heater: HeaterParams,
                     waveguide: WaveguideParams) -> float:
    """Steady-state temperature rise from applied voltage.

    ΔT = V² / (R · R_th_corrected)

    Includes TCR self-consistent correction: as temperature rises,
    resistance increases, reducing the actual power slightly at
    fixed voltage. Solved self-consistently:

        V² / R(T) = ΔT / R_th
        V² / [R₀(1 + TCR·ΔT)] = ΔT / R_th
        → ΔT² + ΔT/TCR - V²/(R₀·TCR·R_th) = 0

    Args:
        voltage: applied voltage (V)
        heater: heater parameters
        waveguide: waveguide parameters

    Returns:
        Temperature rise ΔT in Kelvin
    """
    R0 = heater_resistance(heater)
    R_th = thermal_resistance_1d(heater, waveguide)
    TCR = 0.0038  # K⁻¹ for Ti

    # Self-consistent solution including TCR
    # V²/[R₀(1+TCR·ΔT)] = ΔT/R_th
    # → TCR·ΔT² + ΔT - V²·R_th/R₀ = 0
    a = TCR
    b = 1.0
    c_val = -voltage**2 * R_th / R0

    # Positive root
    discriminant = b**2 - 4 * a * c_val
    if discriminant < 0:
        return 0.0
    delta_T = (-b + np.sqrt(discriminant)) / (2 * a)
    return max(0.0, delta_T)


def temperature_rise_from_power(power_W: float, heater: HeaterParams,
                                 waveguide: WaveguideParams) -> float:
    """Steady-state temperature rise from dissipated electrical power.

    ΔT = P · R_th

    This is the simpler model — ignores TCR feedback on resistance.

    Args:
        power_W: electrical power dissipated in heater (W)
        heater: heater parameters
        waveguide: waveguide parameters

    Returns:
        Temperature rise ΔT in Kelvin
    """
    R_th = thermal_resistance_1d(heater, waveguide)
    return power_W * R_th


def phase_shift_from_temperature(delta_T: float, heater: HeaterParams,
                                  waveguide: WaveguideParams,
                                  wavelength_nm: float = 1550.0) -> float:
    """Phase shift from temperature rise via thermo-optic effect.

    Δφ = (2π/λ) · Δn_eff · L_heated
       = (2π/λ) · (dn_eff/dT · ΔT) · L_heated

    Note: dn_eff/dT is slightly less than dn_Si/dT because the optical mode
    is partially in the SiO₂ cladding (which has ~10× smaller dn/dT).
    We use ~85% confinement factor in Si for a 0.5×0.22 μm strip waveguide.

    Args:
        delta_T: temperature rise (K)
        heater: heater parameters (for length)
        waveguide: waveguide parameters (for dn/dT)
        wavelength_nm: operating wavelength (nm)

    Returns:
        Phase shift in radians
    """
    # Confinement factor: fraction of mode energy in Si (vs SiO₂)
    confinement_Si = 0.85  # typical for 0.5×0.22 μm strip waveguide TE mode
    dn_eff_dT = waveguide.dn_dT * confinement_Si

    # Δn_eff from temperature
    delta_n_eff = dn_eff_dT * delta_T

    # Phase shift
    L = heater.length_um * 1e-6  # m
    k0 = 2 * np.pi / (wavelength_nm * 1e-9)  # rad/m
    delta_phi = k0 * delta_n_eff * L

    return delta_phi


def phase_shift(voltage: float, heater: HeaterParams,
                waveguide: WaveguideParams,
                wavelength_nm: float = 1550.0) -> float:
    """Phase shift from applied voltage (full electro-thermal-optical chain).

    Args:
        voltage: applied voltage (V)
        heater: heater parameters
        waveguide: waveguide parameters
        wavelength_nm: operating wavelength (nm)

    Returns:
        Phase shift in radians
    """
    delta_T = temperature_rise(voltage, heater, waveguide)
    return phase_shift_from_temperature(delta_T, heater, waveguide, wavelength_nm)


def p_pi(heater: HeaterParams, waveguide: WaveguideParams,
         wavelength_nm: float = 1550.0) -> float:
    """Pπ — electrical power required for π phase shift.

    From Δφ = (2π/λ) · dn_eff/dT · ΔT · L = π:
      ΔT_π = λ / (2 · dn_eff/dT · L)
      P_π = ΔT_π / R_th

    This is a key figure of merit for thermo-optic phase shifters.
    Typical values: 12–25 mW for standard SOI platform.

    Args:
        heater: heater parameters
        waveguide: waveguide parameters
        wavelength_nm: operating wavelength

    Returns:
        Pπ in Watts
    """
    # Confinement factor
    confinement_Si = 0.85
    dn_eff_dT = waveguide.dn_dT * confinement_Si

    # Temperature rise needed for π
    L = heater.length_um * 1e-6
    delta_T_pi = wavelength_nm * 1e-9 / (2 * dn_eff_dT * L)

    # Thermal resistance
    R_th = thermal_resistance_1d(heater, waveguide)

    # Power for π
    P_pi = delta_T_pi / R_th
    return P_pi


class PhaseShifter:
    """A single thermo-optic phase shifter.

    Encapsulates the full electro-thermal-optical chain for one
    phase shifter in an MZI. Can be driven by voltage or power.
    """

    def __init__(self, heater: HeaterParams | None = None,
                 waveguide: WaveguideParams | None = None,
                 wavelength_nm: float = 1550.0,
                 phase_offset: float = 0.0):
        self.heater = heater or HeaterParams()
        self.waveguide = waveguide or WaveguideParams()
        self.wavelength_nm = wavelength_nm
        self.phase_offset = phase_offset  # Passive phase (from path length)
        self._voltage = 0.0
        self._delta_T = 0.0

    @property
    def R_Ohm(self) -> float:
        return heater_resistance(self.heater)

    @property
    def R_th(self) -> float:
        return thermal_resistance_1d(self.heater, self.waveguide)

    @property
    def P_pi(self) -> float:
        return p_pi(self.heater, self.waveguide, self.wavelength_nm)

    def set_voltage(self, V: float) -> None:
        """Set heater voltage and compute resulting temperature/phase."""
        self._voltage = V
        self._delta_T = temperature_rise(V, self.heater, self.waveguide)

    def set_power(self, P_W: float) -> None:
        """Set heater power directly (bypasses TCR correction)."""
        self._delta_T = temperature_rise_from_power(
            P_W, self.heater, self.waveguide)
        R = self.R_Ohm
        self._voltage = np.sqrt(P_W * R) if R > 0 else 0.0

    def set_phase(self, target_phase: float) -> float:
        """Set heater to achieve a target phase shift (returns required voltage)."""
        # Invert: φ = (2π/λ) · dn_eff/dT · (V²/R_th/R) · L
        # → V² = φ · R · R_th / [(2π/λ) · dn_eff/dT · L]
        confinement_Si = 0.85
        dn_eff_dT = self.waveguide.dn_dT * confinement_Si
        L = self.heater.length_um * 1e-6
        k0 = 2 * np.pi / (self.wavelength_nm * 1e-9)

        R_th = self.R_th
        R0 = self.R_Ohm

        # Approximate (ignoring TCR for initial guess)
        V2 = target_phase * R0 / (k0 * dn_eff_dT * L * R_th)
        V = np.sqrt(max(0, V2))

        # Iterate to include TCR
        for _ in range(5):
            delta_T = temperature_rise(V, self.heater, self.waveguide)
            phi_actual = phase_shift_from_temperature(
                delta_T, self.heater, self.waveguide, self.wavelength_nm)
            if phi_actual > 1e-12:
                V *= np.sqrt(target_phase / phi_actual)

        self.set_voltage(V)
        return V

    @property
    def phase(self) -> float:
        """Current total phase shift (radians)."""
        return self.phase_offset + phase_shift_from_temperature(
            self._delta_T, self.heater, self.waveguide, self.wavelength_nm)

    @property
    def delta_T(self) -> float:
        """Current temperature rise (K)."""
        return self._delta_T

    @property
    def T_K(self) -> float:
        """Current absolute temperature (K)."""
        return self.heater.T_amb + self._delta_T

    @property
    def power_W(self) -> float:
        """Current electrical power dissipation (W)."""
        if self._voltage > 0 and self.R_Ohm > 0:
            return self._voltage**2 / heater_resistance_at_T(
                self.heater, self.T_K)
        return 0.0

    def __repr__(self) -> str:
        return (f"PhaseShifter(φ={self.phase:.3f} rad, "
                f"ΔT={self.delta_T:.1f} K, "
                f"V={self._voltage:.2f} V, "
                f"P={self.power_W*1000:.2f} mW)")
