const express = require('express');
const path = require('path');
const mongoose = require('mongoose');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname)));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'Index.html'));
});

// Telegram Configuration
const TELEGRAM_BOT_TOKEN = '8744660851:AAE...';
const ADMIN_CHAT_ID = '8566606809';

// 1. MongoDB Connection
// 1. MongoDB Connection (Direct URL)
mongoose.connect('mongodb://dd4327982_db_user:<yM9uNNz07MvnXPmY>@ac-woefusx-shard-00-00.heppxyt.mongodb.net:27017,ac-woefusx-shard-00-01.heppxyt.mongodb.net:27017,ac-woefusx-shard-00-02.heppxyt.mongodb.net:27017/?ssl=true&replicaSet=atlas-o34p2y-shard-0&authSource=admin&appName=Cluster0&compressors=zlib')
    .then(() => console.log('✅ MongoDB Connected Successfully'))
    .catch(err => console.error('❌ MongoDB Connection Error:', err));

// User Schema
const userSchema = new mongoose.Schema({
    username: { type: String, required: true, unique: true },
    wallet_balance: { type: Number, default: 0 }
});
const User = mongoose.model('User', userSchema);

// Deposit Schema
const depositSchema = new mongoose.Schema({
  id: { type: Number, required: true, unique: true },
  username: { type: String, required: true },
  amount: { type: Number, required: true },
  utr: { type: String, required: true, unique: true },
  status: { type: String, default: 'Pending' },
  time: { type: String, required: true }
});
const Deposit = mongoose.model('Deposit', depositSchema);

// 🆕 FIXED: Withdrawal Schema Added for MongoDB Tracking
const withdrawalSchema = new mongoose.Schema({
  id: { type: Number, required: true, unique: true },
  username: { type: String, required: true },
  amount: { type: Number, required: true },
  status: { type: String, default: 'Pending' },
  time: { type: String, required: true }
});
const Withdrawal = mongoose.model('Withdrawal', withdrawalSchema);

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Static File Serving Path Fix
app.use(express.static(path.join(__dirname, 'public')));

// Fetch node-fetch wrapper for API requests to Telegram
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

