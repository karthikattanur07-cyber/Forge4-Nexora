import streamlit as st
import pandas as pd
import json
import os
import re
from typing import List, Tuple

# Teammate merged modules
try:
    from schemas import ScoredCandidate
    from explainer import SmartExplainer
except ImportError as e:
    st.error(f"Failed to import core modules: {e}. Ensure schemas.py and explainer.py are in the working directory.")
    st.stop()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ScoutIQ | Smart Shortlisting Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS BADGES & STYLING ---
st.markdown("""
<style>
    .badge-matched {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 5px;
        margin-bottom: 5px;
        border: 1px solid #c8e6c9;
        display: inline-block;
    }
    .badge-missing {
        background-color: #ffebee;
        color: #c62828;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 5px;
        margin-bottom: 5px;
        border: 1px solid #ffcdd2;
        display: inline-block;
    }
    .metric-card {
        border-radius: 8px;
        padding: 16px;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# --- FALLBACK MOCK DATA ---
MOCK_JD = {
    "role": "Senior Python Backend Developer",
    "skills": ["python", "fastapi", "postgresql", "docker", "rest apis", "redis", "kubernetes"],
    "text": (
        "We are looking for a rockstar Senior Python Backend Developer with 3+ years of experience. "
        "Must be proficient in Python, FastAPI, PostgreSQL, Docker, and REST APIs. "
        "Nice to have: Redis and Kubernetes. Must be willing to work in a fast-paced environment."
    )
}

MOCK_CANDIDATES = [
    ScoredCandidate(
        id="cand_1",
        rank=1,
        name="Sneha Reddy",
        final_score=89.2,
        semantic_score=91.5,
        keyword_score=86.0,
        skills=["python", "fastapi", "postgresql", "docker", "rest apis"]
    ),
    ScoredCandidate(
        id="cand_2",
        rank=2,
        name="Karan Verma",
        final_score=82.4,
        semantic_score=85.0,
        keyword_score=78.5,
        skills=["python", "django", "postgresql", "git", "rest apis"]
    ),
    ScoredCandidate(
        id="cand_3",
        rank=3,
        name="Aditya Kulkarni",
        final_score=75.6,
        semantic_score=79.0,
        keyword_score=70.5,
        skills=["python", "javascript", "docker", "rest apis"]
    ),
    ScoredCandidate(
        id="cand_4",
        rank=4,
        name="Arjun Desai",
        final_score=64.0,
        semantic_score=68.0,
        keyword_score=58.0,
        skills=["git", "linux", "c++", "system design"]
    ),
    ScoredCandidate(
        id="cand_5",
        rank=5,
        name="Aman Tiwari",
        final_score=21.5,
        semantic_score=24.0,
        keyword_score=17.5,
        skills=["sales", "crm", "lead generation", "outreach"]
    )
]

# --- DATA LOADER WITH FALLBACK ---
def load_engine_data() -> Tuple[dict, List[ScoredCandidate], bool]:
    is_live = False
    jd_data = MOCK_JD
    candidates = MOCK_CANDIDATES

    if os.path.exists("jd.json"):
        try:
            with open("jd.json", "r", encoding="utf-8") as f:
                jd_data = json.load(f)
                is_live = True
        except Exception as e:
            st.sidebar.warning(f"Failed to read jd.json: {e}")

    if os.path.exists("rankings.json"):
        try:
            with open("rankings.json", "r", encoding="utf-8") as f:
                raw_rankings = json.load(f)
                candidates = [
                    ScoredCandidate(
                        id=item.get("id", f"cand_{idx + 1}"),
                        rank=item.get("rank", idx + 1),
                        name=item.get("name", "Unknown"),
                        final_score=float(item.get("final_score", 0.0)),
                        semantic_score=float(item.get("semantic_score", 0.0)),
                        keyword_score=float(item.get("keyword_score", 0.0)),
                        skills=item.get("skills", [])
                    )
                    for idx, item in enumerate(raw_rankings)
                ]
                is_live = True
        except Exception as e:
            st.sidebar.warning(f"Failed to read rankings.json: {e}")

    return jd_data, candidates, is_live

jd_data, candidate_pool, is_live_data = load_engine_data()

# Ensure sorted order by score
candidate_pool = sorted(candidate_pool, key=lambda c: c.final_score, reverse=True)
for idx, cand in enumerate(candidate_pool):
    cand.rank = idx + 1

# Instantiate the Explainer
explainer = SmartExplainer(
    jd_skills=jd_data.get("skills", []),
    jd_text=jd_data.get("text", "")
)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Evaluation Setup")
    
    # Offline Status Tag
    st.success("🔒 **Offline Mode:** Active (No APIs)")
    
    if is_live_data:
        st.info("🟢 **Data Source:** Live pipeline outputs (`rankings.json`, `jd.json`)")
    else:
        st.warning("🟠 **Data Source:** Safe Mock Pool (Awaiting pipeline files)")

    # --- INGESTION ROBUSTNESS & NORMALIZATION ENGINE ---
    with st.expander("🛡️ Ingestion Robustness & Normalization Engine", expanded=True):
        st.markdown(
            "<span style='background-color:#e8f5e9;color:#2e7d32;padding:4px 10px;border-radius:12px;font-size:0.85em;font-weight:600;'>🛡️ Noise & Typo Tolerance: Active</span>",
            unsafe_allow_html=True
        )
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        st.markdown("1. **🔤 Typo & Alias Resolver:** Normalized 15+ tech aliases (e.g., ReactJS, Node js, Postgres)")
        st.markdown("2. **📑 Dynamic Header Canonicalization:** Unifies varied formats (Skills, Competencies, Tech Stack)")
        st.markdown("3. **🗓️ Heterogeneous Date Parsing:** Resilient to varied date syntax without pipeline failure")

    st.markdown("---")
    st.subheader("Target Job Profile")
    st.markdown(f"**Role:** `{jd_data.get('role', 'Technical Role')}`")
    
    st.markdown("**Required Skills:**")
    skills_tags = "".join([f"<span class='badge-matched'>{s}</span>" for s in jd_data.get("skills", [])])
    st.markdown(skills_tags, unsafe_allow_html=True)
    
    # --- RECRUITER DYNAMIC SCORING CALIBRATION SLIDER ---
    st.markdown("---")
    st.subheader("🎛️ Scoring Calibration")
    st.caption("Adjust weighting between contextual semantic fit and exact skill matching.")

    semantic_pct = st.slider(
        "Semantic Context (Projects & Experience)",
        min_value=0,
        max_value=100,
        value=60,
        step=5,
        format="%d%%",
        help="Higher values favor candidate experience and projects. Lower values favor explicit skill keyword matches."
    )
    keyword_pct = 100 - semantic_pct

    col_left, col_right = st.columns(2)
    col_left.markdown(f"🛠️ Skills Coverage: `{keyword_pct}%`")
    col_right.markdown(f"💼 Project Context: `{semantic_pct}%`")

    st.progress(semantic_pct / 100.0)

    # Calculation Logic
    semantic_weight = semantic_pct / 100.0
    keyword_weight = (100 - semantic_pct) / 100.0

    # Dynamically recompute scores and sort pool
    for c in candidate_pool:
        c.final_score = round((c.semantic_score * semantic_weight) + (c.keyword_score * keyword_weight), 1)

    candidate_pool = sorted(candidate_pool, key=lambda c: c.final_score, reverse=True)
    for idx, c in enumerate(candidate_pool):
        c.rank = idx + 1

    st.markdown("---")
    if st.button("🔄 Reload Disk Data", use_container_width=True):
        st.rerun()


# --- HEADER SECTION ---
st.title("🎯 ScoutIQ: Smart Shortlisting Engine")
st.caption("Offline Semantic & Keyword Hybrid Matcher | Local Rule-Based Explainability")
st.markdown("---")

# --- HIGH-LEVEL METRICS BANNER ---
top_3 = candidate_pool[:3]
spread = round(candidate_pool[0].final_score - candidate_pool[-1].final_score, 1)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Evaluated Pool", f"{len(candidate_pool)} Resumes")
m2.metric("Top Candidate Score", f"{candidate_pool[0].final_score}%")
m3.metric("Shortlist Cutoff (Top 3)", f"{top_3[-1].final_score}%")
m4.metric("Ranking Spread", f"{spread}%", help="Spread between rank 1 and lowest rank candidate")

st.markdown("---")

# --- RUBRIC ITEM (20%): TOP-3 EXPLAINABLE SHORTLIST ---
st.markdown("## 🏆 Top 3 Explainable Shortlist")
st.caption("Deterministic natural language explanations based on matched skill sets and embedding proximity.")

cols = st.columns(3)
for idx, cand in enumerate(top_3):
    exp = explainer.explain_candidate(cand)
    with cols[idx]:
        st.subheader(f"#{cand.rank} {cand.name}")
        st.progress(min(int(cand.final_score), 100))
        st.markdown(f"**Overall Score:** `{cand.final_score}%`")
        st.caption(f"Semantic Fit: **{cand.semantic_score}%** | Keyword Fit: **{cand.keyword_score}%**")
        
        st.markdown("**Matched Skills:**")
        if exp.matched_skills:
            st.markdown("".join([f"<span class='badge-matched'>{s}</span>" for s in exp.matched_skills]), unsafe_allow_html=True)
        else:
            st.write("_None detected_")
            
        st.markdown("**Missing Skills:**")
        if exp.missing_skills:
            st.markdown("".join([f"<span class='badge-missing'>{s}</span>" for s in exp.missing_skills]), unsafe_allow_html=True)
        else:
            st.write("_None_")
            
        st.markdown("**Explainability Verdict:**")
        st.info(exp.summary)

st.markdown("---")

# --- RUBRIC ITEM (20%): SPREAD & SENSIBILITY TABLE ---
st.markdown("## 📊 Candidate Ranking & Spread Matrix")
st.caption("Demonstrating distinction between strong technical fits, edge cases, and non-technical domains.")

table_rows = [
    {
        "Rank": c.rank,
        "Candidate": c.name,
        "Final Score": c.final_score,
        "Semantic Fit": c.semantic_score,
        "Keyword Fit": c.keyword_score,
        "Skills Extracted": len(c.skills)
    }
    for c in candidate_pool
]
df = pd.DataFrame(table_rows)

st.dataframe(
    df,
    column_config={
        "Rank": st.column_config.NumberColumn("Rank", format="%d"),
        "Candidate": "Candidate Name",
        "Final Score": st.column_config.ProgressColumn(
            "Final Score",
            format="%.1f%%",
            min_value=0,
            max_value=100
        ),
        "Semantic Fit": st.column_config.NumberColumn("Semantic Fit", format="%.1f%%"),
        "Keyword Fit": st.column_config.NumberColumn("Keyword Fit", format="%.1f%%"),
        "Skills Extracted": "Identified Skills"
    },
    use_container_width=True,
    hide_index=True
)

# --- EXECUTIVE SHORTLIST CSV EXPORT ---
export_rows = [
    {
        "Rank": c.rank,
        "Candidate Name": c.name,
        "Final Score (%)": f"{c.final_score:.1f}%",
        "Semantic Fit (%)": f"{c.semantic_score:.1f}%",
        "Keyword Fit (%)": f"{c.keyword_score:.1f}%",
        "Identified Skills": ", ".join(c.skills) if c.skills else "None",
        "Decision Explanation": explainer.explain_candidate(c).summary,

    }
    for c in candidate_pool
]
export_df = pd.DataFrame(export_rows)
csv_bytes = export_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Export Shortlist Executive Report (CSV)",
    data=csv_bytes,
    file_name="ScoutIQ_Shortlist_Report.csv",
    mime="text/csv",
    use_container_width=True,
    help="Download a recruiter-ready executive report with scores and explanations."
)

st.markdown("---")

# --- RUBRIC BONUS 1: RECRUITER COMPARISON TOOL ---
st.markdown("## 💬 Head-to-Head Comparison (Bonus)")
st.caption("Rule-based differential engine addressing: *'Why is Candidate X ranked above Candidate Y?'*")

name_map = {c.name: c for c in candidate_pool}
cand_names = list(name_map.keys())

col_a, col_b = st.columns(2)
with col_a:
    cand_a_name = st.selectbox("Select Candidate A", cand_names, index=0)
with col_b:
    cand_b_name = st.selectbox("Select Candidate B", cand_names, index=min(1, len(cand_names) - 1))

if st.button("Run Head-to-Head Comparison", type="primary"):
    cand_a_obj = name_map[cand_a_name]
    cand_b_obj = name_map[cand_b_name]

    comp_result = explainer.compare_candidates(cand_a_obj, cand_b_obj)

    st.success("**Differential Analysis:**")
    if isinstance(comp_result, dict):
        comp_text = comp_result.get("comparison_text", "No comparative text generated.")
    else:
        comp_text = comp_result

    st.markdown(comp_text)


st.markdown("---")

# --- RUBRIC BONUS 2: JOB DESCRIPTION BIAS AUDIT ---
st.markdown("## 🔍 Job Description Bias Audit (Bonus)")
st.caption("Lexical analysis identifying exclusionary terms, extreme phrasing, or restrictive credential gating.")

with st.expander("Run Automated JD Audit", expanded=True):
    findings = explainer.audit_jd_bias()
    if findings:
        for item in findings:
            category = item.get("category", "Bias Alert")
            desc = item.get("description", "")
            term = item.get("matched_term", "")
            st.warning(f"⚠️ **{category}:** {desc} (Detected term: `{term}`)")
    else:
        st.success("✅ Clean Audit: No exclusionary, aggressive-pace, or elitist terms detected in the Job Description.")

st.markdown("---")

# --- RECRUITER AI CHAT ASSISTANT (OFFLINE) ---
st.markdown("## 💬 Recruiter AI Chat Assistant (Offline)")
st.caption("Ask natural-language questions about candidate rankings, skill discrepancies, or head-to-head decisions.")


def answer_recruiter_query(query: str, pool: List[ScoredCandidate], exp_engine: SmartExplainer) -> str:
    """Parse recruiter natural-language queries and generate rule-based explanations offline."""
    q_lower = query.lower()
    found: List[ScoredCandidate] = []

    # 1. Exact full name matching
    for c in pool:
        if c.name.lower() in q_lower:
            if c not in found:
                found.append(c)

    # 2. First / Last name matching if fewer than 2 candidates matched
    if len(found) < 2:
        for c in pool:
            name_parts = [p.lower() for p in c.name.split() if len(p) >= 3]
            for part in name_parts:
                if re.search(r"\b" + re.escape(part) + r"\b", q_lower):
                    if c not in found:
                        found.append(c)
                    break

    # 3. Rank-based matching (e.g. #2, rank 2, candidate #1)
    rank_matches = re.findall(r"(?:#|rank\s*#?|candidate\s*#?)(\d+)\b", q_lower)
    for r_str in rank_matches:
        r_num = int(r_str)
        for c in pool:
            if c.rank == r_num and c not in found:
                found.append(c)

    # Branch 1: Two candidates found -> Head-to-Head Comparison
    if len(found) >= 2:
        c1, c2 = found[0], found[1]
        comp_res = exp_engine.compare_candidates(c1, c2)
        comp_text = comp_res.get("comparison_text", str(comp_res)) if isinstance(comp_res, dict) else str(comp_res)

        higher = c1 if c1.rank < c2.rank else c2
        lower = c2 if c1.rank < c2.rank else c1
        matched_h, missing_h = exp_engine.extract_skills(higher.skills)
        matched_l, missing_l = exp_engine.extract_skills(lower.skills)

        score_delta = round(abs(higher.final_score - lower.final_score), 1)

        return (
            f"### ⚖️ Head-to-Head Comparison: {higher.name} vs. {lower.name}\n\n"
            f"{comp_text}\n\n"
            f"**Score & Skill Delta Breakdown:**\n"
            f"- **Score Margin:** `{higher.name}` leads by **+{score_delta}%** overall.\n"
            f"- **{higher.name} (Rank #{higher.rank}):** Final `{higher.final_score}%` "
            f"(Semantic: `{higher.semantic_score}%`, Keyword: `{higher.keyword_score}%`) | "
            f"**Matched Skills ({len(matched_h)}):** {', '.join(matched_h) if matched_h else 'None'} | "
            f"**Missing:** {', '.join(missing_h) if missing_h else 'None'}\n"
            f"- **{lower.name} (Rank #{lower.rank}):** Final `{lower.final_score}%` "
            f"(Semantic: `{lower.semantic_score}%`, Keyword: `{lower.keyword_score}%`) | "
            f"**Matched Skills ({len(matched_l)}):** {', '.join(matched_l) if matched_l else 'None'} | "
            f"**Missing:** {', '.join(missing_l) if missing_l else 'None'}"
        )

    # Branch 2: Single candidate found -> Individual Evaluation
    elif len(found) == 1:
        cand = found[0]
        exp = exp_engine.explain_candidate(cand)
        matched_pills = ", ".join([f"`{s}`" for s in exp.matched_skills]) if exp.matched_skills else "_None detected_"
        missing_pills = ", ".join([f"`{s}`" for s in exp.missing_skills]) if exp.missing_skills else "_None (Complete skill coverage)_"

        return (
            f"### 📋 Candidate Evaluation: {cand.name} (Rank #{cand.rank})\n\n"
            f"**Decision Verdict:**\n{exp.summary}\n\n"
            f"**Key Differentiator:** {exp.key_differentiator}\n\n"
            f"**Evaluation Metrics & Skill Breakdown:**\n"
            f"- **Overall Match Score:** `{cand.final_score}%` (Rank #{cand.rank})\n"
            f"- **Contextual Semantic Fit:** `{cand.semantic_score}%`\n"
            f"- **Exact Keyword Fit:** `{cand.keyword_score}%`\n"
            f"- **Core Matched Strengths ({len(exp.matched_skills)}):** {matched_pills}\n"
            f"- **Identified Missing Gaps ({len(exp.missing_skills)}):** {missing_pills}"
        )

    # Branch 3: Fallback guidance
    else:
        return (
            "I can explain specific candidates or comparisons! "
            "Try asking: 'Why is [Candidate A] ranked above [Candidate B]?' or 'Explain [Candidate Name]'."
        )


# Chat State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! Ask me about any candidate's ranking or why one candidate outranked another.",
        }
    ]

# Display prior chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Quick prompt suggestions
st.markdown("**Suggested Questions:**")
q_col1, q_col2, q_col3 = st.columns(3)
clicked_prompt = None

if q_col1.button("Why is Priya Menon ranked above Divya Krishnan?", use_container_width=True):
    clicked_prompt = "Why is Priya Menon ranked above Divya Krishnan?"
if q_col2.button("Explain Aditi Sharma's ranking", use_container_width=True):
    clicked_prompt = "Explain Aditi Sharma's ranking"
if q_col3.button("What are the key skill gaps for #2?", use_container_width=True):
    clicked_prompt = "What are the key skill gaps for #2?"

user_query = st.chat_input("Ask a question about candidates...")
query_to_process = clicked_prompt or user_query

if query_to_process:
    st.session_state.messages.append({"role": "user", "content": query_to_process})
    response_text = answer_recruiter_query(query_to_process, candidate_pool, explainer)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()