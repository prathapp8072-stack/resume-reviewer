import re
import streamlit as st
import PyPDF2
import docx

st.set_page_config(page_title="Resume Reviewer", page_icon="📄", layout="centered")

ACTION_VERBS = [
    "achieved", "built", "created", "designed", "developed", "led", "managed",
    "improved", "increased", "reduced", "launched", "implemented", "organized",
    "delivered", "coordinated", "analyzed", "researched", "solved", "optimized",
    "automated", "negotiated", "trained", "mentored", "presented", "planned"
]

SECTION_KEYWORDS = {
    "Contact Info": ["email", "phone", "linkedin", "@"],
    "Education": ["education", "university", "college", "degree", "bachelor", "master"],
    "Experience": ["experience", "work history", "employment"],
    "Skills": ["skills", "technologies", "tools", "proficient"],
    "Projects": ["project", "projects"],
}

WEAK_PHRASES = [
    "responsible for", "duties included", "worked on", "helped with", "involved in"
]


def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_text_from_docx(file):
    document = docx.Document(file)
    return "\n".join([para.text for para in document.paragraphs])


def extract_resume_text(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    return None


def analyze_resume(text, job_role=""):
    lower_text = text.lower()
    word_count = len(text.split())

    score = 0
    max_score = 10
    strengths = []
    weaknesses = []
    suggestions = []

    if 300 <= word_count <= 900:
        score += 2
        strengths.append(f"Good resume length ({word_count} words).")
    elif word_count < 300:
        weaknesses.append(f"Resume seems short ({word_count} words). It may lack detail.")
        suggestions.append("Add more detail about your experience, projects, and skills.")
    else:
        weaknesses.append(f"Resume seems long ({word_count} words). Recruiters often skim quickly.")
        suggestions.append("Try trimming to the most relevant, impactful points (aim for 1-2 pages).")

    found_sections = []
    missing_sections = []
    for section, keywords in SECTION_KEYWORDS.items():
        if any(kw in lower_text for kw in keywords):
            found_sections.append(section)
        else:
            missing_sections.append(section)

    section_score = round((len(found_sections) / len(SECTION_KEYWORDS)) * 3)
    score += section_score

    if found_sections:
        strengths.append(f"Includes key sections: {', '.join(found_sections)}.")
    if missing_sections:
        weaknesses.append(f"Missing or unclear sections: {', '.join(missing_sections)}.")
        suggestions.append(f"Add clear headings for: {', '.join(missing_sections)}.")

    verbs_found = [v for v in ACTION_VERBS if v in lower_text]
    if len(verbs_found) >= 5:
        score += 2
        strengths.append(f"Uses strong action verbs (e.g. {', '.join(verbs_found[:5])}).")
    elif len(verbs_found) >= 2:
        score += 1
        weaknesses.append("Uses some action verbs, but could use more variety.")
        suggestions.append("Start bullet points with action verbs like 'led', 'built', 'improved'.")
    else:
        weaknesses.append("Few or no strong action verbs found.")
        suggestions.append("Rewrite bullet points to start with action verbs (e.g. 'Developed...', 'Managed...').")

    weak_found = [p for p in WEAK_PHRASES if p in lower_text]
    if weak_found:
        weaknesses.append(f"Contains passive/weak phrases: {', '.join(weak_found)}.")
        suggestions.append("Replace weak phrases with specific achievements and numbers (e.g. 'Reduced costs by 15%').")
    else:
        score += 1
        strengths.append("Avoids generic/passive phrases.")

    has_numbers = bool(re.search(r'\d+%|\d+\+|\$\d+|\d{2,}', text))
    if has_numbers:
        score += 2
        strengths.append("Includes quantifiable results/numbers (great for impact).")
    else:
        weaknesses.append("No numbers or measurable results found.")
        suggestions.append("Add metrics where possible (e.g. 'Increased sales by 20%', 'Managed team of 5').")

    role_match_note = None
    if job_role:
        role_words = [w.lower() for w in re.findall(r'\w+', job_role) if len(w) > 3]
        matched = [w for w in role_words if w in lower_text]
        missing = [w for w in role_words if w not in lower_text]
        if role_words:
            match_pct = round((len(matched) / len(role_words)) * 100)
            role_match_note = f"Keyword match with '{job_role}': {match_pct}% ({len(matched)}/{len(role_words)} terms found)."
            if missing:
                suggestions.append(f"Consider adding these role-related terms if relevant: {', '.join(missing)}.")

    score = min(score, max_score)

    return {
        "score": score,
        "max_score": max_score,
        "word_count": word_count,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "role_match_note": role_match_note,
    }


st.title("📄 Resume Reviewer")
st.write("Upload your resume (PDF or DOCX) and get instant feedback — no API key needed, everything runs locally.")

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
            with st.spinner("Analyzing your resume..."):
                result = analyze_resume(resume_text, job_role)

            st.subheader(f"📝 Overall Score: {result['score']} / {result['max_score']}")
            st.progress(result['score'] / result['max_score'])

            if result["role_match_note"]:
                st.info(result["role_match_note"])

            st.markdown("### ✅ Strengths")
            for s in result["strengths"]:
                st.markdown(f"- {s}")

            st.markdown("### ⚠️ Weaknesses")
            for w in result["weaknesses"]:
                st.markdown(f"- {w}")

            st.markdown("### 💡 Suggestions")
            for sug in result["suggestions"]:
                st.markdown(f"- {sug}")
