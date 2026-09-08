#!/usr/bin/env python3
"""Extract auditable, site-level features for predicted PRSS55 cleavage sites.

This script deliberately does not label sites as substrates or derive a cleavage
probability. It validates the input against UniProt, retrieves annotations, and
optionally computes AlphaFold-model-derived residue RSA using the installed
aganitha-uniprot-parser implementation.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
PARSER_PATH = ROOT / "skills" / "aganitha-uniprot-parser" / "scripts" / "fetch_uniprot.py"
OUTPUT_COLUMNS = (
    "source_id accession resolved_accession source_isoform site_start site_end eight_mer "
    "p1_position p1prime_position model_score sequence_verified protein_name gene_name has_multiple_isoforms "
    "processing_overlap mature_peptide_overlap chain_annotations transmembrane_overlap topology_annotations subcellular_location domain_annotations family_annotations "
    "glycosylation_count_near_site modified_residue_count_near_site disulfide_overlap rsa_p1 rsa_p1prime rsa_window_mean "
    "rsa_window_min plddt_window_mean contact_density_8a plddt_confidence ss_p1 ss_p1prime ss_window_pattern ss_helix_fraction ss_strand_fraction ss_loop_fraction "
    "p1_salt_bridge_partner p1prime_salt_bridge_partner proline_in_window p1prime_is_proline p1_is_basic p1_is_coil_favoring "
    "structure_source evidence_gaps warnings retrieved_at"
).split()

# Residues carrying a formal charge at physiological pH, for the intramolecular
# salt-bridge check below. Arg/Lys are positive; Asp/Glu are negative. His is
# left out -- its protonation state near pH 7 is too uncertain to treat as a
# reliable positive charge.
POSITIVE_RESIDUES = {"ARG", "LYS"}
NEGATIVE_RESIDUES = {"ASP", "GLU"}
# Chou-Fasman-classical coil/turn formers: empirically low helix AND low
# sheet propensity (high turn/coil propensity), not just small side-chain
# size. Proline is excluded -- it gets its own dedicated flag/column, since
# its mechanism (no backbone N-H, elevated cis-bond population) is a
# different, P1'-specific concern, not interchangeable with this P1 check.
COIL_FAVORING_RESIDUES = {"GLY", "SER", "ASN", "ASP"}
# eight_mer uses one-letter codes; POSITIVE_RESIDUES/COIL_FAVORING_RESIDUES use
# three-letter, to match the PDB-derived `residues` dict used elsewhere. Only
# the residues those two sets actually reference need an entry here.
ONE_TO_THREE = {"R": "ARG", "K": "LYS", "G": "GLY", "S": "SER", "N": "ASN", "D": "ASP"}
# CA-CA distance used as a proxy for salt-bridge proximity. A true salt bridge
# is a side-chain-atom contact (typically < 4 A between the charged groups),
# but only backbone CA coordinates are available here; a longer CA-CA radius
# is a deliberately generous envelope so an extended Arg side chain (which can
# reach several A past its own CA) is not missed. This over-calls some
# non-bridging proximity and under-calls bridges between residues whose side
# chains point away from each other -- a heuristic, not a validated geometric
# criterion, same status as contact_density_8a below. Sequence-adjacent
# residues (i, i+1) are excluded from the search entirely: their CA-CA
# distance is fixed at ~3.8 A by peptide-bond geometry regardless of real
# spatial proximity, so they would always trivially pass this radius check --
# see salt_bridge_partner().
SALT_BRIDGE_RADIUS = 8.0


def load_parser():
    if not PARSER_PATH.exists():
        raise RuntimeError(f"Required parser not found: {PARSER_PATH}")
    spec = importlib.util.spec_from_file_location("uniprot_parser", PARSER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def read_sites(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"accession", "site_start", "eight_mer", "model_score"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("Input requires columns: " + ", ".join(sorted(required)))
        for line, row in enumerate(reader, start=2):
            if not row.get("accession", "").strip() or row["accession"].lstrip().startswith("#"):
                continue
            try:
                start = int(row["site_start"])
                score = float(row["model_score"])
            except ValueError as exc:
                raise ValueError(f"Line {line}: site_start and model_score must be numeric") from exc
            offset_text = row.get("p1_offset", "").strip()
            try:
                offset = int(offset_text) if offset_text else None
            except ValueError as exc:
                raise ValueError(f"Line {line}: p1_offset must be blank or an integer 1..7") from exc
            peptide = row["eight_mer"].strip().upper()
            if start < 1 or (offset is not None and offset not in range(1, 8)) or len(peptide) != 8 or not peptide.isalpha():
                raise ValueError(f"Line {line}: require 1-based start, optional p1_offset 1..7, and an 8-aa sequence")
            yield line, {**row, "site_start": start, "p1_offset": offset, "model_score": score, "eight_mer": peptide}


def bounds(feature, parser):
    return parser.feature_bounds(feature)


def overlaps(start, end, feature, parser):
    left, right = bounds(feature, parser)
    return left is not None and left <= end and right >= start


def descriptions(features):
    """Keep the feature type when UniProt intentionally omits a description.

    A blank description for a Signal or Propeptide feature is still meaningful
    and must not be serialised as the same sentinel used for 'no overlap'.
    """
    labels = set()
    for feature in features:
        kind = feature.get("type", "Feature")
        detail = feature.get("description", "") or ""
        labels.add(f"{kind}: {detail}" if detail else kind)
    return "; ".join(sorted(labels)) or "-"


def plddt_by_residue(pdb_text: str):
    """Read AlphaFold pLDDT stored in CA-atom B factors; returns residue -> pLDDT."""
    values = {}
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        try:
            values[int(line[22:26])] = float(line[60:66])
        except ValueError:
            continue
    return values


def ca_coordinates(pdb_text: str):
    """Return CA coordinates to compute local contact density."""
    coords = {}
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        try:
            coords[int(line[22:26])] = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
        except ValueError:
            continue
    return coords


def residue_names(pdb_text: str):
    """Return three-letter residue codes by residue number, from CA atom lines."""
    names = {}
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        try:
            number = int(line[22:26])
        except ValueError:
            continue
        names[number] = line[17:20].strip()
    return names


def salt_bridge_partner(position, coords, residues):
    """Return the nearest oppositely-charged residue number within
    SALT_BRIDGE_RADIUS of `position`, or None if `position` isn't charged or
    has no such partner. See SALT_BRIDGE_RADIUS for the CA-CA proxy caveat."""
    charge = residues.get(position)
    if charge not in POSITIVE_RESIDUES and charge not in NEGATIVE_RESIDUES:
        return None
    if position not in coords:
        return None
    opposite = NEGATIVE_RESIDUES if charge in POSITIVE_RESIDUES else POSITIVE_RESIDUES
    x, y, z = coords[position]
    best_partner, best_dist2 = None, SALT_BRIDGE_RADIUS ** 2
    for other, (ox, oy, oz) in coords.items():
        # Sequence-adjacent residues have a CA-CA distance fixed at ~3.8 A by
        # peptide-bond geometry, regardless of conformation or real spatial
        # proximity -- that's always well inside SALT_BRIDGE_RADIUS, so an
        # immediate neighbor would trivially "pass" this check even with no
        # genuine side-chain interaction. Only a residue at least two
        # positions away carries real, conformation-dependent CA-CA distance
        # information.
        if abs(other - position) <= 1 or residues.get(other) not in opposite:
            continue
        dist2 = (x - ox) ** 2 + (y - oy) ** 2 + (z - oz) ** 2
        if dist2 <= best_dist2:
            best_partner, best_dist2 = other, dist2
    return best_partner


def secondary_structure_by_residue(pdb_text: str):
    """Assign C3 DSSP states from backbone coordinates with local PyDSSP.

    The output uses H (alpha helix), E (beta strand), and C (loop/other). This
    is a structure assignment for the selected AlphaFold model, not an
    experimentally observed ensemble or a sequence-only prediction.
    """
    vendor = ROOT / ".vendor"
    if str(vendor) not in sys.path:
        sys.path.insert(0, str(vendor))
    try:
        import pydssp
    except ImportError as exc:
        raise RuntimeError("PyDSSP unavailable; install project dependencies") from exc
    try:
        coordinates = pydssp.read_pdbtext(pdb_text)
        states = pydssp.assign(coordinates, out_type="c3")
    except (AssertionError, ValueError, IndexError) as exc:
        raise RuntimeError(f"PyDSSP assignment failed: {exc}") from exc
    residue_numbers, seen = [], set()
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "N":
            continue
        try:
            number = int(line[22:26])
        except ValueError:
            continue
        if number not in seen:
            residue_numbers.append(number); seen.add(number)
    if len(residue_numbers) != len(states):
        raise RuntimeError("PyDSSP residue count does not match PDB residue numbering")
    conversion = {"H": "H", "E": "E", "-": "C"}
    return {number: conversion.get(str(state), "C") for number, state in zip(residue_numbers, states)}


def family_annotations(entry):
    """Return curated InterPro/Pfam memberships without inventing coordinates."""
    labels = set()
    for ref in entry.get("uniProtKBCrossReferences", []):
        if ref.get("database") not in {"InterPro", "Pfam"}:
            continue
        name = next((p.get("value") for p in ref.get("properties", []) if p.get("key") == "EntryName"), "")
        labels.add(f"{ref['database']}: {name or ref.get('id', '-')}")
    return "; ".join(sorted(labels)) or "-"


def cached_entry(accession, parser, cache_dir: Path):
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{accession.upper()}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    entry = parser.entry_for(accession)
    cache_path.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return entry


def structural_features(accession, parser):
    """Return RSA/pLDDT/coords/residue-identity evidence. Failures are reported,
    never converted to zero exposure."""
    try:
        rsa, pdb_url = parser.alphafold_rsa(accession)
        pdb_text = parser.get(pdb_url, "text/plain")
        if "_atom_site." in pdb_text or "loop_" in pdb_text:
            raise RuntimeError("AlphaFold returned mmCIF format; PDB format required for current parsing")
        plddt = plddt_by_residue(pdb_text)
        secondary = secondary_structure_by_residue(pdb_text)
        coords = ca_coordinates(pdb_text)
        residues = residue_names(pdb_text)
        return rsa, plddt, secondary, coords, residues, pdb_url, None
    except RuntimeError as exc:
        return {}, {}, {}, {}, {}, "", str(exc)


def cached_structural_features(accession, parser, cache_dir: Path):
    """Structural evidence is per-protein, not per-site; cache it by accession so
    proteins with many candidate sites don't re-fetch AlphaFold and re-run PyDSSP
    once per site."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{accession.upper()}.json"
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if "residues" in cached:
            return (
                {int(k): v for k, v in cached["rsa"].items()},
                {int(k): v for k, v in cached["plddt"].items()},
                {int(k): v for k, v in cached["secondary"].items()},
                {int(k): tuple(v) for k, v in cached["coords"].items()},
                {int(k): v for k, v in cached["residues"].items()},
                cached["structure_source"], cached["structure_error"],
            )
        # Cache written before residue identities were added -- recompute and
        # overwrite rather than error on the missing key.
    rsa, plddt, secondary, coords, residues, structure_source, structure_error = structural_features(accession, parser)
    cache_path.write_text(json.dumps({
        "rsa": rsa, "plddt": plddt, "secondary": secondary,
        "coords": {k: list(v) for k, v in coords.items()},
        "residues": residues,
        "structure_source": structure_source, "structure_error": structure_error,
    }, sort_keys=True) + "\n", encoding="utf-8")
    return rsa, plddt, secondary, coords, residues, structure_source, structure_error


