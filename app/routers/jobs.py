from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel

from app.database import get_db_connection

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobCreate(BaseModel):
    title: str
    company: str
    description: str = ""
    experience_level: str = ""
    skills: str = ""


def normalize_skills(skills_text: str):
    if not skills_text:
        return []
    return [skill.strip().lower() for skill in skills_text.split(",") if skill.strip()]


def calculate_match(resume_skills, job_skills):
    resume_set = {skill.lower().strip() for skill in resume_skills if skill.strip()}
    job_set = {skill.lower().strip() for skill in job_skills if skill.strip()}

    if not job_set:
        return 0, [], []

    matched = sorted(resume_set.intersection(job_set))
    missing = sorted(job_set.difference(resume_set))
    score = round((len(matched) / len(job_set)) * 100)

    return score, matched, missing


def job_to_dict(job):
    return {
        "id": job["id"],
        "job_id": job["id"],
        "title": job["title"],
        "company": job["company"],
        "description": job["description"] or "",
        "experience_level": job["experience_level"] or "",
        "skills": normalize_skills(job["skills"] or ""),
    }


@router.post("/")
def create_job(job: JobCreate):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO jobs (title, company, description, experience_level, skills)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                job.title,
                job.company,
                job.description,
                job.experience_level,
                job.skills,
            ),
        )
        conn.commit()
        return {"message": "Job created successfully", "job_id": cursor.lastrowid}
    finally:
        conn.close()


@router.get("/")
def get_jobs():
    conn = get_db_connection()
    try:
        jobs = conn.execute(
            "SELECT * FROM jobs ORDER BY id DESC"
        ).fetchall()
        return {
            "count": len(jobs),
            "jobs": [job_to_dict(job) for job in jobs],
        }
    finally:
        conn.close()


@router.get("/search")
def search_jobs(
    title: str = "",
    company: str = "",
    experience_level: str = "",
    skill: str = "",
):
    conn = get_db_connection()
    try:
        jobs = conn.execute(
            "SELECT * FROM jobs ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()

    title = title.strip().lower()
    company = company.strip().lower()
    experience_level = experience_level.strip().lower()
    skill = skill.strip().lower()

    filtered_jobs = []
    for job in jobs:
        job_title = (job["title"] or "").lower()
        job_company = (job["company"] or "").lower()
        job_experience = (job["experience_level"] or "").lower()
        job_skills = normalize_skills(job["skills"] or "")

        if title and title not in job_title:
            continue
        if company and company not in job_company:
            continue
        if experience_level and experience_level != job_experience:
            continue
        if skill:
            skill_found = any(
                skill in job_skill or job_skill in skill for job_skill in job_skills
            )
            if not skill_found:
                continue

        filtered_jobs.append(job_to_dict(job))

    return {"count": len(filtered_jobs), "jobs": filtered_jobs}


@router.post("/recommend")
def recommend_jobs(resume_skills: str = Form(...)):
    resume_skills_list = normalize_skills(resume_skills)

    conn = get_db_connection()
    try:
        jobs = conn.execute(
            "SELECT * FROM jobs ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()

    recommendations = []
    for job in jobs:
        job_skills = normalize_skills(job["skills"] or "")
        score, matched, missing = calculate_match(resume_skills_list, job_skills)

        if score == 0:
            continue

        if score >= 80:
            reason = "This job is a strong match for your resume skills."
        elif score >= 50:
            reason = (
                "You have a solid set of required skills, but some gaps remain."
            )
        else:
            reason = (
                "There are a few overlapping skills, but additional development is recommended."
            )

        recommendations.append(
            {
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "description": job["description"] or "",
                "experience_level": job["experience_level"] or "",
                "match_score": score,
                "matched_skills": matched,
                "missing_skills": missing,
                "recommendation_reason": reason,
            }
        )

    recommendations.sort(key=lambda item: item["match_score"], reverse=True)

    return {
        "count": len(recommendations),
        "recommendations": recommendations,
    }


@router.get("/{job_id}")
def get_job(job_id: int):
    conn = get_db_connection()
    try:
        job = conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
    finally:
        conn.close()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job_to_dict(job)


@router.put("/{job_id}")
def update_job(job_id: int, job: JobCreate):
    conn = get_db_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Job not found")

        conn.execute(
            """
            UPDATE jobs
            SET title = ?, company = ?, description = ?, experience_level = ?, skills = ?
            WHERE id = ?
            """,
            (
                job.title,
                job.company,
                job.description,
                job.experience_level,
                job.skills,
                job_id,
            ),
        )
        conn.commit()
        return {"message": "Job updated successfully"}
    finally:
        conn.close()


@router.delete("/{job_id}")
def delete_job(job_id: int):
    conn = get_db_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Job not found")

        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        return {"message": "Job deleted successfully"}
    finally:
        conn.close()