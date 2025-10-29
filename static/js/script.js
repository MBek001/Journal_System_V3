// script.js - Main JavaScript file for all pages

document.addEventListener('DOMContentLoaded', function () {
    // Initialize all components
    function init() {
        initCounterAnimation();
        initSmoothScrolling();
        initMobileMenu();
        initBackToTop();
        initFileUpload();
        initFormValidation();
        initContactForm();
        initPublisherNavigation();
        initCardHoverEffects();
        initAuthorSearch();
        initJournalSearch();
        initJournalNavigation();
        initArticleNavigation();
        initJournalDetailNavigation();
        initPolicyToggle();
        initArticlesListFilters();
        initArticleCardAnimations();
        highlightSearchTerms();
    }

    // Animate statistics counters
    function initCounterAnimation() {
        const counters = document.querySelectorAll('.stat-value[data-count]');
        if (counters.length === 0) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, {threshold: 0.1});

        counters.forEach(counter => {
            observer.observe(counter);
        });
    }

    function animateCounter(counterElement) {
        const target = parseInt(counterElement.getAttribute('data-count')) || 0;
        if (target === 0) return;

        const duration = 2000; // ms
        let start = 0;
        const increment = target / (duration / 16);
        const timer = setInterval(() => {
            start += increment;
            if (start >= target) {
                counterElement.textContent = target.toLocaleString();
                clearInterval(timer);
            } else {
                counterElement.textContent = Math.floor(start).toLocaleString();
            }
        }, 16);
    }

    function initJournalSearch() {
        const searchInput = document.getElementById('journal-search');
        const journalCards = document.querySelectorAll('.journal-card');

        // Sahifa yuklanganda, agar qidiruv maydonida qiymat bo'lsa, filtr qilish
        if (searchInput && journalCards.length > 0) {
            const filterJournals = () => {
                const searchTerm = searchInput.value.toLowerCase().trim();

                journalCards.forEach(card => {
                    const title = (card.dataset.title || '').toLowerCase();
                    // Qidiruv faqat sarlavhada amal qiladi, kerak bo'lsa boshqalarda ham qo'shish mumkin
                    if (searchTerm === '' || title.includes(searchTerm)) {
                        card.style.display = ''; // Ko'rsatish
                    } else {
                        card.style.display = 'none'; // Yashirish
                    }
                });
            };

            searchInput.addEventListener('input', filterJournals);

            filterJournals();
        }
    }


    // Initialize smooth scrolling for anchor links
    function initSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                if (targetId === '#' || targetId === '') return;

                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    window.scrollTo({
                        top: targetElement.offsetTop - 100,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    // Initialize mobile menu behavior
    function initMobileMenu() {
        const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
        const navbar = document.getElementById('navbarNav');

        if (mobileMenuBtn && navbar) {
            mobileMenuBtn.addEventListener('click', function () {
                navbar.classList.toggle('show');
            });
        }

        // Close mobile menu when clicking a nav link
        document.querySelectorAll('#navbarNav .nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (navbar.classList.contains('show')) {
                    navbar.classList.remove('show');
                }
            });
        });
    }

    // Initialize back to top button
    function initBackToTop() {
        const backToTopButton = document.getElementById('back-to-top');
        if (!backToTopButton) return;

        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopButton.style.display = 'flex';
            } else {
                backToTopButton.style.display = 'none';
            }
        });

        backToTopButton.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }


    // Initialize form validation
    function initFormValidation() {
        const forms = document.querySelectorAll('form.needs-validation');

        Array.from(forms).forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }

                form.classList.add('was-validated');
            }, false);
        });
    }

    // Initialize contact form
    function initContactForm() {
        const contactForm = document.querySelector('.contact-form form');
        if (!contactForm) return;

        contactForm.addEventListener('submit', function (e) {
            const nameInput = this.querySelector('input[name="name"]');
            const emailInput = this.querySelector('input[name="email"]');
            const subjectInput = this.querySelector('input[name="subject"]');
            const messageInput = this.querySelector('textarea[name="message"]');

            let isValid = true;

            // Simple validation
            if (!nameInput.value.trim()) {
                isValid = false;
                nameInput.classList.add('is-invalid');
            } else {
                nameInput.classList.remove('is-invalid');
            }

            if (!emailInput.value.trim() || !/^\S+@\S+\.\S+$/.test(emailInput.value)) {
                isValid = false;
                emailInput.classList.add('is-invalid');
            } else {
                emailInput.classList.remove('is-invalid');
            }

            if (!subjectInput.value.trim()) {
                isValid = false;
                subjectInput.classList.add('is-invalid');
            } else {
                subjectInput.classList.remove('is-invalid');
            }

            if (!messageInput.value.trim()) {
                isValid = false;
                messageInput.classList.add('is-invalid');
            } else {
                messageInput.classList.remove('is-invalid');
            }

            if (!isValid) {
                e.preventDefault();
                e.stopPropagation();

                // Show error message
                const errorContainer = document.createElement('div');
                errorContainer.className = 'alert alert-danger';
                errorContainer.textContent = 'Iltimos, barcha maydonlarni to\'ldiring!';
                this.insertBefore(errorContainer, this.firstChild);

                setTimeout(() => {
                    errorContainer.remove();
                }, 5000);
            }
        });
    }

    // Initialize publisher navigation
    function initPublisherNavigation() {
        const navItems = document.querySelectorAll('.publisher-category .category-item');

        navItems.forEach(item => {
            item.addEventListener('click', function () {
                // Remove active class from all items
                document.querySelectorAll('.category-item').forEach(i => {
                    i.classList.remove('active');
                });

                // Add active class to clicked item
                this.classList.add('active');

                // In a real implementation, this would load content
                console.log('Loading publisher content:', this.textContent);
            });
        });
    }

    // Initialize card hover effects for Imfaktor style
    function initCardHoverEffects() {
        const cards = document.querySelectorAll('.card');

        cards.forEach(card => {
            const overlay = card.querySelector('.overlay');
            const image = card.querySelector('.journal-cover');

            if (overlay && image) {
                card.addEventListener('mouseenter', () => {
                    overlay.style.background = 'rgba(0, 109, 119, 0.2)';
                    const icon = overlay.querySelector('i');
                    if (icon) icon.style.opacity = '1';
                    image.style.transform = 'scale(1.03)';
                });

                card.addEventListener('mouseleave', () => {
                    overlay.style.background = 'rgba(0, 109, 119, 0)';
                    const icon = overlay.querySelector('i');
                    if (icon) icon.style.opacity = '0';
                    image.style.transform = 'scale(1)';
                });
            }
        });
    }

    // Initialize author search
    function initAuthorSearch() {
        const searchInput = document.getElementById('author-search');
        const searchButton = document.getElementById('author-search-btn');
        const authorCards = document.querySelectorAll('.author-card-item');

        if (!searchInput || authorCards.length === 0) {
            return;
        }

        const filterAuthors = () => {
            const searchTerm = searchInput.value.toLowerCase().trim();

            authorCards.forEach(card => {
                const authorName = (card.dataset.name || '').toLowerCase();

                if (searchTerm === '' || authorName.includes(searchTerm)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        };

        searchInput.addEventListener('input', filterAuthors);

        if (searchButton) {
            searchButton.addEventListener('click', function (event) {
                // event.preventDefault(); // Uncomment if button should only filter, not submit form
                filterAuthors();
            });
        }

        filterAuthors();
    }

    (function () {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initAuthorSearch);
        } else {
            initAuthorSearch();
        }
    })();

    // Journal card navigation
    function initJournalNavigation() {
        const journalCards = document.querySelectorAll('.journal-card');

        journalCards.forEach(card => {
            card.addEventListener('click', function (e) {
                // Don't navigate if clicking on buttons or links
                if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                    return;
                }

                const link = this.querySelector('a[href*="journal_detail"]');
                if (link) {
                    window.location.href = link.href;
                }
            });
        });
    }

    // Article title navigation
    function initArticleNavigation() {
        const articleCards = document.querySelectorAll('.article-card');

        articleCards.forEach(card => {
            card.addEventListener('click', function (e) {
                // Don't navigate if clicking on buttons
                if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                    return;
                }

                const link = this.querySelector('a[href*="article_detail"]');
                if (link) {
                    window.location.href = link.href;
                }
            });
        });
    }

    // Journal detail page navigation
    function initJournalDetailNavigation() {
        const navButtons = document.querySelectorAll('.nav-button-journal');
        const sections = document.querySelectorAll('.content-section-journal');

        navButtons.forEach(button => {
            button.addEventListener('click', function () {
                const targetSection = this.getAttribute('data-section');

                // Hide all sections
                sections.forEach(section => {
                    section.classList.remove('active');
                });

                // Remove active class from all buttons
                navButtons.forEach(btn => {
                    btn.classList.remove('active');
                });

                // Show target section
                if (targetSection) {
                    document.getElementById(targetSection).classList.add('active');
                }

                // Add active class to clicked button
                this.classList.add('active');
            });
        });
    }

    // Policy toggle functionality
    function initPolicyToggle() {
        const policyHeaders = document.querySelectorAll('.policy-header-journal');

        policyHeaders.forEach(header => {
            header.addEventListener('click', function () {
                const content = this.nextElementSibling;
                const icon = this.querySelector('.policy-toggle') || this.querySelector('i');

                if (content.classList.contains('active')) {
                    content.classList.remove('active');
                    if (icon) {
                        icon.classList.remove('fa-chevron-up');
                        icon.classList.add('fa-chevron-down');
                    }
                } else {
                    // Close all other policies
                    document.querySelectorAll('.policy-content-journal').forEach(el => {
                        el.classList.remove('active');
                    });
                    document.querySelectorAll('.policy-header-journal i').forEach(i => {
                        i.classList.remove('fa-chevron-up');
                        i.classList.add('fa-chevron-down');
                    });

                    // Open clicked policy
                    content.classList.add('active');
                    if (icon) {
                        icon.classList.remove('fa-chevron-down');
                        icon.classList.add('fa-chevron-up');
                    }
                }
            });
        });
    }

    function initArticlesListFilters() {
        const filterForm = document.getElementById('articles-filter-form');
        if (!filterForm) return;

        const filterSelects = filterForm.querySelectorAll('select');
        filterSelects.forEach(select => {
            select.addEventListener('change', function () {
                filterForm.submit();
            });
        });

        // Optional: Submit on Enter in search box
        const searchInput = filterForm.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    filterForm.submit();
                }
            });
        }
    }

    function initArticleCardAnimations() {
        // Updated selector to match the HTML class
        const cards = document.querySelectorAll('.article-card'); // <-- Was .article-card-item
        if (cards.length === 0) return;

        // Use Intersection Observer for better performance
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target); // Stop observing once animated
                }
            });
        }, {
            threshold: 0.1 // Trigger when 10% of the card is visible
        });

        cards.forEach((card, index) => {
            // Set initial state for animation
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            // Ensure transition applies correctly (adjust timing if needed)
            card.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
            observer.observe(card);
        });
    }

    function highlightSearchTerms() {
        const query = document.querySelector('#search-input')?.value?.trim();
        if (!query || query.length < 2) return;

        // Split query into words, filter out short words
        const words = query.split(' ').filter(word => word.length > 2);
        if (words.length === 0) return;

        // Create regex pattern for all words
        const pattern = words.map(word => `(${word})`).join('|');
        const regex = new RegExp(pattern, 'gi');

        // Elements to search for text
        const elements = document.querySelectorAll(
            '.article-title a, .article-abstract, .journal-list a, .author-name a, .author-bio'
        );

        elements.forEach(element => {
            if (element.innerHTML && !element.querySelector('.highlight')) {
                element.innerHTML = element.innerHTML.replace(regex, '<span class="highlight">$1</span>');
            }
        });
    }

// Add to your existing DOMContentLoaded handler
    document.addEventListener('DOMContentLoaded', function () {

        initJournalSearch()

        // Initialize search highlighting
        highlightSearchTerms();

        // Smooth scroll to results
        setTimeout(() => {
            const firstResult = document.querySelector('.section-title');
            if (firstResult && document.querySelector('#search-input')?.value?.trim()) {
                firstResult.scrollIntoView({behavior: 'smooth', block: 'start'});
            }
        }, 500);
    });

    // Start initialization
    init();
});