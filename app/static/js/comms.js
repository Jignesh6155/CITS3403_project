/**
 * CareerLink Friends and Shared Applications
 * Common JavaScript for the comms page functionality
 * Enhanced with alphabetical indexing, pagination, and favorites for friends list
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize enhanced friends list with alphabetical indexing and pagination
  initEnhancedFriendsList();
  
  // Tab switching for shared applications
  initTabSwitching();
  
  // Share modal functionality
  initShareModal();
  
  // Initialize favorite functionality
  initFavoriteFunctionality();
});

/**
 * Initialize favorite functionality
 */
/**
 * Updated initFavoriteFunctionality function with better error handling
 * Add this to your comms.js file or replace the existing function
 */
function initFavoriteFunctionality() {
  console.log("Initializing favorite functionality");
  
  // Count buttons for debugging
  const favoriteButtons = document.querySelectorAll('.favorite-btn');
  console.log(`Found ${favoriteButtons.length} favorite buttons`);
  
  // Setup favorite star buttons with more robust click handling
  favoriteButtons.forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log("Star clicked!");
      
      const friendId = this.getAttribute('data-friend-id');
      console.log(`Friend ID: ${friendId}`);
      
      const starIcon = this.querySelector('svg');
      const isFavorite = this.getAttribute('data-is-favorite') === '1';
      console.log(`Current favorite status: ${isFavorite ? 'true' : 'false'}`);
      
      // Optimistic UI update
      if (isFavorite) {
        starIcon.classList.remove('text-yellow-500', 'fill-yellow-500');
        this.setAttribute('data-is-favorite', '0');
      } else {
        starIcon.classList.add('text-yellow-500', 'fill-yellow-500');
        this.setAttribute('data-is-favorite', '1');
      }
      
      // Update parent item's data attribute
      const friendItem = this.closest('.friend-item');
      if (friendItem) {
        friendItem.setAttribute('data-is-favorite', isFavorite ? '0' : '1');
      }
      
      // Update favorite status on server
      fetch(`/toggle-favorite/${friendId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      .then(response => {
        console.log("Server response status:", response.status);
        return response.json();
      })
      .then(data => {
        console.log("Server response data:", data);
        
        if (!data.success) {
          // Revert UI change if the server request failed
          console.error('Failed to toggle favorite status:', data.error);
          if (isFavorite) {
            starIcon.classList.add('text-yellow-500', 'fill-yellow-500');
            this.setAttribute('data-is-favorite', '1');
            if (friendItem) friendItem.setAttribute('data-is-favorite', '1');
          } else {
            starIcon.classList.remove('text-yellow-500', 'fill-yellow-500');
            this.setAttribute('data-is-favorite', '0');
            if (friendItem) friendItem.setAttribute('data-is-favorite', '0');
          }
        } else {
          // Store favorites in localStorage for faster filtering
          const friendName = friendItem ? friendItem.getAttribute('data-name') : '';
          
          let favorites = JSON.parse(localStorage.getItem('favoriteFriends') || '{}');
          if (!isFavorite) { // It's now a favorite
            favorites[friendId] = friendName;
          } else {
            delete favorites[friendId];
          }
          
          localStorage.setItem('favoriteFriends', JSON.stringify(favorites));
          
          // Re-apply filters to reflect changes
          if (typeof filterFriends === 'function') {
            filterFriends();
          } else {
            console.error("filterFriends function is not defined");
          }
        }
      })
      .catch(error => {
        console.error('Error toggling favorite status:', error);
        // Revert UI change on error
        if (isFavorite) {
          starIcon.classList.add('text-yellow-500', 'fill-yellow-500');
          this.setAttribute('data-is-favorite', '1');
          if (friendItem) friendItem.setAttribute('data-is-favorite', '1');
        } else {
          starIcon.classList.remove('text-yellow-500', 'fill-yellow-500');
          this.setAttribute('data-is-favorite', '0');
          if (friendItem) friendItem.setAttribute('data-is-favorite', '0');
        }
      });
    });
  });
}

/**
 * Initialize the enhanced friends list with alphabetical indexing and pagination
 */
function initEnhancedFriendsList() {
  // Get elements
  const friendsList = document.getElementById('friends-list');
  const searchInput = document.getElementById('friend-search');
  const alphabetButtons = document.querySelectorAll('.alphabet-filter');
  const filterOptions = document.querySelectorAll('.filter-option');
  const prevPageBtn = document.getElementById('prev-page');
  const nextPageBtn = document.getElementById('next-page');
  const pageIndicator = document.getElementById('page-indicator');
  const friendsPerPageSelect = document.getElementById('friends-per-page');
  const friendsCountDisplay = document.getElementById('friends-count');
  const noFriendsMessage = document.getElementById('no-friends');
  
  // If elements don't exist, exit early
  if (!friendsList || !alphabetButtons.length) return;
  
  // Variables to track state
  let currentPage = 1;
  let itemsPerPage = parseInt(friendsPerPageSelect.value);
  let currentLetter = 'all';
  let currentFilter = 'all';
  let searchTerm = '';
  
  // Get all friend items
  const allFriends = Array.from(friendsList.querySelectorAll('.friend-item'));
  
  // Load favorites from localStorage for initial state
  const favorites = JSON.parse(localStorage.getItem('favoriteFriends') || '{}');
  allFriends.forEach(friend => {
    const friendId = friend.querySelector('.favorite-btn')?.getAttribute('data-friend-id');
    if (friendId && favorites[friendId]) {
      friend.setAttribute('data-is-favorite', '1');
      const starIcon = friend.querySelector('.favorite-btn svg');
      if (starIcon) {
        starIcon.classList.add('text-yellow-500', 'fill-yellow-500');
      }
      friend.querySelector('.favorite-btn')?.setAttribute('data-is-favorite', '1');
    }
  });
  
  // Function to filter friends
  function filterFriends() {
    let filteredFriends = allFriends;
    
    // Apply letter filter
    if (currentLetter !== 'all') {
      filteredFriends = filteredFriends.filter(friend => {
        return friend.getAttribute('data-first-letter') === currentLetter;
      });
    }
    
    // Apply search filter
    if (searchTerm) {
      filteredFriends = filteredFriends.filter(friend => {
        const name = friend.getAttribute('data-name');
        return name.includes(searchTerm.toLowerCase());
      });
    }
    
    // Apply special filters (favorites, recent, most shared)
    if (currentFilter !== 'all') {
      if (currentFilter === 'favourites') {
        filteredFriends = filteredFriends.filter(friend => {
          return friend.getAttribute('data-is-favorite') === '1';
        });
      } else if (currentFilter === 'shared') {
  // Filter out friends with zero shared applications
  filteredFriends = filteredFriends.filter(friend => {
    const count = parseInt(friend.getAttribute('data-shared-count') || '0');
    return count > 0; // Only include friends with at least 1 shared application
  });
  
  // Then sort the remaining friends by shared count (most first)
  filteredFriends.sort((a, b) => {
    const countA = parseInt(a.getAttribute('data-shared-count') || '0');
    const countB = parseInt(b.getAttribute('data-shared-count') || '0');
    return countB - countA; // Descending order
  });
  
  // Remove any existing badges first
  document.querySelectorAll('.shared-count-badge').forEach(badge => badge.remove());
  
  // Add count badges to show how many apps each friend has shared
  filteredFriends.forEach(friend => {
    const countBadge = document.createElement('span');
    const count = friend.getAttribute('data-shared-count') || '0';
    countBadge.className = 'inline-block bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full ml-1 shared-count-badge';
    countBadge.textContent = `${count} shared`;
    
    // Find the name element and add the badge after it
    const nameElement = friend.querySelector('.font-medium');
    if (nameElement) {
      nameElement.appendChild(countBadge);
    }
  });
}
    }
    
    // Display total count
    updateFriendsCount(filteredFriends.length);
    
    // Paginate the results
    paginateFriends(filteredFriends);
    
    // Show/hide no friends message
    if (filteredFriends.length === 0) {
      if (noFriendsMessage) {
        noFriendsMessage.style.display = '';
        noFriendsMessage.textContent = searchTerm 
          ? 'No friends match your search' 
          : (currentLetter !== 'all' 
              ? `No friends starting with "${currentLetter}"` 
              : (currentFilter === 'favourites'
                  ? 'No favorite friends yet'
                  : (currentFilter === 'recent'
                      ? 'No recent friends'
                      : (currentFilter === 'shared'
                          ? 'No shared applications yet'
                          : 'No friends yet'))));
      }
    } else if (noFriendsMessage) {
      noFriendsMessage.style.display = 'none';
    }
  }
  
  // Function to paginate friends

function paginateFriends(friends) {
  // Hide all friends first
  allFriends.forEach(friend => {
    friend.style.display = 'none';
  });
  
  // Calculate pagination
  const totalPages = Math.ceil(friends.length / itemsPerPage);
  
  // Adjust current page if needed
  if (currentPage > totalPages) {
    currentPage = Math.max(1, totalPages);
  }
  
  // Update page indicator
  pageIndicator.textContent = totalPages > 0 
    ? `Page ${currentPage} of ${totalPages}` 
    : 'Page 1';
  
  // Update pagination buttons
  prevPageBtn.disabled = currentPage <= 1;
  nextPageBtn.disabled = currentPage >= totalPages;
  
  // Show current page
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, friends.length);
  
  // Important: When we're using the 'shared' filter, maintain the sorted order
  // by showing the friends in the order they appear in the filteredFriends array
  for (let i = startIndex; i < endIndex; i++) {
    friends[i].style.display = '';
  }
}
  
  // Function to update the friends count display
  function updateFriendsCount(count) {
    const total = allFriends.length;
    
    if (count === total) {
      friendsCountDisplay.textContent = `Showing all ${total} friend${total !== 1 ? 's' : ''}`;
    } else {
      friendsCountDisplay.textContent = `Showing ${count} of ${total} friend${total !== 1 ? 's' : ''}`;
    }
  }
  
  // Event listeners for alphabet filter
  alphabetButtons.forEach(button => {
    button.addEventListener('click', function() {
      // Update active state
      alphabetButtons.forEach(btn => btn.classList.remove('active', 'bg-indigo-100', 'text-indigo-800'));
      alphabetButtons.forEach(btn => btn.classList.add('bg-gray-100', 'text-gray-800'));
      this.classList.remove('bg-gray-100', 'text-gray-800');
      this.classList.add('active', 'bg-indigo-100', 'text-indigo-800');
      
      // Update current letter
      currentLetter = this.getAttribute('data-letter');
      
      // Reset to first page
      currentPage = 1;
      
      // Apply filters
      filterFriends();
    });
  });
  
  // Event listeners for filter options
  if (filterOptions) {
    filterOptions.forEach(option => {
      option.addEventListener('click', function() {
        // Update active state
        filterOptions.forEach(opt => opt.classList.remove('active', 'bg-indigo-100', 'text-indigo-800'));
        filterOptions.forEach(opt => opt.classList.add('bg-gray-100', 'text-gray-700'));
        this.classList.remove('bg-gray-100', 'text-gray-700');
        this.classList.add('active', 'bg-indigo-100', 'text-indigo-800');
        
        // Update current filter
        currentFilter = this.getAttribute('data-filter');
        
        // Reset to first page
        currentPage = 1;
        
        // Apply filters
        filterFriends();
      });
    });
  }
  
  // Event listener for search
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      searchTerm = this.value.trim();
      currentPage = 1; // Reset to first page when search changes
      filterFriends();
      
      // Also filter pending requests
      filterPendingRequests(searchTerm);
    });
  }
  
  // Event listeners for pagination
  prevPageBtn.addEventListener('click', function() {
    if (currentPage > 1) {
      currentPage--;
      filterFriends();
    }
  });
  
  nextPageBtn.addEventListener('click', function() {
    const filteredFriends = getFilteredFriends();
    const totalPages = Math.ceil(filteredFriends.length / itemsPerPage);
    
    if (currentPage < totalPages) {
      currentPage++;
      filterFriends();
    }
  });
  
  // Event listener for items per page
  friendsPerPageSelect.addEventListener('change', function() {
    itemsPerPage = parseInt(this.value);
    currentPage = 1; // Reset to first page when changing items per page
    filterFriends();
  });
  
  // Helper function to get currently filtered friends
  function getFilteredFriends() {
    let filteredFriends = allFriends;
    
    // Apply letter filter
    if (currentLetter !== 'all') {
      filteredFriends = filteredFriends.filter(friend => {
        return friend.getAttribute('data-first-letter') === currentLetter;
      });
    }
    
    // Apply search filter
    if (searchTerm) {
      filteredFriends = filteredFriends.filter(friend => {
        const name = friend.getAttribute('data-name');
        return name.includes(searchTerm.toLowerCase());
      });
    }
    
    // Apply special filters (favorites, recent, most shared)
    if (currentFilter !== 'all') {
      if (currentFilter === 'favourites') {
        filteredFriends = filteredFriends.filter(friend => {
          return friend.getAttribute('data-is-favorite') === '1';
        });
      } else if (currentFilter === 'recent') {
        // Sort by most recent first
        filteredFriends.sort((a, b) => {
          const dateA = a.getAttribute('data-last-updated') || '0';
          const dateB = b.getAttribute('data-last-updated') || '0';
          return dateB.localeCompare(dateA);
        });
      } else if (currentFilter === 'shared') {
        // Sort by shared apps count
        filteredFriends.sort((a, b) => {
          const countA = parseInt(a.getAttribute('data-shared-count') || '0');
          const countB = parseInt(b.getAttribute('data-shared-count') || '0');
          return countB - countA;
        });
      }
    }
    
    return filteredFriends;
  }
  
  // Initialize the view
  filterFriends();
}

/**
 * Filter pending requests based on search term
 */
function filterPendingRequests(searchTerm) {
  const pendingItems = document.querySelectorAll('#pending-requests-list .friend-item');
  if (!pendingItems.length) return;
  
  let pendingFound = false;
  
  // Filter pending requests
  pendingItems.forEach(item => {
    const name = item.getAttribute('data-name');
    if (name.includes(searchTerm.toLowerCase())) {
      item.style.display = '';
      pendingFound = true;
    } else {
      item.style.display = 'none';
    }
  });
  
  // Toggle "no results" message
  const noPendingMsg = document.getElementById('no-pending-requests');
  
  if (noPendingMsg) {
    noPendingMsg.style.display = pendingFound ? 'none' : '';
    if (!pendingFound && searchTerm) {
      noPendingMsg.textContent = 'No pending requests match your search';
    } else {
      noPendingMsg.textContent = 'No pending requests';
    }
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
  const searchTerm = document.getElementById('job-search')?.value.toLowerCase() || '';
  const jobTypeFilter = document.getElementById('job-type-filter')?.value.toLowerCase() || '';
  const friendFilter = document.getElementById('friend-filter')?.value.toLowerCase() || '';
  
  // Determine which tab is active
  const activeTabId = document.querySelector('.tab-btn.border-indigo-500')?.id.replace('-tab', '') || 'active';
  const applicationsContainer = document.getElementById(`${activeTabId}-applications`);
  if (!applicationsContainer) return;
  
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
      if (submitBtn) submitBtn.disabled = !anyVisible;
      
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
      if (radio) radio.checked = true;
      
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
  const shareModal = document.getElementById('shareModal');
  if (shareModal) shareModal.classList.remove('hidden');
  
  // Clear any previous search
  const searchInput = document.getElementById('share-friend-search');
  if (searchInput) {
    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input'));
  }
  
  // Clear any previous selection
  document.querySelectorAll('.share-friend-item').forEach(el => {
    el.classList.remove('bg-indigo-50');
    const radio = el.querySelector('input[type="radio"]');
    if (radio) radio.checked = false;
  });
}

/**
 * Close the share modal
 */
function closeShareModal() {
  const shareModal = document.getElementById('shareModal');
  if (shareModal) shareModal.classList.add('hidden');
  currentAppId = null;
}

/**
 * Save a shared application to the user's tracker
 * @param {string} appId - ID of the application to save
 */
function saveApplication(appId) {
  const button = document.getElementById(`save-btn-${appId}`);
  if (!button) return;
  
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
      if (!appItem) return;
      
      const archivedList = document.getElementById('archived-applications');
      if (!archivedList) return;
      
      // Clone the app item for the archived section
      const archivedItem = appItem.cloneNode(true);
      
      // Remove the save button and add "Saved" label
      const saveButton = archivedItem.querySelector('.save-app-btn');
      if (saveButton) saveButton.remove();
      
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
      if (activeList && activeList.querySelectorAll('.app-item').length === 0) {
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
    if (button) {
      button.disabled = false;
      button.textContent = 'Save to Tracker';
      button.classList.remove('opacity-75');
    }
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