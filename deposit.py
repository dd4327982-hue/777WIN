
import os
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'danish_super_secure_random_key_777999'

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "secretpassword777"

# In-memory storage for deposits and wallet balances
deposits = []
user_wallets = {}  # { username: balance_amount }
user_history = {}  # { username: [deposit_records] }

@app.route('/')
def home():
    for name in ['Index.html', 'index.html', 'INDEX.HTML']:
        if os.path.exists(name):
            with open(name, 'r', encoding='utf-8') as f:
                return render_template_string(f.read())
    return "<h3>Index.html not found!</h3>"

@app.route('/dashboard')
def dashboard():
    for name in ['dashboard.html', 'Dashboard.html', 'DASHBOARD.HTML']:
        if os.path.exists(name):
            with open(name, 'r', encoding='utf-8') as f:
                return render_template_string(f.read())
    return "<h3>Dashboard.html not found!</h3>"

# --- DEPOSIT SUBMIT ROUTE ---
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

    # Track user history
    if username.strip() not in user_history:
        user_history[username.strip()] = []
    user_history[username.strip()].append(deposit_record)

    return jsonify({"status": "success", "message": "Deposit request submitted successfully! Waiting for approval."})

# --- CHECK STATUS API FOR USER ---
@app.route('/check-status/<username>', methods=['GET'])
def check_status(username):
    history = user_history.get(username, [])
    balance = user_wallets.get(username, 0.0)
    return jsonify({"username": username, "balance": balance, "history": history})


# --- ADMIN PANEL ROUTE (`/admin`) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template_string('<h3>Wrong Password! <a href="/admin">Try Again</a></h3>')

    if not session.get('admin_logged_in'):
        return render_template_string('''
            <h2>Admin Dashboard Login</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required><br><br>
                <input type="password" name="password" placeholder="Password" required><br><br>
                <button type="submit">Login</button>
            </form>
        ''')

    # Try loading Admin.html if it exists, otherwise fallback to built-in clean table view
    try:
        with open('Admin.html', 'r', encoding='utf-8') as f:
            admin_html = f.read()
            return render_template_string(admin_html, deposits=deposits)
    except FileNotFoundError:
        html = '''
        <html>
        <head><title>Admin Dashboard - Pending Deposits</title>
        <style>
            body { background: #0f172a; color: #fff; font-family: Arial; padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; border-bottom: 1px solid #334155; text-align: left; }
            th { background: #1e293b; }
            .btn-approve { background: #22c55e; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; }
            .btn-reject { background: #ef4444; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; }
            .logout { float: right; background: #dc2626; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; }
        </style>
        </head>
        <body>
            <h2>Admin Dashboard - Deposits <a href="/admin/logout" class="logout">Logout</a></h2>
            <table>
                <tr><th>User</th><th>Amount</th><th>UTR</th><th>Status</th><th>Action</th></tr>
        '''
        for i, d in enumerate(deposits):
            html += f"<tr><td>{d['username']}</td><td>₹{d['amount']}</td><td>{d['utr']}</td><td><b>{d['status']}</b></td>"
            if d['status'] == 'Pending':
                html += f"<td><a href='/admin/action/{i}/approve' class='btn-approve'>Approve</a> &nbsp; <a href='/admin/action/{i}/reject' class='btn-reject'>Reject</a></td>"
            else:
                html += "<td>-</td>"
            html += "</tr>"
        html += "</table></body></html>"
        return render_template_string(html)

@app.route('/admin/action/<int:index>/<string:action_type>')
def admin_action(index, action_type):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))

    if index < len(deposits):
        dep = deposits[index]
        if dep['status'] == 'Pending':
            uname = dep['username']
            if action_type == 'approve':
                dep['status'] = 'Approved'
                # Wallet Balance Update
                user_wallets[uname] = user_wallets.get(uname, 0.0) + dep['amount']
            elif action_type == 'reject':
                dep['status'] = 'Rejected'
                
    return redirect(url_for('admin_panel'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

# --- DYNAMIC GAME / PAGE ROUTE ---
@app.route('/<path:filename>')
def serve_dynamic_file(filename):
    possible_names = [filename, filename + '.html', filename.capitalize() + '.html', filename.lower() + '.html']
    for name in possible_names:
        if os.path.exists(name):
            with open(name, 'r', encoding='utf-8') as f:
                return render_template_string(f.read())
    return f"<h3>Page or Game '{filename}' not found!</h3>", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
