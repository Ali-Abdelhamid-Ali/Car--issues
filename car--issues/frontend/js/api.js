// API Configuration and Helper Functions
const API_BASE_URL = '/api/v1';

// API endpoints
const API_ENDPOINTS = {
    complaints: {
        list: `${API_BASE_URL}/complaints/`,
        create: `${API_BASE_URL}/complaints/`,
        quickSubmit: `${API_BASE_URL}/complaints/quick-submit/`,
        detail: (id) => `${API_BASE_URL}/complaints/${id}/`,
        statistics: `${API_BASE_URL}/complaints/statistics/`,
    },
    cars: {
        list: `${API_BASE_URL}/cars/`,
        detail: (id) => `${API_BASE_URL}/cars/${id}/`,
        byPlate: `${API_BASE_URL}/cars/by_license_plate/`,
        history: (id) => `${API_BASE_URL}/cars/${id}/complaint_history/`,
    },
    chat: {
        sessions: `${API_BASE_URL}/chat/sessions/`,
        createSession: `${API_BASE_URL}/chat/sessions/`,
        sessionDetail: (id) => `${API_BASE_URL}/chat/sessions/${id}/`,
        sendMessage: (id) => `${API_BASE_URL}/chat/sessions/${id}/send_message/`,
        closeSession: (id) => `${API_BASE_URL}/chat/sessions/${id}/close/`,
    },
    customers: {
        list: `${API_BASE_URL}/customers/`,
        detail: (id) => `${API_BASE_URL}/customers/${id}/`,
    }
};

// Helper function to make API requests
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'API request failed');
        }

        return { success: true, data };
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

// API Functions

// Submit complaint with customer and car info
async function submitComplaint(formData) {
    return apiRequest(API_ENDPOINTS.complaints.quickSubmit, {
        method: 'POST',
        body: JSON.stringify(formData),
    });
}

// Get complaint statistics
async function getComplaintStatistics() {
    return apiRequest(API_ENDPOINTS.complaints.statistics);
}

// Search car by license plate
async function searchCarByPlate(licensePlate) {
    const url = `${API_ENDPOINTS.cars.byPlate}?plate=${encodeURIComponent(licensePlate)}`;
    return apiRequest(url);
}

// Get car complaint history
async function getCarComplaintHistory(carId) {
    return apiRequest(API_ENDPOINTS.cars.history(carId));
}

// Create chat session
async function createChatSession(complaintId) {
    return apiRequest(API_ENDPOINTS.chat.createSession, {
        method: 'POST',
        body: JSON.stringify({ complaint_id: complaintId }),
    });
}

// Send message in chat with streaming
async function sendChatMessage(sessionId, message, onChunk) {
    const url = API_ENDPOINTS.chat.sendMessage(sessionId);

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });

        if (!response.ok) {
            throw new Error('API request failed');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            fullResponse += chunk;

            if (onChunk) {
                onChunk(chunk);
            }
        }

        return { success: true, data: { ai_response: { message: fullResponse } } };

    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

// Get chat session details
async function getChatSession(sessionId) {
    return apiRequest(API_ENDPOINTS.chat.sessionDetail(sessionId));
}

// Close chat session
async function closeChatSession(sessionId) {
    return apiRequest(API_ENDPOINTS.chat.closeSession(sessionId), {
        method: 'POST',
    });
}
