# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Not Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - All mail sending notifications

# ------------------------------------------------------------------------------------
# Imports:
from flask_mail import Mail, Message
from datetime import datetime
import re
import os

# Local Imports
from app.extensions import db, mail
from app.extensions import socketio

from app.models.user import Customer, Referral
from app.utils.logging import logger
from app.utils.helpers import get_geoip_data
from app.utils.CONSTS import BASE_DIR

# ------------------------------------------------------------------------------------
# Var Decs

logo_path = os.path.join(BASE_DIR, "app", "static", "images", "email-logo.png")


# ------------------------------------------------------------------------------------

#---------------------------EMAIL NOTIFICATIONS-----------------------------------
def is_valid_email_format(email):
    EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    return EMAIL_REGEX.match(email) is not None

def notify_password_change(recipient, customer, client_ip):
    username = customer.username 
    first_name = customer.first_name
    
    # Lookup geo-data using IP
    try:
        geo_data = get_geoip_data(client_ip)
        country = geo_data.get("country", "Unknown")
        city = geo_data.get("city", "Unknown")
        region = geo_data.get("region", "Unknown")
    except Exception as e:
        country, city, region = "Unknown", "Unknown", "Unknown"
        logger.error(f"GeoIP lookup failed for IP {client_ip}: {e}")

    # HTML body for the email
    html_body = f"""
    <html>
        <body>
            <p>Hi {first_name},</p>
            <p>Your password for Synevyr was successfully changed. The password was changed for the account associated with <strong>{username}</strong>.</p>
            <p>If you didn't make this change, please take immediate action:</p>
            <p>Login details:</p>
            <ul>
                <li><strong>Username:</strong> {username}</li>
                <li><strong>IP Address:</strong> {client_ip}</li>
                <li><strong>Location:</strong> {city}, {region}, {country}</li>
                <li><strong>Date/Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            <p>If this was intended, you can ignore this message. Otherwise, please secure your account as soon as possible or reach out to support.</p>
            <ul>
                <li><a href="https://carpathian.ai/forgot_password">Secure my account</a></li>

                <li><a href="mailto:info@carpathian.ai?subject=Account%20Support&body=Username:%20{username}">Contact support</a></li>
            </ul>
            <p>If this was intended, you can ignore this message.</p>
            <br>
            <p>Best regards,<br>Synevyr Support Team</p>
        </body>
    </html>
    """

    # Create the email message
    msg = Message(
        subject="‼️ Carpathian - YOUR PASSWORD WAS CHANGED!",
        recipients=[recipient],  # Recipient email as a list
        html=html_body  # Use the HTML body for rich formatting
    )

    # Send the email
    mail.send(msg)

def notify_user_login(subject, recipient, customer, ip_address):
    """
    Sends a notification email to the user about a new login.

    :param subject: The email subject
    :param recipient: The recipient email address
    :param customer: The customer object with user details
    :param ip_address: The IP address of the login
    """
    username = customer.username
    first_name = customer.first_name

    # Lookup geo-data using IP
    try:
        geo_data = get_geoip_data(ip_address)
        country = geo_data.get("country", "Unknown")
        city = geo_data.get("city", "Unknown")
        region = geo_data.get("region", "Unknown")
    except Exception as e:
        country, city, region = "Unknown", "Unknown", "Unknown"
        logger.error(f"GeoIP lookup failed for IP {ip_address}: {e}")

    # HTML body for the email
    html_body = f"""
<html>
  <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f9f9f9;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: white; padding: 40px 0;">
  <tr>
    <td align="center">
     <img src="cid:logo_image" alt="Synevyr" style="width: 150px; height: auto;" />
    </td>
  </tr>
</table>


    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center" style="padding: 30px 20px;">
          <table width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; padding: 30px;">
            <tr>
              <td>
                <p style="font-size: 18px; margin-bottom: 20px;">Hi {first_name},</p>
                <p style="font-size: 16px; margin-bottom: 20px;">
                  A login to your Synevyr account was detected. Below are the login details:
                </p>

                <ul style="font-size: 16px; padding-left: 20px; margin-bottom: 20px;">
                  <li><strong>Username:</strong> {username}</li>
                  <li><strong>IP Address:</strong> {ip_address}</li>
                  <li><strong>Location:</strong> {city}, {region}, {country}</li>
                  <li><strong>Date/Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>

                <p style="font-size: 16px; margin-bottom: 20px;">
                  If this login was <strong>not</strong> initiated by you, we recommend taking the following steps immediately:
                </p>

                <ul style="font-size: 16px; padding-left: 20px; margin-bottom: 20px;">
                  <li>Go to <strong>synevyr.org</strong> and click the "Forgot Password" link to reset your password.</li>
                  <li>
                    <a href="mailto:info@carpathian.ai?subject=Account%20Support&body=Username:%20{username}"
                       style="color: #1B8FF2; text-decoration: none;">
                      Email Support
                    </a>
                  </li>
                </ul>

                <p style="font-size: 16px;">If this was you, you can safely ignore this message.</p>

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;" />

                <p style="font-size: 14px; color: #666;">Synevyr Support Team</p>

                <p style="font-size: 12px; color: #999; margin-top: 20px; line-height: 1.5;">
                  <i>
                    Due to ongoing phishing attempts by malicious individuals, <strong>NEVER</strong> click direct links to reset your password or log in to your account.
                    We will <strong>NEVER</strong> send you a login URL. NEVER include personal information in replies as email can be spoofed.
                    <strong>synevyr.org</strong> is the only place you should ever enter your personal account information.
                  </i>
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>

    """

    # Create the email message
    msg = Message(
        subject=subject,
        sender=("Carpathian Bot", "info@carpathian.ai"),
        recipients=[recipient],  # Recipient email as a list
        html=html_body  # Use the HTML body for rich formatting
    )

    with open(logo_path, "rb") as img_file:
        img_data = img_file.read()
        if not img_data:
            raise ValueError("Logo image data is empty.")
        msg.attach(
            filename="email-logo.png",
            content_type="image/png",
            data=img_data,
            disposition="inline",
            headers={"Content-ID": "<logo_image>"}
        )


    # Send the email
    mail.send(msg)
    logger.info(f"Login notification sent to {recipient}")

