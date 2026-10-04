const form = document.getElementById("dns-form");
const domainInput = document.getElementById("domain-input");
const analyzeBtn = document.getElementById("analyze-btn");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error-box");
const errorTitle = document.getElementById("error-title");
const errorMessage = document.getElementById("error-message");
const results = document.getElementById("results");
const recordCards = document.getElementById("record-cards");

function setLoading(isLoading) {
    analyzeBtn.disabled = isLoading;
    loading.classList.toggle("hidden", !isLoading);
}

function hidePanels() {
    errorBox.classList.add("hidden");
    results.classList.add("hidden");
}

function showError(title, message) {
    errorTitle.textContent = title || "DNS Query Failed";
    errorMessage.textContent =
        message || "The domain could not be resolved. Please check the domain name and try again.";
    errorBox.classList.remove("hidden");
    results.classList.add("hidden");
}

function renderValues(values) {
    if (!values || values.length === 0) {
        return '<p class="empty">No records found.</p>';
    }

    const items = values
        .map((value) => `<li>${escapeHtml(value)}</li>`)
        .join("");
    return `<ul class="record-values">${items}</ul>`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function renderResults(data) {
    document.getElementById("result-domain").textContent = data.domain;
    document.getElementById("result-status").textContent = data.status;
    document.getElementById("result-time").textContent = `${data.response_time_ms} ms`;

    const summary = data.summary;
    document.getElementById("summary-status").textContent = summary.query_status;
    document.getElementById("summary-time").textContent = `${summary.response_time_ms} ms`;
    document.getElementById("summary-types").textContent =
        `${summary.record_types_found}/${summary.record_types_total}`;
    document.getElementById("summary-total").textContent = String(summary.total_records);
    document.getElementById("summary-interpretation").textContent = summary.interpretation;

    const recordOrder = ["A", "AAAA", "MX", "NS", "CNAME", "TXT"];
    recordCards.innerHTML = recordOrder
        .map((type) => {
            const record = (data.records && data.records[type]) || {
                type: type,
                description: "",
                values: [],
            };
            return `
                <article class="record-card">
                    <h3 class="record-type">${escapeHtml(record.type)} RECORD</h3>
                    <p class="record-desc">${escapeHtml(record.description)}</p>
                    ${renderValues(record.values)}
                </article>
            `;
        })
        .join("");

    errorBox.classList.add("hidden");
    results.classList.remove("hidden");
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hidePanels();

    const domain = domainInput.value.trim();
    if (!domain) {
        showError(
            "Invalid Input",
            "Please enter a domain name before analyzing DNS records."
        );
        return;
    }

    setLoading(true);

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ domain }),
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            showError(data.error, data.message);
            return;
        }

        renderResults(data);
    } catch (error) {
        showError(
            "DNS Query Failed",
            "Unable to reach the analyzer. Please make sure the Flask server is running and try again."
        );
    } finally {
        setLoading(false);
    }
});
