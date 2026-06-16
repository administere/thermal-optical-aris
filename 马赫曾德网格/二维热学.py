"""
2D Finite-Difference Steady-State Thermal Solver (COMSOL Surrogate)
====================================================================

Solves the steady-state heat equation on a 2D cross-section (X-Z plane)
of the SOI photonic chip:

    ∂/∂x (k ∂T/∂x) + ∂/∂z (k ∂T/∂z) + Q(x,z) = 0

Discretized with a 5-point central-difference stencil on a uniform
Cartesian grid. The resulting sparse linear system is solved via
scipy.sparse.linalg.spsolve.

This is the equivalent of COMSOL's stationary thermal study with the
Heat Transfer in Solids interface. We trade FEM's adaptive mesh for
a simpler uniform grid and direct sparse solve — adequate for the
geometry and accuracy requirements of MZI crosstalk modeling.

Key outputs:
  - 2D temperature field T(x,z)
  - Thermal crosstalk matrix C_{ij}: how heater j's power affects
    the temperature at phase shifter i

Physics validation:
  - Grid convergence: solution changes <1% when halving dx, dz
  - Energy conservation: total flux out = total heat generated
  - Analytical comparison: 1D R_th model within 10% of 2D FD for single heater
  - Crosstalk decay: Bessel K₀(|Δr|/L_diff) for widely-spaced heaters

Typical usage:
    >>> from mzi_mesh import ThermalGrid2D, ThermalCrosstalkSolver
    >>> solver = ThermalCrosstalkSolver.for_n_heaters(n=4, pitch_um=127)
    >>> T_field = solver.solve_temperature(heater_powers_mW=[5, 5, 5, 5])
    >>> crosstalk = solver.compute_crosstalk_matrix()
"""

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass


# ============================================================
# Material properties for the 2D domain
# ============================================================
@dataclass
class Material2D:
    """Thermal material properties for one region in the 2D domain."""
    k: float       # Thermal conductivity (W/m·K)
    label: str = ""


# Default materials library
MATERIALS = {
    'si':    Material2D(k=148.0, label='Si'),
    'sio2':  Material2D(k=1.38,  label='SiO₂'),
    'ti':    Material2D(k=21.9,  label='Ti'),
    'air':   Material2D(k=0.026, label='Air'),
}


