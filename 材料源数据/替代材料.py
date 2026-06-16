#!/usr/bin/env python3
"""
热光计算替代光热材料搜索
===========================

评估 DiSubPc·C70 的潜在替代品, 用于热光混合处理器。
选择标准:
  1. 在 850 nm (或可行的 VCSEL 波长) 处具有强吸收率
  2. 高光热转换效率 (PCE)
  3. 在 242°C+ 下具有热稳定性
  4. 光学调制的潜力 (Δn, Δk, 或 Δφ)
  5. 对计算应用的适用性 (阵列兼容, 薄膜可加工)

来源: 2024-2026 年文献 + Nature Photonics 2026 MOESM 基准测试
"""

import numpy as np

# ============================================================
# 候选材料数据库
# ============================================================

CANDIDATES = {
    # ── 有机共晶 (供体-受体 CT 复合物) ──
    'TMB-TCNB (T2C1)': {
        'type': '有机 CT 共晶',
        'absorption_nm': (400, 957),  # 范围
        'peak_nm': 808,
        'alpha_at_850': '~5000 cm⁻¹ (估计)',
        'PCE_pct': 75.5,
        'max_temp_C': 106,  # @ 0.7 W/cm²
        'T_decomp_C': '未知 (~200-250 估计)',
        'thermal_tau_s': '未知',
        'modulation_mechanism': 'CT 态布居 (ps-ns)',
        'optical_nonlinearity': '弱 (中心对称堆积?)',
        'quantum_coherence': '未知',
        'CMOS_compatible': '可能 (有机薄膜)',
        'key_advantage': '极高的 PCE (75.5%), NIR 吸收可调',
        'key_disadvantage': '仅达到 106°C (不是 242°C), 热稳定性未知',
        'ref': 'Xu et al., Chin. Chem. Lett. 2024, 35, 109808',
        'suitable': False,  # 温度不足
    },
    'MFC (F₄TCNQ 基)': {
        'type': '有机 CT 共晶',
        'absorption_nm': (600, 1100),
        'peak_nm': 808,
        'alpha_at_850': '中等 (CT 带)',
        'PCE_pct': 54.6,
        'max_temp_C': '未明确报告',
        'T_decomp_C': '未知',
        'thermal_tau_s': '未知',
        'modulation_mechanism': 'CT 态布居',
        'optical_nonlinearity': '可能 (取决于堆积)',
        'quantum_coherence': '未知',
        'CMOS_compatible': '可能',
        'key_advantage': 'NIR-II 吸收范围, 强 CT 相互作用',
        'key_disadvantage': 'PCE 低于 DiSubPc·C70, 温度数据不足',
        'ref': 'Zhang et al., Chin. J. Chem. 2024, 42, 1563',
        'suitable': False,
    },
    'DFQ (二甲蒽-F₄TCNQ)': {
        'type': '有机 CT 共晶',
        'absorption_nm': (700, 1200),
        'peak_nm': 1064,
        'alpha_at_850': '中等-强',
        'PCE_pct': 73.6,
        'max_temp_C': '未明确报告',
        'T_decomp_C': '未知',
        'thermal_tau_s': '未知',
        'modulation_mechanism': 'CT 态布居',
        'optical_nonlinearity': '可能',
        'quantum_coherence': '未知',
        'CMOS_compatible': '可能',
        'key_advantage': 'NIR-II 高 PCE (73.6%)',
        'key_disadvantage': '1064 nm 优化 (非 850 nm), 温度数据不足',
        'ref': 'RSC Advances / Angew. Chem. 2024',
        'suitable': False,
    },

    # ── 克酮酸菁染料 ──
    'CR880 (克酮酸菁)': {
        'type': '有机 NIR 染料',
        'absorption_nm': (800, 950),
        'peak_nm': 880,
        'alpha_at_850': 'ε = 1.84×10⁵ L/(cm·mol) → α ~10⁴ cm⁻¹',
        'PCE_pct': 58,
        'max_temp_C': '约 80 (纳米粒子)',
        'T_decomp_C': '>250 (有机物, 估计)',
        'thermal_tau_s': 'ps-ns (非辐射弛豫)',
        'modulation_mechanism': '激发态吸收 (ESA)',
        'optical_nonlinearity': '中等 (大 π 共轭)',
        'quantum_coherence': '未研究',
        'CMOS_compatible': '兼容 (可溶液加工)',
        'key_advantage': '非常强的 880 nm 吸收, 优异的光稳定性',
        'key_disadvantage': '低热稳定性 (有机染料), 无量子相干性',
        'ref': 'Spence, Hartland & Smith, Chem. Sci. 2013, 4, 4240',
        'suitable': False,
    },
    'CRTe (Te-克酮酸菁)': {
        'type': '有机 NIR 染料',
        'absorption_nm': (900, 1200),
        'peak_nm': 1064,
        'alpha_at_850': '弱 (在带边以下)',
        'PCE_pct': 70.6,
        'max_temp_C': '约 80',
        'T_decomp_C': '>250 (估计)',
        'thermal_tau_s': 'ps-ns',
        'modulation_mechanism': '激发态吸收',
        'optical_nonlinearity': '中等',
        'quantum_coherence': '未研究',
        'CMOS_compatible': '兼容',
        'key_advantage': '目前已知最高的有机 PCE (70.6%), NIR-II',
        'key_disadvantage': '1064 nm 优化, 而非 850 nm; 温度限制',
        'ref': 'Chalcogen-Modulated Croconaine, 2024',
        'suitable': False,
    },

    # ── 无机相变材料 ──
    'GST (Ge₂Sb₂Te₅)': {
        'type': '无机相变材料',
        'absorption_nm': (900, 5000),  # 宽带
        'peak_nm': '宽带 (无定形态 >90% 吸收 @ 0.9–1.4 μm)',
        'alpha_at_850': '~10⁴–10⁵ cm⁻¹ (无定形态)',
        'PCE_pct': 'N/A (相变, 非光热)',
        'max_temp_C': 150,  # 结晶温度
        'T_decomp_C': '>600 (硫系玻璃)',
        'thermal_tau_s': 'ps (飞秒激光致非晶化)',
        'modulation_mechanism': '非晶 ↔ 晶体 相变 (Δn ~1–2)',
        'optical_nonlinearity': '高 (相变调制)',
        'quantum_coherence': 'N/A',
        'CMOS_compatible': '✅ 已在相变存储器中验证',
        'key_advantage': '成熟的光子学平台, 超快 (ps) 切换, 多级',
        'key_disadvantage': '功率大, 需要 ~160°C 以上才能擦除, 疲劳寿命有限 (10⁶–10⁸ 次循环)',
        'ref': 'Sci. China Mater. 2024; Photonics 2024, 11(3), 272',
        'suitable': True,  # ★ 经证实的光子计算候选方案
    },
    'Sb₂S₃ (宽带隙 PCM)': {
        'type': '无机相变材料',
        'absorption_nm': (500, 900),
        'peak_nm': '可见光-近红外',
        'alpha_at_850': '~10⁴ cm⁻¹ (无定形态)',
        'PCE_pct': 'N/A',
        'max_temp_C': 270,  # 结晶温度
        'T_decomp_C': '>500',
        'thermal_tau_s': 'ns-μs',
        'modulation_mechanism': '非晶 ↔ 晶体 (Δn ~0.5–1)',
        'optical_nonlinearity': '中等-高',
        'quantum_coherence': 'N/A',
        'CMOS_compatible': '✅ 低毒, 与 BEOL 兼容',
        'key_advantage': '比 GST 透明更好; 更高的结晶温度 (270°C)',
        'key_disadvantage': '折射率对比度低于 GST, 相变速度较慢',
        'ref': 'Delaney et al., Adv. Mater. 2020; Nat. Photonics 2021',
        'suitable': True,
    },

    # ── MXene (2D 过渡金属碳化物) ──
    'Ti₃C₂ MXene': {
        'type': '2D 无机材料',
        'absorption_nm': (300, 2000),  # 超宽带
        'peak_nm': '宽带 (等离子体 + 自由载流子)',
        'alpha_at_850': '~10⁵ cm⁻¹ (薄膜)',
        'PCE_pct': '~60–80 (纳米片)',
        'max_temp_C': '>200',
        'T_decomp_C': '>500 (氧化问题在空气中 >300°C)',
        'thermal_tau_s': 'ps (光激发载流子冷却)',
        'modulation_mechanism': '自由载流子吸收 + 热',
        'optical_nonlinearity': '高 (可饱和吸收)',
        'quantum_coherence': 'N/A',
        'CMOS_compatible': '⚠️ 需要惰性气氛 (氧化敏感性)',
        'key_advantage': '超宽带吸收, 高 PCE, 强光-物质相互作用',
        'key_disadvantage': '在空气中 >300°C 时氧化; 难以均匀成膜',
        'ref': 'Adv. Electron. Mater. 2025; Sci. Direct 2025',
        'suitable': False,  # 长期氧化稳定性问题
    },

    # ── 二维 TMD (过渡金属二硫属化物) ──
    'MoS₂ (少层)': {
        'type': '2D TMD 半导体',
        'absorption_nm': (400, 700),  # 可见光为主
        'peak_nm': '~660 (A 激子) / ~610 (B 激子)',
        'alpha_at_850': '非常弱 (低于带隙, E_g≈1.8 eV → 689 nm)',
        'PCE_pct': '~40–50',
        'max_temp_C': '>500',
        'T_decomp_C': '>800',
        'thermal_tau_s': 'ps (激子-声子耦合)',
        'modulation_mechanism': '激子诱导 Δn',
        'optical_nonlinearity': '极高 (χ⁽²⁾ ~10⁻⁷ esu, 单层)',
        'quantum_coherence': '激子量子拍频 (飞秒尺度)',
        'CMOS_compatible': '✅ 与硅集成已验证',
        'key_advantage': '超强 χ⁽²⁾, 高温稳定性, 已验证的器件',
        'key_disadvantage': '在 850 nm 处极弱吸收 (< 带隙), 需要可见光 VCSEL',
        'ref': 'Nat. Nanotech. 2014-2024; ACS Nano 2025',
        'suitable': True,  # ★ 如果切换至可见光 VCSEL (630-670 nm)
    },

    # ── 卟啉基材料 ──
    '卟啉 COF (共价有机框架)': {
        'type': '有机框架',
        'absorption_nm': (600, 900),  # 取决于金属化
        'peak_nm': '可调 (金属化卟啉)',
        'alpha_at_850': '中等 (Q 带)',
        'PCE_pct': '~50–65',
        'max_temp_C': '>300 (COF 热稳定性 >400°C)',
        'T_decomp_C': '>400',
        'thermal_tau_s': 'ps-ns',
        'modulation_mechanism': '金属配位调制 Δn',
        'optical_nonlinearity': '高 (push-pull 卟啉)',
        'quantum_coherence': '可能的 (金属中心自旋)',
        'CMOS_compatible': '可能',
        'key_advantage': '高热稳定性, 波长可调, 有序孔道结构',
        'key_disadvantage': '合成复杂, 薄膜质量控制困难',
        'ref': 'Sci. China Mater. 2024; Angew. Chem. 2025',
        'suitable': True,
    },
}


