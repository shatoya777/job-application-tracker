import unittest

from matching import calculate_job_matches


class JobMatchingTests(unittest.TestCase):
    def test_required_skill_percentage_is_case_insensitive(self):
        jobs = [{
            "job_title": "Backend Developer",
            "requirements": '{"required_skills": ["Python", "SQL", "Flask"], "preferred_skills": ["Docker"]}',
        }]
        result = calculate_job_matches(jobs, ["python", "SQL"])[0]
        self.assertEqual(result["match_percentage"], 67)
        self.assertEqual(result["matched_skills"], ["Python", "SQL"])
        self.assertEqual(result["missing_skills"], ["Flask"])
        self.assertEqual(result["preferred_matches"], [])

    def test_preferred_skills_are_used_when_required_skills_are_absent(self):
        jobs = [{
            "job_title": "Support Intern",
            "requirements": {"preferred_skills": ["Linux", "Python"]},
        }]
        result = calculate_job_matches(jobs, ["Python"])[0]
        self.assertEqual(result["match_percentage"], 50)
        self.assertEqual(result["scoring_label"], "Preferred skills (used because no required skills were listed)")

    def test_job_without_skills_has_no_percentage(self):
        result = calculate_job_matches([{"job_title": "General Role", "requirements": None}], ["Python"])[0]
        self.assertIsNone(result["match_percentage"])
        self.assertEqual(result["missing_skills"], [])

    def test_jobs_are_ranked_by_percentage(self):
        jobs = [
            {"job_title": "Partial", "requirements": {"required_skills": ["Python", "SQL"]}},
            {"job_title": "Full", "requirements": {"required_skills": ["Python"]}},
        ]
        results = calculate_job_matches(jobs, ["Python", "SQL"])
        self.assertEqual([item["job_title"] for item in results], ["Full", "Partial"])

    def test_duplicate_required_skills_do_not_change_denominator(self):
        jobs = [{"job_title": "Role", "requirements": {"required_skills": ["SQL", "SQL", "Python"]}}]
        result = calculate_job_matches(jobs, ["SQL"])[0]
        self.assertEqual(result["skills_count"], 2)
        self.assertEqual(result["match_percentage"], 50)


if __name__ == "__main__":
    unittest.main()
