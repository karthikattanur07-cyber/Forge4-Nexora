from rapidfuzz import fuzz


SKILL_SYNONYMS = {
    "ml": "machine learning",
    "machine-learning": "machine learning",
    "ai": "artificial intelligence",

    "rest api": "rest api",
    "rest apis": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",

    "node": "node.js",
    "nodejs": "node.js",

    "reactjs": "react",
    "react.js": "react",

    "postgres": "postgresql",
    "postgres db": "postgresql",

    "mongo": "mongodb",
    "mongo db": "mongodb",

    "js": "javascript",
    "ts": "typescript",

    "k8s": "kubernetes",
}


def normalize_skill(skill):
    """
    Normalize skill names so equivalent skills
    can be matched.
    """

    skill = skill.lower().strip()

    return SKILL_SYNONYMS.get(
        skill,
        skill
    )


def keyword_score(
    jd_skills,
    resume_explicit_skills,
    resume_indirect_skills=None
):
    """
    Compare JD skills against resume skills.

    JD:
        skills_mentioned

    Resume:
        skills_explicit
        skills_indirect

    Uses:
        1. Skill normalization
        2. Exact matching
        3. Fuzzy matching
        4. Explicit + indirect skills

    Returns:
        score
        matched_skills
        missing_skills
    """

    if not jd_skills:

        return {
            "score": 0.0,
            "matched_skills": [],
            "missing_skills": []
        }

    if resume_indirect_skills is None:
        resume_indirect_skills = []

    # Normalize JD skills

    normalized_jd_skills = [
        normalize_skill(skill)
        for skill in jd_skills
    ]

    # Combine explicit + indirect skills

    resume_skills = (
        resume_explicit_skills
        + resume_indirect_skills
    )

    normalized_resume_skills = [
        normalize_skill(skill)
        for skill in resume_skills
    ]

    total_score = 0

    matched_skills = []
    missing_skills = []

    for index, jd_skill in enumerate(
        normalized_jd_skills
    ):

        best_match_score = 0

        for resume_skill in normalized_resume_skills:

            # Exact match

            if jd_skill == resume_skill:

                match_score = 1.0

            # Fuzzy match

            else:

                similarity = fuzz.token_set_ratio(
                    jd_skill,
                    resume_skill
                )

                if similarity >= 85:

                    match_score = similarity / 100

                else:

                    match_score = 0

            best_match_score = max(
                best_match_score,
                match_score
            )

        total_score += best_match_score

        original_skill = jd_skills[index]

        if best_match_score > 0:

            matched_skills.append(
                original_skill
            )

        else:

            missing_skills.append(
                original_skill
            )

    score = (
        total_score
        / len(normalized_jd_skills)
    )

    return {
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }


if __name__ == "__main__":

    # Sample JD from Data Dev

    jd_skills = [
        "Data Structures & Algorithms",
        "Express.js",
        "Git/Version Control",
        "HTML/CSS",
        "JavaScript",
        "MongoDB",
        "Node.js",
        "REST API",
        "React"
    ]

    # Sample resume skills from Rahul Bose

    resume_explicit_skills = [
        "React",
        "Node.js"
    ]

    resume_indirect_skills = [
        "Express.js"
    ]

    result = keyword_score(
        jd_skills,
        resume_explicit_skills,
        resume_indirect_skills
    )

    print("\nKeyword Matching Result")
    print("-----------------------")

    print(
        "Keyword score:",
        result["score"]
    )

    print(
        "Keyword score (%):",
        round(
            result["score"] * 100,
            2
        )
    )

    print(
        "Matched skills:",
        result["matched_skills"]
    )

    print(
        "Missing skills:",
        result["missing_skills"]
    )