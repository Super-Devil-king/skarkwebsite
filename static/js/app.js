function showLoading() {
    document.querySelector('.loader-border').style.opacity = '1';
    document.getElementById('user-input').disabled = true; // Disable input
    document.getElementById('send-btn').disabled = true; // Disable send button
}
const messages = document.getElementById('messages');

messages.addEventListener('wheel', function (e) {
    e.preventDefault(); // Prevent default scroll
    messages.scrollBy({
        top: e.deltaY * 0.5,  // Adjust multiplier to control speed (0.2 slows it down)
        behavior: 'smooth'
    });
});
function hideLoading() {
    document.querySelector('.loader-border').style.opacity = '0';
    document.getElementById('user-input').disabled = false; // Enable input
    document.getElementById('send-btn').disabled = false; // Enable send button
    document.getElementById('user-input').focus(); // Automatically focus input
}

function autoResizeInput(input) {
    input.style.height = 'auto';
    input.style.height = input.scrollHeight + 'px';
}
// script.js
document.addEventListener("DOMContentLoaded", () => {
    const toggleSwitch = document.getElementById("mode-switch");

    // Check localStorage for the mode preference
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark-mode");
        toggleSwitch.checked = true;
    }

    toggleSwitch.addEventListener("change", () => {
        document.body.classList.toggle("dark-mode");

        // Store the user's theme preference
        if (document.body.classList.contains("dark-mode")) {
            localStorage.setItem("theme", "dark");
        } else {
            localStorage.setItem("theme", "light");
        }
    });
});
function checkEnter(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
}
// Detect DevTools open with a performance measurement trick
function detectDevTools() {
    let devtoolsDetected = false;
    const threshold = 100;
    const start = performance.now();
    debugger; // This will pause if DevTools is open
    if (performance.now() - start > threshold) {
        devtoolsDetected = true;
        alert('DevTools detected! Exiting...');
        window.close(); // Close the tab
    }
}

setInterval(detectDevTools, 1000); // Check for DevTools every second

// Disable right-click, F12, and common DevTools key combinations
document.addEventListener('contextmenu', function (event) {
    event.preventDefault(); // Disable right-click
});

document.addEventListener('keydown', function (event) {
    if (
        event.keyCode === 123 || // F12
        (event.ctrlKey && event.shiftKey && event.keyCode === 73) || // Ctrl+Shift+I
        (event.ctrlKey && event.shiftKey && event.keyCode === 67) || // Ctrl+Shift+C
        (event.ctrlKey && event.shiftKey && event.keyCode === 74) || // Ctrl+Shift+J
        (event.ctrlKey && event.keyCode === 85) // Ctrl+U (view source)
    ) {
        event.preventDefault();
        alert('Restricted action! Exiting...');
        window.close(); // Close the tab
    }
});

// Disable console usage
console.log = function () { };
console.error = function () { };
console.warn = function () { };
console.info = function () { };
console.debug = function () { };
window.console = {
    log: function () { },
    error: function () { },
    warn: function () { },
    info: function () { },
    debug: function () { }
};

function showLoading() {
    document.querySelector('.loader-border').style.opacity = '1';
    document.getElementById('user-input').disabled = true; // Disable input
    document.getElementById('send-btn').disabled = true; // Disable send button
}

function hideLoading() {
    document.querySelector('.loader-border').style.opacity = '0';
    document.getElementById('user-input').disabled = false; // Enable input
    document.getElementById('send-btn').disabled = false; // Enable send button
    document.getElementById('user-input').focus(); // Automatically focus input
}

function autoResizeInput(input) {
    input.style.height = 'auto';
    input.style.height = input.scrollHeight + 'px';
}

function checkEnter(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
}
function sendMessage() {
    var userInput = document.getElementById('user-input').value;
    if (userInput === '') return; // Check for empty input

    showLoading(); // Show loader

    // Display the user's message in the chat
    var userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.textContent = userInput;
    document.getElementById('messages').appendChild(userMessage);

    // Send the message to the backend
    fetch('/get_response', {
        method: 'POST',
        headers: {
            'Content-Type'  : 'application/json',
        },
        body: JSON.stringify({ message: userInput }),
    })
        .then(response => response.json())
        .then(data => {
            setTimeout(function () {
                hideLoading(); // Hide loader after delay

                // Only display the bot's response if it's not empty or whitespace
                if (data.response && data.response.trim() !== "") {
                    var botMessage = document.createElement('div');
                    botMessage.className = 'message bot-message';
                    botMessage.innerHTML = data.response;
                    document.getElementById('messages').appendChild(botMessage);
                }

                // Only append the menu if it's not empty
                if (data.menu && data.menu.trim() !== "") {
                    var botMenu = document.createElement('div');
                    botMenu.className = 'message bot-message'; // Use regular class for spacing
                    botMenu.innerHTML = data.menu;
                    document.getElementById('messages').appendChild(botMenu);
                }

                // Scroll chat to bottom
                document.getElementById('user-input').placeholder = 'Please type to continue';
                document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;

                saveChatHistory();

                document.getElementById('user-input').value = '';
            }, 100);
            // hideLoading();
        });

    // Clear the input field
    document.getElementById('user-input').value = '';
    saveChatHistory();
}


function confirmExit() {
    if (confirm('Goodbye! Do you really want to exit?')) {
        window.close();
    }
}

function loadChatHistory() {
    const savedMessages = localStorage.getItem('chatMessages');
    if (savedMessages) {
        document.getElementById('messages').innerHTML = savedMessages;
    }
}

function saveChatHistory() {
    const messagesHTML = document.getElementById('messages').innerHTML;
    localStorage.setItem('chatMessages', messagesHTML);
}

function confirmClear() {
    if (confirm('Are you sure you want to clear all messages and user data?')) {
        // Clear chat messages from the chatbox
        document.getElementById('messages').innerHTML = '';

        // Clear chat history and any other stored data from localStorage
        localStorage.removeItem('chatMessages');  // Clear specific chat history

        // Optionally, clear all localStorage data if there's more user data stored
        localStorage.clear();  // This will clear ALL data from localStorage

        // Clear sessionStorage if you're using it for temporary user data
        sessionStorage.clear();  // This will clear ALL data from sessionStorage

        // Send a request to the backend to clear the Flask session
        fetch('/clear_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);  // Log the session cleared message (optional)
            })
            .catch(error => console.error('Error clearing session:', error))
            .finally(() => {
                // This will always run, ensuring the page reloads
                window.location.reload();  // Reload the page to reflect changes
            });
    }
}

// Load chat history on page load
window.onload = function () {
    loadChatHistory(); // Load chat history from localStorage
    document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
};