def compare_candidates():
    """不同候选材料的系统比较"""
    print("=" * 80)
    print("  热光计算替代光热材料 — 系统比较")
    print("=" * 80)

    suitable = {k: v for k, v in CANDIDATES.items() if v['suitable']}
    unsuitable = {k: v for k, v in CANDIDATES.items() if not v['suitable']}

    # 按类型分组
    print(f"\n  ★ 合适候选 ({len(suitable)}) — 满足最低要求:")
    for name, m in suitable.items():
        print(f"\n    [{m['type']}] {name}")
        print(f"      吸收: {m['peak_nm']}")
        print(f"      最大温度: {m['max_temp_C']}°C")
        print(f"      调制: {m['modulation_mechanism']}")
        print(f"      非线性光学: {m['optical_nonlinearity']}")
        print(f"      CMOS 兼容性: {m['CMOS_compatible']}")
        print(f"      优势: {m['key_advantage']}")
        print(f"      劣势: {m['key_disadvantage']}")
        print(f"      参考文献: {m['ref']}")

    print(f"\n  ✗ 排除的候选 ({len(unsuitable)}) — 未达到要求:")
    for name, m in unsuitable.items():
        reason = "温度不足" if 'max_temp_C' in str(m.get('key_disadvantage', '')) else m['key_disadvantage'][:60]
        print(f"    {name:<25s}: {reason}")

    return suitable


