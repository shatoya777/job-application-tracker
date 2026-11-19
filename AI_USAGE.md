# AI Usage Documentation

## Tools Used

- **ChatGPT (GPT-6):** Used for project planning, reviewing the project specification and past assignments, drafting portions of the Flask/MySQL implementation, working through the Job Match feature, troubleshooting the interface, and improving the project documentation.

## Key Prompts

1. Review the project specification and Assignments 1–7, identify the required features and deliverables, and help organize the implementation.
2. Compare my existing MySQL table definitions with the final project schema and identify the changes needed while preserving existing records.
3. Help me build a Flask and MySQL application with CRUD operations for companies, jobs, applications, and contacts, using parameterized SQL queries and HTML templates.
4. How to implement a Job Match feature that compares user-entered skills with skills stored in the jobs requirements JSON column and ranks active jobs by match percentage.
5. Review the setup instructions, migration approach, and tests, and help make the project easier to install and run.
6. Explain why the Actions column was misaligned and suggest a CSS refinement that would not change the application's functionality.

## What Worked Well

- ChatGPT generated initial drafts of much of the repetitive application structure, including Flask route logic, reusable database operations, HTML templates, SQL scripts, and the Job Match calculation. This provided a useful starting point for the project.
- It helped identify differences between the original assignment schema and the final project specification, including the contact fields, job URL field, and allowed ENUM values.
- It helped explain database relationships, JSON handling, parameterized queries, and the purpose of the migration script.
- It helped diagnose the Actions-column layout issue and suggest a presentation-only CSS improvement.

## What I Reviewed, Changed, or Verified

- I compared the proposed database changes with the actual table definitions and records in MySQL Workbench before running the migration.
- I used the migration for my existing course database so that the earlier assignment data and useful additional columns were retained.
- I reviewed the Job Match behavior, including how required skills, preferred skills, missing skills, and jobs without skill data are handled.
- I applied the UI refinements while keeping the Flask routes and database operations unchanged.
- I ran the five standalone Job Match unit tests and manually tested the application locally against MySQL using a functionality checklist covering the dashboard, the four CRUD sections, and Job Match.
- I checked the setup and documentation against the project requirements rather than treating generated output as automatically correct.

## Lessons Learned

- I get more useful help when I provide the relevant project requirements, existing code or schema, and the behavior I want.
- AI suggestions are a starting point, not a substitute for understanding my project or checking whether an answer is correct.
- I learned to verify suggested changes against my own files and test them in my environment, especially when they affect existing data.
- Asking follow-up questions and describing what did not work helped me refine suggestions to fit my project.
- AI was most useful for brainstorming, explanations, and getting an initial draft, I still needed to make decisions and take responsibility for the final implementation.
