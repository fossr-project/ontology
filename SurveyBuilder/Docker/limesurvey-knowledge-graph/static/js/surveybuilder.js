// Survey Builder JavaScript - COMPLETE & FIXED VERSION
// All functions included, correct HTML IDs, no double prefixes

let selectedGroups = [];
let selectedQuestions = [];
let allGroups = [];
let allQuestions = [];
let draggedElement = null;
let sparqlTemplates = [];
let lastQueryResults = null;
let editTextCallback = null;

// Mapping dei tipi di domanda LimeSurvey
const questionTypes = {
    '5': '5 punti (1-5)',
    'A': 'Array (5 punti)',
    'B': 'Array (10 punti)',
    'C': 'Array (Sì/No/Non so)',
    'D': 'Data',
    'E': 'Array crescente',
    'F': 'Array (Flessibile)',
    'G': 'Genere',
    'H': 'Array per colonna',
    'I': 'Lingua',
    'K': 'Scelta multipla numerica',
    'L': 'Lista (Radio)',
    'M': 'Scelta multipla',
    'N': 'Numerico',
    'O': 'Lista con commento',
    'P': 'Scelta multipla con commento',
    'Q': 'Testi multipli brevi',
    'R': 'Ranking',
    'S': 'Testo breve',
    'T': 'Testo lungo',
    'U': 'Testo lunghissimo',
    'X': 'Testo Boilerplate',
    'Y': 'Sì/No',
    '!': 'Dropdown list',
    ':': 'Array numerico',
    ';': 'Array testo',
    '|': 'Caricamento file',
    '*': 'Equazione'
};

function getQuestionTypeLabel(typeCode) {
    return questionTypes[typeCode] || `Tipo ${typeCode}`;
}

// ==================== HELPER FUNCTIONS ====================

function showToast(title, message, type) {
    console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
    // Puoi implementare un toast UI se vuoi
    const statusEl = document.getElementById('statusMessage');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;
        statusEl.style.display = 'block';
        setTimeout(() => statusEl.style.display = 'none', 5000);
    }
}

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    // Find and activate the clicked tab
    const clickedTab = event.target;
    clickedTab.classList.add('active');

    const tabContent = document.getElementById(tabName);
    if (tabContent) {
        tabContent.classList.add('active');
    }
}

// ==================== TEST CONNECTION ====================
async function testConnection() {
    // ✅ USA GLI ID CORRETTI DALL'HTML
    const url = document.getElementById('graphdbUrl').value;
    const repo = document.getElementById('repository').value;

    showToast('Connection Test', '🧪 Testing connection...', 'info');

    try {
        // ✅ URL CORRETTO (no doppio /surveybuilder/)
        await fetch('/api/surveybuilder/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ graphdb_url: url, repository: repo })
        });

        const response = await fetch('/api/surveybuilder/test');
        const data = await response.json();

        if (data.status === 'error') {
            showToast('Connection Failed', data.message + '\n💡 ' + (data.help || ''), 'error');
            console.error('Connection test failed:', data);
            return;
        }

        console.log('Connection test results:', data);

        let message = `✅ Connected!\n`;
        message += `📊 Total triples: ${data.total_triples}\n`;
        message += `📦 Classes found: ${data.classes.length}\n\n`;

        if (data.classes.length > 0) {
            message += `Top classes:\n`;
            data.classes.slice(0, 5).forEach(c => {
                const className = c.class.split('/').pop().split('#').pop();
                message += `  • ${className}: ${c.count} instances\n`;
            });
        }

        alert(message);
        showToast('Test Complete', 'Connection successful!', 'success');
    } catch (error) {
        showToast('Connection Error', error.message, 'error');
        console.error('Connection error:', error);
    }
}

