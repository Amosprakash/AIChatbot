# AI Chat Assistant 🤖

[![Python Version](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.1+-green)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Overview 📝

An advanced AI-powered chatbot with document analysis, data querying, and conversational capabilities. Built with Flask, OpenAI GPT-4, and a modern, responsive UI featuring dark mode, chat history management, and comprehensive export options.

---

## ✨ New Features & Improvements

### 🎨 **Modern UI Redesign**
- **Beautiful Interface**: Clean, modern design with smooth animations
- **Dark Mode**: Toggle between light and dark themes with persistent preference
- **Better Color Scheme**: Professional indigo blue theme with improved contrast
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Smooth Animations**: Slide-in messages, typing indicators, and transitions

### 💬 **Chat History Management**
- **Save Conversations**: Save and name your chat sessions
- **Load Previous Chats**: Access your conversation history anytime
- **Delete Chats**: Remove unwanted conversations
- **Sidebar Navigation**: Easy access to all saved chats
- **Active Chat Indication**: See which chat you're currently viewing

### 🛠️ **Enhanced User Experience**
- **Toast Notifications**: Beautiful, non-intrusive alerts for all actions
- **Copy Messages**: One-click copy for any message (bot or user)
- **Clear Chat**: Quickly start fresh while keeping history
- **File Preview**: See attached files before sending
- **Improved File Upload**: Visual feedback with file tags and remove buttons
- **Message Actions**: Edit, delete, and copy messages easily

### 🔒 **Backend Improvements**
- **Environment Variables**: Secure configuration for sensitive data
- **Better Error Handling**: Comprehensive logging and error messages
- **Chat Persistence**: Server-side chat history storage
- **REST API**: Clean endpoints for chat management

### 🎤 **Voice & Interaction**
- **Voice Commands**: Control the app with voice (send, export, attach, clear)
- **Speech-to-Text**: Integrated Web Speech API
- **Visual Feedback**: Animated microphone button while listening

---

## 🚀 Core Features

### 📄 **Document Processing**
- Multi-format support: PDF, Word, Excel, CSV, TXT, Images
- OCR for scanned documents
- Multi-document analysis and synthesis
- Document relevance checking
- Automatic summarization

### 📊 **Data Analytics**
- Natural language to SQL query generation
- Automatic chart creation from data
- Table visualization
- Export to PDF, Excel, CSV
- SQL injection protection

### 💡 **AI Capabilities**
- Powered by OpenAI GPT-4.1-mini
- Context-aware conversations
- Question answering from documents
- Data summarization and insights
- Voice recognition and commands

---

## 🎯 Quick Features Guide

| Feature | How to Use |
|---------|-----------|
| **Dark Mode** | Click moon/sun icon in header |
| **Save Chat** | Click save icon, enter chat name |
| **Load Chat** | Open sidebar, click on saved chat |
| **Copy Message** | Hover over message, click copy icon |
| **Clear Chat** | Click trash icon in header |
| **Voice Input** | Click microphone, speak your message |
| **File Upload** | Click paperclip, select files |
| **Export Data** | Click download icon, choose format |
| **Edit Message** | Hover over user message, click edit |

---

## 💻 Installation

### Prerequisites
- Python 3.10 or higher
- OpenAI API key
- SQL Server (optional, for database queries)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/Amosprakash/AIChatbot.git
cd AIChatbot
```

2. **Create a virtual environment**
```bash
python -m venv .venv
```

3. **Activate the environment**

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Configure environment variables**

Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here

# Optional: SQL Server Configuration
SQL_SERVER=your_server_address
SQL_DATABASE=your_database_name
SQL_UID=your_username
SQL_PWD=your_password
```

6. **Run the application**
```bash
python myapp.py
```

The application will be available at `http://localhost:5000`

---

## 📁 Project Structure

```
AIChatbot/
│
├── myapp.py              # Main Flask application
├── fileread.py           # Document processing module
├── export.py             # Data export functionality
├── summarize.py          # Document summarization
├── new.py                # SQL safety and pattern detection
├── filedownload.py       # File download handler
├── requirements.txt      # Python dependencies
├── test.wsgi            # WSGI configuration
│
├── templates/
│   └── index.html       # Main UI template
│
├── static/
│   ├── style.css        # Modern, dark-mode enabled styles
│   ├── script.js        # Frontend functionality
│   └── typo.js          # Spell checker library
│
├── uploads/             # User uploaded files
├── dictioniaries/       # Spell check dictionaries
└── README.md            # This file
```

---

## 🎨 UI Themes

### Light Mode
- Clean white background
- Indigo blue accents
- Excellent readability
- Professional appearance

### Dark Mode
- Slate dark background
- Reduced eye strain
- Consistent branding
- Persistent preference

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main chat interface |
| `/chat` | POST | Send message and get response |
| `/save-chat` | POST | Save current conversation |
| `/load-chat/<id>` | GET | Load saved conversation |
| `/list-chats` | GET | List all saved chats |
| `/delete-chat/<id>` | DELETE | Delete a saved chat |
| `/export/pdf` | POST | Export data as PDF |
| `/export/excel` | POST | Export data as Excel |
| `/export/csv` | POST | Export data as CSV |
| `/download-file/<path>` | GET | Download uploaded file |

---

## 🎯 Usage Examples

### Document Analysis
1. Click the paperclip icon
2. Select one or more documents
3. Ask questions about the content
4. Get AI-powered insights

### Data Queries
1. Type a natural language question
2. AI generates and executes SQL query
3. View results as charts or tables
4. Export in your preferred format

### Voice Commands
1. Click the microphone icon
2. Say "send message" to send
3. Say "export pdf" to export
4. Say "clear chat" to start fresh

---

## 🛡️ Security Features

- Environment variable configuration
- SQL injection prevention
- Secure file upload handling
- Path traversal protection
- Input validation and sanitization
- Session-based authentication

---

## 🚀 Performance Optimizations

- File content caching with MD5 hashing
- Efficient document chunking
- Optimized SQL query generation
- Client-side localStorage for preferences
- Smooth CSS transitions and animations

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 Changelog

### Version 2.0.0 (Latest)

**Major UI/UX Improvements:**
- ✅ Complete UI redesign with modern aesthetics
- ✅ Dark mode toggle with persistent preference
- ✅ Toast notifications for all user actions
- ✅ Improved file upload with visual preview
- ✅ Better responsive design for mobile

**New Features:**
- ✅ Chat history management (save/load/delete)
- ✅ Copy message functionality
- ✅ Clear chat without losing history
- ✅ Sidebar for chat navigation
- ✅ Enhanced message actions

**Backend Improvements:**
- ✅ Environment variable configuration
- ✅ Comprehensive logging
- ✅ Better error handling
- ✅ Chat persistence endpoints
- ✅ Secure database connection

---

## 📄 License

MIT License © [Amosprakash](https://github.com/Amosprakash)

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Flask framework
- Chart.js for data visualization
- Font Awesome for icons
- Web Speech API for voice recognition

---

## 📧 Contact

For questions, suggestions, or issues:
- GitHub: [@Amosprakash](https://github.com/Amosprakash)
- Issues: [GitHub Issues](https://github.com/Amosprakash/AIChatbot/issues)

---

**Made with ❤️ by Amosprakash**
