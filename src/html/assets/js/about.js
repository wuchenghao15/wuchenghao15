(function() {
    'use strict';
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
    function checkNationalMemorialDay() {
        const today = new Date();
        const month = today.getMonth() + 1;
        const day = today.getDate();
        const memorialDays = [
            { month: 12, day: 13 },
            { month: 5, day: 12 },
            { month: 7, day: 28 }
        ];
        return memorialDays.some(memDay => memDay.month === month && memDay.day === day);
    }
    document.addEventListener('DOMContentLoaded', function() {
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            alert('该操作已被禁止');
            return false;
        });
        document.addEventListener('selectstart', function(e) {
            e.preventDefault();
            return false;
        });
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'c' || e.key === 'x' || e.key === 'u')) {
                e.preventDefault();
                return false;
            }
        });
        if (checkNationalMemorialDay()) {
            document.documentElement.classList.add('memorial-day-theme');
        }
    });
})();