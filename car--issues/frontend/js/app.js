// Main Application Logic

// Global state
let currentComplaint = null;
let currentChatSession = null;
let currentCar = null;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();

});

// Setup event listeners
function setupEventListeners() {
    // Complaint form submission
    const complaintForm = document.getElementById('complaintForm');
    if (complaintForm) {
        complaintForm.addEventListener('submit', handleComplaintSubmit);
    }

    // Navigation smooth scrolling
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = e.target.getAttribute('href').substring(1);
            scrollToSection(targetId);

            // Update active nav link
            document.querySelectorAll('.nav-menu a').forEach(l => l.classList.remove('active'));
            e.target.classList.add('active');
        });
    });
}

// Scroll to section
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Handle complaint form submission
async function handleComplaintSubmit(e) {
    e.preventDefault();

    const formData = {
        customer_name: document.getElementById('customerName').value,
        customer_email: document.getElementById('customerEmail').value,
        customer_phone: document.getElementById('customerPhone').value,
        license_plate: document.getElementById('licensePlate').value,
        car_make: document.getElementById('carMake').value,
        car_model: document.getElementById('carModel').value,
        car_year: parseInt(document.getElementById('carYear').value) || undefined,
        car_mileage: parseInt(document.getElementById('carMileage').value) || 0,
        complaint_text: document.getElementById('complaintText').value,
        crash: document.getElementById('crash').checked,
        fire: document.getElementById('fire').checked,
    };

    // Validate at least email or phone
    if (!formData.customer_email && !formData.customer_phone) {
        alert('Please provide at least an email or phone number.');
        return;
    }

    showLoading(true);

    const result = await submitComplaint(formData);

    showLoading(false);

    if (result.success) {
        currentComplaint = result.data.data.complaint;
        currentCar = result.data.data.car;

        displayComplaintResult(result.data.data);

        // Scroll to result
        setTimeout(() => {
            document.getElementById('resultCard').scrollIntoView({ behavior: 'smooth' });
        }, 300);
    } else {
        alert('Error submitting complaint: ' + result.error);
    }
}

// Display complaint submission result
function displayComplaintResult(data) {
    const { complaint, car, customer } = data;

    document.getElementById('complaintId').textContent = complaint.id;
    document.getElementById('predictedCategory').textContent =
        complaint.category_display || complaint.predicted_category;
    document.getElementById('confidence').innerHTML =
        `<span style="color: ${getConfidenceColor(complaint.prediction_confidence)}">
            ${(complaint.prediction_confidence * 100).toFixed(1)}%
        </span>`;

    // Show analysis only for this complaint
    const analysisEl = document.getElementById('analysisContent');
    if (analysisEl) {
        analysisEl.innerHTML = complaint.analysis || 'No analysis available.';
        // Ensure the container is visible
        const container = document.getElementById('analysisSection');
        if (container) container.style.display = 'block';
    }

    document.getElementById('resultCard').style.display = 'block';
}

// Get color based on confidence level
function getConfidenceColor(confidence) {
    if (confidence >= 0.8) return '#10b981';
    if (confidence >= 0.6) return '#f59e0b';
    return '#ef4444';
}

// Start chat with AI mechanic
async function startChat() {
    if (!currentComplaint) {
        alert('No complaint selected');
        return;
    }

    showLoading(true);

    // Create chat session
    const result = await createChatSession(currentComplaint.id);

    showLoading(false);

    if (result.success) {
        currentChatSession = result.data;

        // Setup chat UI
        displayChatInterface();

        // Load initial messages
        loadChatMessages();

        // Scroll to chat section
        scrollToSection('chat');
    } else {
        alert('Error starting chat: ' + result.error);
    }
}

// Display chat interface
function displayChatInterface() {
    const chatSection = document.getElementById('chat');
    chatSection.style.display = 'block';

    // Set car info
    const carInfo = `${currentCar.display_name} (${currentCar.license_plate})`;
    document.getElementById('chatCarInfo').textContent = carInfo;

    // Set complaint category
    document.getElementById('chatComplaintCategory').textContent =
        currentComplaint.category_display || currentComplaint.predicted_category;

    // Clear previous messages
    document.getElementById('chatMessages').innerHTML = '';
}

// Load chat messages
async function loadChatMessages() {
    if (!currentChatSession) return;

    const result = await getChatSession(currentChatSession.id);

    if (result.success) {
        const messages = result.data.messages;
        displayMessages(messages);
    }
}

