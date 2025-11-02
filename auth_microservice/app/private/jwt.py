import secrets

# Genera una chiave segreta JWT
jwt_secret_key = secrets.token_hex(32)
print(jwt_secret_key)