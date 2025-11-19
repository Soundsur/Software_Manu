# auth_worker.py
from bus_communication import BusCommunication
import os, time, hmac, json, hashlib, base64

# Config local (sin settings externos)
AUTH_SEPARATOR = ';'
SERVICE_NAME = "auth_"              # 5 chars exactos
TOKEN_TTL_SECONDS = 3600            # 1 hora
# Clave para HMAC (puedes setearla por env: set SECRET_KEY=loquesea)
SECRET_KEY = (os.getenv("SECRET_KEY") or "dev-secret-supercambia-esto").encode("utf-8")

def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

def _b64url_decode(s: str) -> bytes:
    # añade padding si falta
    pad = '=' * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _sign(data: bytes) -> str:
    sig = hmac.new(SECRET_KEY, data, hashlib.sha256).digest()
    return _b64url_encode(sig)

def generate_token(username: str) -> str:
    """
    Genera un token estilo JWT: header.payload.signature (HS256)
    Payload: sub, iat, exp
    """
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {"sub": username, "iat": now, "exp": now + TOKEN_TTL_SECONDS}

    h_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{h_b64}.{p_b64}".encode("ascii")
    sig_b64 = _sign(signing_input)
    return f"{h_b64}.{p_b64}.{sig_b64}"

def verify_token(token: str) -> bool:
    """
    Verifica firma y expiración. Útil para tests/manual.
    """
    try:
        h_b64, p_b64, s_b64 = token.split(".")
        # verificar firma
        signing_input = f"{h_b64}.{p_b64}".encode("ascii")
        expected_sig = _sign(signing_input)
        if not hmac.compare_digest(expected_sig, s_b64):
            return False
        # verificar exp
        payload = json.loads(_b64url_decode(p_b64))
        return int(time.time()) < int(payload.get("exp", 0))
    except Exception:
        return False

class AuthWorker(BusCommunication):
    def process_transaction(self, service: str, datos: str):
        """
        Formato requerido:
            service == 'auth_'
            datos   == 'LOGIN;usuario;password'
        Respuesta OK:
            'token=<jwt> iat=<unix> exp=<unix>'
        """
        if service != SERVICE_NAME:
            return "NK", "motivo=not_implemented"

        if not datos or not datos.startswith(f"LOGIN{AUTH_SEPARATOR}"):
            return "NK", "motivo=formato_login_invalido"

        parts = datos.split(AUTH_SEPARATOR, 2)  # LOGIN;user;pass
        if len(parts) != 3 or parts[0] != "LOGIN":
            return "NK", "motivo=formato_login_invalido"

        user, passwd = parts[1], parts[2]
        if not user or not passwd:
            return "NK", "motivo=credenciales_incompletas"

        # TODO: validación real. Por demo, cualquier user/pass es OK.
        tok = generate_token(user)
        # (Opcional) puedes chequear que el token sea válido:
        # assert verify_token(tok)
        now = int(time.time())
        exp = now + TOKEN_TTL_SECONDS
        return "OK", f"token={tok} iat={now} exp={exp}"

if __name__ == "__main__":
    # Levanta el worker en 0.0.0.0:5000
    AuthWorker(bus_host="0.0.0.0", bus_port=5000).listen_for_transactions(SERVICE_NAME)
