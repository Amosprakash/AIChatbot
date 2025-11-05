// ============================================
// DOM Elements
// ============================================
const chatWindow = document.getElementById("chatWindow");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const fileInput = document.getElementById("fileInput");
const micBtn = document.getElementById("micBtn");
const filePreview = document.getElementById("filePreview");

// Header buttons
const toggleSidebar = document.getElementById("toggleSidebar");
const closeSidebar = document.getElementById("closeSidebar");
const clearChatBtn = document.getElementById("clearChatBtn");
const saveChatBtn = document.getElementById("saveChatBtn");
const darkModeToggle = document.getElementById("darkModeToggle");

// Sidebar elements
const sidebar = document.getElementById("sidebar");
const chatList = document.getElementById("chatList");
const newChatBtn = document.getElementById("newChatBtn");

// Modal elements
const saveChatModal = document.getElementById("saveChatModal");
const closeSaveModal = document.getElementById("closeSaveModal");
const cancelSave = document.getElementById("cancelSave");
const confirmSave = document.getElementById("confirmSave");
const chatNameInput = document.getElementById("chatNameInput");

// Toast container
const toastContainer = document.getElementById("toastContainer");

// Export elements
const exportDropdown = document.querySelector(".export-dropdown");
const exportToggle = document.querySelector(".export-toggle");
const exportPdfBtn = document.getElementById("exportPdfBtn");
const exportExcelBtn = document.getElementById("exportExcelBtn");
const exportCsvBtn = document.getElementById("exportCsvBtn");

// ============================================
// Global Variables
// ============================================
let lastBotResponse = null;
let recognizer = null;
let isListening = false;
let editingMessageContent = null;
let currentChatId = null;

// ============================================
// Toast Notifications
// ============================================
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icon = document.createElement('div');
  icon.className = 'toast-icon';

  // Set icon based on type
  const icons = {
    success: '<i class="fas fa-check-circle"></i>',
    error: '<i class="fas fa-exclamation-circle"></i>',
    warning: '<i class="fas fa-exclamation-triangle"></i>',
    info: '<i class="fas fa-info-circle"></i>'
  };
  icon.innerHTML = icons[type] || icons.info;

  const messageDiv = document.createElement('div');
  messageDiv.className = 'toast-message';
  messageDiv.textContent = message;

  toast.appendChild(icon);
  toast.appendChild(messageDiv);
  toastContainer.appendChild(toast);

  // Auto remove after 3 seconds
  setTimeout(() => {
    toast.style.animation = 'toastIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================
// Dark Mode Toggle
// ============================================
function initDarkMode() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateDarkModeIcon(savedTheme);
}

function toggleDarkMode() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  updateDarkModeIcon(newTheme);

  showToast(`${newTheme === 'dark' ? 'Dark' : 'Light'} mode activated`, 'success');
}

function updateDarkModeIcon(theme) {
  const icon = darkModeToggle.querySelector('i');
  icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

// ============================================
// Sidebar Management
// ============================================
function toggleSidebarVisibility() {
  sidebar.classList.toggle('closed');
  if (window.innerWidth <= 768) {
    sidebar.classList.toggle('open');
  }
}

function loadChatHistory() {
  fetch('/list-chats')
    .then(res => res.json())
    .then(chats => {
      chatList.innerHTML = '';
      if (chats.length === 0) {
        chatList.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem; text-align: center; padding: 1rem;">No saved chats</p>';
        return;
      }

      chats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-item';
        if (chat.id === currentChatId) {
          chatItem.classList.add('active');
        }

        chatItem.innerHTML = `
          <div class="chat-item-header">
            <div class="chat-item-name">${chat.name}</div>
            <button class="chat-item-delete" onclick="deleteChat('${chat.id}', event)">
              <i class="fas fa-trash"></i>
            </button>
          </div>
          <div class="chat-item-info">${chat.message_count} messages</div>
        `;

        chatItem.addEventListener('click', () => loadChat(chat.id));
        chatList.appendChild(chatItem);
      });
    })
    .catch(err => {
      console.error('Failed to load chat history:', err);
      showToast('Failed to load chat history', 'error');
    });
}

