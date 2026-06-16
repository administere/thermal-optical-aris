# Thermal-Optical Hybrid Processor — Engineering Validation

> Computing with light, controlling light with heat. An honest engineering analysis.

## What This Is

I'm analyzing the feasibility of a new type of optical computing chip. The core idea is simple:

```
A laser beam → passes through a special thin film → hits a detector
                     ↑
              The film is heated to 242°C
              Heating changes how the film bends light
              This controls light intensity precisely
              = "thermo-optic computing"
```

The key trick is **photon reuse**: one light pulse passes through 2048 modulation points, doing 2048 multiplications. The light carries data AND maintains the temperature.

## Six Core Questions

| # | Question | Current Answer |
|---|----------|:--:|
| 1 | Can we sustain 242°C? | Material confirmed capable, but VCSEL self-heating alone is insufficient — needs external heat source |
| 2 | Is it fast enough? | Classical thermal: ~0.5 weight updates/sec — comparable to H100 |
| 3 | Is the optical signal strong enough? | Yes, SNR 32 dB |
| 4 | Is the circuit design complex? | No — needs only D ADCs, not D² |
| 5 | Is it energy efficient? | With quantum beating (17.6 GHz): ~200× better than H100. Classical: only a few × |
| 6 | Can we build it? | Needs experimental validation first. ~$5K, ~2 weeks |

## The Material: DiSubPc·C70

Sichuan University published a paper in *Nature Photonics* (2026) about an organic cocrystal called DiSubPc·C70. When illuminated, it heats itself to 242°C, and its electrons exhibit "quantum beating" at 17.6 billion times per second.

The original paper only used it for photothermal conversion (steam generation, desalination). I'm the first to propose using it for optical computing — the material's refractive index changes with temperature at 242°C, which can be used for optical multiplication.

### What makes it special

- **17.6 GHz quantum beating**: electrons oscillate between two quantum states 17.6 billion times per second. If this oscillation can be converted to light intensity modulation, computing speed would be 400× faster than classical thermal methods.
- **Polar crystal structure**: the molecules are arranged asymmetrically — this is the structural basis for quantum beating. The similar C60 version is symmetric and only achieves 6 GHz.

### What's problematic

- **850nm absorption is too weak**: the material absorbs best at ~570nm (green light). At 850nm (near-infrared), absorption is ~230× weaker. We estimated the value mathematically but with large uncertainty.
- **No measurements at 242°C**: all spectral data only goes to room temperature (27°C). What happens at 242°C is extrapolated.
- **Quantum beating hasn't been used for computing**: the paper only proved beating generates heat, not that it can modulate light.

## Alternative Material: TiO₂

If we skip quantum beating and just do "heat changes refractive index", TiO₂ is the better engineering choice:

- Thermo-optic coefficient 3× larger than DiSubPc·C70
- Completely transparent — no light wasted
- Melting point 1840°C — 242°C is nothing
- Standard semiconductor fabrication process

But it has zero quantum effects. TiO₂ is better for classical thermo-optic computing. DiSubPc·C70 is the only option if you're betting on a quantum breakthrough.

## Energy Comparison

| Approach | Energy per dot product | vs H100 |
|----------|:--:|:--:|
| DiSubPc·C70 self-heating @ 850nm | 377,000 fJ | 8× |
| DiSubPc·C70 external oven @ 570nm | 706,000 fJ | 4× |
| TiO₂ external oven @ 570nm | 693,000 fJ | 4× |
| **DiSubPc·C70 quantum beating** | **14,000 fJ** | **199×** |

> H100 GPU doing the same work needs ~2,900,000 fJ.

**Bottom line: classical thermal methods are only a few × better than GPU. Only quantum beating enables an order-of-magnitude breakthrough. Choosing TiO₂ vs DiSubPc matters ~20%. Choosing quantum vs classical matters ~50×.**

## Experiment Priority

1. **Most critical**: verify at 242°C whether quantum beating can modulate light
2. **Important**: measure TiO₂ and DiSubPc·C70 actual thermo-optic coefficient at 242°C
3. **Can wait**: precisely measure DiSubPc·C70 absorption at 850nm

## Run

```bash
# Main validation
python engineering_validation.py

# Material analyses
python materal_source_data/absorption_analysis.py
python materal_source_data/modulation_mechanisms.py
python materal_source_data/crystal_structure_analysis.py

# Optical simulation
python meep_fdtd_validation.py

# Energy comparison
python energy_comparison_v2.py

# Oven architecture (long-term exploration)
python oven_architecture_validation.py
```

## About

Independent engineering analysis of a novel optical computing architecture. All physical parameters calibrated against MOESM1-8 experimental data. Honest assessment of feasibility and uncertainties.

🤖 AI-assisted analysis · Independent engineering validation
