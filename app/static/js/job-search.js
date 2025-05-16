// Global variables and constants
const PAGE_SIZE = 10;
let currentPage = 1;
let hasMore = true;
let jobs = [];
let isScrapingActive = false;

// Add these style classes at the start of your script
const FILTER_STYLES = {
  location: {
    active: 'bg-blue-50 text-blue-800 border-blue-300',
    hover: 'hover:bg-blue-100'
  },
  jobtype: {
    active: 'bg-green-50 text-green-800 border-green-300',
    hover: 'hover:bg-green-100'
  },
  category: {
    active: 'bg-purple-50 text-purple-800 border-purple-300',
    hover: 'hover:bg-purple-100'
  }
};

function setSelectValue(selectId, value) {
  const select = document.querySelector(`select[data-type="${selectId}"]`);
  if (select) {
    const options = Array.from(select.options);
    const option = options.find(opt => 
      opt.value.toLowerCase() === value.toLowerCase() ||
      opt.text.toLowerCase() === value.toLowerCase()
    );
    if (option) {
      select.value = option.value;
      select.dispatchEvent(new Event('change'));
    }
  }
}

function saveJob(jobData) {
  const payload = {
    title: jobData.title,
    company: jobData.company,
    location: jobData.location || (jobData.tags?.location || ''),
    job_type: jobData.job_type || (jobData.tags?.jobtype || ''),
    closing_date: jobData.closing_date || '',
    status: 'Saved',
  };
  if (jobData.id) payload.scraped_job_id = jobData.id;
  let btn = null;
  if (event && event.target && event.target.classList.contains('save-job-btn')) {
    btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="loader mr-2"></span>Saving...';
  }
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const CSRF = csrfMeta ? csrfMeta.content : '';
  fetch('/add-application', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(CSRF && { 'X-CSRFToken': CSRF }),
    },
    body: JSON.stringify(payload)
  })
  .then(async response => {
    const contentType = response.headers.get('content-type');
    if (!response.ok) {
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to save job');
      } else {
        throw new Error('You may not be logged in, or an unexpected error occurred.');
      }
    }
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    } else {
      throw new Error('Unexpected server response. Please log in again.');
    }
  })
  .then(data => {
    if (data.success) {
      if (btn) {
        btn.innerHTML = 'Saved!';
        btn.classList.remove('bg-white', 'text-indigo-600', 'hover:bg-indigo-50');
        btn.classList.add('bg-gray-100', 'text-gray-600', 'cursor-not-allowed');
      }
      showToast('Job saved successfully!', 'success');
    } else {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'Save Job';
      }
      throw new Error(data.error || 'Failed to save job');
    }
  })
  .catch(error => {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = 'Save Job';
    }
    console.error('Error:', error);
    showToast(error.message || 'Failed to save job', 'error');
  });
}

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
  const searchInput = document.querySelector('input[placeholder="Search for roles, companies, or locations"]');
  const searchButton = document.getElementById('start-scraping-btn');
  const scrapingLoader = document.getElementById('scraping-loader');
  const locationSelect = document.querySelectorAll('select')[0];
  const typeSelect = document.querySelectorAll('select')[1];
  const categorySelect = document.querySelectorAll('select')[2];
  const jobsList = document.getElementById('scraped-jobs-list');
  const jobsWindow = document.getElementById('scraped-jobs-window');
  locationSelect.className = `border rounded-md px-3 py-2 ${FILTER_STYLES.location.hover}`;
  typeSelect.className = `border rounded-md px-3 py-2 ${FILTER_STYLES.jobtype.hover}`;
  categorySelect.className = `border rounded-md px-3 py-2 ${FILTER_STYLES.category.hover}`;
  locationSelect.setAttribute('data-type', 'location');
  typeSelect.setAttribute('data-type', 'jobtype');
  categorySelect.setAttribute('data-type', 'category');
  function updateFilterStyle(select, type) {
    const styles = FILTER_STYLES[type];
    if (select.value && select.value !== select.options[0].text) {
      select.className = `border rounded-md px-3 py-2 ${styles.active}`;
    } else {
      select.className = `border rounded-md px-3 py-2 ${styles.hover}`;
    }
  }
  function getFilterValue(select, defaultText) {
    const val = select.value;
    return (val && val !== select.options[0].text) ? val : '';
  }
  function renderJobTags(tags) {
    if (!tags) return '';
    const tagElements = [];
    if (tags.location) {
      tagElements.push(`
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 cursor-pointer hover:bg-blue-200" 
              onclick="setSelectValue('location', '${tags.location}')">
          <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          ${tags.location}
        </span>
      `);
    }
    if (tags.jobtype) {
      tagElements.push(`
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 cursor-pointer hover:bg-green-200"
              onclick="setSelectValue('jobtype', '${tags.jobtype}')">
          <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
          ${tags.jobtype}
        </span>
      `);
    }
    if (tags.category) {
      tagElements.push(`
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 cursor-pointer hover:bg-purple-200"
              onclick="setSelectValue('category', '${tags.category}')">
          <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
          </svg>
          ${tags.category}
        </span>
      `);
    }
    return tagElements.length ? `
      <div class="flex flex-wrap gap-2 mt-2">
        ${tagElements.join('')}
      </div>
    ` : '';
  }
  function renderJobs(jobsArr, append = false) {
    if (!append) jobsList.innerHTML = '';
    if (jobsArr.length === 0 && !append) {
      jobsList.innerHTML = '<li class="text-gray-400">No jobs found.</li>';
      return;
    }
    jobsArr.forEach(job => {
      const li = document.createElement('li');
      li.className = 'bg-white border border-indigo-100 p-4 rounded-md shadow-sm scraped-job-item';
      let closingHtml = '';
      if (job.closing_in || job.closing_date) {
        closingHtml = `
          <div class="text-red-600 font-medium text-sm mt-2">
            ${job.closing_in ? job.closing_in : ''}
            ${job.closing_in && job.closing_date ? ' • ' : ''}
            ${job.closing_date ? job.closing_date : ''}
          </div>
        `;
      }
      li.innerHTML = `
        <div class="flex justify-between items-center">
          <span class="font-semibold truncate max-w-[60%] block">${job.title}</span>
          <div class="flex items-center gap-2 flex-shrink-0">
            ${job.posted_date && job.posted_date !== 'n/a' ? `<span class="text-gray-400 text-xs">Posted: ${job.posted_date}</span>` : ''}
            <button class="save-job-btn inline-flex items-center justify-center w-24 flex-shrink-0 px-2.5 py-1.5 border border-indigo-500 text-xs font-medium rounded text-indigo-600 bg-white hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
              <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
              </svg>
              Save Job
            </button>
          </div>
        </div>
        ${job.company ? `<div class="text-gray-600 text-sm mt-1">Company: ${job.company}</div>` : ''}
        ${closingHtml}
        <p class="text-gray-700 mt-2">${job.ai_summary}</p>
        ${renderJobTags(job.tags)}
        <a href="${job.link}" target="_blank" class="text-indigo-600 hover:underline text-xs mt-2 inline-block">View Job</a>
      `;
      const saveButton = li.querySelector('.save-job-btn');
      saveButton.addEventListener('click', () => saveJob(job));
      jobsList.appendChild(li);
    });
  }
  function addJobLive(job) {
    const li = document.createElement('li');
    li.className = 'bg-white border border-indigo-100 p-4 rounded-md shadow-sm scraped-job-item';
    let closingHtml = '';
    if (job.closing_in || job.closing_date) {
      closingHtml = `
        <div class="text-red-600 font-medium text-sm mt-2">
          ${job.closing_in ? job.closing_in : ''}
          ${job.closing_in && job.closing_date ? ' • ' : ''}
          ${job.closing_date ? job.closing_date : ''}
        </div>
      `;
    }
    li.innerHTML = `
      <div class="flex justify-between items-center">
        <span class="font-semibold truncate max-w-[60%] block">${job.title}</span>
        <div class="flex items-center gap-2 flex-shrink-0">
          ${job.posted_date && job.posted_date !== 'n/a' ? `<span class="text-gray-400 text-xs">Posted: ${job.posted_date}</span>` : ''}
          <button class="save-job-btn inline-flex items-center justify-center w-24 flex-shrink-0 px-2.5 py-1.5 border border-indigo-500 text-xs font-medium rounded text-indigo-600 bg-white hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
            </svg>
            Save Job
          </button>
        </div>
      </div>
      ${job.company ? `<div class="text-gray-600 text-sm mt-1">Company: ${job.company}</div>` : ''}
      ${closingHtml}
      <p class="text-gray-700 mt-2">${job.ai_summary}</p>
      ${renderJobTags(job.tags)}
      <a href="${job.link}" target="_blank" class="text-indigo-600 hover:underline text-xs mt-2 inline-block">View Job</a>
    `;
    const saveButton = li.querySelector('.save-job-btn');
    saveButton.addEventListener('click', () => saveJob(job));
    jobsList.insertBefore(li, jobsList.firstChild);
  }
  function fetchJobs(reset = true) {
    if (reset) {
      currentPage = 1;
      jobs = [];
      hasMore = true;
      jobsList.innerHTML = '<li class="text-gray-400">Loading...</li>';
    }
    const params = new URLSearchParams({
      search: searchInput.value.trim(),
      location: getFilterValue(locationSelect, 'Location'),
      type: getFilterValue(typeSelect, 'Opportunity Type'),
      category: getFilterValue(categorySelect, 'Category'),
      offset: (currentPage - 1) * PAGE_SIZE,
      limit: PAGE_SIZE
    });
    console.log('Fetching jobs with params:', params.toString());
    fetch(`/api/scraped-jobs?${params.toString()}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        console.log('Received jobs data:', data);
        hasMore = data.has_more;
        if (reset) {
          jobs = data.jobs.slice();
          jobs.sort((a, b) => {
            const aDate = a.closing_date ? new Date(a.closing_date) : null;
            const bDate = b.closing_date ? new Date(b.closing_date) : null;
            if (aDate && bDate) return aDate - bDate;
            if (aDate && !bDate) return -1;
            if (!aDate && bDate) return 1;
            return 0;
          });
          renderJobs(jobs);
        } else {
          jobs = jobs.concat(data.jobs);
          jobs.sort((a, b) => {
            const aDate = a.closing_date ? new Date(a.closing_date) : null;
            const bDate = b.closing_date ? new Date(b.closing_date) : null;
            if (aDate && bDate) return aDate - bDate;
            if (aDate && !bDate) return -1;
            if (!aDate && bDate) return 1;
            return 0;
          });
          renderJobs(jobs);
        }
      })
      .catch(error => {
        console.error('Error fetching jobs:', error);
        jobsList.innerHTML = '<li class="text-red-400">Failed to load jobs. Please try again.</li>';
      });
  }
  searchInput.addEventListener('input', () => fetchJobs());
  searchButton.addEventListener('click', function(e) {
    e.preventDefault();
    if (isScrapingActive) return;
    const jobtype = getFilterValue(typeSelect, 'Opportunity Type').toLowerCase() || 'internships';
    const discipline = getFilterValue(categorySelect, 'Category').toLowerCase();
    const location = getFilterValue(locationSelect, 'Location').toLowerCase();
    const keyword = searchInput.value.trim();
    scrapingLoader.classList.remove('hidden');
    isScrapingActive = true;
    jobsList.innerHTML = '<li class="text-gray-400">Starting new search...</li>';
    fetch('/api/start-scraping', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jobtype, discipline, location, keyword })
    })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        console.log('Scraping started successfully');
      })
      .catch(err => {
        console.error('Error sending POST /api/start-scraping:', err);
        scrapingLoader.classList.add('hidden');
        isScrapingActive = false;
        jobsList.innerHTML = '<li class="text-red-400">Failed to start search. Please try again.</li>';
      });
  });
  locationSelect.addEventListener('change', () => {
    updateFilterStyle(locationSelect, 'location');
    fetchJobs();
  });
  typeSelect.addEventListener('change', () => {
    updateFilterStyle(typeSelect, 'jobtype');
    fetchJobs();
  });
  categorySelect.addEventListener('change', () => {
    updateFilterStyle(categorySelect, 'category');
    fetchJobs();
  });
  jobsWindow.addEventListener('scroll', function() {
    if (jobsWindow.scrollTop + jobsWindow.clientHeight >= jobsWindow.scrollHeight - 50) {
      if (hasMore && !isScrapingActive) {
        currentPage++;
        fetchJobs(false);
      }
    }
  });
  if (!!window.EventSource) {
    console.log('Opening SSE connection to /api/scraping-stream');
    const sse = new EventSource('/api/scraping-stream');
    sse.onmessage = function(event) {
      console.log('SSE job received:', event.data);
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'ping') {
          console.log('Received ping from server');
          return;
        }
        if (data.status === 'complete') {
          console.log('Scraping complete, hiding loader');
          scrapingLoader.classList.add('hidden');
          isScrapingActive = false;
          fetchJobs();
          return;
        }
        addJobLive(data);
      } catch (error) {
        console.error('Error processing SSE message:', error);
      }
    };
    sse.onerror = function(error) {
      console.error('SSE connection error:', error);
      scrapingLoader.classList.add('hidden');
      isScrapingActive = false;
    };
  }
  const dropArea = document.getElementById('resume-drop-area');
  const fileInput = document.getElementById('resume-input');
  const fileNameSpan = document.getElementById('resume-filename');
  if (dropArea && fileInput) {
    dropArea.addEventListener('click', function(e) {
      if (e.target === fileInput) return;
      fileInput.click();
    });
    fileInput.addEventListener('change', function() {
      if (fileInput.files.length > 0) {
        fileNameSpan.textContent = fileInput.files[0].name;
      } else {
        fileNameSpan.textContent = '';
      }
    });
    ['dragenter', 'dragover'].forEach(eventName => {
      dropArea.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropArea.classList.add('border-indigo-400', 'bg-indigo-50');
      });
    });
    ['dragleave', 'drop'].forEach(eventName => {
      dropArea.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropArea.classList.remove('border-indigo-400', 'bg-indigo-50');
      });
    });
    dropArea.addEventListener('drop', e => {
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        fileNameSpan.textContent = fileInput.files[0].name;
      }
    });
  }
  const resetFiltersBtn = document.getElementById('reset-filters');
  function resetFilters() {
    locationSelect.selectedIndex = 0;
    typeSelect.selectedIndex = 0;
    categorySelect.selectedIndex = 0;
    searchInput.value = '';
    updateFilterStyle(locationSelect, 'location');
    updateFilterStyle(typeSelect, 'jobtype');
    updateFilterStyle(categorySelect, 'category');
    fetchJobs();
  }
  resetFiltersBtn.addEventListener('click', resetFilters);
  updateFilterStyle(locationSelect, 'location');
  updateFilterStyle(typeSelect, 'jobtype');
  updateFilterStyle(categorySelect, 'category');
  fetchJobs();
}); 