function loadChat(chatId) {
  fetch(`/load-chat/${chatId}`)
    .then(res => res.json())
    .then(chat => {
      currentChatId = chatId;
      chatWindow.innerHTML = '';

      chat.messages.forEach(msg => {
        appendMessage(msg.sender, msg.text, false);
      });

      showToast('Chat loaded successfully', 'success');
      loadChatHistory(); // Refresh to update active state

      if (window.innerWidth <= 768) {
        toggleSidebarVisibility();
      }
    })
    .catch(err => {
      console.error('Failed to load chat:', err);
      showToast('Failed to load chat', 'error');
    });
}

function deleteChat(chatId, event) {
  event.stopPropagation();

  if (!confirm('Are you sure you want to delete this chat?')) {
    return;
  }

  fetch(`/delete-chat/${chatId}`, { method: 'DELETE' })
    .then(res => res.json())
    .then(() => {
      if (chatId === currentChatId) {
        clearChat();
        currentChatId = null;
      }
      loadChatHistory();
      showToast('Chat deleted successfully', 'success');
    })
    .catch(err => {
      console.error('Failed to delete chat:', err);
      showToast('Failed to delete chat', 'error');
    });
}

function startNewChat() {
  clearChat();
  currentChatId = null;
  showToast('New chat started', 'info');

  if (window.innerWidth <= 768) {
    toggleSidebarVisibility();
  }
}

// ============================================
// Save Chat Functionality
// ============================================
function openSaveChatModal() {
  const messages = getAllMessages();
  if (messages.length <= 1) { // Only welcome message
    showToast('No messages to save', 'warning');
    return;
  }

  chatNameInput.value = currentChatId ? '' : `Chat ${new Date().toLocaleString()}`;
  saveChatModal.classList.add('show');
  chatNameInput.focus();
}

function closeSaveChatModal() {
  saveChatModal.classList.remove('show');
  chatNameInput.value = '';
}

function saveCurrentChat() {
  const chatName = chatNameInput.value.trim();
  if (!chatName) {
    showToast('Please enter a chat name', 'warning');
    return;
  }

  const messages = getAllMessages();
  const chatId = currentChatId || Date.now().toString();

  fetch('/save-chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      chat_name: chatName,
      messages: messages
    })
  })
    .then(res => res.json())
    .then(data => {
      currentChatId = data.chat_id;
      closeSaveChatModal();
      loadChatHistory();
      showToast('Chat saved successfully', 'success');
    })
    .catch(err => {
      console.error('Failed to save chat:', err);
      showToast('Failed to save chat', 'error');
    });
}

function getAllMessages() {
  const messages = [];
  const messageWrappers = chatWindow.querySelectorAll('.message-wrapper');

  messageWrappers.forEach(wrapper => {
    const sender = wrapper.classList.contains('bot') ? 'bot' : 'user';
    const messageContent = wrapper.querySelector('.message-content');
    if (messageContent) {
      messages.push({
        sender: sender,
        text: messageContent.textContent
      });
    }
  });

  return messages;
}

// ============================================
// Clear Chat
// ============================================
function clearChat() {
  if (chatWindow.querySelectorAll('.message-wrapper').length <= 1) {
    showToast('Chat is already empty', 'info');
    return;
  }

  if (!confirm('Are you sure you want to clear the chat?')) {
    return;
  }

  chatWindow.innerHTML = '';
  appendMessage('bot', 'Hi! I\'m your AI assistant. I can help you with document analysis, data queries, and much more. How can I assist you today?', false);
  showToast('Chat cleared', 'success');
  currentChatId = null;
}