// Display messages in chat
function displayMessages(messages) {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';

    messages.forEach(message => {
        appendMessage(message.role, message.message);
    });

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Append single message to chat
function appendMessage(role, text) {
    const chatMessages = document.getElementById('chatMessages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const roleSpan = document.createElement('div');
    roleSpan.className = 'message-role';
    roleSpan.textContent = role === 'user' ? 'You' : 'AI Mechanic';

    const textDiv = document.createElement('div');

    // Render Markdown for assistant messages
    if (role === 'assistant') {
        textDiv.innerHTML = renderMarkdown(text);
    } else {
        textDiv.textContent = text;
    }

    contentDiv.appendChild(roleSpan);
    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

// Helper function to render Markdown
function renderMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
        .replace(/^### (.+)$/gm, '<h3>$1</h3>') // Headers (multiline)
        .replace(/^- (.+)$/gm, '<li>$1</li>') // List items (multiline)
        .replace(/\n/g, '<br>'); // Newlines
}

// Send message
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) return;
    if (!currentChatSession) {
        alert('No active chat session');
        return;
    }

    // Clear input
    messageInput.value = '';

    // Display user message immediately
    appendMessage('user', message);

    // Create empty AI message bubble
    const aiMessageDiv = appendMessage('assistant', '');
    const aiContentDiv = aiMessageDiv.querySelector('.message-content div:last-child');

    // Send message to API with streaming callback
    let fullResponse = '';
    const result = await sendChatMessage(currentChatSession.id, message, (chunk) => {
        fullResponse += chunk;
        aiContentDiv.innerHTML = renderMarkdown(fullResponse);

        // Scroll to bottom
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });

    // Remove typing indicator (not needed with streaming, but good cleanup)
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();

    if (!result.success) {
        aiMessageDiv.remove(); // Remove empty/partial bubble
        appendMessage('system', 'Error: Could not get response from AI mechanic.');
    }
}

// Handle Enter key in message input
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Close chat
async function closeChat() {
    if (!currentChatSession) return;

    const confirmed = confirm('Are you sure you want to close this chat session?');
    if (!confirmed) return;

    showLoading(true);

    await closeChatSession(currentChatSession.id);

    showLoading(false);

    // Hide chat section
    document.getElementById('chat').style.display = 'none';

    // Reset state
    currentChatSession = null;

    alert('Chat session closed successfully');
}

// Search vehicle by license plate
async function searchVehicle() {
    const licensePlate = document.getElementById('searchPlate').value.trim();

    if (!licensePlate) {
        alert('Please enter a license plate number');
        return;
    }

    showLoading(true);

    const result = await searchCarByPlate(licensePlate);

    showLoading(false);

    if (result.success) {
        const car = result.data;

        // Get complaint history
        const historyResult = await getCarComplaintHistory(car.id);

        if (historyResult.success) {
            displaySearchResults(historyResult.data);
        }
    } else {
        document.getElementById('searchResults').innerHTML =
            '<div class="search-card"><p>No vehicle found with this license plate.</p></div>';
    }
}

// Display search results
function displaySearchResults(data) {
    const { car, complaints } = data;
    const resultsDiv = document.getElementById('searchResults');

    if (complaints.length === 0) {
        resultsDiv.innerHTML = '<div class="search-card"><p>No complaints found for this vehicle.</p></div>';
        return;
    }

    let html = `<div class="search-card">
        <h3>Vehicle: ${car.display_name}</h3>
        <p><strong>License Plate:</strong> ${car.license_plate}</p>
        <p><strong>Customer:</strong> ${car.customer.name}</p>
        <p><strong>Total Complaints:</strong> ${complaints.length}</p>
    </div>`;

    complaints.forEach(complaint => {
        html += `
        <div class="complaint-card">
            <div class="complaint-header">
                <div>
                    <h4>${complaint.category_display || complaint.predicted_category}</h4>
                    <small>${new Date(complaint.created_at).toLocaleString()}</small>
                </div>
                <div>
                    ${complaint.crash ? 'CRASH' : ''}
                    ${complaint.fire ? 'FIRE' : ''}
                </div>
            </div>
            <div class="complaint-body">
                <p>${complaint.complaint_text || 'N/A'}</p>
            </div>
        </div>`;
    });

    resultsDiv.innerHTML = html;
}



// Show/hide loading spinner
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    spinner.style.display = show ? 'flex' : 'none';
}
