/**
 * Django Message Loader Component
 * Handles loading and displaying Django messages through MessageHandler
 */

document.addEventListener('DOMContentLoaded', function() {
    const messagesElement = document.getElementById('django-messages-data');
    if (!messagesElement) {
        return;
    }

    // If MessageHandler is already loaded (from base.html), it auto-processes
    // messages in its own DOMContentLoaded handler — skip to avoid duplicates.
    if (window.MessageHandler) {
        return;
    }

    try {
        const djangoMessages = JSON.parse(messagesElement.textContent);
        window.djangoMessages = djangoMessages;

        // Dynamically load message handler as fallback
        const script = document.createElement('script');
        script.src = document.querySelector('[data-static-url]')?.dataset.staticUrl + 'js/components/message-handler.js';
        script.onload = function() {
            processDjangoMessages(djangoMessages);
        };
        document.head.appendChild(script);
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
        window.MessageHandler.show(message.text, message.type);
    });
}