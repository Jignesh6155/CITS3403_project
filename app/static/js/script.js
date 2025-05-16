/**
 * Global utility functions for the CareerLink application
 * 
 * This script contains general functions used across the application including:
 * - Login form control (show/hide)
 * - Notification handling system
 * - Date/time formatting utilities
 */

/**
 * Shows the login form by animating it into view
 * Removes the translate-x-full class and adds translate-x-0 for slide-in effect
 */
function showLogin() {
  document.getElementById('login-form').classList.remove('translate-x-full');
  document.getElementById('login-form').classList.add('translate-x-0');
}

/**
 * Hides the login form by animating it out of view
 * Removes the translate-x-0 class and adds translate-x-full for slide-out effect
 */
function hideLogin() {
  document.getElementById('login-form').classList.remove('translate-x-0');
  document.getElementById('login-form').classList.add('translate-x-full');
}

/**
 * Notification system initialization
 * Sets up event handlers for the notification dropdown and loads notifications from the API
 */
document.addEventListener('DOMContentLoaded', function() {
  const notificationButton = document.getElementById('notificationButton');
  if (!notificationButton) return; // Exit if not on a page with notifications
  
  const notificationDropdown = document.getElementById('notificationDropdown');
  const notificationBadge = document.getElementById('notification-badge');
  const notificationList = document.getElementById('notificationList');
  const markAllReadBtn = document.getElementById('markAllRead');
  const loadMoreBtn = document.getElementById('loadMoreNotifications');
  
  let currentPage = 1;
  let hasMoreNotifications = false;
  
  /**
   * Toggle notification dropdown visibility when notification icon is clicked
   * Also reloads notifications when opening the dropdown
   */
  notificationButton.addEventListener('click', function() {
    notificationDropdown.classList.toggle('hidden');
    if (!notificationDropdown.classList.contains('hidden')) {
      loadNotifications(1, true); // Reset to first page when opening
    }
  });
  
  /**
   * Close notification dropdown when clicking outside
   * Handles document-level click events to detect clicks outside the dropdown
   */
  document.addEventListener('click', function(event) {
    if (!notificationButton.contains(event.target) && !notificationDropdown.contains(event.target)) {
      notificationDropdown.classList.add('hidden');
    }
  });
  
  /**
   * Mark all notifications as read
   * Sends an empty notification_ids array to mark all as read
   */
  markAllReadBtn.addEventListener('click', function() {
    fetch('/api/notifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notification_ids: [] }) // Empty array marks all as read
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        loadNotifications(1, true);
        updateNotificationCount();
      }
    });
  });
  
  /**
   * Load more notifications when clicking the "Load more" button
   * Increments the page and appends new notifications
   */
  loadMoreBtn.addEventListener('click', function(e) {
    e.preventDefault();
    if (hasMoreNotifications) {
      loadNotifications(currentPage + 1, false);
    }
  });
  
  /**
   * Load notifications from the API
   * @param {number} page - The page number to load
   * @param {boolean} reset - Whether to reset the notification list or append
   */
  function loadNotifications(page, reset) {
    currentPage = page;
    
    fetch(`/api/notifications?page=${page}&per_page=5`)
      .then(response => response.json())
      .then(data => {
        hasMoreNotifications = data.has_next;
        loadMoreBtn.style.display = hasMoreNotifications ? 'inline' : 'none';
        
        // Update the UI
        if (reset) {
          notificationList.innerHTML = '';
        }
        
        if (data.notifications.length === 0 && reset) {
          notificationList.innerHTML = '<div class="py-6 text-center text-gray-500 text-sm">No notifications</div>';
          return;
        }
        
        data.notifications.forEach(notification => {
          const notificationItem = document.createElement('div');
          notificationItem.className = `p-4 hover:bg-gray-50 transition ${notification.is_read ? 'opacity-60' : 'bg-indigo-50 bg-opacity-30'}`;
          
          // Choose icon based on notification type
          let iconClass = 'user';
          if (notification.type === 'friend_request') iconClass = 'user-plus';
          else if (notification.type === 'application_shared') iconClass = 'briefcase';
          
          notificationItem.innerHTML = `
            <a href="${notification.link || '#'}" class="block">
              <div class="flex items-start">
                <div class="flex-shrink-0 mt-0.5">
                  <i data-lucide="${iconClass}" class="w-5 h-5 text-indigo-500"></i>
                </div>
                <div class="ml-3 flex-1">
                  <p class="text-sm text-gray-900">${notification.content}</p>
                  <p class="text-xs text-gray-500 mt-1">${timeAgo(new Date(notification.created_at))}</p>
                </div>
                ${!notification.is_read ? 
                  `<button class="mark-read-btn flex-shrink-0 ml-2" data-id="${notification.id}">
                    <i data-lucide="check" class="w-4 h-4 text-gray-400 hover:text-indigo-600"></i>
                  </button>` : ''}
              </div>
            </a>
          `;
          
          notificationList.appendChild(notificationItem);
        });
        
        // Initialize Lucide icons for the new elements
        lucide.createIcons();
        
        // Add event listeners to mark as read buttons
        document.querySelectorAll('.mark-read-btn').forEach(btn => {
          btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const notificationId = this.getAttribute('data-id');
            markAsRead([notificationId]);
          });
        });
      });
  }
  
  /**
   * Mark specific notifications as read
   * @param {Array} ids - Array of notification IDs to mark as read
   */
  function markAsRead(ids) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch('/api/notifications', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken  // Add CSRF token for security
      },
      body: JSON.stringify({ notification_ids: ids })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        loadNotifications(currentPage, true);
        updateNotificationCount();
      }
    })
    .catch(error => console.error('Error:', error)); 
  }

  /**
   * Update notification count badge in the UI
   * Makes an API call to get the unread count and updates the badge visibility
   */
  function updateNotificationCount() {
    fetch('/api/notifications?count_only=true')
      .then(response => response.json())
      .then(data => {
        if (data.unread_count > 0) {
          notificationBadge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
          notificationBadge.classList.remove('hidden');
        } else {
          notificationBadge.classList.add('hidden');
        }
      });
  }
  
  /**
   * Convert a date to a human-readable "time ago" string
   * @param {Date|string} dateStr - Date object or ISO string
   * @returns {string} Human-readable time difference (e.g., "5 minutes ago")
   */
  function timeAgo(dateStr) {
    // Check if we received a backend formatted datetime without timezone
    // Format: "2025-05-06 14:30:45"
    if (typeof dateStr === 'string' && dateStr.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)) {
      // Assume UTC and convert to ISO format
      dateStr = dateStr.replace(' ', 'T') + 'Z';
    }
    
    // Ensure the date is properly parsed
    const date = new Date(dateStr);
    
    // Validate if the date is valid
    if (isNaN(date.getTime())) {
      console.error('Invalid date provided to timeAgo:', dateStr);
      return 'unknown time ago';
    }
    
    // Compare with current time
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    // For debugging - log time difference info
    console.log('Time difference debugging:', {
      now: now.toISOString(),
      date: date.toISOString(),
      differenceInSeconds: seconds
    });
    
    // Negative time difference guard
    if (seconds < 0) {
      return 'in the future';
    }
    
    // Calculate appropriate time unit
    let interval = Math.floor(seconds / 31536000);
    if (interval > 1) return interval + ' years ago';
    if (interval === 1) return '1 year ago';
    
    interval = Math.floor(seconds / 2592000);
    if (interval > 1) return interval + ' months ago';
    if (interval === 1) return '1 month ago';
    
    interval = Math.floor(seconds / 86400);
    if (interval > 1) return interval + ' days ago';
    if (interval === 1) return '1 day ago';
    
    interval = Math.floor(seconds / 3600);
    if (interval > 1) return interval + ' hours ago';
    if (interval === 1) return '1 hour ago';
    
    interval = Math.floor(seconds / 60);
    if (interval > 1) return interval + ' minutes ago';
    if (interval === 1) return '1 minute ago';
    
    if (seconds < 10) return 'just now';
    return Math.floor(seconds) + ' seconds ago';
  }
  
  // Initialize notification count on page load and set interval to update
  updateNotificationCount();
  setInterval(updateNotificationCount, 60000); // Update every minute
});