// ==================== CONNECT TO GRAPHDB ====================
async function connectToGraphDB() {
    // ✅ USA GLI ID CORRETTI DALL'HTML
    const url = document.getElementById('graphdbUrl').value;
    const repo = document.getElementById('repository').value;

    showToast('Loading Data', 'Loading data from GraphDB...', 'info');

    try {
        await fetch('/api/surveybuilder/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ graphdb_url: url, repository: repo })
        });

        const groupsResp = await fetch('/api/surveybuilder/groups');
        const groupsData = await groupsResp.json();

        if (groupsData.status === 'error') {
            throw new Error(groupsData.message);
        }

        allGroups = groupsData.groups;
        console.log('✓ Loaded groups:', allGroups);

        const questionsResp = await fetch('/api/surveybuilder/questions');
        const questionsData = await questionsResp.json();

        if (questionsData.status === 'error') {
            throw new Error(questionsData.message);
        }

        allQuestions = questionsData.questions;
        console.log('✓ Loaded questions:', allQuestions);

        if (allGroups.length === 0 && allQuestions.length === 0) {
            showToast('No Data', '⚠️ No data found! Repository is empty or uses different namespaces.', 'error');
            document.getElementById('itemsList').innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <h4 style="color: #dc3545; margin-bottom: 10px;">Repository empty or wrong namespaces</h4>
                    <p style="text-align: left; padding: 0 20px;">
                        <strong>Check:</strong><br><br>
                        1. Does the repository contain data?<br>
                        2. Data uses namespace:<br>
                           <code style="background: #f0f0f0; padding: 2px 5px;">https://w3id.org/fossr/ontology/limesurvey/</code><br>
                        3. Are there instances of:<br>
                           • <code>ns1:QuestionGroup</code><br>
                           • <code>ls:Question</code><br><br>
                        <strong>Use "Test Connection" to diagnose</strong>
                    </p>
                </div>
            `;
        } else {
            displayItems();
            const totalQuestionsInGroups = allGroups.reduce((sum, g) => sum + (g.questions ? g.questions.length : 0), 0);
            showToast('Data Loaded', `✅ Loaded ${allGroups.length} groups (${totalQuestionsInGroups} linked questions) and ${allQuestions.length} total questions`, 'success');
        }
    } catch (error) {
        showToast('Load Error', '❌ ' + error.message, 'error');
        console.error('Load error:', error);
    }
}

// ==================== DISPLAY ITEMS ====================
function displayItems() {
    const container = document.getElementById('itemsList');
    container.innerHTML = '';

    // Display groups with questions
    allGroups.forEach((group, groupIndex) => {
        const el = document.createElement('div');
        el.className = 'group-item';
        el.id = `group-${group.uri}`;
        const hasQuestions = group.questions && group.questions.length > 0;

        el.innerHTML = `
            <div class="item-header">
                <div style="display: flex; align-items: center; flex: 1;">
                    ${hasQuestions ? `<span class="expand-icon" id="expand-${groupIndex}" onclick="toggleGroupExpand(event, ${groupIndex})">▶</span>` : ''}
                    <div class="item-title" id="group-title-${groupIndex}">${group.name}</div>
                    <span class="edit-icon" onclick="editGroupTitle(event, ${groupIndex})" title="Edit group name">✏️</span>
                    <span class="item-badge">ID ${group.id}</span>
                    ${hasQuestions ? `<span class="question-count">${group.questions.length} Q</span>` : ''}
                </div>
            </div>
            <div class="item-description" id="group-desc-${groupIndex}">${group.description || 'No description'}</div>
            <span class="edit-icon" onclick="editGroupDescription(event, ${groupIndex})" title="Edit description" style="margin-left: 10px; font-size: 0.85em;">✏️ desc</span>
            <div id="questions-container-${groupIndex}" style="display: none; margin-top: 10px;"></div>
        `;

        el.addEventListener('click', (e) => {
            if (!e.target.classList.contains('expand-icon') &&
                !e.target.classList.contains('edit-icon') &&
                !e.target.closest('input')) {
                toggleGroup(group);
            }
        });

        container.appendChild(el);

        // Add nested questions if any
        if (hasQuestions) {
            const questionsContainer = document.getElementById(`questions-container-${groupIndex}`);
            group.questions.forEach((question) => {
                const qEl = document.createElement('div');
                qEl.className = 'nested-question';
                qEl.id = `question-${question.uri}`;
                qEl.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <div style="margin-bottom: 5px;">
                                <strong>Q${question.id}:</strong>
                                <span id="question-text-${groupIndex}-${question.id}" style="cursor: pointer;" onclick="editQuestionText(event, ${groupIndex}, '${question.uri}')" title="Click to edit">${question.text.substring(0, 60)}...</span>
                                <span class="edit-icon" onclick="editQuestionText(event, ${groupIndex}, '${question.uri}')" title="Edit question text">✏️</span>
                            </div>
                            <div style="color: #666; font-size: 0.8em; margin-top: 3px;">
                                <span style="background: #e3f2fd; padding: 2px 6px; border-radius: 3px; margin-right: 5px;">
                                    📝 ${getQuestionTypeLabel(question.questionType)}
                                </span>
                                <span style="color: #999;">${question.variableCod}</span>
                            </div>
                        </div>
                    </div>
                `;

                qEl.addEventListener('click', (e) => {
                    if (!e.target.classList.contains('edit-icon') &&
                        !e.target.id.includes('question-text-') &&
                        !e.target.closest('input')) {
                        e.stopPropagation();
                        toggleQuestion(question);
                    }
                });

                questionsContainer.appendChild(qEl);
            });
        }
    });

    // Display standalone questions (questions without groups)
    const orphanQuestions = allQuestions.filter(q =>
        !allGroups.some(g => g.questions && g.questions.some(gq => gq.uri === q.uri))
    );

    if (orphanQuestions.length > 0) {
        const separator = document.createElement('div');
        separator.style.padding = '10px';
        separator.style.color = '#999';
        separator.style.fontSize = '0.9em';
        separator.innerHTML = '<strong>Questions without group:</strong>';
        container.appendChild(separator);

        orphanQuestions.forEach(q => {
            const el = document.createElement('div');
            el.className = 'question-item';
            el.id = `question-${q.uri}`;
            el.innerHTML = `
                <div class="item-header">
                    <div class="item-title" style="cursor: pointer;" onclick="editOrphanQuestionText(event, '${q.uri}')" title="Click to edit">${q.text.substring(0, 50)}...</div>
                    <span class="edit-icon" onclick="editOrphanQuestionText(event, '${q.uri}')" title="Edit text">✏️</span>
                    <div class="item-badge">Q${q.id}</div>
                </div>
                <div class="item-meta">
                    <span>🏷️ ${q.variableCod}</span>
                    <span>📝 ${getQuestionTypeLabel(q.questionType)}</span>
                </div>
            `;

            el.addEventListener('click', (e) => {
                if (!e.target.classList.contains('edit-icon') &&
                    !e.target.classList.contains('item-title') &&
                    !e.target.closest('input')) {
                    toggleQuestion(q);
                }
            });
            container.appendChild(el);
        });
    }
}

