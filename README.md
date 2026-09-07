# Asia Central News Scanner

Daily automated news digest from top 5 Asian Central news websites, delivered via ProtonMail every morning at 8:00 AM Paris time.

## Features

✨ **Automated Daily Scanning** - Runs every day at 8:00 AM Paris time (configurable)
📰 **Multiple News Sources** - Monitors 5 top Asian Central news websites:
  - Eurasianet
  - Cabar.asia
  - Stanradar
  - Azernews
  - The Diplomat (Asia section)

📧 **Email Summary** - Beautiful HTML-formatted email with news highlights
🔄 **Robust Error Handling** - Continues operating even if one source fails
📝 **Comprehensive Logging** - Tracks all activities in `news_scanner.log`
🔐 **ProtonMail Support** - Send securely via ProtonMail

## Quick Start

⚡ **Get running in 5 minutes!** See [QUICKSTART.md](QUICKSTART.md) for step-by-step instructions.

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- ProtonMail account

### Step 1: Clone the Repository
```bash
git clone https://github.com/RegardsSteppe/asia-central-news-scanner.git
cd asia-central-news-scanner
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure ProtonMail

#### Option A: Using ProtonMail Bridge (Recommended)

ProtonMail Bridge allows SMTP access to your ProtonMail account with encryption.

1. **Download ProtonMail Bridge** from https://proton.me/download/bridge
2. **Install and launch** ProtonMail Bridge
3. **Sign in** with your ProtonMail credentials
4. **Note the SMTP credentials** (usually localhost:1025)

Then create `.env` file:
```
SENDER_EMAIL=your_email@proton.me
SENDER_PASSWORD=your_bridge_password
RECIPIENT_EMAIL=recipient@proton.me
SMTP_SERVER=127.0.0.1
SMTP_PORT=1025
```

#### Option B: Direct SMTP (Without Bridge)

1. Create a copy of `.env.example`:
```bash
cp .env.example .env
```

2. Edit `.env` with your ProtonMail credentials:
```
SENDER_EMAIL=your_email@proton.me
SENDER_PASSWORD=your_protonmail_password
RECIPIENT_EMAIL=recipient@proton.me
SMTP_SERVER=smtp.protonmailrmez7hm6.onion
SMTP_PORT=1025
```

3. Enable IMAP/SMTP in ProtonMail:
   - Go to https://mail.proton.me/u/0/settings/labels
   - Scroll to **IMAP/SMTP** section
   - Follow the instructions to enable SMTP access
   - Generate an app-specific password if required

**Note:** ProtonMail's SMTP server requires Tor support or ProtonMail Bridge for best compatibility.

### Step 4: Test Your Configuration
```bash
python test_email.py
```

This will send a test email to verify your ProtonMail setup is working correctly.

## Usage

### Run the Scanner
```bash
python news_scanner.py
```

The script will:
1. Start the scheduler
2. Display "News scanner scheduled to run daily at 08:00 AM (Paris Time)"
3. Wait for the scheduled time to run
4. Fetch news and send email via ProtonMail automatically

### Manual Test
To test the script immediately without waiting until 8 AM, you can modify the script temporarily or create a test script. Check the logs to verify everything works.

## Running as a Background Service

### Linux/macOS - Using `nohup`
```bash
nohup python news_scanner.py > news_scanner.log 2>&1 &
```

### Linux - Using Systemd Service
Create `/etc/systemd/system/news-scanner.service`:
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
Environment="PATH=/usr/bin:/usr/local/bin"

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable news-scanner
sudo systemctl start news-scanner
```

Check status:
```bash
sudo systemctl status news-scanner
```

View logs:
```bash
journalctl -u news-scanner -f
```

### macOS - Using LaunchAgent
Create `~/Library/LaunchAgents/com.newscanner.asia.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.newscanner.asia</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/asia-central-news-scanner/news_scanner.py</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>StandardOutPath</key>
    <string>/path/to/asia-central-news-scanner/news_scanner.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/asia-central-news-scanner/news_scanner.log</string>
</dict>
</plist>
```

Then load:
```bash
launchctl load ~/Library/LaunchAgents/com.newscanner.asia.plist
```

