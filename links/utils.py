import secrets
import string
from .models import ShortenedURL
Alphabet=string.ascii_letters + string.digits
code_length=7
def generate_unique_code(length=code_length):
    while True:
        code=""
        for _ in range(length):
            code+=secrets.choice(Alphabet)
        if not ShortenedURL.objects.filter(code=code).exists():
            return code
        