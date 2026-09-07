# Asia Central News Scanner - Quick Start Guide

Follow these steps to get your news scanner running in 5 minutes!

## 1️⃣ Installation (2 minutes)

```bash
# Clone the repository
git clone https://github.com/RegardsSteppe/asia-central-news-scanner.git
cd asia-central-news-scanner

# Install dependencies
pip install -r requirements.txt
```

## 2️⃣ ProtonMail Setup (2 minutes)

### Using ProtonMail Bridge (Recommended)

```bash
# Download and install from https://proton.me/download/bridge
# Then launch Bridge and sign in with your ProtonMail credentials

# Create .env file
cp .env.example .env

# Edit .env with Bridge credentials
nano .env
# Add:
# SENDER_EMAIL=your_email@proton.me
# SENDER_PASSWORD=your_bridge_password
# RECIPIENT_EMAIL=recipient@proton.me
# SMTP_SERVER=127.0.0.1
# SMTP_PORT=1025
```

### Without Bridge (Direct SMTP)

```bash
cp .env.example .env
nano .env
# Add your ProtonMail credentials:
# SENDER_EMAIL=your_email@proton.me
# SENDER_PASSWORD=your_protonmail_password
# RECIPIENT_EMAIL=recipient@proton.me
# SMTP_SERVER=smtp.protonmailrmez7hm6.onion
# SMTP_PORT=1025
```

## 3️⃣ Test Configuration (1 minute)

```bash
python test_email.py
```

You should see:
```
🔧 Testing ProtonMail Configuration...
📧 From: your_email@proton.me
📧 To: recipient@proton.me
🖥️  Server: 127.0.0.1:1025

📤 Connecting to SMTP server...
🔐 TLS connection established
🔑 Authenticating...
✅ Authentication successful
📧 Sending test email...
✅ Email sent successfully!

🎉 All tests passed! Your configuration is ready.
```

## 4️⃣ Run the Scanner

### Option A: Development Mode (Terminal)
```bash
python news_scanner.py
```

The script will wait until 8:00 AM Paris time and send the first email automatically.

### Option B: Background Service (Linux)

```bash
# Run in background
nohup python news_scanner.py > news_scanner.log 2>&1 &

# Check logs
tail -f news_scanner.log
```

### Option C: Systemd Service (Linux - Persistent)

```bash
# Create service file
sudo nano /etc/systemd/system/news-scanner.service
```

Paste:
```ini
[Unit]
Description=Asia Central News Scanner
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/asia-central-news-scanner
ExecStart=/usr/bin/python3 /path/to/asia-central-news-scanner/news_scanner.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable news-scanner
sudo systemctl start news-scanner
sudo systemctl status news-scanner
```

## 🎉 Done!

Your news scanner is now set up and will:
- ✅ Run every day at 8:00 AM Paris time
- ✅ Scan 5 top Asian Central news websites
- ✅ Send a beautiful HTML email summary via ProtonMail
- ✅ Handle errors gracefully

## 📋 What You'll Receive

Each morning at 8 AM you'll get an email with:
- Top headlines from 5 news sources
- Direct links to full articles
- Formatted in a clean, readable HTML template

## 🔧 Troubleshooting

**Email not sent?**
1. Check if Bridge is running (if using Bridge)
2. Verify `.env` file is in the correct location
3. Run `python test_email.py` to diagnose
4. Check `news_scanner.log` for errors

**Script not running?**
1. Ensure terminal is still open (for dev mode)
2. For services: `sudo systemctl status news-scanner`
3. Check logs: `tail -f news_scanner.log`

## 📚 Next Steps

- **Customize sources**: Edit `TOP_NEWS_SOURCES` in `news_scanner.py`
- **Change time**: Modify schedule in `schedule_daily_job()`
- **Add more articles**: Update the article limit in `fetch_news_from_source()`

See [README.md](README.md) for full documentation.

---

**Need help?** Open an issue on GitHub or check the full README.