def notify_user_unsuccessful_login(recipient, customer, ip_address):
    """
    Sends a notification email to the user about unsuccessful login.

    :param subject: The email subject
    :param recipient: The recipient email address
    :param customer: The customer object with user details
    :param ip_address: The IP address of the login
    """
    username = customer.username  # Assuming the customer object has a username field
    first_name = customer.first_name

    # Lookup geo-data using IP
    try:
        geo_data = get_geoip_data(ip_address)
        country = geo_data.get("country", "Unknown")
        city = geo_data.get("city", "Unknown")
        region = geo_data.get("region", "Unknown")
    except Exception as e:
        country, city, region = "Unknown", "Unknown", "Unknown"
        logger.error(f"GeoIP lookup failed for IP {ip_address}: {e}")

    # HTML body for the email
    html_body = f"""
<html>
  <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f9f9f9;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: white; padding: 40px 0;">
      <tr>
        <td align="center">
         <img src="cid:logo_image" alt="Synevyr" style="width: 120px; height: auto;" />
        </td>
      </tr>
    </table>

    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center" style="padding: 30px 20px;">
          <table width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; padding: 30px;">
            <tr>
              <td>
                <p style="font-size: 18px; margin-bottom: 20px;">Hi {first_name},</p>
                <p style="font-size: 16px; margin-bottom: 20px;">
                  A login attempt to your Synevyr account was detected but unsuccessful. Below are the login details:
                </p>

                <ul style="font-size: 16px; padding-left: 20px; margin-bottom: 20px;">
                  <li><strong>Username:</strong> {username}</li>
                  <li><strong>IP Address:</strong> {ip_address}</li>
                  <li><strong>Location:</strong> {city}, {region}, {country}</li>
                  <li><strong>Date/Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>

                <p style="font-size: 16px; margin-bottom: 20px;">
                  If this attempt was <strong>NOT</strong> you, your account is still secure. However, after 3 unsuccessful attempts, your account
                  will be locked and you'll need to reach out to support to get it reset.
                </p>

                <p style="margin-bottom: 20px;">
                  <a href="mailto:info@carpathian.ai?subject=Account%20Support&body=Username:%20{username}"
                     style="font-size: 16px; color: #1B8FF2; text-decoration: none;">
                    Contact support
                  </a>
                </p>

                <p style="font-size: 16px;">If this was you, you can ignore this message.</p>

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;" />

                <p style="font-size: 14px; color: #666;">Synevyr Support Team</p>

                <p style="font-size: 12px; color: #999; margin-top: 20px; line-height: 1.5;">
                  <i>
                    Due to ongoing phishing attempts by malicious individuals, <strong>NEVER</strong> click a link inside an email to reset your password or log in to your account.
                    We will <strong>NEVER</strong> send you a direct link to the login page. NEVER include personal information in your email replies to us as email can also be spoofed.
                    <strong>synevyr.org</strong> is the only place you should ever enter your personal account information.
                  </i>
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>

    """

    # Create the email message
    msg = Message(
        subject="‼️ Carpathian - Unsuccessful Login Attempt!",
        recipients=[recipient],  # Recipient email as a list
        html=html_body  # Use the HTML body for rich formatting
    )

    # Send the email
    mail.send(msg)
    logger.info(f"Login notification sent to {recipient}")

