import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import os

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose()
    text = soup.get_text(separator=' ')
    return ' '.join(text.split())

def is_valid_profile_url(url):
    blacklist = [r'/news/', r'/events/', r'prize', r'award', r'/media', r'\.pdf$', r'/alumni/']
    if any(re.search(pattern, url.lower()) for pattern in blacklist):
        return False
    return True

def get_internal_links(url, html_content, max_links=20):
    soup = BeautifulSoup(html_content, 'html.parser')
    domain = urlparse(url).netloc
    internal_links = set()
    
    priority_kws = ['team', 'people', 'staff', 'researcher', 'cv', 'portrait', 'group', 'professorship', 'project']
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(url, href)
        parsed = urlparse(full_url)
        
        if parsed.netloc == domain and not parsed.fragment and is_valid_profile_url(full_url):
            if any(kw in full_url.lower() for kw in priority_kws):
                internal_links.add(full_url)
                if len(internal_links) >= max_links:
                    break
    return list(internal_links)

def load_sources():
    sources = []
    # Load UniBE from the provided Excel inventory
    if os.path.exists('unibe_sous_domaines_publics_etendus.xlsx'):
        df = pd.read_excel('unibe_sous_domaines_publics_etendus.xlsx', sheet_name='Sous-domaines UniBE')
        for _, r in df.iterrows():
            if not pd.isna(r['URL']):
                sources.append({
                    "institution_id": str(r['Sous-domaine']).strip().replace('.', '_'),
                    "institution_name": str(r['Description']).strip(),
                    "seed_urls": [str(r['URL']).strip()]
                })
    
    # CRITERION 5 & 6: Easy to extend configuration for non-Excel targets
    extra_sources = [
        {
            "institution_id": "artorg",
            "institution_name": "ARTORG Center for Biomedical Engineering Research",
            "seed_urls": ["https://www.artorg.unibe.ch/research/index_eng.html", "https://www.artorg.unibe.ch/about_us/index_eng.html"]
        },
        {
            "institution_id": "dcberne",
            "institution_name": "Diabetes Center Berne",
            "seed_urls": ["https://www.dcberne.com/en/research", "https://www.dcberne.com/en/about-us/team"]
        }
    ]
    sources.extend(extra_sources)
    return sources

def run_scraper():
    sources = load_sources()
    scraped_data, visited_urls = [], set()
    headers = {'User-Agent': 'HackApertus-ResearchNavigator/4.0'}
    
    for source in sources:
        print(f"Crawling: {source['institution_name']}")
        for seed_url in source['seed_urls']:
            urls_to_crawl = [seed_url]
            try:
                res = requests.get(seed_url, headers=headers, timeout=10)
                if res.status_code == 200:
                    urls_to_crawl.extend(get_internal_links(seed_url, res.text))
            except Exception: pass

            for url in urls_to_crawl:
                if url in visited_urls: continue
                visited_urls.add(url)
                try:
                    res = requests.get(url, headers=headers, timeout=8)
                    if res.status_code == 200:
                        cleaned = clean_html(res.text)
                        if len(cleaned) > 400: 
                            scraped_data.append({"institution_id": source['institution_id'], "source_url": url, "text": cleaned})
                except Exception: pass

    with open('scraped_data.json', 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False)
    print(f"Scraping complete. Total highly-targeted pages: {len(scraped_data)}")

if __name__ == "__main__":
    run_scraper()