"""
Email utilities for sending notifications.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to_emails: List[str],
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP configuration.
    Returns True if successful, False otherwise.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured, skipping email send")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = ', '.join(to_emails)
        
        # Attach text and HTML versions
        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))
        
        # Connect to SMTP server
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_emails, msg.as_string())
        
        logger.info(f"Email sent successfully to {to_emails}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def send_signup_confirmation(user_email: str, first_name: str) -> bool:
    """Send signup confirmation email to user."""
    subject = f"{settings.APP_NAME} - Account Pending Approval"
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a1a; color: #ffffff; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #2d2d2d; border-radius: 10px; padding: 30px;">
            <h1 style="color: #2A9FD6;">OneIT SAN Analytics</h1>
            <h2>Account Registration Received</h2>
            <p>Dear {first_name},</p>
            <p>Thank you for registering for OneIT SAN Analytics Dashboard.</p>
            <p>Your account is currently <strong style="color: #FF8800;">pending approval</strong> by an administrator.</p>
            <p>You will receive another email once your account has been approved and you can log in.</p>
            <hr style="border-color: #444;">
            <p style="color: #888; font-size: 12px;">
                This is an automated message. Please do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email([user_email], subject, body_html)


def send_admin_new_signup_notification(
    admin_emails: List[str],
    user_first_name: str,
    user_last_name: str,
    user_email: str,
    tenant_name: str
) -> bool:
    """Send notification to admins about new user signup."""
    subject = f"{settings.APP_NAME} - New User Registration Requires Approval"
    
    approve_url = f"{settings.FRONTEND_URL}/user-mgmt"
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a1a; color: #ffffff; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #2d2d2d; border-radius: 10px; padding: 30px;">
            <h1 style="color: #2A9FD6;">OneIT SAN Analytics</h1>
            <h2 style="color: #FF8800;">New User Registration</h2>
            <p>A new user has registered and requires approval:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #444; color: #888;">Name:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #444;"><strong>{user_first_name} {user_last_name}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #444; color: #888;">Email:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #444;"><strong>{user_email}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #444; color: #888;">Requested Tenant:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #444;"><strong>{tenant_name}</strong></td>
                </tr>
            </table>
            <p>
                <a href="{approve_url}" style="display: inline-block; background-color: #2A9FD6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                    Review in Dashboard
                </a>
            </p>
            <hr style="border-color: #444; margin-top: 30px;">
            <p style="color: #888; font-size: 12px;">
                This is an automated notification from OneIT SAN Analytics.
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(admin_emails, subject, body_html)


def send_account_approved(user_email: str, first_name: str) -> bool:
    """Send account approval notification to user."""
    subject = f"{settings.APP_NAME} - Account Approved!"
    
    login_url = f"{settings.FRONTEND_URL}/auth"
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a1a; color: #ffffff; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #2d2d2d; border-radius: 10px; padding: 30px;">
            <h1 style="color: #2A9FD6;">OneIT SAN Analytics</h1>
            <h2 style="color: #77B300;">Account Approved!</h2>
            <p>Dear {first_name},</p>
            <p>Great news! Your OneIT SAN Analytics account has been <strong style="color: #77B300;">approved</strong>.</p>
            <p>You can now log in and start using the dashboard.</p>
            <p style="margin: 30px 0;">
                <a href="{login_url}" style="display: inline-block; background-color: #77B300; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                    Log In Now
                </a>
            </p>
            <hr style="border-color: #444;">
            <p style="color: #888; font-size: 12px;">
                If you did not request this account, please contact your administrator.
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email([user_email], subject, body_html)


def send_account_rejected(user_email: str, first_name: str) -> bool:
    """Send account rejection notification to user."""
    subject = f"{settings.APP_NAME} - Account Request Status"
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a1a; color: #ffffff; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #2d2d2d; border-radius: 10px; padding: 30px;">
            <h1 style="color: #2A9FD6;">OneIT SAN Analytics</h1>
            <h2>Account Request Update</h2>
            <p>Dear {first_name},</p>
            <p>We regret to inform you that your account request for OneIT SAN Analytics has not been approved at this time.</p>
            <p>If you believe this is an error or would like more information, please contact your system administrator.</p>
            <hr style="border-color: #444;">
            <p style="color: #888; font-size: 12px;">
                This is an automated message from OneIT SAN Analytics.
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email([user_email], subject, body_html)


def send_alert_notification(
    to_emails: List[str],
    pool_name: str,
    storage_system: str,
    utilization_pct: float,
    level: str,
    days_until_full: int
) -> bool:
    """Send storage alert notification."""
    level_colors = {
        'warning': '#FF8800',
        'critical': '#CC0000',
        'emergency': '#FF0000'
    }
    
    level_color = level_colors.get(level, '#FF8800')
    subject = f"Storage Alert - {level.upper()}: {pool_name} at {utilization_pct:.1f}%"
    
    dashboard_url = f"{settings.FRONTEND_URL}/overview"
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a1a; color: #ffffff; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #2d2d2d; border-radius: 10px; padding: 30px;">
            <h1 style="color: #2A9FD6;">OneIT SAN Analytics</h1>
            <h2 style="color: {level_color};">Storage Capacity Alert</h2>
            <div style="background-color: #1a1a1a; border-left: 4px solid {level_color}; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; font-size: 18px;"><strong>{level.upper()}</strong></p>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #444; color: #888;">Pool:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #444;"><strong>{pool_name}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #444; color: #888;">System:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #444;"><strong>{storage_system}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #444; color: #888;">Utilization:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #444;"><strong style="color: {level_color};">{utilization_pct:.1f}%</strong></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #444; color: #888;">Days Until Full:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #444;"><strong>{days_until_full if days_until_full > 0 else 'IMMEDIATE'}</strong></td>
                </tr>
            </table>
            <p>Please take immediate action to prevent storage issues.</p>
            <p style="margin: 30px 0;">
                <a href="{dashboard_url}" style="display: inline-block; background-color: #2A9FD6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                    View Dashboard
                </a>
            </p>
            <hr style="border-color: #444;">
            <p style="color: #888; font-size: 12px;">
                This alert will repeat daily until acknowledged in the dashboard.
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_emails, subject, body_html)

