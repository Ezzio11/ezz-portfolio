(function ($) {
    "use strict";

    // Initialize all functions when DOM is ready
    $(document).ready(function() {
        initAnimusBackground();
        setupDarkMode();
        setupBackToTop();
        setupTestimonialCarousel();
        setupContactForm();
        setupReadMore();
        setupChatbot();
        setupChatBubble(); // New function for chat bubble
    });

    function setupChatBubble() {
        const bubble = $('#chatbot-bubble');
        let isDragging = false;
        let offsetX = 0, offsetY = 0;
        let lastX = 0, lastY = 0;
        let velocityX = 0, velocityY = 0;
        const dragThreshold = 5;
        const friction = 0.9;

        // Handle both mouse and touch events
        bubble.on('mousedown touchstart', startDrag);

        function startDrag(e) {
            e.preventDefault();
            const clientX = e.clientX || e.originalEvent.touches[0].clientX;
            const clientY = e.clientY || e.originalEvent.touches[0].clientY;
            
            const rect = bubble[0].getBoundingClientRect();
            offsetX = clientX - rect.left;
            offsetY = clientY - rect.top;
            
            isDragging = true;
            bubble.addClass('dragging');
            
            lastX = clientX;
            lastY = clientY;
            
            document.body.style.userSelect = 'none';
            
            // Attach move and end events
            $(document)
                .on('mousemove.chatbubble touchmove.chatbubble', dragMove)
                .on('mouseup.chatbubble touchend.chatbubble', endDrag);
        }

        function dragMove(e) {
            if (!isDragging) return;
            e.preventDefault();
            
            const clientX = e.clientX || e.originalEvent.touches[0].clientX;
            const clientY = e.clientY || e.originalEvent.touches[0].clientY;
            
            velocityX = clientX - lastX;
            velocityY = clientY - lastY;
            lastX = clientX;
            lastY = clientY;
            
            bubble.css({
                'left': (clientX - offsetX) + 'px',
                'top': (clientY - offsetY) + 'px',
                'right': 'auto',
                'bottom': 'auto'
            });
        }

        function endDrag(e) {
            if (!isDragging) return;
            isDragging = false;
            bubble.removeClass('dragging');
            document.body.style.userSelect = '';
            
            if (Math.abs(velocityX) > 2 || Math.abs(velocityY) > 2) {
                applyMomentum();
            } else {
                checkBoundaries();
            }
            
            // Don't remove the document listeners here
            // They'll be cleaned up when new drag starts
        }

        function applyMomentum() {
            let currentX = parseInt(bubble.css('left')) || 0;
            let currentY = parseInt(bubble.css('top')) || 0;
            
            const animateMomentum = () => {
                velocityX *= friction;
                velocityY *= friction;
                
                currentX += velocityX;
                currentY += velocityY;
                
                bubble.css({
                    'left': currentX + 'px',
                    'top': currentY + 'px'
                });
                
                if (Math.abs(velocityX) > 0.5 || Math.abs(velocityY) > 0.5) {
                    requestAnimationFrame(animateMomentum);
                } else {
                    checkBoundaries();
                }
            };
            
            requestAnimationFrame(animateMomentum);
        }

        function checkBoundaries() {
            const rect = bubble[0].getBoundingClientRect();
            const windowWidth = window.innerWidth;
            const windowHeight = window.innerHeight;
            
            let newLeft = parseInt(bubble.css('left')) || 0;
            let newTop = parseInt(bubble.css('top')) || 0;
            
            if (newLeft < 0) newLeft = 0;
            if (newLeft + rect.width > windowWidth) newLeft = windowWidth - rect.width;
            if (newTop < 0) newTop = 0;
            if (newTop + rect.height > windowHeight) newTop = windowHeight - rect.height;
            
            const snapThreshold = 20;
            if (newLeft < snapThreshold) newLeft = 0;
            if (windowWidth - (newLeft + rect.width) < snapThreshold) newLeft = windowWidth - rect.width;
            if (newTop < snapThreshold) newTop = 0;
            if (windowHeight - (newTop + rect.height) < snapThreshold) newTop = windowHeight - rect.height;
            
            bubble.animate({
                'left': newLeft + 'px',
                'top': newTop + 'px'
            }, 200, 'easeOutQuad');
        }

        // Handle click separately
        bubble.on('click', function(e) {
            if (bubble.hasClass('dragging')) {
                e.stopImmediatePropagation();
                bubble.removeClass('dragging');
                return false;
            }
        });
    }

    function setupChatbot() {
        // DOM elements
        const bubble = $('#chatbot-bubble');
        const window = $('#chatbot-window');
        const closeBtn = $('#chatbot-close');
        const sendBtn = $('#chatbot-send');
        const input = $('#chatbot-input');
        const messagesContainer = $('#chatbot-messages');
        
        // Toggle chat window
        bubble.on('click', function() {
            window.toggle();
            if (window.is(':visible')) {
                input.focus();
            }
        });
        
        // Close chat window
        closeBtn.on('click', function(e) {
            e.stopPropagation();
            window.hide();
        });
        
        // Send message on button click
        sendBtn.on('click', sendMessage);
        
        // Send message on Enter key
        input.on('keypress', function(e) {
            if (e.which === 13) { // Enter key
                sendMessage();
            }
        });
        
        // Load chat history from localStorage
        loadChatHistory();
        
        // Add welcome message if first interaction
        if (!localStorage.getItem('chatbotFirstInteraction')) {
            addBotMessage("Hello! I'm XANE, your AI assistant. How can I help you today?");
            localStorage.setItem('chatbotFirstInteraction', 'true');
        }
        
        function sendMessage() {
            const message = $('#chatbot-input').val().trim();
            if (!message) return;

            // Add user message
            addUserMessage(message);
            $('#chatbot-input').val('');
            
            // Show typing indicator
            const typingIndicator = $(`
                <div class="message bot-message typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `);
            $('#chatbot-messages').append(typingIndicator);
            $('#chatbot-messages').scrollTop($('#chatbot-messages')[0].scrollHeight);

            // Get CSRF token
            const csrfToken = $('[name=csrfmiddlewaretoken]').val();
            
            // Make the AJAX request
            $.ajax({
                type: 'POST',
                url: '/chatbot/',
                data: {
                    message: message,
                    csrfmiddlewaretoken: csrfToken
                },
                dataType: 'json',
                success: function(data) {
                    typingIndicator.remove();
                    if (data && data.response) {
                        addBotMessage(data.response);
                    } else {
                        addBotMessage("Sorry, I didn't get a proper response.");
                    }
                },
                error: function(xhr, status, error) {
                    typingIndicator.remove();
                    let errorMsg = "Sorry, I'm having trouble responding right now.";
                    try {
                        if (xhr.responseJSON && xhr.responseJSON.response) {
                            errorMsg = xhr.responseJSON.response;
                        }
                    } catch (e) {
                        console.error('Error parsing response:', e);
                    }
                    addBotMessage(errorMsg);
                    console.error('Chatbot error:', status, error);
                }
            });
        }
        
        function addUserMessage(message) {
            const messageElement = $(`
                <div class="message user-message">
                    ${message}
                    <div class="message-time">${getCurrentTime()}</div>
                </div>
            `);
            messagesContainer.append(messageElement);
            messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
        }
        
        function addBotMessage(message) {
            const messageElement = $(`
                <div class="message bot-message">
                    ${message}
                    <div class="message-time">${getCurrentTime()}</div>
                </div>
            `);
            messagesContainer.append(messageElement);
            messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
        }
        
        function getCurrentTime() {
            const now = new Date();
            return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        
        function saveChatHistory() {
            const messages = [];
            messagesContainer.find('.message').each(function() {
                const isUser = $(this).hasClass('user-message');
                messages.push({
                    type: isUser ? 'user' : 'bot',
                    content: $(this).clone().find('.message-time').remove().end().text().trim(),
                    time: $(this).find('.message-time').text()
                });
            });
            localStorage.setItem('chatbotHistory', JSON.stringify(messages));
        }
        
        function loadChatHistory() {
            const history = localStorage.getItem('chatbotHistory');
            if (history) {
                const messages = JSON.parse(history);
                messages.forEach(msg => {
                    if (msg.type === 'user') {
                        addUserMessage(msg.content);
                    } else {
                        addBotMessage(msg.content);
                    }
                });
            }
        }
    }

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
            homeIcon?.classList.replace('fa-moon', 'fa-sun');
        }
    
        // Toggle dark mode
        document.getElementById('dark-mode-toggle')?.addEventListener('click', function () {
            body.classList.toggle('dark-mode');
            animusBg.classList.toggle('dark-mode');
            
            if (body.classList.contains('dark-mode')) {
                homeIcon?.classList.replace('fa-moon', 'fa-sun');
                localStorage.setItem('darkMode', 'enabled');
            } else {
                homeIcon?.classList.replace('fa-sun', 'fa-moon');
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
