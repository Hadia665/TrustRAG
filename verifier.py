import os
import re

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")


client = genai.Client(api_key=api_key)


def verify_claim(claim, evidence_items):

    evidence_text = ""

    for i, item in enumerate(evidence_items, start=1):

        evidence_text += f"""
EVIDENCE {i}
PAGE: {item["page"]}
TEXT:
{item["text"]}

"""


    prompt = f"""
You are an evidence verification system.

Determine whether the CLAIM is supported by the provided EVIDENCE.

Use ONLY the provided evidence.

Return exactly this format:

STATUS: SUPPORTED
PAGE: number
EVIDENCE: exact relevant sentence or short passage
EXPLANATION: short explanation

OR

STATUS: PARTIALLY_SUPPORTED
PAGE: number
EVIDENCE: exact relevant sentence or short passage
EXPLANATION: short explanation

OR

STATUS: UNSUPPORTED
PAGE: NONE
EVIDENCE: NONE
EXPLANATION: short explanation

Rules:

SUPPORTED:
The evidence directly supports the entire claim.

PARTIALLY_SUPPORTED:
The evidence supports part of the claim, but some detail is not supported.

UNSUPPORTED:
The provided evidence does not support the claim.

Do not use outside knowledge.

CLAIM:
{claim}

PROVIDED EVIDENCE:
{evidence_text}
"""


    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text