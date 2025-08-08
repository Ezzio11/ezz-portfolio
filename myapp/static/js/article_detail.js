// Initialize Supabase client first
const initializeSupabase = () => {
    const supabaseUrl = "https://gefqshdrgozkxdiuligl.supabase.co";
    const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdlZnFzaGRyZ296a3hkaXVsaWdsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM0NjgyNDMsImV4cCI6MjA1OTA0NDI0M30.QJbcNl479A5_tdq8lqNubMQS26fkwcPyk-zvTU0Ffy0";
    return supabase.createClient(supabaseUrl, supabaseKey);
};

// Main initialization when DOM is ready
document.addEventListener("DOMContentLoaded", async function() {
    // Check if Supabase is loaded, load it dynamically if not
    if (typeof supabase === 'undefined') {
        await new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
            script.onload = resolve;
            document.head.appendChild(script);
        });
    }

    const supabaseClient = initializeSupabase();

    // Mobile menu toggle
    document.getElementById('mobileMenuButton')?.addEventListener('click', function() {
        document.getElementById('sidebar')?.classList.toggle('open');
    });

    // Day/Night Toggle
    document.getElementById('themeToggle')?.addEventListener('click', function() {
        document.documentElement.classList.toggle('dark');
        const icon = this.querySelector('svg');
        if (document.documentElement.classList.contains('dark')) {
            icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />`;
        } else {
            icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />`;
        }
    });

    // Sound Toggle
    const soundToggle = document.getElementById('soundToggle');
    if (soundToggle) {
        let audio = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-ambient-study-loop-258.mp3');
        audio.loop = true;
        
        soundToggle.addEventListener('click', function() {
            if (audio.paused) {
                audio.play();
                soundToggle.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-goldaccent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" clip-rule="evenodd" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14a2 2 0 100-4 2 2 0 000 4z" />
                    </svg>
                `;
            } else {
                audio.pause();
                soundToggle.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-goldaccent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072M12 6a7.975 7.975 0 015.657 2.343m0 0a7.975 7.975 0 010 11.314m-11.314 0a7.975 7.975 0 010-11.314m0 0a7.975 7.975 0 015.657-2.343" />
                    </svg>
                `;
            }
        });
    }

    // Initialize footnotes
    document.querySelectorAll('.footnote').forEach((fn, index) => {
        fn.setAttribute('data-number', index + 1);
    });

    // Load other readings from Supabase
    async function loadOtherReadings() {
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
                if (data?.length > 0) {
                    container.innerHTML = data.map(article => `
                        <li class="mb-2">
                            <a href="/mstag/${article.slug}/" 
                               class="text-parchment/70 hover:text-goldaccent transition arabic">
                                ${article.title}
                            </a>
                        </li>
                    `).join('');
                } else {
                    container.innerHTML = '<li class="text-parchment/70">No recommendations available</li>';
                }
            }
        } catch (error) {
            console.error('Error loading other readings:', error);
            const container = document.getElementById('other-readings');
            if (container) {
                container.innerHTML = '<li class="text-parchment/70">Error loading recommendations</li>';
            }
        }
    }

    // Table of Contents generation
    function generateTOC() {
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
                
                // Add different styling for h2 and h3
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
                
                // Add elegant dot before each item
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
                    this.innerHTML = tocList.classList.contains("hidden") ? 
                        '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" /></svg>' : 
                        '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>';
                }
            });
        }
    }

    // Enhanced comment form handling
    const commentForm = document.querySelector('.comment-form');
    if (commentForm) {
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
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (!response.ok) throw new Error('Network response was not ok');
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    window.location.href = `${window.location.pathname}?comment_success=true#comments`;
                } else {
                    window.location.href = `${window.location.pathname}?comment_error=true#comments`;
                }
            } catch (error) {
                console.error('Error:', error);
                this.submit();
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Comment';
            }
        });
    }
    
    // Scroll to comments if anchor exists
    if (window.location.hash === '#comments') {
        setTimeout(() => {
            const commentsSection = document.getElementById('comments');
            if (commentsSection) {
                commentsSection.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        }, 100);
    }

    // Initialize components
    generateTOC();
    loadOtherReadings();
});