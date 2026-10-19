import json
import re
import chromadb
from openai import OpenAI
from sentence_transformers import SentenceTransformer

client = OpenAI(api_key="keera_sk_CADaymc6ZVcjrMfTwAXdEZReX6LFLK2r5sDVJKRI8Fk", base_url="https://gateway.keera.ch/api/v1/")
db_client = chromadb.PersistentClient(path="./research_navigator_db")
collection = db_client.get_or_create_collection(name="profiles")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

EXTRACTION_PROMPT = """
Analyze the webpage text and extract all distinct individual researchers or research groups.
CRITICAL: For each entity, generate 5-10 'semantic_lay_terms'. These are common synonyms, layperson phrases, or alternative terminology for their expertise (e.g. if expertise is 'Continuous Glucose Monitoring', lay terms are 'blood sugar tracker, diabetes wearable, CGM').

Return a valid JSON array of objects strictly matching this schema:
[
  {
    "person_name": "Full Name",
    "roles_and_affiliations": ["Role"],
    "department_or_institute": "Department",
    "fields_of_expertise": ["Technical Expertise"],
    "related_projects": ["Project Name"],
    "infrastructure_services": ["Infrastructure"],
    "semantic_lay_terms": ["lay term 1", "synonym 2", "alternative phrase 3"]
  }
]
"""

def extract_and_enrich(text, url):
    try:
        response = client.chat.completions.create(
            model="apertus-v1-5-70b",
            messages=[{"role": "system", "content": EXTRACTION_PROMPT}, 
                      {"role": "user", "content": f"URL: {url}\nText: {text[:4500]}"}],
            temperature=0.0, max_tokens=1500
        )
        content = response.choices[0].message.content
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else []
    except Exception:
        return []

def format_value(val):
    return ", ".join([str(i).strip() for i in val if i]) if isinstance(val, list) else str(val).strip() if val else ""

def populate():
    with open('scraped_data.json', 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)

    if collection.get()['ids']: collection.delete(ids=collection.get()['ids'])
    invalid_names = ["unknown", "n/a", "not explicitly", "university", "center overview", "none"]

    total = 0
    for i, item in enumerate(scraped_data):
        print(f"Deep Extracting & Enriching ({i+1}/{len(scraped_data)}): {item['source_url']}")
        profiles = extract_and_enrich(item['text'], item['source_url'])
        
        for j, p in enumerate(profiles):
            name = format_value(p.get("person_name"))
            if not name or len(name) < 4 or any(inv in name.lower() for inv in invalid_names): continue

            metadata = {
                "source_url": item['source_url'],
                "person_name": name,
                "roles_and_affiliations": format_value(p.get("roles_and_affiliations")),
                "department_or_institute": format_value(p.get("department_or_institute")),
                "fields_of_expertise": format_value(p.get("fields_of_expertise")),
                "related_projects": format_value(p.get("related_projects")),
                "infrastructure_services": format_value(p.get("infrastructure_services")),
                "semantic_lay_terms": format_value(p.get("semantic_lay_terms")) # The Secret Weapon
            }

            if not metadata["fields_of_expertise"] and not metadata["related_projects"]: continue

            # Vector is now enriched with generated synonyms permanently
            embed_content = f"Name: {metadata['person_name']} | Expertise: {metadata['fields_of_expertise']} | " \
                            f"Synonyms & Lay Terms: {metadata['semantic_lay_terms']} | Projects: {metadata['related_projects']}"
            
            collection.add(
                embeddings=[embedding_model.encode(embed_content).tolist()],
                metadatas=[metadata], documents=[item['text'][:1000]], ids=[f"ent_{i}_{j}"]
            )
            total += 1

    print(f"\nDatabase fully enriched. Total experts indexed: {total}")

if __name__ == "__main__":
    populate()