"""Skill matching logic for job applications."""

import json
from typing import Any

"""Normalize a skill string for comparison purposes.
This function lowercases the string, removes leading and trailing whitespace,
and collapses multiple spaces into a single space."""
def _normalize_skill(value: str) -> str:
    return " ".join(value.casefold().strip().split())

"""Convert a value to a dictionary if possible."""
def _requirements_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    return {}

"""Calculate the match percentage of jobs based on user skills."""
def calculate_job_matches(jobs: list[dict[str, Any]], user_skills: list[str]) -> list[dict[str, Any]]:
    skill_lookup = {_normalize_skill(skill) for skill in user_skills if skill.strip()}
    results: list[dict[str, Any]] = []

    """Iterate through each job, extract required and preferred skills,"""
    for original in jobs:
        job = dict(original)
        requirements = _requirements_dict(job.get("requirements"))
        required = requirements.get("required_skills") or []
        preferred = requirements.get("preferred_skills") or []
        required = [str(item).strip() for item in required if isinstance(item, (str, int, float)) and str(item).strip()] if isinstance(required, list) else []
        preferred = [str(item).strip() for item in preferred if isinstance(item, (str, int, float)) and str(item).strip()] if isinstance(preferred, list) else []

        """Helper function to get unique skills while preserving order."""
        def unique_skills(values: list[str]) -> list[str]:
            seen: set[str] = set()
            unique: list[str] = []
            for skill in values:
                key = _normalize_skill(skill)
                if key and key not in seen:
                    seen.add(key)
                    unique.append(skill)
            return unique

        required = unique_skills(required)
        preferred = unique_skills(preferred)
        scoring_skills = required if required else preferred
        if required:
            scoring_label = "Required skills"
        elif preferred:
            scoring_label = "Preferred skills (used because no required skills were listed)"
        else:
            scoring_label = "No skills listed"

        matched = [skill for skill in scoring_skills if _normalize_skill(skill) in skill_lookup]
        missing = [skill for skill in scoring_skills if _normalize_skill(skill) not in skill_lookup]
        preferred_matches = [skill for skill in preferred if _normalize_skill(skill) in skill_lookup]
        percentage = round((len(matched) / len(scoring_skills)) * 100) if scoring_skills else None

        job.update({
            "match_percentage": percentage,
            "matched_skills": matched,
            "missing_skills": missing,
            "preferred_matches": preferred_matches,
            "scoring_label": scoring_label,
            "skills_count": len(scoring_skills),
        })
        results.append(job)

    results.sort(key=lambda item: (
        item["match_percentage"] is None,
        -(item["match_percentage"] or 0),
        (item.get("job_title") or "").casefold(),
    ))
    return results
