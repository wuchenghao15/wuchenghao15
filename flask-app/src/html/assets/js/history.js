document.addEventListener('DOMContentLoaded', function() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.timeline-item, .milestone-card, .vision-card').forEach(function(el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(el);
    });

    document.querySelectorAll('.back-link, .nav a').forEach(function(link) {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href.startsWith('/') && !href.startsWith('//')) {
                e.preventDefault();
                window.location.href = href;
            }
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
            
            if (el.textContent.includes('万')) {
                el.textContent = (current / 10000).toFixed(1) + '万+';
            } else if (el.textContent.includes('+')) {
                el.textContent = current + '+';
            } else {
                el.textContent = current;
            }
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        
        requestAnimationFrame(update);
    }

    const numberObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const card = entry.target;
                const numberEl = card.querySelector('.milestone-number');
                if (numberEl) {
                    const text = numberEl.textContent;
                    let target = 0;
                    
                    if (text.includes('万')) {
                        const num = parseFloat(text) * 10000;
                        target = Math.floor(num);
                    } else {
                        target = parseInt(text) || 0;
                    }
                    
                    if (target > 0) {
                        animateNumber(numberEl, target, 1500);
                    }
                }
                numberObserver.unobserve(card);
            }
        });
    }, { threshold: 0.3 });

    document.querySelectorAll('.milestone-card').forEach(function(card) {
        numberObserver.observe(card);
    });
});
