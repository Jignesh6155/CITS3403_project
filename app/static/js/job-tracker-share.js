/* 
 * Enhanced share modal for jobTracker.html
 * This script replaces the existing dropdown with a searchable friend selector
 */

// Replace the existing share modal with an enhanced version that includes search
function enhanceShareModal() {
  const originalModal = document.getElementById('shareModal');
  if (!originalModal) return;
  
  // Create the enhanced modal HTML
  const enhancedModalHTML = `
    <div id="shareModal" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 hidden">
      <div class="bg-white p-6 rounded-lg w-full max-w-md relative">
        <button onclick="closeShareModal()" class="absolute top-2 right-3 text-gray-500 hover:text-black text-xl font-bold">&times;</button>
        <h2 class="text-lg font-semibold text-gray-800 mb-4">Share Application</h2>
        
        <!-- Search input for finding friends -->
        <div class="relative mb-4">
          <input type="text" id="share-friend-search" placeholder="Search friends..." class="w-full border rounded px-3 py-2 text-sm mb-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        
        <form method="POST" id="shareForm">
          <div class="max-h-60 overflow-y-auto mb-4 border rounded">
            <ul id="share-friends-list" class="divide-y divide-gray-200">
              <!-- Friend items will be populated dynamically -->
            </ul>
          </div>
          <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-2 rounded w-full disabled:opacity-50 disabled:cursor-not-allowed" id="share-submit-btn">
            Share Application
          </button>
        </form>
      </div>
    </div>
  `;
  
  // Replace the original modal
  originalModal.outerHTML = enhancedModalHTML;
  
  // Populate the friends list using the existing friends data
  populateFriendsList();
}

// Populate the friends list in the share modal
function populateFriendsList() {
  const friendsList = document.getElementById('share-friends-list');
  if (!friendsList) return;
  
  // Get existing friends data from the document
  const friendsData = getFriendsData();
  
  if (friendsData.length === 0) {
    friendsList.innerHTML = '<li class="py-4 text-center text-gray-500">No friends to share with</li>';
    return;
  }
  
  // Build the list of friends
  let friendsHTML = '';
  
  friendsData.forEach(friend => {
    friendsHTML += `
      <li class="py-2 px-3 hover:bg-gray-50 cursor-pointer share-friend-item" data-id="${friend.id}" data-name="${friend.name.toLowerCase()}">
        <label class="flex items-center cursor-pointer w-full">
          <input type="radio" name="friend_id" value="${friend.id}" class="mr-2">
          <span>${friend.name}</span>
        </label>
      </li>
    `;
  });
  
  friendsList.innerHTML = friendsHTML;
  
  // Add event listeners to friend items
  setupFriendItemListeners();
}

// Extract friends data from the existing form
function getFriendsData() {
  const friendsData = [];
  
  // Try to get friends from any existing select element
  const select = document.querySelector('select[name="friend_id"]');
  if (select) {
    Array.from(select.options).forEach(option => {
      if (option.value) {
        friendsData.push({
          id: option.value,
          name: option.textContent.trim()
        });
      }
    });
  }
  
  return friendsData;
}

// Setup event listeners for friend items in the share modal
function setupFriendItemListeners() {
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
}

// Setup event listener for the friend search input
function setupFriendSearch() {
  const shareFriendSearch = document.getElementById('share-friend-search');
  if (!shareFriendSearch) return;
  
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
    if (submitBtn) {
      submitBtn.disabled = !anyVisible;
    }
    
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

// Update the openShareModal function to use the enhanced modal
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

// Update the submit handler for the share form
function setupShareFormSubmission() {
  const shareForm = document.getElementById('shareForm');
  if (!shareForm) return;
  
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

// Toast notification function
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

// Initialize the enhanced share modal functionality
document.addEventListener('DOMContentLoaded', function() {
  // Replace the share modal with the enhanced version
  enhanceShareModal();
  
  // Setup friend search
  setupFriendSearch();
  
  // Setup form submission
  setupShareFormSubmission();
});