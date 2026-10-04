import re

from rag import generate_answer
from claim_extractor import extract_claims
from verifier import verify_claim


def run_trustrag(question):

    answer, evidence = generate_answer(question)

    claims_text = extract_claims(answer)

    claims = []
    for line in claims_text.splitlines():
        line = re.sub(r"^\s*(\d+[\.\)]|[-*•])\s*", "", line).strip()
        if line and not line.lower().startswith("claims"):
            claims.append(line)

    verified_claims = []

    for claim in claims:
        try:
            verification = verify_claim(claim, evidence)
        except Exception as e:
            verification = (
                "STATUS: UNSUPPORTED\nPAGE: NONE\nEVIDENCE: NONE\n"
                f"EXPLANATION: Verification failed ({e})"
            )

        verified_claims.append({
            "claim": claim,
            "verification": verification
        })

    return {
        "question": question,
        "answer": answer,
        "evidence": evidence,
        "claims": verified_claims
    }