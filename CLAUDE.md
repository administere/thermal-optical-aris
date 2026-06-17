# 热光混合处理器 — 工程验证

## 项目概述

研究 DiSubPc·C70 有机共晶材料在光计算中的应用可行性。核心问题：能否利用光热效应（或量子相干拍频 17.6 GHz）实现低能耗光学矩阵乘法？

## 关键参数

- 材料：DiSubPc·C70（四川大学 Nature Photonics 2026）
- 工作温度：242°C
- 量子拍频：17.6 GHz（MOESM2 实测）
- 激发态寿命：τ = 4.2 ns（MOESM8 瞬态吸收）
- 极性非中心对称堆积：Cc 空间群（MOESM3 晶体结构）
- 目标波长：850nm（计算）/ 570nm（加热）

## 验证脚本体系

### 核心验证（根目录）
- `工程验证.py` — 核心工程分析（热耦合、SNR、噪声预算、能量效率）
- `综合验证.py` — 8 子系统多维验证（3D 热学、TMM 光学、良率模型、制造可行性）
- `第一性原理.py` — 五定理物理推导（Maxwell/Boltzmann 出发）
- `能量对比v2.py` — 5 方案能耗对比（含量子拍频）
- `材料局限性.py` — DiSubPc·C70 四大局限
- `FDTD光学验证.py` — MEEP 全波电磁仿真

### 材料源数据（材料源数据/）
- `吸收分析.py` — 乌尔巴赫带尾外推 850nm 吸收系数
- `调制机制.py` — 三种调制机制速度对比
- `晶体结构分析.py` — 三种共晶结构对比

### MZI 波导网格（马赫曾德网格/）
- Clements 酉分解 → SVD 矩阵乘法 → 保真度/串扰分析

### 验证测试（脚本/）
- 四级验证：单 MZI → 2D 热学 → Clements → SVD

## 核心风险（按优先级）

1. 量子拍频能否耦合到光调制？论文只证明拍频产生热，未证明光调制
2. DiSubPc·C70 在 242°C 长期运行（>1000h）不分解？
3. 850nm 吸收系数外推不确定度 ~10×（α = 35-3500 cm⁻¹）
4. dn/dT 在 242°C 下不退化？
5. 大面积薄膜均匀性 ±5μm？

## 技术栈

- Python 3.10+, NumPy, SciPy, Matplotlib
- MEEP（FDTD 全波电磁仿真）
- openpyxl（读取 MOESM Excel 数据）

## 运行环境

```bash
pip install numpy scipy matplotlib openpyxl
# MEEP 需要系统级安装:
sudo apt install meep meep-mpi-default
# 或 conda:
conda install -c conda-forge pymeep
```

## ARIS 自动化科研环境

本项目集成了 ARIS (Auto-Research-In-Sleep)，80 个科研 skills 可用于自动化文献调研、idea 发现、实验规划、论文写作。

**首次使用:**
```bash
bash setup-aris.sh
```

**审稿模式:** `manual`（零成本，粘贴到任何免费模型即可审稿）。如需 Codex MCP（GPT-5.5 审稿），运行 `codex setup`。

**常用 ARIS 命令（在 claude 会话中）:**
- `/research-lit "主题"` — 文献调研
- `/idea-discovery "方向"` — 找创新点
- `/research-pipeline "方向"` — 全流程自动化
- `/auto-review-loop "论文"` — 自动审稿循环
- `/paper-writing "报告"` — 写论文

## 可复用的分析链路

换任何新材料（TiO₂、Sb₂S₃、VO₂、GST...），只需:
1. 把 MOESM 数据放到 `材料源数据/`
2. 修改对应脚本中的材料参数
3. 运行分析链: `吸收分析.py` → `调制机制.py` → `工程验证.py` → `能量对比v2.py`
4. 用 ARIS skills 辅助文献对比和实验规划
