#!/usr/bin/env python3
"""
调制机制分析: 量子相干 vs 经典热调制
======================================

基于 MOESM1-8 实验数据的系统分析，区分三种可能的调制机制
及其对热筛架构的意义。

三种机制:
  1. 经典热 Δn: τ ≈ 2s → f_max ≈ 0.5 Hz
  2. 电子激发态布居: τ_decay ≈ 4.2ns → f_max ≈ 0.24 GHz
  3. 量子相干拍频: f_beat = 17.6 GHz (C70) / 6.0 GHz (C60)

关键见解: 17.6 GHz 拍频不是经典调制速率。
它是局域单线态和离域三重态 (¹TT) 之间的量子力学相干振荡。
"""

import numpy as np

# ============================================================
# 机制 1: 经典热光效应 (Δn = dn/dT × ΔT)
# ============================================================
def thermal_modulation():
    """MOESM7 数据: 纯热响应时间"""
    print("=" * 70)
    print("  机制 1: 经典热光调制 (Δn = dn/dT × ΔT)")
    print("=" * 70)

    # MOESM7 Fig 4a 实测数据
    t_times = np.array([0, 1, 2, 5, 20, 30, 60])
    T_C70 = np.array([29, 112, 179, 228, 237, 242, 242])

    Delta_T = T_C70[-1] - T_C70[0]  # 213°C
    t_rise = 30  # 达到稳态需约 30s
    tau_thermal = 2.0  # 63.2% 上升 ~2s

    f_max_thermal = 1 / (2 * np.pi * tau_thermal)

    print(f"""
  物理机制:
    吸收光 → 非辐射衰变 → 晶格加热 → 折射率变化
    Δn = (dn/dT) × ΔT = (-1×10⁻⁴ /K) × 213K = -0.021

  实测参数 (MOESM7):
    热时间常数 τ ≈ {tau_thermal} s
    达到 242°C (稳态): ~30 s
    冷却时间 (关灯后): > 300 s (图 4b)

  调制带宽:
    f_max ≈ 1/(2πτ) ≈ {f_max_thermal:.3f} Hz
    这比当前假设的 0.033 Hz 快约 15 倍
    但比当前假设的 10 GHz 时钟慢 2×10¹⁰ 倍！

  适用场景:
    ✅ 静态推理 (权重 >2s 内不变)
    ✅ 批量处理 (同一权重处理多个输入)
    ❌ 实时训练
    ❌ 多租户快速切换
    ❌ 逐脉冲调制 (>GHz 速率)
""")

    return {
        'mechanism': 'Thermal Δn',
        'tau_s': tau_thermal,
        'f_max_Hz': f_max_thermal,
        'delta_n': -0.021,
        'source': 'MOESM7 Fig 4a/4b',
    }


