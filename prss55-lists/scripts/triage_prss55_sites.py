#!/usr/bin/env python3
"""Create an auditable PRSS55 candidate shortlist from extracted site features.

This is a deterministic analysis step, not a fitted or retrained model. It
filters structural incompatibilities, records unresolved evidence, and ranks the
remaining candidates only by the supplied upstream cleavage probability.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def probability(row):
    try:
        return float(row["model_score"])
    except (KeyError, TypeError, ValueError):
        return float("-inf")


# Terms that mark a location as plausibly reaching a surface-anchored
# ectoenzyme's compartment (extracellular fluid, cell surface). If any of
# these appear, the location is never treated as inaccessible, even
# alongside an organelle term below -- a protein annotated across multiple
# trafficking stages may still have a secreted/surface pool.
ACCESSIBLE_MARKERS = ("secreted", "cell membrane", "cell surface", "extracellular", "acrosome")

# Unambiguous intracellular compartments with no route to the extracellular
# space short of cell lysis -- hard exclusion.
INACCESSIBLE_PREFIXES = ("nucleus", "chromosome", "mitochondri", "peroxisom")

# Secretory-pathway compartments a protein may only be transiting through on
# its way to secretion or the surface -- a REVIEW flag, not an exclusion.
SECRETORY_PATHWAY_MARKERS = ("golgi", "endoplasmic reticulum", "lysosom")


def subcellular_verdict(subcell_raw):
    """Classify a UniProt subcellular_location string against PRSS55 accessibility.

    Matches per semicolon-separated location term, not the raw string --
    a naive substring check on "cytoplasm" also matches "Cytoplasmic
    vesicle, secretory vesicle, acrosome", which is a distinct membrane-bound
    compartment, not bulk cytosol.
    """
    terms = [t.strip() for t in subcell_raw.lower().split(";") if t.strip()]
    if any(marker in term for term in terms for marker in ACCESSIBLE_MARKERS):
        return None, None
    for term in terms:
        if term == "cytoplasm" or term.startswith("cytoplasm,") or term.startswith(INACCESSIBLE_PREFIXES):
            return f"subcellular location indicates an intracellular compartment inaccessible to a surface-anchored protease ({term})", None
    for term in terms:
        if any(marker in term for marker in SECRETORY_PATHWAY_MARKERS):
            return None, f"subcellular location ({term}) is a secretory-pathway compartment with no Secreted/surface annotation; confirm the site's trafficking destination"
    return None, None


SOLUBLE_MARKERS = ("secreted", "extracellular", "acrosome")


def has_no_membrane_topology_question(subcell_raw):
    """True when subcellular_location indicates a purely soluble/secreted protein
    with no membrane term anywhere. Such a protein never crosses a membrane, so
    it has no cytoplasmic-vs-extracellular sidedness for UniProt to annotate --
    a missing Topological domain feature there is expected, not a genuine gap.
    A protein that is secreted *and* membrane-associated (e.g. a shed
    ectodomain) still has a real sidedness question, so any membrane term
    keeps this False.
    """
    terms = [t.strip() for t in subcell_raw.lower().split(";") if t.strip()]
    if not terms:
        return False
    has_soluble = any(any(marker in term for marker in SOLUBLE_MARKERS) for term in terms)
    has_membrane = any("membrane" in term for term in terms)
    return has_soluble and not has_membrane


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--features", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    with args.features.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    out = []
    for row in rows:
        exclusions, review = [], []
        if row.get("sequence_verified") != "true":
            exclusions.append("8-mer does not match the retrieved UniProt sequence")
        if row.get("transmembrane_overlap") not in ("", "-"):
            exclusions.append("overlaps a transmembrane/intramembrane annotation")
        if row.get("processing_overlap") not in ("", "-"):
            exclusions.append("overlaps a sequence-processing annotation")
        topo = row.get("topology_annotations", "").lower()
        if "cytoplasmic" in topo:
            exclusions.append("overlaps a cytoplasmic topology annotation (inaccessible to PRSS55)")
        elif topo in ("", "-") and not has_no_membrane_topology_question(row.get("subcellular_location", "")):
            review.append("membrane-side accessibility has no UniProt topology annotation")

        subcell_exclusion, subcell_review = subcellular_verdict(row.get("subcellular_location", ""))
        if subcell_exclusion:
            exclusions.append(subcell_exclusion)
        if subcell_review:
            review.append(subcell_review)
        if row.get("glycosylation_count_near_site") not in ("", "0"):
            review.append("nearby glycosylation annotation")
        if row.get("modified_residue_count_near_site") not in ("", "0"):
            review.append("nearby non-glycan modified-residue annotation")
        if row.get("disulfide_overlap") == "true":
            review.append("overlaps a disulfide bond")

        ss_p1, ss_p1prime = row.get("ss_p1", ""), row.get("ss_p1prime", "")
        if ss_p1 in ("H", "E") or ss_p1prime in ("H", "E"):
            review.append("P1/P1' bond falls within a predicted helix/strand rather than coil/loop")

        # Proline at P1' is a distinct, localized mechanistic concern -- no
        # backbone N-H for the oxyanion hole, an elevated cis-bond population,
        # and steric bulk in the enzyme's S1' subsite -- independent of
        # whether the surrounding window is otherwise disordered (a Pro
        # elsewhere in the window can even favor coil/loop character, which
        # is why window-level proline is reported separately and not treated
        # as unfavorable on its own). Kept in its own review-pro column, not
        # just folded into review_reason, so it can be filtered on its own.
        pro_flags = []
        if row.get("p1prime_is_proline") == "true":
            pro_flags.append("Proline at P1' -- mechanistically disfavored for serine-protease catalysis (no backbone N-H, elevated cis-bond population); general serine-protease-family observation, not confirmed for PRSS55")
        if row.get("proline_in_window") == "true":
            pro_flags.append("proline present in the 8-mer window -- context-dependent (may promote local disorder); confirm manually")
        review.extend(pro_flags)

        # Sanity check on the P1-offset convention: nothing upstream verifies
        # that P1 is actually compatible with PRSS55's trypsin-like S1 pocket
        # (basic: Arg/Lys) or at least a residue that won't itself lock the
        # local backbone into rigid helix/strand geometry (Chou-Fasman
        # coil/turn formers: Gly/Ser/Asn/Asp). Kept as two independent
        # criteria -- p1_is_basic and p1_is_coil_favoring -- rather than one
        # merged column, so each can be inspected/filtered on its own; the
        # review-p1 flag only fires when a row fails both.
        p1_flags = []
        p1_basic, p1_coil_favoring = row.get("p1_is_basic", ""), row.get("p1_is_coil_favoring", "")
        if p1_basic == "false" and p1_coil_favoring == "false":
            p1_flags.append("P1 residue is neither basic (Arg/Lys) nor a coil-favoring small residue (Gly/Ser/Asn/Asp) -- contradicts the dataset's central-residue convention; verify the offset/site mapping for this row")
        review.extend(p1_flags)

        # CA-CA proxy for an intramolecular salt bridge (see SALT_BRIDGE_RADIUS
        # in extract_prss55_site_features.py) -- a charged P1/P1' side chain
        # already paired with an opposite charge in the folded substrate is
        # less available to engage the protease's S1 pocket, even if the
        # residue's window-level RSA reads as exposed.
        p1_partner = row.get("p1_salt_bridge_partner", "")
        if p1_partner not in ("", "-"):
            review.append(f"P1 residue may be intramolecularly salt-bridged (partner residue {p1_partner})")
        p1prime_partner = row.get("p1prime_salt_bridge_partner", "")
        if p1prime_partner not in ("", "-"):
            review.append(f"P1' residue may be intramolecularly salt-bridged (partner residue {p1prime_partner})")

        # Heuristic cutoff on CA atoms within 8 A of the window; not
        # experimentally calibrated. Revisit once experimental cleavage
        # outcomes are available to validate a proper threshold.
        contact_density = row.get("contact_density_8a", "")
        if contact_density.isdigit() and int(contact_density) >= 20:
            review.append(f"elevated local contact density ({contact_density} CA atoms within 8 Å; possible steric burial)")

        if row.get("plddt_confidence", "").startswith("Low"):
            review.append("pLDDT confidence is Low (low-confidence AlphaFold region); does not by itself mean buried -- check rsa_window_mean/rsa_window_min")

        if row.get("has_multiple_isoforms") == "true":
            review.append("protein has multiple annotated isoforms; confirm the site is present in the isoform used for testing")

        if row.get("domain_annotations") not in ("", "-"):
            review.append(f"overlaps an annotated domain/motif/region: {row['domain_annotations']}")

        if row.get("evidence_gaps") not in ("", "-"):
            review.append(row["evidence_gaps"])
        if not row.get("p1_position"):
            review.append("exact P1–P1′ bond unresolved; only window-level accessibility can be interpreted")
        if exclusions:
            status = "EXCLUDE"
        elif review:
            status = "REVIEW"
        else:
            status = "ELIGIBLE"
        out.append(row | {"analysis_status": status, "exclusion_reason": " | ".join(exclusions) or "-", "review_reason": " | ".join(review) or "-", "review-pro": " | ".join(pro_flags) or "-", "review-p1": " | ".join(p1_flags) or "-"})
    order = {"ELIGIBLE": 0, "REVIEW": 1, "EXCLUDE": 2}
    out.sort(key=lambda row: (order[row["analysis_status"]], -probability(row), row.get("source_id", "")))
    fields = list(rows[0].keys()) + ["analysis_status", "exclusion_reason", "review_reason", "review-pro", "review-p1"] if rows else []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader(); writer.writerows(out)
    print(f"Wrote {len(out)} analysed site rows to {args.output}")


if __name__ == "__main__":
    main()
