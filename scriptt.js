const scoreForms = document.querySelectorAll("[data-score-form]");
const apiBaseUrl = window.location.port === "5000" ? "" : "http://127.0.0.1:5000";
const themeButtons = document.querySelectorAll("[data-theme-toggle]");
const authForms = document.querySelectorAll("[data-auth-form]");
const logoutButtons = document.querySelectorAll("[data-logout]");

function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("yuktiTheme", theme);

    themeButtons.forEach((button) => {
        button.textContent = theme === "dark" ? "Day" : "Night";
    });
}

applyTheme(localStorage.getItem("yuktiTheme") || "light");

themeButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const currentTheme = document.documentElement.dataset.theme || "light";
        applyTheme(currentTheme === "dark" ? "light" : "dark");
    });
});

function setText(selector, value) {
    document.querySelectorAll(selector).forEach((element) => {
        element.textContent = value;
    });
}

function setMessage(message, type = "info") {
    document.querySelectorAll("[data-result-message]").forEach((element) => {
        element.textContent = message;
        element.className = `result-message ${type}`;
    });
}

function renderAnalysis(analysis) {
    const chart = document.querySelector("[data-analysis-chart]");
    const summary = document.querySelector("[data-analysis-summary]");

    if (!chart || !summary) {
        return;
    }

    if (!analysis || !analysis.breakdown) {
        chart.innerHTML = "";
        summary.textContent = "Upload a resume to see how the score was built.";
        return;
    }

    const bars = analysis.breakdown.map((item) => {
        const percentage = Math.max(0, Math.min(100, Math.round((item.value / item.max) * 100)));
        return `
            <div class="analysis-bar">
                <div class="analysis-bar-header">
                    <span>${item.label}</span>
                    <strong>${item.value}/${item.max}</strong>
                </div>
                <div class="analysis-track">
                    <div class="analysis-fill" style="width: ${percentage}%"></div>
                </div>
                <p>${item.detail}</p>
            </div>
        `;
    }).join("");

    chart.innerHTML = bars;
    summary.textContent = analysis.summary || "Resume factors are shown above.";
}

function incrementProcessedCount() {
    document.querySelectorAll("[data-resumes-processed]").forEach((element) => {
        const currentValue = Number.parseInt(element.textContent, 10) || 0;
        element.textContent = currentValue + 1;
    });
}

function setAuthMessage(message, type = "info") {
    document.querySelectorAll("[data-auth-message]").forEach((element) => {
        element.textContent = message;
        element.className = `result-message ${type}`;
    });
}

function setAuthUi(username) {
    const signedIn = Boolean(username);

    document.querySelectorAll("[data-auth-user]").forEach((element) => {
        element.textContent = signedIn ? `Signed in as ${username}` : "Not signed in";
    });

    document.querySelectorAll("[data-login-link], [data-signup-link]").forEach((element) => {
        element.hidden = signedIn;
    });

    logoutButtons.forEach((button) => {
        button.hidden = !signedIn;
    });
}

async function loadAuthStatus() {
    try {
        const response = await fetch(`${apiBaseUrl}/auth/status`, {
            credentials: "include",
        });
        const data = await response.json();

        if (data.authenticated) {
            localStorage.setItem("yuktiUser", data.username);
            setAuthUi(data.username);
            return;
        }
    } catch (error) {
        // Live Server can still use localStorage for display if Flask is not reachable.
    }

    setAuthUi(localStorage.getItem("yuktiUser"));
}

loadAuthStatus();

authForms.forEach((form) => {
    const mode = form.dataset.authForm;
    const button = form.querySelector("button");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(form);
        const username = formData.get("username").trim();
        const password = formData.get("password");

        button.disabled = true;
        button.textContent = mode === "signup" ? "Creating..." : "Logging in...";
        setAuthMessage("Please wait...", "info");

        try {
            const response = await fetch(`${apiBaseUrl}/auth/${mode}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
                body: JSON.stringify({ username, password }),
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Authentication failed.");
            }

            localStorage.setItem("yuktiUser", data.username);
            setAuthMessage(data.message, "success");
            window.location.href = "dashboard.html";
        } catch (error) {
            const message = error instanceof TypeError
                ? "Python backend is not running. Start it with: python web_app.py"
                : error.message;

            setAuthMessage(message, "error");
        } finally {
            button.disabled = false;
            button.textContent = mode === "signup" ? "Create Account" : "Login";
        }
    });
});

logoutButtons.forEach((button) => {
    button.addEventListener("click", async () => {
        try {
            await fetch(`${apiBaseUrl}/logout`, {
                method: "POST",
                credentials: "include",
            });
        } catch (error) {
            // Local logout still works when the backend is unavailable.
        }

        localStorage.removeItem("yuktiUser");
        setAuthUi(null);
        window.location.href = "login.html";
    });
});

scoreForms.forEach((form) => {
    const fileInput = form.querySelector('input[type="file"]');
    const button = form.querySelector("button");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!fileInput.files.length) {
            setMessage("Please choose a PDF resume first.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("resume", fileInput.files[0]);

        button.disabled = true;
        button.textContent = "Analyzing...";
        setText("[data-score]", "--");
        setText("[data-candidate-level]", "Analyzing");
        setText("[data-skills-match]", "Checking");
        renderAnalysis(null);
        setMessage("Reading resume and calculating score...", "info");

        try {
            const response = await fetch(`${apiBaseUrl}/score`, {
                method: "POST",
                credentials: "include",
                body: formData,
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to calculate score.");
            }

            setText("[data-score]", data.score);
            setText("[data-candidate-level]", data.candidateLevel);
            setText("[data-skills-match]", data.skillsMatch);
            renderAnalysis(data.analysis);
            setMessage("Analysis complete.", "success");
            incrementProcessedCount();
        } catch (error) {
            const message = error instanceof TypeError
                ? "Python backend is not running. Start it with: python web_app.py"
                : error.message;

            setText("[data-score]", "--");
            setText("[data-candidate-level]", "Upload resume");
            setText("[data-skills-match]", "Pending");
            renderAnalysis(null);
            setMessage(message, "error");
        } finally {
            button.disabled = false;
            button.textContent = "Calculate Score";
        }
    });
});
