import json
import re
import chromadb
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from urllib.parse import urlparse

client = OpenAI(api_key="keera_sk_CADaymc6ZVcjrMfTwAXdEZReX6LFLK2r5sDVJKRI8Fk", base_url="https://gateway.keera.ch/api/v1/")
app = FastAPI(title="Research Navigator")
db_client = chromadb.PersistentClient(path="./research_navigator_db")
collection = db_client.get_or_create_collection(name="profiles")

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class SearchRequest(BaseModel): query: str

@app.get("/")
def serve_frontend(): return FileResponse("index.html")

@app.post("/search")
async def search(request: SearchRequest):
    query_vector = embedding_model.encode([request.query]).tolist()
    
    # CRITERION 1: Broaden initial retrieval to ensure we capture the top 10 accurately
    results = collection.query(query_embeddings=query_vector, n_results=30, include=["metadatas", "distances"])
    
    if not results['metadatas'] or not results['metadatas'][0]: 
        return {"results": []}

    enhanced_results = []
    domain_counts = {}

    for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
        if distance > 1.6: 
            continue 

        source_url = metadata.get("source_url", "")
        domain = urlparse(source_url).netloc
        
        # DIVERSITY ENFORCEMENT: Max 4 results per distinct domain to ensure DCB and ARTORG surface
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
                temperature=0.0, max_tokens=100
            )
            json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
            verification = json.loads(json_match.group(0))
            
            if not verification.get("is_match", False):
                continue
            reason = verification.get("reason", "Expertise logically aligns with the query.")
            
        except Exception as e:
            print(f"ERROR [{metadata.get('person_name')}]: LLM API or Parsing failed - {str(e)}")
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
        
        if len(enhanced_results) >= 10: break # Standardized to Top 10 per requirements

    return {"query": request.query, "results": enhanced_results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)