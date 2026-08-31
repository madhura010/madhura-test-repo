# Citation Fetcher (`fetch_citations.py`)

A simple, standalone Python command-line tool that automatically converts a list of URLs (DOIs, PubMed Central links) or **paper titles** into properly formatted **APA 7th Edition** references and provides **short inline citations**.

It relies purely on Python's built-in standard libraries (`urllib`, `json`), meaning **no installation via pip is required**. It intelligently routes queries to the most appropriate free academic API:
- [OpenAlex](https://openalex.org/) (for DOIs)
- [Crossref](https://crossref.org/) (for robust Paper Title searches)
- [Europe PMC](https://europepmc.org/) (for PubMed Central IDs)

## Features
- **URL Support**: Handles direct DOI URLs and PMC links.
- **Title Search**: You can paste the exact title of a paper, and it will search Crossref to find the correct metadata.
- **All Authors**: The full citation output includes *all* authors, regardless of how many there are (no "et al." in the bibliography).
- **Inline Citation**: Provides a standard short-form inline citation (e.g., `(Hunter et al., 2025)`).

## Usage

### 1. Pass URLs or Titles directly via Command Line
You can pass single or multiple links/titles separated by spaces. If passing a paper title with spaces, be sure to wrap it in quotes.

```bash
python3 fetch_citations.py "https://doi.org/10.1126/science.ads8473" "Artificial intelligence in the rational design of lipid nanoparticles for mRNA therapeutics"
```

**Output Example:**
```
1. Hunter, Theresa, Bao, Yanjie, Zhang, Yan, ... [all authors listed] & Aghajanian, Haig (2025). In vivo CAR T cell generation to treat cancer and autoimmune disease. Science. https://doi.org/10.1126/science.ads8473
   Inline: (Hunter et al., 2025)

2. Zhao, Heyu, Xu, Junchao, Gao, Xia, Zhu, Jingcheng, & He, Zhongshan (2026). Artificial intelligence in the rational design of lipid nanoparticles for mRNA therapeutics. The Innovation Drug Discovery. https://doi.org/10.59717/j.xinn-drugdisc.2026.100006
   Inline: (Zhao et al., 2026)
```

### 2. Read from a Text File
If you have a large list of links or titles, save them into a `.txt` file, with one entry per line.

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
