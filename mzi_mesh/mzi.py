"""
Single Mach-Zehnder Interferometer (MZI) — Optical Transfer Matrix
===================================================================

Implements the standard Clements/Reck convention for the 2×2 unitary:

    T(θ, φ) = [[cos(θ),           -e^{-iφ}·sin(θ)],
               [e^{iφ}·sin(θ),     cos(θ)         ]]

This is unitary: T·T† = I.

The nullification property:
    T†[0,:] · [a, b]^T = cos(θ)·a + e^{-iφ}·sin(θ)·b = 0

can be satisfied for any complex (a,b) by choosing:
    θ = arctan(|a|/|b|)
    φ = π + arg(a) - arg(b)

The physical MZI (DC @ PS(θ) @ DC @ PS(φ)) produces an equivalent
unitary up to a reparameterization. The Clements convention is
chosen here for mathematical convenience in the decomposition.

References:
  - Clements et al., Optica 3(12), 1460-1465 (2016)
  - Pai et al., "Parallel Programming of an Arbitrary Feedforward
    Photonic Network", IEEE JSTQE 2020
"""

import numpy as np
from typing import Tuple


def mzi_transfer_matrix(theta: float, phi: float) -> np.ndarray:
    """Standard Clements/Reck MZI transfer matrix.

    T(θ, φ) = [[cos(θ),           -e^{-iφ}·sin(θ)],
               [e^{iφ}·sin(θ),     cos(θ)         ]]

    This is a 2×2 unitary matrix.

    Args:
        theta: power splitting angle (radians), θ ∈ [0, π/2]
               θ=0: bar state (all transmitted straight)
               θ=π/4: 50:50 splitter
               θ=π/2: cross state (all crossed)
        phi: relative phase (radians), φ ∈ [0, 2π)

    Returns:
        2×2 complex unitary transfer matrix
    """
    ct = np.cos(theta)
    st = np.sin(theta)
    e_ip = np.exp(1j * phi)
    e_im = np.exp(-1j * phi)

    return np.array([[ct, -e_im * st],
                     [e_ip * st, ct]], dtype=complex)


def mzi_params_from_unitary(U_target: np.ndarray) -> Tuple[float, float]:
    """Extract (θ, φ) from a target 2×2 unitary in Clements convention.

    Given T(θ, φ) = [[cos(θ), -e^{-iφ}sin(θ)], [e^{iφ}sin(θ), cos(θ)]]:

      |u11| = |cos(θ)|  →  θ = arccos(|u11|)
      u21/u11 = e^{iφ}·tan(θ)  →  φ = arg(u21/u11)  [when tan(θ) > 0]

    Since θ ∈ [0, π/2] in this convention, cos(θ) ≥ 0 and sin(θ) ≥ 0.

    Args:
        U_target: 2×2 unitary in Clements MZI form

    Returns:
        (theta, phi) in radians
    """
    U = np.asarray(U_target, dtype=complex)
    if U.shape != (2, 2):
        raise ValueError(f"Expected 2×2 matrix, got {U.shape}")

    # θ from |u11| = cos(θ), θ ∈ [0, π/2]
    theta = np.arccos(np.clip(abs(U[0, 0]), 0.0, 1.0))

    # φ from u11 = cos(θ):
    # u21/u11 = e^{iφ}·tan(θ)
    # For the Clements form, u21/u11 should be e^{iφ}·tan(θ) with real tan(θ)
    st = np.sin(theta)
    ct = np.cos(theta)
    if st > 1e-15 and ct > 1e-15:
        # u21 = e^{iφ}·sin(θ), u11 = cos(θ)
        # e^{iφ} = u21 / sin(θ) = u21 / st
        e_iphi = U[1, 0] / st
        phi = np.angle(e_iphi) % (2 * np.pi)
    elif abs(U[0, 1]) > 1e-15:
        # u12 = -e^{-iφ}·sin(θ)
        # e^{-iφ} = -u12/st → e^{iφ} = -st/u12
        e_iphi = -st / U[0, 1]
        phi = np.angle(e_iphi) % (2 * np.pi)
    else:
        phi = 0.0

    # Verify
    U_rec = mzi_transfer_matrix(theta, phi)
    if not np.allclose(U_rec, U, atol=1e-10):
        raise ValueError(f"Matrix not in Clements MZI form "
                         f"(error: {np.max(np.abs(U_rec - U)):.2e})")

    return theta, phi


def directional_coupler(split_ratio: float = 0.5,
                        excess_loss_dB: float = 0.0) -> np.ndarray:
    """Transfer matrix for a directional coupler.

    Note: This is the PHYSICAL coupler matrix. For the mathematical
    Clements decomposition, use mzi_transfer_matrix directly.

    DC = [[√(1-κ),  i√κ     ],
          [i√κ,      √(1-κ) ]]
    """
    kappa = split_ratio
    transmission = 10 ** (-excess_loss_dB / 20.0)
    t = transmission * np.sqrt(1 - kappa)
    k = transmission * np.sqrt(kappa)
    return np.array([[t, 1j * k], [1j * k, t]], dtype=complex)


def phase_shifter_matrix(phi: float) -> np.ndarray:
    """Phase shifter on the upper arm: PS(φ) = diag(e^{iφ}, 1)."""
    return np.array([[np.exp(1j * phi), 0], [0, 1]], dtype=complex)


class MZI:
    """A single Mach-Zehnder Interferometer using the Clements convention.

    Holds current (θ, φ) settings and provides forward propagation.
    """

    def __init__(self, theta: float = 0.0, phi: float = 0.0):
        self.theta = theta
        self.phi = phi

    @property
    def matrix(self) -> np.ndarray:
        return mzi_transfer_matrix(self.theta, self.phi)

    def program(self, U_target: np.ndarray) -> None:
        self.theta, self.phi = mzi_params_from_unitary(U_target)

    def forward(self, x: np.ndarray) -> np.ndarray:
        return self.matrix @ np.asarray(x)

    def __repr__(self) -> str:
        return (f"MZI(θ={np.degrees(self.theta):.0f}°, "
                f"φ={np.degrees(self.phi):.0f}°)")
