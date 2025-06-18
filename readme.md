# Advanced Mental Health Chatbot

A Flask-based AI-powered mental health support chatbot that uses NLP and emotion detection to provide empathetic, contextual, and human-like responses.

## Features

- Emotion detection using Hugging Face Transformers
- Context-aware response generation using Groq LLM (LLaMA-3.3-70B)
- Personalized user conversations with session-based memory
- SQLite database for user authentication and chat history
- Secure password handling with hashing
- Beautiful UI using HTML templates
- Flask-based backend with REST API

## Tech Stack

- Python
- Flask
- SQLite
- Hugging Face Transformers
- LangChain + Groq
- HTML/CSS (Flask Templates)

---

## Getting Started

### 1. Clone the Repository

git clone https://github.com/your-username/chattyauthentication.git
cd chattyauthentication

### 2. Create and Activate Virtual Environment

python -m venv venv

#### On Windows (PowerShell):

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\Activate

#### On CMD:

venv\Scripts\activate.bat

#### On macOS/Linux:

source venv/bin/activate

---

### 3. Install Dependencies

pip install -r requirements.txt

If you don’t have a requirements.txt, install manually:

pip install flask flask-cors transformers langchain langchain-groq werkzeug

---

### 4. Run the App

python app.py

Then visit: http://127.0.0.1:5000/

---

## Environment Variables

Replace the groq_api_key inside the script with your actual Groq API Key:

groq_api_key="your_groq_api_key"

For better security, consider using environment variables or a .env file.

---

## Project Structure

chattyauthentication/
│
├── app.py                  # Main Flask app
├── users.db                # SQLite database (auto-generated)
├── templates/              # HTML templates
│   ├── home.html
│   ├── signup.html
│   ├── login.html
│   └── chat.html
├── static/                 # Optional CSS/JS files
├── venv/                   # Virtual environment
└── README.md

---

## Future Improvements

- Add journaling feature for users
- Integrate daily mood tracker
- Admin panel to manage conversations
- Use environment variables for API keys

---

## Acknowledgements

- Hugging Face for emotion detection model
- Groq + LangChain for LLM integration

---

## License

MIT License — feel free to use and modify for educational purposes.
