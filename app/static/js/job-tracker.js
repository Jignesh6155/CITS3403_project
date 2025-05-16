/**
 * Job Tracker Board JavaScript
 * 
 * Handles all functionality for the job tracking board, including:
 * - Drag and drop between status columns
 * - Modal forms for adding/editing applications
 * - AJAX interactions for status updates and deletions
 * - Filtering and column visibility
 */

/**
 * Toast notification for user feedback
 * @param {string} message - The message to display
 * @param {string} type - Type of toast ('info', 'success', or 'error')
 */
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg text-white ${type === 'success' ? 'bg-green-500' : 'bg-red-500'} transition-opacity duration-300`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

document.addEventListener('DOMContentLoaded', function() {
  // Modal trigger setup
  const modal = document.getElementById('add-application-modal');
  const openModalBtn = document.getElementById('openModal');
  if (openModalBtn && modal) {
    openModalBtn.onclick = () => modal.classList.remove('hidden');
  }

  /**
   * Initialize column visibility dropdowns and settings
   * Restores saved preferences from localStorage
   */
  const columnToggleDropdown = document.getElementById('columnToggleDropdown');
  if (columnToggleDropdown) {
    // Open/close dropdown when button is clicked
    columnToggleDropdown.querySelector('button').onclick = function() {
      const dropdown = document.getElementById('columnDropdown');
      dropdown.classList.toggle('hidden');
    };
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
      const dropdown = document.getElementById('columnDropdown');
      if (!columnToggleDropdown.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.add('hidden');
      }
    });
  }
  
  // Initialize column visibility based on saved preferences
  const checkboxes = document.querySelectorAll('input[type="checkbox"]');
  checkboxes.forEach(checkbox => {
    const columnId = checkbox.dataset.column;
    const isVisible = localStorage.getItem(`column_${columnId}`) !== 'hidden';
    checkbox.checked = isVisible;
    window.toggleColumn(columnId);
  });

  /**
   * Set up job search filter functionality
   * Filters jobs across all columns based on search input
   */
  const searchInput = document.getElementById('job-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      const query = this.value.trim().toLowerCase();
      document.querySelectorAll('[id^="column-"]').forEach(column => {
        column.querySelectorAll('[id^="job-"]').forEach(card => {
          const company = card.querySelector('p.font-semibold')?.textContent.toLowerCase() || '';
          const title = card.querySelector('p.text-gray-600')?.textContent.toLowerCase() || '';
          if (company.includes(query) || title.includes(query)) {
            card.style.display = '';
          } else {
            card.style.display = 'none';
          }
        });
      });
    });
  }

  /**
   * Set up edit job button click handlers
   * Populates the edit modal with current job data
   */
  document.querySelectorAll('.edit-job-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      window.openEditModal(
        this.getAttribute('data-job-id'),
        this.getAttribute('data-title'),
        this.getAttribute('data-company'),
        this.getAttribute('data-location'),
        this.getAttribute('data-job_type'),
        this.getAttribute('data-closing_date'),
        this.getAttribute('data-status')
      );
    });
  });

  /**
   * Set up edit form submission handling
   * Submits form data via AJAX and handles response
   */
  let editForm = document.getElementById('edit-application-form');
  if (editForm) {
    editForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const jobId = document.getElementById('edit-job-id').value;
      fetch(`/update-application/${jobId}`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        body: new FormData(this),
      })
      .then(response => {
        if (!response.ok) throw new Error('Failed to update application');
        return response.json();
      })
      .then(data => {
        if (data.success) {
          window.closeEditModal();
          window.location.reload();
        } else {
          showToast(data.error || 'Failed to update application', 'error');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('Failed to update application. Please try again.', 'error');
      });
    });
  }

  /**
   * Set up delete confirmation modal
   * Handles confirmation flow for job deletion
   */
  let jobToDelete = null;
  
  // When clicking the delete icon, show confirmation modal
  window.confirmDeleteJob = function(id) {
    jobToDelete = id;
    document.getElementById('delete-confirm-modal').classList.remove('hidden');
    document.getElementById('confirm-delete-btn').focus();
  };
  
  // Confirm delete button handler
  document.getElementById('confirm-delete-btn').onclick = function() {
    if (jobToDelete) {
      window.deleteJob(jobToDelete);
      document.getElementById('delete-confirm-modal').classList.add('hidden');
      jobToDelete = null;
    }
  };
  
  // Cancel delete button handler
  document.getElementById('cancel-delete-btn').onclick = function() {
    document.getElementById('delete-confirm-modal').classList.add('hidden');
    jobToDelete = null;
  };
  
  // Close modal button handler
  document.getElementById('close-delete-modal').onclick = function() {
    document.getElementById('delete-confirm-modal').classList.add('hidden');
    jobToDelete = null;
  };
  
  // Enter key should trigger confirm
  window.addEventListener('keydown', function(e) {
    const modal = document.getElementById('delete-confirm-modal');
    if (!modal.classList.contains('hidden') && (e.key === 'Enter' || e.keyCode === 13)) {
      e.preventDefault();
      document.getElementById('confirm-delete-btn').click();
    }
  });

  /**
   * Set up share application modal functionality
   * Handles friend search and selection
   */
  let currentAppId = null;
  
  // Open share modal and reset form
  window.openShareModal = function(appId) {
    currentAppId = appId;
    document.getElementById('shareModal').classList.remove('hidden');
    
    // Clear search and selection
    const searchInput = document.getElementById('share-friend-search');
    if (searchInput) {
      searchInput.value = '';
      searchInput.dispatchEvent(new Event('input'));
    }
    document.querySelectorAll('.share-friend-item').forEach(el => {
      el.classList.remove('bg-indigo-50');
      el.querySelector('input[type="radio"]').checked = false;
    });
  };
  
  // Close share modal
  window.closeShareModal = function() {
    document.getElementById('shareModal').classList.add('hidden');
    currentAppId = null;
  };
  
  // Handle share form submission
  const shareForm = document.getElementById('shareForm');
  if (shareForm) {
    shareForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      // Validate friend selection
      const friendId = this.querySelector('input[name="friend_id"]:checked')?.value;
      if (!friendId) {
        showToast('Please select a friend to share with.', 'error');
        return;
      }
      
      // Prepare form data
      const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
      const formData = new FormData();
      formData.append('friend_id', friendId);
      formData.append('csrf_token', csrfToken);
      
      // Submit sharing request
      fetch(`/share-application/${currentAppId}`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData
      })
      .then(response => {
        if (!response.ok) {
          return response.text().then(text => { throw new Error(text || 'Failed to share application'); });
        }
        if (response.redirected) {
          window.location.href = response.url;
        } else {
          window.closeShareModal();
          showToast('Application shared successfully!', 'success');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('Failed to share application. Please try again.', 'error');
      });
    });
  }
  
  /**
   * Set up friend search in share modal
   * Filters friend list as user types
   */
  const shareFriendSearch = document.getElementById('share-friend-search');
  if (shareFriendSearch) {
    shareFriendSearch.addEventListener('input', function() {
      const searchTerm = this.value.trim().toLowerCase();
      const friendItems = document.querySelectorAll('.share-friend-item');
      let anyVisible = false;
      
      // Filter friends based on search term
      friendItems.forEach(item => {
        const name = item.getAttribute('data-name');
        if (name.includes(searchTerm)) {
          item.style.display = '';
          anyVisible = true;
        } else {
          item.style.display = 'none';
        }
      });
      
      // Update empty state message
      const noFriendsMsg = document.querySelector('#share-friends-list .py-4');
      if (noFriendsMsg && noFriendsMsg.classList.contains('text-center')) {
        if (searchTerm && !anyVisible) {
          noFriendsMsg.textContent = 'No friends match your search';
          noFriendsMsg.style.display = '';
        } else if (!anyVisible) {
          noFriendsMsg.textContent = 'No friends to share with';
          noFriendsMsg.style.display = '';
        } else {
          noFriendsMsg.style.display = 'none';
        }
      }
    });
    
    /**
     * Set up friend item selection behavior
     * Highlights selected friend and checks associated radio button
     */
    document.querySelectorAll('.share-friend-item').forEach(item => {
      item.addEventListener('click', function() {
        const radio = this.querySelector('input[type="radio"]');
        radio.checked = true;
        
        // Update visual selection state
        document.querySelectorAll('.share-friend-item').forEach(el => {
          el.classList.remove('bg-indigo-50');
        });
        this.classList.add('bg-indigo-50');
      });
    });
  }
});

/**
 * Drag and drop start handler
 * Sets data transfer for the dragged job card
 * @param {Event} event - The dragstart event
 */
window.onDragStart = function(event) {
  event.dataTransfer.setData('text/plain', event.target.id);
};

/**
 * Drag and drop handler for job cards
 * Updates job status when dropped in a new column
 * @param {Event} event - The drop event
 * @param {string} columnId - The target column ID (status)
 */
window.onDrop = function(event, columnId) {
  const id = event.dataTransfer.getData('text/plain');
  const jobBox = document.getElementById(id);
  document.getElementById(columnId).appendChild(jobBox);
  
  // Extract job ID from element ID (removing 'job-' prefix)
  const jobId = id.replace('job-', '');
  
  // Update status via API
  fetch('/update-job-status', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({ job_id: jobId, new_status: columnId })
  }).then(response => {
    if (!response.ok) showToast('Failed to update job status.', 'error');
  });
};

/**
 * Helper function to get CSRF token from page
 * @returns {string} CSRF token value
 */
window.getCSRFToken = function() {
  const input = document.querySelector('input[name="csrf_token"]');
  return input ? input.value : '';
};

/**
 * Delete a job application
 * Removes from database and UI
 * @param {string} id - Element ID of job to delete
 */
window.deleteJob = function(id) {
  const jobId = id.replace('job-', '');
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
  
  fetch(`/delete-application/${jobId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    }
  })
  .then(response => {
    if (!response.ok) {
      return response.json().then(data => { throw new Error(data.error || 'Failed to delete job'); });
    }
    return response.json();
  })
  .then(data => {
    if (data.success) {
      // Remove element from UI
      const job = document.getElementById(id);
      if (job) job.remove();
      showToast('Job deleted!', 'success');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    showToast(error.message || 'Failed to delete job. Please try again.', 'error');
  });
};

