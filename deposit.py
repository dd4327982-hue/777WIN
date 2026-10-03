import os
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'danish_super_secure_random_key_777999'

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "secretpassword777"

# In-memory database for deposits and wallets
deposits = []
user_wallets = {}
user_history = {}

@app.route('/')
def home():
    # Home/Login page ke liye variations check karega
    for name in ['Index.html', 'index.html', 'INDEX.HTML']:
        if os.path.exists(name):
            with open(name, 'r', encoding='utf-8') as f:
                return render_template_string(f.read())
    return "<h3>Index.html not found in repository root directory!</h3>"

@app.route('/dashboard')
def dashboard():
    # Dashboard page ke liye variations check karega
    for name in ['dashboard.html', 'Dashboard.html', 'DASHBOARD.HTML']:
        if os.path.exists(name):
            with open(name, 'r', encoding='utf-8') as f:
                return render_template_string(f.read())
    return "<h3>Dashboard.html not found!</h3>"

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

    # Duplicate UTR check
    for d in deposits:
        if d['utr'] == utr:
            return jsonify({"status": "error", "message": "This UTR has already been used!"})

    deposit_record = {
        'username': username.strip(),
        'amount': amount,
        'utr': utr.strip(),
        'status': 'Pending'
    }
    deposits.append(deposit_record)

    if username not in user_history:
        user_history[username] = []
    user_history[username].append(deposit_record)

    return jsonify({"status": "success", "message": "Deposit request submitted successfully! Status: Pending"})

@app.route('/user/history/<username>')
def get_user_history(username):
    history = user_history.get(username, [])
    balance = user_wallets.get(username, 0.0)
    return jsonify({"username": username, "balance": balance, "history": history})

# --- SECURE ADMIN PANEL ---
@app.route('/secure-admin-panel-777', methods=['GET', 'POST'])
def secure_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('secure_admin'))
        else:
            return render_template_string('<h3>Wrong Password! <a href="/secure-admin-panel-777">Try Again</a></h3>')

    if not session.get('admin_logged_in'):
        return render_template_string('''
            <h2>Admin Secure Login</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required><br><br>
                <input type="password" name="password" placeholder="Password" required><br><br>
                <button type="submit">Login</button>
            </form>
        ''')

    try:
        with open('Admin.html', 'r', encoding='utf-8') as f:
            admin_html = f.read()
            return render_template_string(admin_html, deposits=deposits)
    except FileNotFoundError:
        html = "<h2>Admin Panel - Pending Requests</h2><ul>"
        for i, d in enumerate(deposits):
            html += f"<li>User: {d['username']} | Amount: ₹{d['amount']} | UTR: {d['utr']} | Status: <b>{d['status']}</b> "
            if d['status'] == 'Pending':
                html += f"<a href='/admin/action/{i}/approve'>[Approve]</a> <a href='/admin/action/{i}/reject'>[Reject]</a>"
            html += "</li>"
        html += "</ul><br><a href='/admin/logout'>Logout</a>"
        return render_template_string(html)

@app.route('/admin/action/<int:index>/<string:action_type>')
def admin_action(index, action_type):
    if not session.get('admin_logged_in'):
        return redirect(url_for('secure_admin'))

    if index < len(deposits):
        dep = deposits[index]
        if dep['status'] == 'Pending':
            if action_type == 'approve':
                dep['status'] = 'Approved'
                uname = dep['username']
                user_wallets[uname] = user_wallets.get(uname, 0.0) + dep['amount']
                if uname in user_history:
                    for h in user_history[uname]:
                        if h['utr'] == dep['utr']:
                            h['status'] = 'Approved'
            elif action_type == 'reject':
                dep['status'] = 'Rejected'
                uname = dep['username']
                if uname in user_history:
                    for h in user_history[uname]:
                        if h['utr'] == dep['utr']:
                            h['status'] = 'Rejected'
    return redirect(url_for('secure_admin'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

# --- DYNAMIC GAME / PAGE ROUTE (NO MORE PYTHON EDITING NEEDED) ---
@app.route('/<path:filename>')
def serve_dynamic_file(filename):
    # Yeh route automatically koi bhi game ya file (jaise Aviator.html, etc.) utha lega
    possible_names = [filename, filename + '.html', filename.capitalize() + '.html', filename.lower() + '.html']
    for name in possible_names:
        if os.path.exists(name):
            with open(name, 'r', encoding='utf-8') as f:
                return render_template_string(f.read())
    
    return f"<h3>Page or Game '{filename}' not found!</h3>", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
