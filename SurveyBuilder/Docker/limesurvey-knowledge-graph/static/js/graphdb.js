// GraphDB Manager JavaScript

let availableRepositories = [];
let selectedFiles = {
    ontology: null,
    groups: null,
    questions: null
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('GraphDB Manager loaded');
    refreshRepositories();
});

// ==================== REPOSITORY MANAGEMENT ====================
async function refreshRepositories() {
    try {
        const url = document.getElementById('graphdb_url').value;
        const response = await fetch(`/api/graphdb/repositories?url=${encodeURIComponent(url)}`);
        const result = await response.json();

        if (result.success && result.data) {
            availableRepositories = result.data;
            updateRepositorySelects();
            showToast('Success', `Loaded ${result.data.length} repositories`, 'success');
        } else {
            throw new Error(result.message || 'Failed to load repositories');
        }
    } catch (error) {
        handleApiError(error, 'refreshRepositories');
    }
}

function updateRepositorySelects() {
    const selects = [
        'repo_select_list',
        'onto_repo_select',
        'data_repo_select'
    ];

    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (!select) return;

        const currentValue = select.value;
        select.innerHTML = '<option value="">-- Select Repository --</option>';

        availableRepositories.forEach(repo => {
            const option = document.createElement('option');
            option.value = repo.id;
            option.textContent = `${repo.id}${repo.title ? ' - ' + repo.title : ''}`;
            select.appendChild(option);
        });

        if (currentValue) {
            select.value = currentValue;
        }
    });
}

function selectRepositoryFromList() {
    const select = document.getElementById('repo_select_list');
    const repoId = select.value;

    if (!repoId) {
        document.getElementById('repo_details').style.display = 'none';
        return;
    }

    const repo = availableRepositories.find(r => r.id === repoId);
    if (!repo) return;

    // Update danger zone input
    document.getElementById('danger_repo_id').value = repoId;

    // Show details
    const detailsDiv = document.getElementById('repo_details');
    const contentDiv = document.getElementById('repo_details_content');

    contentDiv.innerHTML = `
        <p><strong>ID:</strong> ${repo.id}</p>
        <p><strong>Title:</strong> ${repo.title || 'N/A'}</p>
        <p><strong>Type:</strong> ${repo.type || 'N/A'}</p>
        <p><strong>Location:</strong> ${repo.location || 'N/A'}</p>
    `;

    detailsDiv.style.display = 'block';
}

async function listAllRepositories() {
    try {
        const url = document.getElementById('graphdb_url').value;
        const response = await fetch(`/api/graphdb/repositories?url=${encodeURIComponent(url)}`);
        const result = await response.json();

        if (result.success && result.data) {
            let html = '<div class="table-container"><table>';
            html += '<thead><tr><th>ID</th><th>Title</th><th>Type</th></tr></thead>';
            html += '<tbody>';

            result.data.forEach(repo => {
                html += `<tr>
                    <td>${repo.id}</td>
                    <td>${repo.title || '-'}</td>
                    <td>${repo.type || '-'}</td>
                </tr>`;
            });

            html += '</tbody></table></div>';

            document.getElementById('repo_results').innerHTML = html;
        }
    } catch (error) {
        handleApiError(error, 'listAllRepositories');
    }
}

async function createNewRepository() {
    const repoId = document.getElementById('new_repo_id').value.trim();
    const repoTitle = document.getElementById('new_repo_title').value.trim();
    const ruleset = document.getElementById('new_repo_ruleset').value;

    if (!validateRequired(repoId, 'Repository ID')) return;

    if (!/^[a-z0-9_-]+$/.test(repoId)) {
        showToast('Validation Error', 'Repository ID must be lowercase with no spaces', 'error');
        return;
    }

    showLoading();

    try {
        const data = {
            graphdb_url: document.getElementById('graphdb_url').value,
            repo_id: repoId,
            repo_title: repoTitle,
            ruleset: ruleset
        };

        const response = await fetch('/api/graphdb/repository/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Success', result.message, 'success');
            document.getElementById('new_repo_id').value = '';
            document.getElementById('new_repo_title').value = '';
            await refreshRepositories();
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        handleApiError(error, 'createNewRepository');
    } finally {
        hideLoading();
    }
}

