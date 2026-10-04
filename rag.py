import os

from dotenv import load_dotenv
from google import genai

from retriever import retrieve_evidence


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")


client = genai.Client(api_key=api_key)


def generate_answer(question):

    evidence = retrieve_evidence(
        question,
        top_k=5
    )

    context = ""

    for i, item in enumerate(evidence, start=1):

        context += f"""
Evidence {i}
File: {item["file"]}
Page: {item["page"]}

{item["text"]}

"""


    prompt = f"""
You are an assistant answering questions about a document.

Answer the user's question using ONLY the evidence provided below.

Rules:
- Do not use outside knowledge.
- Do not invent facts.
- If the evidence does not contain enough information,
  clearly say that the information is not available.
- Give a concise answer.

Evidence:
{context}

User Question:
{question}

Answer:
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text, evidence