const translations = {
    en: {
        welcome: "Welcome to Ni Kuchatika tu",
        selectChat: "Select a chat to start messaging",
        privateChat: "Private Chat",
        privateDesc: "Send private messages to other users",
        groupChat: "Group Chat",
        groupDesc: "Create and join group conversations",
        notifications: "Notifications",
        notifDesc: "Stay updated with instant notifications",
        search: "Search users or groups...",
        lastSeen: "Last seen recently",
        members: "members",
        logout: "Logout"
    },
    sw: {
        welcome: "Karibu kwenye Ni Kuchatika tu",
        selectChat: "Chagua chat kuanza kuwasiliana",
        privateChat: "Chat Binafsi",
        privateDesc: "Tuma ujumbe kwa mtu binafsi",
        groupChat: "Chat ya Kikundi",
        groupDesc: "Unda na jiunge na mazungumzo ya kikundi",
        notifications: "Arifa",
        notifDesc: "Pokea taarifa za papo kwa papo",
        search: "Tafuta watumiaji au vikundi...",
        lastSeen: "Alionekana hivi karibuni",
        members: "wanachama",
        logout: "Toka"
    }
};

// Theme toggling
document.getElementById('themeToggle').addEventListener('click', function() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update icon
    this.querySelector('i').className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
});

// Language toggling
document.getElementById('languageToggle').addEventListener('click', function() {
    const currentLang = localStorage.getItem('language') || 'en';
    const newLang = currentLang === 'en' ? 'sw' : 'en';
    
    localStorage.setItem('language', newLang);
    updateLanguage(newLang);
});

function updateLanguage(lang) {
    // Update all translatable elements
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        element.textContent = translations[lang][key];
    });
}

// Initialize theme and language from localStorage
document.addEventListener('DOMContentLoaded', function() {
    // Set theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.getElementById('themeToggle').querySelector('i').className = 
        savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    
    // Set language
    const savedLang = localStorage.getItem('language') || 'sw';
    updateLanguage(savedLang);
}); 