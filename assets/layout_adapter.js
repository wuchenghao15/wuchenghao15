document.addEventListener('DOMContentLoaded', function() {
    console.log('Layout Adapter loaded');
    
    function adjustLayout() {
        var header = document.querySelector('header');
        var nav = document.querySelector('nav');
        if (header && nav) {
            if (window.innerWidth < 768) {
                nav.style.display = 'none';
            } else {
                nav.style.display = 'block';
            }
        }
    }
    
    adjustLayout();
    window.addEventListener('resize', adjustLayout);
    
    var searchInput = document.querySelector('input[type="search"]');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                var query = this.value.trim();
                if (query) {
                    window.location.href = '/search?q=' + encodeURIComponent(query);
                }
            }
        });
    }
});
