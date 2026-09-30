
import os
import shutil

import docx
import pypdf
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.ai_agents import (
    CareerAdvisorAgent,
    JobMatchingAgent,
    ResumeAnalyzerAgent,
)
from app.auth_dependency import get_current_user
from app.database import get_db_connection, init_db
from app.routers.jobs import router as jobs_router
from app.routers.outh import router as auth_router


app = FastAPI(title="AI Resume Analyzer")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-this-secret-key"),
)

app.include_router(auth_router)
app.include_router(jobs_router)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

templates = Jinja2Templates(directory="app/templates")

init_db()

UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

analyzer_agent = ResumeAnalyzerAgent()
matcher_agent = JobMatchingAgent()
advisor_agent = CareerAdvisorAgent()


def extract_text_from_pdf(file_path: str) -> str:
    text = []

    with open(file_path, "rb") as file:
        reader = pypdf.PdfReader(file)

        for page in reader.pages:
            extracted_text = page.extract_text()

            if extracted_text:
                text.append(extracted_text)

    return "\n".join(text)


def extract_text_from_docx(file_path: str) -> str:
    document = docx.Document(file_path)

    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
    )


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.post("/analyze-resume/")
async def analyze_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    allowed_extensions = {".pdf", ".docx"}
    filename = file.filename or ""
    file_extension = os.path.splitext(filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF or DOCX file.",
        )

    safe_filename = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if file_extension == ".pdf":
        extracted_text = extract_text_from_pdf(file_path)
    else:
        extracted_text = extract_text_from_docx(file_path)

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text was found in the uploaded file.",
        )

    try:
        analysis_result = analyzer_agent.analyze(extracted_text)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while analyzing the resume.",
        ) from exc

    connection = get_db_connection()

    try:
        connection.execute(
            """
            INSERT INTO resumes (
                user_id,
                file_name,
                file_path,
                extracted_text,
                technical_skills,
                soft_skills,
                education,
                experience,
                summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_user["id"],
                safe_filename,
                file_path,
                extracted_text,
                ", ".join(analysis_result["extracted_skills"]),
                ", ".join(analysis_result["soft_skills"]),
                "\n".join(analysis_result["education"]),
                "\n".join(analysis_result["experience"]),
                analysis_result["summary"],
            ),
        )

        connection.commit()
    finally:
        connection.close()

    return {
        "filename": safe_filename,
        "extracted_skills": analysis_result["extracted_skills"],
        "soft_skills": analysis_result["soft_skills"],
        "education": analysis_result["education"],
        "experience": analysis_result["experience"],
        "summary": analysis_result["summary"],
        "extracted_text_preview": extracted_text[:1000],
        "extracted_text": extracted_text,
    }


@app.post("/match-and-advise/")
def match_and_advise(
    resume_skills: str = Form(...),
    job_required_skills: str = Form(...),
):
    skills = [
        skill.strip()
        for skill in resume_skills.split(",")
        if skill.strip()
    ]

    match_result = matcher_agent.match(
        skills,
        job_required_skills,
    )

    advice_result = advisor_agent.recommend(
        match_result["missing_skills"],
    )

    return {
        "match_score": f"{match_result['match_score']}%",
        "matched_skills": match_result["matched_skills"],
        "missing_skills": match_result["missing_skills"],
        "advisor_recommendations": advice_result["recommended_courses"],
    }


@app.post("/improve-resume/")
def improve_resume(
    resume_text: str = Form(...),
    extracted_skills: str = Form(...),
):
    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume text is required.",
        )

    skills = [
        skill.strip()
        for skill in extracted_skills.split(",")
        if skill.strip()
    ]

    return advisor_agent.improve_resume(
        resume_text,
        skills,
    )

