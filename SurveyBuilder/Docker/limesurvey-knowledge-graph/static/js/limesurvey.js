async function executeOperation(operation, surveyId = null) {
    const url = document.getElementById('ls_url').value.trim();
    const username = document.getElementById('ls_username').value.trim();
    const password = document.getElementById('ls_password').value.trim();

    if (!validateRequired(url, 'LimeSurvey URL')) return;
    if (!validateRequired(username, 'Username')) return;
    if (!validateRequired(password, 'Password')) return;

    showLoading();

    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url, username, password,
                operation,
                survey_id: surveyId
            })
        });

        const result = await response.json();

        if (result.success) {
            displayResults(result.data, operation);
            showToast('Success', 'Operation completed', 'success');
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        handleApiError(error, operation);
    } finally {
        hideLoading();
    }
}

async function listSurveys() {
    await executeOperation('list_surveys');
}

async function exportGroups() {
    const surveyId = document.getElementById('survey_id_groups').value.trim();
    if (!validateRequired(surveyId, 'Survey ID')) return;

    await executeOperation('list_groups', surveyId);

    // Also download CSV
    const url = document.getElementById('ls_url').value;
    const username = document.getElementById('ls_username').value;
    const password = document.getElementById('ls_password').value;

    const params = new URLSearchParams({
        url, username, password,
        operation: 'list_groups',
        survey_id: surveyId
    });

    window.location.href = `/api/export?${params.toString()}`;
}

async function exportQuestions() {
    const surveyId = document.getElementById('survey_id_questions').value.trim();
    if (!validateRequired(surveyId, 'Survey ID')) return;

    await executeOperation('list_questions', surveyId);

    // Also download CSV
    const url = document.getElementById('ls_url').value;
    const username = document.getElementById('ls_username').value;
    const password = document.getElementById('ls_password').value;

    const params = new URLSearchParams({
        url, username, password,
        operation: 'list_questions',
        survey_id: surveyId
    });

    window.location.href = `/api/export?${params.toString()}`;
}

async function exportResponses() {
    const surveyId = document.getElementById('survey_id_responses').value.trim();
    if (!validateRequired(surveyId, 'Survey ID')) return;

    await executeOperation('export_responses', surveyId);
}

function displayResults(data, operation) {
    const resultsDiv = document.getElementById('results');
    const contentDiv = document.getElementById('results_content');

    let html = '';

    if (Array.isArray(data) && data.length > 0) {
        html += `<div class="status">Found ${data.length} items</div>`;
        html += '<div class="table-container"><table>';

        const headers = Object.keys(data[0]);
        html += '<thead><tr>';
        headers.forEach(h => html += `<th>${h}</th>`);
        html += '</tr></thead><tbody>';

        data.forEach(row => {
            html += '<tr>';
            headers.forEach(h => {
                const value = row[h] !== null ? row[h] : '-';
                html += `<td>${escapeHtml(String(value))}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table></div>';
    } else if (typeof data === 'object') {
        html += '<div class="table-container"><table>';
        for (const [key, value] of Object.entries(data)) {
            html += `<tr><th>${key}</th><td>${value !== null ? escapeHtml(String(value)) : '-'}</td></tr>`;
        }
        html += '</table></div>';
    } else {
        html += `<div class="success">✅ ${data}</div>`;
    }

    contentDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}