// ==================== TOGGLE FUNCTIONS ====================
function toggleGroupExpand(event, groupIndex) {
    event.stopPropagation();
    const icon = document.getElementById(`expand-${groupIndex}`);
    const container = document.getElementById(`questions-container-${groupIndex}`);
    const groupEl = document.getElementById(`group-${allGroups[groupIndex].uri}`);

    const isExpanded = container.style.display !== 'none';

    if (isExpanded) {
        container.style.display = 'none';
        icon.textContent = '▶';
        groupEl.classList.remove('expanded');
    } else {
        container.style.display = 'block';
        icon.textContent = '▼';
        groupEl.classList.add('expanded');
    }
}

function toggleGroup(group) {
    const index = selectedGroups.findIndex(g => g.uri === group.uri);
    if (index > -1) {
        selectedGroups.splice(index, 1);
        // Remove all questions of this group
        if (group.questions) {
            group.questions.forEach(q => {
                const qIndex = selectedQuestions.findIndex(sq => sq.uri === q.uri);
                if (qIndex > -1) selectedQuestions.splice(qIndex, 1);
            });
        }
    } else {
        selectedGroups.push(group);
        // Add all questions of this group
        if (group.questions) {
            group.questions.forEach(q => {
                if (!selectedQuestions.find(sq => sq.uri === q.uri)) {
                    selectedQuestions.push(q);
                }
            });
        }
    }
    updateUI();
}

function toggleQuestion(question) {
    const index = selectedQuestions.findIndex(q => q.uri === question.uri);
    if (index > -1) {
        selectedQuestions.splice(index, 1);
    } else {
        selectedQuestions.push(question);
    }
    updateUI();
}

// ==================== UPDATE UI ====================
function updateUI() {
    // Update visual selection states
    allGroups.forEach(group => {
        const groupEl = document.getElementById(`group-${group.uri}`);
        if (groupEl) {
            if (selectedGroups.find(g => g.uri === group.uri)) {
                groupEl.classList.add('selected');
            } else {
                groupEl.classList.remove('selected');
            }
        }

        if (group.questions) {
            group.questions.forEach(q => {
                const qEl = document.getElementById(`question-${q.uri}`);
                if (qEl) {
                    if (selectedQuestions.find(sq => sq.uri === q.uri)) {
                        qEl.classList.add('selected');
                    } else {
                        qEl.classList.remove('selected');
                    }
                }
            });
        }
    });

    // Update orphan questions
    allQuestions.forEach(q => {
        const qEl = document.getElementById(`question-${q.uri}`);
        if (qEl) {
            if (selectedQuestions.find(sq => sq.uri === q.uri)) {
                qEl.classList.add('selected');
            } else {
                qEl.classList.remove('selected');
            }
        }
    });

    updatePreview();
    updateJSON();
}

