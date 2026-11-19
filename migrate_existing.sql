-- One-time migration for the existing job_tracker database from Assignments 1-7.
-- BACK UP the database before running this file. MySQL DDL statements implicitly commit.
-- This migration preserves existing rows and keeps the extra columns from the assignments.
-- Do not run this against a fresh database created with schema.sql.

USE job_tracker;

-- 1. Convert older values to the final project's application status vocabulary.
--    Phone Screen -> Screening; Interview Completed -> Interview;
--    Offer Accepted -> Offer.
UPDATE applications
SET status = CASE status
    WHEN 'Phone Screen' THEN 'Screening'
    WHEN 'Interview Completed' THEN 'Interview'
    WHEN 'Offer Accepted' THEN 'Offer'
    ELSE status
END
WHERE application_id > 0
  AND status IN ('Phone Screen', 'Interview Completed', 'Offer Accepted');

-- 2. Enforce the ENUM values from the final project specification.
--    The current values reported for this database are all valid job types.
ALTER TABLE jobs
    MODIFY COLUMN job_type ENUM('Full-time', 'Part-time', 'Contract', 'Internship') DEFAULT NULL;

ALTER TABLE applications
    MODIFY COLUMN status ENUM('Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn')
    NOT NULL DEFAULT 'Applied';

-- 4. Combine first_name and last_name into the final contact_name column.
--    The current inspection showed the longest combined name was only 14 characters.
ALTER TABLE contacts
    ADD COLUMN contact_name VARCHAR(100) NULL AFTER company_id;

UPDATE contacts
SET contact_name = TRIM(CONCAT_WS(' ', first_name, last_name))
WHERE contact_id > 0;

ALTER TABLE contacts
    MODIFY COLUMN contact_name VARCHAR(100) NOT NULL,
    CHANGE COLUMN job_title title VARCHAR(100) DEFAULT NULL,
    DROP COLUMN first_name,
    DROP COLUMN last_name;

-- Note: the earlier assignments define salary_min and salary_max as DECIMAL(10,2),
-- while the final project specification says INT. This migration deliberately keeps
-- the existing DECIMAL columns to avoid silently truncating any stored salary values.
-- The application accepts these numeric values. Fresh installations use INT in schema.sql.

-- The application_summary table and assignment-added columns are not dropped.

