//DOM content
const chatWindow = document.getElementById("chatWindow");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const messageActions = document.getElementById("messageActions");
const editMessageBtn = document.getElementById("editMessageBtn");
const deleteMessageBtn = document.getElementById("deleteMessageBtn");
const saveMessageBtn = document.getElementById("saveMessageBtn");
const cancelEditBtn = document.getElementById("cancelEditBtn");
const fileInput = document.getElementById("fileInput");

// File Selecting
fileInput.addEventListener("change", () => {
  const files = fileInput.files;
  if (files.length > 0) {
    const fileNames = Array.from(files).map(f => f.name).join(", ");
    alert(`✅ Files selected: ${fileNames}`);
  }
});

userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = userInput.scrollHeight + "px";
});
// Voice recognition setup
const micBtn = document.getElementById("micBtn");
const micIcon = micBtn.querySelector("i");


let recognizer = null;
let isListening = false;

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognizer = new SpeechRecognition();

  recognizer.continuous = true; // keep listening continuously
  recognizer.interimResults = false;
  recognizer.lang = "en-US";

  micBtn.addEventListener("click", () => {
    if (isListening) {
      recognizer.stop();
    } else {
      recognizer.start();
    }
  });

  recognizer.onstart = () => {
    isListening = true;
    micBtn.classList.add("listening");
    micIcon.classList.remove("fa-microphone");
    micIcon.classList.add("fa-stop");
    console.log("Voice recognition started");
  };

  recognizer.onend = () => {
    isListening = false;
    micBtn.classList.remove("listening");
    micIcon.classList.remove("fa-stop");
    micIcon.classList.add("fa-microphone");
    console.log("Voice recognition stopped");
    // Automatically restart after short delay to keep continuous
    // Only restart if user didn't manually stop
    if (micBtn.classList.contains("listening")) {
      recognizer.start();
    }
  };

  recognizer.onresult = (event) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        const transcript = event.results[i][0].transcript.trim();
        console.log("Recognized:", transcript);

        // Optionally: put transcript in user input field
        userInput.value = transcript;

        // Check voice commands
        handleVoiceCommand(transcript.toLowerCase());
      }
    }
  };

  recognizer.onerror = (event) => {
  console.error("Speech recognition error:", event.error);
  const errorMsgMap = {
    "no-speech": "No speech detected. Please try again.",
    "audio-capture": "Microphone not found or accessible.",
    "not-allowed": "Microphone permission denied.",
    "network": "Network error during speech recognition."
  };
  const msg = errorMsgMap[event.error] || `Speech recognition error: ${event.error}`;
  appendMessage("bot", "🎙️ " + msg);
  recognizer.stop();
};


} else {
  micBtn.disabled = true;
  micBtn.title = "Speech recognition not supported in your browser.";
}

// Handle voice commands to trigger actions
function handleVoiceCommand(command) {
  if (command.includes("export pdf")) {
    triggerExport("pdf");
  } else if (command.includes("export excel") || command.includes("export xlsx")) {
    triggerExport("excel");
  } else if (command.includes("export csv")) {
    triggerExport("csv");
  } else if (command.includes("attach file")) {
    const fileInput = document.getElementById("fileInput");
    if (fileInput) fileInput.click();
  } else if (command.includes("send message")) {
    const sendBtn = document.getElementById("sendBtn");
    if (sendBtn) sendBtn.click();
  } else {
    console.log("No matching command for:", command);
  }
}

// Edit the Input Message
sendBtn.addEventListener("click", () => {
  let message = userInput.value.trim();
  const fileInput = document.getElementById("fileInput");
  const hasFiles = fileInput.files.length > 0;

  // If editing a message, override with edited content
  if (editingMessageContent) {
    message = editingMessageContent.textContent.trim();
    editingMessageContent = null;
  }

  // ✅ Send if either message or file is present
  if (message || hasFiles) {
    sendMessage(message);
    userInput.value = "";
    userInput.style.height = "auto";
  } else {
    alert("❌ Please enter a message or attach a file.");
  }
});


// Handle Enter key
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendBtn.click();
});


//Sending Message

function sendMessage(message) {
  appendMessage("user", message);

  const userInput = document.getElementById("userInput");
  userInput.value = "";
  userInput.style.height = "auto";  // Resets textarea height

  const typingIndicator = document.createElement("div");
  typingIndicator.className = "message bot typing-indicator";
  for (let i = 0; i < 3; i++) {
    const dot = document.createElement("div");
    dot.className = "typing-dot";
    typingIndicator.appendChild(dot);
  }
  chatWindow.appendChild(typingIndicator);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  const files = document.getElementById("fileInput").files;
  const formData = new FormData();
  formData.append("message", message);
  for (let i = 0; i < files.length; i++) {
    formData.append("file", files[i]);  // Use same key for each file
  }

  fetch("/chat", {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      lastBotResponse = data;
      typingIndicator.remove();

      if (data.error) {
        appendMessage("bot", `⚠️ ${data.error}`);
      } else if (data.preview) {
      appendMessage("bot", "📝 File preview:\n" + data.preview);
      }else if (data.chart) {
        appendChart(data.chart);
      } else if (data.table) {
        appendTable(data.table);
      } else if (data.summary || data.reply) {
        appendMessage("bot", data.summary || data.reply);
      } else {
        appendMessage("bot", "🤖 Sorry, I couldn't understand that.");
      }
    })
    .catch((err) => {
      console.error(err);
      typingIndicator.remove();
      appendMessage("bot", "⚠️ Failed to fetch response.");
    });
}
let editingMessageContent = null;  // Stores the edited DOM element

