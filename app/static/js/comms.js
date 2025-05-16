/**
 * Updated JavaScript for the Friends List Component
 * Adds collapsible filter section functionality
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize filter toggle functionality
  initFilterToggle();
  
  // Initialize enhanced friends list with alphabetical indexing and pagination
  initEnhancedFriendsList();
  
  // Initialize favorite functionality
  initFavoriteFunctionality();
  
  // Tab switching for shared applications
  initTabSwitching();
  
  // Share modal functionality
  initShareModal();
});

/**
 * Initialize collapsible filter section functionality
 */
function initFilterToggle() {
  const filterToggle = document.getElementById('filter-toggle');
  const filterContent = document.getElementById('filter-content');
  const filterChevron = document.getElementById('filter-chevron');
  
  if (!filterToggle || !filterContent || !filterChevron) return;
  
  // Set initial state - collapsed by default
  let expanded = false;
  filterContent.style.maxHeight = '0px';
  filterChevron.classList.add('rotate-180');
  
  filterToggle.addEventListener('click', function() {
    expanded = !expanded;
    
    if (expanded) {
      // Expand the filter content
      filterContent.style.maxHeight = 'none'; // Let content determine height
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
  
  // Get all the favorite buttons
  const favoriteButtons = document.querySelectorAll('.favorite-btn');
  console.log(`Found ${favoriteButtons.length} favorite buttons`);
  
  // Load favorites from localStorage
  let favorites = JSON.parse(localStorage.getItem('favoriteFriends') || '{}');
  
  // Set up each button
  favoriteButtons.forEach(btn => {
    const friendId = btn.getAttribute('data-friend-id');
    const starIcon = btn.querySelector('.star-icon');
    
    // Set initial state based on localStorage
    if (favorites[friendId]) {
      btn.classList.add('is-favorite');
      btn.setAttribute('data-is-favorite', '1');
      starIcon.classList.add('text-yellow-500', 'fill-yellow-500');
      
      // Also set on parent item
      const friendItem = btn.closest('.friend-item');
      if (friendItem) {
        friendItem.setAttribute('data-is-favorite', '1');
      }
    } else {
      starIcon.classList.add('text-gray-400');
    }
    
    // Add click handler
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log("Star clicked for friend ID:", friendId);
      
      // Check current state
      const isFavorite = btn.classList.contains('is-favorite');
      console.log("Current state - is favorite:", isFavorite);
      
      // Toggle state
      if (isFavorite) {
        // Remove favorite
        btn.classList.remove('is-favorite');
        btn.setAttribute('data-is-favorite', '0');
        starIcon.classList.remove('text-yellow-500', 'fill-yellow-500');
        starIcon.classList.add('text-gray-400');
        
        // Update parent item
        const friendItem = btn.closest('.friend-item');
        if (friendItem) {
          friendItem.setAttribute('data-is-favorite', '0');
        }
        
        // Remove from localStorage
        delete favorites[friendId];
      } else {
        // Add favorite
        btn.classList.add('is-favorite');
        btn.setAttribute('data-is-favorite', '1');
        starIcon.classList.remove('text-gray-400');
        starIcon.classList.add('text-yellow-500', 'fill-yellow-500');
        
        // Update parent item
        const friendItem = btn.closest('.friend-item');
        if (friendItem) {
          friendItem.setAttribute('data-is-favorite', '1');
          favorites[friendId] = friendItem.getAttribute('data-name') || '';
        }
      }
      
      // Save to localStorage
      localStorage.setItem('favoriteFriends', JSON.stringify(favorites));
      console.log("Updated favorites:", favorites);
      
      // Re-apply filters if we're on the favorites filter
      if (window.currentFilter === 'favourites') {
        filterFriends();
      }
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
    
    // Apply special filters (favorites, shared)
    if (currentFilter !== 'all') {
      if (currentFilter === 'favourites') {
        filteredFriends = filteredFriends.filter(friend => {
          const friendId = friend.querySelector('.favorite-btn')?.getAttribute('data-friend-id');
          const favorites = JSON.parse(localStorage.getItem('favoriteFriends') || '{}');
          return favorites[friendId];
        });
      } else if (currentFilter === 'shared') {
        // Filter out friends with zero shared applications
        filteredFriends = filteredFriends.filter(friend => {
          const count = parseInt(friend.getAttribute('data-shared-count') || '0');
          return count > 0;
        });
        
        // Sort by shared count (most first)
        filteredFriends.sort((a, b) => {
          const countA = parseInt(a.getAttribute('data-shared-count') || '0');
          const countB = parseInt(b.getAttribute('data-shared-count') || '0');
          return countB - countA;
        });
        
        // Add count badges
        filteredFriends.forEach(friend => {
          const countBadge = document.createElement('span');
          const count = friend.getAttribute('data-shared-count') || '0';
          countBadge.className = 'inline-block bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full ml-1 shared-count-badge';
          countBadge.textContent = `${count} shared`;
          
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
                  : (currentFilter === 'shared'
                      ? 'No shared applications yet'
                      : 'No friends yet')));
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
    
    // Apply special filters (favorites, shared)
    if (currentFilter !== 'all') {
      if (currentFilter === 'favourites') {
        filteredFriends = filteredFriends.filter(friend => {
          return friend.getAttribute('data-is-favorite') === '1';
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
  // Hide all tab contents
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.add('hidden');
  });
  
  // Remove active state from all tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('bg-white', 'text-blue-700', 'font-medium', 'shadow-sm');
    btn.classList.add('text-gray-700', 'hover:bg-gray-50');
  });
  
  // Show selected tab content
  const selectedContent = document.getElementById(`${tabName}-applications`);
  if (selectedContent) {
    selectedContent.classList.remove('hidden');
  }
  
  // Set active state on selected tab
  const selectedTab = document.getElementById(`${tabName}-tab`);
  if (selectedTab) {
    selectedTab.classList.remove('text-gray-700', 'hover:bg-gray-50');
    selectedTab.classList.add('bg-white', 'text-blue-700', 'font-medium', 'shadow-sm');
  }
  
  // Re-apply filters to the newly visible tab
  filterApplications();
}

// Make the key functions available globally
window.filterFriends = filterFriends;
window.filterPendingRequests = filterPendingRequests;
window.switchTab = switchTab;

// --- SHARED APPLICATIONS: IMPLEMENTED FUNCTIONS ---
function filterApplications() {
  console.log("Filtering applications...");
  
  // Get filter values
  const search = document.getElementById('job-search')?.value.trim().toLowerCase() || '';
  const jobType = document.getElementById('job-type-filter')?.value || '';
  const friend = document.getElementById('friend-filter')?.value.trim().toLowerCase() || '';
  
  console.log(`Filter values - search: "${search}", jobType: "${jobType}", friend: "${friend}"`);

  // Filter both active and archived lists
  ['active-applications', 'archived-applications'].forEach(listId => {
    const appList = document.querySelector(`#${listId} ul`);
    if (!appList) return;
    
    let visibleCount = 0;
    appList.querySelectorAll('.app-item').forEach(item => {
      // Get attribute values and log them for debugging
      const title = item.getAttribute('data-title') || '';
      const type = (item.getAttribute('data-job-type') || '').toLowerCase();
      const sharedBy = item.getAttribute('data-friend') || '';
      
      console.log(`Item - title: "${title}", type: "${type}", sharedBy: "${sharedBy}"`);
      
      // Improved matching logic with case-insensitive comparison for job type
      const jobTypeMatch = !jobType || 
                           type.includes(jobType.toLowerCase()) || 
                           jobType.toLowerCase().includes(type);
      
      const matches =
        (search === '' || title.includes(search)) &&
        jobTypeMatch &&
        (friend === '' || sharedBy.includes(friend));
      
      item.style.display = matches ? '' : 'none';
      if (matches) visibleCount++;
    });
    
    console.log(`${listId} - visible items: ${visibleCount}`);
    
    // Show/hide empty message based on results
    const emptyMessage = document.querySelector(`#${listId} .empty-message`);
    if (emptyMessage) {
      emptyMessage.style.display = visibleCount === 0 ? '' : 'none';
    }
  });
}

function saveApplication(appId) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
  
  fetch(`/save-shared-application/${appId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Move the application to archived tab
      const appElement = document.getElementById(`shared-app-${appId}`);
      if (appElement) {
        const archivedList = document.querySelector('#archived-applications ul');
        if (archivedList) {
          archivedList.appendChild(appElement);
        }
      }
      
      // Show success message
      const saveBtn = document.getElementById(`save-btn-${appId}`);
      if (saveBtn) {
        saveBtn.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          Saved
        `;
        saveBtn.disabled = true;
        saveBtn.classList.remove('from-green-500', 'to-emerald-600', 'hover:from-green-600', 'hover:to-emerald-700');
        saveBtn.classList.add('bg-gray-100', 'text-gray-600', 'cursor-default');
      }
      
      // Re-apply filters
      filterApplications();
    } else {
      alert(data.error || 'Failed to save application');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Failed to save application. Please try again.');
  });
}

function resetFilters() {
  // Reset the search input
  const searchInput = document.getElementById('job-search');
  if (searchInput) searchInput.value = '';
  
  // Reset the filter dropdowns
  const typeFilter = document.getElementById('job-type-filter');
  if (typeFilter) typeFilter.value = '';
  
  const friendFilter = document.getElementById('friend-filter');
  if (friendFilter) friendFilter.value = '';
  
  // Apply the reset filters
  filterApplications();
}

// Add this at the end of your comms.js file
console.log("===== COMMS.JS LOADED =====");
// Debug helper - can be called from browser console
window.debugFavorites = function() {
  const favoriteButtons = document.querySelectorAll('.favorite-btn');
  console.log(`Found ${favoriteButtons.length} favorite buttons`);
  
  favoriteButtons.forEach(btn => {
    const friendId = btn.getAttribute('data-friend-id');
    const isFavorite = btn.classList.contains('is-favorite');
    const dataAttr = btn.getAttribute('data-is-favorite');
    
    console.log(`Friend ID: ${friendId}, Button class: ${isFavorite ? 'is-favorite' : 'not-favorite'}, Data attribute: ${dataAttr}`);
  });
  
  const favoritesInStorage = localStorage.getItem('favoriteFriends');
  console.log("Favorites in localStorage:", favoritesInStorage);
};

window.resetFilters = resetFilters;
window.filterApplications = filterApplications;
window.saveApplication = saveApplication;
