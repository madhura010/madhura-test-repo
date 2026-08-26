# Citation Fetcher (`fetch_citations.py`)

A simple, standalone Python command-line tool that automatically converts a list of URLs (DOIs, PubMed Central links) or paper titles into properly formatted **APA 7th Edition** references and provides **inline citations**.

It relies purely on Python's built-in standard libraries (`urllib`, `json`), meaning **no installation via pip is required**. It queries the open and free [OpenAlex API](https://openalex.org/) and the [Europe PMC API](https://europepmc.org/).

## Features
- Handles direct DOI URLs (e.g., `https://doi.org/10.1126/science.ads8473`)
- Handles PubMed Central URLs (e.g., `https://pmc.ncbi.nlm.nih.gov/articles/PMC8862159/`)
- Can search by the exact Title of the paper.
- Outputs a full APA-style reference.
- Outputs a short-form inline citation (e.g., `(Hunter et al., 2025)`).

## Usage

### 1. Pass URLs or Titles directly via Command Line
You can pass single or multiple links/titles separated by spaces. (If passing titles with spaces, be sure to wrap them in quotes).

```bash
python3 fetch_citations.py "https://doi.org/10.1126/science.ads8473" "https://pmc.ncbi.nlm.nih.gov/articles/PMC8862159/"
```
**Output Example:**
```
1. Theresa Hunter et al. (2025). In vivo CAR T cell generation to treat cancer and autoimmune disease. Science. https://doi.org/10.1126/science.ads8473
   Inline: (Hunter et al., 2025)

2. Patel R et al. (2022). A comprehensive review of SARS-CoV-2 vaccines: Pfizer, Moderna & Johnson & Johnson.. Hum Vaccin Immunother. https://doi.org/10.1080/21645515.2021.2002083
   Inline: (R et al., 2022)
```

### 2. Read from a Text File
If you have a large list of links, save them into a `.txt` file, with one link or title per line.

**`links.txt`**
```
https://doi.org/10.1126/science.ads8473
https://pmc.ncbi.nlm.nih.gov/articles/PMC8862159/
The 60-year evolution of lipid nanoparticles for nucleic acid delivery
```

Then run:
```bash
python3 fetch_citations.py -f links.txt
```

## Requirements
- Python 3.6+
- Active internet connection (to reach APIs)
