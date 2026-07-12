"""
ResumeIQ - Streamlit App
=========================
Web UI wrapper around the `resumeiq` package: upload a resume, optionally
paste a job description, and get the full ATS scoring + job match +
cover letter + interview prep pipeline in your browser.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import os
import tempfile

import pandas as pd
import streamlit as st

from resumeiq import (
    parse_resume_file,
    parse_resume_text,
    extract_structured_data,
    score_resume,
    match_job,
    generate_cover_letter,
    generate_interview_questions,
    build_pdf_report,
)

st.set_page_config(
    page_title="ResumeIQ - AI Resume Analyzer",
    page_icon="🧠",
    layout="wide",
)

PRIMARY = "#4338CA"

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
for key in ("structured", "score_result", "match_result", "cover_letter",
            "interview_questions", "raw_text", "report_bytes"):
    if key not in st.session_state:
        st.session_state[key] = None

# --------------------------------------------------------------------------
# Sidebar - inputs
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h2 style='color:{PRIMARY};'>ResumeIQ 🧠</h2>", unsafe_allow_html=True)
    st.caption("AI Resume Analyzer & Career Copilot")

    resume_file = st.file_uploader("Upload resume", type=["pdf", "docx", "txt"])

    st.markdown("---")
    jd_text = st.text_area(
        "Job description (optional)",
        height=180,
        placeholder="Paste the job description here to unlock Job Match, "
                    "Cover Letter, and JD-aware Keyword scoring...",
    )
    company_name = st.text_input("Company name (optional)", placeholder="Acme Corp")

    st.markdown("---")
    api_key = st.text_input(
        "OpenAI API key (optional)", type="password",
        help="If provided, extraction / cover letter / interview questions "
             "upgrade to LLM-generated output. Leave blank to run fully "
             "offline with the built-in rule-based engine.",
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    analyze_clicked = st.button("Analyze Resume", type="primary", use_container_width=True)

    st.markdown("---")
    with st.expander("Try it with sample data"):
        if st.button("Load sample resume + JD", use_container_width=True):
            st.session_state["_use_sample"] = True

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.markdown(
    f"<h1 style='color:{PRIMARY}; margin-bottom:0;'>ResumeIQ</h1>"
    "<p style='color:#666; margin-top:4px;'>Instant ATS scoring · Job match "
    "intelligence · AI cover letters · Interview prep</p>",
    unsafe_allow_html=True,
)

use_sample = st.session_state.pop("_use_sample", False)

# --------------------------------------------------------------------------
# Run pipeline
# --------------------------------------------------------------------------
def run_pipeline(raw_text: str, jd: str, company: str) -> None:
    with st.spinner("Parsing and scoring resume..."):
        structured = extract_structured_data(raw_text)
        score_result = score_resume(raw_text, structured, jd or None)

    match_result = None
    cover_letter = None
    if jd:
        with st.spinner("Running job match + generating cover letter..."):
            match_result = match_job(raw_text, structured, jd)
            cover_letter = generate_cover_letter(structured, match_result, jd, company)

    with st.spinner("Generating interview questions..."):
        interview_questions = generate_interview_questions(structured, company or "the company")

    with st.spinner("Building PDF report..."):
        tmp_path = os.path.join(tempfile.gettempdir(), "resumeiq_report.pdf")
        build_pdf_report(tmp_path, structured, score_result, match_result,
                          cover_letter, interview_questions)
        with open(tmp_path, "rb") as f:
            report_bytes = f.read()

    st.session_state["raw_text"] = raw_text
    st.session_state["structured"] = structured
    st.session_state["score_result"] = score_result
    st.session_state["match_result"] = match_result
    st.session_state["cover_letter"] = cover_letter
    st.session_state["interview_questions"] = interview_questions
    st.session_state["report_bytes"] = report_bytes


if analyze_clicked or use_sample:
    if use_sample:
        sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
        with open(os.path.join(sample_dir, "sample_resume.txt"), "r") as f:
            raw_text = parse_resume_text(f.read())
        with open(os.path.join(sample_dir, "sample_job_description.txt"), "r") as f:
            jd_text = f.read()
        company_name = company_name or "Acme Corp"
        run_pipeline(raw_text, jd_text, company_name)
    elif resume_file is None:
        st.warning("Upload a resume file first (or use the sample data option in the sidebar).")
    else:
        suffix = os.path.splitext(resume_file.name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(resume_file.getvalue())
            tmp_path = tmp.name
        try:
            raw_text = parse_resume_text(parse_resume_file(tmp_path))
        finally:
            os.unlink(tmp_path)
        run_pipeline(raw_text, jd_text, company_name)

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
if st.session_state["score_result"] is None:
    st.info("Upload a resume in the sidebar and click **Analyze Resume** to get started.")
    st.stop()

structured = st.session_state["structured"]
score_result = st.session_state["score_result"]
match_result = st.session_state["match_result"]
cover_letter = st.session_state["cover_letter"]
interview_questions = st.session_state["interview_questions"]

tab_overview, tab_scores, tab_match, tab_letter, tab_interview, tab_report = st.tabs(
    ["Overview", "Score Breakdown", "Job Match", "Cover Letter", "Interview Prep", "Download Report"]
)

# --- Overview tab ---
with tab_overview:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Overall Resume Score", f"{score_result['overall_score']}/100")
        if match_result:
            st.metric("Job Match Score", f"{match_result['job_match_score']}/100")
            st.metric("Interview Readiness", f"{match_result['interview_readiness']}/100")
    with col2:
        st.markdown("**Candidate**")
        st.write(f"Name: {structured.get('name') or '—'}")
        st.write(f"Email: {structured.get('email') or '—'}")
        st.write(f"Phone: {structured.get('phone') or '—'}")
        st.write(f"LinkedIn: {structured.get('linkedin') or '—'}")
        st.write(f"GitHub: {structured.get('github') or '—'}")
        st.markdown("**Skills detected**")
        st.write(", ".join(structured.get("skills", [])) or "None detected")

# --- Score breakdown tab ---
with tab_scores:
    chart_df = pd.DataFrame({
        "Metric": list(score_result["scores"].keys()),
        "Score": list(score_result["scores"].values()),
    }).set_index("Metric")
    st.bar_chart(chart_df, color=PRIMARY)

    for metric, value in score_result["scores"].items():
        with st.container(border=True):
            c1, c2 = st.columns([1, 4])
            with c1:
                st.markdown(f"**{metric}**")
                st.progress(value / 100)
                st.caption(f"{value}/100")
            with c2:
                for tip in score_result["suggestions"][metric]:
                    st.write(f"• {tip}")

# --- Job match tab ---
with tab_match:
    if match_result is None:
        st.info("Paste a job description in the sidebar and re-analyze to see the job match breakdown.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Job Match Score", f"{match_result['job_match_score']}/100")
        c2.metric("Matched Skills", len(match_result["matched_skills"]))
        c3.metric("Missing Skills", len(match_result["missing_skills"]))

        st.markdown("**✅ Matched skills**")
        st.write(", ".join(match_result["matched_skills"]) or "None")
        st.markdown("**⚠️ Missing skills**")
        st.write(", ".join(match_result["missing_skills"]) or "None")
        st.markdown("**💡 Recommended to add**")
        st.write(", ".join(match_result["recommended_to_add"]) or "None")

# --- Cover letter tab ---
with tab_letter:
    if cover_letter is None:
        st.info("Paste a job description in the sidebar and re-analyze to generate a cover letter.")
    else:
        st.text_area("Generated cover letter", cover_letter, height=400)
        st.download_button("Download cover letter (.txt)", cover_letter,
                            file_name="cover_letter.txt", mime="text/plain")

# --- Interview prep tab ---
with tab_interview:
    for category, questions in interview_questions.items():
        st.markdown(f"**{category.upper()}**")
        for q in questions:
            st.write(f"• {q}")
        st.markdown("")

# --- Download report tab ---
with tab_report:
    st.write("Export the full analysis - scores, job match, cover letter, and "
             "interview questions - as a single PDF report.")
    st.download_button(
        "📄 Download PDF Report",
        st.session_state["report_bytes"],
        file_name="resumeiq_report.pdf",
        mime="application/pdf",
        type="primary",
    )
