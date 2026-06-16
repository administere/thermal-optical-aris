"""
SVD Engine — General N×M Matrix Multiplication via M = U Σ V†
===============================================================

Uses Singular Value Decomposition to reduce any N×M matrix multiplication to:
  1. Unitary transformation V† (Clements mesh #1)
  2. Diagonal scaling Σ (attenuator array)
  3. Unitary transformation U (Clements mesh #2)

This is the optical equivalent of:
    y = M · x
    → y = U · Σ · V† · x

With two Clements meshes and an array of tunable attenuators, any
real or complex matrix can be multiplied optically.

References:
  - Miller, Photonics Research 1(1), 1-11 (2013)
  - Clements et al., Optica 3(12), 1460 (2016)
  - COMSOL article: SVD-based general matrix-vector multiplier
"""

import numpy as np
from typing import Tuple
from .clements_mesh import ClementsMesh


def svd_decompose(M: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute SVD: M = U · Σ · V†

    Args:
        M: N×M complex or real matrix

    Returns:
        (U, S, Vh) — U is N×N unitary, S is min(N,M) singular values,
        Vh is M×M unitary (V†, conjugate transpose of V)
    """
    U, S, Vh = np.linalg.svd(M, full_matrices=True)
    return U, S, Vh


class SVDEngine:
    """Full SVD-based optical matrix multiplier.

    Architecture:
        Input x (M-dim) → ClementsMesh V† → Attenuators Σ → ClementsMesh U → Output y (N-dim)

    For complex matrices, the diagonal Σ matrix elements are generally complex:
        Σ = diag(σ_1, σ_2, ..., σ_k)
    where σ_k are the singular values (real, non-negative for standard SVD).

    If M is complex, we need an additional diagonal phase correction:
        M = U · Σ_real · D_phase · V†
    which requires an extra phase shifter array after Σ.
    """

    def __init__(self, N: int, M: int | None = None):
        """
        Args:
            N: number of output modes (rows of matrix)
            M: number of input modes (columns of matrix), defaults to N
        """
        self.N = N
        self.M = M if M is not None else N
        self.K = min(N, self.M)

        # Two Clements meshes
        self.mesh_U = ClementsMesh(N)    # U transformation (output side)
        self.mesh_Vh = ClementsMesh(self.M)  # V† transformation (input side)

        # Diagonal scaling factors (σ_k / σ_max, normalized to [0, 1])
        self.singular_values: np.ndarray = np.ones(self.K)
        self.sigma_max: float = 1.0

        # Target matrix
        self._M_target: np.ndarray | None = None

    def program_matrix(self, M_target: np.ndarray, max_attenuation_dB: float = 30.0) -> None:
        """Program the SVD engine to implement a target matrix M.

        The singular values are scaled so that the maximum is 1 (0 dB
        attenuation) and values below the noise floor are truncated.

        Args:
            M_target: N×M complex or real matrix
            max_attenuation_dB: maximum allowed attenuation before truncation
        """
        M = np.asarray(M_target, dtype=complex)
        if M.shape != (self.N, self.M):
            raise ValueError(f"Expected {self.N}×{self.M} matrix, got {M.shape}")

        self._M_target = M

        # SVD decomposition
        U, S, Vh = svd_decompose(M)
        # U is N×N, S has length K, Vh is M×M

        self.sigma_max = float(S[0]) if S[0] > 0 else 1.0

        # Normalize singular values
        self.singular_values = S / self.sigma_max

        # Truncate singular values below noise floor
        noise_floor = 10 ** (-max_attenuation_dB / 20.0)
        self.singular_values[self.singular_values < noise_floor] = 0.0

        # Program the U mesh
        self.mesh_U.program_unitary(U)

        # Program the V† mesh (Vh = V†)
        self.mesh_Vh.program_unitary(Vh)

    def forward(self, x: np.ndarray, global_gain: float = 1.0) -> np.ndarray:
        """Apply the optical SVD engine to an input vector.

        y = gain · U · Σ · V† · x

        Args:
            x: input vector of shape (M,)
            global_gain: overall amplitude scaling (e.g., to compensate
                        for the singular value normalization)

        Returns:
            Output vector of shape (N,)
        """
        x = np.asarray(x, dtype=complex)

        # Step 1: Apply V† (input mesh)
        z = self.mesh_Vh.forward(x)  # shape (M,)

        # Step 2: Apply Σ (diagonal scaling)
        z_scaled = np.zeros(self.N, dtype=complex)
        for k in range(self.K):
            z_scaled[k] = z[k] * self.singular_values[k]
        # Remaining dimensions are zero-padded or truncated

        # Step 3: Apply U (output mesh)
        y = self.mesh_U.forward(z_scaled)  # shape (N,)

        return y * global_gain * self.sigma_max

    @property
    def effective_matrix(self) -> np.ndarray:
        """Compute the effective matrix implemented by the current programming.

        This should closely match M_target (up to the max_attenuation_dB
        truncation and numerical precision).
        """
        M_eff = np.zeros((self.N, self.M), dtype=complex)
        eye = np.eye(self.M, dtype=complex)
        for j in range(self.M):
            M_eff[:, j] = self.forward(eye[j], global_gain=1.0)
        return M_eff

    @property
    def reconstruction_error(self) -> float:
        """Relative Frobenius error between target and effective matrix."""
        if self._M_target is None:
            return 0.0
        M_eff = self.effective_matrix
        return float(np.linalg.norm(M_eff - self._M_target) /
                     max(np.linalg.norm(self._M_target), 1e-15))

    def __repr__(self) -> str:
        return (f"SVDEngine(N={self.N}, M={self.M}, "
                f"K={self.K}, "
                f"σ_max={self.sigma_max:.3f}, "
                f"σ_eff_range=[{self.singular_values.min():.4f}, "
                f"{self.singular_values.max():.4f}])")
