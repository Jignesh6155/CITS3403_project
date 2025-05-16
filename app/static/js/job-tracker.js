// Job Tracker Board JavaScript
// All logic moved from jobTracker.html script block

// Toast notification (copied from job-search.js for consistency)
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
  // Modal logic
  const modal = document.getElementById('add-application-modal');
  const openModalBtn = document.getElementById('openModal');
  if (openModalBtn && modal) {
    openModalBtn.onclick = () => modal.classList.remove('hidden');
  }

  // Drag and drop
  window.onDragStart = function(event) {
    event.dataTransfer.setData('text/plain', event.target.id);
  };
  window.onDrop = function(event, columnId) {
    const id = event.dataTransfer.getData('text/plain');
    const jobBox = document.getElementById(id);
    document.getElementById(columnId).appendChild(jobBox);
    const jobId = id.replace('job-', '');
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

  // CSRF helper
  window.getCSRFToken = function() {
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
  };

  // Delete job
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

  // Share modal logic
  let currentAppId = null;
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
  window.closeShareModal = function() {
    document.getElementById('shareModal').classList.add('hidden');
    currentAppId = null;
  };
  const shareForm = document.getElementById('shareForm');
  if (shareForm) {
    shareForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const friendId = this.querySelector('input[name="friend_id"]:checked')?.value;
      if (!friendId) {
        showToast('Please select a friend to share with.', 'error');
        return;
      }
      const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
      const formData = new FormData();
      formData.append('friend_id', friendId);
      formData.append('csrf_token', csrfToken);
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
  // Friend search in share modal
  const shareFriendSearch = document.getElementById('share-friend-search');
  if (shareFriendSearch) {
    shareFriendSearch.addEventListener('input', function() {
      const searchTerm = this.value.trim().toLowerCase();
      const friendItems = document.querySelectorAll('.share-friend-item');
      let anyVisible = false;
      friendItems.forEach(item => {
        const name = item.getAttribute('data-name');
        if (name.includes(searchTerm)) {
          item.style.display = '';
          anyVisible = true;
        } else {
          item.style.display = 'none';
        }
      });
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
    // Friend item click
    document.querySelectorAll('.share-friend-item').forEach(item => {
      item.addEventListener('click', function() {
        const radio = this.querySelector('input[type="radio"]');
        radio.checked = true;
        document.querySelectorAll('.share-friend-item').forEach(el => {
          el.classList.remove('bg-indigo-50');
        });
        this.classList.add('bg-indigo-50');
      });
    });
  }

  // Column visibility dropdown
  const columnToggleDropdown = document.getElementById('columnToggleDropdown');
  if (columnToggleDropdown) {
    columnToggleDropdown.querySelector('button').onclick = function() {
      const dropdown = document.getElementById('columnDropdown');
      dropdown.classList.toggle('hidden');
    };
    document.addEventListener('click', function(event) {
      const dropdown = document.getElementById('columnDropdown');
      if (!columnToggleDropdown.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.add('hidden');
      }
    });
  }
  // Toggle columns
  window.toggleColumn = function(columnId) {
    const column = document.getElementById(`column-${columnId}`);
    const checkbox = document.querySelector(`input[data-column="${columnId}"]`);
    if (column && checkbox) {
      if (checkbox.checked) {
        column.classList.remove('hidden');
      } else {
        column.classList.add('hidden');
      }
      localStorage.setItem(`column_${columnId}`, checkbox.checked ? 'visible' : 'hidden');
    }
  };
  // Initialize column visibility
  const checkboxes = document.querySelectorAll('input[type="checkbox"]');
  checkboxes.forEach(checkbox => {
    const columnId = checkbox.dataset.column;
    const isVisible = localStorage.getItem(`column_${columnId}`) !== 'hidden';
    checkbox.checked = isVisible;
    window.toggleColumn(columnId);
  });

  // Edit modal logic
  let editModal = document.getElementById('edit-application-modal');
  let editForm = document.getElementById('edit-application-form');
  window.openEditModal = function(jobId, title, company, location, jobType, closingDate, status) {
    document.getElementById('edit-job-id').value = jobId;
    document.getElementById('edit-title').value = title;
    document.getElementById('edit-company').value = company;
    document.getElementById('edit-location').value = location;
    document.getElementById('edit-job_type').value = jobType;
    document.getElementById('edit-closing_date').value = closingDate;
    document.getElementById('edit-status').value = status;
    editForm.action = `/update-application/${jobId}`;
    editModal.classList.remove('hidden');
  };
  window.closeEditModal = function() {
    editModal.classList.add('hidden');
  };
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

  // Delete confirmation modal
  let jobToDelete = null;
  window.confirmDeleteJob = function(id) {
    jobToDelete = id;
    document.getElementById('delete-confirm-modal').classList.remove('hidden');
    document.getElementById('confirm-delete-btn').focus();
  };
  document.getElementById('confirm-delete-btn').onclick = function() {
    if (jobToDelete) {
      window.deleteJob(jobToDelete);
      document.getElementById('delete-confirm-modal').classList.add('hidden');
      jobToDelete = null;
    }
  };
  document.getElementById('cancel-delete-btn').onclick = function() {
    document.getElementById('delete-confirm-modal').classList.add('hidden');
    jobToDelete = null;
  };
  document.getElementById('close-delete-modal').onclick = function() {
    document.getElementById('delete-confirm-modal').classList.add('hidden');
    jobToDelete = null;
  };
  window.addEventListener('keydown', function(e) {
    const modal = document.getElementById('delete-confirm-modal');
    if (!modal.classList.contains('hidden') && (e.key === 'Enter' || e.keyCode === 13)) {
      e.preventDefault();
      document.getElementById('confirm-delete-btn').click();
    }
  });

  // Job search filter
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
}); 