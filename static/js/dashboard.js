document.addEventListener("DOMContentLoaded", function() {
    // Sidebar toggle functionality for mobile
    const toggleBtn = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    
    if (toggleBtn && sidebar && overlay) {
        toggleBtn.addEventListener("click", function() {
            sidebar.classList.toggle("show");
            overlay.classList.toggle("show");
        });

        overlay.addEventListener("click", function() {
            sidebar.classList.remove("show");
            overlay.classList.remove("show");
        });
    }
});
