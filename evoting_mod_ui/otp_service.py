import os
import random
from database import get_db
from utils import utc_now_str

try:
    from twilio.rest import Client
except Exception:
    Client = None

ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID')


def _format_mobile(mobile: str) -> str:
    digits = ''.join(ch for ch in mobile if ch.isdigit())[-10:]
    return f'+91{digits}'


def _save_local_otp(mobile: str, otp: str):
    db = get_db()
    db.execute(
        '''INSERT INTO otp_store (mobile, otp, created_at)
           VALUES (?, ?, ?)
           ON CONFLICT(mobile)
           DO UPDATE SET otp=excluded.otp, created_at=excluded.created_at''',
        (mobile, otp, utc_now_str())
    )
    db.commit()
    db.close()


# 🔐 SEND OTP
def create_otp(mobile: str) -> dict:
    mobile = ''.join(ch for ch in mobile if ch.isdigit())[-10:]
    formatted_mobile = _format_mobile(mobile)

    print("📱 Sending OTP to:", formatted_mobile)

    # ✅ Try Twilio first
    if Client and ACCOUNT_SID and AUTH_TOKEN and VERIFY_SERVICE_SID:
        try:
            client = Client(ACCOUNT_SID, AUTH_TOKEN)

            verification = client.verify.v2.services(VERIFY_SERVICE_SID).verifications.create(
                to=formatted_mobile,
                channel='sms'
            )

            print("✅ Twilio OTP sent:", verification.status)

            return {
                'sent': True,
                'message': 'OTP sent to your mobile number'
            }

        except Exception as e:
            print("❌ Twilio Error:", str(e))

    # 🔁 Fallback OTP
    otp = str(random.randint(100000, 999999))
    _save_local_otp(mobile, otp)

    print("⚠️ Using DEMO OTP:", otp)

    return {
        'sent': True,
        'message': f'Demo OTP sent (Twilio failed). OTP: {otp}',
        'demo_otp': otp
    }


# 🔐 VERIFY OTP
def verify_otp(mobile: str, otp: str) -> bool:
    mobile = ''.join(ch for ch in mobile if ch.isdigit())[-10:]
    formatted_mobile = _format_mobile(mobile)

    print("🔍 Verifying OTP for:", formatted_mobile)

    # ✅ Try Twilio verification
    if Client and ACCOUNT_SID and AUTH_TOKEN and VERIFY_SERVICE_SID:
        try:
            client = Client(ACCOUNT_SID, AUTH_TOKEN)

            check = client.verify.v2.services(VERIFY_SERVICE_SID).verification_checks.create(
                to=formatted_mobile,
                code=otp
            )

            print("🔐 Twilio verification status:", check.status)

            if check.status == 'approved':
                return True

        except Exception as e:
            print("❌ Twilio Verify Error:", str(e))

    # 🔁 Fallback verification
    db = get_db()
    row = db.execute(
        'SELECT otp FROM otp_store WHERE mobile=?',
        (mobile,)
    ).fetchone()
    db.close()

    return bool(row and row['otp'] == str(otp).strip())