// ============================================
// File Upload Management
// ============================================
function updateFilePreview() {
  const files = fileInput.files;
  filePreview.innerHTML = '';

  if (files.length === 0) return;

  Array.from(files).forEach((file, index) => {
    const fileTag = document.createElement('div');
    fileTag.className = 'file-tag';
    fileTag.innerHTML = `
      <i class="fas fa-file"></i>
      <span>${file.name}</span>
      <button onclick="removeFile(${index})" title="Remove file">
        <i class="fas fa-times"></i>
      </button>
    `;
    filePreview.appendChild(fileTag);
  });
}

function removeFile(index) {
  const dt = new DataTransfer();
  const files = fileInput.files;

  for (let i = 0; i < files.length; i++) {
    if (i !== index) {
      dt.items.add(files[i]);
    }
  }

  fileInput.files = dt.files;
  updateFilePreview();
}

// ============================================
// Message Management
// ============================================
function appendMessage(sender, text, addActions = true) {
  const wrapper = document.createElement('div');
  wrapper.className = `message-wrapper ${sender}`;

  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}`;

  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  messageContent.textContent = text;

  messageDiv.appendChild(messageContent);
  wrapper.appendChild(messageDiv);

  if (addActions) {
    const actionIcons = document.createElement('div');
    actionIcons.className = 'action-icons';

    // Copy button for all messages
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.title = 'Copy message';
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    copyBtn.addEventListener('click', () => copyMessage(messageContent.textContent));
    actionIcons.appendChild(copyBtn);

    // Edit and delete for user messages only
    if (sender === 'user') {
      const editBtn = document.createElement('button');
      editBtn.className = 'edit-btn';
      editBtn.title = 'Edit message';
      editBtn.innerHTML = '<i class="fas fa-edit"></i>';

      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'delete-btn';
      deleteBtn.title = 'Delete message';
      deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';

      const saveBtn = document.createElement('button');
      saveBtn.className = 'save-btn';
      saveBtn.title = 'Save changes';
      saveBtn.innerHTML = '<i class="fas fa-save"></i>';
      saveBtn.style.display = 'none';

      const cancelBtn = document.createElement('button');
      cancelBtn.className = 'cancel-btn';
      cancelBtn.title = 'Cancel editing';
      cancelBtn.innerHTML = '<i class="fas fa-times"></i>';
      cancelBtn.style.display = 'none';

      let originalText = text;

      editBtn.addEventListener('click', () => {
        messageDiv.classList.add('editing');
        messageContent.contentEditable = 'true';
        messageContent.focus();

        editBtn.style.display = 'none';
        deleteBtn.style.display = 'none';
        copyBtn.style.display = 'none';
        saveBtn.style.display = 'inline-block';
        cancelBtn.style.display = 'inline-block';
      });

      saveBtn.addEventListener('click', () => {
        messageContent.contentEditable = 'false';
        messageDiv.classList.remove('editing');

        editBtn.style.display = 'inline-block';
        deleteBtn.style.display = 'inline-block';
        copyBtn.style.display = 'inline-block';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';

        originalText = messageContent.textContent;
        editingMessageContent = messageContent;
        showToast('Message edited', 'success');
      });

      cancelBtn.addEventListener('click', () => {
        messageContent.textContent = originalText;
        messageContent.contentEditable = 'false';
        messageDiv.classList.remove('editing');

        editBtn.style.display = 'inline-block';
        deleteBtn.style.display = 'inline-block';
        copyBtn.style.display = 'inline-block';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';
      });

      deleteBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to delete this message?')) {
          wrapper.remove();
          showToast('Message deleted', 'success');
        }
      });

      actionIcons.append(editBtn, deleteBtn, saveBtn, cancelBtn);
    }

    wrapper.appendChild(actionIcons);
  }

  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function copyMessage(text) {
  navigator.clipboard.writeText(text)
    .then(() => showToast('Message copied to clipboard', 'success'))
    .catch(() => showToast('Failed to copy message', 'error'));
}

// ============================================
// Send Message
// ============================================
function sendMessage(message) {
  appendMessage('user', message);

  userInput.value = '';
  userInput.style.height = 'auto';

  // Show typing indicator
  const typingIndicator = document.createElement('div');
  typingIndicator.className = 'typing-indicator';
  for (let i = 0; i < 3; i++) {
    const dot = document.createElement('div');
    dot.className = 'typing-dot';
    typingIndicator.appendChild(dot);
  }
  chatWindow.appendChild(typingIndicator);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  const files = fileInput.files;
  const formData = new FormData();
  formData.append('message', message);

  for (let i = 0; i < files.length; i++) {
    formData.append('file', files[i]);
  }

  fetch('/chat', {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      lastBotResponse = data;
      typingIndicator.remove();

      if (data.error) {
        appendMessage('bot', `⚠️ ${data.error}`);
      } else if (data.preview) {
        appendMessage('bot', `📝 ${data.preview}`);
      } else if (data.chart) {
        appendChart(data.chart);
      } else if (data.table) {
        appendTable(data.table);
      } else if (data.summary || data.reply) {
        appendMessage('bot', data.summary || data.reply);
      } else if (data.download_link) {
        appendMessage('bot', data.message || 'File ready for download');
      } else {
        appendMessage('bot', '🤖 Sorry, I couldn\'t understand that.');
      }
    })
    .catch(err => {
      console.error(err);
      typingIndicator.remove();
      appendMessage('bot', '⚠️ Failed to fetch response.');
      showToast('Failed to send message', 'error');
    });

  // Clear file input
  fileInput.value = '';
  updateFilePreview();
}

// ============================================
// Chart and Table Functions
// ============================================
function appendChart(data) {
  const canvas = document.createElement('canvas');
  const container = document.createElement('div');
  container.className = 'chart-container';
  container.appendChild(canvas);
  chatWindow.appendChild(container);

  const labels = data.map(item => item.label);
  const values = data.map(item => item.value);

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Count',
        data: values,
        backgroundColor: '#4f46e5aa',
        borderColor: '#4f46e5',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: true }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function appendTable(data) {
  if (!data.length) {
    appendMessage('bot', 'No data to display.');
    return;
  }

  const table = document.createElement('table');
  table.className = 'data-table';

  // Header
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  Object.keys(data[0]).forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Body
  const tbody = document.createElement('tbody');
  data.forEach(row => {
    const tr = document.createElement('tr');
    Object.values(row).forEach(val => {
      const td = document.createElement('td');
      td.textContent = val;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  chatWindow.appendChild(table);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ============================================
// Voice Recognition
// ============================================
function initVoiceRecognition() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    micBtn.disabled = true;
    micBtn.title = 'Speech recognition not supported';
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognizer = new SpeechRecognition();
  recognizer.continuous = true;
  recognizer.interimResults = false;
  recognizer.lang = 'en-US';

  micBtn.addEventListener('click', () => {
    if (isListening) {
      recognizer.stop();
    } else {
      recognizer.start();
    }
  });

  recognizer.onstart = () => {
    isListening = true;
    micBtn.classList.add('listening');
    const icon = micBtn.querySelector('i');
    icon.className = 'fas fa-stop';
    showToast('Listening...', 'info');
  };

  recognizer.onend = () => {
    isListening = false;
    micBtn.classList.remove('listening');
    const icon = micBtn.querySelector('i');
    icon.className = 'fas fa-microphone';
  };

  recognizer.onresult = (event) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        const transcript = event.results[i][0].transcript.trim();
        userInput.value = transcript;
        handleVoiceCommand(transcript.toLowerCase());
      }
    }
  };

  recognizer.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    const errorMessages = {
      'no-speech': 'No speech detected',
      'audio-capture': 'Microphone not accessible',
      'not-allowed': 'Microphone permission denied',
      'network': 'Network error'
    };
    showToast(errorMessages[event.error] || 'Speech recognition error', 'error');
    recognizer.stop();
  };
}

function handleVoiceCommand(command) {
  if (command.includes('send message') || command.includes('send')) {
    sendBtn.click();
  } else if (command.includes('export pdf')) {
    triggerExport('pdf');
  } else if (command.includes('export excel')) {
    triggerExport('excel');
  } else if (command.includes('export csv')) {
    triggerExport('csv');
  } else if (command.includes('attach file')) {
    fileInput.click();
  } else if (command.includes('clear chat')) {
    clearChat();
  }
}

// ============================================
// Export Functionality
// ============================================
function triggerExport(format) {
  if (!lastBotResponse) {
    showToast('No data to export', 'warning');
    return;
  }

  let payload = {};
  if (lastBotResponse.table) payload.table_data = lastBotResponse.table;
  else if (lastBotResponse.chart) payload.chart_data = lastBotResponse.chart;
  else if (lastBotResponse.summary || lastBotResponse.reply) {
    payload.summary = lastBotResponse.summary || lastBotResponse.reply;
  } else {
    showToast('Nothing exportable', 'warning');
    return;
  }

  fetch(`/export/${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(res => {
      if (!res.ok) throw new Error('Export failed');
      return res.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export.${format === 'excel' ? 'xlsx' : format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(`Exported as ${format.toUpperCase()}`, 'success');
    })
    .catch(err => {
      console.error('Export error:', err);
      showToast('Failed to export file', 'error');
    })
    .finally(() => {
      exportDropdown.classList.remove('show');
    });
}

// ============================================
// Event Listeners
// ============================================

// Send message
sendBtn.addEventListener('click', () => {
  let message = userInput.value.trim();
  const hasFiles = fileInput.files.length > 0;

  if (editingMessageContent) {
    message = editingMessageContent.textContent.trim();
    editingMessageContent = null;
  }

  if (message || hasFiles) {
    sendMessage(message);
  } else {
    showToast('Please enter a message or attach a file', 'warning');
  }
});

// Enter key to send
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendBtn.click();
  }
});

