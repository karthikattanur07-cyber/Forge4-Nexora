"""
Data schemas for the offline resume shortlisting system.
Uses standard library dataclasses with zero external dependencies.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class CandidateProfile:
    """Represents the parsed profile of a job candidate."""
    id: str
    name: str
    skills: List[str] = field(default_factory=list)
    experience_text: str = ""
    projects_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScoredCandidate:
    """Represents a candidate scored against job requirements."""
    id: str
    name: str
    rank: int
    final_score: float
    semantic_score: float
    keyword_score: float
    skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateExplanation:
    """Detailed explanation and breakdown for candidate evaluation."""
    rank: int
    name: str
    final_score: float
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    summary: str = ""
    key_differentiator: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
