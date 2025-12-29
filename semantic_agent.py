import google.generativeai as genai
import json
import time
import os
import dotenv

dotenv.load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={
        "temperature": 0.1,
        "response_mime_type": "application/json"
    }
)


def normalize_reference_batch(batch):
    prompt = f"""
You are a citation normalization engine.

Rules:
- DO NOT hallucinate.
- If unsure, return null fields.
- Output must be VALID JSON.
- Output must be an array of objects.

Each object must have:
{{
  "authors": string or null,
  "title": string or null,
  "year": string or null,
  "link": string or null,
  "source_type": "paper" | "website" | "standard" | "unknown",
  "confidence": number
}}

Input:
{json.dumps(batch, indent=2)}
"""

    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)

    except Exception as e:
        return [{"error": str(e), "raw": r} for r in batch]
    
    
def process_references(parsed_references, batch_size=8):
    all_results = []

    for i in range(0, len(parsed_references), batch_size):
        batch = parsed_references[i:i + batch_size]

        print(f"Processing batch {i//batch_size + 1}")

        normalized = normalize_reference_batch(batch)
        all_results.extend(normalized)

        time.sleep(2)

    return all_results
