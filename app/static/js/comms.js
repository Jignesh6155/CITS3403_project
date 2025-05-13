/**
 * CareerLink Friends and Shared Applications
 * Common JavaScript for the comms page functionality
 */

document.addEventListener('DOMContentLoaded', function() {
  // Friend search functionality
  initFriendSearch();
  
  // Tab switching for shared applications
  initTabSwitching();
  
  // Share modal functionality
  initShareModal();
});

/**
 * Initialize the friend search functionality
 */
function initFriendSearch() {
  const friendSearchInput = document.getElementById('friend-search');
  if (!friendSearchInput) return;
  
  friendSearchInput.addEventListener('input', function() {
    const searchTerm = this.value.trim().toLowerCase();
    const friendItems = document.querySelectorAll('#friends-list .friend-item');
    const pendingItems = document.querySelectorAll('#pending-requests-list .friend-item');
    
    let friendsFound = false;
    let pendingFound = false;
    
    // Filter friends list
    friendItems.forEach(item => {
      const name = item.getAttribute('data-name');
      if (name.includes(searchTerm)) {
        item.style.display = '';
        friendsFound = true;
      } else {
        item.style.display = 'none';
      }
    });
    
    // Filter pending requests
    pendingItems.forEach(item => {
      const name = item.getAttribute('data-name');
      if (name.includes(searchTerm)) {
        item.style.display = '';
        pendingFound = true;
      } else {
        item.style.display = 'none';
      }
    });
    
    // Toggle "no results" messages
    const noFriendsMsg = document.getElementById('no-friends');
    const noPendingMsg = document.getElementById('no-pending-requests');
    
    if (noFriendsMsg) {
      noFriendsMsg.style.display = friendsFound ? 'none' : '';
      if (!friendsFound && searchTerm) {
        noFriendsMsg.textContent = 'No friends match your search';
      } else {
        noFriendsMsg.textContent = 'No friends yet';
      }
    }
    
    if (noPendingMsg) {
      noPendingMsg.style.display = pendingFound ? 'none' : '';
      if (!pendingFound && searchTerm) {
        noPendingMsg.textContent = 'No pending requests match your search';
      } else {
        noPendingMsg.textContent = 'No pending requests';
      }
    }
  });
}

/**
 * Initialize the tab switching functionality for shared applications
 */
function initTabSwitching() {
  // Initial tab setup on page load
  switchTab('active');
}

/**
 * Switch between active and archived shared applications tabs
 * @param {string} tabName - Tab to switch to ('active' or 'archived')
 */
function switchTab(tabName) {
  // Update tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('border-b-2', 'border-indigo-500', 'text-indigo-600', 'font-medium');
    btn.classList.add('text-gray-600', 'hover:text-gray-800');
  });
  
  document.getElementById(`${tabName}-tab`).classList.remove('text-gray-600', 'hover:text-gray-800');
  document.getElementById(`${tabName}-tab`).classList.add('border-b-2', 'border-indigo-500', 'text-indigo-600', 'font-medium');
  
  // Hide all tab content and show the selected one
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.add('hidden');
  });
  document.getElementById(`${tabName}-applications`).classList.remove('hidden');
  
  // Run filtering on the visible tab
  filterApplications();
}

/**
 * Filter applications based on search, job type, and friend
 */
function filterApplications() {
  const searchTerm = document.getElementById('job-search').value.toLowerCase();
  const jobTypeFilter = document.getElementById('job-type-filter').value.toLowerCase();
  const friendFilter = document.getElementById('friend-filter').value.toLowerCase();
  
  // Determine which tab is active
  const activeTabId = document.querySelector('.tab-btn.border-indigo-500').id.replace('-tab', '');
  const applicationsContainer = document.getElementById(`${activeTabId}-applications`);
  const applications = Array.from(applicationsContainer.querySelectorAll('.app-item'));
  
  // If no applications, exit early
  if (applications.length === 0) return;
  
  // Filter by search term, job type, and friend
  let filteredApps = applications.filter(app => {
    const jobTitle = app.getAttribute('data-title') || '';
    const jobType = app.getAttribute('data-job-type') || '';
    const friend = app.getAttribute('data-friend') || '';
    
    const matchesSearch = !searchTerm || jobTitle.includes(searchTerm);
    const matchesJobType = !jobTypeFilter || jobType.includes(jobTypeFilter);
    const matchesFriend = !friendFilter || friend === friendFilter;
    
    return matchesSearch && matchesJobType && matchesFriend;
  });
  
  // Hide all applications first
  applications.forEach(app => {
    app.classList.add('hidden');
  });
  
  // Show filtered applications
  filteredApps.forEach(app => {
    app.classList.remove('hidden');
  });
  
  // Show/hide empty message
  const emptyMessage = applicationsContainer.querySelector('.empty-message');
  if (emptyMessage) {
    if (filteredApps.length === 0) {
      emptyMessage.textContent = 'No applications match your filters.';
      emptyMessage.classList.remove('hidden');
    } else {
      emptyMessage.classList.add('hidden');
    }
  }
}

/**
 * Reset all filters and show all applications
 */
