import json
import re
import chromadb
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from urllib.parse import urlparse

client = OpenAI(
    api_key="keera_sk_CADaymc6ZVcjrMfTwAXdEZReX6LFLK2r5sDVJKRI8Fk",
    base_url="https://gateway.keera.ch/api/v1/"
)

app = FastAPI(title="Research & Expertise Navigator")
db_client = chromadb.PersistentClient(path="./research_navigator_db")
collection = db_client.get_or_create_collection(name="profiles")

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class SearchRequest(BaseModel):
    query: str

def expand_query(user_query: str) -> list[str]:
    """Expands user query with academic and lay-term synonyms using Apertus LLM."""
    prompt = f"""
    Given the search query: '{user_query}', generate 3-4 medical, technical, or lay-term synonyms and related terms used in academic research.
    Output ONLY a comma-separated list of terms without additional commentary or numbers.
    Example Input: glucose sensors
    Example Output: continuous glucose monitoring, CGM, biosensing, metabolic monitoring, glucose sensors
    """
    try:
        response = client.chat.completions.create(
            model="apertus-v1-5-70b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        expanded_terms = response.choices[0].message.content.strip().split(",")
        cleaned_terms = [term.strip() for term in expanded_terms if term.strip()]
        return list(set([user_query] + cleaned_terms))
    except Exception as e:
        print(f"Query expansion warning: {e}")
        return [user_query]

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.post("/search")
async def search(request: SearchRequest):
    # 1. Expand query terms using Apertus 70B
    expanded_terms = expand_query(request.query)
    combined_query = ", ".join(expanded_terms)
    print(f"DEBUG: Expanded Query -> '{combined_query}'")

    # 2. Vector search in ChromaDB using expanded query vector
    query_vector = embedding_model.encode([combined_query]).tolist()
    results = collection.query(query_embeddings=query_vector, n_results=30, include=["metadatas", "distances"])
    
    if not results['metadatas'] or not results['metadatas'][0]: 
        return {"results": [], "expanded_terms": expanded_terms}

    enhanced_results = []
    domain_counts = {}

    # 3. LLM Match Verification Bouncer
    for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
        if distance > 1.6: 
            continue 

        source_url = metadata.get("source_url", "")
        domain = urlparse(source_url).netloc
        
        # Enforce diversity (max 4 per domain to prevent UniBE from dominating ARTORG/DCB)
        if domain_counts.get(domain, 0) >= 4:
            continue

        prompt = f"""
        Determine if '{metadata.get('person_name')}' matches the query '{request.query}'.
        Expertise: {metadata.get('fields_of_expertise')}
        Lay Terms: {metadata.get('semantic_lay_terms')}
        Projects: {metadata.get('related_projects')}
        Infrastructure: {metadata.get('infrastructure_services')}
        
        Output strictly valid JSON with no other text:
        {{
            "is_match": true/false,
            "reason": "1 concise sentence explaining the connection based on the facts."
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model="apertus-v1-5-70b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0, 
                max_tokens=100
            )
            json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
            verification = json.loads(json_match.group(0))
            
            if not verification.get("is_match", False):
                continue
            reason = verification.get("reason", "Expertise logically aligns with the query.")
            
        except Exception as e:
            print(f"Verification error for {metadata.get('person_name')}: {e}")
            continue 

        domain_counts[domain] = domain_counts.get(domain, 0) + 1

        enhanced_results.append({
            "person": metadata.get("person_name"),
            "role": metadata.get("roles_and_affiliations") or "Researcher",
            "unit": metadata.get("department_or_institute"),
            "expertise": [e.strip() for e in metadata.get("fields_of_expertise", "").split(",") if e.strip()],
            "projects": [p.strip() for p in metadata.get("related_projects", "").split(",") if p.strip()],
            "infrastructure": [i.strip() for i in metadata.get("infrastructure_services", "").split(",") if i.strip()],
            "reason_for_match": reason,
            "source_url": source_url
        })
        
        if len(enhanced_results) >= 10: 
            break 

    return {
        "query": request.query, 
        "expanded_terms": expanded_terms, 
        "results": enhanced_results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 