def diag_analysis():
    """对角线分析: 哪种候选材料适用于哪种场景?"""
    print("\n" + "=" * 80)
    print("  情景分析: 为您的架构匹配候选材料")
    print("=" * 80)

    scenarios = {
        'A: 当前架构 (850 nm, 242°C)': {
            'primary': 'GST (Ge₂Sb₂Te₅)',
            'reason': '在 850 nm 处吸收 >90%, 热稳定性 >600°C, '
                       '已验证的光子计算平台, 多级相变状态',
            'tradeoff': '循环疲劳 (10⁶-10⁸), 需要重置功率',
            'alternative': '当前的 DiSubPc·C70 在量子相干性方面仍然更优',
        },
        'B: 可见光 VCSEL (630-670 nm)': {
            'primary': 'MoS₂ (单层/少层)',
            'reason': '强激子共振吸收, 极高的 χ⁽²⁾ (~10⁻⁷ esu), '
                       '已验证的片上集成, >800°C 热稳定性',
            'tradeoff': '需要可见光 VCSEL (630 nm), 而非 850 nm; 覆盖面积小 (μm)',
            'alternative': '卟啉 COF — 可调 Q 带吸收, 热稳定性 >400°C',
        },
        'C: 仅热筛 (无量子相干, 静态权重)': {
            'primary': 'Sb₂S₃ 宽带隙 PCM',
            'reason': '宽透明窗口, 高结晶温度 (270°C), '
                       '低光学损耗, BEOL 兼容',
            'tradeoff': '调制速度较慢 (ns-μs), 比 GST 低的折射率对比度',
            'alternative': 'Ti₃C₂ MXene — 如果氧化问题得到解决',
        },
        'D: 混合量子-经典 (χ⁽²⁾ 增强)': {
            'primary': '2DiSubPc-C70 (当前材料)',
            'reason': '唯一具有量子相干拍频 + 非中心对称 χ⁽²⁾ 的材料, '
                       '已达到 242°C, 独特的 S₁-¹TT 拍频机制',
            'tradeoff': '在 850 nm 处吸收弱 (α≈350 cm⁻¹), 需要辅助加热',
            'alternative': '卟啉 COF + 金属中心 (自旋-轨道耦合增强)',
        },
    }

    for scenario, analysis in scenarios.items():
        print(f"\n  📋 {scenario}")
        print(f"     → 主要候选: {analysis['primary']}")
        print(f"     → 原因: {analysis['reason']}")
        print(f"     → 权衡: {analysis['tradeoff']}")
        print(f"     → 替代方案: {analysis['alternative']}")


