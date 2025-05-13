/**
 * CareerLink Friends and Shared Applications
 * Common JavaScript for the comms page functionality
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all components
  initFriendSearch();
  initAlphabeticalIndex();
  initPagination();
  initFavoriteButtons();
  initTabSwitching();
  initShareModal();
});

// Constants for pagination
const ITEMS_PER_PAGE = 10;
let currentPage = 1;
let filteredFriends = [];

/**
 * Initialize the friend search functionality
 */
function initFriendSearch() {
  const searchInput = document.getElementById('friend-search');
  if (!searchInput) return;
  
  searchInput.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    filterFriends(searchTerm);
  });
}

/**
 * Initialize alphabetical index functionality
 */
function initAlphabeticalIndex() {
  const letterButtons = document.querySelectorAll('#alphabet-index button');
  if (!letterButtons.length) return;
  
  letterButtons.forEach(button => {
    button.addEventListener('click', () => {
      const letter = button.getAttribute('data-letter');
      filterFriendsByLetter(letter);
    });
  });
}

/**
 * Filter friends based on search term
 */
function filterFriends(searchTerm) {
  const friendItems = document.querySelectorAll('#friends-list .friend-item');
  filteredFriends = Array.from(friendItems).filter(item => {
    const name = item.getAttribute('data-name');
    return name.includes(searchTerm);
  });
  
  currentPage = 1;
  updatePagination();
}

/**
 * Filter friends by letter
 */
function filterFriendsByLetter(letter) {
  const friendItems = document.querySelectorAll('#friends-list .friend-item');
  filteredFriends = Array.from(friendItems).filter(item => {
    if (letter === 'all') return true;
    const firstLetter = item.getAttribute('data-first-letter');
    return firstLetter === letter;
  });
  
  currentPage = 1;
  updatePagination();
  
  // Update active state of letter buttons
  document.querySelectorAll('#alphabet-index button').forEach(btn => {
    btn.classList.remove('bg-indigo-100', 'text-indigo-700');
    if (btn.getAttribute('data-letter') === letter) {
      btn.classList.add('bg-indigo-100', 'text-indigo-700');
    }
  });
}

/**
 * Initialize pagination functionality
 */
function initPagination() {
  const prevButton = document.getElementById('prev-page');
  const nextButton = document.getElementById('next-page');
  const pageInfo = document.getElementById('page-info');
  const friendsList = document.getElementById('friends-list');
  const paginationContainer = document.getElementById('pagination-container');
  
  if (!prevButton || !nextButton || !pageInfo || !friendsList || !paginationContainer) return;
  
  prevButton.addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      updatePagination();
    }
  });
  
  nextButton.addEventListener('click', () => {
    const maxPages = Math.ceil(filteredFriends.length / ITEMS_PER_PAGE);
    if (currentPage < maxPages) {
      currentPage++;
      updatePagination();
    }
  });
  
  // Initialize with all friends
  filteredFriends = Array.from(document.querySelectorAll('#friends-list .friend-item'));
  updatePagination();
}

/**
 * Initialize favorite buttons functionality
 */
function initFavoriteButtons() {
  document.querySelectorAll('.favorite-btn').forEach(button => {
    button.addEventListener('click', function(e) {
      e.stopPropagation();
      const friendItem = this.closest('.friend-item');
      const isFavorite = friendItem.getAttribute('data-category') === 'favorites';
      
      if (isFavorite) {
        friendItem.setAttribute('data-category', 'all');
        this.querySelector('i').classList.remove('text-yellow-500');
      } else {
        friendItem.setAttribute('data-category', 'favorites');
        this.querySelector('i').classList.add('text-yellow-500');
      }
      
      // Update category filter if it's active
      const categorySelect = document.getElementById('friend-category');
      if (categorySelect.value === 'favorites') {
        filterFriendsByCategory('favorites');
      }
    });
  });
}

/**
 * Filter friends by category
 */
function filterFriendsByCategory(category) {
  const friendItems = document.querySelectorAll('#friends-list .friend-item');
  filteredFriends = Array.from(friendItems).filter(item => {
    if (category === 'all') return true;
    const itemCategory = item.getAttribute('data-category');
    return itemCategory === category;
  });
  
  currentPage = 1;
  updatePagination();
}

/**
 * Update pagination UI and display
 */
function updatePagination() {
  const prevButton = document.getElementById('prev-page');
  const nextButton = document.getElementById('next-page');
  const pageInfo = document.getElementById('page-info');
  const friendsList = document.getElementById('friends-list');
  const paginationContainer = document.getElementById('pagination-container');
  
  if (!prevButton || !nextButton || !pageInfo || !friendsList || !paginationContainer) return;
  
  const maxPages = Math.ceil(filteredFriends.length / ITEMS_PER_PAGE);
  
  // Hide pagination if no results
  if (filteredFriends.length === 0) {
    paginationContainer.style.display = 'none';
    pageInfo.textContent = '';
    
    // Hide all friend items
    document.querySelectorAll('#friends-list .friend-item').forEach(item => {
      item.style.display = 'none';
    });
    
    // Show no results message
    const noFriendsMsg = document.getElementById('no-friends');
    if (noFriendsMsg) {
      noFriendsMsg.innerHTML = `
        <i data-lucide="users" class="w-8 h-8 mx-auto mb-2 text-gray-300"></i>
        <p>No friends found</p>
        <p class="text-sm mt-1">Try a different letter or search</p>
      `;
      noFriendsMsg.style.display = '';
      // Reinitialize Lucide icons
      lucide.createIcons();
    }
    return;
  }
  
  // Show pagination if there are results
  paginationContainer.style.display = 'flex';
  
  const start = (currentPage - 1) * ITEMS_PER_PAGE;
  const end = start + ITEMS_PER_PAGE;
  
  // Update pagination controls
  prevButton.disabled = currentPage === 1;
  nextButton.disabled = currentPage === maxPages;
  pageInfo.textContent = `Page ${currentPage} of ${maxPages}`;
  
  // Hide all friends first
  document.querySelectorAll('#friends-list .friend-item').forEach(item => {
    item.style.display = 'none';
  });
  
  // Show current page items
  filteredFriends.slice(start, end).forEach(item => {
    item.style.display = '';
  });
  
  // Hide no results message if we have results
  const noFriendsMsg = document.getElementById('no-friends');
  if (noFriendsMsg) {
    noFriendsMsg.style.display = 'none';
  }
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