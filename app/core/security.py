import hashlib
import hmac
import secrets


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        310_000,
    ).hex()
    return f"pbkdf2_sha256${salt}${password_hash}"


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        310_000,
    ).hex()
    return hmac.compare_digest(password_hash, expected_hash)


def verify_stored_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected_hash = stored_hash.split("$", 2)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    return verify_password(password, salt, expected_hash)
