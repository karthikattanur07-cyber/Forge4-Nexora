"""
Smart explainer module for offline resume shortlisting.
Operates 100% locally with zero external API dependencies.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from schemas import CandidateExplanation, ScoredCandidate


class SmartExplainer:
    """Local, rule-based explanation and audit engine for candidates and job descriptions."""

    BIAS_RULES = [
        {
            "category": "Pedigree / Elitism Bias",
            "pattern": r"\b(?:tier\s*[-–—]?\s*(?:1|one)|top\s*[-–—]?\s*tier|ivy\s+league|premier\s+institutes?)\b",
            "description": "Favors candidates from specific elite institutions over evaluated competency.",
            "suggestion": "Focus on demonstrated technical skills and project outcomes rather than school pedigree.",
        },
        {
            "category": "Hyper-Competitive / Gender-Coded Buzzwords",
            "pattern": r"\b(?:rock\s*star|ninja|guru|wizard|code\s*jedi|hacker|superhero|work\s+hard\s*,?\s*play\s+hard)\b",
            "description": "Informal or aggressive buzzwords that can discourage qualified diverse applicants.",
            "suggestion": "Replace with objective terms such as 'skilled engineer', 'proficient developer', or 'collaborative builder'.",
        },
        {
            "category": "Arbitrary / Rigid Experience Threshold",
            "pattern": r"\b(?:\d+\+?\s*(?:-|to)?\s*\d*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)?)\b",
            "description": "Rigid experience thresholds (e.g., '3+ years experience') frequently exclude talented candidates with accelerated growth.",
            "suggestion": "Specify concrete competency levels, system complexity, or practical deliverables instead of fixed calendar years.",
        },
        {
            "category": "Age / Demographic Bias",
            "pattern": r"\b(?:young\s+and\s+energetic|digital\s+native|fresh\s+blood|energetic\s+youth)\b",
            "description": "Phrasing with implicit age bias that may exclude experienced or career-transitioning applicants.",
            "suggestion": "Focus on role attributes such as 'proactive problem solver' or 'motivated contributor'.",
        },
    ]

    def __init__(self, jd_skills: List[str], jd_text: str):
        """
        Initialize the explainer with job description skills and text.

        :param jd_skills: List of required or desired skills from the job description.
        :param jd_text: Full text of the job description.
        """
        self.jd_skills = [s.strip() for s in jd_skills if s and s.strip()]
        self.jd_text = jd_text

    def extract_skills(self, candidate_skills: List[str]) -> Tuple[List[str], List[str]]:
        """
        Extract matched and missing skills using set intersection and set difference.

        :param candidate_skills: List of skills from the candidate profile.
        :return: Tuple of (matched_skills, missing_skills).
        """
        cand_map = {s.strip().lower(): s.strip() for s in candidate_skills if s and s.strip()}
        jd_map = {s.strip().lower(): s.strip() for s in self.jd_skills if s and s.strip()}

        cand_set: Set[str] = set(cand_map.keys())
        jd_set: Set[str] = set(jd_map.keys())

        # Set intersection for matched skills and set difference for missing skills
        matched_keys: Set[str] = cand_set.intersection(jd_set)
        missing_keys: Set[str] = jd_set.difference(cand_set)

        matched_skills = [jd_map[k] for k in sorted(matched_keys)]
        missing_skills = [jd_map[k] for k in sorted(missing_keys)]

        return matched_skills, missing_skills

    def explain_candidate(
        self, candidate: ScoredCandidate, key_differentiator: Optional[str] = None
    ) -> CandidateExplanation:
        """
        Generate a natural 2-4 sentence explanation for a candidate (specifically tailored
        for ranks 1, 2, and 3), detailing matched skills, missing skills, and dynamic
        reasoning based on whether semantic or keyword score was higher.

        :param candidate: ScoredCandidate instance.
        :param key_differentiator: Optional manual override for candidate key differentiator.
        :return: CandidateExplanation instance.
        """
        matched_skills, missing_skills = self.extract_skills(candidate.skills)

        # Sentence 1: Rank placement and overall standing
        if candidate.rank == 1:
            rank_sentence = (
                f"{candidate.name} is the top-ranked candidate with a leading composite score of "
                f"{candidate.final_score:.2f}, demonstrating the strongest overall alignment with the target role."
            )
        elif candidate.rank == 2:
            rank_sentence = (
                f"{candidate.name} secures rank 2 with a competitive composite score of "
                f"{candidate.final_score:.2f}, standing out as a high-potential alternative for the position."
            )
        elif candidate.rank == 3:
            rank_sentence = (
                f"{candidate.name} is ranked 3rd with a solid composite score of "
                f"{candidate.final_score:.2f}, presenting a viable profile with clear baseline qualifications."
            )
        else:
            rank_sentence = (
                f"{candidate.name} holds rank {candidate.rank} with an overall evaluation score of "
                f"{candidate.final_score:.2f}."
            )

        # Sentence 2: Matched skills and missing skill coverage
        if matched_skills and missing_skills:
            matched_str = ", ".join(matched_skills[:5]) + ("..." if len(matched_skills) > 5 else "")
            missing_str = ", ".join(missing_skills[:4]) + ("..." if len(missing_skills) > 4 else "")
            skill_sentence = (
                f"The candidate successfully demonstrated {len(matched_skills)} required competencies ({matched_str}), "
                f"while missing {len(missing_skills)} target areas ({missing_str})."
            )
        elif matched_skills and not missing_skills:
            matched_str = ", ".join(matched_skills[:5]) + ("..." if len(matched_skills) > 5 else "")
            skill_sentence = (
                f"They achieved complete coverage across all target requirements ({matched_str}) with zero identified skill gaps."
            )
        else:
            missing_str = ", ".join(missing_skills[:4]) + ("..." if len(missing_skills) > 4 else "none specified")
            skill_sentence = (
                f"No direct keyword matches were detected from the primary job requirements ({missing_str}), "
                f"indicating a potential need for onboarding ramp-up."
            )

        # Sentence 3: Dynamic reasoning based on semantic vs keyword score
        score_delta = candidate.semantic_score - candidate.keyword_score
        if score_delta > 0.05:
            reasoning_sentence = (
                f"Their standing is predominantly driven by high semantic alignment "
                f"({candidate.semantic_score:.2f} semantic vs {candidate.keyword_score:.2f} keyword), "
                f"reflecting extensive conceptual depth and relevant hands-on project experience despite terminology variations."
            )
            default_differentiator = "Strong practical project depth and contextual domain knowledge"
        elif score_delta < -0.05:
            reasoning_sentence = (
                f"Their placement is anchored by precise keyword matching "
                f"({candidate.keyword_score:.2f} keyword vs {candidate.semantic_score:.2f} semantic), "
                f"reflecting direct mastery of the requested tech stack, though broader contextual framing scored lower."
            )
            default_differentiator = "Exact match against core toolchains and specific framework requirements"
        else:
            reasoning_sentence = (
                f"The candidate exhibits well-balanced competence with harmonized semantic ({candidate.semantic_score:.2f}) "
                f"and keyword ({candidate.keyword_score:.2f}) scores, confirming both vocabulary precision and practical background."
            )
            default_differentiator = "Balanced profile with simultaneous technical coverage and applied experience"

        # Combine into a natural 3-sentence summary
        summary = f"{rank_sentence} {skill_sentence} {reasoning_sentence}"
        differentiator = key_differentiator if key_differentiator else default_differentiator

        return CandidateExplanation(
            rank=candidate.rank,
            name=candidate.name,
            final_score=candidate.final_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            summary=summary,
            key_differentiator=differentiator,
        )

    def explain_top_candidates(
        self, candidates: List[ScoredCandidate], top_n: int = 3
    ) -> List[CandidateExplanation]:
        """
        Generate explanations for the top N candidates (default: ranks 1, 2, and 3).

        :param candidates: List of ScoredCandidate objects.
        :param top_n: Number of top candidates to explain.
        :return: List of CandidateExplanation objects.
        """
        sorted_candidates = sorted(candidates, key=lambda c: c.rank)[:top_n]
        return [self.explain_candidate(c) for c in sorted_candidates]

    def compare_candidates(self, candidate_a: ScoredCandidate, candidate_b: ScoredCandidate) -> str:
        """
        Compare two ScoredCandidate objects and explain why one ranked higher based on
        score margin and exclusive skills.

        :param candidate_a: First ScoredCandidate.
        :param candidate_b: Second ScoredCandidate.
        :return: Explanation string explaining ranking divergence.
        """
        if candidate_a.rank == candidate_b.rank and candidate_a.final_score == candidate_b.final_score:
            return (
                f"{candidate_a.name} and {candidate_b.name} are tied at rank {candidate_a.rank} "
                f"with an identical final score of {candidate_a.final_score:.2f}."
            )

        # Identify higher and lower ranked candidates
        if candidate_a.rank < candidate_b.rank or (
            candidate_a.rank == candidate_b.rank and candidate_a.final_score > candidate_b.final_score
        ):
            higher, lower = candidate_a, candidate_b
        else:
            higher, lower = candidate_b, candidate_a

        score_margin = higher.final_score - lower.final_score
        semantic_margin = higher.semantic_score - lower.semantic_score
        keyword_margin = higher.keyword_score - lower.keyword_score

        # Determine exclusive skills using set operations
        higher_map = {s.strip().lower(): s.strip() for s in higher.skills if s.strip()}
        lower_map = {s.strip().lower(): s.strip() for s in lower.skills if s.strip()}

        higher_set = set(higher_map.keys())
        lower_set = set(lower_map.keys())

        higher_exclusive_keys = higher_set.difference(lower_set)
        lower_exclusive_keys = lower_set.difference(higher_set)

        higher_exclusive = [higher_map[k] for k in sorted(higher_exclusive_keys)]
        lower_exclusive = [lower_map[k] for k in sorted(lower_exclusive_keys)]

        # Construct exclusive skill commentary
        higher_skills_desc = (
            f"exclusive skills in {', '.join(higher_exclusive)}"
            if higher_exclusive
            else "no unique skills over the runner-up"
        )
        lower_skills_desc = (
            f"brings separate expertise in {', '.join(lower_exclusive)}"
            if lower_exclusive
            else "offers no distinct skills not already covered by the leader"
        )

        # Determine primary score factor
        if semantic_margin > keyword_margin and semantic_margin > 0:
            driver = (
                f"contextual experience depth ({higher.semantic_score:.2f} vs {lower.semantic_score:.2f} semantic score)"
            )
        elif keyword_margin > semantic_margin and keyword_margin > 0:
            driver = (
                f"direct keyword match density ({higher.keyword_score:.2f} vs {lower.keyword_score:.2f} keyword score)"
            )
        else:
            driver = (
                f"concurrent advantages in both semantic relevance (+{semantic_margin:.2f}) and keyword precision (+{keyword_margin:.2f})"
            )

        explanation = (
            f"{higher.name} (Rank {higher.rank}, Score {higher.final_score:.2f}) outranked {lower.name} "
            f"(Rank {lower.rank}, Score {lower.final_score:.2f}) by a margin of {score_margin:.2f} points. "
            f"The key performance driver was higher's superior {driver}. "
            f"In terms of skill divergence, {higher.name} holds {higher_skills_desc}, whereas {lower.name} {lower_skills_desc}."
        )
        return explanation

    def audit_jd_bias(self, text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Audit job description text using regex to flag exclusionary or biased phrasing
        such as 'tier-1', 'rockstar', or '3+ years experience'.

        :param text: Optional custom text to audit. If None, audits self.jd_text.
        :return: List of detected bias findings with category, matched term, span, and recommendations.
        """
        content = text if text is not None else self.jd_text
        findings: List[Dict[str, Any]] = []

        if not content:
            return findings

        for rule in self.BIAS_RULES:
            pattern = re.compile(rule["pattern"], re.IGNORECASE)
            for match in pattern.finditer(content):
                matched_text = match.group(0)
                start, end = match.span()

                # Extract surrounding snippet for context (up to 30 chars before and after)
                snippet_start = max(0, start - 30)
                snippet_end = min(len(content), end + 30)
                snippet = content[snippet_start:snippet_end].replace("\n", " ").strip()

                findings.append(
                    {
                        "category": rule["category"],
                        "matched_term": matched_text,
                        "span": (start, end),
                        "snippet": f"...{snippet}...",
                        "description": rule["description"],
                        "suggestion": rule["suggestion"],
                    }
                )

        return findings
