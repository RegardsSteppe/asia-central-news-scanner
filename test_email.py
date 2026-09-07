#!/usr/bin/env python3
"""
Quick test script to verify ProtonMail configuration
Run this to test if emails can be sent before setting up the scheduler
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

EMAIL_CONFIG = {
    'sender_email': os.getenv('SENDER_EMAIL', 'your_email@proton.me'),
    'sender_password': os.getenv('SENDER_PASSWORD', ''),
    'recipient_email': os.getenv('RECIPIENT_EMAIL', 'recipient@proton.me'),
    'smtp_server': os.getenv('SMTP_SERVER', '127.0.0.1'),
    'smtp_port': int(os.getenv('SMTP_PORT', 1025))
}

def test_email():
    """Test sending an email via ProtonMail"""
    try:
        print("🔧 Testing ProtonMail Configuration...")
        print(f"📧 From: {EMAIL_CONFIG['sender_email']}")
        print(f"📧 To: {EMAIL_CONFIG['recipient_email']}")
        print(f"🖥️  Server: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
        print()
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Test Email - Asia Central News Scanner"
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        
        # Create test email body
        html_body = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #1a5490; color: white; padding: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Test Email Success!</h1>
                    </div>
                    <p>Your ProtonMail SMTP configuration is working correctly.</p>
                    <p>The Asia Central News Scanner is ready to send daily digests.</p>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        print("📤 Connecting to SMTP server...")
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            print("🔐 TLS connection established")
            
            print("🔑 Authenticating...")
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            print("✅ Authentication successful")
            
            print("📧 Sending test email...")
            server.send_message(msg)
            print("✅ Email sent successfully!")
        
        print()
        print("🎉 All tests passed! Your configuration is ready.")
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {str(e)}")
        print("   Check your email and password in .env")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {str(e)}")
        print("   Check your SMTP server and port settings")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if not EMAIL_CONFIG['sender_password']:
        print("❌ Error: SENDER_PASSWORD not set in .env file")
        print("   Please copy .env.example to .env and configure your credentials")
    else:
        test_email()
