import os
import json
import random
from typing import Dict
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from transformers import pipeline
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
    create_engine,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///users.db")
is_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine)
metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(150), unique=True, nullable=False),
    Column("email", String(255), unique=True, nullable=False),
    Column("password", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

user_chat_history_table = Table(
    "user_chat_history",
    metadata,
    Column("user_id", Integer, primary_key=True),
    Column("chat_history", Text),
    Column("last_updated", DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
)

mood_checkins_table = Table(
    "mood_checkins",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("mood", Integer, nullable=False),
    Column("note", Text),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

journal_entries_table = Table(
    "journal_entries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("title", String(200)),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

CRISIS_KEYWORDS = {
    "suicide",
    "kill myself",
    "end my life",
    "self harm",
    "self-harm",
    "hurt myself",
    "can't go on",
    "cant go on",
}

class AdvancedMentalHealthChatbot:
    def __init__(self):
        # Emotion Detection
        self.emotion_classifier = pipeline(
            "text-classification", 
            model="j-hartmann/emotion-english-distilroberta-base", 
            return_all_scores=True
        )
        
        # LLM Initialization
        self.llm = ChatGroq(
            temperature=0.7,
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            model_name="llama-3.3-70b-versatile"
        )
        
        # Store conversation contexts for each user
        self.user_conversations = {}
        
        # Predefined Emotion Response Templates
        self.emotion_responses = {
            'anger': [
                "I sense you're feeling angry. Can you tell me more about what's causing this frustration?",
                "Anger can be a powerful emotion. Would you like to explore what's triggering these feelings?",
                "It sounds like something has really upset you. I'm here to listen without judgment."
            ],
            'sadness': [
                "I hear that you're feeling sad. Would you like to talk about what's making you feel this way?",
                "Sometimes sadness can feel overwhelming. I'm here to support you through this.",
                "Your feelings are valid. Can you share more about what's causing your sadness?"
            ],
            'joy': [
                "It's wonderful to hear you're feeling positive! What's bringing you joy?",
                "Happiness is beautiful. I'd love to hear more about what's making you feel good.",
                "Enjoying a good moment? Tell me more about what's making you smile."
            ],
            'neutral': [
                "How are you really feeling right now?",
                "Sometimes it's hard to pinpoint exactly what we're feeling. Let's explore that together.",
                "I'm here to listen and understand what's going on in your mind."
            ]
        }
    
    def get_user_context(self, user_id):
        """Get or create a conversation context for a specific user"""
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = {
                'emotional_history': [],
                'current_emotion': None,
                'conversation_depth': 0,
                'last_topic': None
            }
            
            # Try to load from database if exists
            try:
                db_session = SessionLocal()
                result = db_session.execute(
                    select(user_chat_history_table.c.chat_history)
                    .where(user_chat_history_table.c.user_id == user_id)
                ).fetchone()
                db_session.close()
                
                if result and result[0]:
                    # Load saved history from database
                    history_data = json.loads(result[0])
                    self.user_conversations[user_id] = history_data
            except Exception as e:
                print(f"Error loading chat history for user {user_id}: {e}")
                
        return self.user_conversations[user_id]
        
    def save_user_context(self, user_id, context):
        """Save a user's conversation context to the database"""
        try:
            db_session = SessionLocal()
            context_json = json.dumps(context)
            existing = db_session.execute(
                select(user_chat_history_table.c.user_id)
                .where(user_chat_history_table.c.user_id == user_id)
            ).fetchone()
            if existing:
                db_session.execute(
                    user_chat_history_table.update()
                    .where(user_chat_history_table.c.user_id == user_id)
                    .values(chat_history=context_json, last_updated=func.now())
                )
            else:
                db_session.execute(
                    user_chat_history_table.insert()
                    .values(user_id=user_id, chat_history=context_json)
                )
            db_session.commit()
            db_session.close()
        except Exception as e:
            print(f"Error saving chat history for user {user_id}: {e}")
    
    def detect_emotion(self, message: str) -> str:
        """Detect primary emotion in the message"""
        try:
            emotions = self.emotion_classifier(message)[0]
            emotion_map = {e['label']: e['score'] for e in emotions}
            primary_emotion = max(emotion_map, key=emotion_map.get)
            
            emotion_mapping = {
                'anger': 'anger',
                'sadness': 'sadness',
                'joy': 'joy',
                'love': 'joy',
                'surprise': 'neutral',
                'fear': 'sadness',
                'disgust': 'anger'
            }
            
            return emotion_mapping.get(primary_emotion, 'neutral')
        except Exception as e:
            print(f"Emotion detection error: {e}")
            return 'neutral'
    
    def generate_contextual_response(self, user_id: int, user_message: str) -> Dict:
        """Generate a contextually aware and empathetic response for a specific user"""
        normalized_message = user_message.lower()
        if any(keyword in normalized_message for keyword in CRISIS_KEYWORDS):
            return {
                'response': (
                    "I'm really sorry you're feeling this way. You deserve support, and you don't have "
                    "to go through this alone. If you're in immediate danger or thinking about harming "
                    "yourself, please contact local emergency services right now. If you're in the U.S., "
                    "you can call or text 988 for the Suicide & Crisis Lifeline. If you're elsewhere, I can "
                    "help find a local crisis line."
                ),
                'emotion': 'sadness',
                'interactive_options': [
                    "Find local help",
                    "I'm safe right now",
                    "Talk to me"
                ],
                'crisis_resources': True
            }
        # Get user-specific context
        context = self.get_user_context(user_id)
        
        current_emotion = self.detect_emotion(user_message)
        context['current_emotion'] = current_emotion
        
        # Adjust response length based on conversation depth
        conversation_depth = context['conversation_depth']
        if conversation_depth < 3:
            length_guidance = "Keep your response brief and focused (20 words). Be direct and supportive."
        elif conversation_depth < 10:
            length_guidance = "Provide a moderate-length response (25 words). Balance brevity with meaningful support."
        else:
            length_guidance = "You can provide a more detailed response if needed(max 35 words), but remain focused and concise."
        
        prompt_template = PromptTemplate(
            input_variables=["emotion", "message", "context", "length_guidance", "depth"],
            template="""
            You are a compassionate and emotionally intelligent mental health support chatbot.

Your tone should be warm, natural, and sincere—like a trusted friend who truly listens without judgment. 
Be gentle and emotionally present. Respond in a conversational, human way that doesn’t sound robotic or rehearsed.

Emotion detected: {emotion}
Recent conversation: {context}
Conversation depth: {depth}

User: {message}

{length_guidance}

Your job:
- Start by validating what they’re feeling in a real, personal way.
- Don’t overanalyze. Just *be there* with them.
- Sound human. Use contractions (“I’m”, “you’re”, “it’s”, etc).
- Avoid clichés—be specific and emotionally grounded.
- Offer one clear, gentle suggestion if appropriate, but don’t force solutions.
- End with a caring, open-ended follow-up or gentle question to keep the door open. But dont be blunt if he wants to stop convo then give a comforting endingss
If the user seems like they’re wrapping up or feeling calmer, respond without pushing another question

Keep it supportive, short-to-medium length, and sincere.
If the user seems done or at peace, let the conversation soften to a natural close.
Respond:"""
        )
        
        context_history = " ".join(context['emotional_history'][-3:])
        
        try:
            prompt = prompt_template.format(
                emotion=current_emotion,
                message=user_message,
                context=context_history,
                length_guidance=length_guidance,
                depth=conversation_depth
            )
            response = self.llm.invoke(prompt).content
        except Exception as e:
            response = random.choice(
                self.emotion_responses.get(current_emotion, 
                self.emotion_responses['neutral'])
            )
        
        # Update user context
        context['emotional_history'].append(user_message)
        context['conversation_depth'] += 1
        
        # Save updated context
        self.save_user_context(user_id, context)
        
        return {
            'response': response,
            'emotion': current_emotion,
            'interactive_options': [
                "Tell me more",
                "How can I help?",
                "I want to understand better"
            ]
        }

# Flask App Setup
app = Flask(__name__)
CORS(app)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
)

chatbot = AdvancedMentalHealthChatbot()

def init_db():
    metadata.create_all(engine)

init_db()

@app.route('/')
def home():
    quotes = [
        "You are stronger than you think.",
        "This too shall pass.",
        "Your feelings are valid.",
        "You deserve to be happy."
    ]
    return render_template("home.html", quotes=quotes)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords don't match!", 'error')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        db_session = SessionLocal()
        try:
            db_session.execute(
                users_table.insert().values(
                    username=username,
                    email=email,
                    password=hashed_password,
                )
            )
            db_session.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db_session.rollback()
            flash('Username or email already exists!', 'error')
        finally:
            db_session.close()

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db_session = SessionLocal()
        user = db_session.execute(
            select(users_table)
            .where(users_table.c.username == username)
        ).fetchone()
        db_session.close()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('chat'))
        else:
            flash('Invalid username or password!', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        flash('Please log in to access the chatbot.', 'error')
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('chat.html')

    elif request.method == 'POST':
        # Check content type
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 415
            
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Invalid request format'}), 400
            
        user_message = data['message']
        user_id = session['user_id']
        
        try:
            response = chatbot.generate_contextual_response(user_id, user_message)
            return jsonify(response)
        except Exception as e:
            print(f"Error processing message: {e}")
            return jsonify({
                'response': "I'm here for you. Let's try again.",
                'interactive_options': [
                    "Retry conversation",
                    "Start over",
                    "Get support"
                ]
            }), 500


@app.route('/checkin', methods=['POST'])
def checkin():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415

    data = request.get_json()
    mood = data.get('mood')
    note = data.get('note', '')

    if mood is None or not isinstance(mood, int) or mood < 1 or mood > 5:
        return jsonify({'error': 'Mood must be an integer between 1 and 5'}), 400

    db_session = SessionLocal()
    db_session.execute(
        mood_checkins_table.insert().values(
            user_id=session['user_id'],
            mood=mood,
            note=note,
        )
    )
    db_session.commit()
    db_session.close()

    return jsonify({'status': 'saved'})


@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    if request.method == 'POST':
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 415

        data = request.get_json()
        title = data.get('title')
        content = data.get('content')

        if not content:
            return jsonify({'error': 'Content is required'}), 400

        db_session = SessionLocal()
        db_session.execute(
            journal_entries_table.insert().values(
                user_id=session['user_id'],
                title=title,
                content=content,
            )
        )
        db_session.commit()
        db_session.close()

        return jsonify({'status': 'saved'})

    db_session = SessionLocal()
    entries = db_session.execute(
        select(
            journal_entries_table.c.id,
            journal_entries_table.c.title,
            journal_entries_table.c.content,
            journal_entries_table.c.created_at,
        ).where(journal_entries_table.c.user_id == session['user_id'])
        .order_by(journal_entries_table.c.created_at.desc())
        .limit(20)
    ).fetchall()
    db_session.close()

    return jsonify({
        'entries': [
            {
                'id': entry.id,
                'title': entry.title,
                'content': entry.content,
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in entries
        ]
    })


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
