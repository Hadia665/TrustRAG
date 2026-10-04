import re
import html
import streamlit as st
from pathlib import Path
from pypdf import PdfReader

from pdf_processor import process_pdf
from embeddings import create_embeddings
from trustrag import run_trustrag
from vector_store import create_vector_store, reset_vector_store, delete_source


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrustRAG",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)
if "db_reset" not in st.session_state:
    reset_vector_store()
    st.session_state.db_reset = True

# ============================================================
# BACKEND — PDF PROCESSING   (unchanged from your original)
# ============================================================

def process_files(uploaded_file):

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    pdf_path = data_dir / uploaded_file.name

    # Save uploaded PDF
    pdf_path.write_bytes(uploaded_file.getbuffer())

    # Count pages
    reader = PdfReader(str(pdf_path))
    pages = len(reader.pages)

    # Create chunks
    chunks = process_pdf(str(pdf_path))

    if not chunks:
        raise ValueError(
            "No text could be extracted from this PDF. "
            "Please use a text-based PDF rather than a scanned/image-only PDF."
        )

    # Create embeddings
    embeddings = create_embeddings(chunks)
    # Store in ChromaDB
    create_vector_store(chunks, embeddings, uploaded_file.name)
    return {
        "name": uploaded_file.name,
        "pages": pages,
        "size": uploaded_file.size
    }

# ============================================================
# BACKEND — TRUSTRAG   (unchanged from your original)
# ============================================================
def parse_verification(text):
    t = text.replace("**", "")
    m = re.search(r"STATUS:\s*(PARTIALLY_SUPPORTED|SUPPORTED|UNSUPPORTED)", t, re.I)
    status = m.group(1).upper() if m else "UNSUPPORTED"

    m = re.search(r"PAGE:\s*(\d+)", t)
    page = int(m.group(1)) if m else None

    m = re.search(r"EVIDENCE:\s*(.*?)\s*(?=\n\s*EXPLANATION:|\Z)", t, re.S)
    evidence = m.group(1).strip() if m else ""
    if evidence.upper() == "NONE":
        evidence = ""

    m = re.search(r"EXPLANATION:\s*(.*)", t, re.S)
    explanation = m.group(1).strip() if m else ""

    return status, page, evidence, explanation
def run_rag(question, files):

    result = run_trustrag(question)

    claims = []
    for item in result["claims"]:
        status, page, evidence_text, explanation = parse_verification(
            item["verification"]
        )
        claims.append({
            "text": item["claim"],
            "status": status,
            "evidence": evidence_text,
            "explanation": explanation,
            "page": page
        })
    evidences = []
    for item in result["evidence"]:

        evidences.append({
            "page": item["page"],
            "file": item["file"],
            "text": item["text"]
        })

    return {
        "answer": result["answer"],
        "claims": claims,
        "evidences": evidences
    }


# ============================================================
# UI STYLE
# ============================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --bg: #F7F8FA;
  --panel: #FFFFFF;
  --border: #E5E7EB;
  --text: #111827;
  --body: #1F2937;
  --muted: #6B7280;
  --sel: #EEF1F5;
  --ok: #047857;   --ok-bg: #ECFDF5;
  --warn: #B45309; --warn-bg: #FFFBEB;
  --bad: #B91C1C;  --bad-bg: #FEF2F2;
}

html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; color: var(--body); }
.stApp { background: var(--bg); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 1300px; padding-top: 2rem; padding-bottom: 6rem; }

/* Sidebar: permanently visible */
section[data-testid="stSidebar"] {
  background: var(--panel);
  border-right: 1px solid var(--border);
  min-width: 300px !important; max-width: 300px !important;
  transform: none !important; visibility: visible !important;
}
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarResizeHandle"] { display: none !important; }

