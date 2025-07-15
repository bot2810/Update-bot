from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ডাটাবেস ইনিশিয়ালাইজেশন
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # ইউজার টেবিল
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 email TEXT UNIQUE,
                 phone TEXT UNIQUE,
                 password TEXT,
                 name TEXT,
                 balance REAL DEFAULT 0,
                 spins_today INTEGER DEFAULT 0,
                 last_spin_date TEXT,
                 profile_pic TEXT,
                 status TEXT DEFAULT 'active')''')
    
    # স্পিন হিস্ট্রি টেবিল
    c.execute('''CREATE TABLE IF NOT EXISTS spin_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 reward REAL,
                 spin_date TEXT,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # উইথড্রয়াল রিকোয়েস্ট টেবিল
    c.execute('''CREATE TABLE IF NOT EXISTS withdrawals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 amount REAL,
                 upi_id TEXT,
                 status TEXT DEFAULT 'pending',
                 request_date TEXT,
                 processed_date TEXT,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

init_db()

# হোম পেজ
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# লগিন পেজ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_phone = request.form['email_phone']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        c.execute("SELECT * FROM users WHERE (email=? OR phone=?) AND password=?", 
                 (email_phone, email_phone, password))
        user = c.fetchone()
        
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            return "Invalid credentials", 401
    
    return render_template('login.html')

# স্পিন API
@app.route('/spin', methods=['POST'])
def spin():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # চেক করুন ইউজারের আজকের স্পিন কতটা হয়েছে
    c.execute("SELECT spins_today, last_spin_date FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    
    if user[1] != today:
        # নতুন দিন, স্পিন কাউন্ট রিসেট করুন
        c.execute("UPDATE users SET spins_today=0, last_spin_date=? WHERE id=?", (today, user_id))
        spins_today = 0
    else:
        spins_today = user[0]
    
    if spins_today >= 20:
        return jsonify({'error': 'Daily spin limit reached'}), 400
    
    # রিওয়ার্ড জেনারেট করুন
    rewards = [0.10, 0.20, 0.50, 1.00, 2.00, 5.00, 10.00]
    reward = random.choice(rewards)
    
    # 5ম এবং 10ম স্পিনে বোনাস
    if spins_today + 1 in [5, 10]:
        reward *= 2  # ডাবল রিওয়ার্ড
    
    # ডাটাবেস আপডেট করুন
    c.execute("UPDATE users SET balance=balance+?, spins_today=spins_today+1 WHERE id=?", 
              (reward, user_id))
    c.execute("INSERT INTO spin_history (user_id, reward, spin_date) VALUES (?, ?, ?)",
              (user_id, reward, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'reward': reward,
        'spins_today': spins_today + 1,
        'is_special': spins_today + 1 in [5, 10]
    })

# উইথড্রয়াল রিকোয়েস্ট
@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    amount = float(request.form['amount'])
    upi_id = request.form['upi_id']
    user_id = session['user_id']
    
    if amount < 5:
        return jsonify({'error': 'Minimum withdrawal is ₹5'}), 400
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # চেক করুন ব্যালেন্স
    c.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < amount:
        return jsonify({'error': 'Insufficient balance'}), 400
    
    # ব্যালেন্স কমানো হবে যখন অ্যাডমিন অ্যাপ্রুভ করবে
    c.execute("INSERT INTO withdrawals (user_id, amount, upi_id, status, request_date) VALUES (?, ?, ?, ?, ?)",
              (user_id, amount, upi_id, 'pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Withdrawal request submitted'})

# অ্যাডমিন ড্যাশবোর্ড
@app.route('/admin')
def admin_dashboard():
    # এখানে অথেন্টিকেশন যোগ করতে হবে
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT SUM(balance) FROM users")
    total_balance = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'")
    pending_withdrawals = c.fetchone()[0]
    
    conn.close()
    
    return render_template('admin.html', 
                         total_users=total_users,
                         total_balance=total_balance,
                         pending_withdrawals=pending_withdrawals)

if __name__ == '__main__':
    app.run(debug=True)
