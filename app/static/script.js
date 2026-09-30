
document.addEventListener("DOMContentLoaded", () => {
    const $ = (id) => document.getElementById(id);

    async function parseResponse(response) {
        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {
            throw new Error(
                data.detail ||
                data.message ||
                "An unexpected server error occurred."
            );
        }

        return data;
    }

    function showMessage(element, message, type = "error") {
        if (!element) return;

        element.textContent = message;
        element.style.display = "block";
        element.style.color = type === "success" ? "#198754" : "#dc3545";
    }

    function clearElement(element) {
        if (element) {
            element.innerHTML = "";
        }
    }

    function renderBadges(container, items = [], className = "skill-badge") {
        if (!container) return;

        clearElement(container);

        if (!Array.isArray(items) || items.length === 0) {
            container.innerHTML =
                '<span class="empty-result">No data available.</span>';
            return;
        }

        items.forEach((item) => {
            const badge = document.createElement("span");
            badge.className = className;
            badge.textContent = String(item);
            container.appendChild(badge);
        });
    }

    function renderList(container, items = []) {
        if (!container) return;

        clearElement(container);

        if (!Array.isArray(items) || items.length === 0) {
            container.innerHTML =
                '<div class="empty-result">No data available.</div>';
            return;
        }

        const ul = document.createElement("ul");

        items.forEach((item) => {
            const li = document.createElement("li");
            li.textContent =
                typeof item === "string" ? item : JSON.stringify(item);

            ul.appendChild(li);
        });

        container.appendChild(ul);
    }

    function renderObject(container, object = {}) {
        if (!container) return;

        clearElement(container);

        if (
            !object ||
            typeof object !== "object" ||
            Object.keys(object).length === 0
        ) {
            container.innerHTML =
                '<div class="empty-result">No recommendations available.</div>';
            return;
        }

        Object.entries(object).forEach(([key, value]) => {
            const item = document.createElement("div");
            item.className = "info-item";

            const title = document.createElement("strong");
            title.textContent = key;

            const content = document.createElement("p");
            content.textContent =
                typeof value === "string"
                    ? value
                    : JSON.stringify(value);

            item.appendChild(title);
            item.appendChild(content);
            container.appendChild(item);
        });
    }

    function renderJobs(container, jobs = []) {
        if (!container) return;

        clearElement(container);

        if (!Array.isArray(jobs) || jobs.length === 0) {
            container.innerHTML =
                '<div class="empty-result">No suitable jobs were found.</div>';
            return;
        }

        jobs.forEach((job) => {
            const card = document.createElement("div");
            card.className = "job-card";

            const title = document.createElement("h3");
            title.textContent = job.title || "Untitled Position";

            const company = document.createElement("p");
            company.textContent =
                `Company: ${job.company || "Not specified"}`;

            const experience = document.createElement("p");
            experience.textContent =
                `Experience Level: ${job.experience_level || "Not specified"}`;

            const description = document.createElement("p");
            description.textContent =
                job.description || "No description available.";

            card.appendChild(title);
            card.appendChild(company);
            card.appendChild(experience);
            card.appendChild(description);

            if (job.match_score !== undefined) {
                const score = document.createElement("p");
                score.className = "job-score";
                score.textContent =
                    `Match Score: ${job.match_score}%`;

                card.appendChild(score);
            }

            if (
                Array.isArray(job.matched_skills) &&
                job.matched_skills.length
            ) {
                const matchedTitle = document.createElement("strong");
                matchedTitle.textContent = "Matched Skills:";
                card.appendChild(matchedTitle);

                const matched = document.createElement("div");
                matched.className = "skills-container";

                job.matched_skills.forEach((skill) => {
                    const badge = document.createElement("span");
                    badge.className = "matched-skill";
                    badge.textContent = skill;
                    matched.appendChild(badge);
                });

                card.appendChild(matched);
            }

            if (
                Array.isArray(job.missing_skills) &&
                job.missing_skills.length
            ) {
                const missingTitle = document.createElement("strong");
                missingTitle.textContent = "Missing Skills:";
                card.appendChild(missingTitle);

                const missing = document.createElement("div");
                missing.className = "skills-container";

                job.missing_skills.forEach((skill) => {
                    const badge = document.createElement("span");
                    badge.className = "missing-skill";
                    badge.textContent = skill;
                    missing.appendChild(badge);
                });

                card.appendChild(missing);
            }

            if (job.recommendation_reason) {
                const reason = document.createElement("p");
                reason.textContent =
                    `Recommendation: ${job.recommendation_reason}`;

                card.appendChild(reason);
            }

            container.appendChild(card);
        });
    }

    const loginForm = $("login-form");
    const registerForm = $("register-form");
    const logoutBtn = $("logout-btn");

    if (loginForm) {
        loginForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const email = $("login-email")?.value.trim();
            const password = $("login-password")?.value;
            const message = $("login-message");

            if (!email || !password) {
                showMessage(
                    message,
                    "Please enter your email and password."
                );
                return;
            }

            try {
                const response = await fetch("/auth/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    credentials: "include",
                    body: JSON.stringify({
                        email,
                        password
                    })
                });

                await parseResponse(response);

                showMessage(
                    message,
                    "Login successful.",
                    "success"
                );

                setTimeout(() => {
                    window.location.href = "/";
                }, 500);
            } catch (error) {
                showMessage(message, error.message);
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const name = $("register-name")?.value.trim();
            const email = $("register-email")?.value.trim();
            const password = $("register-password")?.value;
            const message = $("register-message");

            if (!name || !email || !password) {
                showMessage(
                    message,
                    "Please fill in all fields."
                );
                return;
            }

            if (password.length < 8) {
                showMessage(
                    message,
                    "Password must be at least 8 characters long."
                );
                return;
            }

            try {
                const response = await fetch("/auth/register", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        name,
                        email,
                        password
                    })
                });

                await parseResponse(response);

                showMessage(
                    message,
                    "Account created successfully. Redirecting to login.",
                    "success"
                );

                setTimeout(() => {
                    window.location.href = "/login";
                }, 800);
            } catch (error) {
                showMessage(message, error.message);
            }
        });
    }

    const showRegister = $("show-register");

    if (showRegister) {
        showRegister.addEventListener("click", () => {
            window.location.href = "/register";
        });
    }

    const showLogin = $("show-login");

    if (showLogin) {
        showLogin.addEventListener("click", () => {
            window.location.href = "/login";
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            try {
                const response = await fetch("/auth/logout", {
                    method: "POST",
                    credentials: "include"
                });

                await parseResponse(response);
                window.location.href = "/login";
            } catch (error) {
                alert(error.message);
            }
        });
    }

    const uploadForm = $("upload-form");

    if (uploadForm) {
        uploadForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const fileInput = $("resume-file");
            const file = fileInput?.files?.[0];

            if (!file) {
                alert("Please select a resume file.");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);

            try {
                const response = await fetch("/analyze-resume/", {
                    method: "POST",
                    credentials: "include",
                    body: formData
                });

                const data = await parseResponse(response);
                const result = $("analysis-result");

                if (result) {
                    result.style.display = "block";
                }

                if ($("result-filename")) {
                    $("result-filename").textContent =
                        data.filename || file.name;
                }

                if ($("summary")) {
                    $("summary").textContent =
                        data.summary || "No summary available.";
                }

                renderBadges(
                    $("technical-skills"),
                    data.extracted_skills || [],
                    "skill-badge"
                );

                renderBadges(
                    $("soft-skills"),
                    data.soft_skills || [],
                    "skill-badge"
                );

                renderList($("education"), data.education || []);
                renderList($("experience"), data.experience || []);

                if ($("extracted-skills-input")) {
                    $("extracted-skills-input").value =
                        (data.extracted_skills || []).join(", ");
                }

                if ($("resume-text-input")) {
                    $("resume-text-input").value =
                        data.extracted_text || "";
                }

                if ($("improve-skills-input")) {
                    $("improve-skills-input").value =
                        (data.extracted_skills || []).join(", ");
                }
            } catch (error) {
                alert(error.message);
            }
        });
    }

    const matchForm = $("match-form");

    if (matchForm) {
        matchForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const resumeSkills =
                $("extracted-skills-input")?.value.trim();

            const jobSkills =
                $("job-skills-input")?.value.trim();

            if (!resumeSkills || !jobSkills) {
                alert(
                    "Please enter the resume skills and required job skills."
                );
                return;
            }

            const formData = new FormData();
            formData.append("resume_skills", resumeSkills);
            formData.append("job_required_skills", jobSkills);

            try {
                const response = await fetch("/match-and-advise/", {
                    method: "POST",
                    credentials: "include",
                    body: formData
                });

                const data = await parseResponse(response);
                const result = $("match-result");

                if (result) {
                    result.style.display = "block";
                }

                if ($("match-score")) {
                    $("match-score").textContent =
                        data.match_score || "0%";
                }

                renderBadges(
                    $("matched-skills"),
                    data.matched_skills || [],
                    "matched-skill"
                );

                renderBadges(
                    $("missing-skills"),
                    data.missing_skills || [],
                    "missing-skill"
                );

                renderObject(
                    $("advisor-recommendations"),
                    data.advisor_recommendations || {}
                );
            } catch (error) {
                alert(error.message);
            }
        });
    }

    const improveButton = $("improve-resume-btn");

    if (improveButton) {
        improveButton.addEventListener("click", async () => {
            const resumeText =
                $("resume-text-input")?.value.trim();

            const skills =
                $("improve-skills-input")?.value.trim();

            if (!resumeText) {
                alert("Please enter the resume text.");
                return;
            }

            if (!skills) {
                alert("Please enter your current skills.");
                return;
            }

            const formData = new FormData();
            formData.append("resume_text", resumeText);
            formData.append("extracted_skills", skills);

            try {
                const response = await fetch("/improve-resume/", {
                    method: "POST",
                    credentials: "include",
                    body: formData
                });

                const data = await parseResponse(response);
                const result = $("improve-result");

                if (result) {
                    result.style.display = "block";
                }

                renderList(
                    $("weaknesses"),
                    data.weaknesses || []
                );

                renderList(
                    $("improvements"),
                    data.improvements || []
                );

                renderBadges(
                    $("improvement-missing-skills"),
                    data.missing_skills || [],
                    "missing-skill"
                );

                renderList(
                    $("certifications"),
                    data.certifications || []
                );

                renderList(
                    $("learning-resources"),
                    data.learning_resources || []
                );
            } catch (error) {
                alert(error.message);
            }
        });
    }

    const recommendJobsButton = $("recommend-jobs-btn");

    if (recommendJobsButton) {
        recommendJobsButton.addEventListener("click", async () => {
            const skills =
                $("extracted-skills-input")?.value.trim();

            if (!skills) {
                alert(
                    "Please analyze your resume first or enter your skills."
                );
                return;
            }

            try {
                const response = await fetch("/jobs/recommend", {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/x-www-form-urlencoded"
                    },
                    credentials: "include",
                    body: `resume_skills=${encodeURIComponent(skills)}`
                });

                const data = await parseResponse(response);
                const result = $("jobs-result");

                if (result) {
                    result.style.display = "block";
                }

                renderJobs(
                    $("jobs-list"),
                    data.recommendations || []
                );
            } catch (error) {
                alert(error.message);
            }
        });
    }

    const searchJobsButton = $("search-jobs-btn");

    if (searchJobsButton) {
        searchJobsButton.addEventListener("click", async () => {
            const title = $("search-title")?.value.trim() || "";
            const company = $("search-company")?.value.trim() || "";
            const skill = $("search-skill")?.value.trim() || "";
            const experience = $("search-experience")?.value || "";

            const params = new URLSearchParams();

            if (title) {
                params.append("title", title);
            }

            if (company) {
                params.append("company", company);
            }

            if (skill) {
                params.append("skill", skill);
            }

            if (experience) {
                params.append("experience_level", experience);
            }

            try {
                const response = await fetch(
                    `/jobs/search?${params.toString()}`,
                    {
                        method: "GET",
                        cre

