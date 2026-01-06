// Appointment Detail Interactive Features
document.addEventListener('DOMContentLoaded', function() {
    // Add loading animation to detail cards
    const detailCards = document.querySelectorAll('.detail-card');
    detailCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease-out';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 200);
    });
    
    // Add hover effects to action buttons
    const actionButtons = document.querySelectorAll('.btn-action');
    actionButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px) scale(1.05)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add confirmation dialog for status changes
    const statusChangeButtons = document.querySelectorAll('form[action*="confirm"], form[action*="complete"]');
    statusChangeButtons.forEach(form => {
        form.addEventListener('submit', function(e) {
            const action = this.action.includes('confirm') ? 'confirm' : 'complete';
            const actionText = action === 'confirm' ? 'confirm this appointment' : 'mark this appointment as completed';
            
            if (!confirm(`Are you sure you want to ${actionText}?`)) {
                e.preventDefault();
            }
        });
    });
    
    // Add click animation to buttons
    const buttons = document.querySelectorAll('.btn-action, .btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Create ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Add status badge pulse animation for pending appointments
    const pendingBadges = document.querySelectorAll('.status-badge.status-pending');
    pendingBadges.forEach(badge => {
        badge.classList.add('pulse');
    });
    
    // Add timeline animation
    const timelineItems = document.querySelectorAll('.timeline-item');
    timelineItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-30px)';
        
        setTimeout(() => {
            item.style.transition = 'all 0.6s ease-out';
            item.style.opacity = '1';
            item.style.transform = 'translateX(0)';
        }, index * 300);
    });
    
    // Add smooth scroll to sections
    const backButtons = document.querySelectorAll('a[href*="appointments"]');
    backButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Add a small delay for smooth transition
            setTimeout(() => {
                window.location.href = this.href;
            }, 200);
        });
    });
    
    // Add real-time status updates (if needed)
    const statusBadge = document.querySelector('.status-badge');
    if (statusBadge) {
        // Add a subtle glow effect for status badges
        statusBadge.style.boxShadow = '0 0 10px rgba(0,0,0,0.1)';
    }
    
    // Add fade-in animation to main content
    const mainContent = document.querySelector('.fade-in');
    if (mainContent) {
        mainContent.style.opacity = '0';
        mainContent.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            mainContent.style.transition = 'all 0.8s ease-out';
            mainContent.style.opacity = '1';
            mainContent.style.transform = 'translateY(0)';
        }, 100);
    }
});

// Add CSS for ripple effect and pulse animation
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .btn-action {
        position: relative;
        overflow: hidden;
    }
    
    .status-badge {
        transition: all 0.3s ease;
    }
    
    .status-badge:hover {
        transform: scale(1.05);
    }
`;
document.head.appendChild(style);