.app-title { font-size: 22px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.app-subtitle { color: var(--muted); font-size: 13px; margin-bottom: 18px; }
.section-title {
  font-size: 11px; font-weight: 700; color: var(--muted);
  text-transform: uppercase; letter-spacing: .08em; margin: 22px 0 8px 0;
}

/* File card */
.file-card { background: #F8FAFC; border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; margin-top: 10px; }
.file-name { font-size: 14px; font-weight: 600; color: var(--text); word-break: break-word; }
.file-meta { font-size: 12px; color: var(--muted); margin-top: 3px; }

/* Buttons */
.stButton > button {
  border-radius: 8px; border: 1px solid #D1D5DB; background: #fff; color: #374151;
  font-size: 14px; font-weight: 500;
}
.stButton > button:hover { border-color: #9CA3AF; background: #F9FAFB; color: var(--text); }
.stButton > button:focus { box-shadow: none; outline: none; color: var(--text); }
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
  background: var(--text); color: #fff; border-color: var(--text);
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
  background: #1F2937; color: #fff; border-color: #1F2937;
}

/* History rows */
section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {
  width: 100%; justify-content: flex-start; text-align: left;
  border: none; background: transparent; padding: .45rem .6rem; font-weight: 400;
}
section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover {
  background: var(--sel);
}
section[data-testid="stSidebar"] .stButton { margin-bottom: 2px; }
.hist-active {
  background: var(--sel); border-radius: 8px; padding: .45rem .6rem;
  font-size: 14px; font-weight: 500; color: var(--text); margin-bottom: 2px;
}

/* Chat */
.user-message {
  background: var(--text); color: #fff; padding: 12px 16px; border-radius: 14px;
  margin: 18px 0 10px auto; max-width: 80%; width: fit-content; line-height: 1.5; font-size: 15px;
}
.assistant-message {
  background: var(--panel); border: 1px solid var(--border); color: var(--body);
  padding: 16px 18px; border-radius: 14px; margin: 6px 0 8px 0; line-height: 1.7; font-size: 15px;
}
.err {
  border: 1px solid #FECACA; background: var(--bad-bg); color: var(--bad);
  border-radius: 10px; padding: 10px 14px; font-size: 14px; margin: 6px 0;
}

/* Verification summary under each answer */
.summary { display: flex; align-items: center; gap: 12px; margin: 8px 0 4px 2px; flex-wrap: wrap; }
.summary-main { font-size: 13px; font-weight: 600; color: var(--text); }
.summary-sub { font-size: 12px; color: var(--muted); }
.stack { display: flex; height: 6px; width: 160px; background: #E5E7EB; border-radius: 999px; overflow: hidden; }
.stack span { display: block; height: 100%; }
.s-ok { background: #10B981; } .s-warn { background: #F59E0B; } .s-bad { background: #EF4444; }

/* Evidence panel */
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; margin-bottom: 12px; }
.panel-title { font-size: 15px; font-weight: 700; color: var(--text); margin: 0 0 10px 0; }
.stat-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.stat { font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 6px; }
.st-ok { background: var(--ok-bg); color: var(--ok); }
.st-warn { background: var(--warn-bg); color: var(--warn); }
.st-bad { background: var(--bad-bg); color: var(--bad); }

.claim { padding: 12px 0; border-top: 1px solid var(--border); }
.claim:first-of-type { border-top: none; padding-top: 0; }
.claim-text { font-size: 14px; color: var(--text); font-weight: 500; line-height: 1.5; }
.badge { display: inline-block; margin-top: 8px; padding: 3px 9px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.evidence-box {
  background: #F8FAFC; border-left: 3px solid #64748B; padding: 9px 12px; margin-top: 8px;
  font-size: 13px; color: #4B5563; line-height: 1.55; border-radius: 0 6px 6px 0;
}
.page-label { color: var(--muted); font-size: 12px; margin-top: 8px; line-height: 1.5; }
.src-head { font-size: 12px; font-weight: 700; color: var(--text); margin-bottom: 6px; }

/* Welcome */
.welcome { text-align: center; padding: 110px 20px 60px 20px; }
.welcome-title { font-size: 30px; font-weight: 700; color: var(--text); }
.welcome-text { color: var(--muted); font-size: 15px; max-width: 560px; margin: 10px auto; line-height: 1.6; }

[data-testid="stFileUploader"] section { background: #F8FAFC; border: 1px dashed #C5CBD3; border-radius: 10px; }
[data-testid="stChatInput"] { border-radius: 12px; }
[data-testid="stBottom"] > div { background: var(--bg); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def compact(s: str) -> str:
    """Strip indentation so Markdown does not treat HTML as a code block."""
    return re.sub(r"\n\s*", "", s)


def esc(x) -> str:
    return html.escape(str(x))


def multiline(x) -> str:
    return esc(x).replace("\n", "<br>")


STATUS_UI = {
    "SUPPORTED": ("ok", "SUPPORTED"),
    "PARTIALLY_SUPPORTED": ("warn", "PARTIALLY SUPPORTED"),
    "UNSUPPORTED": ("bad", "UNSUPPORTED"),
}


def count_claims(claims):
    """Real counts taken directly from the verifier's statuses."""
    sup = sum(1 for c in claims if c["status"] == "SUPPORTED")
    par = sum(1 for c in claims if c["status"] == "PARTIALLY_SUPPORTED")
    uns = len(claims) - sup - par
    return sup, par, uns


def stacked_bar(sup, par, uns):
    total = sup + par + uns
    if total == 0:
        return '<div class="stack"></div>'
    return (
        '<div class="stack">'
        f'<span class="s-ok" style="width:{sup / total * 100:.1f}%"></span>'
        f'<span class="s-warn" style="width:{par / total * 100:.1f}%"></span>'
        f'<span class="s-bad" style="width:{uns / total * 100:.1f}%"></span>'
        '</div>'
    )


# ============================================================
# SESSION STATE
# ============================================================

ss = st.session_state
ss.setdefault("files", [])
ss.setdefault("processed_key", set())
ss.setdefault("convs", [])        # [{"id", "title", "turns": [{"q", "res", "error"}]}]
ss.setdefault("current", None)    # open conversation id (None = new chat)
ss.setdefault("next_id", 1)
ss.setdefault("open_turn", None)  # (conv_id, turn_index) shown in the evidence panel


def get_conv(cid):
    return next((c for c in ss.convs if c["id"] == cid), None)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown('<div class="app-title">TrustRAG</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Evidence-grounded document assistant</div>',
        unsafe_allow_html=True
    )

    if st.button("New chat", type="primary", use_container_width=True):
        ss.current = None
        ss.open_turn = None
        st.rerun()

    # ----------------------------
    # DOCUMENT
    # ----------------------------
    st.markdown('<div class="section-title">Document</div>', unsafe_allow_html=True)

    uploads = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    ss.setdefault("failed_key", set())
    current_keys = {(u.name, u.size) for u in uploads} if uploads else set()

    # 1) Jo files uploader se hata di gayin, unka data har jagah se delete karo
    removed = [fl for fl in ss.files if (fl["name"], fl["size"]) not in current_keys]

    if removed:
        for fl in removed:
            delete_source(fl["name"])
            try:
                (Path("data") / fl["name"]).unlink(missing_ok=True)
            except Exception:
                pass
            ss.processed_key.discard((fl["name"], fl["size"]))

        ss.files = [fl for fl in ss.files if (fl["name"], fl["size"]) in current_keys]
        ss.convs = []
        ss.current = None
        ss.open_turn = None
        st.rerun()

    # failed list bhi saaf karo agar file hat gayi
    ss.failed_key &= current_keys

    # 2) Nayi files index karo
    if uploads:
        new_uploads = [
            f for f in uploads
            if (f.name, f.size) not in ss.processed_key
            and (f.name, f.size) not in ss.failed_key
        ]
        if new_uploads:
            with st.spinner("Indexing documents..."):
                for f in new_uploads:
                    try:
                        info = process_files(f)
                        ss.files.append(info)
                        ss.processed_key.add((info["name"], info["size"]))
                    except Exception as e:
                        ss.failed_key.add((f.name, f.size))
                        st.error(f"{f.name} failed")
                        st.exception(e)
            ss.convs = []
            ss.current = None
            ss.open_turn = None
            st.rerun()

    for file in ss.files:
        st.markdown(
            compact(f"""
            <div class="file-card">
              <div class="file-name">{esc(file["name"])}</div>
              <div class="file-meta">{esc(file["pages"])} pages · Ready</div>
            </div>"""),
            unsafe_allow_html=True
        )

    # ----------------------------
    # HISTORY
    # ----------------------------
    st.markdown('<div class="section-title">Conversation history</div>', unsafe_allow_html=True)

    if not ss.convs:
        st.caption("Your questions will appear here.")

    for c in reversed(ss.convs):
        label = c["title"] if len(c["title"]) <= 34 else c["title"][:32] + "..."

        if c["id"] == ss.current:
            st.markdown(f'<div class="hist-active">{esc(label)}</div>', unsafe_allow_html=True)
        else:
            if st.button(label, key=f"hist_{c['id']}", use_container_width=True):
                ss.current = c["id"]
                ss.open_turn = None
                st.rerun()

    if ss.convs:
        if st.button("Clear all history", use_container_width=True):
            ss.convs = []
            ss.current = None
            ss.open_turn = None
            st.rerun()


# ============================================================
# MAIN AREA
# ============================================================

conv = get_conv(ss.current)
turns = conv["turns"] if conv else []

show_panel = (
    ss.open_turn is not None
    and conv is not None
    and ss.open_turn[0] == conv["id"]
    and ss.open_turn[1] < len(turns)
)

if show_panel:
    chat_col, ev_col = st.columns([3, 2], gap="large")
else:
    chat_col, ev_col = st.container(), None


# ---------------- Conversation ----------------
with chat_col:

    if not turns:
        st.markdown(
            compact("""
            <div class="welcome">
              <div class="welcome-title">Ask questions about your PDF</div>
              <div class="welcome-text">
                TrustRAG retrieves relevant evidence from your document,
                generates an answer, and verifies each claim against
                the retrieved evidence.
              </div>
            </div>"""),
            unsafe_allow_html=True
        )

    for i, t in enumerate(turns):

        st.markdown(
            f'<div class="user-message">{multiline(t["q"])}</div>',
            unsafe_allow_html=True
        )

        if t.get("error"):
            st.markdown(f'<div class="err">{esc(t["error"])}</div>', unsafe_allow_html=True)
            continue

        res = t["res"]

        st.markdown(
            f'<div class="assistant-message">{multiline(res["answer"])}</div>',
            unsafe_allow_html=True
        )

        claims = res["claims"]
        sup, par, uns = count_claims(claims)
        total = len(claims)

        if total:
            st.markdown(
                compact(f"""
                <div class="summary">
                  <span class="summary-main">{sup} of {total} claims supported</span>
                  {stacked_bar(sup, par, uns)}
                  <span class="summary-sub">{par} partial · {uns} unsupported</span>
                </div>"""),
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="summary"><span class="summary-sub">No claims were extracted from this answer.</span></div>',
                unsafe_allow_html=True
            )

        is_open = show_panel and ss.open_turn == (conv["id"], i)

        if is_open:
            if st.button("Hide evidence", key=f"hide_{conv['id']}_{i}"):
                ss.open_turn = None
                st.rerun()
        else:
            if st.button("View evidence", key=f"show_{conv['id']}_{i}"):
                ss.open_turn = (conv["id"], i)
                st.rerun()


# ---------------- Evidence / verification panel ----------------
if show_panel and ev_col is not None:

    res = turns[ss.open_turn[1]]["res"]
    claims = res["claims"]
    evidences = res["evidences"]
    sup, par, uns = count_claims(claims)
    total = len(claims)

    with ev_col:

        # Summary
        st.markdown(
            compact(f"""
            <div class="panel">
              <p class="panel-title">Verification</p>
              <div class="summary-main">{sup} of {total} claims supported by the document</div>
              <div style="margin-top:10px">{stacked_bar(sup, par, uns)}</div>
              <div class="stat-row">
                <span class="stat st-ok">{sup} supported</span>
                <span class="stat st-warn">{par} partial</span>
                <span class="stat st-bad">{uns} unsupported</span>
              </div>
            </div>"""),
            unsafe_allow_html=True
        )

        # Claims
        if claims:
            rows = ""
            for c in claims:
                cls, label = STATUS_UI.get(c["status"], ("bad", "UNSUPPORTED"))
                page = f'Page {esc(c["page"])}' if c["page"] else "Page not available"
                ev_text = esc(c["evidence"]) if c["evidence"] else "No supporting evidence found."
                expl = f'<div class="page-label">{esc(c["explanation"])}</div>' if c["explanation"] else ""

                rows += compact(f"""
                <div class="claim">
                  <div class="claim-text">{esc(c["text"])}</div>
                  <span class="badge st-{cls}">{label}</span>
                  <div class="page-label">{page}</div>
                  <div class="evidence-box">{ev_text}</div>
                  {expl}
                </div>""")

            st.markdown(
                f'<div class="panel"><p class="panel-title">Claims</p>{rows}</div>',
                unsafe_allow_html=True
            )

        # Retrieved evidence
        if evidences:
            rows = ""
            for n, ev in enumerate(evidences, start=1):
                rows += compact(f"""
                <div class="claim">
                  <div class="src-head">Source {n} · Page {esc(ev["page"])}</div>
                  <div class="evidence-box" style="margin-top:0">{esc(ev["text"])}</div>
                  <div class="page-label">{esc(ev["file"])}</div>
                </div>""")

            st.markdown(
                f'<div class="panel"><p class="panel-title">Retrieved evidence · {len(evidences)} sources</p>{rows}</div>',
                unsafe_allow_html=True
            )


# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input(
    "Ask a question about your document..."
    if ss.files else "Upload a PDF in the sidebar to begin"
)

if question:

    if not ss.files:
        st.warning("Please upload a PDF before asking a question.")

    else:
        if conv is None:
            conv = {"id": ss.next_id, "title": question.strip(), "turns": []}
            ss.next_id += 1
            ss.convs.append(conv)
            ss.current = conv["id"]

        turn = {"q": question, "res": None, "error": None}

        with st.spinner("Retrieving evidence and verifying answer..."):
            try:
                turn["res"] = run_rag(question, ss.files)
            except Exception as e:
                turn["error"] = f"Something went wrong while answering: {e}"

        conv["turns"].append(turn)
        ss.open_turn = None
        st.rerun()
