// Library Advisor JavaScript

let selectedProjectId = '';
let isProcessing = false;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadProjectsFromStorage();
});

function setupEventListeners() {
    // Upload form
    document.getElementById('uploadForm').addEventListener('submit', handleFileUpload);
    
    // Path form
    document.getElementById('pathForm').addEventListener('submit', handlePathAnalysis);
    
    // Project selection
    document.getElementById('selectedProject').addEventListener('change', function() {
        selectedProjectId = this.value;
    });
}

function handleFileUpload(e) {
    e.preventDefault();
    
    if (isProcessing) return;
    
    const fileInput = document.getElementById('projectFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('Please select a file to upload.', 'warning');
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) { // 50MB
        showAlert('File size must be less than 50MB.', 'danger');
        return;
    }
    
    const formData = new FormData();
    formData.append('project', file);
    
    uploadProject(formData);
}

function handlePathAnalysis(e) {
    e.preventDefault();
    
    if (isProcessing) return;
    
    const pathInput = document.getElementById('projectPath');
    const projectPath = pathInput.value.trim();
    
    if (!projectPath) {
        showAlert('Please enter a project path.', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('project_path', projectPath);
    
    uploadProject(formData);
}

function uploadProject(formData) {
    isProcessing = true;
    showProgress(true);
    
    fetch('/api/projects/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(`Project "${data.stats.framework}" analyzed successfully! Processed ${data.stats.files_processed} files and created ${data.stats.chunks_created} embeddings.`, 'success');
            
            // Add project to dropdown
            addProjectToDropdown(data.project_id, data);
            
            // Refresh page to show new project
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showAlert(`Error: ${data.error}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showAlert('Upload failed. Please try again.', 'danger');
    })
    .finally(() => {
        isProcessing = false;
        showProgress(false);
    });
}

function showProgress(show) {
    const progressSection = document.getElementById('progressSection');
    if (show) {
        progressSection.style.display = 'block';
        progressSection.scrollIntoView({ behavior: 'smooth' });
    } else {
        progressSection.style.display = 'none';
    }
}

function addProjectToDropdown(projectId, data) {
    const select = document.getElementById('selectedProject');
    const option = document.createElement('option');
    option.value = projectId;
    option.textContent = `${data.message} (${data.stats.framework})`;
    select.appendChild(option);
}

function selectProject(projectId) {
    selectedProjectId = projectId;
    document.getElementById('selectedProject').value = projectId;
    
    // Highlight selected project
    document.querySelectorAll('.project-card').forEach(card => {
        card.classList.remove('border-primary', 'bg-light');
    });
    
    event.target.closest('.project-card').classList.add('border-primary', 'bg-light');
    
    // Show success message
    showAlert('Project selected! You can now ask questions about it.', 'info', 3000);
}

function setQuery(query) {
    document.getElementById('userQuery').value = query;
}

function askQuestion() {
    if (isProcessing) return;
    
    const query = document.getElementById('userQuery').value.trim();
    const projectId = selectedProjectId;
    
    if (!query) {
        showAlert('Please enter a question.', 'warning');
        return;
    }
    
    if (!projectId) {
        showAlert('Please select a project first.', 'warning');
        return;
    }
    
    isProcessing = true;
    const askButton = document.getElementById('askButton');
    askButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    askButton.disabled = true;
    
    fetch('/api/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: query,
            project_id: projectId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayAnswer(data);
        } else {
            showAlert(`Error: ${data.error}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Query error:', error);
        showAlert('Failed to process query. Please try again.', 'danger');
    })
    .finally(() => {
        isProcessing = false;
        askButton.innerHTML = '<i class="fas fa-paper-plane"></i> Ask Question';
        askButton.disabled = false;
    });
}

function displayAnswer(data) {
    const answerSection = document.getElementById('answerSection');
    const answerContent = document.getElementById('answerContent');
    const confidenceBadge = document.getElementById('confidenceBadge');
    
    // Format and display answer
    answerContent.innerHTML = formatAnswer(data.answer);
    confidenceBadge.textContent = `Confidence: ${Math.round(data.confidence * 100)}%`;
    
    // Display sources if available
    if (data.sources && data.sources.length > 0) {
        displaySources(data.sources);
    }
    
    // Display function calls if available
    if (data.function_calls && data.function_calls.length > 0) {
        displayFunctionCalls(data.function_calls);
    }
    
    // Show the answer section
    answerSection.style.display = 'block';
    answerSection.scrollIntoView({ behavior: 'smooth' });
    answerSection.classList.add('fade-in');
}

function formatAnswer(answer) {
    // Convert markdown-like formatting to HTML
    let formatted = answer;
    
    // Headers
    formatted = formatted.replace(/^### (.*$)/gim, '<h5>$1</h5>');
    formatted = formatted.replace(/^## (.*$)/gim, '<h4>$1</h4>');
    formatted = formatted.replace(/^# (.*$)/gim, '<h3>$1</h3>');
    
    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Code blocks
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Inline code
    formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Line breaks
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Lists
    formatted = formatted.replace(/^- (.*$)/gim, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    return `<div class="answer-content">${formatted}</div>`;
}

function displaySources(sources) {
    const sourcesSection = document.getElementById('sourcesSection');
    const sourcesContent = document.getElementById('sourcesContent');
    
    let html = '';
    sources.forEach((source, index) => {
        html += `
            <div class="source-item">
                <div class="source-header">
                    ${index + 1}. ${source.file_path} 
                    <span class="badge bg-info ms-2">Score: ${source.score.toFixed(3)}</span>
                </div>
                <div class="source-content">${escapeHtml(source.content)}</div>
            </div>
        `;
    });
    
    sourcesContent.innerHTML = html;
    sourcesSection.style.display = 'block';
}

function displayFunctionCalls(functionCalls) {
    const functionCallsSection = document.getElementById('functionCallsSection');
    const functionCallsContent = document.getElementById('functionCallsContent');
    
    let html = '';
    functionCalls.forEach((call, index) => {
        html += `
            <div class="function-call">
                <div class="function-header">
                    <i class="fas fa-cog"></i> ${call.function}
                </div>
                <div><strong>Query:</strong> ${escapeHtml(call.query)}</div>
                <div class="mt-2"><strong>Result:</strong></div>
                <pre class="mt-1">${escapeHtml(call.result)}</pre>
            </div>
        `;
    });
    
    functionCallsContent.innerHTML = html;
    functionCallsSection.style.display = 'block';
}

function showAlert(message, type, duration = 5000) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 400px;';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after duration
    setTimeout(() => {
        if (alertDiv && alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function loadProjectsFromStorage() {
    // This would load projects from localStorage in a real implementation
    // For now, projects are loaded from the server on page refresh
}

// Utility functions for API calls

function checkLibraryCompatibility(library, projectId) {
    return fetch('/api/libraries/check', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            library: library,
            project_id: projectId
        })
    })
    .then(response => response.json());
}

function getLibrarySuggestions(projectId, category = 'general') {
    return fetch('/api/libraries/suggest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            project_id: projectId,
            category: category
        })
    })
    .then(response => response.json());
}

function getProjectProfile(projectId) {
    return fetch(`/api/projects/${projectId}/profile`)
        .then(response => response.json());
}

function getProjectDependencies(projectId) {
    return fetch(`/api/projects/${projectId}/dependencies`)
        .then(response => response.json());
}

// Export functions for use in other scripts
window.LibraryAdvisor = {
    askQuestion,
    selectProject,
    setQuery,
    checkLibraryCompatibility,
    getLibrarySuggestions,
    getProjectProfile,
    getProjectDependencies
};
