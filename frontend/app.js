// Configuration
const API_URL = "http://127.0.0.1:8000";

// DOM Elements - Inputs
const commentInput = document.getElementById("comment-input");
const thresholdSlider = document.getElementById("threshold-slider");
const thresholdVal = document.getElementById("threshold-val");
const analyzeBtn = document.getElementById("analyze-btn");
const clearBtn = document.getElementById("clear-btn");
const charCounter = document.getElementById("char-counter");
const sampleChips = document.querySelectorAll(".sample-chip");

// DOM Elements - State Views
const idleView = document.getElementById("idle-view");
const loadingView = document.getElementById("loading-view");
const errorView = document.getElementById("error-view");
const resultsView = document.getElementById("results-view");
const errorMessage = document.getElementById("error-message");
const retryBtn = document.getElementById("retry-btn");

// DOM Elements - Results Output
const latencyBadge = document.getElementById("latency-badge");
const verdictBanner = document.getElementById("verdict-banner");
const verdictIcon = document.getElementById("verdict-icon");
const verdictText = document.getElementById("verdict-text");

// DOM Elements - Footer Status
const apiStatusDot = document.getElementById("api-status-dot");
const apiStatusText = document.getElementById("api-status-text");

// Toxicity labels from backend
const CATEGORIES = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"];

/* ==========================================================================
   State Management & UI Toggles
   ========================================================================== */
function showState(state) {
    // Hide all views first
    idleView.classList.add("hidden");
    loadingView.classList.add("hidden");
    errorView.classList.add("hidden");
    resultsView.classList.add("hidden");

    // Activate selected view
    if (state === "idle") idleView.classList.remove("hidden");
    else if (state === "loading") loadingView.classList.remove("hidden");
    else if (state === "error") errorView.classList.remove("hidden");
    else if (state === "results") resultsView.classList.remove("hidden");
}

/* ==========================================================================
   API Connectivity Status Checks
   ========================================================================== */
async function checkApiStatus() {
    apiStatusDot.className = "status-dot loading";
    apiStatusText.textContent = "Connecting to API...";
    
    try {
        const response = await fetch(`${API_URL}/api/health`, { signal: AbortSignal.timeout(4000) });
        if (response.ok) {
            const data = await response.json();
            apiStatusDot.className = "status-dot online";
            if (data.model_loaded) {
                apiStatusText.textContent = `Backend online (Inference ready - ${data.device.toUpperCase()})`;
            } else {
                apiStatusText.textContent = "Backend online (Model pre-loading...)";
            }
            return true;
        }
    } catch (e) {
        apiStatusDot.className = "status-dot offline";
        apiStatusText.textContent = "Backend offline (Check model weight setup)";
    }
    return false;
}

/* ==========================================================================
   Inference Submission & UI Processing
   ========================================================================== */
async function analyzeComment() {
    const text = commentInput.value.trim();
    const threshold = parseFloat(thresholdSlider.value);

    if (!text) {
        commentInput.focus();
        // Shake animation fallback for empty input
        commentInput.style.animation = "shake 0.4s ease";
        setTimeout(() => commentInput.style.animation = "", 400);
        return;
    }

    showState("loading");
    const startTime = performance.now();

    try {
        const response = await fetch(`${API_URL}/api/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                text: text,
                threshold: threshold
            })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Server inference error");
        }

        const predictions = await response.json();
        const latencyMs = (performance.now() - startTime).toFixed(1);
        
        displayResults(predictions, threshold, latencyMs);
    } catch (err) {
        console.error(err);
        errorMessage.textContent = err.message || "Unable to reach the backend API server. Please confirm the server is started.";
        showState("error");
    }
}

function displayResults(predictions, threshold, latencyMs) {
    // 1. Set latency header
    latencyBadge.innerHTML = `<i data-lucide="clock"></i> ${latencyMs} ms`;
    
    // 2. Scan predictions to check if any category was flagged
    let anyFlagged = false;
    let flaggedList = [];

    CATEGORIES.forEach(cat => {
        const result = predictions[cat];
        const probability = result.probability;
        const flagged = result.flagged;
        
        // Find DOM nodes for this category row
        const rowNode = document.querySelector(`.category-row[data-category="${cat}"]`);
        const valueNode = document.getElementById(`val-${cat}`);
        const barNode = document.getElementById(`bar-${cat}`);

        if (rowNode && valueNode && barNode) {
            // Update percentage label
            valueNode.textContent = `${(probability * 100).toFixed(1)}%`;
            // Animate progress bar width
            barNode.style.width = `${(probability * 100).toFixed(0)}%`;

            // Style class toggling based on threshold flag
            if (flagged) {
                anyFlagged = true;
                flaggedList.push(cat.replace("_", " ").toUpperCase());
                rowNode.classList.add("flagged");
            } else {
                rowNode.classList.remove("flagged");
            }
        }
    });

    // 3. Render Verdict Banner
    verdictBanner.className = "verdict-banner"; // reset
    if (anyFlagged) {
        verdictBanner.classList.add("toxic");
        verdictText.textContent = `Flagged: ${flaggedList.join(", ")}`;
        verdictIcon.setAttribute("data-lucide", "shield-alert");
    } else {
        verdictBanner.classList.add("safe");
        verdictText.textContent = "Safe Comment — Content clean";
        verdictIcon.setAttribute("data-lucide", "shield-check");
    }

    // Refresh icons inside dynamic nodes
    lucide.createIcons();
    showState("results");
}

/* ==========================================================================
   Event Listeners
   ========================================================================== */

// Input word/character counter
commentInput.addEventListener("input", () => {
    const len = commentInput.value.length;
    charCounter.textContent = `${len} character${len === 1 ? "" : "s"}`;
});

// Slider updates threshold indicator value
thresholdSlider.addEventListener("input", () => {
    thresholdVal.textContent = parseFloat(thresholdSlider.value).toFixed(2);
});

// Action buttons
analyzeBtn.addEventListener("click", analyzeComment);

commentInput.addEventListener("keydown", (e) => {
    // Submit with Ctrl+Enter or Cmd+Enter
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        analyzeComment();
    }
});

clearBtn.addEventListener("click", () => {
    commentInput.value = "";
    charCounter.textContent = "0 characters";
    commentInput.focus();
    showState("idle");
});

// Quick Sample Chips
sampleChips.forEach(chip => {
    chip.addEventListener("click", () => {
        const sampleText = chip.getAttribute("data-text");
        commentInput.value = sampleText;
        charCounter.textContent = `${sampleText.length} characters`;
        analyzeComment();
    });
});

// Error view retry connection
retryBtn.addEventListener("click", () => {
    checkApiStatus();
    analyzeComment();
});

// Initialize Status on Load
window.addEventListener("DOMContentLoaded", () => {
    checkApiStatus();
});
