const express = require('express');
const cors = require('cors');
const app = express();

app.use(express.json());
app.use(cors());

app.get('/', (req, res) => {
    res.send('Node.js Local Server is Running Successfully!');
});

// Mock User Database / State (Aage chal kar isko multi-user bhi bana sakte hain)
let userAccount = {
    username: "Player",
    balance: 0.00,
    history: []
};

let pendingRequests = [];

// 1. Deposit / Withdrawal request receive karne ka API
app.post('/submit-request', (req, res) => {
    const { type, username, amount, utr, upi } = req.body;
    
    const newRequest = {
        id: Date.now(),
        type: type, // 'Deposit' ya 'Withdrawal'
        username: username || userAccount.username,
        amount: parseFloat(amount),
        utr: utr || 'X', 
        upi: upi || 'X', 
        status: 'Pending' 
    };

    pendingRequests.push(newRequest);
    res.json({ status: 'success', message: 'Request submitted successfully! Waiting for approval.' });
});

// 2. Admin panel ke liye requests fetch karne ka API
app.get('/admin/requests', (req, res) => {
    res.json(pendingRequests);
});

// 3. User balance aur history fetch karne ka API (Frontend ke liye)
app.get('/user/data', (req, res) => {
    res.json(userAccount);
});

// 4. Admin Accept/Reject action handle karne ka API (Point 1 & 2 Logic)
app.post('/admin/action', (req, res) => {
    const { requestId, action } = req.body; 
    
    const request = pendingRequests.find(r => r.id === requestId);
    if (!request) {
        return res.status(404).json({ status: 'error', message: 'Request not found' });
    }

    if (request.status !== 'Pending') {
        return res.status(400).json({ status: 'error', message: 'Request already processed' });
    }

    if (action === 'Accept') {
        request.status = 'Completed';

        if (request.type === 'Deposit') {
            // Point 1: Deposit Accept hone par balance badhao
            userAccount.balance += request.amount;
            userAccount.history.unshift({
                type: 'Deposit',
                amount: request.amount,
                status: 'Successful',
                date: new Date().toLocaleString()
            });
        } else if (request.type === 'Withdrawal') {
            // Point 2: Withdrawal Accept hone par balance cut karo
            if (userAccount.balance >= request.amount) {
                userAccount.balance -= request.amount;
                userAccount.history.unshift({
                    type: 'Withdrawal',
                    amount: request.amount,
                    status: 'Successful',
                    date: new Date().toLocaleString()
                });
            } else {
                request.status = 'Rejected (Insufficient Balance)';
                return res.json({ status: 'error', message: 'User has insufficient balance for this withdrawal!' });
            }
        }
    } else {
        request.status = 'Rejected';
        userAccount.history.unshift({
            type: request.type,
            amount: request.amount,
            status: 'Rejected',
            date: new Date().toLocaleString()
        });
    }

    res.json({ status: 'success', message: `Request ${action}ed successfully!` });
});

app.listen(3000, () => {
    console.log('Server is running on http://localhost:3000');
});
