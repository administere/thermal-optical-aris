# Thermal-Optical Hybrid Processor — Engineering Validation

> Independent engineering analysis. Central thesis: heat is not a parasitic effect — it is the computational mechanism itself.

## What This Is

This repository contains my engineering validation of a novel thermal-optical hybrid processor architecture:

```
VCSEL Array → DiSubPc·C70 Thermal Sieve (242°C) → CMOS+APD Detector Array
     ↑                    ↑                              ↑
  Q-encoded        Photothermal Δn               Direct photodetection
  photons          screens photons               (dot product result)
```

The key physical mechanism is **photon reuse**: a single photon pulse traverses D modulation points, completing D multiply-accumulate (MAC) operations. Light serves a dual purpose — it carries Q-encoded signals and simultaneously sustains the photothermal layer at its quantum coherent beating window (242°C).

![Architecture](figures/architecture.png)

## Six Engineering Questions

I structured my analysis around six core questions. Here are the conclusions:

| # | Question | Finding | Status |
|---|----------|---------|:------:|
| 1 | Can VCSEL light alone sustain 242°C? | ~16W auxiliary heating needed; optimizable | ⚠️ |
| 2 | Is 0.033Hz weight update viable? | Yes for static-weight inference; not for training | ✅ |
| 3 | Detector SNR after fan-out splitting? | Si APD (M=20) recovers SNR to >18dB at D=2048 | ✅ |
| 4 | How does ADC architecture scale? | Row-sequential pulsed readout: D ADCs, not D² | ✅ |
| 5 | Energy per dot product vs H100? | 0.6 fJ (optical) / 17 fJ (system) vs 2.9 nJ (H100) | ✅ |
| 6 | Experimental feasibility path? | $15K, ~4 weeks; 4×4 array is the critical milestone | ⚠️ |

## Key Numbers (D=2048)

| Metric | Value |
|--------|-------|
| Pure optical energy per D-dim dot product | **0.6 fJ** (~5 million × better than H100) |
| System energy (incl. ADC + detectors) | **17 fJ** (~170,000 × better than H100) |
| Total system power | ~707 W |
| Dot products per second | 41.9 Pops/s |
| CMOS temperature (50μm gap + cooling) | 107°C |
| SNR (APD M=20) | 18 dB |
| Photon reuse efficiency | 1 photon (~0.0002 fJ) performs 2048 MACs |

## D Scaling Law

The D=512–1024 range offers the best balance between energy efficiency and numerical precision.

| D | System Energy | vs H100 | SNR | ENOB | Total Power |
|:--:|:-------:|:-------:|:---:|:----:|:-----:|
| 128 | 3 fJ | 82K× | 38 dB | 6.1b | 3W |
| 256 | 4 fJ | 104K× | 34 dB | 5.3b | 11W |
| 512 | 6 fJ | 124K× | 29 dB | 4.5b | 44W |
| 1024 | 10 fJ | 141K× | 24 dB | 3.6b | 177W |
| 2048 | 17 fJ | 170K× | 18 dB | 2.7b | 707W |

![D Scaling](figures/d_scaling.png)

## Sensitivity Analysis

Which parameters matter most? I ran a systematic sweep. The top three:

1. **ADC FOM** — improving from 50→15 fJ/conv yields ~3× efficiency gain
2. **Detector power** — reducing from 0.1→0.01 mW/pixel yields ~5× efficiency gain
3. **VCSEL wall-plug efficiency** — improving from 40%→80% yields ~2× efficiency gain

![Sensitivity Analysis](figures/sensitivity.png)

## Candid Assessment

- **Physically sound**: the attojoule advantage of photon reuse follows directly from Maxwell's equations. Not an extrapolation.
- **Architecture is novel**: free-space thermal sieve is physically distinct from waveguide MZI (Xidian PTC) and passive diffraction (Gezhi OGPU).
- **Not a universal processor**: weight update rate is ~0.033Hz — static-weight inference only. Training, LoRA, and multi-tenant switching are not supported.
- **Amdahl's law applies**: attention accounts for ~3% of per-layer FLOPs in autoregressive inference. End-to-end speedup is ~1×. The value is in attention energy reduction, not throughput.
- **Simulation-to-experiment gap**: all results are simulation-based; no hardware yet. First experiment: VCSEL + DiSubPc·C70 film + APD (~$15K, ~4 weeks).

## Originality Statement

This work makes the following **first-disclosed** technical contributions:

1. **First proposal of DiSubPc·C70 as an optical computing element.** The material was discovered by Chen, Zhang, Wan, Zhang, You et al. (Sichuan University / CAS) and published in *Nature Photonics* (2026). Their paper concerns photothermal conversion only — steam generation, seawater desalination, photothermal therapy — with no mention of computing. I am the first to identify the material's 242°C / 17.6 GHz quantum coherent beating window as a mechanism for optical MAC operations.

2. **First self-heating thermal sieve architecture.** The data-carrying VCSEL beam simultaneously sustains the DiSubPc·C70 film at 242°C, eliminating external heaters. All prior thermo-optic computing architectures (PHIL, PCM-GEMM) rely on external electrical Joule heating or separate optical heating sources.

3. **First free-space photon reuse in a thermal modulation array.** One photon pulse traverses D modulation points, completing D MAC operations. Photon reuse exists in waveguide delay lines (ReFOCUS, MICRO 2023), but its implementation in a free-space thermal sieve is, to my knowledge, unprecedented.

For a detailed prior art analysis with full citations, see [PRIOR_ART.md](PRIOR_ART.md).

## Comparison with Other Photonic Approaches (D=512)

![Energy Comparison](figures/energy_comparison.png)

![Competitive Radar](figures/radar.png)

| Approach | Energy/Dot Product | Weight Update | Maturity |
|----------|:--------:|:--------:|:-----:|
| **Thermal-optical hybrid (this work)** | **6 fJ** | 30s (thermal) | Simulation |
| MZI electro-optic (Xidian PTC) | 10 fJ | ~μs | Chip demo |
| Passive diffractive (Gezhi OGPU) | 0.1 fJ | Non-updatable | Chip demo |
| SLM free-space (FAST-ONN) | 100 fJ | ~ms | Lab demo |

## Run

```bash
conda activate meep_env
python engineering_validation.py
```

## Context

This analysis is an independent engineering review of the photonic Transformer architecture described in [photonic-attention](https://github.com/administere/photonic-attention) (Wayne, 2026). The goal was to identify and quantify engineering challenges before tapeout — maintaining architectural consistency while stress-testing physical assumptions.

## Author

AI-assisted analysis · Independent engineering validation.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
