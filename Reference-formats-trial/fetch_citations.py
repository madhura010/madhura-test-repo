import urllib.request
import json
import urllib.parse
import sys
import argparse

def fetch_europepmc(pmcid):
    """Fetch metadata from Europe PMC for PMC IDs."""
    url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmcid}&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': 'Python Citation Fetcher'})
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
    """Fetch metadata from OpenAlex for DOIs or Titles."""
    if query.startswith('http') and 'doi.org' in query:
        url = f'https://api.openalex.org/works/{query}'
    else:
        encoded_title = urllib.parse.quote(query)
        url = f'https://api.openalex.org/works?filter=title.search:{encoded_title}'
        
    req = urllib.request.Request(url, headers={'User-Agent': 'Python Citation Fetcher'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
            if 'results' in data:
                if len(data['results']) > 0:
                    item = data['results'][0]
                else:
                    return None
            else:
                item = data
                
            authors = [a['author']['display_name'] for a in item.get('authorships', []) if 'author' in a]
            venue = item.get('primary_location', {}).get('source', {}).get('display_name') if item.get('primary_location') and item.get('primary_location').get('source') else ''
            
            return {
                'title': item.get('title'),
                'authors': authors,
                'year': item.get('publication_year'),
                'venue': venue,
                'doi': item.get('doi'),
                'query': query
            }
    except Exception as e:
        print(f"Error fetching {query} from OpenAlex: {e}", file=sys.stderr)
    return None

def format_apa(data):
    """Format the metadata into APA 7th Edition style."""
    if not data: return "Could not generate citation."
    
    authors = data['authors']
    if len(authors) == 1:
        auth_str = authors[0]
    elif len(authors) == 2:
        auth_str = f"{authors[0]}, & {authors[1]}"
    elif len(authors) > 2:
        # Simplified APA for script output: First Author et al., if more than 2 (or full list up to 20 for true APA)
        auth_str = f"{authors[0]} et al."
    else:
        auth_str = "Unknown Authors"
        
    year = data.get('year', 'n.d.')
    title = data.get('title', 'Unknown Title')
    venue = data.get('venue', 'Unknown Venue')
    doi = data.get('doi', '')
    
    return f"{auth_str} ({year}). {title}. {venue}. {doi}"

def format_inline(data):
    """Format the metadata into an APA inline citation."""
    if not data: return ""
    authors = data['authors']
    year = data.get('year', 'n.d.')
    
    if len(authors) == 1:
        # Very rough extraction of last name
        last_name = authors[0].split()[-1]
        return f"({last_name}, {year})"
    elif len(authors) == 2:
        last_name1 = authors[0].split()[-1]
        last_name2 = authors[1].split()[-1]
        return f"({last_name1} & {last_name2}, {year})"
    elif len(authors) > 2:
        last_name = authors[0].split()[-1]
        return f"({last_name} et al., {year})"
    return f"(Unknown, {year})"

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
        # Detect PMC
        if 'PMC' in query and 'nih.gov' in query:
            pmcid = [part for part in query.split('/') if part.startswith('PMC')]
            if pmcid:
                data = fetch_europepmc(pmcid[0])
            else:
                data = None
        else:
            data = fetch_openalex(query)
            
        if data:
            apa = format_apa(data)
            inline = format_inline(data)
            print(f"{i}. {apa}")
            print(f"   Inline: {inline}\n")
        else:
            print(f"{i}. Failed to retrieve data for: {query}\n")

if __name__ == '__main__':
    main()