def recommendation():
    """最终建议"""
    print("\n" + "=" * 80)
    print("  建议的行动方案")
    print("=" * 80)

    print("""
  第 1 优先级: 在 850 nm 处对 DiSubPc·C70 进行薄膜吸收测量
    在更换材料之前, 首先通过实验确认 α(850 nm) 的实际值。
    乌尔巴赫外推表明 α≈350 cm⁻¹ (吸收率为 30%), 但外推
    存在固有缺陷。在 850 nm 处的直接薄膜透射率测量可以解决
    这一不确定性。

  第 2 优先级: 评估 808 nm VCSEL (而非 850 nm)
    许多有机 CT 材料在 808 nm 处的吸收要强得多 (流行的二极管
    激光器波长)。TMB-TCNB 和克酮酸菁在 808 nm 处均表现出
    强吸收。将 VCSEL 波长从 850 nm 改为 808 nm 将开启更广泛
    的候选材料范围。

  第 3 优先级: 并行开发 GST/Sb₂S₃ 基线
    在 DiSubPc·C70 的量子相干调制得到实验验证之前, GST 或 Sb₂S₃
    相变材料提供了低风险的后备方案。两者都已用于光子计算,
    并具有高声学成熟度 (TRL 4–6)。

  第 4 优先级: 探索 1064 nm VCSEL 选项
    NIR-II 候选材料 (DFQ, CRTe) 在 1064 nm 处表现出优异的 PCE
    (70–74%)。如果 1064 nm VCSEL 可行, 这些材料可能比 850 nm
    选项表现更好。

  底线:
    DiSubPc·C70 对于量子相干增强的光热转换仍然是独一无二的。
    没有其他候选材料同时具备: 242°C 工作温度 + 量子相干拍频 +
    非中心对称 χ⁽²⁾ + 已证实的光热稳定性。
    但它在 850 nm 处的弱吸收是真正的弱点 — 在切换材料之前,
    首先通过实验测量这一点。
""")


if __name__ == '__main__':
    suitable = compare_candidates()
    diag_analysis()
    recommendation()
