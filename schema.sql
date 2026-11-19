-- Job Application Tracker database
-- MySQL 8.0+
-- Creates a new database and the four tables for companies, jobs, applications, and contacts.

CREATE DATABASE IF NOT EXISTS job_tracker
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE job_tracker;

-- Table for storing company information
CREATE TABLE IF NOT EXISTS companies (
    company_id INT NOT NULL AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50) DEFAULT NULL,
    website VARCHAR(200) DEFAULT NULL,
    city VARCHAR(50) DEFAULT NULL,
    state VARCHAR(50) DEFAULT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (company_id),
    INDEX idx_company_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table for storing job postings
CREATE TABLE IF NOT EXISTS jobs (
    job_id INT NOT NULL AUTO_INCREMENT,
    company_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    job_type ENUM('Full-time', 'Part-time', 'Contract', 'Internship') DEFAULT NULL,
    salary_min INT DEFAULT NULL,
    salary_max INT DEFAULT NULL,
    job_url VARCHAR(300) DEFAULT NULL,
    date_posted DATE DEFAULT NULL,
    requirements JSON DEFAULT NULL,
    
    job_description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (job_id),
    INDEX idx_job_title (job_title),
    INDEX idx_company_type (company_id, job_type),
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table for storing job applications
CREATE TABLE IF NOT EXISTS applications (
    application_id INT NOT NULL AUTO_INCREMENT,
    job_id INT NOT NULL,
    application_date DATE NOT NULL,
    status ENUM('Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn')
        NOT NULL DEFAULT 'Applied',
    resume_version VARCHAR(50) DEFAULT NULL,
    cover_letter_sent BOOLEAN NOT NULL DEFAULT FALSE,
    interview_data JSON DEFAULT NULL,
    
    response_date DATE DEFAULT NULL,
    interview_date DATETIME DEFAULT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (application_id),
    INDEX idx_applications_job_id (job_id),
    INDEX idx_app_status (status),
    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table for storing contact information
CREATE TABLE IF NOT EXISTS contacts (
    contact_id INT NOT NULL AUTO_INCREMENT,
    company_id INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title VARCHAR(100) DEFAULT NULL,
    email VARCHAR(100) DEFAULT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    linkedin_url VARCHAR(200) DEFAULT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contact_id),
    INDEX idx_contacts_company_id (company_id),
    CONSTRAINT fk_contacts_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


