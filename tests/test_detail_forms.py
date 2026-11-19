"""Exercise structured detail fields through the Flask routes."""

import json
import unittest
from unittest.mock import patch

from app import create_app


class DetailFormTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = app.test_client()
        self.job = {"job_id": 1, "company_id": 2, "job_title": "Developer", "company_name": "Example"}
        self.application = dict(self.job, application_id=3, status="Interview", application_date="2026-10-01")

    def test_job_creation_feeds_job_match(self):
        with patch("database.fetch_all", return_value=[self.job]) as fetch_all, patch("database.execute_write") as write:
            response = self.client.post("/jobs/new", data={
                "company_id": "2", "job_title": "Developer", "is_active": "on",
                "required_skills": " Python, SQL, , ", "preferred_skills": " Docker ",
                "experience_years": "0", "remote_option": "no",
            })
            self.assertEqual(response.status_code, 302)
            stored = write.call_args.args[1][-1]
            self.assertEqual(json.loads(stored), {
                "required_skills": ["Python", "SQL"], "preferred_skills": ["Docker"],
                "experience_years": 0, "remote_option": False,
            })
            fetch_all.return_value = [dict(self.job, requirements=stored)]
            result = self.client.post("/job-match", data={"skills": "python, docker"}).get_data(as_text=True)
            self.assertIn("50%", result)
            self.assertIn("Also matches preferred skills: Docker", result)

    def test_job_edit_prefills_and_preserves_stored_properties(self):
        original = {
            "required_skills": ["Python", "Research, development", 5],
            "preferred_skills": ["Docker"], "experience_years": 0,
            "remote_option": False, "certification": {"options": ["AWS", "Azure"]},
        }
        job = dict(self.job, requirements=json.dumps(original))
        with patch("database.fetch_one", return_value=job), patch("database.fetch_all", side_effect=[[self.job], [self.job], []]), patch("database.execute_write") as write:
            form = self.client.get("/jobs/1/edit").get_data(as_text=True)
            self.assertIn('value="Python, Research, development, 5"', form)
            self.assertIn('value="0"', form)
            self.assertIn('value="no" selected', form)
            response = self.client.post("/jobs/1/edit", data={
                "company_id": "2", "job_title": "Developer", "required_skills": "Python, Research, development, 5",
                "preferred_skills": "", "experience_years": "0", "remote_option": "no",
            })
            self.assertEqual(response.status_code, 302)
            del original["preferred_skills"]
            self.assertEqual(json.loads(write.call_args.args[1][-2]), original)
            detail = self.client.get("/jobs/1").get_data(as_text=True)
            self.assertIn("<li>Research, development</li>", detail)
            self.assertIn("<dt>Certification</dt>", detail)
            self.assertIn("<dd><ul><li>AWS</li><li>Azure</li></ul></dd>", detail)
            self.assertNotIn("<pre", detail)

    def test_interview_creation_and_validation(self):
        with patch("database.fetch_all", return_value=[self.job]), patch("database.execute_write") as write:
            form = {"job_id": "1", "application_date": "2026-10-01", "status": "Interview",
                    "interview_rounds": "-1", "interviewers": "Jordan, Sam",
                    "technical_questions": "Explain joins.\r\n\r\nDescribe an index."}
            response = self.client.post("/applications/new", data=form).get_data(as_text=True)
            self.assertIn("Interview rounds cannot be negative.", response)
            self.assertIn('value="Jordan, Sam"', response)
            write.assert_not_called()
            response = self.client.post("/applications/new", data=dict(form, interview_rounds="2"))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(json.loads(write.call_args.args[1][-1]), {
                "interview_rounds": 2, "interviewers": ["Jordan", "Sam"],
                "technical_questions": ["Explain joins.", "Describe an index."],
            })

    def test_interview_edit_preserves_extra_details_and_escapes_display(self):
        original = {"interview_rounds": 2, "interviewers": ["Jordan", "Sam"],
                    "feedback": "First line\nSecond line", "schedule": [{"room": "<script>"}]}
        application = dict(self.application, interview_data=original)
        with patch("database.fetch_one", return_value=application), patch("database.fetch_all", return_value=[self.job]), patch("database.execute_write") as write:
            form = self.client.get("/applications/3/edit").get_data(as_text=True)
            self.assertIn('value="Jordan, Sam"', form)
            self.assertIn("First line\nSecond line", form)
            response = self.client.post("/applications/3/edit", data={
                "job_id": "1", "application_date": "2026-10-01", "status": "Interview",
                "feedback": "First line\r\nSecond line", "next_steps": "Send availability",
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(json.loads(write.call_args.args[1][-2]), dict(original, next_steps="Send availability"))
            detail = self.client.get("/applications/3").get_data(as_text=True)
            self.assertIn("<dt>Schedule</dt>", detail)
            self.assertIn("&lt;script&gt;", detail)
            self.assertNotIn("<pre", detail)