// ==========================================
// 💸 1. DEPOSIT REQUEST API (AUTOMATED INTERACTION)
// ==========================================
app.post('/api/deposit', async (req, res) => {
  const { username, amount, utr } = req.body;
  const depositAmount = parseFloat(amount);

  if (!depositAmount || !utr) {
    return res.status(400).json({ success: false, message: 'Amount and UTR required.' });
}


  if (depositAmount < 100) {
    return res.status(400).json({ success: false, message: 'Minimum deposit amount is ₹100.' });
  }

  try {
    const existingUtr = await Deposit.findOne({ utr: utr });
    if (existingUtr) {
      return res.status(400).json({ success: false, message: 'This UTR has already been used.' });
    }

    const reqId = Date.now();

    const newRequest = new Deposit({
      id: reqId,
      username: username,
      amount: depositAmount,
      utr: utr,
      status: 'Pending',
      time: new Date().toLocaleTimeString()
    });
    await newRequest.save();

    const messageText = `⚠️ *New Deposit Request* ⚠️\n\n👤 *User:* ${username}\n💰 *Amount:* ₹${depositAmount}\n🆔 *UTR:* \`${utr}\`\n⏳ *Status:* PENDING`;
    
    const keyboard = {
      inline_keyboard: [[
        { text: '✅ Accept', callback_data: `depaccept_${reqId}` },
        { text: '❌ Reject', callback_data: `depreject_${reqId}` }
      ]]
    };

    await fetch(`https://api.telegram.org/bot${'8744660851:AAEOG8ZUAroYJ5X1M1IG6qs_KewsniifRmQ'}/sendMessage`, {

      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: ADMIN_CHAT_ID,
        text: messageText,
        parse_mode: 'Markdown',
        reply_markup: keyboard
      })
    });

    res.json({ success: true, message: 'Deposit request submitted successfully! Awaiting approval.' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
});

// ==========================================
// 🏧 2. NEW: WITHDRAWAL REQUEST API
// ==========================================
app.post('/api/withdraw', async (req, res) => {
  const { username, amount } = req.body;
  const withdrawAmount = parseFloat(amount);

  if (!username || !withdrawAmount) {
    return res.status(400).json({ success: false, message: 'Username and Amount required.' });
  }

  if (withdrawAmount < 100) {
    return res.status(400).json({ success: false, message: 'Minimum withdrawal amount is ₹100.' });
  }

  try {
    // Check if user exists and has enough balance
    const user = await User.findOne({ username: username });
    if (!user || user.wallet_balance < withdrawAmount) {
      return res.status(400).json({ success: false, message: 'Insufficient wallet balance!' });
    }

    // 🔒 Lock the amount immediately from user's account
    user.wallet_balance -= withdrawAmount;
    await user.save();

    const reqId = Date.now();

    // Create a database entry for withdrawal
    const newWithdrawRequest = new Withdrawal({
      id: reqId,
      username: username,
      amount: withdrawAmount,
      status: 'Pending',
      time: new Date().toLocaleTimeString()
    });
    await newWithdrawRequest.save();

    // 🔔 Send alert to admin via Telegram
    const messageText = `🏧 *New Withdrawal Request* 🏧\n\n👤 *User:* ${username}\n💵 *Amount:* ₹${withdrawAmount}\n⏳ *Status:* PENDING`;
    
    const keyboard = {
      inline_keyboard: [[
        { text: '✅ Approve', callback_data: `witaccept_${reqId}` },
        { text: '❌ Reject & Refund', callback_data: `witreject_${reqId}` }
      ]]
    };

    await fetch(`https://api.telegram.org/bot${'8744660851:AAEOG8ZUAroYJ5X1M1IG6qs_KewsniifRmQ'}/sendMessage`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: ADMIN_CHAT_ID,
        text: messageText,
        parse_mode: 'Markdown',
        reply_markup: keyboard
      })
    });

    res.json({ success: true, message: 'Withdrawal request sent to admin. Balance deducted.' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
});

// ==========================================
// 🤖 3. UPDATED: TELEGRAM WEBHOOK CONTROLLER
// ==========================================
app.post('/api/telegram-webhook', async (req, res) => {
  const update = req.body;

  if (update.callback_query) {
    const callbackQuery = update.callback_query;
    const data = callbackQuery.data;
    const chatId = callbackQuery.message.chat.id;
    const messageId = callbackQuery.message.message_id;

    // Pattern parsing (e.g., depaccept_171123, witreject_171123)
    const [typeWithAction, reqIdStr] = data.split('_');
    const reqId = parseInt(reqIdStr);
    let updatedText = '';

    try {
      // 🟩 DEPOSIT LOGIC ACTION
      if (typeWithAction.startsWith('dep')) {
        const reqItem = await Deposit.findOne({ id: reqId });
        if (reqItem && reqItem.status === 'Pending') {
          if (typeWithAction === 'depaccept') {
            reqItem.status = 'Approved';
            await reqItem.save();

            let user = await User.findOne({ username: reqItem.username });
            if (!user) user = new User({ username: reqItem.username, wallet_balance: 0 });
            user.wallet_balance += reqItem.amount;
            await user.save();

            updatedText = `✅ *Deposit Request Approved* ✅\n\n👤 *User:* ${reqItem.username}\n💰 *Amount:* ₹${reqItem.amount}\n🆔 *UTR:* \`${reqItem.utr}\`\n🟢 *Status:* SUCCESS`;
          } else {
            reqItem.status = 'Rejected';
            await reqItem.save();
            updatedText = `❌ *Deposit Request Rejected* ❌\n\n👤 *User:* ${reqItem.username}\n💰 *Amount:* ₹${reqItem.amount}\n🆔 *UTR:* \`${reqItem.utr}\`\n🔴 *Status:* REJECTED`;
          }
        }
      }

      // 🟦 WITHDRAWAL LOGIC ACTION
      if (typeWithAction.startsWith('wit')) {
        const reqItem = await Withdrawal.findOne({ id: reqId });
        if (reqItem && reqItem.status === 'Pending') {
          if (typeWithAction === 'witaccept') {
            reqItem.status = 'Approved';
            await reqItem.save();
            updatedText = `✅ *Withdrawal Request Approved* ✅\n\n👤 *User:* ${reqItem.username}\n💵 *Amount:* ₹${reqItem.amount}\n🟢 *Status:* COMPLETED (Sent to User)`;
          } else {
            reqItem.status = 'Rejected';
            await reqItem.save();

            // 🔄 REFUND: Return money back to user account since admin rejected
            const user = await User.findOne({ username: reqItem.username });
            if (user) {
              user.wallet_balance += reqItem.amount;
              await user.save();
            }
            updatedText = `❌ *Withdrawal Request Rejected* ❌\n\n👤 *User:* ${reqItem.username}\n💵 *Amount:* ₹${reqItem.amount}\n🔴 *Status:* REJECTED (Amount Refunded)`;
          }
        }
      }

      // Edit message in Telegram with updated text
      if (updatedText !== '') {
        await fetch(`https://api.telegram.org/bot${'8744660851:AAEOG8ZUAroYJ5X1M1IG6qs_KewsniifRmQ'}/editMessageText`, { 

          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: chatId,
            message_id: messageId,
            text: updatedText,
            parse_mode: 'Markdown'
          })
        });
      }
    } catch (error) {
      console.error('Webhook processing failure:', error);
    }
  }
  res.json({ success: true });
});

// User Balance Check Route
app.get('/api/user/balance/:username', async (req, res) => {
  try {
    const user = await User.findOne({ username: req.params.username });
    res.json({ success: true, balance: user ? user.wallet_balance : 0.00 });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Server Error' });
  }
});

// Fallback Server Route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'dashboard.html'));
});

app.listen(PORT, () => {
  console.log(`🚀 Server fully operational at http://localhost:${PORT}`);
});
