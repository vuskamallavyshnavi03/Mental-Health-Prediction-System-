from flask import Flask, render_template, request, jsonify, redirect,session
import json, random, pickle
import nltk
from nltk.stem import WordNetLemmatizer
from gtts import gTTS
import uuid
import os
from flask_sqlalchemy import SQLAlchemy

nltk.download('punkt')
nltk.download('wordnet')

app = Flask(__name__)
app.secret_key= "mentalhealth123"

lemmatizer = WordNetLemmatizer()

# Load data
with open("intents.json") as f:
    intents = json.load(f)
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))
clf = pickle.load(open("model.pkl", "rb"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method =='POST':
        email = request.form.get('email')
        session['email'] = email
        return redirect('/home')
    return render_template("login.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/quiz")
def quiz():
    return render_template("quiz.html")

@app.route("/doctor")
def doctor():
    return render_template("doctor.html")

@app.route("/appointment")
def appointment():
    return render_template("appointment.html")

@app.route("/payment")
def payment():
    doctor = request.args.get("doctor")
    name = request.args.get("name")
    email = request.args.get("email")
    date = request.args.get("date")
    time = request.args.get("time")
    mode = request.args.get("mode")
    return render_template("payment.html", doctor=doctor, name=name, email=email, daye=date, time=time, mode=mode)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route('/profile')
def profile():
    print("Session Email:",session.get('email'))
    email = session.get('email')
    if not email:
        return redirect('/login')
    user = Survey.query.filter_by(email=email).first()
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.get_json()
    msg = data.get("message", "")
    lang = data.get("lang", "en")

    tokens = nltk.word_tokenize(msg)
    cleaned = " ".join([lemmatizer.lemmatize(w.lower()) for w in tokens if w.isalpha()])
    X = vectorizer.transform([cleaned])
    probs = clf.predict_proba(X)[0]
    max_idx = probs.argmax()

    if probs[max_idx] < 0.3:
        reply = "I'm not sure I understand. Could you rephrase?"
    else:
        tag = clf.classes_[max_idx]
        reply = random.choice(next(i["responses"] for i in intents["intents"] if i["tag"] == tag))

    audio_path = ""
    try:
        tts = gTTS(reply, lang=lang)
        filename = f"static/audio/{uuid.uuid4().hex}.mp3"
        os.makedirs("static/audio", exist_ok=True)
        tts.save(filename)
        audio_path = "/" + filename
    except Exception:
        pass

    return jsonify({"response": reply, "audio": audio_path})

# 📌 SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///survey.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model
class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    email = db.Column(db.String(100))
    mood = db.Column(db.String(50))

# ✅ Create tables before first request
def create_tables():
    db.create_all()

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    age = request.form.get('age')
    gender = request.form.get('gender')
    email = request.form.get('email')
    mood = request.form.get('mood')

    entry = Survey(name=name, age=age, gender=gender, email=email, mood=mood)
    db.session.add(entry)
    db.session.commit()
    session['email'] = email
    return redirect('/home')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)