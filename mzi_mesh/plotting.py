"""
Visualization Functions for MZI Mesh Thermal-Optical Simulation
================================================================

Follows the style patterns established in generate_figures.py.
All figures are publication-quality with bilingual CJK support.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import Dict, List, Optional, Tuple

# ============================================================
# Style — matches generate_figures.py
# ============================================================
COLORS = {
    'primary': '#2563eb',
    'secondary': '#7c3aed',
    'tertiary': '#059669',
    'warn': '#d97706',
    'danger': '#dc2626',
    'h100': '#9ca3af',
    'grey': '#6b7280',
}

plt.rcParams.update({
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'legend.fontsize': 8,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'figure.facecolor': 'white',
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'WenQuanYi Micro Hei',
                         'Bitstream Vera Sans', 'Arial', 'sans-serif'],
    'axes.unicode_minus': False,
})


# ============================================================
# Figure 1: Single MZI Phase Sweep
# ============================================================
def fig_mzi_phase_sweep(out_path: str,
                         theta_range: Tuple[float, float] = (0, 2*np.pi),
                         n_points: int = 200):
    """MZI output power vs internal phase θ, showing sin²/cos² splitting."""
    from .mzi import mzi_transfer_matrix

    thetas = np.linspace(theta_range[0], theta_range[1], n_points)

    # Fix φ = 0 for the sweep
    P_out1 = np.zeros(n_points)
    P_out2 = np.zeros(n_points)

    x_in = np.array([1.0, 0.0])  # Light into port 1

    for i, theta in enumerate(thetas):
        U = mzi_transfer_matrix(theta, 0.0)
        y = U @ x_in
        P_out1[i] = abs(y[0])**2
        P_out2[i] = abs(y[1])**2

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # Power vs θ
    theta_deg = np.degrees(thetas)
    ax1.plot(theta_deg, P_out1, color=COLORS['primary'], linewidth=1.5,
             label='Output 1 (Bar)')
    ax1.plot(theta_deg, P_out2, color=COLORS['secondary'], linewidth=1.5,
             label='Output 2 (Cross)')
    ax1.plot(theta_deg, P_out1 + P_out2, 'k--', linewidth=0.8,
             alpha=0.4, label='Total (loss check)')
    ax1.set_xlabel('Internal Phase θ (degrees)')
    ax1.set_ylabel('Normalized Output Power')
    ax1.set_title('MZI Power Splitting Characteristic')
    ax1.legend(fontsize=7)
    ax1.set_ylim(-0.05, 1.15)

    # Annotate
    ax1.axvline(x=90, color=COLORS['grey'], linestyle=':', alpha=0.5)
    ax1.text(92, 0.95, 'θ=90°\n50:50 split', fontsize=7, color=COLORS['grey'])

    # Complex transfer function at θ sweep
    U_matrices = np.array([mzi_transfer_matrix(t, 0).flatten()
                           for t in thetas])
    ax2.plot(U_matrices[:, 0].real, U_matrices[:, 0].imag,
             color=COLORS['primary'], linewidth=1, alpha=0.7, label='u₁₁')
    ax2.plot(U_matrices[:, 1].real, U_matrices[:, 1].imag,
             color=COLORS['secondary'], linewidth=1, alpha=0.7, label='u₁₂')

    ax2.set_xlabel('Re(U)')
    ax2.set_ylabel('Im(U)')
    ax2.set_title('Complex Transfer Function (φ=0)')
    ax2.legend(fontsize=7)
    ax2.set_aspect('equal')

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f'  ✅ {out_path}')


# ============================================================
# Figure 2: Phase Shifter Characterization
# ============================================================
def fig_phase_shifter(out_path: str, V_max: float = 10.0, n_points: int = 100):
    """Phase shift vs voltage / power for a thermo-optic phase shifter."""
    from .phase_shifter import PhaseShifter
    from .params import HeaterParams, WaveguideParams

    ps = PhaseShifter(HeaterParams(), WaveguideParams())
    P_pi = ps.P_pi

    voltages = np.linspace(0, V_max, n_points)
    phases = np.zeros(n_points)
    powers = np.zeros(n_points)
    delta_Ts = np.zeros(n_points)

    for i, V in enumerate(voltages):
        ps.set_voltage(V)
        phases[i] = ps.phase - ps.phase_offset  # exclude passive offset
        powers[i] = ps.power_W * 1000  # mW
        delta_Ts[i] = ps.delta_T

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))

    # φ vs V
    ax = axes[0]
    ax.plot(voltages, np.degrees(phases), color=COLORS['primary'],
            linewidth=1.5)
    # Fit V² curve
    ax.plot(voltages, np.degrees(phases[-1] * (voltages/V_max)**2),
            '--', color=COLORS['grey'], linewidth=1, alpha=0.6,
            label='∝ V² (ideal)')
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('Phase Shift (degrees)')
    ax.set_title('φ vs V')
    ax.legend(fontsize=7)
    ax.axhline(y=180, color=COLORS['danger'], linestyle=':', alpha=0.5)
    ax.text(V_max*0.55, 185, 'π rad', fontsize=7, color=COLORS['danger'])

    # φ vs P
    ax = axes[1]
    ax.plot(powers, np.degrees(phases), color=COLORS['secondary'],
            linewidth=1.5)
    ax.set_xlabel('Electrical Power (mW)')
    ax.set_ylabel('Phase Shift (degrees)')
    ax.set_title('φ vs P (linear)')
    ax.axhline(y=180, color=COLORS['danger'], linestyle=':', alpha=0.5)
    ax.axvline(x=P_pi*1000, color=COLORS['tertiary'], linestyle='--', alpha=0.5)
    ax.text(P_pi*1000 + 0.5, 10, f'Pπ = {P_pi*1000:.1f} mW',
            fontsize=8, color=COLORS['tertiary'])

    # ΔT vs P
    ax = axes[2]
    ax.plot(powers, delta_Ts, color=COLORS['warn'], linewidth=1.5)
    ax.set_xlabel('Electrical Power (mW)')
    ax.set_ylabel('Temperature Rise ΔT (K)')
    ax.set_title('ΔT vs P')
    ax.axhline(y=delta_Ts[-1], color=COLORS['grey'], linestyle=':',
               alpha=0.4)
    ax.text(powers[-1]*0.3, delta_Ts[-1] + 1,
            f'ΔT({V_max}V) = {delta_Ts[-1]:.0f} K',
            fontsize=7, color=COLORS['grey'])

    fig.suptitle(f'Thermo-Optic Phase Shifter: Pπ = {P_pi*1000:.1f} mW',
                 fontweight='bold')
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f'  ✅ {out_path}')


# ============================================================
# Figure 3: 2D Thermal Map
# ============================================================
def fig_thermal_map(out_path: str):
    """2D temperature field from finite-difference solver."""
    from .thermal_2d import ThermalCrosstalkSolver

    solver = ThermalCrosstalkSolver.for_n_heaters(
        n=5, pitch_um=100, domain_depth_um=200, dx=0.5, dz=1.0)

    # Heat only the center heater
    powers = [0, 0, 5, 0, 0]  # mW
    T_field = solver.solve_temperature(powers)

    x_nodes = solver.grid.x_nodes
    z_nodes = solver.grid.z_nodes

    fig, ax = plt.subplots(figsize=(9, 4))

    # Temperature colormap
    T_plot = T_field - 300  # ΔT, not absolute T
    vmax = np.percentile(T_plot, 99)

    im = ax.pcolormesh(x_nodes, z_nodes, T_plot,
                       cmap='inferno', shading='auto',
                       vmin=0, vmax=vmax)

    cbar = fig.colorbar(im, ax=ax, label='ΔT (K)')
    cbar.ax.tick_params(labelsize=7)

    # Mark heater positions
    for i, x in enumerate(solver.x_positions()):
        color = 'cyan' if powers[i] > 0 else 'white'
        ax.plot(x, 0.05, 'v', color=color, markersize=8, markeredgecolor='black',
                markeredgewidth=0.5)

    ax.set_xlabel('X (μm) — Across chip surface')
    ax.set_ylabel('Z (μm) — Depth into substrate')
    ax.set_title('2D Thermal Map: 5 Heaters, Center @ 5 mW')

    # Annotate
    ax.text(0.02, 0.95, 'ΔT(x) shows thermal\ncrosstalk decay length',
            transform=ax.transAxes, fontsize=8, va='top',
            color='white', fontstyle='italic')

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f'  ✅ {out_path}')


# ============================================================
# Figure 4: Thermal Crosstalk vs Spacing
# ============================================================
def fig_crosstalk_vs_spacing(out_path: str):
    """Crosstalk coefficient vs MZI spacing — Bessel K₀ decay."""
    from .thermal_2d import ThermalCrosstalkSolver

    spacings = np.array([25, 50, 75, 100, 125, 150, 200, 250])
    alpha_values = []
    delta_T_self = []
    delta_T_cross = []

    for pitch in spacings:
        solver = ThermalCrosstalkSolver.for_n_heaters(
            n=3, pitch_um=pitch, dx=0.5, dz=1.0)

        # Heat only the center heater
        powers = [0, 5, 0]  # mW
        T_field = solver.solve_temperature(powers)

        T_self = solver.grid.get_heater_temperature(1, T_field) - 300
        T_cross = solver.grid.get_heater_temperature(0, T_field) - 300

        delta_T_self.append(T_self)
        delta_T_cross.append(T_cross)
        alpha_values.append(T_cross / T_self if T_self > 0 else 0)

    delta_T_self = np.array(delta_T_self)
    delta_T_cross = np.array(delta_T_cross)
    alpha_values = np.array(alpha_values)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # Absolute crosstalk
    ax1.semilogy(spacings, delta_T_cross, 'o-', color=COLORS['danger'],
                 linewidth=1.5, markersize=5, label='ΔT_cross')
    ax1.axhline(y=delta_T_self[0], color=COLORS['primary'], linestyle='--',
                linewidth=1, label=f'ΔT_self ≈ {delta_T_self[0]:.1f} K')
    ax1.set_xlabel('Heater Spacing (μm)')
    ax1.set_ylabel('Temperature Rise ΔT (K) — log scale')
    ax1.set_title('Crosstalk ΔT vs Spacing')
    ax1.legend(fontsize=7)
    ax1.grid(True, alpha=0.3, which='both')

    # Annotate safe spacing
    ax1.axvline(x=125, color=COLORS['tertiary'], linestyle=':', alpha=0.5)
    ax1.text(126, delta_T_self[0]*0.3, 'Safe spacing\n~125 μm',
             fontsize=7, color=COLORS['tertiary'])

    # Relative crosstalk coefficient
    ax2.plot(spacings, alpha_values * 100, 's-', color=COLORS['secondary'],
             linewidth=1.5, markersize=5)
    ax2.set_xlabel('Heater Spacing (μm)')
    ax2.set_ylabel('Crosstalk Coefficient α = Cᵢⱼ/Cⱼⱼ (%)')
    ax2.set_title('Relative Crosstalk Coefficient')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3, which='both')

    # 1% threshold
    ax2.axhline(y=1, color=COLORS['warn'], linestyle=':', alpha=0.5)
    ax2.text(spacings[-1]*0.7, 1.2, '1% crosstalk', fontsize=7,
             color=COLORS['warn'])

    fig.suptitle('Thermal Crosstalk: 2D Finite-Difference Solution',
                 fontweight='bold')
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f'  ✅ {out_path}')


# ============================================================
# Figure 5: Matrix Fidelity vs Crosstalk
# ============================================================
def fig_fidelity_vs_spacing(out_path: str, n_trials: int = 5):
    """The KEY result: matrix fidelity vs. MZI spacing."""
    from .fidelity import fidelity_vs_spacing

    spacings = [25, 50, 75, 100, 125, 150, 200, 250]
    print('  Computing fidelity vs spacing (this may take a moment)...')
    results = fidelity_vs_spacing(spacings, N=4, num_trials=n_trials)

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    # (1) Amplitude fidelity vs spacing
    ax = axes[0, 0]
    means = np.array(results['amplitude_fidelity_mean'])
    stds = np.array(results['amplitude_fidelity_std'])
    ax.errorbar(spacings, means, yerr=stds, 'o-', color=COLORS['primary'],
                linewidth=1.5, markersize=5, capsize=3)
    ax.set_xlabel('MZI Spacing (μm)')
    ax.set_ylabel('Amplitude Fidelity ℱₐ')
    ax.set_title('Matrix Fidelity vs MZI Spacing')
    ax.axhline(y=0.99, color=COLORS['tertiary'], linestyle='--', alpha=0.5)
    ax.text(spacings[-1]*0.7, 0.985, 'ℱₐ = 0.99', fontsize=7,
            color=COLORS['tertiary'])
    ax.set_ylim(0.9, 1.01)

    # (2) Frobenius error vs spacing
    ax = axes[0, 1]
    frob_means = np.array(results['frobenius_error_mean'])
    ax.semilogy(spacings, frob_means, 's-', color=COLORS['secondary'],
                linewidth=1.5, markersize=5)
    ax.set_xlabel('MZI Spacing (μm)')
    ax.set_ylabel('Frobenius Error (log scale)')
    ax.set_title('Matrix Error vs Spacing')
    ax.grid(True, alpha=0.3, which='both')

    # (3) Effective bits vs spacing
    ax = axes[1, 0]
    bits_means = np.array(results['effective_bits_mean'])
    ax.plot(spacings, bits_means, 'D-', color=COLORS['warn'],
            linewidth=1.5, markersize=5)
    ax.set_xlabel('MZI Spacing (μm)')
    ax.set_ylabel('Effective Bit Precision')
    ax.set_title('Crosstalk-Limited Precision')
    ax.axhline(y=8, color=COLORS['grey'], linestyle='--', alpha=0.5)
    ax.text(spacings[-1]*0.6, 8.2, '8-bit target', fontsize=7,
            color=COLORS['grey'])

    # (4) Summary bar chart
    ax = axes[1, 1]
    # Phase error at each spacing
    phase_errs = []
    for raw in results['raw_results']:
        if raw['fidelities']:
            phase_errs.append(np.arccos(np.clip(np.mean(raw['fidelities']), -1, 1)))
        else:
            phase_errs.append(np.pi)

    colors_bar = [COLORS['danger'] if p > 0.3 else
                  COLORS['warn'] if p > 0.1 else
                  COLORS['tertiary'] for p in phase_errs]

    bars = ax.bar(range(len(spacings)), np.degrees(phase_errs),
                  color=colors_bar, edgecolor='white')
    ax.set_xticks(range(len(spacings)))
    ax.set_xticklabels([str(s) for s in spacings])
    ax.set_xlabel('MZI Spacing (μm)')
    ax.set_ylabel('Phase Error RMS (degrees)')
    ax.set_title('Phase Error per Spacing')

    # Value labels
    for bar, val in zip(bars, np.degrees(phase_errs)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}°', ha='center', fontsize=7, fontweight='bold')

    fig.suptitle('Thermal Crosstalk Impact on Matrix Fidelity (N=4 Clements Mesh)',
                 fontweight='bold')
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f'  ✅ {out_path}')


# ============================================================
# Figure 6: SVD Reconstruction Example
# ============================================================
def fig_svd_example(out_path: str, N: int = 4, M_dim: int = 4):
    """SVD-based matrix reconstruction: target vs. achieved vs. error."""
    from .svd_engine import SVDEngine

    # Generate random matrix
    M_target = np.random.randn(N, M_dim) + 1j * np.random.randn(N, M_dim) * 0.3

    engine = SVDEngine(N, M_dim)
    engine.program_matrix(M_target)
    M_achieved = engine.effective_matrix
    M_error = np.abs(M_achieved - M_target)

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))

    vmax = max(np.abs(M_target).max(), np.abs(M_achieved).max())

    # Target
    im0 = axes[0].imshow(np.abs(M_target), cmap='Blues', aspect='auto',
                         vmin=0, vmax=vmax)
    axes[0].set_title('Target |M|')
    for i in range(N):
        for j in range(M_dim):
            axes[0].text(j, i, f'{M_target[i,j]:.2f}',
                        ha='center', va='center', fontsize=6,
                        color='black' if np.abs(M_target[i,j]) < vmax/2 else 'white')

    # Achieved
    im1 = axes[1].imshow(np.abs(M_achieved), cmap='Blues', aspect='auto',
                         vmin=0, vmax=vmax)
    axes[1].set_title('Achieved |M|')
    for i in range(N):
        for j in range(M_dim):
            axes[1].text(j, i, f'{M_achieved[i,j]:.2f}',
                        ha='center', va='center', fontsize=6,
                        color='black' if np.abs(M_achieved[i,j]) < vmax/2 else 'white')

    # Error
    im2 = axes[2].imshow(M_error, cmap='Reds', aspect='auto')
    axes[2].set_title(f'|Error| (max={M_error.max():.2e})')
    plt.colorbar(im2, ax=axes[2], shrink=0.8)

    fig.suptitle(f'SVD Optical Matrix Multiplication: {N}×{M_dim} → Reconstruction',
                 fontweight='bold')
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f'  ✅ {out_path}')


# ============================================================
# Figure 7: Clements Mesh Topology Diagram
# ============================================================
def fig_clements_mesh(out_path: str, N: int = 4):
    """Schematic of Clements mesh topology."""
    from .clements_mesh import ClementsMesh

    mesh = ClementsMesh(N)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_xlim(-0.5, N + 0.5)
    ax.set_ylim(-1, N)
    ax.axis('off')

    # Draw waveguides (horizontal lines)
    for i in range(N):
        ax.axhline(y=i, xmin=0.1, xmax=0.9, color=COLORS['grey'],
                   linewidth=2, alpha=0.5)
        ax.text(-0.3, i, f'In {i+1}', fontsize=8, ha='right', va='center',
                fontweight='bold', color=COLORS['primary'])
        ax.text(N + 0.3, i, f'Out {i+1}', fontsize=8, ha='left', va='center',
                fontweight='bold', color=COLORS['secondary'])

    # Draw MZI positions
    for mzi_idx, (mode_i, mode_j) in enumerate(mesh._topology):
        # Determine column
        col = 0
        for c in range(N - 1):
            topo_col = mesh._generate_topology()[
                sum((N - 1 - i % 2) // 2 for i in range(c)):
                sum((N - 1 - i % 2) // 2 for i in range(c + 1))
            ]
            if (mode_i, mode_j) in mesh._topology[c*((N+1)//2):(c+1)*((N+1)//2)]:
                col = c // 2 + (0 if c % 2 == 0 else 0)
                break

        # Simpler: just map MZI index to column
        col = mzi_idx // (N // 2 + N % 2) + 0.5  # approximate

        # Draw as a rectangle connecting two adjacent waveguides
        y_center = (mode_i + mode_j) / 2
        x = 1 + mzi_idx * (N - 2) / mesh.num_mzis

        rect = mpatches.FancyBboxPatch(
            (x - 0.15, y_center - 0.3), 0.3, 0.6,
            boxstyle="round,pad=0.02",
            facecolor=COLORS['tertiary'], edgecolor='white',
            alpha=0.6,
        )
        ax.add_patch(rect)
        ax.text(x, y_center, f'M{mzi_idx+1}', fontsize=5,
                ha='center', va='center', color='white', fontweight='bold')

    ax.set_title(f'Clements Mesh Topology: N={N}, {mesh.num_mzis} MZIs',
                 fontweight='bold', fontsize=13)
    ax.text(0.5, -0.7,
            'Each rectangle = one MZI acting on adjacent waveguide modes',
            fontsize=9, ha='center', color=COLORS['grey'], fontstyle='italic')

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f'  ✅ {out_path}')
