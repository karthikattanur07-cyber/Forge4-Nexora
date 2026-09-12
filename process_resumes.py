"""
Resume Processing and Offline Evaluation Pipeline.
Computes Keyword Fit, Semantic Fit, and composite Final Score for candidate resumes.
Outputs rankings.json matching the evaluation schema.
Operates 100% locally with zero external API dependencies.
"""

import glob
import json
import os
import re
from typing import Any, Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


# Default skill matching patterns and synonyms
SKILL_PATTERNS: Dict[str, List[str]] = {
    "javascript": ["javascript", "js", "es6", "es6+"],
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node"],
    "express": ["express", "express.js", "expressjs"],
    "rest apis": ["rest api", "rest apis", "restful api", "restful apis", "rest"],
    "mongodb": ["mongodb", "mongo"],
    "postgresql": ["postgresql", "postgres"],
    "sql": ["sql", "mysql", "nosql", "sqlite"],
    "git": ["git", "github"],
    "typescript": ["typescript", "ts"],
    "docker": ["docker", "containerization"],
    "aws": ["aws", "ec2", "s3", "cloud"],
    "jest": ["jest", "mocha", "testing"],
    "agile": ["agile", "scrum"],
}


def extract_text_from_file(file_path: str) -> str:
    """Extract raw text from PDF or text file."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(file_path)
                pages_text = [p.extract_text() or "" for p in reader.pages]
                return "\n".join(pages_text).strip()
            except Exception as e:
                print(f"[Warning] pypdf failed on {file_path}: {e}")

        if pdfplumber is not None:
            try:
                with pdfplumber.open(file_path) as pdf:
                    pages_text = [p.extract_text() or "" for p in pdf.pages]
                    return "\n".join(pages_text).strip()
            except Exception as e:
                print(f"[Warning] pdfplumber failed on {file_path}: {e}")

    # Fallback / Plain text file
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            # If the text file happens to be a raw PDF binary
            if content.startswith("%PDF") and pypdf is not None:
                reader = pypdf.PdfReader(file_path)
                pages_text = [p.extract_text() or "" for p in reader.pages]
                return "\n".join(pages_text).strip()
            return content.strip()
    except Exception as e:
        print(f"[Error] Failed to read {file_path}: {e}")
        return ""


def extract_candidate_name(file_path: str, text: str) -> str:
    """Extract candidate name from file name or header."""
    base = os.path.basename(file_path)
    stem = os.path.splitext(base)[0]

    # Pattern: Resume_01_Aditi_Sharma -> Aditi Sharma
    cleaned_filename = re.sub(r"^(?:Resume_)?\d+[_\-\s]*", "", stem, flags=re.IGNORECASE)
    cleaned_filename = cleaned_filename.replace("_", " ").strip()

    # Check header of resume
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        first_line = lines[0]
        # If first line looks like a valid candidate name (2-4 words, no email/phone)
        if (
            2 <= len(first_line.split()) <= 4
            and "@" not in first_line
            and not re.search(r"\d{4,}", first_line)
            and len(first_line) < 40
        ):
            return first_line

    if cleaned_filename:
        return cleaned_filename

    return "Unknown Candidate"


def match_skills(text: str, jd_skills: List[str]) -> List[str]:
    """Detect which JD skills are matched in candidate resume."""
    text_lower = text.lower()
    matched = []

    for skill in jd_skills:
        skill_clean = skill.strip().lower()
        synonyms = SKILL_PATTERNS.get(skill_clean, [skill_clean])
        # Build regex pattern for skill and its synonyms
        pattern = r"\b(?:" + "|".join(re.escape(syn) for syn in synonyms) + r")\b"
        if re.search(pattern, text_lower):
            matched.append(skill_clean)

    return matched


def compute_keyword_fit(matched_skills: List[str], jd_skills: List[str]) -> float:
    """Compute keyword match percentage (0.0 to 100.0)."""
    if not jd_skills:
        return 0.0
    ratio = len(matched_skills) / len(jd_skills)
    return round(min(100.0, ratio * 100.0), 1)


def compute_semantic_fits(jd_text: str, resume_texts: List[str]) -> List[float]:
    """
    Compute offline context/lexical similarity using TF-IDF cosine similarity
    calibrated to a realistic 0-100 percentage scale.
    """
    if not resume_texts:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
        max_features=5000,
    )

    all_docs = [jd_text] + resume_texts
    tfidf_matrix = vectorizer.fit_transform(all_docs)

    jd_vector = tfidf_matrix[0:1]
    resume_vectors = tfidf_matrix[1:]

    raw_cosines = cosine_similarity(jd_vector, resume_vectors)[0]

    min_c = float(raw_cosines.min())
    max_c = float(raw_cosines.max())

    # Map raw cosine range to realistic evaluation scale [20.0, 95.0]
    scaled_scores = []
    for cos in raw_cosines:
        if max_c > min_c:
            norm = (cos - min_c) / (max_c - min_c)
            # Scale from 20.0 to 94.0
            score = 20.0 + (norm * 74.0)
        else:
            score = 50.0
        scaled_scores.append(round(score, 1))

    return scaled_scores


def process_all_resumes(
    resumes_dir: str = "test_resumes",
    jd_file: str = "jd.json",
    output_file: str = "rankings.json",
) -> List[Dict[str, Any]]:
    """Process all resumes in directory and export rankings.json."""
    if not os.path.exists(jd_file):
        raise FileNotFoundError(f"Job description file {jd_file} not found!")

    with open(jd_file, "r", encoding="utf-8") as f:
        jd_data = json.load(f)

    jd_skills = jd_data.get("skills", [])
    jd_text = jd_data.get("text", "")

    # Locate resume files (.pdf and .txt)
    target_dir = resumes_dir if os.path.exists(resumes_dir) else "Testing Dataset"
    pattern_pdf = os.path.join(target_dir, "*.pdf")
    pattern_txt = os.path.join(target_dir, "*.txt")
    file_paths = sorted(glob.glob(pattern_pdf) + glob.glob(pattern_txt))

    if not file_paths:
        raise FileNotFoundError(f"No resume files found in {target_dir}")

    print(f"Found {len(file_paths)} resumes in '{target_dir}'. Processing...")

    resumes_data = []
    resume_texts = []

    for file_path in file_paths:
        text = extract_text_from_file(file_path)
        name = extract_candidate_name(file_path, text)
        matched = match_skills(text, jd_skills)
        kw_fit = compute_keyword_fit(matched, jd_skills)

        resumes_data.append(
            {
                "file_path": file_path,
                "name": name,
                "matched_skills": matched,
                "keyword_score": kw_fit,
            }
        )
        resume_texts.append(text)

    # Compute semantic fits across all candidate resumes
    semantic_scores = compute_semantic_fits(jd_text, resume_texts)

    scored_candidates = []
    for cand_info, sem_score in zip(resumes_data, semantic_scores):
        kw_score = cand_info["keyword_score"]
        # Final Score: (0.6 * Semantic Fit) + (0.4 * Keyword Fit)
        final_score = round((0.6 * sem_score) + (0.4 * kw_score), 1)

        scored_candidates.append(
            {
                "name": cand_info["name"],
                "final_score": final_score,
                "semantic_score": sem_score,
                "keyword_score": kw_score,
                "skills": cand_info["matched_skills"],
            }
        )

    # Sort descending by final_score
    scored_candidates.sort(key=lambda c: c["final_score"], reverse=True)

    # Assign IDs: cand_1, cand_2, ...
    rankings_output = []
    for idx, cand in enumerate(scored_candidates):
        rankings_output.append(
            {
                "id": f"cand_{idx + 1}",
                "name": cand["name"],
                "final_score": cand["final_score"],
                "semantic_score": cand["semantic_score"],
                "keyword_score": cand["keyword_score"],
                "skills": cand["skills"],
            }
        )

    # Write output to rankings.json
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(rankings_output, f, indent=2)

    print(f"Successfully exported {len(rankings_output)} candidates to '{output_file}'.")
    return rankings_output


if __name__ == "__main__":
    process_all_resumes()
