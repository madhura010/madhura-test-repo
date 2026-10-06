# LNP-IL Design

A docking-and-triage funnel for ionizable lipids: it ranks known and newly proposed lipids by predicted mRNA transfection efficiency, with an uncertainty and a synthesis route on each, trained only on public data. It narrows what a wet lab should make. It does not claim what works.

## Using it

The project is in the design phase. Two commands work today. The first builds the curated dataset from LNPDB (clone it first, see below):

```bash
uv run lnp-il data curate --lnpdb-dir $LNPDB_DIR --out-dir data/curated
uv run lnp-il data atlas --atlas-csv $ATLAS_CSV --lnpdb-dir $LNPDB_DIR --out-dir data/curated
```

The second command adds structures from LNP Atlas (CC BY 4.0, [Zenodo 17243732](https://doi.org/10.5281/zenodo.17243732)). Atlas has no usable activity label.

What exists today:

- `docs/vision.md`: who it serves and the gates it must pass.
- `docs/design.md`: the proposed modules and decisions, with open questions marked.
- `docs/data-sources.md`: the public datasets and how they overlap.

When the pipeline exists, its output is a shortlist table (ranked candidates, controls, uncertainty, nearest training lipids, synthesis route) for a partner to synthesize and screen.

## Developing it

```bash
make install   # uv sync
make test
make help      # all targets
```

Map in `AGENTS.md`, decisions in `docs/design.md`, state and next steps in `docs/status.md`.

The data is not in this repo. Clone LNPDB (MIT code; check the data terms) next to this folder and point `LNPDB_DIR` at the clone:

```bash
git clone https://github.com/evancollins1/LNPDB.git ../LNPDB
export LNPDB_DIR=$PWD/../LNPDB
```

For the `atlas` command, download the LNP Atlas CSV (CC BY 4.0) and point `ATLAS_CSV` at it. The file is EUC-KR text, which the command handles:

```bash
curl -L -o ../LNP_Atlas_DB_202509_v1.csv \
  https://zenodo.org/api/records/17243733/files/LNP_Atlas_DB_202509_v1.csv/content
export ATLAS_CSV=$PWD/../LNP_Atlas_DB_202509_v1.csv
```
