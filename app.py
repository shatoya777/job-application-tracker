"""Flask application for the Job Application Tracker project."""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlsplit

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

import database
from matching import calculate_job_matches

load_dotenv()

JOB_TYPES = ("Full-time", "Part-time", "Contract", "Internship")
APPLICATION_STATUSES = (
    "Applied",
    "Screening",
    "Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
)

"""Validate and normalize form input values for database operations."""
def _optional_text(value: str | None, label: str = "Field", max_length: int | None = None) -> str | None:
    value = (value or "").strip()
    if value and max_length and len(value) > max_length:
        raise ValueError(f"{label} must be {max_length} characters or fewer.")
    return value or None

def _optional_url(value: str | None, label: str, max_length: int, allow_missing_scheme: bool = False) -> str | None:
    value = _optional_text(value, label, max_length)
    if not value:
        return None
    candidate = value if "://" in value else (f"https://{value}" if allow_missing_scheme else value)
    parsed = urlsplit(candidate)
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label} must be a valid http or https URL.")
    return value

"""Convert a value to a dictionary if possible."""
def _required_text(value: str | None, label: str, max_length: int | None = None) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{label} is required.")
    if max_length and len(value) > max_length:
        raise ValueError(f"{label} must be {max_length} characters or fewer.")
    return value

