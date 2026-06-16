#!/usr/bin/env python3
"""
晶体结构对验证的影响: 非中心对称 Cc 空间群与 χ⁽²⁾ 非线性
=============================================================

基于 MOESM3-5 (CIF 文件) 和 MOESM1 (表 S2) 的晶体学数据分析。

关键发现:
  - 2DiSubPc-C70: 单斜 Cc (非中心对称, 极性) → 支持 χ⁽²⁾
  - 2DiSubPc-C60: 单斜 P2₁/n (中心对称) → 无 χ⁽²⁾
  - 2DiSubPc 纯相: 三方 R-3c (中心对称) → 无 χ⁽²⁾

  极性空间群是 C70 共晶具有 17.6 GHz 量子拍频的结构基础。
"""

import numpy as np

# ============================================================
# 晶体学数据 (MOESM1 Table S2 + MOESM3-5 CIF)
# ============================================================

CRYSTAL_DATA = {
    '2DiSubPc (纯相)': {
        'file': 'MOESM3',
        'crystal_system': '三方 (Trigonal)',
        'space_group': 'R-3c (#167)',
        'symmetry': 'D₃d — 中心对称',
        'a_A': 13.3772, 'b_A': 13.3772, 'c_A': 41.769,
        'alpha': 90, 'beta': 90, 'gamma': 120,
        'V_A3': 6473.1,
        'density': 1.623,
        'B_B_distance_A': 6.96,
        'fullerene_distance_A': None,  # 无富勒烯
        'void_volume_pct': None,
        'T_measurement_K': 130,
        'R_factor_pct': 6.18,
        'is_centrosymmetric': True,
        'is_polar': False,
        'chi2_possible': False,
    },
    '2DiSubPc-C60': {
        'file': 'MOESM4',
        'crystal_system': '单斜 (Monoclinic)',
        'space_group': 'P2₁/n (#14)',
        'symmetry': 'C₂h — 中心对称',
        'a_A': 13.238, 'b_A': 25.513, 'c_A': 17.776,
        'alpha': 90, 'beta': 92.285, 'gamma': 90,
        'V_A3': 5998.9,
        'density': 1.586,
        'B_B_distance_A': 6.95,
        'fullerene_distance_A': (3.15, 3.37),  # min, max C60-SubPc
        'void_volume_pct': 3.5,  # 含甲苯
        'void_note': '去除甲苯后增至 25.6% → 结构可能塌缩',
        'T_measurement_K': 153,
        'R_factor_pct': 13.35,
        'is_centrosymmetric': True,
        'is_polar': False,
        'chi2_possible': False,
        'quantum_beat_GHz': 6.0,  # MOESM2 审稿人回复
    },
    '2DiSubPc-C70': {
        'file': 'MOESM5',
        'crystal_system': '单斜 (Monoclinic)',
        'space_group': 'Cc (#9)',
        'symmetry': 'Cₛ — 非中心对称 (极性!)',
        'a_A': 49.716, 'b_A': 11.0347, 'c_A': 21.540,
        'alpha': 90, 'beta': 103.506, 'gamma': 90,
        'V_A3': 11490.1,
        'density': 1.581,
        'B_B_distance_A': 6.90,
        'fullerene_distance_A': (3.03, 3.31),  # min, max C70-SubPc
        'void_volume_pct': 12.0,
        'void_note': '不足以容纳甲苯分子',
        'T_measurement_K': 150,
        'R_factor_pct': 23.67,
        'is_centrosymmetric': False,
        'is_polar': True,
        'chi2_possible': True,
        'quantum_beat_GHz': 17.6,  # MOESM2 审稿人回复
    },
}


def analyze_symmetry():
    """分析晶体对称性对光学非线性的影响"""
    print("=" * 70)
    print("  晶体结构对比分析")
    print("=" * 70)

    print(f"\n  {'晶体':<18s} {'空间群':<12s} {'对称性':<20s} {'极性':<6s} {'χ⁽²⁾':<6s} {'拍频':<10s}")
    print(f"  {'-'*70}")
    for name, d in CRYSTAL_DATA.items():
        short_name = name.replace('2DiSubPc', 'SubPc').replace(' (纯相)', '')
        sg = d['space_group'].split('(')[0].strip()
        pol = '✅' if d['is_polar'] else '❌'
        chi = '✅' if d['chi2_possible'] else '❌'
        beat = f"{d.get('quantum_beat_GHz', '—')} GHz" if d.get('quantum_beat_GHz') else '—'
        print(f"  {short_name:<18s} {sg:<12s} {d['symmetry']:<20s} {pol:<6s} {chi:<6s} {beat:<10s}")

    return CRYSTAL_DATA


