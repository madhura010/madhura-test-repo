# LNP Luciferase Expression Assays

## How to read this

Every assay here returns luminescence in arbitrary units. What distinguishes them is the denominator, and the denominator decides whether the value means anything outside its own plate.

**On the value ranges.** The ranges given are approximate, order-of-magnitude expectations from typical practice, not sourced figures. They are there to tell you whether a number you are looking at is plausible, saturating, or near noise — not to serve as a reference standard. Absolute luminescence depends on the luminometer, its gain and integration time, the substrate kit, the lysate volume and the cell number, so a value an order of magnitude outside these ranges usually indicates a different instrument setting rather than different biology. Treat every range as "the exponent is usually this", and calibrate against your own background and positive control.

Where a range is expressed as a ratio or a fold change it is far more stable, and those are the rows worth comparing against published work.

## In vitro assays

| Assay | Definition | Formula | Typical range (approximate) | Caveat | Post-normalisation |
| --- | --- | --- | --- | --- | --- |
| Endpoint firefly luciferase (Fluc) lysate assay | Cells treated with Fluc-mRNA LNP, lysed at a fixed time, luciferin + ATP added, integrated photon count read | Signal = RLU_sample − RLU_mock | Mock 10²–10³ RLU; a working LNP in HEK293 or HeLa at 100 ng/well, 24 h: 10⁵–10⁸ RLU. Signal-to-background 10³–10⁵ for a good formulation | Population total; cannot separate many weak cells from few bright ones. RLU is instrument-arbitrary | Required: divide by protein or viable-cell signal |
| Dual-luciferase (Fluc/Rluc) | Fluc from the test LNP, Rluc from a co-delivered or co-formulated control, read sequentially in one lysate | Ratio = RLU_Fluc / RLU_Rluc | Ratio 0.1–10 depending on the promoter and molar pairing; 1–50 fold spread between constructs within one study | Assumes both reporters reach the same cells in the formulated ratio — fine for co-encapsulated mRNA, weaker for two separate LNPs. Rluc can be squelched by strong Fluc expression | Fold change of the ratio vs a reference LNP |
| NanoLuc (Nluc) / Nano-Glo | Same design using the smaller, brighter NanoLuc with furimazine substrate | Signal = RLU_Nluc − RLU_mock | 10⁶–10⁹ RLU at the same dose; roughly 10–100 fold above the matching Fluc value | Detector saturation is common; furimazine is less stable and autoluminesces; spectral crossover into the Fluc channel in dual formats | As for Fluc |
| Protein-normalised specific activity | Luminescence divided by total protein in the same lysate (BCA or Bradford) | Specific activity = (RLU_sample − RLU_blank) / protein (mg) | 10⁶–10⁹ RLU/mg protein for a working formulation; protein per well 0.05–0.5 mg in a 96-well format | Protein content itself falls under LNP toxicity, which inflates the ratio. Lysis detergents interfere with BCA unless a compatible kit is used | Usually the final value; can still be expressed as fold over reference |
| Viability-normalised expression | Luminescence divided by a parallel viability measurement | RLU per viable cell = RLU_sample / viable cell count | 10⁰–10³ RLU per cell; relative viability above 80% of mock is the usual acceptance threshold | CellTiter-Glo is itself luminescent — run it in separate parallel wells, never the same well. Metabolic assays conflate fewer cells with less active cells | Fold over reference LNP at matched dose |
| mRNA-normalised expression | Luminescence divided by delivered reporter mRNA measured by RT-qPCR or ddPCR on the same wells | TE = RLU / mRNA copies per cell | 10²–10⁵ mRNA copies per cell after a standard dose; TE spans 1–20 fold across formulations | Measures total cell-associated mRNA, including mRNA still trapped in endosomes, so it understates true cytosolic translation efficiency | Fold over reference; log₂ for modelling |
| Uptake-normalised (endosomal escape) | Luminescence divided by internalised labelled mRNA or lipid signal | Escape index = RLU / internalised cargo signal | Escape fraction is typically 1–4% of internalised cargo, so the index is small and its spread across formulations is wide | Surface-bound particles count as internalised unless the extracellular signal is quenched or the cells are trypsin-stripped | Fold over reference |
| Secreted luciferase (Gaussia, Cypridina) | Supernatant sampled repeatedly; reporter accumulates in the medium | Cumulative = Σ (RLU_t × dilution factor), corrected for volume removed | 10⁴–10⁷ RLU per 10–20 µL of medium; signal rises for 24–72 h then plateaus | Flash kinetics require injectors; the sampling schedule is part of the measurement; medium pH and serum affect activity | Area under the curve, then fold over reference |
| Live-cell kinetic luciferase | Cell-permeable luciferin left in the medium, plate read repeatedly | AUC = ∫ RLU dt, by trapezoid over the read series | Peak between 6 and 24 h for mRNA LNP; AUC 10⁶–10⁹ RLU·h | ATP-dependent and substrate-depleting over long runs; separates kinetics from magnitude, which an endpoint cannot | AUC per mg protein or per viable cell |
| Dose–response / in vitro potency | Luminescence across an mRNA dose series | EC₅₀ from a four-parameter logistic fit of log(dose) vs RLU | EC₅₀ roughly 1–100 ng mRNA per well in a 96-well format; Hill slope usually 0.8–2 | A single dose can rank LNPs incorrectly because curves cross; the top plateau may be set by toxicity rather than biology | Relative potency = EC₅₀_reference / EC₅₀_test |

