from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import session, redirect, url_for, render_template
import mysql.connector
from deepface import DeepFace
import cv2
from flask import Flask, send_file
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import os
import json
from flask_bcrypt import Bcrypt
import random  
from emotion_analyzer import analyze_emotions
from emotion_analyzer import run_emotion_capture
from collections import Counter
from visualizations import generate_pie_chart, generate_bar_chart
app = Flask(__name__)
app.secret_key = '1a61f6c915ae006ae5e1717869c3c884'
bcrypt = Bcrypt(app)

questions_list = [
    "Tell me about yourself and your background.",
    "Why are you interested in this position?",
    "What are your biggest strengths and weaknesses?",
    "What are your salary expectations?",
    "Why do you want to work for this company?",
    "What are your career goals?",
    "Why should we hire you?",
    "Tell me about a time you worked effectively under pressure.",
    "Describe your experience with teamwork and collaboration?",
    "How do you stay organized and manage your time effectively?",
    "What are your technical skills and how do you stay updated?",
    "Tell me about a time you had to overcome a challenge.",
    "How do you handle criticism or feedback?",
    "Describe your communication skills.",
    "Are you comfortable working independently and taking initiative?",
    "Tell me about your experience with problem-solving.",
    "What are your biggest accomplishments to date?",
    "Describe a time you had to deal with a conflict at work.",
    "Tell me about a time you made a mistake and how you learned from it."
]

emotion_counter = Counter()
emotion_results = []

# Database Connection
"""db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jaswanthi@07",
    database="user_db"
)"""

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Jaswanthi@07",
        database="user_db"
    )