async function clearRepositoryData() {
    const repoId = document.getElementById('danger_repo_id').value.trim();

    if (!validateRequired(repoId, 'Repository ID')) return;

    const confirmed = confirm(`⚠️ CLEAR REPOSITORY\n\nThis will delete ALL data from repository "${repoId}".\n\nThe repository structure will remain, but all triples will be deleted.\n\nAre you sure?`);

    if (!confirmed) return;

    showLoading();

    try {
        const data = {
            graphdb_url: document.getElementById('graphdb_url').value,
            repo_id: repoId
        };

        const response = await fetch('/api/graphdb/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Success', result.message, 'success');
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        handleApiError(error, 'clearRepositoryData');
    } finally {
        hideLoading();
    }
}

async function deleteRepository() {
    const repoId = document.getElementById('danger_repo_id').value.trim();

    if (!validateRequired(repoId, 'Repository ID')) return;

    const confirmed1 = confirm(`⚠️⚠️⚠️ DELETE REPOSITORY ⚠️⚠️⚠️\n\nThis will PERMANENTLY DELETE the repository "${repoId}" and ALL its data.\n\nThis action CANNOT be undone!\n\nAre you absolutely sure?`);

    if (!confirmed1) return;

    const confirmed2 = prompt(`Type the repository ID "${repoId}" to confirm deletion:`);

    if (confirmed2 !== repoId) {
        showToast('Cancelled', 'Repository ID does not match', 'warning');
        return;
    }

    showLoading();

    try {
        const data = {
            graphdb_url: document.getElementById('graphdb_url').value,
            repo_id: repoId
        };

        const response = await fetch('/api/graphdb/repository/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Success', result.message, 'success');
            document.getElementById('danger_repo_id').value = '';
            await refreshRepositories();
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        handleApiError(error, 'deleteRepository');
    } finally {
        hideLoading();
    }
}

// ==================== ONTOLOGY MANAGEMENT ====================
function refreshOntologyRepos() {
    refreshRepositories();
}

async function loadOntologiesForRepo() {
    const repoId = document.getElementById('onto_repo_select').value;
    const listEl = document.getElementById('ontologies_list');

    if (!repoId) {
        listEl.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">Select a repository to view loaded named graphs</p>';
        return;
    }

    listEl.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">Loading named graphs...</p>';

    try {
        const graphdb_url = document.getElementById('graphdb_url').value;

        const response = await fetch('/api/graphdb/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                graphdb_url: graphdb_url,
                repo_id: repoId,
                query: `
                    SELECT DISTINCT ?graph (COUNT(?s) as ?triples)
                    WHERE {
                        GRAPH ?graph {
                            ?s ?p ?o
                        }
                    }
                    GROUP BY ?graph
                    ORDER BY ?graph
                `
            })
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Query failed');
        }

        const bindings = result.data.results.bindings;

        if (bindings.length === 0) {
            listEl.innerHTML = '<p style="color: #999; font-size: 0.9em; padding: 10px;">No named graphs found in this repository</p>';
            return;
        }

        let html = '<div class="table-container"><table style="font-size: 0.85em;">';
        html += '<thead><tr><th>Named Graph</th><th>Triples</th><th>Actions</th></tr></thead><tbody>';

        bindings.forEach(binding => {
            const graph = binding.graph.value;
            const triples = binding.triples.value;
            const isOntology = graph.includes('ontology') || graph.includes('owl');
            const icon = isOntology ? '📚' : '📊';

            const displayGraph = graph.length > 60 ? graph.substring(0, 57) + '...' : graph;

            html += `<tr>
                <td title="${graph}">${icon} ${displayGraph}</td>
                <td>${triples}</td>
                <td>
                    <button class="btn btn-small btn-danger" onclick="deleteNamedGraph('${encodeURIComponent(graph)}')" style="padding: 4px 8px; font-size: 0.8em;">
                        🗑️ Delete
                    </button>
                </td>
            </tr>`;
        });

        html += '</tbody></table></div>';
        listEl.innerHTML = html;

    } catch (error) {
        console.error('Error loading ontologies:', error);
        listEl.innerHTML = `<p style="color: #ef5350; font-size: 0.9em; padding: 10px;">❌ Error: ${error.message}</p>`;
        showToast('Error', `Failed to load ontologies: ${error.message}`, 'error');
    }
}

