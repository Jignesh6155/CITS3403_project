/**
 * Dashboard Charts Initialization
 * 
 * This script initializes and renders the charts displayed on the dashboard.
 * It parses data from script tags and creates interactive chart visualizations
 * using Chart.js.
 * 
 * Dependencies: 
 * - Chart.js library
 * - JSON data embedded in application/json script tags
 */

// Parse chart data from embedded JSON in script tags
const labels = JSON.parse(document.getElementById('dashboard-labels').textContent);
const counts = JSON.parse(document.getElementById('dashboard-counts').textContent);

// Define color array for consistent chart styling
// The array is sliced to match the number of data points to ensure consistent colors
const colors = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#f97316', '#22d3ee'].slice(0, labels.length);

// Initialize charts only if Chart.js is loaded
if (window.Chart) {
  /**
   * Bar Chart Initialization
   * Shows the distribution of job applications by status
   */
  new Chart(document.getElementById('barChart'), {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Count',
        data: counts,
        backgroundColor: colors,
        borderColor: colors,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false }},  // Hide legend for cleaner appearance
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1 } }  // Start y-axis at 0 with whole number steps
      }
    }
  });
  
  /**
   * Pie Chart Initialization
   * Shows the relative proportion of each job application status
   */
  new Chart(document.getElementById('pieChart'), {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: counts,
        backgroundColor: colors,
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom' },  // Place legend below for better layout
        tooltip: { mode: 'index', intersect: false }  // Show tooltip on hover over any part of slice
      }
    }
  });
}
