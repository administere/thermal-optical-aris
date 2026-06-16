# Email 4: PCM GEMM Team (Tang et al.)

**To:** Tang R. et al.
**Find corresponding author email from:** *Laser & Photonics Reviews* 17(2), 2023, DOI `10.1002/lpor.202200381`
**Priority:** ⭐⭐⭐ — free-space optical MVM architecture precedent

---

**Subject: Free-space optical MVM with organic cocrystals instead of PCM — a thermal alternative**

Dear Dr. Tang,

Your free-space PCM-based GEMM accelerator (*Laser & Photonics Reviews*, 2023) is, to my knowledge, one of the clearest demonstrations that free-space optical matrix-vector multiplication can be practically engineered. I cite your work as establishing the viability of the free-space optical MVM architectural motif.

I've been working on an independent engineering analysis of a related approach, and would be grateful for your perspective.

**The key difference: replacing GST phase-change material with DiSubPc·C70 organic cocrystals.**

Instead of storing weights via amorphous↔crystalline phase transitions:
- DiSubPc·C70 modulates refractive index via **quantum coherent beating** between singlet and triplet states at 242°C (discovered by Chen et al., *Nature Photonics* 2026)
- The data-carrying VCSEL beam **simultaneously heats** the film to 242°C — no external ITO electrodes, no Joule heating
- **Photon reuse**: one photon pulse traverses D modulation points for D MACs, vs. single-pass in your architecture

**Comparison:**
| PCM GEMM (Tang et al.) | This Work |
|------------------------|-----------|
| GST (inorganic chalcogenide) | DiSubPc·C70 (organic cocrystal) |
| External Joule heating | Self-heating via signal light |
| ~μs weight update | ~30 s weight update |
| No photon reuse | D× photon reuse |
| Non-volatile weights | Continuous thermal modulation |

**Tradeoff:** We lose weight update speed (~30s thermal vs ~μs electrical) but potentially gain attojoule-scale dot products through photon reuse.

I should be transparent: this is entirely simulation-based, no hardware, and I'm an independent researcher without institutional backing.

**What I'm asking:**
Having actually designed a free-space optical MVM system end-to-end, what do you see as the biggest practical blocker for a thermal modulation approach? In your experience with PCM arrays, what surprised you most when moving from simulation to experiment?

Analysis and code: https://github.com/[your-username]/thermal-optical-validation

I understand completely if you're too busy to reply. Thank you for the PCM GEMM work — it shaped my thinking on free-space architectures.

Best regards,
[Your Name]
[Affiliation / City]
[Email]
