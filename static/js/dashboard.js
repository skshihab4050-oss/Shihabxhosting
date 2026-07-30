// ========== DASHBOARD FUNCTIONS ==========

// Load dashboard data
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    // Load user files
    loadUserFiles();
});

// Load user files
async function loadUserFiles() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/files', {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        
        const result = await response.json();
        if (result.success) {
            // Update file list
            const fileList = document.getElementById('fileList');
            if (fileList && result.files) {
                fileList.innerHTML = result.files.map(file => `
                    <div class="file-item">
                        <span>📄 ${file.filename}</span>
                        <span class="file-date">${file.uploaded_at}</span>
                        <a href="/download/${file.id}" class="btn btn-secondary">Download</a>
                        <button onclick="deleteFile(${file.id})" class="btn btn-danger">Delete</button>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

// Delete file
async function deleteFile(fileId) {
    if (!confirm('Are you sure you want to delete this file?')) return;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/files/${fileId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        
        const result = await response.json();
        if (result.success) {
            loadUserFiles(); // Refresh file list
        } else {
            alert('Failed to delete file: ' + result.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}