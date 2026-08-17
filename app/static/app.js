/**
 * AI Data Analyst - Frontend Application
 */

// ========================================
// DOM Elements
// ========================================
const messagesEl = document.getElementById('messages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const sendIcon = document.getElementById('sendIcon');
const loadingIcon = document.getElementById('loadingIcon');
const chartsList = document.getElementById('chartsList');
const chartCount = document.getElementById('chartCount');
const resetBtn = document.getElementById('resetBtn');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const modelInfo = document.getElementById('modelInfo');
const tokenInfo = document.getElementById('tokenInfo');

// ========================================
// State
// ========================================
const state = {
    isLoading: false,
    charts: [],
    messageCount: 0,
};

// ========================================
// API Client
// ========================================
async function apiRequest(endpoint, options = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail?.message || error.message || `HTTP ${response.status}`);
    }
    
    return response.json();
}

async function fetchHealth() {
    try {
        const health = await apiRequest('/health');
        modelInfo.textContent = `Model: ${health.model.split('/').pop()}`;
        statusDot.classList.remove('error');
        statusText.textContent = 'Connected';
        return health;
    } catch (e) {
        statusDot.classList.add('error');
        statusText.textContent = 'Disconnected';
        console.error('Health check failed:', e);
    }
}

async function sendMessage(message) {
    const response = await apiRequest('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message, reset_context: false }),
    });
    return response;
}

async function resetConversation() {
    return apiRequest('/api/reset', { method: 'POST' });
}

// ========================================
// UI Functions
// ========================================
function addMessage(type, content, meta = null) {
    // Remove welcome message on first real message
    if (state.messageCount === 0) {
        const welcome = messagesEl.querySelector('.welcome');
        if (welcome) welcome.remove();
    }
    state.messageCount++;
    
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    
    const avatar = type === 'user' ? '👤' : type === 'error' ? '⚠️' : '🤖';
    
    messageEl.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${formatContent(content)}
            ${meta ? formatMeta(meta) : ''}
        </div>
    `;
    
    messagesEl.appendChild(messageEl);
    scrollToBottom();
    
    return messageEl;
}

function formatContent(content) {
    // Escape HTML
    let escaped = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Convert markdown-like formatting
    // Bold: **text** or __text__
    escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/__(.+?)__/g, '<strong>$1</strong>');
    
    // Italic: *text* or _text_
    escaped = escaped.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em>$1</em>');
    
    // Code: `text`
    escaped = escaped.replace(/`([^`]+?)`/g, '<code>$1</code>');
    
    // Preserve newlines as paragraphs
    const paragraphs = escaped.split('\n\n').filter(p => p.trim());
    return paragraphs.map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
}

function formatMeta(meta) {
    const parts = [];
    if (meta.duration_ms) parts.push(`⏱️ ${(meta.duration_ms / 1000).toFixed(1)}s`);
    if (meta.iterations) parts.push(`🔄 ${meta.iterations} iterations`);
    if (meta.tools_used && meta.tools_used.length) {
        parts.push(`🔧 ${meta.tools_used.length} tools`);
    }
    
    if (parts.length === 0) return '';
    
    return `<div class="message-meta">${parts.join(' • ')}</div>`;
}

function addTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message message-agent';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    messagesEl.appendChild(indicator);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

function addChart(url, title = 'Chart') {
    state.charts.push({ url, title });
    
    // Clear empty state
    const empty = chartsList.querySelector('.charts-empty');
    if (empty) empty.remove();
    
    const chartEl = document.createElement('div');
    chartEl.className = 'chart-item';
    chartEl.innerHTML = `
        <div class="chart-title">${escapeHtml(title)}</div>
        <img class="chart-image" src="${url}" alt="${escapeHtml(title)}" 
             onclick="window.open('${url}', '_blank')" />
        <div class="chart-actions">
            <a class="chart-action" href="${url}" target="_blank" download>⬇️ Download</a>
            <a class="chart-action" href="${url}" target="_blank">🔍 Full Size</a>
        </div>
    `;
    
    // Prepend so newest is at top
    chartsList.insertBefore(chartEl, chartsList.firstChild);
    
    // Update count
    chartCount.textContent = `${state.charts.length} chart${state.charts.length !== 1 ? 's' : ''}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function setLoading(loading) {
    state.isLoading = loading;
    sendBtn.disabled = loading;
    messageInput.disabled = loading;
    
    if (loading) {
        sendIcon.classList.add('hidden');
        loadingIcon.classList.remove('hidden');
    } else {
        sendIcon.classList.remove('hidden');
        loadingIcon.classList.add('hidden');
        messageInput.focus();
    }
}

function scrollToBottom() {
    setTimeout(() => {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }, 50);
}

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

// ========================================
// Event Handlers
// ========================================
async function handleSubmit(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || state.isLoading) return;
    
    // Add user message
    addMessage('user', message);
    
    // Clear input
    messageInput.value = '';
    autoResizeTextarea();
    
    // Show loading
    setLoading(true);
    addTypingIndicator();
    
    try {
        const response = await sendMessage(message);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add agent response
        addMessage('agent', response.response, {
            duration_ms: response.duration_ms,
            iterations: response.iterations,
            tools_used: response.tools_used,
        });
        
        // Update token info
        tokenInfo.textContent = `Iterations: ${response.iterations}`;
        
        // Add generated charts
        if (response.charts_generated && response.charts_generated.length > 0) {
            response.charts_generated.forEach(url => {
                // Extract chart title from URL
                const filename = url.split('/').pop().split('_').slice(1, -2).join(' ');
                addChart(url, filename || 'Generated Chart');
            });
        }
        
    } catch (error) {
        removeTypingIndicator();
        console.error('Chat error:', error);
        addMessage('error', `Error: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

async function handleReset() {
    if (!confirm('Reset conversation? This will clear the current context.')) return;
    
    try {
        await resetConversation();
        
        // Clear messages
        messagesEl.innerHTML = '';
        state.messageCount = 0;
        
        // Show welcome again
        messagesEl.innerHTML = `
            <div class="message message-agent welcome">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <p>Conversation reset. Ready for your next question!</p>
                </div>
            </div>
        `;
        
        // Reset stats
        tokenInfo.textContent = 'Iterations: 0';
        
    } catch (error) {
        console.error('Reset error:', error);
        addMessage('error', `Failed to reset: ${error.message}`);
    }
}

function handleExampleClick(e) {
    if (!e.target.classList.contains('example-query')) return;
    
    const query = e.target.dataset.query;
    messageInput.value = query;
    autoResizeTextarea();
    messageInput.focus();
}

function handleKeyDown(e) {
    // Enter to send (Shift+Enter for new line)
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
}

// ========================================
// Initialization
// ========================================
function init() {
    // Attach event listeners
    chatForm.addEventListener('submit', handleSubmit);
    resetBtn.addEventListener('click', handleReset);
    messageInput.addEventListener('input', autoResizeTextarea);
    messageInput.addEventListener('keydown', handleKeyDown);
    messagesEl.addEventListener('click', handleExampleClick);
    
    // Fetch health check
    fetchHealth();
    
    // Poll health every 30 seconds
    setInterval(fetchHealth, 30000);
    
    // Focus input
    messageInput.focus();
    
    console.log('AI Data Analyst UI ready');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
