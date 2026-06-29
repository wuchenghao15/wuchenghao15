document.addEventListener('DOMContentLoaded', function() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const animatedElements = document.querySelectorAll(
        '.business-card, .choose-item, .culture-card, .member-card, .news-item, .mv-card, .goal-item, .benefit-item'
    );

    animatedElements.forEach(function(el, index) {
        el.style.animationDelay = (index * 0.05) + 's';
        observer.observe(el);
    });

    const filterBtns = document.querySelectorAll('.filter-btn');
    const newsItems = document.querySelectorAll('.news-item');

    if (filterBtns.length > 0 && newsItems.length > 0) {
        filterBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                filterBtns.forEach(function(b) { b.classList.remove('active'); });
                btn.classList.add('active');

                const filter = btn.getAttribute('data-filter');

                newsItems.forEach(function(item) {
                    if (filter === 'all' || item.getAttribute('data-category') === filter) {
                        item.style.display = 'flex';
                        setTimeout(function() {
                            item.style.opacity = '1';
                            item.style.transform = 'translateY(0)';
                        }, 10);
                    } else {
                        item.style.opacity = '0';
                        item.style.transform = 'translateY(20px)';
                        setTimeout(function() {
                            item.style.display = 'none';
                        }, 300);
                    }
                });
            });
        });
    }

    const pageBtns = document.querySelectorAll('.page-btn:not(.disabled)');
    pageBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (btn.classList.contains('active')) return;
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });

    function animateNumber(el, target, duration) {
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (target - start) * easeOut);
            el.textContent = current + (el.dataset.suffix || '');

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    const statNumbers = document.querySelectorAll('.stat-number, .milestone-number');
    const numberObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const text = entry.target.textContent;
                const match = text.match(/([\d.]+)(.*)/);
                if (match) {
                    const num = parseFloat(match[1].replace(',', ''));
                    const suffix = match[2] || '';
                    entry.target.dataset.suffix = suffix;
                    animateNumber(entry.target, num, 1500);
                }
                numberObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(function(el) {
        numberObserver.observe(el);
    });
});
