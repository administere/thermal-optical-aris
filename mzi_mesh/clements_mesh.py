"""
Clements Mesh — N×N Unitary Matrix Synthesis
=============================================

Implements the Clements et al. (Optica 2016) decomposition using the
standard MZI convention:

    T(θ, φ) = [[cos(θ),           -e^{-iφ}·sin(θ)],
               [e^{iφ}·sin(θ),     cos(θ)         ]]

The mesh uses N(N-1)/2 MZIs arranged in a rectangular N×(N-1) grid.

Decomposition algorithm:
  1. Work from rightmost column to leftmost
  2. For each MZI position, nullify one off-diagonal element of U
  3. The nullification condition T†[0,:]·[a,b]^T = 0 gives (θ, φ)
  4. Diagonal phase correction at output ports

References:
  - Clements, Humphreys, Metcalf, Kolthammer, Walmsley.
    "Optimal design for universal multiport interferometers."
    Optica 3(12), 1460-1465 (2016).
"""

import numpy as np
from typing import List, Tuple
from .mzi import mzi_transfer_matrix


def _embed_2x2(U_2x2: np.ndarray, N: int, mode_i: int, mode_j: int) -> np.ndarray:
    """Embed a 2×2 matrix into an N×N identity at modes (i, j)."""
    T = np.eye(N, dtype=complex)
    idx = sorted([mode_i, mode_j])
    T[idx[0], idx[0]] = U_2x2[0, 0]
    T[idx[0], idx[1]] = U_2x2[0, 1]
    T[idx[1], idx[0]] = U_2x2[1, 0]
    T[idx[1], idx[1]] = U_2x2[1, 1]
    return T


def _nullify_params(a: complex, b: complex) -> Tuple[float, float]:
    """Compute (θ, φ) to nullify element 'a' using pivot 'b'.

    We want T(θ, φ)† · [a, b]^T = [0, b']^T.

    T† = [[cos(θ),             e^{-iφ}·sin(θ) ],
          [-e^{iφ}·sin(θ),     cos(θ)           ]]

    T†[0,:] · [a,b]^T = cos(θ)·a + e^{-iφ}·sin(θ)·b = 0

    Let a = |a|·e^{iα}, b = |b|·e^{iβ}:
        e^{-iφ} = -a/(b·tan(θ))
    With tan(θ) = |a|/|b| (θ ∈ [0, π/2]):
        e^{-iφ} = -e^{i(α-β)}
        → φ = β - α - π  (mod 2π)

    Args:
        a: element to nullify (complex)
        b: pivot element (complex)

    Returns:
        (theta, phi) in radians
    """
    if abs(b) < 1e-15:
        return 0.0, 0.0

    theta = np.arctan2(abs(a), abs(b))
    phi = (np.angle(b) - np.angle(a) - np.pi) % (2 * np.pi)

    return theta, phi


def clements_decompose(U_target: np.ndarray) -> Tuple[List[Tuple[int, int, float, float]], np.ndarray]:
    """Decompose an N×N unitary into MZI sequence + diagonal correction.

    Uses the Reck et al. (1994) ordering: nullify upper off-diagonal
    elements working from right column to left, top to bottom within
    each column.

    For each column i (N-1 down to 1):
        For each row j (i-1 down to 0):
            Nullify U[j, i] using MZI on modes (j, j+1)

    The pivot is always U[j+1, i] — since we process from top to bottom
    (j decreasing), the pivot hasn't been nullified yet.

    Returns:
        (mzi_list, D_diag) — MZI list in decomposition order,
        and diagonal correction D such that U = (Π T) · D
    """
    U = np.asarray(U_target, dtype=complex).copy()
    N = U.shape[0]

    if U.shape != (N, N):
        raise ValueError(f"Expected square matrix, got {U.shape}")

    if not np.allclose(U @ U.conj().T, np.eye(N), atol=1e-8):
        raise ValueError("Matrix is not unitary")

    mzi_list: List[Tuple[int, int, float, float]] = []

    # Nullify upper triangular part: for each column i, nullify rows above
    # Process top-to-bottom (j ascending) so each pivot is preserved
    for i in range(N - 1, 0, -1):          # column (right to left)
        for j in range(0, i):               # row (top to bottom)
            a = U[j, i]      # to nullify
            b = U[j + 1, i]  # pivot (one row below, not yet nullified)

            if abs(a) < 1e-14:
                mzi_list.append((j, j + 1, 0.0, 0.0))
                continue

            theta, phi = _nullify_params(a, b)
            T = mzi_transfer_matrix(theta, phi)
            T_dag = T.conj().T

            # Apply T† to rows (j, j+1)
            idx = [j, j + 1]
            block = U[np.ix_(idx, range(N))]
            U[np.ix_(idx, range(N))] = T_dag @ block

            mzi_list.append((j, j + 1, theta, phi))

    D_diag = np.diag(U).copy()
    return mzi_list, D_diag