def _optional_int(value: str | None, label: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        decimal_number = Decimal(value)
        if not decimal_number.is_finite() or decimal_number != decimal_number.to_integral_value():
            raise ValueError
        number = int(decimal_number)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be a whole number.") from exc
    if number < 0:
        raise ValueError(f"{label} cannot be negative.")
    return number

def _required_int(value: str | None, label: str) -> int:
    number = _optional_int(value, label)
    if number is None:
        raise ValueError(f"{label} is required.")
    return number

def _optional_date(value: str | None, label: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid date.") from exc

def _optional_datetime(value: str | None, label: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid date and time.") from exc

def _json_object(value: str | None, label: str) -> str | None:
    """Validate a JSON object and return a JSON string suitable for MySQL."""
    value = (value or "").strip()
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must contain valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object (start with {{ and end with }}).")
    return json.dumps(parsed, ensure_ascii=False)



def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "local-development-key-change-this")
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    CSRFProtect(app)

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    @app.template_filter("date_input")
    def date_input(value: Any) -> str:
        if not value:
            return ""
        return value[:10] if isinstance(value, str) else value.isoformat()

    @app.template_filter("datetime_input")
    def datetime_input(value: Any) -> str:
        if not value:
            return ""
        if isinstance(value, str):
            return value[:16]
        return value.strftime("%Y-%m-%dT%H:%M")

    @app.template_filter("json_pretty")
    def json_pretty(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return value
        return json.dumps(value, indent=2, ensure_ascii=False)

    @app.template_filter("money")
    def money(value: Any) -> str:
        if value is None or value == "":
            return "Not provided"
        try:
            amount = Decimal(str(value))
            return f"${amount:,.0f}"
        except (InvalidOperation, ValueError):
            return str(value)

    @app.context_processor
    def inject_choices():
        return {"job_types": JOB_TYPES, "application_statuses": APPLICATION_STATUSES}

    @app.errorhandler(mysql.connector.Error)
    def handle_database_error(error):
        app.logger.exception("Database operation failed: %s", error)
        flash("A database operation could not be completed. Check the database connection and try again.", "error")
        return render_template("error.html", message="The database could not complete that request."), 500

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", message="The page or record you requested was not found."), 404

    @app.get("/")
    def dashboard():
        stats = database.fetch_one(
            """
            SELECT
                (SELECT COUNT(*) FROM companies) AS company_count,
                (SELECT COUNT(*) FROM jobs) AS job_count,
                (SELECT COUNT(*) FROM jobs WHERE is_active = 1) AS active_job_count,
                (SELECT COUNT(*) FROM applications) AS application_count,
                (SELECT COUNT(*) FROM contacts) AS contact_count,
                (SELECT COUNT(*) FROM applications WHERE status = 'Offer') AS offer_count
            """
        ) or {}
        status_counts = database.fetch_all(
            "SELECT status, COUNT(*) AS total FROM applications GROUP BY status ORDER BY total DESC, status"
        )
        recent_applications = database.fetch_all(
            """
            SELECT a.application_id, a.application_date, a.status,
                   j.job_title, c.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY a.application_date DESC, a.application_id DESC
            LIMIT 6
            """
        )
        return render_template(
            "dashboard.html",
            stats=stats,
            status_counts=status_counts,
            recent_applications=recent_applications,
        )

    # ------------------------------ Companies ------------------------------
    @app.get("/companies")
    def companies():
        records = database.fetch_all(
            """
            SELECT c.*, COUNT(DISTINCT j.job_id) AS job_count,
                   COUNT(DISTINCT a.application_id) AS application_count
            FROM companies c
            LEFT JOIN jobs j ON c.company_id = j.company_id
            LEFT JOIN applications a ON j.job_id = a.job_id
            GROUP BY c.company_id
            ORDER BY c.company_name
            """
        )
        return render_template("companies.html", companies=records)

    @app.get("/companies/<int:company_id>")
    def company_detail(company_id: int):
        company = database.fetch_one("SELECT * FROM companies WHERE company_id = %s", (company_id,))
        if not company:
            abort(404)
        related_jobs = database.fetch_all(
            "SELECT job_id, job_title, job_type, is_active, date_posted FROM jobs WHERE company_id = %s ORDER BY date_posted DESC, job_title",
            (company_id,),
        )
        related_contacts = database.fetch_all(
            "SELECT contact_id, contact_name, title, email FROM contacts WHERE company_id = %s ORDER BY contact_name",
            (company_id,),
        )
        return render_template("company_detail.html", company=company, jobs=related_jobs, contacts=related_contacts)

    @app.route("/companies/new", methods=["GET", "POST"])
    def company_new():
        if request.method == "POST":
            form = request.form
            try:
                values = (
                    _required_text(form.get("company_name"), "Company name", 100),
                    _optional_text(form.get("industry"), "Industry", 50),
                    _optional_url(form.get("website"), "Website", 200, allow_missing_scheme=True),
                    _optional_text(form.get("city"), "City", 50),
                    _optional_text(form.get("state"), "State", 50),
                    _optional_text(form.get("notes")),
                )
                database.execute_write(
                    "INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES (%s, %s, %s, %s, %s, %s)",
                    values,
                )
                flash("Company added successfully.", "success")
                return redirect(url_for("companies"))
            except ValueError as error:
                flash(str(error), "error")
                return render_template("company_form.html", company=form, page_title="Add company")
        return render_template("company_form.html", company={}, page_title="Add company")

    @app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
    def company_edit(company_id: int):
        company = database.fetch_one("SELECT * FROM companies WHERE company_id = %s", (company_id,))
        if not company:
            abort(404)
        if request.method == "POST":
            form = request.form
            try:
                values = (
                    _required_text(form.get("company_name"), "Company name", 100),
                    _optional_text(form.get("industry"), "Industry", 50),
                    _optional_url(form.get("website"), "Website", 200, allow_missing_scheme=True),
                    _optional_text(form.get("city"), "City", 50),
                    _optional_text(form.get("state"), "State", 50),
                    _optional_text(form.get("notes")),
                    company_id,
                )
                database.execute_write(
                    "UPDATE companies SET company_name=%s, industry=%s, website=%s, city=%s, state=%s, notes=%s WHERE company_id=%s",
                    values,
                )
                flash("Company updated successfully.", "success")
                return redirect(url_for("companies"))
            except ValueError as error:
                flash(str(error), "error")
                return render_template("company_form.html", company=form, page_title="Edit company")
        return render_template("company_form.html", company=company, page_title="Edit company")

    @app.post("/companies/<int:company_id>/delete")
    def company_delete(company_id: int):
        try:
            _, affected = database.execute_write("DELETE FROM companies WHERE company_id = %s", (company_id,))
            flash("Company deleted." if affected else "Company was not found.", "success" if affected else "warning")
        except mysql.connector.IntegrityError:
            flash("This company still has jobs or contacts. Delete or reassign those records first.", "error")
        return redirect(url_for("companies"))

    # -------------------------------- Jobs ----------------------------------
    @app.get("/jobs")
    def jobs():
        records = database.fetch_all(
            """
            SELECT j.*, c.company_name,
                   (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.job_id) AS application_count
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY j.is_active DESC, j.date_posted DESC, j.job_title
            """
        )
        return render_template("jobs.html", jobs=records)

    @app.get("/jobs/<int:job_id>")
    def job_detail(job_id: int):
        job = database.fetch_one(
            "SELECT j.*, c.company_name FROM jobs j JOIN companies c ON j.company_id = c.company_id WHERE j.job_id = %s",
            (job_id,),
        )
        if not job:
            abort(404)
        related_applications = database.fetch_all(
            "SELECT application_id, application_date, status FROM applications WHERE job_id = %s ORDER BY application_date DESC",
            (job_id,),
        )
        return render_template("job_detail.html", job=job, applications=related_applications)

    def save_job(form, job_id: int | None = None):
        company_id = _required_int(form.get("company_id"), "Company")
        job_title = _required_text(form.get("job_title"), "Job title", 100)
        job_type = _optional_text(form.get("job_type"))
        if job_type and job_type not in JOB_TYPES:
            raise ValueError("Select a valid job type.")
        salary_min = _optional_int(form.get("salary_min"), "Minimum salary")
        salary_max = _optional_int(form.get("salary_max"), "Maximum salary")
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise ValueError("Minimum salary cannot be greater than maximum salary.")
        date_posted = _optional_date(form.get("date_posted"), "Date posted")
        job_url = _optional_url(form.get("job_url"), "Job URL", 300)
        requirements = _json_object(form.get("requirements"), "Requirements")
        job_description = _optional_text(form.get("job_description"))
        is_active = 1 if form.get("is_active") == "on" else 0

        values = (
            company_id, job_title, job_description, salary_min, salary_max,
            job_type, job_url, date_posted, is_active, requirements,
        )
        if job_id is None:
            database.execute_write(
                """INSERT INTO jobs
                   (company_id, job_title, job_description, salary_min, salary_max,
                    job_type, job_url, date_posted, is_active, requirements)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                values,
            )
        else:
            database.execute_write(
                """UPDATE jobs SET company_id=%s, job_title=%s, job_description=%s,
                   salary_min=%s, salary_max=%s, job_type=%s, job_url=%s,
                   date_posted=%s, is_active=%s, requirements=%s
                   WHERE job_id=%s""",
                values + (job_id,),
            )

    @app.route("/jobs/new", methods=["GET", "POST"])
    def job_new():
        companies_list = database.fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name")
        if request.method == "POST":
            try:
                save_job(request.form)
                flash("Job added successfully.", "success")
                return redirect(url_for("jobs"))
            except ValueError as error:
                flash(str(error), "error")
                return render_template("job_form.html", job=request.form, companies=companies_list, page_title="Add job")
        return render_template("job_form.html", job={"is_active": 1}, companies=companies_list, page_title="Add job")

    @app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
    def job_edit(job_id: int):
        job = database.fetch_one("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
        if not job:
            abort(404)
        companies_list = database.fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name")
        if request.method == "POST":
            try:
                save_job(request.form, job_id)
                flash("Job updated successfully.", "success")
                return redirect(url_for("jobs"))
            except ValueError as error:
                flash(str(error), "error")
                return render_template("job_form.html", job=request.form, companies=companies_list, page_title="Edit job")
        return render_template("job_form.html", job=job, companies=companies_list, page_title="Edit job")

    @app.post("/jobs/<int:job_id>/delete")
    def job_delete(job_id: int):
        try:
            _, affected = database.execute_write("DELETE FROM jobs WHERE job_id = %s", (job_id,))
            flash("Job deleted." if affected else "Job was not found.", "success" if affected else "warning")
        except mysql.connector.IntegrityError:
            flash("This job has applications. Delete or reassign its applications before deleting the job.", "error")
        return redirect(url_for("jobs"))

    # ----------------------------- Applications ----------------------------
    @app.get("/applications")
    def applications():
        records = database.fetch_all(
            """
            SELECT a.*, j.job_title, c.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY a.application_date DESC, a.application_id DESC
            """
        )
        return render_template("applications.html", applications=records)

    @app.get("/applications/<int:application_id>")
    def application_detail(application_id: int):
        application = database.fetch_one(
            """SELECT a.*, j.job_title, j.job_id, c.company_name, c.company_id
               FROM applications a
               JOIN jobs j ON a.job_id = j.job_id
               JOIN companies c ON j.company_id = c.company_id
               WHERE a.application_id = %s""",
            (application_id,),
        )
        if not application:
            abort(404)
        return render_template("application_detail.html", application=application)

    def save_application(form, application_id: int | None = None):
        job_id = _required_int(form.get("job_id"), "Job")
        application_date = _optional_date(form.get("application_date"), "Application date")
        if application_date is None:
            raise ValueError("Application date is required.")
        status = _required_text(form.get("status"), "Status")
        if status not in APPLICATION_STATUSES:
            raise ValueError("Select a valid application status.")
        resume_version = _optional_text(form.get("resume_version"), "Resume version", 50)
        cover_letter_sent = 1 if form.get("cover_letter_sent") == "on" else 0
        response_date = _optional_date(form.get("response_date"), "Response date")
        interview_date = _optional_datetime(form.get("interview_date"), "Interview date")
        notes = _optional_text(form.get("notes"))
        interview_data = _json_object(form.get("interview_data"), "Interview data")
        values = (
            job_id, application_date, status, resume_version, cover_letter_sent,
            response_date, interview_date, notes, interview_data,
        )
        if application_id is None:
            database.execute_write(
                """INSERT INTO applications
                   (job_id, application_date, status, resume_version, cover_letter_sent,
                    response_date, interview_date, notes, interview_data)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                values,
            )
        else:
            database.execute_write(
                """UPDATE applications SET job_id=%s, application_date=%s, status=%s,
                   resume_version=%s, cover_letter_sent=%s, response_date=%s,
                   interview_date=%s, notes=%s, interview_data=%s
                   WHERE application_id=%s""",
                values + (application_id,),
            )

    @app.route("/applications/new", methods=["GET", "POST"])
    def application_new():
        jobs_list = database.fetch_all(
            "SELECT j.job_id, j.job_title, c.company_name FROM jobs j JOIN companies c ON j.company_id=c.company_id ORDER BY c.company_name, j.job_title"
        )
        if request.method == "POST":
            try:
                save_application(request.form)
                flash("Application added successfully.", "success")
                return redirect(url_for("applications"))
            except ValueError as error:
                flash(str(error), "error")
                return render_template("application_form.html", application=request.form, jobs=jobs_list, page_title="Add application")
        return render_template(
            "application_form.html",
            application={"application_date": date.today().isoformat(), "status": "Applied"},
            jobs=jobs_list,
            page_title="Add application",
        )

    @app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
    def application_edit(application_id: int):
        application = database.fetch_one("SELECT * FROM applications WHERE application_id = %s", (application_id,))
        if not application:
            abort(404)
        jobs_list = database.fetch_all(
            "SELECT j.job_id, j.job_title, c.company_name FROM jobs j JOIN companies c ON j.company_id=c.company_id ORDER BY c.company_name, j.job_title"
        )
        if request.method == "POST":
            try:
                save_application(request.form, application_id)
                flash("Application updated successfully.", "success")
                return redirect(url_for("applications"))
            except ValueError as error:
                flash(str(error), "error")
                return render_template("application_form.html", application=request.form, jobs=jobs_list, page_title="Edit application")
        return render_template("application_form.html", application=application, jobs=jobs_list, page_title="Edit application")

    @app.post("/applications/<int:application_id>/delete")
    def application_delete(application_id: int):
        _, affected = database.execute_write("DELETE FROM applications WHERE application_id = %s", (application_id,))
        flash("Application deleted." if affected else "Application was not found.", "success" if affected else "warning")
        return redirect(url_for("applications"))

    # -------------------------------- Contacts ------------------------------
    @app.get("/contacts")
    def contacts():
        records = database.fetch_all(
            """
            SELECT ct.*, c.company_name
            FROM contacts ct
            JOIN companies c ON ct.company_id = c.company_id
            ORDER BY c.company_name, ct.contact_name
            """
        )
        return render_template("contacts.html", contacts=records)

    @app.get("/contacts/<int:contact_id>")
    def contact_detail(contact_id: int):
        contact = database.fetch_one(
            "SELECT ct.*, c.company_name FROM contacts ct JOIN companies c ON ct.company_id = c.company_id WHERE ct.contact_id = %s",
            (contact_id,),
        )
        if not contact:
            abort(404)
        return render_template("contact_detail.html", contact=contact)

    def save_contact(form, contact_id: int | None = None):
        company_id = _required_int(form.get("company_id"), "Company")
        contact_name = _required_text(form.get("contact_name"), "Contact name", 100)
        title = _optional_text(form.get("title"), "Title", 100)
        email = _optional_text(form.get("email"), "Email", 100)
        if email and ("@" not in email or email.startswith("@") or email.endswith("@") or any(ch.isspace() for ch in email)):
            raise ValueError("Enter a valid email address.")
        phone = _optional_text(form.get("phone"), "Phone", 20)
        linkedin_url = _optional_url(form.get("linkedin_url"), "LinkedIn URL", 200, allow_missing_scheme=True)
        notes = _optional_text(form.get("notes"))
        values = (company_id, contact_name, title, email, phone, linkedin_url, notes)
        if contact_id is None:
            database.execute_write(
                """INSERT INTO contacts
                   (company_id, contact_name, title, email, phone, linkedin_url, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                values,
            )
        else:
            database.execute_write(
                """UPDATE contacts SET company_id=%s, contact_name=%s, title=%s,
                   email=%s, phone=%s, linkedin_url=%s, notes=%s WHERE contact_id=%s""",
                values + (contact_id,),
            )

    @app.route("/contacts/new", methods=["GET", "POST"])
    def contact_new():
        companies_list = database.fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name")
        if request.method == "POST":
            try:
                save_contact(request.form)
                flash("Contact added successfully.", "success")
                return redirect(url_for("contacts"))
            except ValueError as error:
                flash(str(error), "error")
                return render_template("contact_form.html", contact=request.form, companies=companies_list, page_title="Add contact")
        return render_template("contact_form.html", contact={}, companies=companies_list, page_title="Add contact")

    @app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
    def contact_edit(contact_id: int):
        contact = database.fetch_one("SELECT * FROM contacts WHERE contact_id = %s", (contact_id,))
        if not contact:
            abort(404)
        companies_list = database.fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name")
        if request.method == "POST":
            try:
                save_contact(request.form, contact_id)
                flash("Contact updated successfully.", "success")
                return redirect(url_for("contacts"))
            except ValueError as error:
                flash(str(error), "error")
                return render_template("contact_form.html", contact=request.form, companies=companies_list, page_title="Edit contact")
        return render_template("contact_form.html", contact=contact, companies=companies_list, page_title="Edit contact")

    @app.post("/contacts/<int:contact_id>/delete")
    def contact_delete(contact_id: int):
        _, affected = database.execute_write("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))
        flash("Contact deleted." if affected else "Contact was not found.", "success" if affected else "warning")
        return redirect(url_for("contacts"))

    # -------------------------------- Job Match -----------------------------
    @app.route("/job-match", methods=["GET", "POST"])
    def job_match():
        skills_text = ""
        matches: list[dict[str, Any]] = []
        searched = False
        if request.method == "POST":
            searched = True
            skills_text = request.form.get("skills", "").strip()
            skills = [item.strip() for item in skills_text.replace("\n", ",").replace(";", ",").split(",") if item.strip()]
            if not skills:
                flash("Enter at least one skill to calculate job matches.", "error")
            else:
                active_jobs = database.fetch_all(
                    """
                    SELECT j.job_id, j.job_title, j.job_type, j.salary_min, j.salary_max,
                           j.job_url, j.requirements, c.company_name, c.city, c.state
                    FROM jobs j
                    JOIN companies c ON j.company_id = c.company_id
                    WHERE j.is_active = 1
                    """
                )
                matches = calculate_job_matches(active_jobs, skills)
        return render_template("job_match.html", skills_text=skills_text, matches=matches, searched=searched)

    return app


app = create_app()

if __name__ == "__main__":
    # Debug mode is intentionally disabled by default. Enable only for local development.
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "0") == "1")
