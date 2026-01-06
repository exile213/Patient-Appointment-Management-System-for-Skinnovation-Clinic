// Attendant Dashboard Interactive Features
document.addEventListener('DOMContentLoaded', function() {
    // Add loading animation to stats cards
    const statsCards = document.querySelectorAll('.stats-card');
    statsCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease-out';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 200);
    });
    
    // Add hover effects to appointment cards
    const appointmentCards = document.querySelectorAll('.appointment-card');
    appointmentCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add click animation to buttons
    const buttons = document.querySelectorAll('.btn');
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
    
    // Add typing animation to welcome text
    const welcomeText = document.querySelector('.dashboard-welcome h2');
    if (welcomeText) {
        const text = welcomeText.textContent;
        welcomeText.textContent = '';
        let i = 0;
        
        const typeWriter = () => {
            if (i < text.length) {
                welcomeText.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            }
        };
        
        setTimeout(typeWriter, 500);
    }
    
    // Add notification count animation
    const notificationBadge = document.querySelector('.notification-badge');
    if (notificationBadge) {
        const count = parseInt(notificationBadge.textContent);
        if (count > 0) {
            notificationBadge.classList.add('pulse');
        }
    }
    
    // Add smooth scroll to sections
    const quickActionButtons = document.querySelectorAll('.btn[href^="#"]');
    quickActionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add real-time clock
    const updateClock = () => {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // Update any clock elements if they exist
        const clockElements = document.querySelectorAll('.current-time');
        clockElements.forEach(element => {
            element.textContent = timeString;
        });
    };
    
    // Update clock every second
    setInterval(updateClock, 1000);
    updateClock(); // Initial call
    
    // Add fade-in animation to content
    const content = document.querySelector('.fade-in');
    if (content) {
        content.style.opacity = '0';
        content.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            content.style.transition = 'all 0.8s ease-out';
            content.style.opacity = '1';
            content.style.transform = 'translateY(0)';
        }, 100);
    }
    
    // Add animation to quick action buttons
    const quickActionButtons = document.querySelectorAll('.quick-action-btn');
    quickActionButtons.forEach((button, index) => {
        button.style.opacity = '0';
        button.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            button.style.transition = 'all 0.6s ease-out';
            button.style.opacity = '1';
            button.style.transform = 'translateY(0)';
        }, 300 + (index * 150));
    });
    
    // Add click animation to quick action buttons
    quickActionButtons.forEach(button => {
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
});

// Add CSS for ripple effect
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
    
    .current-time {
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
`;
document.head.appendChild(style);
