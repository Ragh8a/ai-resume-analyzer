
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "sqlite.db"


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def get_db_connection():
    return get_db()


def migrate_jobs_table(connection):
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(jobs)").fetchall()
    }

    if "skills" not in columns:
        connection.execute(
            """
            ALTER TABLE jobs
            ADD COLUMN skills TEXT
            """
        )

    if "required_skills" in columns:
        connection.execute(
            """
            UPDATE jobs
            SET skills = required_skills
            WHERE skills IS NULL OR TRIM(skills) = ''
            """
        )

    connection.commit()


def init_db():
    connection = get_db()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT,
            experience_level TEXT,
            required_skills TEXT NOT NULL DEFAULT '',
            skills TEXT
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            content TEXT,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    connection.commit()
    migrate_jobs_table(connection)
    connection.close()

    seed_reference_jobs()


def seed_reference_jobs():
    reference_jobs = [
        {
            "title": "AI Engineer",
            "company": "AI Solutions",
            "description": (
                "Develop AI solutions and implement machine learning "
                "and deep learning models."
            ),
            "experience_level": "Junior",
            "skills": [
                "Python",
                "Machine Learning",
                "Deep Learning",
                "TensorFlow",
                "PyTorch",
                "NLP",
            ],
        },
        {
            "title": "Machine Learning Engineer",
            "company": "Tech Labs",
            "description": (
                "Build, develop, and deploy machine learning models "
                "and analyze data."
            ),
            "experience_level": "Junior",
            "skills": [
                "Python",
                "Machine Learning",
                "Scikit-learn",
                "Pandas",
                "NumPy",
                "SQL",
            ],
        },
        {
            "title": "Arduino Engineer",
            "company": "IoT Systems",
            "description": (
                "Develop embedded and IoT systems using Arduino "
                "and sensors."
            ),
            "experience_level": "Junior",
            "skills": [
                "Arduino",
                "C++",
                "Embedded Systems",
                "IoT",
                "Sensors",
                "Microcontrollers",
            ],
        },
        {
            "title": "Frontend Developer",
            "company": "ITI",
            "description": "Develop modern and responsive web interfaces.",
            "experience_level": "Junior",
            "skills": [
                "HTML",
                "CSS",
                "JavaScript",
                "React",
                "Git",
            ],
        },
        {
            "title": "Frontend Developer",
            "company": "WebCraft",
            "description": (
                "Develop user interfaces using JavaScript and React."
            ),
            "experience_level": "Junior",
            "skills": [
                "HTML",
                "CSS",
                "JavaScript",
                "React",
                "TypeScript",
                "Git",
            ],
        },
        {
            "title": "Backend Developer",
            "company": "Cloud Systems",
            "description": (
                "Develop REST APIs, backend services, and database solutions."
            ),
            "experience_level": "Junior",
            "skills": [
                "Python",
                "FastAPI",
                "REST API",
                "SQL",
                "PostgreSQL",
                "Git",
            ],
        },
        {
            "title": "Full Stack Developer",
            "company": "Digital Factory",
            "description": (
                "Develop full-stack applications using frontend "
                "and backend technologies."
            ),
            "experience_level": "Mid",
            "skills": [
                "HTML",
                "CSS",
                "JavaScript",
                "React",
                "Python",
                "FastAPI",
                "SQL",
            ],
        },
        {
            "title": "Data Scientist",
            "company": "Data Analytics",
            "description": (
                "Analyze data and build statistical and predictive models."
            ),
            "experience_level": "Junior",
            "skills": [
                "Python",
                "Pandas",
                "NumPy",
                "SQL",
                "Machine Learning",
                "Statistics",
            ],
        },
        {
            "title": "DevOps Engineer",
            "company": "CloudTech",
            "description": (
                "Manage infrastructure, automation, and CI/CD processes."
            ),
            "experience_level": "Mid",
            "skills": [
                "Linux",
                "Docker",
                "Kubernetes",
                "Git",
                "CI/CD",
                "AWS",
            ],
        },
        {
            "title": "Computer Vision Engineer",
            "company": "Vision AI",
            "description": (
                "Develop computer vision solutions and process "
                "images and video."
            ),
            "experience_level": "Junior",
            "skills": [
                "Python",
                "OpenCV",
                "Computer Vision",
                "Deep Learning",
                "PyTorch",
                "TensorFlow",
            ],
        },
        {
            "title": "Cybersecurity Engineer",
            "company": "SecureNet",
            "description": (
                "Protect systems and networks and analyze security "
                "vulnerabilities."
            ),
            "experience_level": "Junior",
            "skills": [
                "Cybersecurity",
                "Networking",
                "Linux",
                "Python",
                "Security",
                "OWASP",
            ],
        },
    ]

    connection = get_db()

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(jobs)").fetchall()
    }

    for job in reference_jobs:
        skills_text = ", ".join(job["skills"])

        existing = connection.execute(
            """
            SELECT id
            FROM jobs
            WHERE LOWER(title) = LOWER(?)
              AND LOWER(company) = LOWER(?)
            LIMIT 1
            """,
            (job["title"], job["company"]),
        ).fetchone()

        if existing:
            if "required_skills" in columns:
                connection.execute(
                    """
                    UPDATE jobs
                    SET
                        description = ?,
                        experience_level = ?,
                        required_skills = ?,
                        skills = ?
                    WHERE id = ?
                    """,
                    (
                        job["description"],
                        job["experience_level"],
                        skills_text,
                        skills_text,
                        existing["id"],
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE jobs
                    SET
                        description = ?,
                        experience_level = ?,
                        skills = ?
                    WHERE id = ?
                    """,
                    (
                        job["description"],
                        job["experience_level"],
                        skills_text,
                        existing["id"],
                    ),
                )
            continue

        if "required_skills" in columns:
            connection.execute(
                """
                INSERT INTO jobs (
                    title,
                    company,
                    description,
                    experience_level,
                    required_skills,
                    skills
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job["title"],
                    job["company"],
                    job["description"],
                    job["experience_level"],
                    skills_text,
                    skills_text,
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO jobs (
                    title,
                    company,
                    description,
                    experience_level,
                    skills
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    job["title"],
                    job["company"],
                    job["description"],
                    job["experience_level"],
                    skills_text,
                ),
            )

    connection.commit()
    connection.close()
