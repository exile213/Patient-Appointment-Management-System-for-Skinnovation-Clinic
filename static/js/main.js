// Main JavaScript file for Beauty Clinic

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Service category filter animation
    const categoryButtons = document.querySelectorAll('.category-filter .btn');
    if (categoryButtons.length > 0) {
        categoryButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Add a small animation when clicking category buttons
                this.classList.add('btn-pulse');
                setTimeout(() => {
                    this.classList.remove('btn-pulse');
                }, 300);
            });
        });
    }

    // Add animation class for service cards
    const serviceCards = document.querySelectorAll('.service-card, .service-item');
    if (serviceCards.length > 0) {
        // Simple animation when scrolling to service cards
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        serviceCards.forEach(card => {
            observer.observe(card);
        });
    }
});

// Add custom validation for booking form
if (document.getElementById('booking-form')) {
    const bookingForm = document.getElementById('booking-form');

    bookingForm.addEventListener('submit', function(event) {
        let isValid = true;

        // Validate dermatologist selection
        const dermatologistSelect = document.getElementById('dermatologist_id');
        if (dermatologistSelect.value === '') {
            isValid = false;
            dermatologistSelect.classList.add('is-invalid');
        } else {
            dermatologistSelect.classList.remove('is-invalid');
        }

        // Validate date selection
        const dateInput = document.getElementById('appointment_date');
        if (dateInput.value === '') {
            isValid = false;
            dateInput.classList.add('is-invalid');
        } else {
            dateInput.classList.remove('is-invalid');
        }

        // Validate time selection
        const timeSelect = document.getElementById('appointment_time');
        if (timeSelect.value === '') {
            isValid = false;
            timeSelect.classList.add('is-invalid');
        } else {
            timeSelect.classList.remove('is-invalid');
        }

        if (!isValid) {
            event.preventDefault();
            // Show validation message
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger mt-3';
            alertDiv.textContent = 'Please fill in all required fields.';

            // Remove any existing alerts
            const existingAlerts = bookingForm.querySelectorAll('.alert');
            existingAlerts.forEach(alert => alert.remove());

            bookingForm.prepend(alertDiv);
        }
    });
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('collapsed');
}