// ==================== UPDATE PREVIEW ====================
function updatePreview() {
    const container = document.getElementById('previewContent');

    if (selectedGroups.length === 0 && selectedQuestions.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: #999;">
                <div style="font-size: 3em; margin-bottom: 20px;">📝</div>
                <p>Select items from the sidebar</p>
            </div>
        `;
        return;
    }

    let html = '<div style="space-y: 20px;">';

    // Display selected groups
    selectedGroups.forEach((group, idx) => {
        const groupQuestions = selectedQuestions.filter(q => q.groupUri === group.uri);

        html += `
            <div style="background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea; margin-bottom: 20px;">
                <h4 style="color: #667eea; margin-bottom: 10px;">📁 ${group.name}</h4>
                <p style="color: #666; margin-bottom: 15px;">${group.description || 'No description'}</p>
        `;

        if (groupQuestions.length > 0) {
            groupQuestions.forEach((q, qIdx) => {
                html += `
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid #28a745;">
                        <div style="font-weight: bold; margin-bottom: 5px;">Q${qIdx + 1}. ${q.text}</div>
                        <div style="color: #666; font-size: 0.9em;">
                            <span style="background: #e3f2fd; padding: 2px 8px; border-radius: 3px; margin-right: 8px;">
                                ${getQuestionTypeLabel(q.questionType)}
                            </span>
                            <span>${q.variableCod}</span>
                        </div>
                    </div>
                `;
            });
        }

        html += '</div>';
    });

    // Display standalone questions
    const standaloneQuestions = selectedQuestions.filter(q =>
        !q.groupUri || !selectedGroups.find(g => g.uri === q.groupUri)
    );

    if (standaloneQuestions.length > 0) {
        html += `
            <div style="background: #fff3cd; padding: 20px; border-radius: 10px; border-left: 4px solid #ffc107; margin-bottom: 20px;">
                <h4 style="color: #856404; margin-bottom: 10px;">⚠️ Questions without group</h4>
        `;

        standaloneQuestions.forEach((q, idx) => {
            html += `
                <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid #ffc107;">
                    <div style="font-weight: bold; margin-bottom: 5px;">Q${idx + 1}. ${q.text}</div>
                    <div style="color: #666; font-size: 0.9em;">
                        <span style="background: #e3f2fd; padding: 2px 8px; border-radius: 3px; margin-right: 8px;">
                            ${getQuestionTypeLabel(q.questionType)}
                        </span>
                        <span>${q.variableCod}</span>
                    </div>
                </div>
            `;
        });

        html += '</div>';
    }

    html += '</div>';
    container.innerHTML = html;
}

// ==================== UPDATE JSON ====================
function updateJSON() {
    const data = {
        groups: selectedGroups.map(g => ({
            uri: g.uri,
            id: g.id,
            name: g.name,
            description: g.description
        })),
        questions: selectedQuestions.map(q => ({
            uri: q.uri,
            id: q.id,
            text: q.text,
            variableCod: q.variableCod,
            questionType: q.questionType,
            groupUri: q.groupUri
        }))
    };

    document.getElementById('jsonOutput').textContent = JSON.stringify(data, null, 2);
}

// ==================== ACTIONS ====================
function clearSelection() {
    selectedGroups = [];
    selectedQuestions = [];
    updateUI();
    showToast('Selection Cleared', 'All selections cleared', 'success');
}

function selectAllGroups() {
    selectedGroups = [...allGroups];
    selectedQuestions = [];

    // Add all questions from all groups
    allGroups.forEach(g => {
        if (g.questions) {
            g.questions.forEach(q => {
                if (!selectedQuestions.find(sq => sq.uri === q.uri)) {
                    selectedQuestions.push(q);
                }
            });
        }
    });

    updateUI();
    showToast('All Selected', `Selected ${allGroups.length} groups`, 'success');
}

function exportSurvey() {
    if (selectedGroups.length === 0 && selectedQuestions.length === 0) {
        showToast('Nothing to Export', 'Select at least one item', 'warning');
        return;
    }

    const data = {
        groups: selectedGroups,
        questions: selectedQuestions
    };

    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'survey_export.json';
    a.click();
    URL.revokeObjectURL(url);

    showToast('Export Complete', 'Survey exported successfully', 'success');
}

function showCreateSurveyModal() {
    if (selectedGroups.length === 0 && selectedQuestions.length === 0) {
        showToast('Nothing Selected', 'Select at least one item first', 'warning');
        return;
    }

    document.getElementById('modalSelectedCount').textContent =
        `${selectedGroups.length} groups, ${selectedQuestions.length} questions`;
    document.getElementById('createSurveyModal').style.display = 'block';
}

function closeCreateSurveyModal() {
    document.getElementById('createSurveyModal').style.display = 'none';
}

async function createSurveyOnLimeSurvey() {
    const title = document.getElementById('surveyTitle').value;
    const url = document.getElementById('limesurveyUrl').value;
    const username = document.getElementById('limesurveyUsername').value;
    const password = document.getElementById('limesurveyPassword').value;

    if (!title) {
        alert('⚠️ Enter a survey name!');
        return;
    }

    showToast('Creating Survey', '🚀 Creating survey on LimeSurvey...', 'info');
    closeCreateSurveyModal();

    try {
        await fetch('/api/surveybuilder/limesurvey/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, username, password })
        });

        const response = await fetch('/api/surveybuilder/limesurvey/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                groups: selectedGroups,
                questions: selectedQuestions
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            showToast('Survey Created', '✅ Survey created successfully!', 'success');
            alert(`✅ Survey "${title}" created!\n\nID: ${data.survey_id}\n\nURL: ${data.url}`);
            window.open(data.url, '_blank');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        showToast('Error', '❌ ' + error.message, 'error');
        alert('❌ Error creating survey:\n\n' + error.message);
    }
}

// Modal click outside to close
window.onclick = function(event) {
    const createModal = document.getElementById('createSurveyModal');
    const editTextModal = document.getElementById('editTextModal');

    if (event.target == createModal) {
        closeCreateSurveyModal();
    }
    if (event.target == editTextModal) {
        closeEditTextModal();
    }
}

// ==================== SEARCH/FILTER ====================
function filterItems() {
    const search = document.getElementById('searchBox').value.toLowerCase().trim();

    if (search === '') {
        document.querySelectorAll('.group-item, .question-item').forEach(el => {
            el.style.display = 'block';
        });
        return;
    }

    // Filter groups
    allGroups.forEach((group) => {
        const groupEl = document.getElementById(`group-${group.uri}`);
        if (groupEl) {
            const searchableText = `${group.name} ${group.description} ${group.id}`.toLowerCase();
            groupEl.style.display = searchableText.includes(search) ? 'block' : 'none';
        }
    });

    // Filter standalone questions
    allQuestions.forEach((q) => {
        const qEl = document.getElementById(`question-${q.uri}`);
        if (qEl && !qEl.classList.contains('nested-question')) {
            const searchableText = `${q.text} ${q.variableCod} ${q.id}`.toLowerCase();
            qEl.style.display = searchableText.includes(search) ? 'block' : 'none';
        }
    });
}

// ==================== EDIT FUNCTIONS WITH MODAL ====================

function editGroupTitle(event, groupIndex) {
    event.stopPropagation();
    const group = allGroups[groupIndex];

    openEditTextModal(
        'Edit Group Name',
        'Group name:',
        group.name,
        (newText) => {
            if (newText.trim() === '') {
                alert('⚠️ Group name cannot be empty!');
                return false;
            }

            allGroups[groupIndex].name = newText.trim();

            // Update in selected groups if present
            const selectedIndex = selectedGroups.findIndex(g => g.uri === allGroups[groupIndex].uri);
            if (selectedIndex > -1) {
                selectedGroups[selectedIndex].name = newText.trim();
            }

            displayItems();
            updateUI();
            showToast('Success', '✅ Group name updated', 'success');
            return true;
        }
    );
}

function editGroupDescription(event, groupIndex) {
    event.stopPropagation();
    const group = allGroups[groupIndex];

    openEditTextModal(
        'Edit Group Description',
        'Description:',
        group.description || '',
        (newText) => {
            allGroups[groupIndex].description = newText;

            // Update in selected groups if present
            const selectedIndex = selectedGroups.findIndex(g => g.uri === allGroups[groupIndex].uri);
            if (selectedIndex > -1) {
                selectedGroups[selectedIndex].description = newText;
            }

            displayItems();
            updateUI();
            showToast('Success', '✅ Group description updated', 'success');
            return true;
        }
    );
}

function editQuestionText(event, groupIndex, questionUri) {
    event.stopPropagation();

    // Find the question in the group by URI
    const group = allGroups[groupIndex];
    const question = group.questions.find(q => q.uri === questionUri);

    if (!question) {
        console.error('Question not found:', questionUri);
        return;
    }

    openEditTextModal(
        'Edit Question Text',
        'Question text:',
        question.text,
        (newText) => {
            if (newText.trim() === '') {
                alert('⚠️ Question text cannot be empty!');
                return false;
            }

            // Update in allGroups
            question.text = newText.trim();

            // Update in allQuestions
            const globalIndex = allQuestions.findIndex(q => q.uri === question.uri);
            if (globalIndex > -1) {
                allQuestions[globalIndex].text = newText.trim();
            }

            // Update in selected questions
            const selectedIndex = selectedQuestions.findIndex(q => q.uri === question.uri);
            if (selectedIndex > -1) {
                selectedQuestions[selectedIndex].text = newText.trim();
            }

            displayItems();
            updateUI();
            showToast('Success', '✅ Question text updated', 'success');
            return true;
        }
    );
}

function editOrphanQuestionText(event, questionUri) {
    event.stopPropagation();

    const question = allQuestions.find(q => q.uri === questionUri);

    if (!question) {
        console.error('Question not found:', questionUri);
        return;
    }

    openEditTextModal(
        'Edit Question Text',
        'Question text:',
        question.text,
        (newText) => {
            if (newText.trim() === '') {
                alert('⚠️ Question text cannot be empty!');
                return false;
            }

            question.text = newText.trim();

            // Update in selected questions if present
            const selectedIndex = selectedQuestions.findIndex(q => q.uri === questionUri);
            if (selectedIndex > -1) {
                selectedQuestions[selectedIndex].text = newText.trim();
            }

            displayItems();
            updateUI();
            showToast('Success', '✅ Question text updated', 'success');
            return true;
        }
    );
}

function openEditTextModal(title, label, currentText, callback) {
    document.getElementById('editTextModalTitle').textContent = title;
    document.getElementById('editTextLabel').textContent = label;
    document.getElementById('editTextArea').value = currentText;
    updateCharCount();

    editTextCallback = callback;

    document.getElementById('editTextModal').style.display = 'block';
    document.getElementById('editTextArea').focus();
}

function closeEditTextModal() {
    document.getElementById('editTextModal').style.display = 'none';
    editTextCallback = null;
}

function saveEditText() {
    const newText = document.getElementById('editTextArea').value;

    if (editTextCallback) {
        const result = editTextCallback(newText);
        // Se callback ritorna false, non chiudere il modal
        if (result !== false) {
            closeEditTextModal();
        }
    } else {
        closeEditTextModal();
    }
}

function updateCharCount() {
    const textarea = document.getElementById('editTextArea');
    const count = document.getElementById('editTextCharCount');
    if (textarea && count) {
        count.textContent = textarea.value.length;
    }
}

// Add event listener for character count update on typing
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('editTextArea');
    if (textarea) {
        textarea.addEventListener('input', updateCharCount);
    }
});

// ==================== SPARQL MODAL FUNCTIONS ====================

async function showSparqlModal() {
    document.getElementById('sparqlModal').style.display = 'block';
    if (sparqlTemplates.length === 0) {
        await loadSparqlTemplates();
    }
}

function closeSparqlModal() {
    document.getElementById('sparqlModal').style.display = 'none';
}

async function loadSparqlTemplates() {
    try {
        const response = await fetch('/api/surveybuilder/sparql/templates');
        const data = await response.json();
        if (data.status === 'success') {
            sparqlTemplates = data.templates;
            const select = document.getElementById('sparqlTemplate');
            select.innerHTML = '<option value="">-- Select template --</option>';
            data.templates.forEach((template, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `${template.name} - ${template.description}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

function loadTemplate() {
    const select = document.getElementById('sparqlTemplate');
    const index = select.value;
    if (index !== '') {
        const template = sparqlTemplates[index];
        document.getElementById('sparqlQueryInput').value = template.query;
    }
}

async function executeSparqlQuery() {
    const query = document.getElementById('sparqlQueryInput').value;
    if (!query.trim()) {
        alert('⚠️ Enter a SPARQL query!');
        return;
    }

    const executeBtn = event.target;
    executeBtn.disabled = true;
    executeBtn.textContent = '⏳ Executing...';

    try {
        const response = await fetch('/api/surveybuilder/sparql/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await response.json();
        if (data.status === 'success') {
            lastQueryResults = data;
            displaySparqlResults(data);
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        alert('❌ Error: ' + error.message);
        console.error('SPARQL error:', error);
    } finally {
        executeBtn.disabled = false;
        executeBtn.textContent = '▶️ Execute Query';
    }
}

function displaySparqlResults(data) {
    const resultsDiv = document.getElementById('sparqlResults');
    const countSpan = document.getElementById('resultCount');
    const headerEl = document.getElementById('resultsHeader');
    const bodyEl = document.getElementById('resultsBody');

    countSpan.textContent = data.count;

    let headerHTML = '<tr>';
    data.columns.forEach(col => {
        headerHTML += `<th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">${col}</th>`;
    });
    headerHTML += '</tr>';
    headerEl.innerHTML = headerHTML;

    let bodyHTML = '';
    data.results.forEach((row, rowIndex) => {
        bodyHTML += `<tr style="background: ${rowIndex % 2 === 0 ? '#fff' : '#f8f9fa'};">`;
        data.columns.forEach(col => {
            const value = row[col] || '';
            const displayValue = value.length > 100 ? value.substring(0, 97) + '...' : value;
            bodyHTML += `<td style="padding: 10px; border-bottom: 1px solid #e0e0e0;" title="${value}">${displayValue}</td>`;
        });
        bodyHTML += '</tr>';
    });
    bodyEl.innerHTML = bodyHTML;
    resultsDiv.style.display = 'block';
}

function exportResultsCSV() {
    if (!lastQueryResults) return;
    let csv = lastQueryResults.columns.join(';') + '\n';
    lastQueryResults.results.forEach(row => {
        const values = lastQueryResults.columns.map(col => {
            const val = row[col] || '';
            return val.includes(';') ? `"${val}"` : val;
        });
        csv += values.join(';') + '\n';
    });
    downloadFile(csv, 'sparql_results.csv', 'text/csv');
}

function exportResultsJSON() {
    if (!lastQueryResults) return;
    const json = JSON.stringify(lastQueryResults.results, null, 2);
    downloadFile(json, 'sparql_results.json', 'application/json');
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function loadResultsIntoApp() {
    if (!lastQueryResults || !lastQueryResults.results || lastQueryResults.results.length === 0) {
        alert('⚠️ No results to load!');
        return;
    }

    const columns = lastQueryResults.columns;
    const results = lastQueryResults.results;

    console.log('Loading SPARQL results into app:', results);
    console.log('Available columns:', columns);

    // Identify data type from column names
    const hasGroupColumns = columns.some(col =>
        col.toLowerCase().includes('group') &&
        !col.toLowerCase().includes('question')
    );
    const hasQuestionColumns = columns.some(col =>
        col.toLowerCase().includes('question')
    );

    let loadedGroups = [];
    let loadedQuestions = [];

    // CASE 1: Query returns groups
    if (hasGroupColumns && !hasQuestionColumns) {
        loadedGroups = parseGroupsFromResults(results, columns);
        showToast('Data Loaded', `✅ Loaded ${loadedGroups.length} groups from SPARQL query`, 'success');
    }
    // CASE 2: Query returns questions
    else if (hasQuestionColumns && !hasGroupColumns) {
        loadedQuestions = parseQuestionsFromResults(results, columns);
        showToast('Data Loaded', `✅ Loaded ${loadedQuestions.length} questions from SPARQL query`, 'success');
    }
    // CASE 3: Query returns both groups and questions
    else if (hasGroupColumns && hasQuestionColumns) {
        const parsed = parseGroupsAndQuestionsFromResults(results, columns);
        loadedGroups = parsed.groups;
        loadedQuestions = parsed.questions;
        showToast('Data Loaded', `✅ Loaded ${loadedGroups.length} groups and ${loadedQuestions.length} questions from SPARQL query`, 'success');
    }
    // CASE 4: Unknown type
    else {
        alert('⚠️ Cannot determine data type from query.\n\nMake sure your query returns columns with names like:\n- "group", "groupId", "groupName" for groups\n- "question", "questionId", "questionText" for questions');
        return;
    }

    // Replace existing data with query results
    if (loadedGroups.length > 0) {
        allGroups = loadedGroups;
    }
    if (loadedQuestions.length > 0) {
        allQuestions = loadedQuestions;
    }

    // Update display
    displayItems();

    // Close modal
    closeSparqlModal();

    // Show confirmation
    const totalQuestionsInGroups = allGroups.reduce((sum, g) => sum + (g.questions ? g.questions.length : 0), 0);
    alert(`✅ Data loaded successfully!\n\n📁 Groups: ${allGroups.length}\n❓ Total questions: ${allQuestions.length}\n└─ Questions in groups: ${totalQuestionsInGroups}`);
}

function parseGroupsFromResults(results, columns) {
    // Find key columns
    const groupCol = columns.find(c => c === 'group' || c.toLowerCase().includes('groupuri'));
    const groupIdCol = columns.find(c => c.toLowerCase().includes('groupid') || c === 'id');
    const groupNameCol = columns.find(c => c.toLowerCase().includes('groupname') || c === 'name');
    const groupDescCol = columns.find(c => c.toLowerCase().includes('description') || c.toLowerCase().includes('desc'));

    if (!groupCol) {
        console.error('No group column found in results');
        return [];
    }

    const groups = [];
    const groupMap = new Map();

    results.forEach(row => {
        const uri = row[groupCol];
        if (!uri || groupMap.has(uri)) return;

        const group = {
            uri: uri,
            id: row[groupIdCol] || `G${groups.length + 1}`,
            name: row[groupNameCol] || 'Unnamed Group',
            description: row[groupDescCol] || '',
            type: 'group',
            questions: []
        };

        groups.push(group);
        groupMap.set(uri, group);
    });

    console.log('Parsed groups:', groups);
    return groups;
}

function parseQuestionsFromResults(results, columns) {
    // Find key columns
    const questionCol = columns.find(c => c === 'question' || c.toLowerCase().includes('questionuri'));
    const questionIdCol = columns.find(c => c.toLowerCase().includes('questionid') || c === 'id');
    const questionTextCol = columns.find(c => c.toLowerCase().includes('questiontext') || c === 'text');
    const variableCol = columns.find(c => c.toLowerCase().includes('variable') || c.toLowerCase().includes('cod'));
    const typeCol = columns.find(c => c.toLowerCase().includes('type') && c.toLowerCase().includes('question'));
    const orderCol = columns.find(c => c.toLowerCase().includes('order'));

    if (!questionCol) {
        console.error('No question column found in results');
        return [];
    }

    const questions = [];
    const questionMap = new Map();

    results.forEach(row => {
        const uri = row[questionCol];
        if (!uri || questionMap.has(uri)) return;

        const question = {
            uri: uri,
            id: row[questionIdCol] || `Q${questions.length + 1}`,
            text: row[questionTextCol] || 'Question without text',
            variableCod: row[variableCol] || '',
            questionType: row[typeCol] || 'L',
            order: row[orderCol] || '0',
            type: 'question'
        };

        questions.push(question);
        questionMap.set(uri, question);
    });

    console.log('Parsed questions:', questions);
    return questions;
}

function parseGroupsAndQuestionsFromResults(results, columns) {
    // Find columns for groups
    const groupCol = columns.find(c => c === 'group' || (c.toLowerCase().includes('group') && c.toLowerCase().includes('uri')));
    const groupIdCol = columns.find(c => c.toLowerCase().includes('groupid'));
    const groupNameCol = columns.find(c => c.toLowerCase().includes('groupname'));
    const groupDescCol = columns.find(c => c.toLowerCase().includes('groupdesc'));

    // Find columns for questions
    const questionCol = columns.find(c => c === 'question' || (c.toLowerCase().includes('question') && c.toLowerCase().includes('uri')));
    const questionIdCol = columns.find(c => c.toLowerCase().includes('questionid'));
    const questionTextCol = columns.find(c => c.toLowerCase().includes('questiontext'));
    const variableCol = columns.find(c => c.toLowerCase().includes('variable'));
    const typeCol = columns.find(c => c.toLowerCase().includes('questiontype'));
    const orderCol = columns.find(c => c.toLowerCase().includes('order'));

    const groupMap = new Map();
    const questionMap = new Map();

    results.forEach(row => {
        // Parse group
        if (groupCol && row[groupCol]) {
            const groupUri = row[groupCol];
            if (!groupMap.has(groupUri)) {
                const group = {
                    uri: groupUri,
                    id: row[groupIdCol] || `G${groupMap.size + 1}`,
                    name: row[groupNameCol] || 'Unnamed Group',
                    description: row[groupDescCol] || '',
                    type: 'group',
                    questions: []
                };
                groupMap.set(groupUri, group);
            }

            // Parse question and link to group
            if (questionCol && row[questionCol]) {
                const questionUri = row[questionCol];
                if (!questionMap.has(questionUri)) {
                    const question = {
                        uri: questionUri,
                        id: row[questionIdCol] || `Q${questionMap.size + 1}`,
                        text: row[questionTextCol] || 'Question without text',
                        variableCod: row[variableCol] || '',
                        questionType: row[typeCol] || 'L',
                        order: row[orderCol] || '0',
                        groupUri: groupUri,
                        type: 'question'
                    };

                    questionMap.set(questionUri, question);
                    groupMap.get(groupUri).questions.push(question);
                }
            }
        }
    });

    const groups = Array.from(groupMap.values());
    const questions = Array.from(questionMap.values());

    console.log('Parsed groups with questions:', groups);
    console.log('Parsed questions:', questions);

    return { groups, questions };
}

// ==================== INITIALIZATION ====================
console.log('✅ Survey Builder JavaScript loaded and ready!');
console.log('📊 Version: COMPLETE with correct HTML IDs');