// Thai Massage Manager - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize form validations
    initFormValidations();
    
    // Initialize date pickers
    initDatePickers();
    
    // Initialize auto-calculation
    initAutoCalculations();
});

// Tooltip initialization
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Form validation
function initFormValidations() {
    // Password strength indicator
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', function() {
            checkPasswordStrength(this.value, this);
        });
    });
    
    // Numeric input validation
    const numericInputs = document.querySelectorAll('input[type="number"]');
    numericInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value < 0) {
                this.value = 0;
                showToast('El valor no puede ser negativo', 'warning');
            }
        });
    });
}

// Password strength checker
function checkPasswordStrength(password, inputElement) {
    if (!password) return;
    
    const strengthIndicator = inputElement.parentNode.querySelector('.password-strength');
    if (!strengthIndicator) return;
    
    let strength = 0;
    let feedback = '';
    
    // Length check
    if (password.length >= 8) strength++;
    else feedback = 'La contraseña debe tener al menos 8 caracteres. ';
    
    // Lowercase check
    if (/[a-z]/.test(password)) strength++;
    else feedback += 'Incluye letras minúsculas. ';
    
    // Uppercase check
    if (/[A-Z]/.test(password)) strength++;
    else feedback += 'Incluye letras mayúsculas. ';
    
    // Number check
    if (/[0-9]/.test(password)) strength++;
    else feedback += 'Incluye números. ';
    
    // Special character check
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    else feedback += 'Incluye caracteres especiales. ';
    
    // Update strength indicator
    const strengthClasses = ['bg-danger', 'bg-warning', 'bg-info', 'bg-success'];
    strengthIndicator.className = `password-strength progress-bar ${strengthClasses[strength - 1] || 'bg-danger'}`;
    strengthIndicator.style.width = `${(strength / 5) * 100}%`;
    strengthIndicator.setAttribute('aria-valuenow', (strength / 5) * 100);
    
    // Update feedback
    const feedbackElement = inputElement.parentNode.querySelector('.password-feedback');
    if (feedbackElement) {
        feedbackElement.textContent = feedback || 'Contraseña segura';
        feedbackElement.className = `password-feedback form-text ${strength >= 4 ? 'text-success' : 'text-warning'}`;
    }
}

// Date picker initialization
function initDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        // Set max date to today for future restrictions
        if (!input.max) {
            const today = new Date().toISOString().split('T')[0];
            input.max = today;
        }
    });
}

// Auto-calculation for session forms
function initAutoCalculations() {
    const hoursInput = document.getElementById('hours');
    const priceInput = document.getElementById('price_per_hour');
    
    if (hoursInput && priceInput) {
        const calculateTotal = () => {
            const hours = parseFloat(hoursInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0;
            const total = hours * price;
            const tax = total * 0.21;
            const net = total - tax;
            
            // Update display elements if they exist
            const totalElement = document.getElementById('total-display');
            const taxElement = document.getElementById('tax-display');
            const netElement = document.getElementById('net-display');
            
            if (totalElement) totalElement.textContent = total.toFixed(2) + '€';
            if (taxElement) taxElement.textContent = tax.toFixed(2) + '€';
            if (netElement) netElement.textContent = net.toFixed(2) + '€';
        };
        
        hoursInput.addEventListener('input', calculateTotal);
        priceInput.addEventListener('input', calculateTotal);
    }
}

// Toast notification system
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove toast from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
}

// Export functions for global access
window.TMM = {
    showToast: showToast,
    initTooltips: initTooltips
};

// Auto-dismiss alerts after 5 seconds
const autoDismissAlerts = document.querySelectorAll('.alert-dismissible');
autoDismissAlerts.forEach(alert => {
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    }, 5000);
});

// Confirm dialog for destructive actions
function confirmAction(message = '¿Estás seguro de que quieres realizar esta acción?') {
    return confirm(message);
}

// Attach confirm to all delete buttons
const deleteButtons = document.querySelectorAll('a[href*="delete"], button[type="submit"][class*="danger"]');
deleteButtons.forEach(button => {
    button.addEventListener('click', function(e) {
        if (!confirmAction()) {
            e.preventDefault();
        }
    });
});