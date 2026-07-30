// ========== ADMIN FUNCTIONS ==========

// Check if admin is logged in
function isAdminLoggedIn() {
    return localStorage.getItem('adminToken') !== null;
}

// Admin logout
function adminLogout() {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminUser');
    window.location.href = '/admin-login';
}

// Require admin auth
function requireAdminAuth() {
    if (!isAdminLoggedIn()) {
        window.location.href = '/admin-login';
    }
}

// Handle admin login
document.addEventListener('DOMContentLoaded', function() {
    const adminLoginForm = document.querySelector('#adminLoginForm');
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/api/admin-login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    localStorage.setItem('adminToken', result.token);
                    localStorage.setItem('adminUser', JSON.stringify(result.user));
                    window.location.href = '/admin-panel';
                } else {
                    alert('Admin login failed: ' + result.message);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
    }
});