document.addEventListener("DOMContentLoaded", function () {
    // Table of Contents generation
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

    // TOC toggle functionality
    if (tocToggle) {
        tocToggle.addEventListener("click", function () {
            tocList.classList.toggle("hidden");
            tocToggle.innerText = tocList.classList.contains("hidden") ? "📁" : "📂";
        });
    }

    // Form submission handling
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Posting...';
            }
        });
    }
});