// Initialize Supabase client
const initializeSupabase = () => {
    const supabaseUrl = window.SUPABASE_URL;
    const supabaseKey = window.SUPABASE_KEY;
    return supabase.createClient(supabaseUrl, supabaseKey);
};

// Create dust particles
function createDustParticles() {
    const container = document.getElementById('dustContainer');
    if (!container) return;
    
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.className = 'dust-particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.width = (Math.random() * 3 + 1) + 'px';
        particle.style.height = particle.style.width;
        particle.style.opacity = Math.random() * 0.6 + 0.2;
        particle.style.animationDelay = Math.random() * 10 + 's';
        particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
        container.appendChild(particle);
    }
}

// Google Translate Widget Initialization
function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'ar',
        includedLanguages: 'en,es,fr,de,it,pt,ru,zh-CN,ja,ar',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false,
        gaTrack: false,
        gaId: '',
        multilanguagePage: true
    }, 'google_translate_element');
}

// Main initialization when DOM is ready
document.addEventListener("DOMContentLoaded", async function() {
    // Load Supabase if needed
    if (typeof supabase === 'undefined') {
        await new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
            script.onload = resolve;
            document.head.appendChild(script);
        });
    }

    const supabaseClient = initializeSupabase();
    createDustParticles();

    // Mobile menu toggle
    const setupMobileMenu = () => {
        const mobileMenuButton = document.getElementById('mobileMenuButton');
        const sidebar = document.getElementById('sidebar');
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        const sidebarCloseButton = document.getElementById('sidebarCloseButton');

        if (mobileMenuButton && sidebar) {
            mobileMenuButton.addEventListener('click', () => {
                sidebar.classList.toggle('translate-x-0');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.toggle('opacity-0');
                    sidebarOverlay.classList.toggle('pointer-events-none');
                }
                document.body.classList.toggle('overflow-hidden');
            });
        }

        if (sidebarCloseButton && sidebarOverlay) {
            sidebarCloseButton.addEventListener('click', () => {
                sidebar.classList.remove('translate-x-0');
                sidebarOverlay.classList.add('opacity-0');
                sidebarOverlay.classList.add('pointer-events-none');
                document.body.classList.remove('overflow-hidden');
            });
        }

        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                sidebar.classList.remove('translate-x-0');
                this.classList.add('opacity-0');
                this.classList.add('pointer-events-none');
                document.body.classList.remove('overflow-hidden');
            });
        }
    };
    setupMobileMenu();

    // Theme toggle
    const setupThemeToggle = () => {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;

        themeToggle.addEventListener('click', function() {
            document.documentElement.classList.toggle('dark');
            const icon = this.querySelector('svg');
            if (!icon) return;

            icon.innerHTML = document.documentElement.classList.contains('dark')
                ? `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />`
                : `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />`;
        });
    };
    setupThemeToggle();

    // Audio Player
    const setupAudioPlayer = () => {
        let audio;
        const volumeControl = document.getElementById('volumeControl');
        const soundToggle = document.getElementById('soundToggle');
        const playIcon = document.getElementById('playIcon');

        if (!volumeControl || !soundToggle || !playIcon) return;

        try {
            audio = new Audio('/static/audio/library-ambience.m4a');
            audio.volume = volumeControl.value;
            audio.loop = true;
            
            // Handle audio errors
            audio.addEventListener('error', () => {
                console.error('Audio load error, using fallback');
                audio.src = 'https://assets.mixkit.co/sfx/preview/mixkit-ambient-study-loop-258.mp3';
            });

            // Volume control
            volumeControl.addEventListener('input', () => {
                audio.volume = volumeControl.value;
            });

            // Play/pause toggle
            soundToggle.addEventListener('click', async () => {
                try {
                    if (audio.paused) {
                        await audio.play();
                        playIcon.innerHTML = `
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" 
                                clip-rule="evenodd" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M17 14a2 2 0 100-4 2 2 0 000 4z" />
                        `;
                    } else {
                        audio.pause();
                        playIcon.innerHTML = `
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M15.536 8.464a5 5 0 010 7.072M12 6a7.975 7.975 0 015.657 2.343m0 0a7.975 7.975 0 010 11.314m-11.314 0a7.975 7.975 0 010-11.314m0 0a7.975 7.975 0 015.657-2.343" />
                        `;
                    }
                } catch (error) {
                    console.error('Audio playback error:', error);
                }
            });

            // Mobile touch for volume
            if ('ontouchstart' in window) {
                let touchTimer;
                soundToggle.addEventListener('touchstart', () => {
                    touchTimer = setTimeout(() => {
                        volumeControl.classList.toggle('w-0');
                        volumeControl.classList.toggle('opacity-0');
                        volumeControl.classList.toggle('w-[100px]');
                        volumeControl.classList.toggle('opacity-100');
                    }, 500);
                }, { passive: true });

                soundToggle.addEventListener('touchend', () => {
                    clearTimeout(touchTimer);
                }, { passive: true });
            }

            // Try autoplay with fallback
            const playAudio = async () => {
                try {
                    await audio.play();
                } catch (err) {
                    console.log("Auto-play blocked, waiting for interaction");
                }
            };
            
            document.addEventListener('click', () => playAudio(), { once: true });
            playAudio();

        } catch (error) {
            console.error('Audio initialization failed:', error);
        }
    };
    setupAudioPlayer();

    // Initialize footnotes
    document.querySelectorAll('.footnote').forEach((fn, index) => {
        fn.setAttribute('data-number', index + 1);
    });

    // Load other readings from Supabase
    const loadOtherReadings = async () => {
        try {
            const pathSegments = window.location.pathname.split('/');
            const currentSlug = pathSegments[pathSegments.length - 1];
            
            const { data, error } = await supabaseClient
                .from('articles')
                .select('id, title, slug')
                .order('date_published', { ascending: false })
                .limit(3)
                .neq('slug', currentSlug);
            
            if (error) throw error;
            
            const container = document.getElementById('other-readings');
            if (container) {
                container.innerHTML = data?.length > 0
                    ? data.map(article => `
                        <li class="mb-2">
                            <a href="/mstag/${article.slug}/" 
                               class="text-parchment/70 hover:text-goldaccent transition arabic">
                                ${article.title}
                            </a>
                        </li>
                    `).join('')
                    : '<li class="text-parchment/70">No recommendations available</li>';
            }
        } catch (error) {
            console.error('Error loading other readings:', error);
            const container = document.getElementById('other-readings');
            if (container) {
                container.innerHTML = '<li class="text-parchment/70">Error loading recommendations</li>';
            }
        }
    };

    // Table of Contents generation
    const generateTOC = () => {
        const tocList = document.getElementById("toc-list");
        const articleBody = document.querySelector(".article-body");
        const tocToggle = document.getElementById("toc-toggle");

        if (tocList && articleBody) {
            tocList.innerHTML = '';
            
            const headings = articleBody.querySelectorAll("h2, h3");
            let currentH2 = null;
            
            headings.forEach((heading, idx) => {
                const text = heading.innerText;
                const slug = "toc-" + idx;
                heading.id = slug;

                const li = document.createElement("li");
                li.className = "mb-1";
                
                const a = document.createElement("a");
                a.href = "#" + slug;
                a.innerText = text;
                a.className = "text-parchment/70 hover:text-goldaccent transition flex items-start";
                
                if (heading.tagName === "H2") {
                    a.className += " font-medium";
                    li.className += " mt-3";
                    currentH2 = li;
                } else {
                    a.className += " text-sm ml-4";
                    if (currentH2) {
                        const sublist = currentH2.querySelector("ul") || document.createElement("ul");
                        sublist.className = "mt-1 space-y-1";
                        sublist.appendChild(li);
                        if (!currentH2.querySelector("ul")) {
                            currentH2.appendChild(sublist);
                        }
                        return;
                    }
                }
                
                const dot = document.createElement("span");
                dot.className = "inline-block w-2 h-2 rounded-full bg-goldaccent mr-2 mt-2";
                a.prepend(dot);
                
                li.appendChild(a);
                tocList.appendChild(li);
            });
        }

        if (tocToggle) {
            tocToggle.addEventListener("click", function() {
                const tocList = document.getElementById("toc-list");
                if (tocList) {
                    tocList.classList.toggle("hidden");
                    this.innerHTML = tocList.classList.contains("hidden") 
                        ? '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" /></svg>' 
                        : '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>';
                }
            });
        }
    };

    // Enhanced comment form handling
    const setupCommentForm = () => {
        const commentForm = document.querySelector('.comment-form');
        if (!commentForm) return;

        commentForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Posting...';
            
            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                
                if (!response.ok) throw new Error('Network response was not ok');
                
                const data = await response.json();
                window.location.href = `${window.location.pathname}?comment_${data.status === 'success' ? 'success' : 'error'}=true#comments`;
            } catch (error) {
                console.error('Error:', error);
                this.submit();
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Comment';
            }
        });
    };

    // Card hover effects
    const setupCardHover = () => {
        const cards = document.querySelectorAll('.card-hover');
        
        document.addEventListener('mousemove', (e) => {
            cards.forEach(card => {
                const rect = card.getBoundingClientRect();
                card.style.setProperty('--x', (e.clientX - rect.left) + 'px');
                card.style.setProperty('--y', (e.clientY - rect.top) + 'px');
            });
        });
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.opacity = 1;
                        entry.target.style.transform = 'translateY(0)';
                    }, 100 * index);
                }
            });
        }, { threshold: 0.1 });
        
        cards.forEach(card => {
            card.style.opacity = 0;
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(card);
        });
    };

    // Google Translate dropdown
    const setupLanguageSelect = () => {
        const languageSelect = document.getElementById('language-select');
        if (!languageSelect) return;
    
        const getCookie = (name) => {
            const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
            return match ? match[2] : null;
        };
    
        const googtrans = getCookie('googtrans');
        if (googtrans) {
            const lang = googtrans.split('/')[2];
            if (lang) {
                languageSelect.value = lang;
            }
        }
    
        languageSelect.addEventListener('change', function() {
            if (this.value === 'ar') {
                document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            } else {
                document.cookie = `googtrans=/ar/${this.value}; path=/;`;
            }
            location.reload();
        });
    };

    // Initialize all components
    loadOtherReadings();
    generateTOC();
    setupCommentForm();
    setupCardHover();
    setupLanguageSelect();

    // Scroll to comments if anchor exists
    if (window.location.hash === '#comments') {
        setTimeout(() => {
            const commentsSection = document.getElementById('comments');
            if (commentsSection) {
                commentsSection.scrollIntoView({ behavior: 'smooth' });
            }
        }, 100);
    }

});

