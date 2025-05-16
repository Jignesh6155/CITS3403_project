/**
 * Settings Management JavaScript
 * 
 * This module handles all functionality related to user settings management,
 * including the settings dropdown, modal forms, and API interactions to update
 * user settings such as name and password.
 */

// Initialize settings functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  const settingsButton = document.getElementById('settingsButton');
  if (!settingsButton) return; // Exit if not on a page with settings button
  
  const settingsDropdown = document.getElementById('settingsDropdown');
  
  /**
   * Toggle settings dropdown visibility when settings icon is clicked
   */
  settingsButton.addEventListener('click', function() {
    settingsDropdown.classList.toggle('hidden');
  });
  
  /**
   * Close settings dropdown when clicking outside
   * Handles document-level click events to detect clicks outside the dropdown
   */
  document.addEventListener('click', function(event) {
    if (!settingsButton.contains(event.target) && !settingsDropdown.contains(event.target)) {
      settingsDropdown.classList.add('hidden');
    }
  });
  
  // Set up form handlers for settings forms
  registerSettingsFormHandlers();
});

/**
 * Opens a settings modal for the specified settings type
 * @param {string} modalId - The ID of the modal to open
 */
function openSettingsModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('hidden');
    // Close any dropdowns to avoid UI conflicts
    document.getElementById('settingsDropdown')?.classList.add('hidden');
  }
}

/**
 * Closes a settings modal
 * @param {string} modalId - The ID of the modal to close
 */
function closeSettingsModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('hidden');
  }
}

/**
 * Registers event handlers for all settings forms
 * Handles form submission via fetch API and processes responses
 */
function registerSettingsFormHandlers() {
  // Map of form IDs to their respective API endpoints
  const forms = {
    'change-name-form': '/update-name',
    'change-password-form': '/update-password'
  };
  
  // Set up handlers for each form
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
        
        // Validate that passwords match before submitting
        if (newPassword !== confirmPassword) {
          showToast('Passwords do not match', 'error');
          return;
        }
      }
      
      // Submit form data to the API
      fetch(endpoint, {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showToast(data.message || 'Settings updated successfully', 'success');
          closeSettingsModal(formId.replace('form', 'modal'));
          
          // Refresh the page if needed (e.g., after name change)
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
  
  // Add click handler to close modals when clicking outside the modal content
  const modals = document.querySelectorAll('[id$="-modal"]');
  modals.forEach(modal => {
    modal.addEventListener('click', function(event) {
      if (event.target === modal) {
        modal.classList.add('hidden');
      }
    });
  });
}

/**
 * Displays a toast notification to the user
 * @param {string} message - The message to display
 * @param {string} type - The type of toast: 'info', 'success', or 'error'
 */
function showToast(message, type = 'info') {
  // Remove any existing toasts to prevent stacking
  const existingToasts = document.querySelectorAll('.toast-notification');
  existingToasts.forEach(toast => toast.remove());
  
  // Create new toast element
  const toast = document.createElement('div');
  
  // Set color scheme based on type
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
