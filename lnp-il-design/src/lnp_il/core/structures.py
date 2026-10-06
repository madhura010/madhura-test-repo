"""Structure standardization shared by every source."""

import pandas as pd
from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize

rdBase.DisableLog("rdApp.*")


def standardize_smiles(smiles: str) -> tuple[str, str] | None:
    """Return (canonical isomeric SMILES, InChIKey) for the largest fragment, or None if invalid."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    mol = rdMolStandardize.LargestFragmentChooser().choose(mol)
    return Chem.MolToSmiles(mol), Chem.MolToInchiKey(mol)


def add_standard_structures(table: pd.DataFrame) -> pd.DataFrame:
    """Add il_smiles and il_inchikey from il_smiles_raw; drop rows that cannot be parsed.

    Rows with a missing il_smiles_raw are dropped too.
    """
    cache = {s: standardize_smiles(s) for s in table["il_smiles_raw"].dropna().unique()}
    parsed = table["il_smiles_raw"].map(cache)
    ok = parsed.notna()
    out = table.loc[ok].copy()
    out["il_smiles"] = parsed[ok].map(lambda pair: pair[0])
    out["il_inchikey"] = parsed[ok].map(lambda pair: pair[1])
    return out.drop(columns="il_smiles_raw")