### Windows - Using Task Scheduler
1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Set trigger to **Daily** at **8:00 AM**
4. Set action to run: `python C:\path\to\news_scanner.py`
5. Enable **Run with highest privileges** if needed
6. Ensure ProtonMail Bridge is running (if using Bridge)

## Customization

### Add More News Sources
Edit the `TOP_NEWS_SOURCES` list in `news_scanner.py`:

```python
TOP_NEWS_SOURCES = [
    {
        'name': 'Your News Site',
        'url': 'https://example.com/',
        'description': 'Description of the news source'
    },
    # ... more sources
]
```

### Change Schedule Time
Edit the `schedule_daily_job()` function in `news_scanner.py`:

```python
schedule.every().day.at("15:30").do(job)  # 3:30 PM instead of 8:00 AM
```

### Change Number of Articles
In `fetch_news_from_source()`, modify:
```python
articles: articles[:5],  # Change 5 to desired number
```

## Troubleshooting

### Email not sending via ProtonMail
1. **Using Bridge**: 
   - Ensure ProtonMail Bridge is running and logged in
   - Check if port 1025 is accessible: `telnet 127.0.0.1 1025`
   - Verify bridge password in `.env`

2. **Direct SMTP**:
   - Check if you enabled IMAP/SMTP in ProtonMail settings
   - Verify email and password are correct
   - Some firewalls block Tor - use ProtonMail Bridge instead

3. General:
   - Check `.env` file is in the same directory as `news_scanner.py`
   - Review `news_scanner.log` for error messages
   - Run `python test_email.py` to diagnose

### No news fetched from a source
- The website structure may have changed
- Website may require authentication
- Check internet connection
- Review `news_scanner.log` for specific errors

### Script not running at scheduled time
- Ensure the terminal/service is still running
- ProtonMail Bridge must be running if using Bridge method
- Check if system timezone is set correctly
- On Linux, verify: `timedatectl` or `date`
- Review `news_scanner.log` for any errors

### Check Logs
```bash
# For nohup/direct run
tail -f news_scanner.log

# For systemd service
journalctl -u news-scanner -f

# For last 50 lines
tail -50 news_scanner.log
```

## Project Structure

```
asia-central-news-scanner/
├── news_scanner.py          # Main scheduler script
├── test_email.py            # Test ProtonMail configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment configuration
├── .gitignore              # Git ignore patterns
├── README.md               # Full documentation (this file)
└── QUICKSTART.md           # Quick start guide
```

## Email Output Sample

Each morning you'll receive an HTML email containing:
- 📅 Date and time (Paris timezone)
- 🔗 Up to 5 news sources with current headlines
- 📰 Top 3 articles per source with direct links
- ✅ Status for each source

## Security Notes

🔐 **ProtonMail + Security Best Practices:**
- ProtonMail Bridge encrypts your password locally
- Direct SMTP uses Tor for privacy
- **Never commit `.env` file** to version control (included in `.gitignore`)
- Keep `news_scanner.log` private (contains email addresses)
- Rotate email credentials periodically
- If using Bridge, run it on a secure connection
- Use strong, unique passwords for ProtonMail

## Environment Variables

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `SENDER_EMAIL` | Yes | `user@proton.me` | Your ProtonMail address |
| `SENDER_PASSWORD` | Yes | `password` | ProtonMail or Bridge password |
| `RECIPIENT_EMAIL` | Yes | `recipient@proton.me` | Email to receive digest |
| `SMTP_SERVER` | Yes | `127.0.0.1` | SMTP server address |
| `SMTP_PORT` | Yes | `1025` | SMTP server port |

## License

MIT License - Feel free to modify and distribute

## Contributing

Feel free to submit issues and enhancement requests!

## Support

For issues or questions:
1. Check [QUICKSTART.md](QUICKSTART.md) for common setup issues
2. Review the **Troubleshooting** section above
3. Check `news_scanner.log` for error details
4. Open an issue on GitHub

---

**Last Updated**: 2026-09-07  
**Timezone**: Europe/Paris (UTC+2 in summer, UTC+1 in winter)  
**Email Provider**: ProtonMail (Privacy-focused)  
**Python Version**: 3.8+
