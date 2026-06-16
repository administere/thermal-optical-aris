#!/usr/bin/env python3
"""
Level 1 Validation: Single MZI Transfer Matrix
===============================================
Clements convention: T(θ,φ) = [[cos(θ), -e^{-iφ}sin(θ)], [e^{iφ}sin(θ), cos(θ)]]

Validates:
  1. Unitarity: T·T† = I
  2. Bar/cross/3dB states: θ=0, π/2, π/4
  3. Phase response: sin²/cos² power splitting
  4. Inverse: round-trip through mzi_params_from_unitary
  5. Phase shifter thermo-optic model: Pπ verification
  6. MZI class
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from mzi_mesh import (MZI, mzi_transfer_matrix, mzi_params_from_unitary,
                       directional_coupler, phase_shifter_matrix)
from mzi_mesh.phase_shifter import PhaseShifter, p_pi

print("=" * 68)
print("  Level 1: Single MZI — Transfer Matrix Validation")
print("  Convention: T(θ,φ) = [[cos(θ), -e^{-iφ}sin(θ)],")
print("                         [e^{iφ}sin(θ), cos(θ)]]")
print("=" * 68)

# ----------------------------------------------------------
# Test 1: Unitarity
# ----------------------------------------------------------
print("\n── Test 1: Unitarity ──")
np.random.seed(42)
errors = []
for _ in range(100):
    theta = np.random.uniform(0, np.pi/2)
    phi = np.random.uniform(0, 2*np.pi)
    T = mzi_transfer_matrix(theta, phi)
    TTdag = T @ T.conj().T
    err = np.max(np.abs(TTdag - np.eye(2)))
    errors.append(err)

print(f"  Max unitarity deviation: {max(errors):.2e}")
assert max(errors) < 1e-15
print(f"  ✅ Unitarity holds to machine precision")

# ----------------------------------------------------------
# Test 2: Bar / Cross / 3dB States
# ----------------------------------------------------------
print("\n── Test 2: Bar / Cross / 3dB States ──")
x = np.array([1.0, 0.0])

# θ=0, φ=0: bar state
T_bar = mzi_transfer_matrix(0.0, 0.0)
y = T_bar @ x
print(f"  θ=0, φ=0 (bar): P1={abs(y[0])**2:.4f}, P2={abs(y[1])**2:.4f}")
assert abs(abs(y[0])**2 - 1.0) < 1e-15
assert abs(abs(y[1])**2 - 0.0) < 1e-15

# θ=π/2, φ=0: cross state
T_cross = mzi_transfer_matrix(np.pi/2, 0.0)
y = T_cross @ x
print(f"  θ=π/2, φ=0 (cross): P1={abs(y[0])**2:.4f}, P2={abs(y[1])**2:.4f}")
assert abs(abs(y[0])**2 - 0.0) < 1e-15
assert abs(abs(y[1])**2 - 1.0) < 1e-15

# θ=π/4, φ=0: 3dB (50:50)
T_3db = mzi_transfer_matrix(np.pi/4, 0.0)
y = T_3db @ x
P1, P2 = abs(y[0])**2, abs(y[1])**2
print(f"  θ=π/4, φ=0 (3dB): P1={P1:.4f}, P2={P2:.4f}")
assert abs(P1 - 0.5) < 1e-15
assert abs(P2 - 0.5) < 1e-15
print(f"  ✅ Bar/cross/3dB states verified")

# ----------------------------------------------------------
# Test 3: Power Splitting vs θ
# ----------------------------------------------------------
print("\n── Test 3: Power Splitting P(θ) = sin²(θ) ──")
thetas = np.linspace(0, np.pi/2, 100)
max_dev = 0.0
for theta in thetas:
    T = mzi_transfer_matrix(theta, 0.0)
    y = T @ x
    P2 = abs(y[1])**2
    expected = np.sin(theta)**2
    max_dev = max(max_dev, abs(P2 - expected))

print(f"  Max deviation from sin²(θ) law: {max_dev:.2e}")
assert max_dev < 1e-15
print(f"  ✅ Power splitting follows sin²(θ)")

# ----------------------------------------------------------
# Test 4: Inverse (round-trip)
# ----------------------------------------------------------
print("\n── Test 4: Round-trip — T → (θ,φ) → T ──")
np.random.seed(123)
max_err = 0.0
for trial in range(20):
    theta_true = np.random.uniform(0, np.pi/2)
    phi_true = np.random.uniform(0, 2*np.pi)
    T = mzi_transfer_matrix(theta_true, phi_true)
    theta_rec, phi_rec = mzi_params_from_unitary(T)
    T_rec = mzi_transfer_matrix(theta_rec, phi_rec)
    err = np.max(np.abs(T_rec - T))
    max_err = max(max_err, err)
    if err > 1e-12:
        print(f"  Trial {trial}: err={err:.2e}")

print(f"  Max round-trip error: {max_err:.2e}")
assert max_err < 1e-12
print(f"  ✅ Round-trip exact")

# ----------------------------------------------------------
# Test 5: Phase Shifter Thermo-Optic Model
# ----------------------------------------------------------
print("\n── Test 5: Phase Shifter (Thermo-Optic Model) ──")
ps = PhaseShifter()
P_pi = ps.P_pi
print(f"  Pπ = {P_pi*1000:.2f} mW")
print(f"  Heater R = {ps.R_Ohm:.1f} Ω")
print(f"  R_th (1D) = {ps.R_th:.1f} K/W")

# Verify Pπ yields π phase
ps.set_power(P_pi)
phase = ps.phase - ps.phase_offset
print(f"  Phase at Pπ: {np.degrees(phase):.1f}° (expected 180°)")
assert abs(phase - np.pi) < 1e-10
print(f"  ✅ Pπ yields π phase shift")

# ----------------------------------------------------------
# Test 6: MZI Class
# ----------------------------------------------------------
print("\n── Test 6: MZI Class ──")
mzi = MZI()
T_test = mzi_transfer_matrix(np.pi/3, np.pi/4)
mzi.program(T_test)
err = np.max(np.abs(mzi.matrix - T_test))
print(f"  Program error: {err:.2e}")
assert err < 1e-14
print(f"  ✅ MZI class works")

# ----------------------------------------------------------
print("\n" + "=" * 68)
print("  Level 1: ALL TESTS PASSED ✅")
print("=" * 68)