async function deleteNamedGraph(encodedGraphUri) {
    const graphUri = decodeURIComponent(encodedGraphUri);

    if (!confirm(`Delete named graph:\n${graphUri}\n\nThis cannot be undone!`)) return;

    showLoading();

    try {
        const repoId = document.getElementById('onto_repo_select').value;
        const data = {
            graphdb_url: document.getElementById('graphdb_url').value,
            repo_id: repoId,
            context: graphUri
        };

        const response = await fetch('/api/graphdb/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Success', 'Named graph deleted', 'success');
            await loadOntologiesForRepo();
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        handleApiError(error, 'deleteNamedGraph');
    } finally {
        hideLoading();
    }
}

function handleOntologyFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        selectedFiles.ontology = file;
        document.getElementById('ontology_file_path').value = file.name;
        showToast('File Selected', `Ontology: ${file.name}`, 'success');
    }
}

async function uploadOntology() {
    const repoId = document.getElementById('onto_repo_select').value;
    const context = document.getElementById('ontology_context').value;

    if (!validateRequired(repoId, 'Repository')) return;
    if (!selectedFiles.ontology) {
        showToast('Error', 'Please select an ontology file', 'error');
        return;
    }

    const btn = document.getElementById('upload_ontology_btn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner-inline"></div> Uploading...';

    updateProgress('ontology_progress', 10, 'Uploading file to server...');

    try {
        // Upload file to server
        const filepath = await uploadFileToServer(selectedFiles.ontology);

        updateProgress('ontology_progress', 50, 'Uploading to GraphDB...');

        // Upload to GraphDB
        const data = {
            graphdb_url: document.getElementById('graphdb_url').value,
            repo_id: repoId,
            ontology_file: filepath,
            context: context
        };

        const response = await fetch('/api/graphdb/upload/ontology', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            updateProgress('ontology_progress', 100, 'Upload complete!');
            showToast('Success', result.message, 'success');

            // Clear selection
            selectedFiles.ontology = null;
            document.getElementById('ontology_file_path').value = '';
            document.getElementById('ontology_file_input').value = '';

            // Reload ontologies list
            await loadOntologiesForRepo();
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        hideProgress('ontology_progress');
        handleApiError(error, 'uploadOntology');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '📤 Upload Ontology';
    }
}

// ==================== DATA UPLOAD ====================
function refreshDataRepos() {
    refreshRepositories();
}

function handleGroupsFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        selectedFiles.groups = file;
        document.getElementById('groups_file_path').value = file.name;
        showToast('File Selected', `Groups: ${file.name}`, 'success');
    }
}

function handleQuestionsFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        selectedFiles.questions = file;
        document.getElementById('questions_file_path').value = file.name;
        showToast('File Selected', `Questions: ${file.name}`, 'success');
    }
}