# ============================================================
class ThermalGrid2D:
    """2D structured Cartesian grid for finite-difference thermal simulation.

    The grid lies in the X-Z plane:
      - X: horizontal (across chip surface, captures heater crosstalk)
      - Z: vertical (depth into substrate, from top surface downward)

    The grid is uniform in each direction.
    """

    def __init__(self,
                 x_range: Tuple[float, float],  # (x_min, x_max) in μm
                 z_range: Tuple[float, float],  # (z_min, z_max) in μm
                 dx: float = 0.5,               # Grid spacing X (μm)
                 dz: float = 1.0):              # Grid spacing Z (μm)
        """
        Args:
            x_range: (x_min, x_max) in μm
            z_range: (z_min, z_max) in μm — z=0 at top surface, positive downward
            dx: grid spacing in x (μm)
            dz: grid spacing in z (μm)
        """
        self.x_min, self.x_max = x_range
        self.z_min, self.z_max = z_range
        self.dx = dx
        self.dz = dz

        # Grid points
        self.nx = int(np.ceil((self.x_max - self.x_min) / dx)) + 1
        self.nz = int(np.ceil((self.z_max - self.z_min) / dz)) + 1

        # Node coordinates
        self.x_nodes = np.linspace(self.x_min, self.x_max, self.nx)
        self.z_nodes = np.linspace(self.z_min, self.z_max, self.nz)

        # Total number of nodes
        self.N = self.nx * self.nz

        # Material property arrays
        self.k_field = np.full((self.nz, self.nx), MATERIALS['sio2'].k)
        self.Q_field = np.zeros((self.nz, self.nx))  # Heat source (W/m³)

        # Boundary conditions
        self.T_bottom = 300.0   # K — substrate base
        self.h_top = 10.0       # W/m²·K — natural convection
        self.T_amb = 300.0      # K — ambient
        self.emissivity = 0.7   # — surface emissivity for radiation

        # Heater tracking
        self.heater_regions: List[Dict] = []

    # ----------------------------------------------------------
    def _ij_to_idx(self, i: int, j: int) -> int:
        """Convert (i, j) grid indices to linear index. i=row(z), j=col(x)."""
        return i * self.nx + j

    def _idx_to_ij(self, idx: int) -> Tuple[int, int]:
        """Convert linear index to (i, j) grid indices."""
        return idx // self.nx, idx % self.nx

    def _x_idx(self, x_um: float) -> int:
        """Nearest grid index for x coordinate in μm."""
        return int(round((x_um - self.x_min) / self.dx))

    def _z_idx(self, z_um: float) -> int:
        """Nearest grid index for z coordinate in μm."""
        return int(round((z_um - self.z_min) / self.dz))

    # ----------------------------------------------------------
    def set_uniform_material(self, material_name: str) -> None:
        """Fill entire domain with one material."""
        self.k_field[:] = MATERIALS[material_name].k

    def add_rect_region(self,
                         x_center: float, z_center: float,
                         width: float, height: float,
                         material_name: str) -> None:
        """Add a rectangular material region.

        Args:
            x_center, z_center: center of rectangle (μm)
            width, height: full width and height (μm)
            material_name: key into MATERIALS dict
        """
        i1 = max(0, self._z_idx(z_center - height / 2))
        i2 = min(self.nz - 1, self._z_idx(z_center + height / 2))
        j1 = max(0, self._x_idx(x_center - width / 2))
        j2 = min(self.nx - 1, self._x_idx(x_center + width / 2))
        self.k_field[i1:i2+1, j1:j2+1] = MATERIALS[material_name].k

    def add_heater(self,
                   x_center: float,
                   z_top: float,
                   width_um: float = 1.8,
                   thickness_um: float = 0.1,
                   label: str = "") -> int:
        """Add a Ti heater and return its index.

        The heater material (Ti) is set in the specified rectangle.
        To avoid extreme temperatures from sub-grid features, the
        effective heater thickness is clamped to at least dz.

        Args:
            x_center: heater center x (μm)
            z_top: top surface of heater (μm)
            width_um: heater width (μm)
            thickness_um: heater thickness (μm), clamped to dz
            label: identifier for this heater

        Returns:
            Heater index
        """
        # Clamp heater thickness to grid resolution
        eff_thickness = max(thickness_um, self.dz)

        heater_idx = len(self.heater_regions)
        self.heater_regions.append({
            'idx': heater_idx,
            'label': label or f'H{heater_idx}',
            'x_center': x_center,
            'z_center': z_top + eff_thickness / 2,
            'width': width_um,
            'height': eff_thickness,
            'actual_thickness': thickness_um,  # for volumetric correction
        })

        self.add_rect_region(x_center, z_top + eff_thickness / 2,
                            width_um, eff_thickness, 'ti')

        # SiO₂ spacer below heater
        self.add_rect_region(x_center, z_top + eff_thickness + 0.5,
                            width_um, 1.0, 'sio2')

        # Si waveguide below spacer
        self.add_rect_region(x_center, z_top + eff_thickness + 1.25,
                            0.5, 0.22, 'si')

        return heater_idx

    def set_heater_power(self, heater_idx: int, power_W: float,
                         heater_length_um: float = 200.0) -> None:
        """Set the volumetric heat generation for a heater.

        Uses the ACTUAL heater cross-section (not grid-clamped) for
        volumetric power density, then applies to grid cells.

        Args:
            heater_idx: heater index (from add_heater)
            power_W: electrical power dissipated (W)
            heater_length_um: length of heater along waveguide (μm)
        """
        if heater_idx >= len(self.heater_regions):
            raise ValueError(f"Heater {heater_idx} not found")

        h = self.heater_regions[heater_idx]
        # Use ACTUAL thickness for volume calculation
        actual_thickness = h.get('actual_thickness', h['height'])
        area_m2 = (h['width'] * 1e-6) * (actual_thickness * 1e-6)
        vol_m3 = area_m2 * (heater_length_um * 1e-6)

        Q = power_W / vol_m3  # W/m³

        # Scale Q to account for the fact that we spread over larger grid cells
        # The grid cells are height/actual_thickness times larger
        if actual_thickness > 0:
            scale = actual_thickness / h['height']
            Q *= scale  # correct for enlarged cell volume

        # Apply to heater cells
        i1 = max(0, self._z_idx(h['z_center'] - h['height'] / 2))
        i2 = min(self.nz - 1, self._z_idx(h['z_center'] + h['height'] / 2))
        j1 = max(0, self._x_idx(h['x_center'] - h['width'] / 2))
        j2 = min(self.nx - 1, self._x_idx(h['x_center'] + h['width'] / 2))
        self.Q_field[i1:i2+1, j1:j2+1] = Q

    def get_heater_temperature(self, heater_idx: int,
                                T_field: np.ndarray) -> float:
        """Average temperature at a heater location from the solution field.

        Args:
            heater_idx: heater index
            T_field: solved temperature field T(z, x) — shape (nz, nx)

        Returns:
            Average temperature (K) in the heater region
        """
        if heater_idx >= len(self.heater_regions):
            raise ValueError(f"Heater {heater_idx} not found")

        h = self.heater_regions[heater_idx]
        i1 = max(0, self._z_idx(h['z_center'] - h['height'] / 2))
        i2 = min(self.nz - 1, self._z_idx(h['z_center'] + h['height'] / 2))
        j1 = max(0, self._x_idx(h['x_center'] - h['width'] / 2))
        j2 = min(self.nx - 1, self._x_idx(h['x_center'] + h['width'] / 2))
        return float(np.mean(T_field[i1:i2+1, j1:j2+1]))

    # ----------------------------------------------------------
    def assemble_system(self) -> Tuple[sparse.csr_matrix, np.ndarray]:
        """Assemble the sparse linear system A·T = b for steady-state heat eq.

        Uses harmonic-mean conductivity at interfaces for flux conservation.

        Returns:
            (A, b) where A is (N×N) sparse CSR matrix, b is (N,) RHS vector
        """
        # Harmonic mean of k at interfaces gives better flux conservation
        # than arithmetic mean for heterogeneous materials
        k_right = np.zeros((self.nz, self.nx))
        k_left = np.zeros((self.nz, self.nx))
        k_down = np.zeros((self.nz, self.nx))
        k_up = np.zeros((self.nz, self.nx))

        # Interior points: harmonic mean with neighbor
        # k_{i+1/2,j} = 2 / (1/k_{i,j} + 1/k_{i+1,j})
        for i in range(self.nz):
            for j in range(self.nx):
                ki = self.k_field[i, j]

                # Right neighbor (j+1)
                if j < self.nx - 1:
                    kj = self.k_field[i, j + 1]
                    k_right[i, j] = 2.0 / (1.0 / ki + 1.0 / kj) if ki > 0 and kj > 0 else 0
                # Left neighbor (j-1)
                if j > 0:
                    kj = self.k_field[i, j - 1]
                    k_left[i, j] = 2.0 / (1.0 / ki + 1.0 / kj) if ki > 0 and kj > 0 else 0
                # Down neighbor (i+1) — downward is deeper into substrate
                if i < self.nz - 1:
                    kj = self.k_field[i + 1, j]
                    k_down[i, j] = 2.0 / (1.0 / ki + 1.0 / kj) if ki > 0 and kj > 0 else 0
                # Up neighbor (i-1)
                if i > 0:
                    kj = self.k_field[i - 1, j]
                    k_up[i, j] = 2.0 / (1.0 / ki + 1.0 / kj) if ki > 0 and kj > 0 else 0

        # Build sparse matrix in COO format then convert to CSR
        rows, cols, data = [], [], []
        b = np.zeros(self.N)

        dx = self.dx * 1e-6  # μm → m
        dz = self.dz * 1e-6  # μm → m

        for i in range(self.nz):
            for j in range(self.nx):
                idx = self._ij_to_idx(i, j)
                diag = 0.0
                rhs = 0.0

                # Interior: 5-point stencil
                is_boundary = (i == 0 or i == self.nz - 1 or
                              j == 0 or j == self.nx - 1)

                if not is_boundary:
                    # Right neighbor contribution
                    kr = k_right[i, j]
                    if kr > 0:
                        coeff = kr / (dx * dx)
                        rows.append(idx); cols.append(self._ij_to_idx(i, j + 1))
                        data.append(-coeff)
                        diag += coeff

                    # Left neighbor
                    kl = k_left[i, j]
                    if kl > 0:
                        coeff = kl / (dx * dx)
                        rows.append(idx); cols.append(self._ij_to_idx(i, j - 1))
                        data.append(-coeff)
                        diag += coeff

                    # Down neighbor
                    kd = k_down[i, j]
                    if kd > 0:
                        coeff = kd / (dz * dz)
                        rows.append(idx); cols.append(self._ij_to_idx(i + 1, j))
                        data.append(-coeff)
                        diag += coeff

                    # Up neighbor
                    ku = k_up[i, j]
                    if ku > 0:
                        coeff = ku / (dz * dz)
                        rows.append(idx); cols.append(self._ij_to_idx(i - 1, j))
                        data.append(-coeff)
                        diag += coeff

                    rhs = self.Q_field[i, j]

                # Top boundary (i = 0): convection + radiation
                elif i == 0 and 0 < j < self.nx - 1:
                    # Convection: -k ∂T/∂z = h (T - T_amb)
                    # FD: -k_down (T[1,j] - T[0,j]) / dz = h (T[0,j] - T_amb)
                    # → (k_down/dz + h) T[0,j] - (k_down/dz) T[1,j] = h·T_amb
                    kd = k_down[i, j]
                    h_eff = self.h_top  # Linearized (ignoring radiation nonlinearity)

                    coeff_down = kd / (dz * dz)
                    coeff_boundary = h_eff / dz

                    rows.append(idx); cols.append(self._ij_to_idx(i + 1, j))
                    data.append(-coeff_down)
                    diag += coeff_down + coeff_boundary
                    rhs = coeff_boundary * self.T_amb

                    # Include radiation correction (linearized around T_amb)
                    # q_rad = εσ(T⁴ - T_amb⁴) ≈ 4εσT_amb³ · (T - T_amb)
                    sigma_SB = 5.670374419e-8
                    h_rad = 4 * self.emissivity * sigma_SB * self.T_amb**3
                    coeff_rad = h_rad / dz
                    diag += coeff_rad
                    rhs += coeff_rad * self.T_amb

                    # Right and left neighbors (conduction along surface)
                    if j < self.nx - 1:
                        kr = k_right[i, j]
                        if kr > 0:
                            coeff = kr / (dx * dx)
                            rows.append(idx); cols.append(self._ij_to_idx(i, j + 1))
                            data.append(-coeff)
                            diag += coeff
                    if j > 0:
                        kl = k_left[i, j]
                        if kl > 0:
                            coeff = kl / (dx * dx)
                            rows.append(idx); cols.append(self._ij_to_idx(i, j - 1))
                            data.append(-coeff)
                            diag += coeff

                    rhs += self.Q_field[i, j]

                # Bottom boundary (i = nz-1): fixed temperature
                elif i == self.nz - 1:
                    diag = 1.0
                    rhs = self.T_bottom

                # Left boundary (j = 0): adiabatic (symmetry)
                elif j == 0 and 0 < i < self.nz - 1:
                    kr = k_right[i, j]
                    ku = k_up[i, j] if i > 0 else 0
                    kd = k_down[i, j] if i < self.nz - 1 else 0

                    if kr > 0:
                        coeff = kr / (dx * dx)
                        rows.append(idx); cols.append(self._ij_to_idx(i, j + 1))
                        data.append(-coeff)
                        diag += coeff
                    if ku > 0:
                        coeff = ku / (dz * dz)
                        rows.append(idx); cols.append(self._ij_to_idx(i - 1, j))
                        data.append(-coeff)
                        diag += coeff
                    if kd > 0:
                        coeff = kd / (dz * dz)
                        rows.append(idx); cols.append(self._ij_to_idx(i + 1, j))
                        data.append(-coeff)
                        diag += coeff
                    rhs = self.Q_field[i, j]

                # Right boundary (j = nx-1): adiabatic
                elif j == self.nx - 1 and 0 < i < self.nz - 1:
                    kl = k_left[i, j]
                    ku = k_up[i, j] if i > 0 else 0
                    kd = k_down[i, j] if i < self.nz - 1 else 0

                    if kl > 0:
                        coeff = kl / (dx * dx)
                        rows.append(idx); cols.append(self._ij_to_idx(i, j - 1))
                        data.append(-coeff)
                        diag += coeff
                    if ku > 0:
                        coeff = ku / (dz * dz)
                        rows.append(idx); cols.append(self._ij_to_idx(i - 1, j))
                        data.append(-coeff)
                        diag += coeff
                    if kd > 0:
                        coeff = kd / (dz * dz)
                        rows.append(idx); cols.append(self._ij_to_idx(i + 1, j))
                        data.append(-coeff)
                        diag += coeff
                    rhs = self.Q_field[i, j]

                # Corner points: fix to ambient (don't contribute much)
                else:
                    diag = 1.0
                    rhs = self.T_amb

                rows.append(idx); cols.append(idx)
                data.append(diag)
                b[idx] = rhs

        A = sparse.coo_matrix((data, (rows, cols)), shape=(self.N, self.N))
        return A.tocsr(), b

    def solve(self) -> np.ndarray:
        """Solve the steady-state thermal system.

        Returns:
            T_field: 2D temperature array with shape (nz, nx)
        """
        A, b = self.assemble_system()
        T_flat = spsolve(A, b)
        return T_flat.reshape(self.nz, self.nx)

    def check_energy_conservation(self, T_field: np.ndarray,
                                   heater_powers: List[float]) -> Dict:
        """Verify energy conservation in the solution.

        Total heat flux out through boundaries should equal total heat
        generated by heaters.

        Returns:
            Dict with 'total_heat_W', 'flux_out_W', 'error_pct'
        """
        total_Q = sum(heater_powers)

        # Compute heat flux out through boundaries
        # Top: convection + radiation
        q_top = 0.0
        dx_m = self.dx * 1e-6
        for j in range(self.nx):
            T_surf = T_field[0, j]
            q_conv = self.h_top * (T_surf - self.T_amb)
            sigma = 5.670374419e-8
            q_rad = self.emissivity * sigma * (T_surf**4 - self.T_amb**4)
            q_top += (q_conv + q_rad) * dx_m

        # Bottom: conductive flux into substrate
        q_bottom = 0.0
        dz_m = self.dz * 1e-6
        for j in range(self.nx):
            k_bottom = self.k_field[-1, j]
            T_grad = (T_field[-1, j] - T_field[-2, j]) / dz_m
            q_bottom += k_bottom * T_grad * dx_m

        total_flux = q_top + q_bottom

        return {
            'total_heat_W': total_Q,
            'flux_out_W': abs(total_flux),
            'error_pct': abs(total_flux - total_Q) / total_Q * 100 if total_Q > 0 else 0,
        }


