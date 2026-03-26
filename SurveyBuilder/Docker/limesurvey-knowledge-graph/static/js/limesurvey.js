// ============================================
// VERSION WITH EXTENSIVE DEBUG
// ============================================

async function executeOperation(operation, surveyId = null) {
    console.log('🔍 executeOperation START');
    console.log('  Operation:', operation);
    console.log('  Survey ID:', surveyId);

    const url = document.getElementById('ls_url').value.trim();
    const username = document.getElementById('ls_username').value.trim();
    const password = document.getElementById('ls_password').value.trim();

    if (!validateRequired(url, 'LimeSurvey URL')) return;
    if (!validateRequired(username, 'Username')) return;
    if (!validateRequired(password, 'Password')) return;

    showLoading();

    try {
        const requestBody = {
            url, username, password,
            operation,
            survey_id: surveyId
        };

        console.log('📤 Request body:', JSON.stringify(requestBody, null, 2));

        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        console.log('📥 Response status:', response.status);
        console.log('📥 Response headers:', [...response.headers.entries()]);

        // Get response as text first to see what we got
        const responseText = await response.text();
        console.log('📥 Response text:', responseText);

        // Try to parse as JSON
        let result;
        try {
            result = JSON.parse(responseText);
            console.log('📦 Parsed result:', result);
        } catch (e) {
            console.error('❌ Failed to parse JSON:', e);
            console.error('❌ Response was:', responseText);
            throw new Error('Invalid JSON response from server');
        }

        console.log('✓ Result keys:', Object.keys(result));
        console.log('  - success:', result.success);
        console.log('  - data:', result.data ? `${result.data.length} items` : 'undefined');
        console.log('  - file_path:', result.file_path);
        console.log('  - error:', result.error);
        console.log('  - message:', result.message);

        if (result.success) {
            console.log('✅ Operation successful');

            // Check if it's a file export (has file_path)
            if (result.file_path) {
                console.log('📄 File export detected');
                console.log('   Path:', result.file_path);

                // File export operation
                showToast('Success', `File exported: ${result.file_path}`, 'success');

                // Display file info
                const resultsDiv = document.getElementById('results');
                const contentDiv = document.getElementById('results_content');

                console.log('   results div:', resultsDiv ? 'found' : 'NOT FOUND');
                console.log('   content div:', contentDiv ? 'found' : 'NOT FOUND');

                if (resultsDiv && contentDiv) {
                    const fileName = result.file_path.split('/').pop();
                    contentDiv.innerHTML = `
                        <div class="success">
                            <h3>✅ File Exported Successfully</h3>
                            <p><strong>Operation:</strong> ${operation}</p>
                            <p><strong>File:</strong> ${fileName}</p>
                            <p><strong>Path:</strong> ${result.file_path}</p>
                            ${result.message ? `<p>${result.message}</p>` : ''}
                        </div>
                    `;
                    resultsDiv.style.display = 'block';
                    console.log('   Displayed file info');
                }
            } else if (result.data) {
                console.log('📊 Data export detected');
                console.log('   Items:', result.data.length);

                // Normal data operation
                displayResults(result.data, operation);
                showToast('Success', 'Operation completed', 'success');
            } else {
                console.log('⚠️ Success but no data or file_path');
                showToast('Success', result.message || 'Operation completed', 'success');
            }
        } else {
            console.error('❌ Operation failed');
            console.error('   Error:', result.error);
            throw new Error(result.error || 'Operation failed');
        }
    } catch (error) {
        console.error('❌ EXCEPTION in executeOperation');
        console.error('   Error name:', error.name);
        console.error('   Error message:', error.message);
        console.error('   Error stack:', error.stack);
        handleApiError(error, operation);
    } finally {
        console.log('🏁 executeOperation END');
        hideLoading();
    }
}

async function exportQuestionProperties() {
    console.log('🚀 exportQuestionProperties START');

    const surveyId = document.getElementById('survey_id_question_properties').value.trim();
    console.log('   Survey ID:', surveyId);

    if (!validateRequired(surveyId, 'Survey ID')) {
        console.log('❌ Survey ID validation failed');
        return;
    }

    console.log('✓ Calling executeOperation with question_properties');

    try {
        // Execute operation
        await executeOperation('question_properties', surveyId);

        console.log('✓ executeOperation completed');
        console.log('📥 Triggering download...');

        // Also download JSON file
        const url = document.getElementById('ls_url').value;
        const username = document.getElementById('ls_username').value;
        const password = document.getElementById('ls_password').value;

        const params = new URLSearchParams({
            url, username, password,
            operation: 'question_properties',
            survey_id: surveyId
        });

        const downloadUrl = `/api/export?${params.toString()}`;
        console.log('   Download URL:', downloadUrl);

        // Trigger download
        window.location.href = downloadUrl;

        console.log('✅ exportQuestionProperties END');
    } catch (error) {
        console.error('❌ Error in exportQuestionProperties:', error);
        throw error;
    }
}

async function listSurveys() {
    await executeOperation('list_surveys');
}

async function exportGroups() {
    const surveyId = document.getElementById('survey_id_groups').value.trim();
    if (!validateRequired(surveyId, 'Survey ID')) return;

    await executeOperation('list_groups', surveyId);

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

// ============================================
// ISTRUZIONI
// ============================================

/*
COME USARE QUESTO FILE PER DEBUG:

1. Sostituisci limesurvey.js con questo file

2. Apri la console del browser (F12 → Console)

3. Clicca "Export Question Properties"

4. Nella console vedrai TUTTI i dettagli:
   🔍 executeOperation START
   📤 Request body: {...}
   📥 Response status: 200
   📥 Response text: {...}
   📦 Parsed result: {...}
   ✓ Result keys: [...]
     - success: true/false
     - file_path: ...
     - error: ...

5. COPIA TUTTO L'OUTPUT DELLA CONSOLE e mandamelo

6. Guarda anche il TERMINALE FLASK - dovrebbe mostrare:
   🔍 ex() called with operation: 'question_properties'
   ✅ Matched 'question_properties'
   ...

7. Se vedi errori, mandami:
   - L'output completo della console del browser
   - L'output completo del terminale Flask
*/