// Theme management
class ThemeManager {
    constructor() {
        this.themeToggle = document.getElementById('themeToggle');
        this.themeIcon = this.themeToggle ? this.themeToggle.querySelector('i') : null;
        this.currentTheme = localStorage.getItem('theme') || 'light';
        
        this.init();
    }

    init() {
        // Set initial theme
        this.applyTheme(this.currentTheme);
        
        // Add click listener
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        if (this.themeIcon) {
            if (theme === 'dark') {
                this.themeIcon.classList.replace('fa-moon', 'fa-sun');
            } else {
                this.themeIcon.classList.replace('fa-sun', 'fa-moon');
            }
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(this.currentTheme);
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
});

document.addEventListener('DOMContentLoaded', function() {
    const themeButtons = document.querySelectorAll('.theme-btn');
    
    themeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const theme = this.dataset.theme;
            document.documentElement.setAttribute('data-theme', theme);
            
            fetch('/theme', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ theme: theme })
            });
        });
    });
}); 