def chi2_analysis():
    """χ⁽²⁾ 非线性光学分析"""
    print("\n" + "=" * 70)
    print("  χ⁽²⁾ 非线性光学计算潜力")
    print("=" * 70)

    c70 = CRYSTAL_DATA['2DiSubPc-C70']
    c60 = CRYSTAL_DATA['2DiSubPc-C60']

    # 非中心对称对 χ⁽²⁾ 至关重要
    # 在偶极近似下, χ⁽²⁾ = 0 对所有中心对称晶体
    # Cc 空间群属于 C_s 点群, 允许非零 χ⁽²⁾ 张量分量

    # C_s 对称性 (Cc 空间群) 的非零 χ⁽²⁾ 分量:
    # 镜面在 ac 平面 → y 轴垂直于镜面
    # 非零分量: d_11, d_12, d_13, d_22, d_23, d_31, d_32, d_33
    # (取决于轴的约定)

    print(f"""
  Cc 空间群 (C_s 点群) 的非零 χ⁽²⁾ 分量:

    对于标准约定 (b 轴垂直于镜面):
      χ⁽²⁾_xxx, χ⁽²⁾_xyy, χ⁽²⁾_xzz, χ⁽²⁾_xzx,
      χ⁽²⁾_yyx, χ⁽²⁾_yxy, χ⁽²⁾_yyy,
      χ⁽²⁾_zxx, χ⁽²⁾_zyy, χ⁽²⁾_zzz, χ⁽²⁾_zxz

  对于光学计算, 最重要的 χ⁽²⁾ 过程:
    1. 和频产生 (SFG): ω₁ + ω₂ → ω₃
    2. 差频产生 (DFG): ω₁ - ω₂ → ω₃
    3. 电光效应 (Pockels): Δn ∝ χ⁽²⁾E

  C70 共晶独有的优势:
    → 极性空间群 → 非零 χ⁽²⁾ → 二阶非线性光学过程
    → 更近的富勒烯-SubPc 距离 ({c70['fullerene_distance_A'][0]:.2f}–{c70['fullerene_distance_A'][1]:.2f} Å
       vs C60: {c60['fullerene_distance_A'][0]:.2f}–{c60['fullerene_distance_A'][1]:.2f} Å)
    → 更短距离 → 更强的电荷转移耦合 → 更大的 χ⁽²⁾

  对调制方案的影响:
    量子拍频 (17.6 GHz) 产生布居振荡
    → χ⁽²⁾ 非线性将布居振荡转换为光学频率转换
    → 例如, 探测光 ω_probe ± ω_beat → 边带
    → 边带强度 ∝ χ⁽²⁾² × N_population
    → 可以通过滤波检测边带来读取调制信号
""")


def structure_property_relationship():
    """结构-性质关系"""
    print("=" * 70)
    print("  结构-性质关系: 为什么 C70 > C60?")
    print("=" * 70)

    print("""
  ┌─────────────────┬──────────────────┬──────────────────┐
  │ 性质              │ 2DiSubPc-C60     │ 2DiSubPc-C70     │
  ├─────────────────┼──────────────────┼──────────────────┤
  │ 空间群            │ P2₁/n (中心对称)  │ Cc (非中心, 极性) │
  │ 富勒烯距离        │ 3.15–3.37 Å      │ 3.03–3.31 Å      │
  │ 空隙体积          │ 3.5% (含甲苯)    │ 12%              │
  │ 量子拍频          │ 6.0 GHz          │ 17.6 GHz         │
  │ 光热 ΔT           │ 211°C            │ 242°C            │
  │ χ⁽²⁾ 非线性       │ 禁止 (对称性)    │ 允许             │
  │ 结构稳定性        │ 依赖甲苯         │ 无溶剂, 更稳定   │
  └─────────────────┴──────────────────┴──────────────────┘

  因果链:
    非中心对称 Cc 空间群
      → 极性晶体结构
        → 非零 χ⁽²⁾ 非线性
          → 更强的光-物质相互作用
            → 更大的 S₁-¹TT 能隙 (ΔE)
              → 更高的量子拍频 (17.6 vs 6.0 GHz)
                → 更快的能量转移速率
                  → 更高效的光热转换 (242°C vs 211°C)

  这就是为什么 C70 共晶独一无二:
    C70 的椭球形状 + 不对称 π-π 相互作用
    → 诱导极性堆积 (Cc)
    → 量子相干增强光热转换
    → 这是传统有机光热材料无法达到的
""")


if __name__ == '__main__':
    analyze_symmetry()
    chi2_analysis()
    structure_property_relationship()
