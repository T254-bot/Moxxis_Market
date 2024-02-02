$(document).ready(function(){
    $('.sidenav').sidenav();
});

// Function to fade out flash messages after a timeout
window.onload = function() {
    var flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.parentNode.removeChild(message);
            }, 50); // Fade-out animation duration in milliseconds
        }, 10000); // Flash message display duration in milliseconds
    });
};