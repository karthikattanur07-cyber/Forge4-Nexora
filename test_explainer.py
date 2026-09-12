"""
Test script for verifying SmartExplainer functionality.
Tests top 3 explanations, candidate comparison, and JD bias auditing.
"""

from explainer import SmartExplainer
from schemas import ScoredCandidate


def run_tests():
    print("=" * 80)
    print("   OFFLINE RESUME SHORTLISTING SYSTEM - EXPLAINER VERIFICATION")
    print("=" * 80)

    # Sample Job Description
    sample_jd_skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis"]
    sample_jd_text = (
        "We are looking for a rockstar backend developer from a tier-1 institute. "
        "The ideal candidate must have 3+ years experience architecting cloud systems "
        "using Python, FastAPI, Docker, and AWS. We are seeking a young and energetic ninja "
        "who thrives in a high-pace environment."
    )

    # Initialize SmartExplainer
    explainer = SmartExplainer(jd_skills=sample_jd_skills, jd_text=sample_jd_text)

    # Create dummy candidates
    candidates = [
        ScoredCandidate(
            id="cand_001",
            name="Aria Montgomery",
            rank=1,
            final_score=0.93,
            semantic_score=0.97,
            keyword_score=0.87,
            skills=["Python", "FastAPI", "Docker", "AWS", "Redis", "Kubernetes", "GraphQL"],
        ),
        ScoredCandidate(
            id="cand_002",
            name="Liam Vance",
            rank=2,
            final_score=0.86,
            semantic_score=0.79,
            keyword_score=0.94,
            skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis", "MySQL"],
        ),
        ScoredCandidate(
            id="cand_003",
            name="Elena Rostova",
            rank=3,
            final_score=0.79,
            semantic_score=0.79,
            keyword_score=0.79,
            skills=["Python", "Docker", "PostgreSQL", "Linux", "Git"],
        ),
        ScoredCandidate(
            id="cand_004",
            name="David Kim",
            rank=4,
            final_score=0.68,
            semantic_score=0.70,
            keyword_score=0.65,
            skills=["Python", "Django", "SQLite"],
        ),
    ]

    # --------------------------------------------------------------------------
    # 1) Verify Top 3 Explanations Print Cleanly
    # --------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("1) TOP 3 CANDIDATE EXPLANATIONS")
    print("-" * 80)

    top_explanations = explainer.explain_top_candidates(candidates, top_n=3)
    assert len(top_explanations) == 3, f"Expected 3 explanations, got {len(top_explanations)}"

    for exp in top_explanations:
        print(f"\n[Rank #{exp.rank}] Candidate: {exp.name} (Final Score: {exp.final_score:.2f})")
        print(f"  • Matched Skills ({len(exp.matched_skills)}): {', '.join(exp.matched_skills)}")
        print(f"  • Missing Skills ({len(exp.missing_skills)}): {', '.join(exp.missing_skills) if exp.missing_skills else 'None'}")
        print(f"  • Key Differentiator: {exp.key_differentiator}")
        print(f"  • Explanation Summary:\n    \"{exp.summary}\"")

        # Verify summary contains 2-4 sentences
        sentences = [s.strip() for s in exp.summary.split(". ") if s.strip()]
        assert 2 <= len(sentences) <= 4, f"Explanation must be 2-4 sentences, got {len(sentences)}"

    # --------------------------------------------------------------------------
    # 2) Verify Candidate Comparison (compare_candidates)
    # --------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("2) CANDIDATE COMPARISON (Rank #1 Aria vs Rank #2 Liam)")
    print("-" * 80)

    comparison_text = explainer.compare_candidates(candidates[0], candidates[1])
    print(f"\n{comparison_text}\n")

    # Assertions on comparison output
    assert "Aria Montgomery" in comparison_text
    assert "Liam Vance" in comparison_text
    assert "margin of 0.07" in comparison_text or "0.07" in comparison_text
    assert "exclusive skills" in comparison_text.lower()
    assert "GraphQL" in comparison_text or "Kubernetes" in comparison_text

    # --------------------------------------------------------------------------
    # 3) Verify Job Description Bias Audit (audit_jd_bias)
    # --------------------------------------------------------------------------
    print("-" * 80)
    print("3) JOB DESCRIPTION BIAS AUDIT")
    print("-" * 80)

    bias_findings = explainer.audit_jd_bias()
    print(f"\nTotal Bias Flags Detected: {len(bias_findings)}\n")

    for idx, finding in enumerate(bias_findings, 1):
        print(f"[{idx}] Category   : {finding['category']}")
        print(f"    Matched Term: '{finding['matched_term']}' at span {finding['span']}")
        print(f"    Snippet     : {finding['snippet']}")
        print(f"    Description : {finding['description']}")
        print(f"    Suggestion  : {finding['suggestion']}")
        print()

    # Verify expected bias flags are detected
    flagged_terms = [f["matched_term"].lower() for f in bias_findings]
    assert any("rockstar" in term for term in flagged_terms), "Failed to flag 'rockstar'"
    assert any("tier-1" in term or "tier" in term for term in flagged_terms), "Failed to flag 'tier-1'"
    assert any("3+ years" in term for term in flagged_terms), "Failed to flag '3+ years experience'"

    print("=" * 80)
    print(" ALL CHECKS PASSED: Explanations, comparison, and bias audit validated!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
