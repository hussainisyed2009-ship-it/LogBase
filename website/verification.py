from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mailman import EmailMessage

def get_token(email, key):
    serializer = URLSafeTimedSerializer(key)
    token = serializer.dumps(email)
    return token
