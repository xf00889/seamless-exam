/**
 * Django Message Loader Component
 * Handles loading and displaying Django messages through MessageHandler
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we have Django messages data
    const messagesElement = document.getElementById('django-messages-data');
    if (!messagesElement) {
        return;
    }

    try {
        // Parse Django messages from JSON script tag
        const djangoMessages = JSON.parse(messagesElement.textContent);
        
        // Make messages available globally for MessageHandler
        window.djangoMessages = djangoMessages;
        
        // Load message handler component if not already loaded
        if (!window.MessageHandler) {
            const script = document.createElement('script');
            script.src = document.querySelector('[data-static-url]')?.dataset.staticUrl + 'js/components/message-handler.js';
            script.onload = function() {
                // Process messages after MessageHandler is loaded
                processDjangoMessages(djangoMessages);
            };
            document.head.appendChild(script);
        } else {
            // If already loaded, process messages immediately
            processDjangoMessages(djangoMessages);
        }
    } catch (error) {
        console.error('Error processing Django messages:', error);
    }
});

/**
 * Process Django messages and display them using MessageHandler
 * @param {Array} messages - Array of Django message objects
 */
function processDjangoMessages(messages) {
    if (!window.MessageHandler || !Array.isArray(messages)) {
        return;
    }

    messages.forEach(message => {
        // Use the message type directly since our custom filter provides the correct format
        window.MessageHandler.show(message.text, message.type);
    });
}