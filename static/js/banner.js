// ========== BANNER FUNCTIONS ==========

// Load custom banner from localStorage
document.addEventListener('DOMContentLoaded', function() {
    const bannerImg = document.getElementById('bannerImage');
    if (bannerImg) {
        const savedBanner = localStorage.getItem('customBanner');
        if (savedBanner) {
            bannerImg.src = savedBanner;
        }
    }
});

// Update banner function
function updateBanner(url) {
    localStorage.setItem('customBanner', url);
    const bannerImg = document.getElementById('bannerImage');
    if (bannerImg) {
        bannerImg.src = url;
    }
}