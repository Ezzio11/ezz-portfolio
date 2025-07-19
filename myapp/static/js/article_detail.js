document.addEventListener("DOMContentLoaded", function () {
    // Table of Contents generation (existing code)
    const tocList = document.getElementById("toc-list");
    const articleBody = document.querySelector(".article-body");
    const tocToggle = document.getElementById("toc-toggle");

    if (tocList && articleBody) {
        const headings = articleBody.querySelectorAll("h2, h3");
        headings.forEach((heading, idx) => {
            const text = heading.innerText;
            const slug = "toc-" + idx;
            heading.id = slug;

            const li = document.createElement("li");
            const a = document.createElement("a");
            a.href = "#" + slug;
            a.innerText = text;

            li.appendChild(a);
            tocList.appendChild(li);
        });
    }

    // TOC toggle functionality (existing code)
    if (tocToggle) {
        tocToggle.addEventListener("click", function () {
            tocList.classList.toggle("hidden");
            tocToggle.innerText = tocList.classList.contains("hidden") ? "📁" : "📂";
        });
    }

    // Enhanced comment form handling
    const commentForm = document.querySelector('.comment-form form');
    if (commentForm) {
        commentForm.addEventListener('submit', async function(e) {
            // Check if JavaScript is working
            const isJsWorking = true;
            
            if (!isJsWorking) {
                return; // Let the form submit normally
            }
            
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Posting...';
            
            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Force page reload to ensure consistency
                    window.location.href = `${window.location.pathname}?comment_success=true#comments`;
                } else {
                    window.location.href = `${window.location.pathname}?comment_error=true#comments`;
                }
            } catch (error) {
                console.error('Error:', error);
                // Fallback to regular form submission if AJAX fails
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
            document.getElementById('comments').scrollIntoView({
                behavior: 'smooth'
            });
        }, 100);
    }
});