def clements_synthesize(mzi_list: List[Tuple[int, int, float, float]],
                         N: int,
                         D_diag: np.ndarray | None = None) -> np.ndarray:
    """Synthesize N×N unitary from MZI sequence + diagonal correction.

    Decomposition yields: D = Tₖ† · ... · T₁† · U_target
    → U_target = T₁ · T₂ · ... · Tₖ · D

    Since the MZIs don't commute, the multiplication order matters.
    Apply MZIs in REVERSE order with left multiplication:
        U = T₁ · (T₂ · (... · (Tₖ · D)...))

    Args:
        mzi_list: MZI sequence in decomposition order (T₁, T₂, ..., Tₖ)
        N: matrix dimension
        D_diag: diagonal phase correction (or None)

    Returns:
        N×N complex unitary matrix
    """
    # Start with D
    U = np.diag(D_diag) if D_diag is not None else np.eye(N, dtype=complex)

    # Apply T₁, T₂, ..., Tₖ from left, but in REVERSE order
    # (rightmost operation applied first)
    for mode_i, mode_j, theta, phi in reversed(mzi_list):
        T = mzi_transfer_matrix(theta, phi)
        T_full = _embed_2x2(T, N, mode_i, mode_j)
        U = T_full @ U

    return U


def clements_mesh_forward(x: np.ndarray,
                           mzi_list: List[Tuple[int, int, float, float]],
                           N: int,
                           D_diag: np.ndarray | None = None) -> np.ndarray:
    """Apply Clements mesh to input vector."""
    return clements_synthesize(mzi_list, N, D_diag) @ np.asarray(x)


class ClementsMesh:
    """Programmable N×N unitary mesh using Clements topology.

    Uses the standard rectangular mesh with N(N-1)/2 MZIs.
    Stores MZI (θ, φ) parameters and an output diagonal phase correction D.
    """

    def __init__(self, N: int):
        self.N = N
        self.num_mzis = N * (N - 1) // 2
        self._mzi_list: List[Tuple[int, int, float, float]] = []
        self._D_diag: np.ndarray = np.ones(N, dtype=complex)

        # Generate topology (which modes each MZI acts on, input-to-output)
        self._topology = self._generate_topology()

        # Initialize to identity
        self.program_unitary(np.eye(N, dtype=complex))

    def _generate_topology(self) -> List[Tuple[int, int]]:
        """Generate the standard Clements rectangular mesh topology.

        Returns MZI positions in input-to-output order.
        For N=4: (0,1), (2,3), (1,2), (0,1), (2,3), (1,2)
        """
        N = self.N
        # Build the topology from the decomposition order
        # Columns are processed right-to-left in decomposition,
        # so input-to-output order is the reverse of that.
        topo_decomp = []
        for col in range(N - 1, 0, -1):
            for diag in range(N - 1, N - col - 1, -1):
                topo_decomp.append((diag - 1, diag))

        # Reverse for input-to-output
        return list(reversed(topo_decomp))

    def program_unitary(self, U_target: np.ndarray) -> None:
        """Program the mesh to implement a target unitary.

        Uses Reck-style decomposition: nullifies upper off-diagonals
        column by column, right to left.

        Args:
            U_target: N×N complex unitary matrix
        """
        U = np.asarray(U_target, dtype=complex)
        if U.shape != (self.N, self.N):
            raise ValueError(f"Expected {self.N}×{self.N} matrix, got {U.shape}")

        N = self.N
        U_work = U.copy()
        mzi_decomp: List[Tuple[int, int, float, float]] = []

        for i in range(N - 1, 0, -1):       # column
            for j in range(0, i):             # row (top to bottom)
                a = U_work[j, i]
                b = U_work[j + 1, i]

                if abs(a) < 1e-14:
                    mzi_decomp.append((j, j + 1, 0.0, 0.0))
                else:
                    theta, phi = _nullify_params(a, b)
                    mzi_decomp.append((j, j + 1, theta, phi))

                    T = mzi_transfer_matrix(theta, phi)
                    T_dag = T.conj().T
                    idx = [j, j + 1]
                    block = U_work[np.ix_(idx, range(N))]
                    U_work[np.ix_(idx, range(N))] = T_dag @ block

        self._D_diag = np.diag(U_work).copy()
        self._mzi_list = mzi_decomp  # forward order = decomposition order
        self._topology = [(j, j + 1) for j, _, _, _ in self._mzi_list]

    @property
    def transfer_matrix(self) -> np.ndarray:
        """Current N×N unitary transfer matrix."""
        return clements_synthesize(self._mzi_list, self.N, self._D_diag)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Apply the mesh to input vector x."""
        return self.transfer_matrix @ np.asarray(x)

    def get_mzi_params(self) -> np.ndarray:
        """Get all (θ, φ) parameters as (num_mzis, 2) array."""
        return np.array([(theta, phi) for _, _, theta, phi in self._mzi_list])

    def set_mzi_phases(self, thetas: np.ndarray, phis: np.ndarray) -> None:
        """Set all MZI phases."""
        assert len(thetas) == len(phis) == self.num_mzis
        new_list = []
        for (mi, mj, _, _), theta, phi in zip(self._mzi_list, thetas, phis):
            new_list.append((mi, mj, theta, phi))
        self._mzi_list = new_list

    def __repr__(self) -> str:
        return f"ClementsMesh(N={self.N}, MZIs={self.num_mzis})"
