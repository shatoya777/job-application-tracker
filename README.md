# Job Application Tracker

A Flask and MySQL web application for organizing companies, job postings, applications, and professional contacts.

## Features

- Dashboard with counts and an application-status overview.
- Create, view, update, and delete operations for companies, jobs, applications, and contacts.
- Individual detail pages for records.
- MySQL foreign keys and JSON columns for job requirements and interview information.
- Job Match page that ranks active jobs based on the skills entered by the user.
- Parameterized SQL queries, server-side validation, CSRF protection for forms, and transaction commits/rollbacks for database writes.

## Technologies

- Python 3
- Flask
- MySQL 8.0+
- `mysql-connector-python`
- HTML and CSS

## Project Structure

```text
job-application-tracker/
├── app.py
├── database.py
├── matching.py
├── schema.sql
├── migrate_existing.sql
├── sample_data.sql
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── AI_USAGE.md
├── templates/          # List pages, forms, and individual detail pages
├── static/             # Application CSS
└── tests/              # Job Match unit tests
```

## Setup on Windows

### 1. Create the database

Make sure MySQL Server is running. Open MySQL Workbench and connect to your local MySQL instance.

**For a fresh installation:**

1. Open `schema.sql` in MySQL Workbench and execute the entire script. It creates the `job_tracker` database and its four core tables.
2. Optionally execute `sample_data.sql` to add fictional demonstration records. Run the sample-data script only once.

**For an existing database from Assignments 1–7:**

1. Export a backup in MySQL Workbench using **Server → Data Export → Export to Self-Contained File**.
2. Open `migrate_existing.sql` in MySQL Workbench and execute it once.
3. Do not execute the fresh-install `schema.sql` or `sample_data.sql` against the already populated database.

The migration adjusts the existing schema to the final project requirements while retaining the existing application records and assignment-added columns.

### 2. Create and activate a virtual environment

Open a terminal in the project folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the database connection

Copy `.env.example` to a new file named `.env` in the project root. Update `DB_USER` and `DB_PASSWORD` with the account used to connect to MySQL. Keep `DB_NAME=job_tracker` unless using another database name.

Example settings:

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_NAME=job_tracker
SECRET_KEY=use_a_long_random_secret_value
```

### 5. Start the application

```powershell
python app.py
```

Open this address in a browser:

```text
http://127.0.0.1:5000
```

Stop the local server with `Ctrl+C` in the terminal.

## Database Design

The four core tables are `companies`, `jobs`, `applications`, and `contacts`. Their relationships are:

- One company can have many jobs.
- One company can have many contacts.
- One job can have many applications.

The `jobs.requirements` JSON column stores `required_skills`, `preferred_skills`, and other flexible job details. The `applications.interview_data` JSON column stores interview rounds, interviewers, questions, feedback, and next steps.

Some additional columns from the earlier course assignments are retained, including `job_description`, `is_active`, `response_date`, `interview_date`, and timestamps. The Assignment 6 `application_summary` table is not required by the web application and is not created by the fresh-install schema. On the existing course database, the migration leaves it untouched.

The final specification uses integer salary fields. The fresh-install `schema.sql` follows that definition. The existing-database migration retains the earlier Assignment 2 `DECIMAL(10,2)` salary columns to avoid losing stored fractional values. The application can read either numeric type.

## Job Match Calculation

Enter skills separated by commas, semicolons, or new lines. Matching is case-insensitive and uses normalized exact skill names. For each active job:

1. If `required_skills` exists, the score is the number of matched required skills divided by the number of required skills.
2. If no required skills are listed, `preferred_skills` is used as the scoring list.
3. Jobs with neither list are still displayed, but no percentage is shown because there is no skill list to score.

When a job has required skills, matching preferred skills are displayed as supplementary information. The main percentage remains based on required skills.

## Testing

The project includes five automated unit tests for the standalone Job Match calculation. Run them from the project root:

```powershell
python -m unittest discover -s tests -v
```

The application was also run locally against MySQL and manually tested using a functionality checklist. The checks covered the dashboard, the Companies, Jobs, Applications, and Contacts sections, their create/read/update/delete workflows and detail views, and the Job Match feature.