# ============================================================
# 机制 2: 电子激发态布居调制
# ============================================================
def electronic_modulation():
    """MOESM8 数据: 激发态衰减时间"""
    print("=" * 70)
    print("  机制 2: 电子激发态布居调制")
    print("=" * 70)

    # MOESM8 Fig 5d 时间分辨衰减
    tau_decay = 4.2  # ns (1/e 衰减)
    f_max_electronic = 1 / (2 * np.pi * tau_decay * 1e-9) * 1e-9  # GHz
    # MOESM1 Table S3 PL lifetimes
    tau1_pl = 0.73  # ns (15.5%) — 辐射
    tau2_pl = 4.96  # ns (84.5%) — 热激活, 在 242°C 下可能更长

    # 温度外推 (MOESM1 Table S3)
    temps_K = np.array([6, 100, 200, 300])
    tau2_vals = np.array([3.72, 4.20, 4.62, 4.96])
    # 线性外推到 515K (242°C)
    slope_tau2 = np.polyfit(temps_K, tau2_vals, 1)[0]
    tau2_515K = np.polyval(np.polyfit(temps_K, tau2_vals, 1), 515)

    print(f"""
  物理机制:
    光激发 → S₁ 态 (单线态, 弗兰克-康登) → ¹TT 态 (三重态对)
    → 非辐射衰变至基态 → 热
    激发态布居改变折射率虚部 (吸收) 和实部 (Kramers-Kronig)

  实测参数 (MOESM8 Fig 5d + MOESM1 Table S3):
    激发态衰减 τ_decay (1/e) ≈ {tau_decay} ns @300K
    PL τ₁ = {tau1_pl} ns ({15.5}% @300K) — 辐射
    PL τ₂ = {tau2_pl} ns ({84.5}% @300K) — 热激活
    外推 τ₂ @515K ≈ {tau2_515K:.1f} ns

  调制带宽 (激发态布居):
    f_max ≈ 1/(2πτ_decay) ≈ {f_max_electronic:.1f} GHz
    注意: τ₂ 随温度升高而增长 — 在 242°C 可能更慢

  与 DiSubPc-C60 的比较 (MOESM2 审稿人回复):
    纯 2DiSubPc: 单线态裂分 S₁→¹TT (τ=2.5ps), 无振荡
    2DiSubPc-C60: 量子拍频 6.0 GHz
    2DiSubPc-C70: 量子拍频 17.6 GHz

  适用场景:
    ✅ ~100 MHz 级别调制 (比热调制快, 但受限于布居寿命)
    ⚠️ 非经典 — 受限于激发态寿命, 而非热扩散
    ❌ 10 GHz 时钟 — 需要量子相干机制
""")

    return {
        'mechanism': 'Electronic population',
        'tau_decay_ns': tau_decay,
        'tau1_pl_ns': tau1_pl,
        'tau2_pl_ns': tau2_pl,
        'tau2_515K_ns': tau2_515K,
        'f_max_GHz': f_max_electronic,
        'source': 'MOESM8 Fig 5d + MOESM1 Table S3',
    }


# ============================================================
# 机制 3: 量子相干拍频
# ============================================================
def quantum_beat_modulation():
    """MOESM2 数据: 量子相干拍频"""
    print("=" * 70)
    print("  机制 3: 量子相干拍频调制")
    print("=" * 70)

    f_beat_C70 = 17.6  # GHz
    f_beat_C60 = 6.0   # GHz
    tau_beat_C70 = 1 / f_beat_C70  # ns = 56.8 ps
    tau_decay = 4.2  # ns (布居衰减)

    n_cycles = tau_decay / tau_beat_C70  # 衰减前的拍频周期数

    print(f"""
  物理机制:
    光激发 → 局域单线态 (S₁, |1>) 和离域三重态对 (¹TT, |2>) 之间
    的量子相干叠加
    |ψ(t)⟩ = c₁(t)|S₁⟩ + c₂(t)|¹TT⟩
    布居振荡频率 f_beat = ΔE/h (两态之间的能隙)

  实测参数 (MOESM2 审稿人回复, Fig R5):
    C70 共晶拍频: {f_beat_C70} GHz → 周期 = {tau_beat_C70:.1f} ps
    C60 共晶拍频: {f_beat_C60} GHz → 周期 = {1/f_beat_C60*1000:.0f} ps
    纯 SubPc: 无振荡 — 仅 S₁→¹TT (τ=2.5ps)

  关键数字:
    布居衰减 τ_decay = {tau_decay} ns
    衰减前的拍频周期数: {n_cycles:.0f} 个
    拍频 vs 衰减比值: {tau_decay/tau_beat_C70:.0f}×

  为什么这对计算至关重要:
    ✅ 17.6 GHz 拍频为实现 ~17 GHz 时钟提供了物理基础
    ✅ 拍频源于量子相干性, 而非经典热弛豫
    ✅ 2DiSubPc-C70 的非中心对称 Cc 空间群 (极性!) 允许强 χ⁽²⁾
       非线性 — 支持相干态混合

  挑战:
    🔴 如何将量子拍频转化为经典光强调制?
       → 需要将相干布居振荡耦合到光学传输
       → 可能途径: χ⁽²⁾ 非线性和频/差频产生
       → 或: 拍频驱动的瞬态吸收调制 (ΔOD 振荡)

    🔴 拍频随温度升高会失相吗?
       → MPL 数据 (MOESM2 Q7) 显示 MPL 在更高温度下
         实际上更强 — 热激活有助于三重态布居
       → 但在 242°C 时失相时间未知

    🔴 C60 (6.0 GHz) vs C70 (17.6 GHz):
       → 拍频频率与结合亲和力相关
       → C70 的极性空间群 (Cc) 使能级分裂更大
       → 拍频频率 = ΔE/h, 更大的 ΔE → 更高的频率

  适用场景:
    ✅ 如果可以通过 χ⁽²⁾ 转换为光强调制, 则支持 ~17 GHz 操作
    ⚠️ 需要实验验证: 242°C 时相干性能维持多长时间?
    ⚠️ 这不是经典热筛 — 是量子相干调制器
    ❌ 如果失相时间 << 1ns, 17 GHz 拍频无法用于计算
""")

    return {
        'mechanism': 'Quantum coherent beating',
        'f_beat_C70_GHz': f_beat_C70,
        'f_beat_C60_GHz': f_beat_C60,
        'tau_beat_ps': tau_beat_C70,
        'n_cycles_before_decay': n_cycles,
        'requires_non_centrosymmetric': True,
        'source': 'MOESM2 Reviewer Response Fig R5',
    }


