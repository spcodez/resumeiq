# ResumeIQ - AI Resume Analyzer & Career Copilot

A Python implementation of the ResumeIQ pipeline: instant ATS scoring, job
match intelligence, AI cover letters, and interview prep.

## Pipeline 

```
Resume (PDF/DOCX/TXT)
      │
      ▼
1. Upload & Parse         resumeiq/parsing.py     (pdfplumber / python-docx)
      │
      ▼
2. Structured Extraction  resumeiq/extraction.py  (regex + optional OpenAI JSON)
      │
      ▼
3. Multi-Metric Scoring   resumeiq/scoring.py      6 scores: ATS, Strength,
      │                                            Grammar, Keyword,
      │                                            Readability, Professional
      ▼
4. Job Match Engine       resumeiq/job_match.py    TF-IDF + skill overlap
      │
      ▼
5. Cover Letter + Prep    resumeiq/cover_letter.py, interview_prep.py
      │
      ▼
6. One-Click PDF Report   resumeiq/report.py       (reportlab)
```


## Install

```bash
pip install -r requirements.txt
```

## Streamlit Web App

A full browser UI is included in `app.py` — upload a resume, paste a job
description, and get the same pipeline (scores, job match, cover letter,
interview prep, PDF download) with no command-line usage required.

```bash
streamlit run app.py
```

This opens the app at `http://localhost:8501`. In the sidebar you can:
- Upload a `.pdf`, `.docx`, or `.txt` resume
- Paste a job description to unlock Job Match + Cover Letter
- Optionally enter an `OPENAI_API_KEY` to upgrade extraction/cover
  letter/interview questions to LLM-generated output
- Click "Load sample resume + JD" to try it instantly with the bundled
  sample data

Results appear across six tabs: Overview, Score Breakdown, Job Match, Cover
Letter, Interview Prep, and Download Report (PDF).

## CLI Usage

Analyze a resume on its own:

```bash
python -m resumeiq.cli --resume sample_data/sample_resume.txt --out report.pdf
```

Analyze against a job description (unlocks Job Match, Cover Letter, and
JD-aware Keyword scoring):

```bash
python -m resumeiq.cli \
    --resume sample_data/sample_resume.txt \
    --jd sample_data/sample_job_description.txt \
    --company "Acme Corp" \
    --out report.pdf \
    --json-out results.json
```

Supported resume formats: `.pdf`, `.docx`, `.txt`.

## Using it as a library

```python
from resumeiq import (
    parse_resume_file, extract_structured_data, score_resume,
    match_job, generate_cover_letter, generate_interview_questions,
    build_pdf_report,
)

text = parse_resume_file("resume.pdf")
structured = extract_structured_data(text)
result = score_resume(text, structured)               # 6-metric breakdown
print(result["overall_score"], result["scores"])

match = match_job(text, structured, job_description_text)
letter = generate_cover_letter(structured, match, job_description_text, "Acme Corp")
questions = generate_interview_questions(structured, "Acme Corp")

build_pdf_report("report.pdf", structured, result, match, letter, questions)
```

## Project layout

```
resumeiq/
  __init__.py         Public API
  skills_db.py         Skills taxonomy + strong/weak verb lists
  parsing.py           Stage 1: file -> raw text
  extraction.py         Stage 2: raw text -> structured JSON
  scoring.py            Stage 3: 6-metric scorer
  job_match.py          Job Match Engine
  cover_letter.py       AI Cover Letter Generator
  interview_prep.py     Interview Question Generator
  report.py             One-Click PDF Report
  cli.py                Command-line entry point
app.py                  Streamlit web app (streamlit run app.py)
sample_data/
  sample_resume.txt
  sample_job_description.txt
requirements.txt
```

## Notes on scoring methodology

- **ATS Score** - checks parseable formatting: contact info present, bullet
  structure, reasonable length, no unicode noise.
- **Strength** - ratio of strong action verbs (led, built, optimized...) to
  weak filler phrases (responsible for, helped...), plus quantified results.
- **Grammar** - lightweight rule-based checks (passive voice, first-person
  pronouns, spacing, tense consistency) - no network call required.
- **Keyword** - skill-keyword overlap against a job description (or general
  taxonomy density if no JD supplied).
- **Readability** - Flesch Reading Ease mapped to a resume-appropriate band.
- **Professional** - tone/polish heuristics: informal words, length, presence
  of LinkedIn/GitHub.
- **Job Match Score** - 70% skill-keyword coverage + 30% TF-IDF cosine
  similarity between resume and job description.

These are transparent, explainable heuristics by design (matching the deck's
"explainable, not a black box" principle on slide 9) - swap in the LLM path
via `OPENAI_API_KEY` for more nuanced, generative scoring when needed.



## SCREENSHOTS OF PROJECT 

 HOMEPAGE 

![alt text](<Screenshot 2026-07-12 123325.png>)

 OVERVIEW

![alt text](<Screenshot 2026-07-12 125338.png>)

![alt text](<Screenshot 2026-07-12 123510.png>)