function resetFilters() {
  // Reset the search input
  const searchInput = document.getElementById('job-search');
  if (searchInput) searchInput.value = '';
  
  // Reset the job type dropdown
  const jobTypeFilter = document.getElementById('job-type-filter');
  if (jobTypeFilter) jobTypeFilter.selectedIndex = 0;
  
  // Reset the friend filter dropdown
  const friendFilter = document.getElementById('friend-filter');
  if (friendFilter) friendFilter.selectedIndex = 0;
  
  // Apply the reset filters
  filterApplications();
  
  // Visual feedback - briefly highlight the button
  const resetBtn = document.getElementById('reset-filters-btn');
  if (resetBtn) {
    resetBtn.classList.add('bg-indigo-100');
    setTimeout(() => {
      resetBtn.classList.remove('bg-indigo-100');
    }, 300);
  }
}

let currentAppId = null;

/**
 * Initialize share modal functionality
 */
function initShareModal() {
  // Share friends search functionality
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
      
      // Enable/disable the submit button based on whether any friends are visible
      const submitBtn = document.getElementById('share-submit-btn');
      submitBtn.disabled = !anyVisible;
      
      // If we have a "no friends" message, update it
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
  }
  
  // Click listener for friend items in the share modal
  const friendItems = document.querySelectorAll('.share-friend-item');
  friendItems.forEach(item => {
    item.addEventListener('click', function() {
      const radio = this.querySelector('input[type="radio"]');
      radio.checked = true;
      
      // Highlight the selected item
      document.querySelectorAll('.share-friend-item').forEach(el => {
        el.classList.remove('bg-indigo-50');
      });
      this.classList.add('bg-indigo-50');
    });
  });
  
  // Share form submission
  const shareForm = document.getElementById('shareForm');
  if (shareForm) {
    shareForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const friendId = this.querySelector('input[type="radio"]:checked')?.value;
      
      if (!friendId) {
        showToast('Please select a friend to share with', 'error');
        return;
      }
      
      fetch(`/share-application/${currentAppId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `friend_id=${friendId}`
      }).then(response => {
        if (response.redirected) {
          window.location.href = response.url;
        } else {
          closeShareModal();
          showToast('Application shared successfully!', 'success');
        }
      }).catch(error => {
        console.error('Error sharing application:', error);
        showToast('Failed to share application', 'error');
      });
    });
  }
}

/**
 * Open the share modal for a specific application
 * @param {string} appId - ID of the application to share
 */
function openShareModal(appId) {
  currentAppId = appId;
  document.getElementById('shareModal').classList.remove('hidden');
  
  // Clear any previous search
  const searchInput = document.getElementById('share-friend-search');
  if (searchInput) {
    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input'));
  }
  
  // Clear any previous selection
  document.querySelectorAll('.share-friend-item').forEach(el => {
    el.classList.remove('bg-indigo-50');
    el.querySelector('input[type="radio"]').checked = false;
  });
}

/**
 * Close the share modal
 */
function closeShareModal() {
  document.getElementById('shareModal').classList.add('hidden');
  currentAppId = null;
}

/**
 * Save a shared application to the user's tracker
 * @param {string} appId - ID of the application to save
 */
function saveApplication(appId) {
  const button = document.getElementById(`save-btn-${appId}`);
  button.disabled = true;
  button.textContent = 'Saving...';
  button.classList.add('opacity-75');

  fetch(`/save-shared-application/${appId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Move the item from active to archived tab
      const appItem = document.getElementById(`shared-app-${appId}`);
      const archivedList = document.getElementById('archived-applications');
      
      // Clone the app item for the archived section
      const archivedItem = appItem.cloneNode(true);
      
      // Remove the save button and add "Saved" label
      const buttonContainer = archivedItem.querySelector('.save-app-btn').parentNode;
      archivedItem.querySelector('.save-app-btn').remove();
      
      // Add saved indicator
      const savedIndicator = document.createElement('span');
      savedIndicator.className = 'inline-block mt-2 bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded';
      savedIndicator.textContent = 'Saved to your tracker';
      archivedItem.querySelector('div').appendChild(savedIndicator);
      
      // Add to archived list
      archivedList.appendChild(archivedItem);
      
      // Remove from active list
      appItem.remove();
      
      // Check if active list is empty
      const activeList = document.getElementById('active-applications');
      if (activeList.querySelectorAll('.app-item').length === 0) {
        const emptyMessage = document.createElement('li');
        emptyMessage.className = 'empty-message text-gray-400 text-center py-4';
        emptyMessage.textContent = 'No active shared applications.';
        activeList.appendChild(emptyMessage);
      }
      
      // Show toast
      showToast('Application saved to your tracker!', 'success');
      
      // Reapply filters
      filterApplications();
    } else {
      throw new Error(data.error || 'Failed to save application');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    button.disabled = false;
    button.textContent = 'Save to Tracker';
    button.classList.remove('opacity-75');
    showToast(error.message || 'Failed to save application', 'error');
  });
}

/**
 * Display a toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of toast ('success' or 'error')
 */
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg text-white ${type === 'success' ? 'bg-green-500' : 'bg-red-500'} transition-opacity duration-300`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}