def feature_row(row, parser, cache_dir, structural_cache_dir, with_rsa):
    entry = cached_entry(row["accession"], parser, cache_dir)
    accession = entry["primaryAccession"]
    sequence = entry.get("sequence", {}).get("value", "")
    start, end = row["site_start"], row["site_start"] + 7
    offset = row["p1_offset"]
    p1 = start + offset - 1 if offset is not None else None
    p1prime = start + offset if offset is not None else None
    # Sequence-only checks -- no structural data needed, always available.
    proline_in_window = "true" if "P" in row["eight_mer"] else "false"
    p1prime_is_proline = "true" if offset is not None and row["eight_mer"][offset] == "P" else ("false" if offset is not None else "")
    # Sanity check on the P1-offset convention itself: this dataset assumes
    # every site's P1 is compatible with PRSS55's trypsin-like S1 pocket
    # (basic: Arg/Lys) or, short of that, at least a residue that won't
    # itself lock the local backbone into rigid helix/strand geometry
    # (Chou-Fasman coil/turn formers: Gly/Ser/Asn/Asp). Nothing upstream
    # verifies this per row. Kept as two separate columns, not one merged
    # boolean, so each criterion can be inspected/filtered independently.
    p1_is_basic, p1_is_coil_favoring = "", ""
    if offset is not None:
        p1_three = ONE_TO_THREE.get(row["eight_mer"][offset - 1])
        p1_is_basic = "true" if p1_three in POSITIVE_RESIDUES else "false"
        p1_is_coil_favoring = "true" if p1_three in COIL_FAVORING_RESIDUES else "false"
    warnings, gaps = [], []
    observed = sequence[start - 1:end] if end <= len(sequence) else ""
    verified = observed == row["eight_mer"]
    if not verified:
        warnings.append(f"sequence mismatch (UniProt has '{observed or 'out of range'}')")

    features = entry.get("features", [])
    by_type = lambda kinds: [f for f in features if f.get("type") in kinds and overlaps(start, end, f, parser)]
    # A UniProt `Chain` commonly spans the mature protein and must not be treated
    # as evidence that a site is removed by processing. Only features that can
    # remove or release the local sequence are used as a processing flag.
    processing = by_type({"Signal", "Propeptide", "Initiator methionine"})
    # `Peptide` is an annotated mature cleavage product. Its overlap supports
    # the existence of the local sequence; it does not mean the sequence was
    # removed and must never be used as an exclusion criterion.
    mature_peptide = by_type({"Peptide"})
    chain = by_type({"Chain"})
    membrane = by_type({"Transmembrane", "Intramembrane"})
    topology = by_type({"Topological domain"})
    domain = by_type({"Domain", "Region", "Repeat", "Motif", "Zinc finger", "Coiled coil"})
    disulfide = by_type({"Disulfide bond"})
    radius = 8
    glyco, modified = [], []
    for f in features:
        if f.get("type") not in {"Glycosylation", "Modified residue"}:
            continue
        left, right = bounds(f, parser)
        if left is not None and left <= end + radius and right >= start - radius:
            (glyco if f.get("type") == "Glycosylation" else modified).append(f)

    rsa, plddt, secondary, coords, residues, structure_source, structure_error = ({}, {}, {}, {}, {}, "", None)
    if with_rsa:
        rsa, plddt, secondary, coords, residues, structure_source, structure_error = cached_structural_features(accession, parser, structural_cache_dir)
        if structure_error:
            gaps.append("RSA/pLDDT unavailable: " + structure_error)
    else:
        gaps.append("RSA/pLDDT not requested; rerun with --with-rsa")
    window_rsa = [rsa[p] for p in range(start, end + 1) if p in rsa]
    window_plddt = [plddt[p] for p in range(start, end + 1) if p in plddt]
    window_ss = [secondary[p] for p in range(start, end + 1) if p in secondary]
    if with_rsa and len(window_rsa) != 8:
        gaps.append("incomplete structural coverage for 8-mer")
    if with_rsa and len(window_ss) != 8:
        gaps.append("incomplete secondary-structure coverage for 8-mer")
    protein = entry.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "-")
    genes = entry.get("genes", [])
    gene = genes[0].get("geneName", {}).get("value", "-") if genes else "-"
    locations = []
    for comment in entry.get("comments", []):
        if comment.get("commentType") == "SUBCELLULAR LOCATION":
            for sub_loc in comment.get("subcellularLocations", []):
                loc = sub_loc.get("location", {}).get("value")
                if loc:
                    locations.append(loc)
    subcellular_location = "; ".join(locations) or "-"

    window_coords = [coords[p] for p in range(start, end + 1) if p in coords]
    contact_count = 0
    if window_coords:
        for p, (x, y, z) in coords.items():
            if start <= p <= end:
                continue
            if any((x - wx)**2 + (y - wy)**2 + (z - wz)**2 <= 64.0 for wx, wy, wz in window_coords):
                contact_count += 1
    contact_density_8a = str(contact_count) if window_coords else ""

    p1_salt_bridge_partner = salt_bridge_partner(p1, coords, residues) if p1 else None
    p1prime_salt_bridge_partner = salt_bridge_partner(p1prime, coords, residues) if p1prime else None

    plddt_mean_val = mean(window_plddt) if window_plddt else None
    plddt_confidence = "Unknown"
    if plddt_mean_val is not None:
        plddt_confidence = "Medium (confident AlphaFold region)" if plddt_mean_val >= 70 else "Low (pLDDT < 70)"

    isoform_comments = [c for c in entry.get("comments", []) if c.get("commentType") == "ALTERNATIVE PRODUCTS"]
    has_multiple_isoforms = "true" if any(len(c.get("isoforms", [])) > 1 for c in isoform_comments) else "false"

    return {
        "source_id": row.get("source_id", "") or f"line_{row.get('_line', '')}",
        "accession": row["accession"], "resolved_accession": accession,
        "source_isoform": row.get("source_isoform", ""), "site_start": start, "site_end": end,
        "eight_mer": row["eight_mer"], "p1_position": p1 or "", "p1prime_position": p1prime or "",
        "model_score": row["model_score"], "sequence_verified": str(verified).lower(),
        "protein_name": protein, "gene_name": gene, "has_multiple_isoforms": has_multiple_isoforms,
        "processing_overlap": descriptions(processing),
        "mature_peptide_overlap": descriptions(mature_peptide),
        "chain_annotations": descriptions(chain),
        "transmembrane_overlap": descriptions(membrane), "topology_annotations": descriptions(topology),
        "subcellular_location": subcellular_location,
        "domain_annotations": descriptions(domain), "family_annotations": family_annotations(entry),
        "glycosylation_count_near_site": len(glyco),
        "modified_residue_count_near_site": len(modified),
        "disulfide_overlap": str(bool(disulfide)).lower(), "rsa_p1": rsa.get(p1, "") if p1 else "",
        "rsa_p1prime": rsa.get(p1prime, "") if p1prime else "",
        "rsa_window_mean": f"{mean(window_rsa):.3f}" if window_rsa else "",
        "rsa_window_min": f"{min(window_rsa):.3f}" if window_rsa else "",
        "plddt_window_mean": f"{mean(window_plddt):.3f}" if window_plddt else "",
        "contact_density_8a": contact_density_8a, "plddt_confidence": plddt_confidence,
        "ss_p1": secondary.get(p1, "") if p1 else "", "ss_p1prime": secondary.get(p1prime, "") if p1prime else "",
        "ss_window_pattern": "".join(window_ss) if len(window_ss) == 8 else "",
        "ss_helix_fraction": f"{window_ss.count('H') / len(window_ss):.3f}" if window_ss else "",
        "ss_strand_fraction": f"{window_ss.count('E') / len(window_ss):.3f}" if window_ss else "",
        "ss_loop_fraction": f"{window_ss.count('C') / len(window_ss):.3f}" if window_ss else "",
        "p1_salt_bridge_partner": p1_salt_bridge_partner or "",
        "p1prime_salt_bridge_partner": p1prime_salt_bridge_partner or "",
        "proline_in_window": proline_in_window, "p1prime_is_proline": p1prime_is_proline,
        "p1_is_basic": p1_is_basic, "p1_is_coil_favoring": p1_is_coil_favoring,
        "structure_source": structure_source, "evidence_gaps": " | ".join(gaps) or "-",
        "warnings": " | ".join(warnings) or "-", "retrieved_at": dt.date.today().isoformat(),
    }