/**
 * Open edit modal with job data
 * Populates form with current job values
 */
window.openEditModal = function(jobId, title, company, location, jobType, closingDate, status) {
  document.getElementById('edit-job-id').value = jobId;
  document.getElementById('edit-title').value = title;
  document.getElementById('edit-company').value = company;
  document.getElementById('edit-location').value = location;
  document.getElementById('edit-job_type').value = jobType;
  document.getElementById('edit-closing_date').value = closingDate;
  document.getElementById('edit-status').value = status;
  document.getElementById('edit-application-form').action = `/update-application/${jobId}`;
  document.getElementById('edit-application-modal').classList.remove('hidden');
};

/**
 * Close edit modal
 */
window.closeEditModal = function() {
  document.getElementById('edit-application-modal').classList.add('hidden');
};

/**
 * Close add application modal
 */
window.closeModal = function() {
  document.getElementById('add-application-modal').classList.add('hidden');
};

/**
 * Toggle column visibility
 * Shows/hides columns based on checkbox state
 * @param {string} columnId - ID of column to toggle
 */
window.toggleColumn = function(columnId) {
  const column = document.getElementById(`column-${columnId}`);
  const checkbox = document.querySelector(`input[data-column="${columnId}"]`);
  if (column && checkbox) {
    if (checkbox.checked) {
      column.classList.remove('hidden');
    } else {
      column.classList.add('hidden');
    }
    // Save preference to localStorage
    localStorage.setItem(`column_${columnId}`, checkbox.checked ? 'visible' : 'hidden');
  }
};
