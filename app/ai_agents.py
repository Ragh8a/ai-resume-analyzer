
import json
import os
import re

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured in .env")

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "qwen-2.5-coder-32b"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_BASE_PATH = os.path.join(
    BASE_DIR,
    "app",
    "knowledge_base",
    "skills_db.json",
)


def load_knowledge_base():
    if os.path.exists(KNOWLEDGE_BASE_PATH):
        try:
            with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass

    return {
        "skills": [
            "Python",
            "FastAPI",
            "SQLite",
            "JavaScript",
            "HTML",
            "CSS",
            "REST API",
            "Frontend",
            "React",
            "Docker",
        ],
        "courses": {
            "Python": "Python for beginners and advanced developers",
            "FastAPI": "FastAPI and REST API development",
            "JavaScript": "Modern JavaScript development",
            "React": "React for frontend development",
            "Docker": "Docker and containerization",
        },
    }


class KnowledgeRetriever:
    def __init__(self):
        self.knowledge_base = load_knowledge_base()

    @staticmethod
    def normalize(text):
        if not text:
            return ""

        text = str(text).lower().strip()
        text = text.replace("-", " ").replace("_", " ")
        return re.sub(r"\s+", " ", text)

    def retrieve(self, query_skills):
        if not query_skills:
            return {}

        skills = self.knowledge_base.get("skills", [])
        courses = self.knowledge_base.get("courses", {})
        certifications = self.knowledge_base.get("certifications", {})
        resources = self.knowledge_base.get("resources", {})

        retrieved = {
            "skills": [],
            "courses": {},
            "certifications": {},
            "resources": {},
        }

        for query_skill in query_skills:
            query_normalized = self.normalize(query_skill)

            if not query_normalized:
                continue

            pattern = rf"\b{re.escape(query_normalized)}\b"

            for skill in skills:
                skill_normalized = self.normalize(skill)

                if re.search(pattern, skill_normalized):
                    if skill not in retrieved["skills"]:
                        retrieved["skills"].append(skill)

            for skill_name, course in courses.items():
                skill_normalized = self.normalize(skill_name)

                if re.search(pattern, skill_normalized):
                    retrieved["courses"][skill_name] = course

            if isinstance(certifications, dict):
                for skill_name, certification in certifications.items():
                    skill_normalized = self.normalize(skill_name)

                    if re.search(pattern, skill_normalized):
                        retrieved["certifications"][skill_name] = certification

            if isinstance(resources, dict):
                for skill_name, resource in resources.items():
                    skill_normalized = self.normalize(skill_name)

                    if re.search(pattern, skill_normalized):
                        retrieved["resources"][skill_name] = resource

        return retrieved


retriever = KnowledgeRetriever()


def safe_json_load(content):
    if not content:
        raise ValueError("Empty AI response")

    cleaned_content = content.strip()
    cleaned_content = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned_content,
        flags=re.IGNORECASE,
    )
    cleaned_content = re.sub(
        r"\s*```$",
        "",
        cleaned_content,
    )

    try:
        return json.loads(cleaned_content)
    except json.JSONDecodeError as exc:
        raise ValueError("AI returned invalid JSON") from exc


def ensure_list(value):
    return value if isinstance(value, list) else []


def ensure_dict(value):
    return value if isinstance(value, dict) else {}


class ResumeAnalyzerAgent:
    def analyze(self, text: str):
        if not text or not text.strip():
            raise ValueError("Resume text is empty")

        prompt = f"""
You are a Resume Analyzer Agent specialized in resume analysis.

Analyze the resume text below and extract only information explicitly
present in the document.

Rules:
- Do not invent or infer information that is not explicitly stated.
- Do not infer companies, job titles, certifications, or skills.
- Return an empty list when information is not available.
- Separate technical skills from soft skills.
- Build the summary only from information found in the resume.
- Return valid JSON only. Do not include any additional text.

Use exactly this structure:
{{
    "technical_skills": [],
    "soft_skills": [],
    "education": [],
    "experience": [],
    "summary": ""
}}

Extraction rules:
1. technical_skills: Mentioned programming languages, tools, technologies,
   frameworks, platforms, and technical skills.
2. soft_skills: Soft skills explicitly mentioned in the resume.
3. education: Degrees, academic programs, universities, and educational
   institutions.
4. experience: Employment, internships, and practical experience, including
   company and duration when available.
5. summary: A concise professional summary based only on the resume data.

Resume:
{text[:10000]}
"""

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            result = safe_json_load(response.choices[0].message.content)

            return {
                "extracted_skills": ensure_list(
                    result.get("technical_skills", [])
                ),
                "soft_skills": ensure_list(
                    result.get("soft_skills", [])
                ),
                "education": ensure_list(
                    result.get("education", [])
                ),
                "experience": ensure_list(
                    result.get("experience", [])
                ),
                "summary": (
                    result.get("summary", "")
                    if isinstance(result.get("summary"), str)
                    else ""
                ),
            }

        except Exception as exc:
            raise RuntimeError("Failed to analyze resume") from exc


