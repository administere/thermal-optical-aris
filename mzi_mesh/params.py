"""
Physical parameters for MZI mesh thermal-optical simulation.

All parameters are traceable to literature values for standard SOI
(Silicon-on-Insulator) photonic platforms at 1550 nm C-band.

Dataclass pattern follows the existing ChipParams from comprehensive_validation.py.
"""

from dataclasses import dataclass, field
import numpy as np

# ============================================================
# Waveguide Parameters (SOI platform, 1550 nm)
# ============================================================
@dataclass
class WaveguideParams:
    """SOI strip waveguide geometry and optical properties.

    Literature sources:
      - n_si @1550nm: Palik, Handbook of Optical Constants (1985)
      - dn/dT: Komma et al., Opt. Lett. 37(9), 2012 (1.8e-4 K⁻¹)
      - Propagation loss: typical foundry value for 0.5 μm strip waveguide
    """
    width_um: float = 0.50             # Si waveguide width (μm)
    height_um: float = 0.22            # Si waveguide height (μm)
    n_si: float = 3.476                # Si refractive index @1550nm, 300K
    n_sio2: float = 1.444              # SiO2 cladding index @1550nm
    n_eff: float = 2.45                # Effective index (fundamental TE mode)
    ng: float = 4.2                    # Group index
    dn_dT: float = 1.80e-4             # Thermo-optic coefficient (K⁻¹)
    loss_dB_cm: float = 2.0            # Propagation loss (dB/cm)

    @property
    def alpha_1pcm(self) -> float:
        """Propagation loss in cm⁻¹ (intensity)."""
        return self.loss_dB_cm / (10 * np.log10(np.e))

    @property
    def loss_per_um(self) -> float:
        """Intensity transmission per μm."""
        return 10 ** (-self.loss_dB_cm / 10 * 1e-4)


# ============================================================
# Heater Parameters (Ti microheater for thermo-optic phase tuning)
# ============================================================
@dataclass
class HeaterParams:
    """Titanium microheater for thermo-optic phase shifting.

    Typical SOI platform values. The heater sits above the Si waveguide
    separated by a thin SiO2 spacer layer.

    Literature sources:
      - Ti resistivity: ~42 μΩ·cm for thin film (Harris et al., IEEE TCPMT 2015)
      - Pπ ~20 mW for standard SOI: Harris et al., Opt. Express 22(9), 2014
    """
    width_um: float = 1.80             # Heater width (μm)
    thickness_um: float = 0.10         # Heater thickness (μm)
    length_um: float = 200.0           # Heated waveguide length (μm)
    rho_Ti_uOhm_cm: float = 42.0       # Ti resistivity (μΩ·cm) — thin film
    spacer_um: float = 1.00            # SiO2 spacer thickness (μm)
    k_sio2: float = 1.38              # SiO2 thermal conductivity (W/m·K)
    k_si: float = 148.0               # Si thermal conductivity (W/m·K)
    T_amb: float = 300.0              # Ambient temperature (K)

    @property
    def resistivity_Ohm_m(self) -> float:
        return self.rho_Ti_uOhm_cm * 1e-8  # μΩ·cm → Ω·m

    @property
    def cross_section_m2(self) -> float:
        return self.width_um * self.thickness_um * 1e-12

    @property
    def volume_m3(self) -> float:
        return self.length_um * self.width_um * self.thickness_um * 1e-18

    @property
    def R_Ohm(self) -> float:
        """Electrical resistance at T_amb."""
        return self.resistivity_Ohm_m * (self.length_um * 1e-6) / self.cross_section_m2

    def R_at_T(self, T_K: float, TCR: float = 0.0038) -> float:
        """Resistance at temperature T including TCR."""
        return self.R_Ohm * (1 + TCR * (T_K - self.T_amb))


# ============================================================
# MZI Parameters
# ============================================================
@dataclass
class MZIParams:
    """Single Mach-Zehnder Interferometer parameters.

    A standard MZI consists of:
      1. 50:50 directional coupler (MMI-based)
      2. Phase shifter PS(θ) on one arm
      3. 50:50 directional coupler
      4. Phase shifter PS(φ) on one arm

    The transfer matrix is U(θ, φ) — any 2×2 unitary up to global phase.
    """
    # Coupler
    coupler_split_ratio: float = 0.50   # Target 50:50 (ideal)
    coupler_excess_loss_dB: float = 0.1 # Excess loss per coupler

    # MZI arms
    arm_length_um: float = 300.0        # Total arm length between couplers
    arm_spacing_um: float = 50.0        # Spacing between two arms
    delta_L_um: float = 0.0             # Path-length imbalance (default balanced)

    # Sub-components
    waveguide: WaveguideParams = field(default_factory=WaveguideParams)
    heater: HeaterParams = field(default_factory=HeaterParams)

    # Operating point
    wavelength_nm: float = 1550.0       # Operating wavelength

    @property
    def k0(self) -> float:
        """Free-space wavenumber (rad/μm)."""
        return 2 * np.pi / (self.wavelength_nm * 1e-3)

    @property
    def neff(self) -> float:
        return self.waveguide.n_eff

    @property
    def beta(self) -> float:
        """Propagation constant (rad/μm)."""
        return self.k0 * self.neff

    @property
    def phase_arm(self) -> float:
        """Passive phase accumulated in each MZI arm."""
        return self.beta * self.arm_length_um


# ============================================================
# Clements Mesh Parameters
# ============================================================
@dataclass
class MeshParams:
    """Clements mesh topology and platform parameters.

    The Clements mesh (Clements et al., Optica 3(12), 2016) arranges
    N(N-1)/2 MZIs in a rectangular grid pattern. Each MZI implements a
    2×2 unitary, and the overall mesh synthesizes an arbitrary N×N unitary.

    Thermal crosstalk between adjacent MZIs is the dominant fidelity
    limitation in scaled meshes.
    """
    N: int = 4                          # Matrix dimension
    mzi_pitch_um: float = 127.0         # Center-to-center MZI spacing (μm)
    substrate_thickness_um: float = 200.0  # Si handle wafer thickness (μm)
    T_ambient: float = 300.0            # Ambient (chuck) temperature (K)
    T_max: float = 450.0               # Maximum safe operating temperature (K)

    # Sub-component defaults for all MZIs in the mesh
    mzi: MZIParams = field(default_factory=MZIParams)

    @property
    def num_mzis(self) -> int:
        """Number of MZIs in the Clements mesh."""
        return self.N * (self.N - 1) // 2

    @property
    def num_phase_shifters(self) -> int:
        """Total number of independent phase shifters (2 per MZI)."""
        return self.num_mzis * 2

    @property
    def mesh_footprint_mm2(self) -> float:
        """Estimated chip area for the MZI mesh (mm²)."""
        # Each MZI takes roughly arm_length × arm_spacing
        mzi_area = (self.mzi.arm_length_um * self.mzi.arm_spacing_um) * 1e-6
        return mzi_area * self.num_mzis * 1.5  # 50% routing overhead

    @property
    def total_power_mW(self) -> float:
        """Estimated total electrical power for phase tuning (mW)."""
        # Each phase shifter draws ~Pπ/2 on average for random unitary
        from .phase_shifter import p_pi
        Ppi = p_pi(self.mzi.heater, self.mzi.waveguide, self.mzi.wavelength_nm)
        return Ppi * 1000 * self.num_phase_shifters * 0.5
