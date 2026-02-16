/* ALTER - Global JS utilities */

// Show toast notification
function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.innerHTML = `
        <div class="bg-white rounded-lg shadow-lg border border-gray-200 p-4 max-w-sm animate-slide-in flex items-start space-x-3">
            ${type === 'success'
                ? '<svg class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
                : type === 'error'
                ? '<svg class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>'
                : '<svg class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
            }
            <div>
                <p class="text-sm font-medium text-gray-900">${title}</p>
                <p class="text-sm text-gray-500">${message}</p>
            </div>
        </div>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// HTMX event listeners for toast notifications
document.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful && evt.detail.verb !== 'get') {
        showToast('Success', 'Action completed successfully', 'success');
    }
});

document.addEventListener('htmx:responseError', function(evt) {
    showToast('Error', 'Something went wrong. Please try again.', 'error');
});
