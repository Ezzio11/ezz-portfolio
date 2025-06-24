(function ($) {
    "use strict";

    // Initialize all functions when DOM is ready
    $(document).ready(function() {
        initAnimusBackground();
        setupDarkMode();
        setupBackToTop();
        setupTestimonialCarousel();
        setupContactForm();
        setupReadMore(); // New function added here
    });

    // Animus Background Initialization
    function initAnimusBackground() {
        // Create container for animus background
        const animusBg = document.createElement('div');
        animusBg.className = 'animus-background';
        
        // Create grid
        const grid = document.createElement('div');
        grid.className = 'animus-grid';
        
        // Create scanline
        const scanline = document.createElement('div');
        scanline.className = 'animus-scanline';
        
        // Create particles container
        const particles = document.createElement('div');
        particles.className = 'animus-particles';
        
        // Add elements to container
        animusBg.appendChild(grid);
        animusBg.appendChild(scanline);
        animusBg.appendChild(particles);
        
        // Add to body
        document.body.insertBefore(animusBg, document.body.firstChild);
        
        // Create particles
        createParticles(particles);
    }

    function createParticles(container) {
        const particleCount = 50;
        const colors = [
            'rgba(0, 162, 255, 0.7)', 
            'rgba(0, 255, 255, 0.5)', 
            'rgba(100, 220, 255, 0.3)',
            'rgba(0, 180, 255, 0.8)'
        ];
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'animus-particle';
            
            // Random properties with larger size range
            const size = Math.random() * 6 + 2;
            const posX = Math.random() * 100;
            const posY = Math.random() * 100 + 100;
            const duration = Math.random() * 10 + 5;
            const delay = Math.random() * 15;
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            // Apply styles
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${posX}%`;
            particle.style.top = `${posY}%`;
            particle.style.animationDuration = `${duration}s`;
            particle.style.animationDelay = `-${delay}s`;
            particle.style.backgroundColor = color;
            
            // Add glow effect to larger particles
            if (size > 4) {
                particle.style.boxShadow = `0 0 ${size}px ${size/2}px rgba(0, 200, 255, 0.3)`;
            }
            
            container.appendChild(particle);
        }
    }

    // Dark mode setup
    function setupDarkMode() {
        const body = document.body;
        const animusBg = document.querySelector('.animus-background');
        const homeIcon = document.getElementById('dark-mode-icon');
        
        // Check for saved preference
        if (localStorage.getItem('darkMode') === 'enabled') {
            body.classList.add('dark-mode');
            animusBg.classList.add('dark-mode');
            homeIcon.classList.replace('fa-moon', 'fa-sun');
        }

        // Toggle dark mode
        document.getElementById('dark-mode-toggle').addEventListener('click', function () {
            body.classList.toggle('dark-mode');
            animusBg.classList.toggle('dark-mode');
            
            if (body.classList.contains('dark-mode')) {
                homeIcon.classList.replace('fa-moon', 'fa-sun');
                localStorage.setItem('darkMode', 'enabled');
            } else {
                homeIcon.classList.replace('fa-sun', 'fa-moon');
                localStorage.setItem('darkMode', 'disabled');
            }
        });
    }
    
    // Back to top button
    function setupBackToTop() {
        $(window).scroll(function () {
            if ($(this).scrollTop() > 300) {
                $('.back-to-top').fadeIn('slow');
            } else {
                $('.back-to-top').fadeOut('slow');
            }
        });
        
        $('.back-to-top').click(function () {
            $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
            return false;
        });
    }

    // Testimonial carousel
    function setupTestimonialCarousel() {
        $(".testimonial-carousel").owlCarousel({
            autoplay: true,
            smartSpeed: 1500,
            center: true,
            dots: true,
            loop: true,
            margin: 0,
            nav: true,
            navText: false,
            responsiveClass: true,
            responsive: {
                0:{ items:1 },
                576:{ items:1 },
                768:{ items:2 },
                992:{ items:3 }
            }
        });
    }

    // Contact form AJAX submission
    function setupContactForm() {
        $('form').on('submit', function(e) {
            e.preventDefault();
            console.log('AJAX form submission initiated');
            
            var form = $(this);
            var submitButton = form.find('button[type="submit"]');
            
            // Disable submit button
            submitButton.prop('disabled', true);
            submitButton.html('<span class="spinner-border spinner-border-sm"></span> Sending...');
            
            $.ajax({
                type: 'POST',
                url: form.attr('action'),
                data: form.serialize(),
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": $('[name=csrfmiddlewaretoken]').val()
                },
                dataType: 'json',
                success: function(response) {
                    showAlert('success', response.message);
                    form.trigger('reset');
                },
                error: function(xhr) {
                    var errorMsg = xhr.responseJSON && xhr.responseJSON.message 
                        ? xhr.responseJSON.message 
                        : 'An error occurred. Please try again.';
                    showAlert('danger', errorMsg);
                },
                complete: function() {
                    submitButton.prop('disabled', false);
                    submitButton.text('Send Message');
                }
            });
        });

        function showAlert(type, message) {
            // Remove existing alerts
            $('.alert-dismissible').remove();
            
            // Create new alert
            var alert = $(`
                <div class="alert alert-${type} alert-dismissible fade show mb-4">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `);
            
            // Insert and scroll to alert
            $('form').before(alert);
            $('html, body').animate({
                scrollTop: alert.offset().top - 100
            }, 500);
        }
    }

    // Read More functionality for testimonials
function setupReadMore() {
    $('.read-more-btn').on('click', function(e) {
        e.preventDefault();
        const $textContainer = $(this).prev('.testimonial-text');
        const $button = $(this);
        
        // Toggle the expanded class
        $textContainer.toggleClass('expanded');
        
        // Check current state and update button text
        if ($textContainer.hasClass('expanded')) {
            $button.text('Read Less');
            // Remove line clamping when expanded
            $textContainer.css({
                '-webkit-line-clamp': 'unset',
                'display': 'block'
            });
        } else {
            $button.text('Read More');
            // Reapply line clamping when collapsed
            $textContainer.css({
                '-webkit-line-clamp': '3',
                'display': '-webkit-box'
            });
        }
    });
}

})(jQuery);
