// JavaScript for settings functionality
document.addEventListener('DOMContentLoaded', function() {
  const settingsButton = document.getElementById('settingsButton');
  if (!settingsButton) return; // Exit if not on a page with settings button
  
  const settingsDropdown = document.getElementById('settingsDropdown');
  
  // Toggle settings dropdown
  settingsButton.addEventListener('click', function() {
    settingsDropdown.classList.toggle('hidden');
  });
  
  // Close dropdown when clicking outside
  document.addEventListener('click', function(event) {
    if (!settingsButton.contains(event.target) && !settingsDropdown.contains(event.target)) {
      settingsDropdown.classList.add('hidden');
    }
  });
  
  // Register form handlers
  registerSettingsFormHandlers();
});

// Modal functions
function openSettingsModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('hidden');
    // Close any dropdowns
    document.getElementById('settingsDropdown')?.classList.add('hidden');
  }
}

function closeSettingsModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('hidden');
  }
}

// Form submission handling
function registerSettingsFormHandlers() {
  const forms = {
    'change-name-form': '/update-name',
    'change-password-form': '/update-password'
  };
  
  Object.entries(forms).forEach(([formId, endpoint]) => {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const formData = new FormData(form);
      
      // Password validation for change-password-form
      if (formId === 'change-password-form') {
        const newPassword = formData.get('new_password');
        const confirmPassword = formData.get('confirm_password');
        
        if (newPassword !== confirmPassword) {
          showToast('Passwords do not match', 'error');
          return;
        }
      }
      
      fetch(endpoint, {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showToast(data.message || 'Settings updated successfully', 'success');
          closeSettingsModal(formId.replace('form', 'modal'));
          
          // Refresh the page if needed
          if (data.refresh) {
            setTimeout(() => window.location.reload(), 1500);
          }
        } else {
          showToast(data.message || 'Failed to update settings', 'error');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
      });
    });
  });
  
  // Close modals when clicking outside
  const modals = document.querySelectorAll('[id$="-modal"]');
  modals.forEach(modal => {
    modal.addEventListener('click', function(event) {
      if (event.target === modal) {
        modal.classList.add('hidden');
      }
    });
  });
}

// Toast notification function
function showToast(message, type = 'info') {
  // Remove any existing toasts
  const existingToasts = document.querySelectorAll('.toast-notification');
  existingToasts.forEach(toast => toast.remove());
  
  // Create new toast
  const toast = document.createElement('div');
  toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg text-white ${
    type === 'success' ? 'bg-green-500' : 
    type === 'error' ? 'bg-red-500' : 
    'bg-blue-500'
  } transition-opacity duration-300 toast-notification z-50`;
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  // Fade out and remove after 3 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}