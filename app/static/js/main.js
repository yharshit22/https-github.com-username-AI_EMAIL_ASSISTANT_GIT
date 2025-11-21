// Main JavaScript file for AI Email Assistant

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add loading state to buttons
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
            }
        });
    });
});

// Utility functions
function showNotification(message, type = 'info') {
    // Create notification element
    var notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Email related functions
function markEmailAsRead(emailId) {
    fetch(`/api/emails/${emailId}/mark_read`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    }).then(response => {
        if (response.ok) {
            // Update UI
            var row = document.querySelector(`tr[data-email-id="${emailId}"]`);
            if (row) {
                row.classList.remove('table-primary');
            }
        }
    });
}

function toggleEmailFlag(emailId) {
    fetch(`/api/emails/${emailId}/toggle_flag`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    }).then(response => {
        if (response.ok) {
            window.location.reload();
        } else {
            showNotification('Failed to toggle flag', 'danger');
        }
    });
}

// Bulk operations
function selectAllEmails(checked) {
    var checkboxes = document.querySelectorAll('.email-checkbox');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = checked;
    });
    updateBulkActions();
}

function getSelectedEmails() {
    var checkboxes = document.querySelectorAll('.email-checkbox:checked');
    return Array.from(checkboxes).map(function(checkbox) {
        return parseInt(checkbox.value);
    });
}

function updateBulkActions() {
    var selectedEmails = getSelectedEmails();
    var bulkActions = document.getElementById('bulkActions');
    var selectedCount = document.getElementById('selectedCount');
    
    if (selectedEmails.length > 0) {
        bulkActions.style.display = 'block';
        selectedCount.textContent = selectedEmails.length;
    } else {
        bulkActions.style.display = 'none';
    }
}

function performBulkAction(action) {
    var selectedEmails = getSelectedEmails();
    if (selectedEmails.length === 0) {
        showNotification('No emails selected', 'warning');
        return;
    }

    confirmAction(`Are you sure you want to ${action} ${selectedEmails.length} email(s)?`, function() {
        fetch('/api/emails/bulk_action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                email_ids: selectedEmails,
                action: action
            })
        }).then(response => response.json())
          .then(data => {
              if (data.success) {
                  showNotification(data.message, 'success');
                  setTimeout(function() {
                      window.location.reload();
                  }, 1000);
              } else {
                  showNotification(data.message || 'Bulk action failed', 'danger');
              }
          });
    });
}

// Search and filter functions
function debounce(func, wait) {
    var timeout;
    return function executedFunction(...args) {
        var later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function searchEmails(query) {
    if (query.length < 2) return;
    
    fetch(`/api/emails/search?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    }).then(response => response.json())
      .then(data => {
          if (data.emails) {
              updateEmailTable(data.emails);
          }
      });
}

function updateEmailTable(emails) {
    // Implementation depends on your table structure
    console.log('Update email table with search results:', emails);
}

// Utility function to get CSRF token
function getCsrfToken() {
    var token = document.querySelector('meta[name="csrf-token"]');
    if (token) {
        return token.getAttribute('content');
    }
    
    // Try to find it in cookies
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.startsWith('csrf_token=')) {
            return cookie.substring('csrf_token='.length);
        }
    }
    
    return '';
}

// Settings and configuration
function saveSettings(settings) {
    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(settings)
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              showNotification('Settings saved successfully', 'success');
          } else {
              showNotification('Failed to save settings', 'danger');
          }
      });
}

// Theme switching
function toggleTheme() {
    var currentTheme = document.documentElement.getAttribute('data-theme');
    var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Load saved theme
function loadTheme() {
    var savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// Auto-refresh functionality
function startAutoRefresh(intervalMinutes) {
    setInterval(function() {
        // Check if user is on dashboard or email list
        if (window.location.pathname === '/' || 
            window.location.pathname === '/dashboard' || 
            window.location.pathname === '/emails') {
            
            fetch('/api/emails/stats', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            }).then(response => response.json())
              .then(data => {
                  if (data.new_emails_count > 0) {
                      showNotification(`You have ${data.new_emails_count} new emails`, 'info');
                  }
              });
        }
    }, intervalMinutes * 60 * 1000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        var searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        var searchInput = document.querySelector('input[name="search"]');
        if (searchInput && searchInput.value) {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
        }
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadTheme();
    
    // Start auto-refresh if enabled
    if (window.autoRefreshEnabled) {
        startAutoRefresh(window.autoRefreshInterval || 5);
    }
    
    // Add search debouncing
    var searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(e) {
            searchEmails(e.target.value);
        }, 300));
    }
});

// Export functions for use in other scripts
window.EmailAssistant = {
    showNotification: showNotification,
    confirmAction: confirmAction,
    markEmailAsRead: markEmailAsRead,
    toggleEmailFlag: toggleEmailFlag,
    selectAllEmails: selectAllEmails,
    performBulkAction: performBulkAction,
    saveSettings: saveSettings,
    toggleTheme: toggleTheme
};