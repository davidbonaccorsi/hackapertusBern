from openai import OpenAI

client = OpenAI(
    api_key="keera_sk_CADaymc6ZVcjrMfTwAXdEZReX6LFLK2r5sDVJKRI8Fk",
    base_url="https://gateway.keera.ch/api/v1/"
)

def expand_query(user_query: str) -> list[str]:
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
    except Exception:
        return [user_query]
    