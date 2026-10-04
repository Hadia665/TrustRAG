import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")


client = genai.Client(api_key=api_key)


def extract_claims(answer):

    prompt = f"""
You are a claim extraction system.

Break the answer below into individual factual claims.

Rules:
- Extract only factual claims.
- Each claim should contain one main idea.
- Do not add new information.
- Do not explain the claims.
- Return one claim per line.
- Number the claims.

Answer:
{answer}

Claims:
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text