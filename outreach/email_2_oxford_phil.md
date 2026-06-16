# Email 2: PHIL Unit Team (Oxford / HYBRAIN)

**To:** Yi Zhang, Nikolaos Farmakidis, Harish Bhaskaran, Nikos Pleros
**Find corresponding author email from:** *Nature Communications* 17 (2026), DOI `10.1038/s41467-025-67726-0`
**Priority:** ⭐⭐⭐⭐ — closest architectural cousin

---

**Subject: Building on PHIL — a free-space thermal sieve for optical MAC using the same "heat as computation" philosophy**

Dear Dr. Zhang, Dr. Farmakidis, Prof. Bhaskaran, and Prof. Pleros,

I recently read your PHIL unit paper in *Nature Communications* (2026) with great interest. The idea that thermal dynamics can be strategically engineered for computation rather than avoided is, in my view, a genuinely important conceptual shift.

I'm writing because I've been exploring a related idea — and would be grateful for your candid assessment of whether it holds water.

**The concept: a free-space thermal sieve for matrix-vector multiplication.**

The key differences from PHIL:
- Instead of titanium nano-antennas on Si microrings, it uses **DiSubPc·C70** — an organic cocrystal that exhibits 17.6 GHz quantum coherent beating between singlet and triplet states at 242°C (discovered by Chen, Zhang, You et al., *Nature Photonics* 2026, for photothermal conversion)
- The **same light beam** that carries Q-encoded data also photothermally sustains the 242°C operating temperature — no separate control wavelength, no external heaters
- **Free-space architecture** (not waveguide): a 2D array of modulation points, with **photon reuse** — one photon pulse traverses D modulation points, performing D MAC operations before detection
- The modulation mechanism is Δn via singlet↔triplet population oscillation (quantum coherent), rather than thermo-optic resonance shift (classical)

**Engineering analysis results (D=2048):**
- Pure optical energy: 0.6 fJ/dot-product (~5×10⁶ vs H100 GPU)
- System energy (with ADC + detectors): 17 fJ
- SNR >18 dB with Si APD (M=20)
- D=512–1024 is the sweet spot for energy-precision tradeoff

**Honest limitations:**
- All simulation, zero hardware
- 0.033 Hz weight update rate (thermal time constant) — inference only
- ~16W auxiliary heating still needed; VCSEL alone can't quite sustain 242°C
- Attention is ~3% of transformer FLOPs, so end-to-end speedup is limited by Amdahl's law

I explicitly cite PHIL as the conceptual precedent for "thermal computing" throughout my analysis. The novelty claims are narrow: new material for computing, self-heating free-space architecture, and photon reuse in a thermal modulation array.

**What I'm asking:**
This is an independent engineering analysis (not a research lab, no funding). I'm looking for expert scrutiny. If you or a member of your group could spend 15 minutes looking at the analysis, I would value any feedback — especially:

1. Is the free-space multi-pass thermal modulation concept physically flawed in ways I'm missing?
2. Are there known results from PHIL experiments that would constrain or invalidate this approach?
3. Is this direction worth pursuing toward a $15K proof-of-concept experiment?

Full analysis and code: https://github.com/[your-username]/thermal-optical-validation

I understand you're busy and this is a cold email. No expectation of a reply. But if this sparks any interest, I'd be happy to discuss further.

Thank you for the PHIL work — it opened a door.

Best regards,
[Your Name]
[Affiliation / City]
[Email]