The four-parameter logistic used for the dose–response fit:

```latex
Y = \text{Bottom} + \frac{\text{Top} - \text{Bottom}}{1 + \left(\frac{EC_{50}}{X}\right)^{H}}
```

where X is mRNA dose, Y is luminescence and H is the Hill slope.

## In vivo assays

| Assay | Definition | Formula | Typical range (approximate) | Caveat | Post-normalisation |
| --- | --- | --- | --- | --- | --- |
| Whole-animal BLI (IVIS) | Luciferin injected (commonly 150 mg/kg IP), animal imaged in a cooled CCD chamber, photons counted in a region of interest | Total flux (photons/s) summed over the ROI; radiance = p/s/cm²/sr | Background 10⁴–10⁵ p/s; liver signal after 0.5 mg/kg IV mRNA LNP 10⁸–10¹⁰ p/s; extrahepatic tissues 10⁶–10⁸ p/s | Depth attenuation means a liver and a muscle signal of equal magnitude are not equal expression; fur, pigmentation, anaesthesia depth, luciferin dose and the delay to imaging all shift the value | Background-subtracted flux, then fold over a benchmark LNP imaged in the same session |
| Kinetic BLI series | Repeated imaging of the same animal over hours or days | AUC = ∫ flux dt over the time series | Peak at 4–6 h after IV dosing, back to background by 48–72 h; AUC 10⁹–10¹¹ p/s·h | Luciferin pharmacokinetics differ between tissues, so peak time is organ-dependent; repeated anaesthesia has cumulative effects | AUC per mg/kg mRNA dose |
| Ex vivo organ BLI | Organs excised after luciferin administration and imaged individually | Flux per organ (p/s); biodistribution % = flux_organ / Σ flux_all organs × 100 | Liver typically 70–95% of total flux for a conventional LNP; spleen 1–20%; lung under 5% unless the formulation is lung-targeted | Time between cull and imaging matters because signal decays; the percentage is compositional, so a rise in one organ mathematically lowers the others | Percentage of total flux, or flux per gram of tissue |
| Tissue homogenate luciferase assay | Organ homogenised, lysate assayed on a luminometer | RLU per mg tissue, or RLU / protein (mg) by BCA | 10⁵–10⁹ RLU/mg protein in liver; 10³–10⁵ in off-target organs; untreated tissue 10²–10³ | Avoids depth attenuation and is the quantitative reference method, but it is terminal and gives one timepoint per animal | Per mg protein, then fold over benchmark |
| Dose–response / in vivo potency | BLI flux across an mRNA dose series | ED₅₀ from a four-parameter logistic fit of log(dose) vs flux | ED₅₀ roughly 0.01–0.3 mg/kg for hepatic expression with a current-generation ionisable lipid | Inter-animal variability is large, so groups below 4–5 give unstable fits; the top plateau may be set by tolerability | Relative potency vs benchmark |
| Benchmark-relative potency | Test LNP compared to a standard ionisable lipid (MC3, ALC-0315, SM-102) in the same experiment | Fold = flux_test / flux_benchmark | 0.1–10 fold is the usual span; above 10 fold over MC3 is a strong claim and warrants a dose–response | Only meaningful when the benchmark ran contemporaneously, at the same dose, route and timepoint | This is itself the normalised value — the most portable in vivo metric |
| Organ selectivity (SORT-type) | Ratio of expression in a target organ to another organ | Selectivity = flux_target / flux_liver | Below 0.1 for conventional LNPs; 1–10 or higher for deliberately retargeted formulations | Ratios are stable to overall dose but hide whether absolute expression rose or the liver signal simply fell | Report alongside absolute flux, never alone |

