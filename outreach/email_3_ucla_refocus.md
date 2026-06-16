# Email 3: ReFOCUS Team (UCLA / University of Florida)

**To:** Shurui Li, Hangbo Yang, Chee Wei Wong, Volker J. Sorger, Puneet Gupta
**Find corresponding author email from:** *ACM/IEEE MICRO* 2023, DOI `10.1145/3613424.3623798`
**Priority:** ⭐⭐⭐ — photon reuse concept originators

---

**Subject: Photon reuse beyond waveguides — a free-space thermal approach, would appreciate your take**

Dear Dr. Li, Prof. Wong, Prof. Sorger, and Prof. Gupta,

Your ReFOCUS paper (MICRO 2023) established the vocabulary and value proposition of "photon reuse" in optical computing — the insight that a single photon can do more than one MAC operation. That paper is explicitly cited in my analysis as the origin of the photon reuse concept.

I'm reaching out because I've been exploring a very different physical implementation of photon reuse — and would value your expert assessment.

**The idea: photon reuse in a free-space thermal modulation array.**

Instead of spiral waveguide delay lines in a 4F correlator:
- A VCSEL beam carrying Q-encoded data passes through a **free-space 2D array** of thermal modulation points (a "thermal sieve")
- The modulation material is DiSubPc·C70, an organic cocrystal that exhibits quantum coherent beating at 242°C (discovered by Chen et al., *Nature Photonics* 2026)
- One photon pulse traverses D modulation points → D MAC operations → detected by CMOS+APD array
- The same light beam also photothermally sustains the 242°C operating temperature

**Key result:** 0.6 fJ per D-dimensional dot product (purely optical), ~5×10⁶ more efficient than a GPU.

**How this relates to ReFOCUS:**
| ReFOCUS | This Work |
|---------|-----------|
| Waveguide delay lines | Free-space multi-pass |
| Fourier optics (4F correlator) | Direct amplitude modulation |
| Passive weights | Active thermal Δn modulation |
| CNN convolution | Matrix-vector dot products |

**Honest state:** All simulation, no hardware. Engineering validation only.

**What I'm asking:**
Your group has hands-on experience with the realities of photon reuse — losses, crosstalk, alignment, detection noise. I'm looking for a reality check:

1. In your experience, what's the dominant loss mechanism that kills photon reuse efficiency in practice?
2. Is a free-space multi-pass architecture fundamentally harder than waveguide reuse, or just different?
3. If you were to design a minimum-viable experiment to test free-space photon reuse with D=4, what would you measure first?

Analysis and code: https://github.com/[your-username]/thermal-optical-validation

No expectation of a reply — just grateful for the foundational work you've already done.

Best,
[Your Name]
[Affiliation / City]
[Email]
