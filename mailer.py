"""
Simple SMTP mailer.
Uses Flask-Mail under the hood; configured entirely from .env.dev.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config


def _send(to: str, subject: str, html: str, text: str):
    """Send an email via SMTP. Raises on failure."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = Config.MAIL_FROM
    msg['To'] = to
    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(Config.MAIL_SMTP_HOST, Config.MAIL_SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(Config.MAIL_SMTP_USER, Config.MAIL_SMTP_PASSWORD)
        server.sendmail(Config.MAIL_FROM, to, msg.as_string())


def send_verification_email(to: str, token: str):
    link = f"{Config.FRONTEND_URL}/verify?token={token}"
    subject = "Verify your email address"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;background:#fff;border-radius:12px;">
      <h2 style="color:#111;margin-bottom:8px;">Verify your email</h2>
      <p style="color:#555;font-size:15px;line-height:1.6;margin-bottom:24px;">
        Thanks for signing up. Click the button below to verify your email address.
        This link expires in <strong>24 hours</strong>.
      </p>
      <a href="{link}"
         style="display:inline-block;background:#1a1a1a;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">
        Verify Email
      </a>
      <p style="color:#999;font-size:13px;margin-top:24px;">
        Or copy this link into your browser:<br>
        <span style="color:#555;word-break:break-all;">{link}</span>
      </p>
      <p style="color:#ccc;font-size:12px;margin-top:32px;">
        If you didn't create an account, you can ignore this email.
      </p>
    </div>
    """
    text = f"Verify your email by visiting: {link}\n\nLink expires in 24 hours."
    _send(to, subject, html, text)


def send_resend_verification_email(to: str, token: str):
    """Same as verification but with slightly different subject."""
    send_verification_email(to, token)


def send_otp_email(to: str, code: str):
    """Send a 2FA OTP code to the user."""
    subject = "Your sign-in verification code"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;background:#fff;border-radius:12px;">
      <h2 style="color:#111;margin-bottom:8px;">Verification code</h2>
      <p style="color:#555;font-size:15px;line-height:1.6;margin-bottom:24px;">
        Use the code below to complete your sign-in. It expires in <strong>10 minutes</strong>.
      </p>
      <div style="display:inline-block;background:#f4f4f4;padding:16px 32px;border-radius:10px;font-size:32px;font-weight:700;letter-spacing:8px;color:#111;">
        {code}
      </div>
      <p style="color:#ccc;font-size:12px;margin-top:32px;">
        If you didn't try to sign in, you can ignore this email.
      </p>
    </div>
    """
    text = f"Your sign-in verification code is: {code}\n\nIt expires in 10 minutes."
    _send(to, subject, html, text)
