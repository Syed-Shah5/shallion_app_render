from django.core import signing
from django.utils import timezone
from django.contrib.auth import get_user_model
from config import settings

User = get_user_model()

# Token configuration
TOKEN_SALT = "email-verification"
TOKEN_MAX_AGE = 60 * 60 * 24  # 24 hours

# Generate Verification Token
def generate_email_verification_token(user):
  
    data = {
        "user_id": user.id,
        "email": user.email,
    }

    token = signing.dumps(data, salt=TOKEN_SALT)

    return token

# Verify Email Token
def verify_email_token(token):
  
    try:
        data = signing.loads(
            token,
            salt=TOKEN_SALT,
            max_age=TOKEN_MAX_AGE
        )

        user = User.objects.get(id=data["user_id"])

        # Prevent verification replay
        if user.is_email_verified:
            return user

        # Extra security check
        if user.email != data["email"]:
            return None

        user.is_email_verified = True
        user.email_verified_at = timezone.now()

        # Activate account if other requirements satisfied
        if user.role == "CLIENT" and user.gp_certificate_verified:
            user.status = "ACTIVE"

        elif user.role == "VOLUNTEER" and user.pvg_verified:
            user.status = "ACTIVE"

        user.save()

        return user

    except signing.SignatureExpired:
        
        return None

    except signing.BadSignature:
      
        return None

    except User.DoesNotExist:
        return None

# Send Verification Email
def send_verification_email(user):
  
    token = generate_email_verification_token(user)

    verification_url = f"{settings.SITE_URL}/accounts/verify-email/{token}/"

    print("\n================ EMAIL VERIFICATION ================")
    print(f"User: {user.email}")
    print("Verification Link:")
    print(verification_url)
    print("====================================================\n")

    return True