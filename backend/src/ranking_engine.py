from keyword_matcher import keyword_score
from semantic_matcher import semantic_score


def calculate_final_score(
    semantic,
    keyword,
    semantic_weight=0.5,
    keyword_weight=0.5
):
    """
    Combine semantic and keyword scores.

    semantic_weight:
        Importance given to experience/projects.

    keyword_weight:
        Importance given to explicit/indirect skills.
    """

    return (
        semantic_weight * semantic
        + keyword_weight * keyword
    )


def rank_candidates(
    jd,
    resumes,
    semantic_weight=0.5,
    keyword_weight=0.5
):
    """
    Calculate scores for all candidates and rank them.

    Expected JD structure:
        raw_text
        skills_mentioned

    Expected resume structure:
        file_name
        candidate_name
        raw_text
        sections
        skills_explicit
        skills_indirect
    """

    results = []

    # -----------------------------
    # JOB DESCRIPTION
    # -----------------------------

    jd_text = jd["raw_text"]

    jd_skills = jd["skills_mentioned"]

    # Check weights

    if round(
        semantic_weight + keyword_weight,
        2
    ) != 1.0:

        raise ValueError(
            "semantic_weight + keyword_weight "
            "must equal 1.0"
        )

    # -----------------------------
    # PROCESS EVERY RESUME
    # -----------------------------

    for resume in resumes:

        # -------------------------
        # RESUME TEXT
        # -------------------------

        sections = resume.get(
            "sections",
            {}
        )

        experience_text = sections.get(
            "Experience",
            ""
        )

        projects_text = sections.get(
            "Projects",
            ""
        )

        summary_text = sections.get(
            "Summary",
            ""
        )

        # Semantic matching focuses
        # primarily on experience + projects.

        resume_text = (
            experience_text
            + " "
            + projects_text
        )

        # -------------------------
        # KEYWORD MATCHING
        # -------------------------

        explicit_skills = resume.get(
            "skills_explicit",
            []
        )

        indirect_skills = resume.get(
            "skills_indirect",
            []
        )

        keyword_result = keyword_score(
            jd_skills,
            explicit_skills,
            indirect_skills
        )

        keyword = keyword_result["score"]

        # -------------------------
        # SEMANTIC MATCHING
        # -------------------------

        semantic = semantic_score(
            jd_text,
            resume_text
        )

        # -------------------------
        # FINAL SCORE
        # -------------------------

        final_score = calculate_final_score(
            semantic,
            keyword,
            semantic_weight,
            keyword_weight
        )

        # -------------------------
        # STORE RESULT
        # -------------------------

        results.append({

            "rank": 0,

            "name": resume.get(
                "candidate_name",
                "Unknown"
            ),

            "id": resume.get(
                "file_name",
                ""
            ),

            "final_score": round(
                final_score,
                4
            ),

            "semantic_score": round(
                semantic,
                4
            ),

            "keyword_score": round(
                keyword,
                4
            ),

            "matched_skills":
                keyword_result[
                    "matched_skills"
                ],

            "missing_skills":
                keyword_result[
                    "missing_skills"
                ]

        })

    # -----------------------------
    # RANK ALL CANDIDATES
    # -----------------------------

    results.sort(
        key=lambda candidate:
        candidate["final_score"],
        reverse=True
    )

    # Assign ranks after sorting

    for index, candidate in enumerate(
        results,
        start=1
    ):

        candidate["rank"] = index

    return results


if __name__ == "__main__":

    import json

    # -----------------------------
    # LOAD JD
    # -----------------------------

    with open(
        "data/jd.json",
        "r",
        encoding="utf-8"
    ) as file:

        jd = json.load(file)

    # -----------------------------
    # LOAD RESUMES
    # -----------------------------

    with open(
        "data/resumes.json",
        "r",
        encoding="utf-8"
    ) as file:

        resumes = json.load(file)

    # -----------------------------
    # RECRUITER WEIGHTS
    # -----------------------------

    keyword_weight = 0.7

    semantic_weight = 0.3

    # -----------------------------
    # RUN RANKING
    # -----------------------------

    rankings = rank_candidates(
        jd,
        resumes,
        semantic_weight=semantic_weight,
        keyword_weight=keyword_weight
    )

    # -----------------------------
    # SAVE RESULTS
    # -----------------------------

    with open(
        "rankings.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            rankings,
            file,
            indent=4
        )

    # -----------------------------
    # DISPLAY RESULTS
    # -----------------------------

    print(
        "\nRankings generated successfully!\n"
    )

    print(
        f"Skill Weight: "
        f"{keyword_weight * 100:.0f}%"
    )

    print(
        f"Experience/Project Weight: "
        f"{semantic_weight * 100:.0f}%\n"
    )

    for candidate in rankings:

        print(
            f"{candidate['rank']}. "
            f"{candidate['name']} "
            f"- Final: "
            f"{candidate['final_score']}"
        )

        print(
            f"   Semantic: "
            f"{candidate['semantic_score']}"
        )

        print(
            f"   Keyword: "
            f"{candidate['keyword_score']}"
        )

        print(
            f"   Matched: "
            f"{candidate['matched_skills']}"
        )

        print(
            f"   Missing: "
            f"{candidate['missing_skills']}"
        )

        print()