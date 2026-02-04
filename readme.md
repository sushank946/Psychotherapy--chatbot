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
- Crisis keyword detection with support messaging
- Mood check-ins and journaling APIs for user wellness tracking

## Tech Stack

- Python
- Flask
- SQLite (local) / PostgreSQL (production)
- Hugging Face Transformers
- LangChain + Groq
- HTML/CSS (Flask Templates)
- SQLAlchemy + Gunicorn

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

Use environment variables for secrets and deployment configuration:

- `GROQ_API_KEY` (required for LLM responses)
- `SECRET_KEY` (Flask session secret)
- `DATABASE_URL` (SQLite or PostgreSQL connection string)
- `SESSION_COOKIE_SECURE` (`true` in production behind HTTPS)

Copy `.env.example` to `.env` and fill in values.

Example:

```
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=replace-with-strong-secret
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/psychotherapy
SESSION_COOKIE_SECURE=true
```

## API Endpoints

- `POST /chat` (JSON) - chatbot conversation
- `POST /checkin` (JSON) - daily mood check-in (1-5 scale)
- `POST /journal` (JSON) - create a journal entry
- `GET /journal` - list recent journal entries
- `GET /health` - health check for load balancers

---

## Project Structure

chattyauthentication/
│
├── app.py                  # Main Flask app
├── users.db                # SQLite database (auto-generated)
├── docker-compose.yml       # Local Docker stack (app + Postgres)
├── Dockerfile               # Production container build
├── .env.example             # Sample environment variables
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

- Admin panel to manage conversations
- Export chat/journal history
- Multi-language support
- Use environment variables for API keys

## Production Deployment (Zero Downtime)

This project is ready for containerized deployment with Gunicorn and PostgreSQL.
For zero-downtime deploys, use a platform that supports rolling deployments
and a shared database (Render, Railway, Fly.io, or Kubernetes).

### Docker (local)

```
cp .env.example .env
docker compose up --build
```

### Gunicorn (production)

```
gunicorn app:app -b 0.0.0.0:5000 --workers 2 --threads 4 --timeout 120
```

---

## Acknowledgements

- Hugging Face for emotion detection model
- Groq + LangChain for LLM integration

---

## License

MIT License — feel free to use and modify for educational purposes.
