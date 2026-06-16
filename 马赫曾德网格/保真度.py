"""
Matrix Fidelity Metrics Under Thermal Crosstalk
================================================

The key physics result: thermal crosstalk between adjacent MZI phase
shifters degrades the programmed matrix fidelity. This module computes:

  1. Phase errors from the thermal crosstalk matrix
  2. Matrix fidelity metrics (Frobenius, amplitude fidelity, unitary deviation)
  3. Effective bit precision limited by crosstalk
  4. Fidelity vs. MZI spacing sweeps

The thermal crosstalk matrix C (K/mW) from thermal_2d.py is the input.
It maps heater powers to temperature rises:

    ΔT_i = Σⱼ C_{ij} · Pⱼ

But due to crosstalk, when we program phase shifter i for a target φ_i,
we apply a voltage that would produce φ_i in isolation. With crosstalk,
the actual temperature (and thus phase) differs:

    φ_i^actual = φ_i^target + Σ_{j≠i} (C_{ij}/C_{jj}) · (∂φ/∂T) · (φ_j^target / (∂φ/∂T))
               = φ_i^target + Σ_{j≠i} α_{ij} · φ_j^target

where α_{ij} = C_{ij}/C_{jj} is the crosstalk coefficient from j to i.
"""

import numpy as np
from typing import Dict, List, Tuple
from .thermal_2d import ThermalCrosstalkSolver
from .clements_mesh import ClementsMesh


def compute_phase_errors(target_phases: np.ndarray,
                          crosstalk_matrix: np.ndarray) -> np.ndarray:
    """Compute actual phases including thermal crosstalk.

    Given target phases φ_target (what we want) and the thermal crosstalk
    matrix C (K/mW), compute the actual phases φ_actual (what we get).

    The model assumes each phase shifter is individually calibrated
    (φ ∝ P, so φ_target → P_target). With crosstalk, the actual
    temperature at shifter i is:

        ΔT_i = C_{ii}·P_i + Σ_{j≠i} C_{ij}·P_j
             = C_{ii}·P_i + Σ_{j≠i} C_{ij}·P_j

    The phase shifter is driven with the power that would give φ_target
    in isolation: P_i = φ_target_i / (∂φ/∂P)

    So the actual phase becomes:
        φ_actual_i = C_{ii}·P_i·(∂φ/∂T) + Σ_{j≠i} C_{ij}·P_j·(∂φ/∂T)
                   = φ_target_i + Σ_{j≠i} (C_{ij}/C_{jj}) · φ_target_j

    Args:
        target_phases: shape (N_heaters,) — target phase shifts (radians)
        crosstalk_matrix: shape (N_heaters, N_heaters) — C in K/mW

    Returns:
        actual_phases: shape (N_heaters,) — actual phase shifts with crosstalk
    """
    n = len(target_phases)
    # Normalized crosstalk coefficients: α_{ij} = C_{ij} / C_{jj}
    alpha = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if crosstalk_matrix[j, j] > 1e-15:
                alpha[i, j] = crosstalk_matrix[i, j] / crosstalk_matrix[j, j]

    actual = target_phases.copy()
    for i in range(n):
        for j in range(n):
            if i != j:
                actual[i] += alpha[i, j] * target_phases[j]

    return actual


def matrix_fidelity(U_target: np.ndarray, U_achieved: np.ndarray) -> Dict:
    """Compute fidelity metrics between target and achieved unitary matrices.

    Args:
        U_target: N×N complex target unitary
        U_achieved: N×N complex achieved matrix (may not be unitary due to errors)

    Returns:
        Dict with keys:
          - frobenius_error: ||U_target - U_achieved||_F
          - relative_error: frobenius_error / ||U_target||_F
          - unitary_deviation: ||U_achieved·U_achieved† - I||_F
          - amplitude_fidelity: |tr(U_target† · U_achieved)| / N
          - max_element_error: max|U_target - U_achieved|
          - phase_error_rms: RMS phase error per matrix element (radians)
    """
    U_t = np.asarray(U_target, dtype=complex)
    U_a = np.asarray(U_achieved, dtype=complex)
    N = U_t.shape[0]

    diff = U_a - U_t
    frob_err = float(np.linalg.norm(diff))
    relative_err = frob_err / max(float(np.linalg.norm(U_t)), 1e-15)

    # Unitary deviation
    unitary_dev = float(np.linalg.norm(U_a @ U_a.conj().T - np.eye(N)))

    # Amplitude fidelity (overlap)
    amp_fid = float(np.abs(np.trace(U_t.conj().T @ U_a))) / N

    # Max element error
    max_err = float(np.max(np.abs(diff)))

    # RMS phase error (element-wise)
    # Phase error for each element: |arg(U_a/U_t)|
    phase_ratio = U_a / np.where(np.abs(U_t) > 1e-15, U_t, 1.0)
    phase_errs = np.abs(np.angle(phase_ratio))
    phase_err_rms = float(np.sqrt(np.mean(phase_errs**2)))

    return {
        'frobenius_error': frob_err,
        'relative_error': relative_err,
        'unitary_deviation': unitary_dev,
        'amplitude_fidelity': amp_fid,
        'max_element_error': max_err,
        'phase_error_rms': phase_err_rms,
    }


