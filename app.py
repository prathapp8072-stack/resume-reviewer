import streamlit as st
import PyPDF2
import docx
import os
from anthropic import Anthropic

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="AI Resume Reviewer", page_icon="📄", layout="centered")

# Put your Anthropic API key here or set it as an environment variable
# Option 1: set env var ANTHROPIC_API_KEY before running
# Option 2: paste it directly below (not recommended for public deployment)
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

client = Anthropic(api_key=API_KEY) if API_KEY else None


# -----------------------------
# TEXT EXTRACTION FUNCTIONS
# -----------------------------
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_text_from_docx(file):
    document = docx.Document(file)
    text = "\n".join([para.text for para in document.paragraphs])
    return text


def extract_resume_text(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        return None


# -----------------------------
# AI REVIEW FUNCTION
# -----------------------------
def review_resume(resume_text, job_role=""):
    role_context = f"The candidate is targeting a role as: {job_role}." if job_role else ""

    prompt = f"""You are an expert resume reviewer and career coach.
Review the following resume text and provide feedback in this exact structure:

1. Overall Score (out of 10)
2. Strengths (3-5 bullet points)
3. Weaknesses / Areas to Improve (3-5 bullet points)
4. Formatting & Structure Feedback
5. Suggested Improvements (specific, actionable)
6. Missing Keywords (if a target role is given)

{role_context}

Resume:
\"\"\"
{resume_text}
\"\"\"
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("📄 AI Resume Reviewer")
st.write("Upload your resume (PDF or DOCX) and get instant AI-powered feedback.")

if not client:
    st.warning("⚠️ No API key found. Set the ANTHROPIC_API_KEY environment variable before running the app.")

job_role = st.text_input("Target job role (optional)", placeholder="e.g. Data Analyst, Software Engineer")

uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

if uploaded_file is not None:
    with st.spinner("Extracting text from your resume..."):
        resume_text = extract_resume_text(uploaded_file)

    if not resume_text or len(resume_text.strip()) < 20:
        st.error("Could not extract text from this file. Try a different file.")
    else:
        with st.expander("View extracted resume text"):
            st.text(resume_text)

        if st.button("Review My Resume"):
            if not client:
                st.error("API key missing. Cannot run review.")
            else:
                with st.spinner("Analyzing your resume..."):
                    feedback = review_resume(resume_text, job_role)
                st.subheader("📝 Resume Feedback")
                st.markdown(feedback)