def notify_user_account_locked(recipient, customer, ip_address):
    """
    Sends a notification email to the user about account locked

    :param subject: The email subject
    :param recipient: The recipient email address
    :param customer: The customer object with user details
    :param ip_address: The IP address of the login
    """
    username = customer.username  # Assuming the customer object has a username field
    first_name = customer.first_name

    # Lookup geo-data using IP
    try:
        geo_data = get_geoip_data(ip_address)
        country = geo_data.get("country", "Unknown")
        city = geo_data.get("city", "Unknown")
        region = geo_data.get("region", "Unknown")
    except Exception as e:
        country, city, region = "Unknown", "Unknown", "Unknown"
        logger.error(f"GeoIP lookup failed for IP {ip_address}: {e}")

    # HTML body for the email
    html_body = f"""
    <html>
        <body>
            <p>Hi {first_name},</p>
            <p>Your Synevyr Account is Locked. Below are the login details:</p>
            <ul>
                <li><strong>Username:</strong> {username}</li>
                <li><strong>IP Address:</strong> {ip_address}</li>
                <li><strong>Location:</strong> {city}, {region}, {country}</li>
                <li><strong>Date/Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            <p>It looks like you entered your password wrong too many times so your account has been suspended for security reasons. Prior to this message you 
            should have received 3 (AND ONLY 3) login attempt messages. If you didn't receive them please contact us immediately.</p>
            <br>
            <p>For security, please go to synevyr.com through your browser and try logging in. If you get a message that your account has been suspended, please reset your password and we'll unlock
            your account.</p>
            <ul>
                <li><a href="mailto:info@carpathian.ai?subject=Account%20Support&body=Username:%20{username}">Contact Support Instead</a></li>
            </ul>
            <br>
            <p>Synevyr Support Team</p>
            <br>
            <p><i>Due to ongoing phishing attempts by malicious individuals, NEVER click a link inside an email to reset your password or login to your acount. We will NEVER send you
            a direct link to the login page. NEVER invlude personal information in your email replies to us as email can also be spoofed. Synevyr.com is the only place you
            should ever enter your personal account information.</i></p>
        </body>
    </html>
    """

    # Create the email message
    msg = Message(
        subject="❌ = 🔒 Carpathian - ACCOUNT LOCKED!",
        recipients=[recipient],  # Recipient email as a list
        html=html_body  # Use the HTML body for rich formatting
    )

    # Send the email
    mail.send(msg)
    logger.info(f"Login notification sent to {recipient}")

def notify_new_user(subject, recipient, customer, ip_address):
    """
    Sends a welcome email to the new user.

    :param subject: The email subject
    :param recipient: The recipient email address
    :param customer: The customer object with user details
    :param ip_address: The IP address of the login
    """
    username = customer.username
    first_name = customer.first_name

    # Lookup geo-data using IP
    try:
        geo_data = get_geoip_data(ip_address)
        country = geo_data.get("country", "Unknown")
        city = geo_data.get("city", "Unknown")
        region = geo_data.get("region", "Unknown")
    except Exception as e:
        country, city, region = "Unknown", "Unknown", "Unknown"
        logger.error(f"GeoIP lookup failed for IP {ip_address}: {e}")

    # HTML body for the email
    html_body = f"""
    <html>
        <body>
            <p>Hi {first_name},</p>
            <p>Welcome to Synevyr! Your account has been successfully created. Below are your details:</p>
            <ul>
                <li><strong>Your Username:</strong> {username}</li>
            </ul>
            <p>You can now log in to your account and start using our platform to manage your cloud machines and launch websites!</p>
            <p>If you have any questions or need assistance, please feel free to reach out to us.</p>
            <ul>
                <li><a href="mailto:info@carpathian.ai?subject=Account%20Support&body=Username:%20{username}">Contact Support</a></li>
            </ul>
            <br>
            <p><i>Security Note:</i> For your safety, we'll never send links inside emails to reset your password or log in to your account. Always access your account through <a href="https://synevyr.org">our official website</a>.</p>
            <br>
            <p>Best regards,<br>Synevyr Support Team</p>
        </body>
    </html>
    """

    # Create the email message
    msg = Message(
        subject=subject,
        sender=("Carpathian Bot", "info@carpathian.ai"),
        recipients=[recipient],  # Recipient email as a list
        html=html_body  # Use the HTML body for rich formatting
    )

    # Send the email
    mail.send(msg)
    logger.info(f"Welcome email sent to {recipient}")

