/**
 * Updated JavaScript for the Friends List Component
 * Adds collapsible filter section functionality
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize filter toggle functionality
  initFilterToggle();
  
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
 * Initialize collapsible filter section functionality
 */
function initFilterToggle() {
  const filterToggle = document.getElementById('filter-toggle');
  const filterContent = document.getElementById('filter-content');
  const filterChevron = document.getElementById('filter-chevron');
  
  if (!filterToggle || !filterContent || !filterChevron) return;
  
  // Set initial state - expanded by default
  let expanded = true;
  
  filterToggle.addEventListener('click', function() {
    expanded = !expanded;
    
    if (expanded) {
      // Expand the filter content
      filterContent.style.maxHeight = '500px';
      filterChevron.classList.remove('rotate-180');
    } else {
      // Collapse the filter content
      filterContent.style.maxHeight = '0px';
      filterChevron.classList.add('rotate-180');
    }
  });
}

/**
 * Initialize favorite functionality
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
    
    // Always remove any existing shared count badges
    document.querySelectorAll('.shared-count-badge').forEach(badge => badge.remove());
    
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
        
        // Add count badges ONLY in shared filter mode
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
      } else if (currentFilter === 'recent') {
        // Sort by most recent first
        filteredFriends.sort((a, b) => {
          const dateA = a.getAttribute('data-last-updated') || '0';
          const dateB = b.getAttribute('data-last-updated') || '0';
          return dateB.localeCompare(dateA);
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
  
  // Make filterFriends function available globally
  window.filterFriends = filterFriends;
  
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
            
            // Filter out friends with zero shared applications
            filteredFriends = filteredFriends.filter(friend => {
              const count = parseInt(friend.getAttribute('data-shared-count') || '0');
              return count > 0; // Only include friends with at least 1 shared application
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

// Make the key functions available globally
window.filterFriends = filterFriends;
window.filterPendingRequests = filterPendingRequests;
window.switchTab = switchTab;

// --- SHARED APPLICATIONS: IMPLEMENTED FUNCTIONS ---
function filterApplications() {
  // Get filter values
  const search = document.getElementById('job-search')?.value.trim().toLowerCase() || '';
  const jobType = document.getElementById('job-type-filter')?.value.trim().toLowerCase() || '';
  const friend = document.getElementById('friend-filter')?.value.trim().toLowerCase() || '';

  // Filter both active and archived lists
  ['active-applications', 'archived-applications'].forEach(listId => {
    const appList = document.querySelector(`#${listId} ul`);
    if (!appList) return;
    appList.querySelectorAll('.app-item').forEach(item => {
      const title = item.getAttribute('data-title') || '';
      const type = item.getAttribute('data-job-type') || '';
      const sharedBy = item.getAttribute('data-friend') || '';
      const matches =
        (search === '' || title.includes(search)) &&
        (jobType === '' || type === jobType) &&
        (friend === '' || sharedBy === friend);
      item.style.display = matches ? '' : 'none';
    });
  });
}

function saveApplication(appId) {
  const btn = document.getElementById(`save-btn-${appId}`);
  if (!btn) return;
  btn.disabled = true;
  btn.innerHTML = '<span class="loader mr-2"></span>Saving...';

  fetch(`/save-shared-application/${appId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>Saved to your tracker';
        btn.classList.remove('bg-gradient-to-r', 'from-green-500', 'to-emerald-600', 'hover:from-green-600', 'hover:to-emerald-700');
        btn.classList.add('bg-gray-100', 'text-gray-600', 'cursor-not-allowed');
      } else {
        btn.disabled = false;
        btn.innerHTML = 'Save to Tracker';
        alert(data.error || 'Failed to save application.');
      }
    })
    .catch(() => {
      btn.disabled = false;
      btn.innerHTML = 'Save to Tracker';
      alert('Failed to save application. Please try again.');
    });
}

window.filterApplications = filterApplications;
window.saveApplication = saveApplication;
