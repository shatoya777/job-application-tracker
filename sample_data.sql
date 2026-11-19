-- Optional fictional demo data for a fresh installation only.
-- Run once, after schema.sql, if you want the instructor/demo environment pre-populated.
-- Do not run this against the user's existing populated database.

USE job_tracker;

INSERT INTO companies (company_name, industry, website, city, state, notes)
VALUES
('Northstar Software', 'Software', 'https://northstar.example', 'Miami', 'Florida', 'Fictional demo company'),
('Bluewave Analytics', 'Data Analytics', 'https://bluewave.example', 'Austin', 'Texas', 'Fictional demo company'),
('Cedar Cloud', 'Cloud Computing', 'https://cedarcloud.example', 'Orlando', 'Florida', 'Fictional demo company');

SET @northstar_id = (SELECT company_id FROM companies WHERE company_name = 'Northstar Software' ORDER BY company_id DESC LIMIT 1);
SET @bluewave_id = (SELECT company_id FROM companies WHERE company_name = 'Bluewave Analytics' ORDER BY company_id DESC LIMIT 1);
SET @cedar_id = (SELECT company_id FROM companies WHERE company_name = 'Cedar Cloud' ORDER BY company_id DESC LIMIT 1);

INSERT INTO jobs
(company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements, job_description, is_active)
VALUES
(@northstar_id, 'Junior Software Developer', 'Full-time', 65000, 85000, 'https://northstar.example/careers/junior-developer', '2026-10-01',
 JSON_OBJECT('required_skills', JSON_ARRAY('Python', 'SQL', 'Flask'), 'preferred_skills', JSON_ARRAY('Git', 'Docker'), 'education', 'Bachelor degree', 'experience_years', 0, 'remote_option', true),
 'Build and maintain web application features with the engineering team.', TRUE),
(@bluewave_id, 'Data Analyst', 'Full-time', 60000, 78000, 'https://bluewave.example/careers/data-analyst', '2026-10-04',
 JSON_OBJECT('required_skills', JSON_ARRAY('SQL', 'Excel', 'Tableau'), 'preferred_skills', JSON_ARRAY('Python', 'Power BI'), 'education', 'Bachelor degree', 'experience_years', 1, 'remote_option', false),
 'Prepare reports and analyze business data.', TRUE),
(@cedar_id, 'Cloud Support Intern', 'Internship', 35000, 45000, 'https://cedarcloud.example/careers/cloud-intern', '2026-10-09',
 JSON_OBJECT('required_skills', JSON_ARRAY('Linux', 'Networking'), 'preferred_skills', JSON_ARRAY('AWS', 'Python'), 'education', 'Currently enrolled student', 'experience_years', 0, 'remote_option', true),
 'Assist with cloud support and infrastructure documentation.', TRUE),
(@northstar_id, 'QA Automation Contractor', 'Contract', 50000, 70000, NULL, '2026-10-11',
 JSON_OBJECT('required_skills', JSON_ARRAY('Python', 'Testing', 'Git'), 'preferred_skills', JSON_ARRAY('Selenium', 'SQL')), 
 'Support test automation and regression testing.', TRUE);

SET @dev_job_id = (SELECT job_id FROM jobs WHERE job_title = 'Junior Software Developer' AND company_id = @northstar_id ORDER BY job_id DESC LIMIT 1);
SET @analyst_job_id = (SELECT job_id FROM jobs WHERE job_title = 'Data Analyst' AND company_id = @bluewave_id ORDER BY job_id DESC LIMIT 1);

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, notes)
VALUES
(@dev_job_id, '2026-10-12', 'Applied', 'Software Resume v1', TRUE, 'Fictional sample application'),
(@analyst_job_id, '2026-10-14', 'Screening', 'Data Resume v1', FALSE, 'Fictional sample application');

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes)
VALUES
(@northstar_id, 'Morgan Lee', 'Technical Recruiter', 'morgan.lee@northstar.example', NULL, NULL, 'Fictional sample contact'),
(@bluewave_id, 'Taylor Brooks', 'Data Team Lead', 'taylor.brooks@bluewave.example', NULL, NULL, 'Fictional sample contact');