def main():
    parser_args = argparse.ArgumentParser(description=__doc__)
    parser_args.add_argument("--input", required=True, type=Path, help="Predicted-site CSV; use data/prss55_predicted_sites.template.csv")
    parser_args.add_argument("--output", required=True, type=Path, help="Output TSV")
    parser_args.add_argument("--cache-dir", type=Path, default=ROOT / "cache" / "uniprot")
    parser_args.add_argument("--structural-cache-dir", type=Path, default=ROOT / "cache" / "structural",
                              help="Per-accession cache for AlphaFold/RSA/secondary-structure results, so proteins with multiple candidate sites are only fetched once")
    parser_args.add_argument("--with-rsa", action="store_true", help="Fetch AlphaFold models and compute RSA/pLDDT; slower")
    args = parser_args.parse_args()
    parser = load_parser()
    sites = list(read_sites(args.input))
    rows = []
    for i, (line, site) in enumerate(sites, start=1):
        site["_line"] = line
        print(f"[{i}/{len(sites)}] {site.get('accession', '')} {site.get('source_id', '')}", file=sys.stderr)
        try:
            rows.append(feature_row(site, parser, args.cache_dir, args.structural_cache_dir, args.with_rsa))
        except RuntimeError as exc:
            rows.append({column: "" for column in OUTPUT_COLUMNS} | {"source_id": site.get("source_id", f"line_{line}"), "accession": site["accession"], "warnings": str(exc), "evidence_gaps": "UniProt retrieval failed"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} site rows to {args.output}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