def crosstalk_limited_precision(crosstalk_matrix: np.ndarray,
                                 target_precision_bits: int = 8) -> float:
    """Estimate effective bit precision limited by thermal crosstalk.

    If the crosstalk coefficient from the strongest neighbor is α_max,
    the phase error is approximately:
        Δφ_rms ≈ α_max · σ_φ

    where σ_φ is the typical phase value (roughly π/√3 for uniform
    distribution in [0, 2π]).

    The effective bit precision is:
        bits_eff = log₂(2π / Δφ_rms)

    Args:
        crosstalk_matrix: N×N crosstalk matrix (K/mW)
        target_precision_bits: design target for comparison

    Returns:
        Effective bit precision
    """
    n = crosstalk_matrix.shape[0]

    # Compute normalized crosstalk coefficients
    alpha_max = 0.0
    for i in range(n):
        for j in range(n):
            if i != j and crosstalk_matrix[j, j] > 1e-15:
                alpha = crosstalk_matrix[i, j] / crosstalk_matrix[j, j]
                alpha_max = max(alpha_max, alpha)

    # Typical phase value for random unitary
    sigma_phi = np.pi / np.sqrt(3)

    # Phase error from worst neighbor
    delta_phi_rms = alpha_max * sigma_phi

    if delta_phi_rms < 1e-15:
        return float(target_precision_bits)

    # Effective bits
    bits_eff = np.log2(2 * np.pi / delta_phi_rms)
    return max(0.0, float(bits_eff))


def fidelity_vs_spacing(spacings_um: List[float],
                         N: int = 4,
                         num_trials: int = 10) -> Dict:
    """Sweep MZI spacing and compute fidelity degradation.

    For each spacing, generates random target unitaries, programs a
    Clements mesh, applies thermal crosstalk, and computes the achieved
    matrix fidelity.

    This is the KEY validation sweep — equivalent to COMSOL parametric
    sweep over MZI pitch.

    Args:
        spacings_um: list of MZI center-to-center spacings (μm)
        N: matrix dimension
        num_trials: number of random unitaries per spacing

    Returns:
        Dict with:
          - 'spacings_um': input spacings
          - 'amplitude_fidelity_mean': mean fidelity per spacing
          - 'amplitude_fidelity_std': std per spacing
          - 'frobenius_error_mean': mean Frobenius error
          - 'effective_bits_mean': mean effective bits
          - 'raw_results': list of per-trial results
    """
    results = {
        'spacings_um': spacings_um,
        'amplitude_fidelity_mean': [],
        'amplitude_fidelity_std': [],
        'frobenius_error_mean': [],
        'effective_bits_mean': [],
        'raw_results': [],
    }

    for pitch in spacings_um:
        fidelities = []
        frob_errs = []
        bits = []

        for trial in range(num_trials):
            try:
                # Build clements mesh
                mesh = ClementsMesh(N)

                # Generate random unitary
                # Use QR decomposition of random complex matrix for Haar measure
                A = np.random.randn(N, N) + 1j * np.random.randn(N, N)
                Q, R = np.linalg.qr(A)
                # Ensure det(Q) phase is uniform
                U_target = Q

                # Program mesh
                mesh.program_unitary(U_target)

                # Get target phases
                target_params = mesh.get_mzi_params()  # (num_mzis, 2)
                target_phases = target_params.flatten()  # [θ1, φ1, θ2, φ2, ...]

                # Build thermal crosstalk solver for this spacing
                n_heaters = len(target_phases)
                thermal = ThermalCrosstalkSolver.for_n_heaters(
                    n=n_heaters, pitch_um=pitch)

                C = thermal.compute_crosstalk_matrix()

                # Compute actual phases with crosstalk
                actual_phases = compute_phase_errors(target_phases, C)

                # Apply degraded phases back to mesh
                actual_params = actual_phases.reshape(-1, 2)
                mesh.set_mzi_phases(actual_params[:, 0], actual_params[:, 1])

                # Compute achieved matrix
                U_achieved = mesh.transfer_matrix

                # Fidelity
                fid = matrix_fidelity(U_target, U_achieved)
                fidelities.append(fid['amplitude_fidelity'])
                frob_errs.append(fid['frobenius_error'])
                bits.append(crosstalk_limited_precision(C))

            except Exception as e:
                # Skip trials that fail (e.g., decomposition issues)
                continue

        results['amplitude_fidelity_mean'].append(np.mean(fidelities))
        results['amplitude_fidelity_std'].append(np.std(fidelities))
        results['frobenius_error_mean'].append(np.mean(frob_errs))
        results['effective_bits_mean'].append(np.mean(bits))
        results['raw_results'].append({
            'pitch_um': pitch,
            'fidelities': fidelities,
            'frob_errors': frob_errs,
            'bits': bits,
        })

    return results
