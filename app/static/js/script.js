function showLogin() {
    document.getElementById('login-form').classList.remove('translate-x-full');
    document.getElementById('login-form').classList.add('translate-x-0');
  }
  
  function hideLogin() {
    document.getElementById('login-form').classList.remove('translate-x-0');
    document.getElementById('login-form').classList.add('translate-x-full');
  }

  // Notification handling
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
  
  // Toggle notification dropdown
  notificationButton.addEventListener('click', function() {
    notificationDropdown.classList.toggle('hidden');
    if (!notificationDropdown.classList.contains('hidden')) {
      loadNotifications(1, true); // Reset to first page when opening
    }
  });
  
  // Close dropdown when clicking outside
  document.addEventListener('click', function(event) {
    if (!notificationButton.contains(event.target) && !notificationDropdown.contains(event.target)) {
      notificationDropdown.classList.add('hidden');
    }
  });
  
  // Mark all as read
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
  
  // Load more notifications
  loadMoreBtn.addEventListener('click', function(e) {
    e.preventDefault();
    if (hasMoreNotifications) {
      loadNotifications(currentPage + 1, false);
    }
  });
  
  // Load notifications function
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
  
  // Mark specific notifications as read
  function markAsRead(ids) {
    fetch('/api/notifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notification_ids: ids })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        loadNotifications(currentPage, true);
        updateNotificationCount();
      }
    });
  }
  
  // Update notification count badge
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
  
  // Time ago function for dates
  function timeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
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