// Edit Message 
function appendMessage(sender, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message-wrapper ${sender}`;

  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${sender}`;

  const messageContent = document.createElement("div");
  messageContent.className = "message-content";
  messageContent.textContent = text;

  messageDiv.appendChild(messageContent);
  wrapper.appendChild(messageDiv);

  if (sender === "user") {
    const actionIcons = document.createElement("div");
    actionIcons.className = "action-icons";

    const editBtn = document.createElement("button");
    editBtn.className = "edit-btn";
    editBtn.title = "Edit message";
    editBtn.textContent = "✏️";

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "delete-btn";
    deleteBtn.title = "Delete message";
    deleteBtn.textContent = "🗑️";

    const saveBtn = document.createElement("button");
    saveBtn.className = "save-btn";
    saveBtn.title = "Save changes";
    saveBtn.textContent = "💾";
    saveBtn.style.display = "none";

    const cancelBtn = document.createElement("button");
    cancelBtn.className = "cancel-btn";
    cancelBtn.title = "Cancel editing";
    cancelBtn.textContent = "❌";
    cancelBtn.style.display = "none";

    actionIcons.append(editBtn, deleteBtn, saveBtn, cancelBtn);
    wrapper.appendChild(actionIcons);

    let originalText = text;

    editBtn.addEventListener("click", () => {
      messageDiv.classList.add("editing");
      messageContent.contentEditable = "true";
      messageContent.focus();

      editBtn.style.display = "none";
      deleteBtn.style.display = "none";
      saveBtn.style.display = "inline-block";
      cancelBtn.style.display = "inline-block";
    });

    saveBtn.addEventListener("click", () => {
      messageContent.contentEditable = "false";
      messageDiv.classList.remove("editing");

      editBtn.style.display = "inline-block";
      deleteBtn.style.display = "inline-block";
      saveBtn.style.display = "none";
      cancelBtn.style.display = "none";

      originalText = messageContent.textContent;

      // Track the edited content for sending
      editingMessageContent = messageContent;
    });


    cancelBtn.addEventListener("click", () => {
      messageContent.textContent = originalText;
      messageContent.contentEditable = "false";
      messageDiv.classList.remove("editing");

      editBtn.style.display = "inline-block";
      deleteBtn.style.display = "inline-block";
      saveBtn.style.display = "none";
      cancelBtn.style.display = "none";
    });

    deleteBtn.addEventListener("click", () => {
      if (confirm("Are you sure you want to delete this message?")) {
        wrapper.remove();
      }
    });
  }

  document.getElementById("chatWindow").appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}



// Chart Function
function appendChart(data) {
  const canvas = document.createElement("canvas");
  const container = document.createElement("div");
  container.className = "chart-container";
  container.appendChild(canvas);
  chatWindow.appendChild(container);

  const labels = data.map((item) => item.label);
  const values = data.map((item) => item.value);

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Count",
        data: values,
        backgroundColor: "#007bff88",
        borderColor: "#007bff",
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: true },
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });

  chatWindow.scrollTop = chatWindow.scrollHeight;
}

//Table Function
function appendTable(data) {
  if (!data.length) {
    appendMessage("bot", "No data to display.");
    return;
  }

  const table = document.createElement("table");
  table.className = "data-table";

  // Header
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  Object.keys(data[0]).forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Body
  const tbody = document.createElement("tbody");
  data.forEach((row) => {
    const tr = document.createElement("tr");
    Object.values(row).forEach((val) => {
      const td = document.createElement("td");
      td.textContent = val;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  chatWindow.appendChild(table);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}
// Export Functions
// Cache DOM elements
const exportDropdown = document.querySelector(".export-dropdown");
const exportToggle = document.querySelector(".export-toggle");
const pdfBtn = document.getElementById("exportPdfBtn");
const excelBtn = document.getElementById("exportExcelBtn");
const csvBtn = document.getElementById("exportCsvBtn");

if (exportToggle) {
  exportToggle.addEventListener("click", (e) => {
    e.stopPropagation();
    exportDropdown.classList.toggle("show");
    console.log("Export toggle clicked. Dropdown:", exportDropdown.classList.contains("show"));
  });
}

document.addEventListener("click", (e) => {
  if (exportDropdown && !exportDropdown.contains(e.target)) {
    exportDropdown.classList.remove("show");
  }
});

function triggerExport(format) {
  console.log("Exporting format:", format, lastBotResponse);
  if (!lastBotResponse) {
    alert("No data to export.");
    return;
  }
  let payload = {};
  if (lastBotResponse.table) payload.table_data = lastBotResponse.table;
  else if (lastBotResponse.chart) payload.chart_data = lastBotResponse.chart;
  else if (lastBotResponse.summary || lastBotResponse.reply) payload.summary = lastBotResponse.summary || lastBotResponse.reply;
  else {
    alert("Nothing exportable.");
    return;
  }

  fetch(`/export/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(res => {
      console.log("Export response status:", res.status);
      if (!res.ok) throw new Error("Export failed. Status " + res.status);
      return res.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `export.${format === "excel" ? "xlsx" : format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    })
    .catch(err => {
      console.error("Export error:", err);
      alert("Failed to export file.");
    })
    .finally(() => {
      exportDropdown.classList.remove("show");
    });
}

if (pdfBtn) pdfBtn.addEventListener("click", () => triggerExport("pdf"));
if (excelBtn) excelBtn.addEventListener("click", () => triggerExport("excel"));
if (csvBtn) csvBtn.addEventListener("click", () => triggerExport("csv"));


 