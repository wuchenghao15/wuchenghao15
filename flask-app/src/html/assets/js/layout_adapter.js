document.addEventListener('DOMContentLoaded', function() {
    console.log('MTSCOS Layout Adapter loaded');
    
    function adjustLayout() {
        const header = document.querySelector('.header');
        const nav = document.querySelector('.nav-bar');
        
        if (window.innerWidth < 768) {
            if (header) {
                header.style.flexDirection = 'column';
                header.style.gap = '12px';
            }
            if (nav) {
                nav.style.overflowX = 'auto';
            }
        } else {
            if (header) {
                header.style.flexDirection = 'row';
                header.style.gap = '0';
            }
            if (nav) {
                nav.style.overflowX = 'visible';
            }
        }
    }
    
    adjustLayout();
    window.addEventListener('resize', adjustLayout);
    
    const searchInputs = document.querySelectorAll('input[type="text"]');
    searchInputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const searchBtn = this.nextElementSibling;
                if (searchBtn && searchBtn.classList.contains('btn')) {
                    searchBtn.click();
                }
            }
        });
    });
});