def get_today_interview_number(user_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM interview_overall_results 
        WHERE user_id = %s AND DATE(created_at) = CURDATE()
    """, (user_id,))
    count = cursor.fetchone()[0]
    return count + 1

def store_overall_emotions(user_id, overall_emotions):
    db = get_db_connection()
    cursor = db.cursor()
    emotions_json = json.dumps(overall_emotions)

    cursor.execute("""
        INSERT INTO interview_overall_results (user_id, overall_result)
        VALUES (%s, %s)
    """, (user_id, emotions_json))

    db.commit()
    return cursor.lastrowid  # interview_id


def store_emotion_results(results,user_id,interview_id):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Jaswanthi@07",
        database="user_db"
    )

    # 👇 Check if the DB connection is still active
    if not db.is_connected():
        db.reconnect()

    cursor = db.cursor()

    for item in results:
        question = item['question']
        emotions = item['emotions']  # This is a dictionary: {'happy': 70, 'neutral': 20, ...}\

        emotions_json = json.dumps(emotions)

        cursor.execute("""
                INSERT INTO emotion_results (user_id,interview_id,question,result)
                VALUES (%s, %s, %s, %s)
            """, (user_id, interview_id, question, emotions_json))

    db.commit()
    cursor.close()
    db.close()



"""cursor = db.cursor()
cursor.execute("USE user_db")"""


@app.route('/')
def home():
    #if request.method == "POST":
    user_name = None
    if 'user_id' in session:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM users WHERE id = %s", (session['user_id'],))
        result = cursor.fetchone()
        if result:
            user_name = result[0]
    selected_questions = random.sample(questions_list, 5)
    session['questions'] = selected_questions
    session['question_index'] = 0
    session['results'] = []
    #    return render_template('interview1.html', question=selected_questions[0])
    return render_template('about_us.html', logged_in='user_id' in session, user_name=user_name)



@app.route('/start_interview')
def start_interview():
    # Display the first question from session
    first_question = session['questions'][0]
    return render_template('interview1.html', question=first_question)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    db = get_db_connection()
    cursor = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('signup'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            cursor.execute("INSERT INTO users (name,email, password) VALUES (%s,%s, %s)", (name,email, hashed_password))
            db.commit()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash("Email already exists!", "danger")
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    db = get_db_connection()
    cursor = db.cursor()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result:
            user_id, stored_password = result
            if bcrypt.check_password_hash(stored_password, password):
                session["user_id"] = user_id
                session["email"] = email
                flash("Login successful!", "success")
                return redirect(url_for("home"))
            else:
                flash("Invalid credentials", "danger")
        else:
            flash("User not found", "danger")

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))
    return render_template('dashboard.html', logged_in=True)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route('/interview')
def interview():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))
    return render_template('interview.html')


def analyze_video_emotions(video_path):
    emotion_counts = []
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        try:
            #face_obj = DeepFace.extract_faces(img_path="input.jpg")  # Get only face  
            #face = face_obj[0]["face"] 
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            if isinstance(result, list) and result:
                emotion_counts.append(result[0]['dominant_emotion'])
        except:
            pass

    cap.release()  # <-- CRUCIAL to release before next file operation

    total = len(emotion_counts)
    freq = Counter(emotion_counts)
    return {emotion: round((count / total) * 100, 2) for emotion, count in freq.items()} if total else {}

@app.route('/interview1')
def interview1():
    index = session.get('question_index', 0)
    if index >= 2:
        return redirect(url_for('report'))
    question = questions_list[index]
    return render_template('interview1.html', question=question, index=index)


@app.route('/analyzing', methods=['POST'])
def analyzing():
    index = session.get('question_index', 0)
    question = questions_list[index]

    # Save uploaded video file
    file = request.files['video']
    video_path = f"temp_video_{index}.mp4"
    file.save(video_path)

    # Analyze emotions
    emotions = analyze_video_emotions(video_path)

    # Store result
    results = session.get('results', {})
    results[question] = emotions
    session['results'] = results

    # Move to next question
    session['question_index'] = index + 1

    if session['question_index'] >= 2:
        return redirect(url_for('report'))
    else:
        return redirect(url_for('interview1'))


def calculate_overall_emotions(results):
    total_emotions = {}
    total_score = 0

    for item in results:
        for emotion, score in item['emotions'].items():
            total_emotions[emotion] = total_emotions.get(emotion, 0) + score
            total_score += score

    # Convert to percentages
    overall_percentages = {emotion: round((score / total_score) * 100, 2) for emotion, score in total_emotions.items()}
    print("📊 Calculated Overall Emotions:", overall_percentages)
    return overall_percentages

def generate_feedback(overall_emotions):
    if not overall_emotions:  # Check if the dictionary is empty
        return "No facial emotions detected. Please check video quality or lighting conditions."
    dominant_emotion = max(overall_emotions, key=overall_emotions.get)
    feedback = ""

    if dominant_emotion == 'happy':
        feedback = "Great job! You appeared confident and positive throughout the interview. Keep maintaining that enthusiasm!"
    elif dominant_emotion == 'neutral':
        feedback = "You remained composed and calm. Try to add a bit more energy or emotional engagement to stand out better."
    elif dominant_emotion == 'sad':
        feedback = "You seemed low on energy or a bit nervous. Try to practice smiling and maintaining a more enthusiastic tone."
    elif dominant_emotion == 'angry':
        feedback = "There were signs of frustration or tension. Practice staying relaxed and approachable in your responses."
    elif dominant_emotion == 'surprised':
        feedback = "There were signs of surprise or confusion. Try to stay composed and expect common questions to reduce uncertainty."
    elif dominant_emotion == 'fear':
        feedback = "You seemed anxious or fearful during the interview. Practicing mock interviews can help you gain more confidence."
    elif dominant_emotion == 'disgust':
        feedback = "Your expressions may have shown discomfort or disinterest. Try to appear more engaged and enthusiastic during the conversation."
    else:
        feedback = "Maintain a balanced emotional tone throughout the interview to make a stronger impression."

    return feedback


@app.route('/submit', methods=['POST'])
def submit():
    if 'questions' not in session:
        return redirect(url_for('home'))
    index = session.get('question_index', 0)
    question = session['questions'][index]
    video = request.files['video']

    video_path = f"temp_video_{index}.webm"
    video.save(video_path)

    emotions = analyze_video_emotions(video_path)  # Your custom function to analyze video
    session['results'].append({'question': question, 'emotions': emotions})
    os.remove(video_path)

    session['question_index'] = index + 1

    if session['question_index'] >= len(session['questions']):
        user_id = session.get('user_id')  # Ensure this is set after login

        # Store to DB
        question = session['questions'][session['question_index'] - 1]
        #report_id = store_emotion_report(user_id,question)
        
        
        overall_emotions = calculate_overall_emotions(session['results'])
        interview_number = get_today_interview_number(user_id)      
        interview_id = store_overall_emotions(user_id, overall_emotions)
        store_emotion_results(session['results'],user_id,interview_id)
        feedback = generate_feedback(overall_emotions)
        charts = {}
    # Overall pie chart
        charts['overall'] = generate_pie_chart(overall_emotions, "Overall Emotion Distribution")

        # Per-question bar charts
        for result in session['results']:
            question = result['question']
            emotions = result['emotions']
            charts[question] = generate_bar_chart(emotions, f"{question} Emotion Distribution")


        return render_template('report.html', results=session['results'],overall_emotions=overall_emotions,feedback=feedback,charts=charts)

    if session['question_index'] >= len(session['questions']):
        return render_template('report.html', results=session['results'])
    else:
        next_question = session['questions'][session['question_index']]
        return render_template('interview1.html', question=next_question)
 

@app.route('/report')
def report():
    results_list = session.get('results', [])
    overall_emotions = calculate_overall_emotions(results_list)
    
    return render_template('report.html', results=results_list,overall_emotions=overall_emotions)

if __name__ == '__main__':
    app.run(debug=True)

