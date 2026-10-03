

import os
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify

app = Flask(__name__)
# Secure secret key for session encryption
app.secret_key = 'danish_super_secure_random_key_777999'

# Admin credentials (tu ise baad me badal bhi sakta hai)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "secretpassword777"

# In-memory storage for deposits and user wallets
deposits = []
user_wallets = {}

@app.route('/')
def home():
    # Saare possible spellings check karega
    possible_names = ['Index.html', 'index.html', 'INDEX.HTML']
    for name in possible_names:
        if os.path.exists(name):
            with open(name, 'r', encoding='utf-8') as f:
                return render_template_string(f.read())
                
    # Agar phir bhi na mile, toh dikhaye ki folder me kya-kya hai (Debugging ke liye)
    files_in_dir = os.listdir('.')
    return f"<h3>Index.html not found! Files available in root directory:</h3> <p>{files_in_dir}</p>"

@app.route('/dashboard')
def dashboard():
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as f:
            return render_template_string(f.read())
    except FileNotFoundError:
        return "<h3>Dashboard.html not found!</h3>"

# --- SECURE ADMIN LOGIN & PANEL ---
@app.route('/secure-admin-panel-777', methods=['GET', 'POST'])
def secure_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('secure_admin'))
        else:
            return render_template_string('''
                <h3>Wrong Password! Access Denied.</h3>
                <a href="/secure-admin-panel-777">Try Again</a>
            ''')

    # Check if admin is logged in
    if not session.get('admin_logged_in'):
        # Return a simple login form for admin
        return render_template_string('''
            <h2>Admin Login</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="Admin Username" required><br><br>
                <input type="password" name="password" placeholder="Password" required><br><br>
                <button type="submit">Login</button>
            </form>
        ''')

    # If logged in, load Admin.html securely
    try:
        with open('Admin.html', 'r', encoding='utf-8') as f:
            admin_html = f.read()
            return render_template_string(admin_html, deposits=deposits)
    except FileNotFoundError:
        return "<h3>Admin.html not found in repository!</h3>"

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form.get('username')
    amount = request.form.get('amount')
    utr = request.form.get('utr')

    if not username or not amount or not utr:
        return jsonify({"status": "error", "message": "All fields are required!"})

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid amount format!"})

    # Duplicate UTR Check
    for d in deposits:
        if d['utr'] == utr:
            return jsonify({"status": "error", "message": "This UTR has already been used!"})

    deposits.append({
        'username': username.strip(),
        'amount': amount,
        'utr': utr.strip(),
        'status': 'Pending'
    })

    return jsonify({"status": "success", "message": "Deposit request submitted successfully!"})

@app.route('/admin/action/<int:index>/<string:action_type>')
def admin_action(index, action_type):
    if not session.get('admin_logged_in'):
        return redirect(url_for('secure_admin'))

    if index < len(deposits):
        dep = deposits[index]
        if dep['status'] == 'Pending':
            if action_type == 'approve':
                dep['status'] = 'Approved'
                user_wallets[dep['username']] = user_wallets.get(dep['username'], 0.0) + dep['amount']
            elif action_type == 'reject':
                dep['status'] = 'Rejected'
    return redirect(url_for('secure_admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