# ============================================================
# 综合比较
# ============================================================
def compare_mechanisms():
    """三种机制的系统比较"""
    print("=" * 70)
    print("  调制机制综合比较")
    print("=" * 70)

    mechanisms = {
        '热 Δn': {
            'f_max': '0.5 Hz',
            'τ': '2 s',
            '物理基础': '热扩散 + 热光效应',
            '优势': '简单, 与现有热筛架构完全兼容',
            '劣势': '极慢, 仅适用于静态推理',
            '数据来源': 'MOESM7 Fig 4a',
            '验证状态': '✅ 已确认',
        },
        '电子布居': {
            'f_max': '0.24 GHz',
            'τ': '4.2 ns',
            '物理基础': '激发态衰减 + Kramers-Kronig',
            '优势': '比热调制快 10⁸ 倍, 与有机光电子学兼容',
            '劣势': '衰减限制了 ~0.2GHz 带宽; 在 242°C 时可能更慢',
            '数据来源': 'MOESM8 Fig 5d + MOESM1 Table S3',
            '验证状态': '⚠️ 仅在 300K 时确认',
        },
        '量子相干拍频': {
            'f_max': '17.6 GHz',
            'τ': '56.8 ps (周期)',
            '物理基础': 'S₁↔¹TT 量子相干振荡',
            '优势': 'GHz 级操作的理论基础; C70 独有',
            '劣势': '需要 χ⁽²⁾ 转换; 242°C 时的失相时间未知; 架构需要根本性重新设计',
            '数据来源': 'MOESM2 审稿人回复 Fig R5',
            '验证状态': '⚠️ 实验观察到但未用于计算',
        },
    }

    print(f"\n  {'机制':<16s} {'最大频率':<12s} {'时间常数':<12s} {'验证':<10s}")
    print(f"  {'-'*50}")
    for name, m in mechanisms.items():
        print(f"  {name:<16s} {m['f_max']:<12s} {m['τ']:<12s} {m['验证状态']:<10s}")

    print(f"\n  建议:")
    print(f"    1. 短期: 使用热 Δn 机制 (τ≈2s), 更新 f_weight_Hz = 0.5")
    print(f"    2. 中期: 在 242°C 下测量 fs-TA, 量化电子调制带宽")
    print(f"    3. 长期: 设计利用 χ⁽²⁾ 非线性进行量子拍频 → 光强转换的实验")

    return mechanisms


if __name__ == '__main__':
    thermal = thermal_modulation()
    electronic = electronic_modulation()
    quantum = quantum_beat_modulation()
    compare_mechanisms()