async function uploadGroups() {
    const repoId = document.getElementById('data_repo_select').value;
    const surveyId = document.getElementById('survey_id_data').value.trim();

    if (!validateRequired(repoId, 'Repository')) return;
    if (!validateRequired(surveyId, 'Survey ID')) return;
    if (!selectedFiles.groups) {
        showToast('Error', 'Please select a groups CSV file', 'error');
        return;
    }

    updateProgress('groups_progress', 10, 'Uploading file...');

    try {
        // Upload file
        const filepath = await uploadFileToServer(selectedFiles.groups);

        updateProgress('groups_progress', 40, 'Converting CSV to RDF...');

        // Convert CSV to RDF
        const convertResponse = await fetch('/api/convert/csv-to-rdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                csv_path: filepath,
                data_type: 'group',
                survey_id: surveyId
            })
        });

        const convertResult = await convertResponse.json();
        if (!convertResult.success) {
            throw new Error(convertResult.error);
        }

        updateProgress('groups_progress', 70, 'Uploading to GraphDB...');

        // Upload to GraphDB
        const uploadResponse = await fetch('/api/graphdb/upload/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                graphdb_url: document.getElementById('graphdb_url').value,
                repo_id: repoId,
                data_type: 'groups',
                file_path: convertResult.output_path,
                survey_id: surveyId
            })
        });

        const uploadResult = await uploadResponse.json();

        if (uploadResult.success) {
            updateProgress('groups_progress', 100, 'Upload complete!');
            showToast('Success', 'Groups uploaded successfully', 'success');
        } else {
            throw new Error(uploadResult.message);
        }
    } catch (error) {
        hideProgress('groups_progress');
        handleApiError(error, 'uploadGroups');
    }
}

async function uploadQuestions() {
    const repoId = document.getElementById('data_repo_select').value;
    const surveyId = document.getElementById('survey_id_data').value.trim();

    if (!validateRequired(repoId, 'Repository')) return;
    if (!validateRequired(surveyId, 'Survey ID')) return;
    if (!selectedFiles.questions) {
        showToast('Error', 'Please select a questions CSV file', 'error');
        return;
    }

    updateProgress('questions_progress', 10, 'Uploading file...');

    try {
        // Upload file
        const filepath = await uploadFileToServer(selectedFiles.questions);

        updateProgress('questions_progress', 40, 'Converting CSV to RDF...');

        // Convert CSV to RDF
        const convertResponse = await fetch('/api/convert/csv-to-rdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                csv_path: filepath,
                data_type: 'question',
                survey_id: surveyId
            })
        });

        const convertResult = await convertResponse.json();
        if (!convertResult.success) {
            throw new Error(convertResult.error);
        }

        updateProgress('questions_progress', 70, 'Uploading to GraphDB...');

        // Upload to GraphDB
        const uploadResponse = await fetch('/api/graphdb/upload/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                graphdb_url: document.getElementById('graphdb_url').value,
                repo_id: repoId,
                data_type: 'questions',
                file_path: convertResult.output_path,
                survey_id: surveyId
            })
        });

        const uploadResult = await uploadResponse.json();

        if (uploadResult.success) {
            updateProgress('questions_progress', 100, 'Upload complete!');
            showToast('Success', 'Questions uploaded successfully', 'success');
        } else {
            throw new Error(uploadResult.message);
        }
    } catch (error) {
        hideProgress('questions_progress');
        handleApiError(error, 'uploadQuestions');
    }
}

async function uploadAllData() {
    if (!selectedFiles.groups || !selectedFiles.questions) {
        showToast('Error', 'Please select both groups and questions files', 'error');
        return;
    }

    updateProgress('batch_progress', 0, 'Starting batch upload...');

    try {
        // Upload groups
        updateProgress('batch_progress', 10, 'Uploading groups...');
        await uploadGroups();

        await new Promise(resolve => setTimeout(resolve, 500));

        // Upload questions
        updateProgress('batch_progress', 55, 'Uploading questions...');
        await uploadQuestions();

        updateProgress('batch_progress', 100, 'All data uploaded!');
        showToast('Complete', 'All survey data has been uploaded', 'success');
    } catch (error) {
        hideProgress('batch_progress');
        handleApiError(error, 'uploadAllData');
    }
}