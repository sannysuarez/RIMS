// Shop Ceramics - JavaScript utilities

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips or other interactive elements
    console.log('Shop Ceramics Inventory System Loaded');
});

// Utility function: Show confirmation dialog
function confirmAction(message) {
    return confirm(message);
}

// Utility function: Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN',
    }).format(amount);
}

// Utility function: Validate form
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    return form.checkValidity() === false ? false : true;
}

// Search and filter helper
function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    const filter = input.value.toUpperCase();
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const text = rows[i].textContent || rows[i].innerText;
        rows[i].style.display = text.toUpperCase().indexOf(filter) > -1 ? '' : 'none';
    }
}

// Format date to locale string
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}
