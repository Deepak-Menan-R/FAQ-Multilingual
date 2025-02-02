import sqlite3
import redis
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from googletrans import Translator
from bs4 import BeautifulSoup
from db.init_db import create_db
from flask_caching import Cache

app = Flask(__name__)
app.secret_key = 'f8777e969dd3b755659226a624d28ace'  
DB_PATH = "db/faq.db"
create_db()

# Redis Cache Configuration
cache = Cache(app, config={
    'CACHE_TYPE': 'RedisCache', 
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})
redis_client = redis.StrictRedis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    email = session['user']
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT question, answer FROM faqs")
            faqs = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error fetching FAQs from the database."

    return render_template('index.html', email=email, faqs=faqs)

@app.route('/api/faqs/', methods=['GET'])
def translate_faqs():
    lang = request.args.get('lang', 'en')
    cache_key = f"faqs_{lang}"

    # Check Redis cache
    try:
        cached_faqs = redis_client.get(cache_key)
        if cached_faqs:
            faqs = eval(cached_faqs)
        else:
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT question, answer FROM faqs")
                    faqs = cursor.fetchall()

                translated_faqs = []
                if lang != 'en':
                    translator = Translator()
                    for question, answer in faqs:
                        try:
                            translated_question = translator.translate(question, dest=lang).text
                            soup = BeautifulSoup(answer, "html.parser")
                            for tag in soup.find_all(text=True):
                                translated_text = translator.translate(tag, dest=lang).text
                                tag.replace_with(translated_text)
                            translated_answer = str(soup)
                            translated_faqs.append((translated_question, translated_answer))
                        except Exception as e:
                            print(f"Translation error: {e}")
                            translated_faqs.append((question, answer))  # In case of error, keep original text
                else:
                    translated_faqs = faqs

                # Store translated FAQs in Redis cache (1-hour expiry)
                redis_client.setex(cache_key, 3600, str(translated_faqs))
                faqs = translated_faqs
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                return "Error fetching FAQs from the database."
            except Exception as e:
                print(f"Error: {e}")
                return "Error while translating FAQs."
    except redis.RedisError as e:
        print(f"Redis cache error: {e}")
        return "Error connecting to the cache service."

    return render_template('index.html', faqs=faqs, lang=lang)

@app.route('/admin', methods=['GET'])
def admin():
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, question, answer FROM faqs")
            faqs = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error fetching FAQs from the database."

    return render_template('admin.html', email=session['user'], faqs=faqs)

@app.route('/edit_faq/<int:faq_id>', methods=['GET'])
def edit_faq(faq_id):
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, question, answer FROM faqs WHERE id = ?", (faq_id,))
            faq = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error fetching FAQ from the database."

    return render_template('edit_faq.html', faq=faq)

@app.route('/update_faq/<int:faq_id>', methods=['POST'])
def update_faq(faq_id):
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    question = request.form['question']
    answer = request.form['answer']
    print(f"Updating FAQ with ID: {faq_id} to question: {question} and answer: {answer}")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE faqs SET question = ?, answer = ? WHERE id = ?", (question, answer, faq_id))
            conn.commit()

        # Invalidate cache for all languages
        redis_client.flushdb()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error updating FAQ in the database."

    return redirect(url_for('admin'))


@app.route('/add_faq', methods=['POST'])
def add_faq():
    if 'user' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    question = request.form['question']
    answer = request.form['answer']  

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO faqs (question, answer) VALUES (?, ?)", (question, answer))
            conn.commit()

        # Invalidate cache for all languages
        redis_client.flushdb()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error adding FAQ to the database."

    return redirect(url_for('admin'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == 'admin@gmail.com' and password == 'admin123':
            session['user'] = email  
            session['role'] = 'Admin'  
            return redirect(url_for('admin')) 
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()

            if user and user[0] == password:
                session['user'] = email  
                session['role'] = 'User' 
                return redirect(url_for('index')) 

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "Error checking user credentials."

        return "Invalid Credentials. <a href='/login'>Try Again</a>"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = 'Admin' if email == 'admin@gmail.com' else 'User'
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    return "User already exists. <a href='/register'>Try Again</a>"
                cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                               (username, email, password, role))
                conn.commit()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "Error registering user in the database."

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None) 
    session.pop('role', None) 
    return redirect(url_for('login'))  

if __name__ == '__main__':
    app.run(debug=True)