def send_email_verification(subject, recipient, customer, token):
    """
    Sends a welcome email to the new user.

    :param subject: The email subject
    :param recipient: The recipient email address
    :param customer: The customer object with user details
    :param ip_address: The IP address of the login
    """

    first_name = customer.first_name
    # HTML body for the email
    html_body = f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f9f9f9;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: white; padding: 40px 0;">
        <tr>
            <td align="center">
           <img src="cid:logo_image" alt="Synevyr" style="width: 120px; height: auto;" />
            </td>
        </tr>
        </table>

        <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td align="center" style="padding: 30px 20px;">
            <table width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; padding: 30px;">
                <tr>
                <td>
                    <p style="font-size: 18px; margin-bottom: 20px;">Hi {first_name},</p>
                    <p style="font-size: 16px; margin-bottom: 20px;">
                    Welcome to Synevyr! To finish setting up your account, please verify your email:
                    </p>

                    <div style="font-size: 24px; font-family: monospace; background-color: #f4f4f4; padding: 12px 16px; border-radius: 6px; text-align: center; margin: 20px 0;">
                    {token}
                    </div>

                    <p style="font-size: 14px; color: #555; margin-top: 30px;">
                    <i>
                        Security Note: For your safety, we'll <strong>never</strong> send links inside emails to reset your password or log in to your account.
                        Always access your account through <a href="https://synevyr.org" style="color: #1B8FF2; text-decoration: none;">our official website</a>.
                    </i>
                    </p>

                    <p style="font-size: 14px; color: #666; margin-top: 40px;">
                    Best regards,<br/>
                    Synevyr Support Team
                    </p>
                </td>
                </tr>
            </table>
            </td>
        </tr>
        </table>
    </body>
    </html>
    """

    # Create the email message
    msg = Message(
        subject=subject,
        sender=("Carpathian Bot", "info@carpathian.ai"),
        recipients=[recipient],  # Recipient email as a list
        html=html_body  # Use the HTML body for rich formatting
    )

    # Send the email
    mail.send(msg)
    logger.info(f"Welcome email sent to {recipient}")

def send_referral_invitation_email(subject, recipient_email, referrer, ip_address):
    """
    Sends a referral invitation email to a prospective user.

    :param subject: The email subject
    :param recipient_email: The recipient's email address
    :param referrer: The User object of the person sending the referral
    :param ip_address: IP address of the sender (used for geo-location context)
    """

    referrer_name = referrer.full_name or referrer.username or "a friend"
    first_name = referrer.customer.first_name or referrer.username or "your referrer"
    referral_code = referrer.referral_code
    referral_link = f"https://synevyr.org/signup?ref={referral_code}"

    # Lookup geo-data using IP (optional but adds context or logging)
    try:
        geo_data = get_geoip_data(ip_address)
        country = geo_data.get("country", "Unknown")
        city = geo_data.get("city", "Unknown")
        region = geo_data.get("region", "Unknown")
    except Exception as e:
        country, city, region = "Unknown", "Unknown", "Unknown"
        logger.error(f"GeoIP lookup failed for IP {ip_address}: {e}")

    # Compose the HTML body
    html_body = f"""
    <html>
        <body>
            <p>Hey!</p>
            <p>{referrer_name} has invited you to join <strong>Synevyr</strong> — a premium platform for cloud-based hosting, creative deployments, and infrastructure tools built for developers and agencies.</p>

            <p>Use the link below to sign up and get started:</p>
            <p><a href="{referral_link}">{referral_link}</a></p>
            <p>By signing up through this link, you'll help {first_name} earn referral rewards and you'll gain access to our platform with the same great tools they're using.</p>
            <br>
            <p><i>Security Note:</i> We never send account login or password reset links via email. Always navigate directly to <a href="https://synevyr.org">synevyr.org</a>.</p>
            <br>
            <p>Best,<br>The Synevyr Team :)</p>
            <br>
            <p style="background-color: #b91c1c; color: #ffffff; padding: 12px; border-radius: 6px; font-size: 14px;">
                <strong>DISCLAIMER:</strong> Synevyr is still in a development state. You may encounter bugs or unfinished features. If you experience any issues, please report them to <a href="mailto:info@carpathian.ai" style="color: #ffffff; text-decoration: underline;">info@carpathian.ai</a>.
            </p>
        </body>
    </html>
    """

    # Create and send the email
    msg = Message(
        subject=subject,
        sender=("Carpathian Bot", "info@carpathian.ai"),
        recipients=[recipient_email],
        html=html_body
    )

    mail.send(msg)

    # Record the referral
    new_referral = Referral(
        referrer_id=referrer.id,
        recipient_email=recipient_email
    )
    db.session.add(new_referral)
    db.session.commit()

    logger.info(f"Referral email sent to {recipient_email} from {referrer.username}")

# Charges Notifications
def notify_user_payment_success(user, message):
    logger.info("[EMAIL LOG] Hit notify_user_payment_success successfully.")
    pass

def notify_user_payment_failure(user, message):
    logger.info("[EMAIL LOG] Hit notify_user_payment_failure successfully.")
    pass

def notify_user_cancel_success(user, message):
    logger.info("[EMAIL LOG] Hit notify_user_cancel_success successfully.")
    pass