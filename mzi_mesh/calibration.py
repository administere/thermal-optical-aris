"""
Phase-Voltage Calibration
==========================

Real MZI meshes require per-MZI calibration due to fabrication variations.
The standard model for thermo-optic phase shifters is:

    φ(V) = φ₀ + φ₂ · V²

where:
  - φ₀ is the passive phase offset (from path length differences)
  - φ₂ is the quadratic coefficient (from P = V²/R → ΔT ∝ P → Δφ ∝ ΔT)

This module fits calibration data and generates synthetic calibration
curves for simulation studies.
"""

import numpy as np
from typing import Tuple, Dict
from scipy.optimize import curve_fit
from .phase_shifter import PhaseShifter, phase_shift


def phase_voltage_model(voltage: float, phi_0: float, phi_2: float) -> float:
    """Quadratic phase-voltage model: φ(V) = φ₀ + φ₂ · V²

    This is the standard model for thermo-optic phase shifters.
    The V² dependence comes from: P = V²/R, ΔT = P·R_th, Δφ ∝ ΔT.

    Args:
        voltage: applied voltage (V)
        phi_0: passive phase offset (rad)
        phi_2: quadratic coefficient (rad/V²)

    Returns:
        Phase shift in radians
    """
    return phi_0 + phi_2 * voltage**2


def fit_phase_voltage(voltages: np.ndarray,
                       measured_phases: np.ndarray,
                       phi_2_initial: float = 0.5) -> Tuple[float, float, np.ndarray]:
    """Least-squares fit of φ₀ and φ₂ from calibration data.

    Args:
        voltages: array of applied voltages (V)
        measured_phases: array of measured phase shifts (rad)
        phi_2_initial: initial guess for φ₂ (rad/V²)

    Returns:
        (phi_0, phi_2, fitted_phases) tuple
    """
    popt, pcov = curve_fit(
        lambda V, p0, p2: phase_voltage_model(V, p0, p2),
        voltages, measured_phases,
        p0=[0.0, phi_2_initial],
        maxfev=10000,
    )
    phi_0, phi_2 = popt
    fitted_phases = phase_voltage_model(voltages, phi_0, phi_2)
    return phi_0, phi_2, fitted_phases


def generate_calibration_data(voltage_range: Tuple[float, float] = (0.0, 10.0),
                               n_points: int = 20,
                               phi_0_true: float = 0.1,
                               phi_2_true: float = 0.5,
                               phase_noise_std: float = 0.02,
                               voltage_noise_std: float = 0.01) -> Dict:
    """Generate synthetic calibration data with measurement noise.

    Simulates a calibration measurement where we sweep the heater voltage
    and measure the resulting phase shift (e.g., via Mach-Zehnder
    interference fringe measurement).

    Args:
        voltage_range: (V_min, V_max) sweep range
        n_points: number of measurement points
        phi_0_true: true passive phase offset (rad)
        phi_2_true: true quadratic coefficient (rad/V²)
        phase_noise_std: std of Gaussian phase measurement noise (rad)
        voltage_noise_std: std of voltage source noise (V)

    Returns:
        Dict with 'voltages', 'phases_measured', 'phases_true',
        'phi_0_true', 'phi_2_true'
    """
    V_ideal = np.linspace(voltage_range[0], voltage_range[1], n_points)
    V_actual = V_ideal + np.random.normal(0, voltage_noise_std, n_points)
    phases_true = phase_voltage_model(V_actual, phi_0_true, phi_2_true)
    phases_measured = phases_true + np.random.normal(0, phase_noise_std, n_points)

    return {
        'voltages': V_actual,
        'phases_measured': phases_measured,
        'phases_true': phases_true,
        'phi_0_true': phi_0_true,
        'phi_2_true': phi_2_true,
    }


def calibration_error_analysis(phi_0_fit: float, phi_2_fit: float,
                                phi_0_true: float, phi_2_true: float,
                                V_typical: float = 5.0) -> Dict:
    """Analyze calibration errors.

    Computes the phase error at a typical operating voltage due to
    calibration parameter errors.

    Args:
        phi_0_fit, phi_2_fit: fitted parameters
        phi_0_true, phi_2_true: true parameters
        V_typical: typical operating voltage

    Returns:
        Dict with error metrics
    """
    phi_fit = phase_voltage_model(V_typical, phi_0_fit, phi_2_fit)
    phi_true = phase_voltage_model(V_typical, phi_0_true, phi_2_true)

    return {
        'phi_error_rad': phi_fit - phi_true,
        'phi_error_deg': np.degrees(phi_fit - phi_true),
        'phi_error_pct': abs(phi_fit - phi_true) / max(abs(phi_true), 1e-15) * 100,
        'phi_0_error': phi_0_fit - phi_0_true,
        'phi_2_error': phi_2_fit - phi_2_true,
    }