**Inter-animal variability.** Expect a CV of 30–100% on BLI flux within a dose group. A two-fold difference between formulations with n = 3 is usually not significant; three to five fold with n = 5 generally is.

## Background floors and detection limits

A range is meaningless without its floor. Define the floor from your own controls on every plate or imaging session, using:

```latex
\mathrm{LOD} = \mu_{\text{background}} + 3\,\sigma_{\text{background}}
\qquad
\mathrm{LOQ} = \mu_{\text{background}} + 10\,\sigma_{\text{background}}
```

| Assay | Background source | Typical floor | What sets it |
| --- | --- | --- | --- |
| Fluc lysate | Mock-transfected lysate + substrate | 10²–10³ RLU | Substrate autoluminescence and detector dark counts |
| NanoLuc | Mock lysate + furimazine | 10³–10⁴ RLU | Furimazine autoluminescence, which is higher than luciferin's |
| Secreted luciferase | Conditioned medium from mock wells | 10³–10⁴ RLU | Serum components and medium pH |
| Whole-animal BLI | Untreated animal, same session and exposure | 10⁴–10⁵ p/s | Chamber stray light, CCD dark current, animal chow autofluorescence |
| Ex vivo organ BLI | Organ from an untreated animal | 10⁴ p/s per organ | Same, plus residual blood |
| Tissue homogenate | Homogenate from an untreated animal | 10²–10³ RLU/mg protein | Endogenous ATP and substrate background |

Two practical consequences. First, a formulation reading within 3 SD of mock has not been shown to work, whatever the fold number looks like after dividing by a small background. Second, fold changes calculated against a near-zero denominator are unstable — subtract background before dividing, never after, and report the raw background value so a reader can check it.

**Saturation at the top.** Photomultipliers saturate, usually somewhere above 10⁷–10⁸ RLU depending on the instrument. A set of strong formulations that all read the same value is more likely saturated than equipotent; dilute the lysate or lower the gain and re-read before concluding anything.

## Which metric travels between studies

In descending order of portability:

1. **Relative potency against a contemporaneous benchmark lipid** — the only in vivo number that survives a change of imaging system. Range 0.1–10 fold.
2. **Fold change over a reference construct or formulation in the same experiment** — range 1–100 fold in vitro, 1–10 fold in vivo.
3. **Protein- or mRNA-normalised specific activity** — comparable within a lab, roughly comparable between labs using the same readout and instrument class.
4. **Organ selectivity ratios** — dimensionless and reasonably portable, but they hide absolute magnitude.
5. **Raw total flux or RLU** — not portable at all.

For a pooled modelling dataset, record which tier each value came from. Mixing tier 1 and tier 5 values in one continuous target is the most common way these datasets go wrong.
