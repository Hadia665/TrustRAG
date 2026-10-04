# TrustRAG

Evidence-grounded document assistant. Upload PDFs, ask questions, and every claim in the answer is verified against the source text with page references.

Built for LovHack Season 3.

**Live demo:** https://trustrag-aauwsse8czfvydqpr9ucqb.streamlit.app/

## The problem
AI chatbots give confident answers, but when you study from a long PDF you cannot tell which sentences are really in the document. TrustRAG shows its proof.

## How it works
1. PDFs are split into overlapping chunks (with page numbers) and embedded with all-MiniLM-L6-v2
2. Chunks are stored in ChromaDB
3. The top relevant chunks are retrieved for each question
4. Gemini answers using only that evidence
5. The answer is split into individual claims
6. Each claim is verified as SUPPORTED, PARTIALLY SUPPORTED or UNSUPPORTED, with the exact evidence, page number and an explanation
7. The UI shows a summary such as "4 of 5 claims supported" and a "View evidence" panel

## Features
- Upload multiple PDFs
- Removing a PDF also deletes its stored data
- Claim-level verification with page references
- Conversation history and evidence panel

## Tech stack
Python, Streamlit, Google Gemini API, ChromaDB, sentence-transformers, pypdf

## Run locally
```bash
git clone https://github.com/Hadia665/TrustRAG.git
cd TrustRAG
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
Create a `.env` file (see `.env.example`) and add your key:
```
GEMINI_API_KEY=your_api_key_here
```
Then run:
```bash
streamlit run app.py
```

## Notes
Demo build with a single shared document index, so test one session at a time. Works with text-based PDFs (scanned PDFs are not supported yet).