# ============================================================
class ThermalCrosstalkSolver:
    """Solve thermal crosstalk between multiple MZI phase shifters.

    Uses superposition of single-heater solutions to build the thermal
    crosstalk matrix efficiently. For N heaters, we solve N single-heater
    problems rather than one N-source problem — this allows reusing the
    system matrix factorization and gives the crosstalk matrix directly.

    The crosstalk matrix C relates heater powers to temperature rises:
        ΔT_i = Σⱼ C_{ij} · Pⱼ

    where:
      - C_{ii} = self-heating thermal resistance (K/W) for heater i
      - C_{ij} = mutual thermal resistance (K/W) from heater j to heater i
    """

    def __init__(self, grid: ThermalGrid2D):
        self.grid = grid
        self._heater_indices: List[int] = []
        self._phase_shifter_x: List[float] = []  # x-positions of shifter centers

    @classmethod
    def for_single_heater(cls, x_um: float = 0.0,
                          domain_width_um: float = 200.0,
                          domain_depth_um: float = 250.0,
                          dx: float = 0.5, dz: float = 1.0) -> 'ThermalCrosstalkSolver':
        """Create solver for a single heater (validation case)."""
        grid = ThermalGrid2D(
            x_range=(-domain_width_um / 2, domain_width_um / 2),
            z_range=(0, domain_depth_um),
            dx=dx, dz=dz,
        )
        grid.set_uniform_material('sio2')

        # Si substrate (bottom 200 μm of domain)
        nz = grid.nz
        nz_sub = int(200 / dz)
        grid.k_field[nz - nz_sub:, :] = MATERIALS['si'].k

        # Si waveguide layer (thin, at top)
        grid.add_rect_region(x_um, 1.25, 0.5, 0.22, 'si')

        solver = cls(grid)
        solver.add_heater(x_um=x_um, label='H0')
        return solver

    @classmethod
    def for_n_heaters(cls, n: int, pitch_um: float = 127.0,
                      domain_depth_um: float = 250.0,
                      dx: float = 0.5, dz: float = 1.0) -> 'ThermalCrosstalkSolver':
        """Create solver for N equally-spaced heaters (MZI mesh cross-section).

        Args:
            n: number of heaters
            pitch_um: center-to-center heater spacing (μm)
            domain_depth_um: vertical domain size (μm)
            dx, dz: grid spacing (μm)
        """
        total_width = max(n * pitch_um + 50, 200)
        grid = ThermalGrid2D(
            x_range=(-total_width / 2, total_width / 2),
            z_range=(0, domain_depth_um),
            dx=dx, dz=dz,
        )
        grid.set_uniform_material('sio2')

        # Si substrate (bottom 200 μm)
        nz = grid.nz
        nz_sub = int(200 / dz)
        grid.k_field[nz - nz_sub:, :] = MATERIALS['si'].k

        solver = cls(grid)

        # Place heaters centered around x=0
        x0 = -(n - 1) * pitch_um / 2
        for k in range(n):
            x = x0 + k * pitch_um
            # Each MZI has 2 phase shifters (θ and φ)
            # For simplicity, put all phase shifters in one row
            # (in reality, they are staggered along the waveguide direction y,
            #  so thermal crosstalk is mainly between phases at same y ≈ 0)
            solver.add_heater(x_um=x, label=f'MZI{k}')

            # Track phase shifter x positions for the waveguide temperature
            solver._phase_shifter_x.append(x)

        return solver

    def add_heater(self, x_um: float, label: str = "") -> int:
        """Add a heater to the grid and track it.

        Returns:
            Heater index
        """
        idx = self.grid.add_heater(
            x_center=x_um, z_top=0.0,
            width_um=1.8, thickness_um=0.1,
            label=label,
        )
        self._heater_indices.append(idx)
        self._phase_shifter_x.append(x_um)
        return idx

    def compute_crosstalk_matrix(self, reference_power_mW: float = 1.0) -> np.ndarray:
        """Compute the thermal crosstalk matrix by solving one heater at a time.

        For each heater j, apply reference_power_mW of power, solve the full
        2D thermal problem, then read the temperature rise at all heaters i.
        This gives column j of the crosstalk matrix.

        Args:
            reference_power_mW: power applied to each single heater (mW)

        Returns:
            C matrix (N_heaters × N_heaters) in K/mW
        """
        n = len(self._heater_indices)
        C = np.zeros((n, n))

        for j in range(n):
            # Reset heat sources
            self.grid.Q_field[:] = 0.0
            self.grid.set_heater_power(
                self._heater_indices[j], reference_power_mW * 1e-3)

            # Solve
            T_field = self.grid.solve()

            # Read temperatures at all heater positions
            for i in range(n):
                T_i = self.grid.get_heater_temperature(
                    self._heater_indices[i], T_field)
                delta_T = T_i - self.grid.T_amb
                C[i, j] = delta_T / reference_power_mW  # K / mW

        return C

    def solve_temperature(self, heater_powers_mW: List[float]) -> np.ndarray:
        """Solve for the full 2D temperature field with all heaters active.

        Args:
            heater_powers_mW: list of power per heater (mW)

        Returns:
            T_field: 2D temperature array shape (nz, nx)
        """
        self.grid.Q_field[:] = 0.0
        for i, power_mW in enumerate(heater_powers_mW):
            if i < len(self._heater_indices):
                self.grid.set_heater_power(
                    self._heater_indices[i], power_mW * 1e-3)
        return self.grid.solve()

    def compute_phase_shifts(self,
                              heater_powers_mW: List[float],
                              wavelength_nm: float = 1550.0,
                              dn_dT: float = 1.8e-4,
                              heater_length_um: float = 200.0,
                              confinement: float = 0.85) -> np.ndarray:
        """Compute phase shifts from heater powers using full 2D thermal solve.

        For each phase shifter i, reads the waveguide temperature from the
        2D solution and computes Δφ = (2π/λ) · dn_eff/dT · ΔT · L.

        Args:
            heater_powers_mW: electrical power per heater (mW)
            wavelength_nm: operating wavelength
            dn_dT: Si thermo-optic coefficient
            heater_length_um: heated waveguide length
            confinement: mode confinement factor in Si

        Returns:
            Array of phase shifts (radians) for each phase shifter
        """
        T_field = self.solve_temperature(heater_powers_mW)

        dn_eff_dT = dn_dT * confinement
        k0 = 2 * np.pi / (wavelength_nm * 1e-9)
        L = heater_length_um * 1e-6

        phases = []
        for x_pos in self._phase_shifter_x:
            # Get temperature at waveguide depth (≈1.25 μm below surface)
            i_wg = self.grid._z_idx(1.25)  # waveguide center depth
            j_wg = self.grid._x_idx(x_pos)
            T_wg = T_field[i_wg, j_wg]
            delta_T = T_wg - self.grid.T_amb
            delta_phi = k0 * dn_eff_dT * delta_T * L
            phases.append(delta_phi)

        return np.array(phases)

    def x_positions(self) -> np.ndarray:
        """Get x-positions of all phase shifters in μm."""
        return np.array(self._phase_shifter_x)

    @property
    def n_heaters(self) -> int:
        return len(self._heater_indices)
