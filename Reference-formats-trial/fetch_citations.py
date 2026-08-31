import urllib.request
import json
import urllib.parse
import sys
import argparse

def fetch_europepmc(pmcid):
    """Fetch metadata from Europe PMC for PMC IDs."""
    url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmcid}&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': 'Python Citation Fetcher/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            results = data.get('resultList', {}).get('result', [])
            if results:
                r = results[0]
                authors = r.get('authorString', '').split(', ')
                return {
                    'title': r.get('title'),
                    'authors': authors,
                    'year': r.get('pubYear'),
                    'venue': r.get('journalTitle'),
                    'doi': f"https://doi.org/{r.get('doi')}" if r.get('doi') else '',
                    'query': pmcid
                }
    except Exception as e:
        print(f"Error fetching {pmcid} from EuropePMC: {e}", file=sys.stderr)
    return None

def fetch_openalex(query):
    """Fetch metadata from OpenAlex for DOIs."""
    url = f'https://api.openalex.org/works/{query}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Python Citation Fetcher/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            authors = [a['author']['display_name'] for a in data.get('authorships', []) if 'author' in a]
            venue = data.get('primary_location', {}).get('source', {}).get('display_name') if data.get('primary_location') and data.get('primary_location').get('source') else ''
            
            return {
                'title': data.get('title'),
                'authors': authors,
                'year': data.get('publication_year'),
                'venue': venue,
                'doi': data.get('doi'),
                'query': query
            }
    except Exception as e:
        print(f"Error fetching {query} from OpenAlex: {e}", file=sys.stderr)
    return None

def fetch_crossref_title(title):
    """Fetch metadata from Crossref for Title searches (more robust than OpenAlex)."""
    encoded_title = urllib.parse.quote(title)
    url = f'https://api.crossref.org/works?query.title={encoded_title}&select=title,author,issued,container-title,DOI&rows=1'
    req = urllib.request.Request(url, headers={'User-Agent': 'Python Citation Fetcher/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            items = data.get('message', {}).get('items', [])
            if not items:
                return None
            
            item = items[0]
            authors = []
            for a in item.get('author', []):
                given = a.get('given', '')
                family = a.get('family', '')
                authors.append(f"{family}, {given}".strip(', '))
                
            issued = item.get('issued', {}).get('date-parts', [[None]])
            year = issued[0][0] if issued and issued[0] else 'n.d.'
            
            return {
                'title': item.get('title', [''])[0],
                'authors': authors,
                'year': year,
                'venue': item.get('container-title', [''])[0],
                'doi': f"https://doi.org/{item.get('DOI', '')}" if item.get('DOI') else '',
                'query': title
            }
    except Exception as e:
        print(f"Error fetching {title} from Crossref: {e}", file=sys.stderr)
    return None

def format_apa(data):
    """Format the metadata into APA style including ALL authors."""
    if not data: return "Could not generate citation."
    
    authors = data['authors']
    if len(authors) == 0:
        auth_str = "Unknown Authors"
    elif len(authors) == 1:
        auth_str = authors[0]
    elif len(authors) == 2:
        auth_str = f"{authors[0]} & {authors[1]}"
    else:
        # Full citation includes all authors separated by commas, with & before the last
        auth_str = ", ".join(authors[:-1]) + f", & {authors[-1]}"
        
    year = data.get('year', 'n.d.')
    title = data.get('title', 'Unknown Title')
    venue = data.get('venue', 'Unknown Venue')
    doi = data.get('doi', '')
    
    return f"{auth_str} ({year}). {title}. {venue}. {doi}"

def format_inline(data):
    """Format the metadata into an APA short inline citation."""
    if not data: return ""
    authors = data['authors']
    year = data.get('year', 'n.d.')
    
    if len(authors) == 0:
        return f"(Unknown, {year})"
    
    if len(authors) == 1:
        last_name = authors[0].split(',')[0].split()[-1]
        return f"({last_name}, {year})"
    elif len(authors) == 2:
        last_name1 = authors[0].split(',')[0].split()[-1]
        last_name2 = authors[1].split(',')[0].split()[-1]
        return f"({last_name1} & {last_name2}, {year})"
    else:
        last_name = authors[0].split(',')[0].split()[-1]
        return f"({last_name} et al., {year})"

def main():
    parser = argparse.ArgumentParser(description="Fetch and format citations from DOIs, PMC links, or Titles.")
    parser.add_argument('inputs', nargs='*', help="List of URLs or titles to process")
    parser.add_argument('-f', '--file', help="Text file containing one URL/Title per line")
    
    args = parser.parse_args()
    
    queries = args.inputs
    if args.file:
        with open(args.file, 'r') as f:
            queries.extend([line.strip() for line in f if line.strip()])
            
    if not queries:
        print("Please provide at least one URL or Title, or use a file input (-f).")
        sys.exit(1)

    print("Fetching citations...\n")
    for i, query in enumerate(queries, 1):
        if 'PMC' in query and 'nih.gov' in query:
            pmcid = [part for part in query.split('/') if part.startswith('PMC')]
            data = fetch_europepmc(pmcid[0]) if pmcid else None
        elif query.startswith('http') and 'doi.org' in query:
            data = fetch_openalex(query)
        else:
            # If it's not a standard URL, treat it as a title search using Crossref
            data = fetch_crossref_title(query)
            
        if data:
            full_cit = format_apa(data)
            inline_cit = format_inline(data)
            print(f"{i}. {full_cit}")
            print(f"   Inline: {inline_cit}\n")
        else:
            print(f"{i}. Failed to retrieve data for: {query}\n")

if __name__ == '__main__':
    main()
