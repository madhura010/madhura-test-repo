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
        elif topo in ("", "-"):
            review.append("membrane-side accessibility has no UniProt topology annotation")

        subcell = row.get("subcellular_location", "").lower()
        if "cytoplasm" in subcell or "nucleus" in subcell:
            exclusions.append("subcellular location indicates cytosolic/nuclear compartment (inaccessible)")
        if row.get("glycosylation_count_near_site") not in ("", "0"):
            review.append("nearby glycosylation annotation")
        if row.get("modified_residue_count_near_site") not in ("", "0"):
            review.append("nearby non-glycan modified-residue annotation")
        if row.get("disulfide_overlap") == "true":
            review.append("overlaps a disulfide bond")

        ss_p1, ss_p1prime = row.get("ss_p1", ""), row.get("ss_p1prime", "")
        if ss_p1 in ("H", "E") or ss_p1prime in ("H", "E"):
            review.append("P1/P1' bond falls within a predicted helix/strand rather than coil/loop")

        # Heuristic cutoff on CA atoms within 8 A of the window; not
        # experimentally calibrated. Revisit once experimental cleavage
        # outcomes are available to validate a proper threshold.
        contact_density = row.get("contact_density_8a", "")
        if contact_density.isdigit() and int(contact_density) >= 20:
            review.append(f"elevated local contact density ({contact_density} CA atoms within 8 Å; possible steric burial)")

        if row.get("exposure_robustness", "").startswith("Low"):
            review.append("exposure robustness is Low (low-confidence AlphaFold region or possible interface)")

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
        out.append(row | {"analysis_status": status, "exclusion_reason": " | ".join(exclusions) or "-", "review_reason": " | ".join(review) or "-"})
    order = {"ELIGIBLE": 0, "REVIEW": 1, "EXCLUDE": 2}
    out.sort(key=lambda row: (order[row["analysis_status"]], -probability(row), row.get("source_id", "")))
    fields = list(rows[0].keys()) + ["analysis_status", "exclusion_reason", "review_reason"] if rows else []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader(); writer.writerows(out)
    print(f"Wrote {len(out)} analysed site rows to {args.output}")


if __name__ == "__main__":
    main()
