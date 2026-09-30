import hashlib
import hmac
import secrets


ITERATIONS = 310_000
SALT_BYTES = 16
KEY_BYTES = 32


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    salt = secrets.token_bytes(SALT_BYTES)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
        dklen=KEY_BYTES
    )

    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
            dklen=KEY_BYTES
        )

        return hmac.compare_digest(
            password_hash.hex(),
            hash_hex
        )

    except (ValueError, TypeError):
        return False