class JobMatchingAgent:
    def match(self, resume_skills: list, job_required_skills: str):
        if not job_required_skills.strip():
            return {
                "match_score": 0,
                "matched_skills": [],
                "missing_skills": [],
            }

        prompt = f"""
You are a job matching specialist.

Compare the candidate's resume skills with the required job skills.
Consider common synonyms and abbreviations such as:
AI = Artificial Intelligence
JS = JavaScript

Resume skills:
{resume_skills}

Required skills:
{job_required_skills}

Return valid JSON only:
{{
    "match_score": 100.0,
    "matched_skills": [],
    "missing_skills": []
}}

Rules:
- match_score must be a number between 0 and 100.
- matched_skills must contain skills found in the resume.
- missing_skills must contain required skills not found in the resume.
- Do not add any text outside the JSON response.
"""

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            result = safe_json_load(response.choices[0].message.content)

            match_score = result.get("match_score", 0)

            if not isinstance(match_score, (int, float)):
                match_score = 0

            match_score = max(0.0, min(100.0, float(match_score)))

            return {
                "match_score": round(match_score, 2),
                "matched_skills": ensure_list(
                    result.get("matched_skills", [])
                ),
                "missing_skills": ensure_list(
                    result.get("missing_skills", [])
                ),
            }

        except Exception:
            required_skills = [
                skill.strip().lower()
                for skill in job_required_skills.split(",")
                if skill.strip()
            ]

            resume_skills_lower = [
                str(skill).strip().lower()
                for skill in resume_skills
            ]

            matched_skills = [
                skill
                for skill in required_skills
                if skill in resume_skills_lower
            ]

            missing_skills = [
                skill
                for skill in required_skills
                if skill not in resume_skills_lower
            ]

            match_score = (
                round(
                    (len(matched_skills) / len(required_skills)) * 100,
                    2,
                )
                if required_skills
                else 0
            )

            return {
                "match_score": match_score,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            }


class CareerAdvisorAgent:
    def recommend(self, missing_skills: list):
        if not missing_skills:
            return {
                "recommended_courses": {
                    "Congratulations": "Your skills fully match the job requirements."
                }
            }

        retrieved_context = retriever.retrieve(missing_skills)
        context_data = json.dumps(
            retrieved_context,
            ensure_ascii=False,
            indent=2,
        )

        prompt = f"""
You are a Career Advisor Agent using a retrieval-augmented approach.

Candidate's missing skills:
{json.dumps(missing_skills, ensure_ascii=False)}

Retrieved knowledge base information:
{context_data}

Use only the retrieved information as the basis for your recommendations.

Return valid JSON only:
{{
    "recommendations": {{
        "skill_name": "recommendation"
    }}
}}

Rules:
- Provide a recommendation for each missing skill.
- Use a course from the knowledge base when one is available.
- Do not invent course names or claim that unavailable resources exist.
- If no information is available for a skill, state that the skill is not
  covered by the knowledge base.
- Do not add text outside the JSON response.
"""

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            result = safe_json_load(response.choices[0].message.content)

            return {
                "recommended_courses": ensure_dict(
                    result.get("recommendations", {})
                )
            }

        except Exception:
            fallback = {}
            courses = retrieved_context.get("courses", {})

            for skill in missing_skills:
                normalized_skill = self._normalize(skill)

                for course_skill, course in courses.items():
                    if normalized_skill in self._normalize(course_skill):
                        fallback[skill] = course

            return {"recommended_courses": fallback}

    @staticmethod
    def _normalize(text):
        if not text:
            return ""

        return re.sub(r"\s+", " ", str(text).lower().strip())

    def improve_resume(self, resume_text: str, extracted_skills: list):
        retrieved_context = retriever.retrieve(extracted_skills)
        context_data = json.dumps(
            retrieved_context,
            ensure_ascii=False,
            indent=2,
        )

        prompt = f"""
You are a Career Advisor Agent specialized in resume improvement.

Analyze the resume below and provide a practical improvement report.

Return valid JSON only:
{{
    "weaknesses": [],
    "improvements": [],
    "missing_skills": [],
    "certifications": [],
    "learning_resources": []
}}

Rules:
- Identify weaknesses that are actually supported by the resume.
- Do not invent information about the candidate.
- Provide practical and actionable improvements.
- Use the knowledge base for courses, certifications, and learning resources.
- Do not claim that a resource exists in the knowledge base if it does not.
- General recommendations are allowed when the knowledge base has no relevant
  information, but clearly treat them as general recommendations.
- Return JSON only.

Extracted skills:
{json.dumps(extracted_skills, ensure_ascii=False)}

Retrieved knowledge base information:
{context_data}

Resume:
{resume_text[:5000]}
"""

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            result = safe_json_load(response.choices[0].message.content)

            return {
                "weaknesses": ensure_list(
                    result.get("weaknesses", [])
                ),
                "improvements": ensure_list(
                    result.get("improvements", [])
                ),
                "missing_skills": ensure_list(
                    result.get("missing_skills", [])
                ),
                "certifications": ensure_list(
                    result.get("certifications", [])
                ),
                "learning_resources": ensure_list(
                    result.get("learning_resources", [])
                ),
            }

        except Exception:
            return {
                "weaknesses": [],
                "improvements": [],
                "missing_skills": [],
                "certifications": [],
                "learning_resources": [],
                "error": "Failed to generate the resume improvement report.",
            }