// Auto-resize textarea
userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = userInput.scrollHeight + 'px';
});

// File input change
fileInput.addEventListener('change', updateFilePreview);

// Sidebar toggle
toggleSidebar.addEventListener('click', toggleSidebarVisibility);
closeSidebar.addEventListener('click', toggleSidebarVisibility);

// New chat
newChatBtn.addEventListener('click', startNewChat);

// Clear chat
clearChatBtn.addEventListener('click', clearChat);

// Save chat
saveChatBtn.addEventListener('click', openSaveChatModal);
closeSaveModal.addEventListener('click', closeSaveChatModal);
cancelSave.addEventListener('click', closeSaveChatModal);
confirmSave.addEventListener('click', saveCurrentChat);

// Dark mode toggle
darkModeToggle.addEventListener('click', toggleDarkMode);

// Export dropdown
exportToggle.addEventListener('click', (e) => {
  e.stopPropagation();
  exportDropdown.classList.toggle('show');
});

document.addEventListener('click', (e) => {
  if (exportDropdown && !exportDropdown.contains(e.target)) {
    exportDropdown.classList.remove('show');
  }
});

exportPdfBtn.addEventListener('click', () => triggerExport('pdf'));
exportExcelBtn.addEventListener('click', () => triggerExport('excel'));
exportCsvBtn.addEventListener('click', () => triggerExport('csv'));

// Close modal on outside click
saveChatModal.addEventListener('click', (e) => {
  if (e.target === saveChatModal) {
    closeSaveChatModal();
  }
});

// ============================================
// Initialize
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  initDarkMode();
  initVoiceRecognition();
  loadChatHistory();

  // Close sidebar by default on desktop
  if (window.innerWidth > 768) {
    sidebar.classList.add('closed');
  }
});
