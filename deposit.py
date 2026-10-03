from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS so Acode frontend can talk to Termux
app.secret_key = 'danish_super_secret_key_777'

deposits = []
user_wallets = {}
ADMIN_PASSWORD = "danish_777"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>777WIN - Deposit Funds</title>
    <style>
        body { background: #0b0f19; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: #121826; padding: 25px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.7); width: 100%; max-width: 400px; border: 1px solid #1e293b; box-sizing: border-box; margin: 20px 0; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        h2 { color: #ffffff; font-size: 20px; margin: 0; }
        .close-btn { color: #94a3b8; font-size: 20px; text-decoration: none; font-weight: bold; }
        .subtitle { text-align: center; font-size: 12px; color: #94a3b8; margin-bottom: 15px; }
        .qr-box { background: #ffffff; padding: 10px; border-radius: 12px; text-align: center; margin-bottom: 15px; }
        .qr-box img { width: 160px; height: 160px; display: block; margin: 0 auto; }
        .upi-box { text-align: center; color: #fbbf24; font-weight: bold; font-size: 15px; margin-bottom: 20px; background: #1e293b; padding: 8px; border-radius: 8px; border: 1px dashed #fbbf24; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 6px; font-size: 13px; color: #94a3b8; }
        input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #0b0f19; color: #fff; font-size: 14px; box-sizing: border-box; }
        input:focus { outline: none; border-color: #fbbf24; }
        button { width: 100%; padding: 14px; background: linear-gradient(135deg, #fbbf24, #d97706); border: none; border-radius: 8px; color: #000; font-size: 15px; font-weight: bold; cursor: pointer; margin-top: 10px; transition: 0.3s; }
        button:hover { opacity: 0.9; }
        .msg-box { background: #065f46; color: #6ee7b7; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 15px; font-size: 13px; }
        .error-box { background: #7f1d1d; color: #fca5a5; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 15px; font-size: 13px; }
        .status-section { margin-top: 25px; border-top: 1px solid #1e293b; padding-top: 15px; }
        .status-card { background: #1e293b; padding: 10px; border-radius: 8px; margin-top: 10px; font-size: 13px; }
        .approved { color: #34d399; font-weight: bold; }
        .rejected { color: #f87171; font-weight: bold; }
        .pending { color: #fbbf24; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h2>Deposit Funds</h2>
            <a href="#" class="close-btn">&times;</a>
        </div>
        <div class="subtitle">Scan QR & Pay via GPay / PhonePe / Paytm</div>
        
        <div class="qr-box">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi://pay?pa=8437871238@fam" alt="UPI QR Code">
        </div>
        
        <div class="upi-box">UPI ID: 8437871238@fam</div>

        {% if msg %}
            <div class="msg-box">{{ msg }}</div>
        {% endif %}
        {% if error_msg %}
            <div class="error-box">{{ error_msg }}</div>
        {% endif %}

        <form method="POST" action="/submit">
            <div class="form-group">
                <label>Username / Player ID</label>
                <input type="text" name="username" required placeholder="Enter username">
            </div>
            <div class="form-group">
                <label>Amount (₹)</label>
                <input type="number" name="amount" required placeholder="Enter Amount (e.g. 500)">
            </div>
            <div class="form-group">
                <label>12-Digit UTR / Transaction ID</label>
                <input type="text" name="utr" required placeholder="Enter 12-digit UTR Number">
            </div>
            <button type="submit">SUBMIT REQUEST</button>
        </form>

        <div class="status-section">
            <h3 style="font-size: 15px; color: #fbbf24; margin-bottom: 10px;">Check Deposit Status</h3>
            <form method="POST" action="/check_status">
                <div class="form-group">
                    <input type="text" name="search_query" required placeholder="Enter Username or UTR">
                </div>
                <button type="submit" style="background: #334155; color: #fff;">CHECK STATUS</button>
            </form>

            {% if searched %}
                <div style="margin-top: 15px;">
                    {% if user_deposits %}
                        {% for d in user_deposits %}
                            <div class="status-card">
                                <div><b>User:</b> {{ d.username }}</div>
                                <div><b>Amount:</b> ₹{{ d.amount }}</div>
                                <div><b>UTR:</b> {{ d.utr }}</div>
                                <div><b>Status:</b> 
                                    {% if d.status == 'Approved' %}
                                        <span class="approved">Payment Successful (Approved)</span>
                                    {% elif 'Rejected' in d.status %}
                                        <span class="rejected">{{ d.status }}</span>
                                    {% else %}
                                        <span class="pending">Pending Admin Approval</span>
                                    {% endif %}
                                </div>
                            </div>
                        {% endfor %}
                    {% else %}
                        <div style="font-size: 13px; color: #94a3b8; text-align: center; margin-top: 10px;">No deposit found with this Username/UTR.</div>
                    {% endif %}
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Login - 777WIN</title>
    <style>
        body { background: #0b0f19; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #121826; padding: 30px; border-radius: 12px; width: 100%; max-width: 350px; border: 1px solid #1e293b; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h2 { color: #fbbf24; text-align: center; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin-bottom: 15px; background: #0b0f19; border: 1px solid #334155; color: #fff; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #fbbf24; color: #000; border: none; font-weight: bold; border-radius: 6px; cursor: pointer; }
        .error { color: #f87171; font-size: 12px; text-align: center; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>Admin Login</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="password" name="password" required placeholder="Enter Admin Password">
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard - 777WIN</title>
    <style>
        body { background: #0b0f19; color: #f8fafc; font-family: sans-serif; padding: 20px; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h2 { color: #fbbf24; margin: 0; }
        .logout { background: #ef4444; color: white; padding: 8px 14px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; background: #121826; border-radius: 8px; overflow: hidden; border: 1px solid #1e293b; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #1e293b; font-size: 14px; }
        th { background: #1e293b; color: #fbbf24; }
        .btn-accept { padding: 6px 12px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; text-decoration: none; display: inline-block; }
        .btn-reject { padding: 6px 12px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; text-decoration: none; display: inline-block; margin-left: 5px; }
        .approved { color: #34d399; font-weight: bold; }
        .rejected { color: #f87171; font-weight: bold; }
        .pending { color: #fbbf24; font-weight: bold; }
    </style>
</head>
<body>
    <div class="top-bar">
        <h2>Admin Dashboard - Pending Deposits</h2>
        <a href="/logout" class="logout">Logout</a>
    </div>
    <table>
        <tr>
            <th>User</th>
            <th>Amount</th>
            <th>UTR</th>
            <th>Status</th>
            <th>Action</th>
        </tr>
        {% for d in deposits %}
        <tr>
            <td>{{ d.username }}</td>
            <td>₹{{ d.amount }}</td>
            <td>{{ d.utr }}</td>
            <td>
                {% if d.status == 'Approved' %}
                    <span class="approved">Approved</span>
                {% elif 'Rejected' in d.status %}
                    <span class="rejected">{{ d.status }}</span>
                {% else %}
                    <span class="pending">Pending</span>
                {% endif %}
            </td>
            <td>
                {% if d.status == 'Pending' %}
                    <a href="/action/approve/{{ loop.index0 }}" class="btn-accept">Accept</a>
                    <a href="/action/reject/{{ loop.index0 }}" class="btn-reject">Reject</a>
                {% else %}
                    -
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/submit', methods=['POST'])
def submit():
    # Check if request is coming as JSON from fetch or standard Form
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        amount_str = data.get('amount')
        utr = data.get('utr', '').strip()
    else:
        username = request.form.get('username')
        amount_str = request.form.get('amount')
        utr = request.form.get('utr', '').strip()
    
    if not username or not amount_str or not utr:
        return jsonify({"status": "error", "message": "All fields are required!"})
        
    try:
        amount = float(amount_str)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid amount format!"})

    # Duplicate UTR Check
    existing_utr = any(d['utr'] == utr for d in deposits)
    
    if existing_q := existing_utr:
        deposits.append({
            "username": username,
            "amount": amount,
            "utr": utr,
            "status": "Rejected (Duplicate UTR)"
        })
        return jsonify({"status": "error", "message": "Error: This UTR has already been used!"})
    
    deposits.append({
        "username": username,
        "amount": amount,
        "utr": utr,
        "status": "Pending"
    })
    return jsonify({"status": "success", "message": "Deposit request submitted successfully!"})

@app.route('/action/<string:action_type>/<int:index>')
def action(action_type, index):
    if not session.get('admin_logged'):
        return redirect(url_for('admin'))
        
    if index < len(deposits):
        dep = deposits[index]
        if dep['status'] == 'Pending':
            if action_type == 'approve':
                dep['status'] = 'Approved'
                user = dep['username']
                user_wallets[user] = user_wallets.get(user, 0.0) + dep['amount']
            elif action_type == 'reject':
                dep['status'] = 'Rejected'
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('admin_logged', None)
    return redirect(url_for('admin'))
@app.route('/admin')
def admin():
    return render_string(ADMIN_TEMPLATE, deposits=deposits)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

