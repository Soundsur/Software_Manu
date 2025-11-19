# bus_communication.py
import socket
import re
class BusCommunication:
    def __init__(self, bus_host="localhost", bus_port=5000):
        self.bus_host = bus_host
        self.bus_port = bus_port

    @staticmethod
    def build_tx(service5: str, data: str) -> str:
        """
        TX (cliente -> bus/servicio) = NNNNN + SSSSS + DATOS
        NNNNN = len(SSSSS + DATOS)
        """
        assert len(service5) == 5, "service5 debe tener 5 chars"
        body = f"{service5}{data}"
        return f"{len(body):05d}{body}"

    @staticmethod
    def parse_rx(rx: str):
        """
        RX (bus/servicio -> cliente) = NNNNN + SSSSS + (OK|NK) + DATOS
        """
        n = int(rx[:5])
        service = rx[5:10]
        status  = rx[10:12]        # OK / NK
        datos   = rx[12:5+n]       # solo lo declarado por NNNNN
        return service, status, datos

    def send_transaction(self, service5, data):
        tx = self.build_tx(service5, data)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((self.bus_host, self.bus_port))
            s.sendall(tx.encode())
            rx = s.recv(4096).decode()
        return rx

    # === Servidor LOCAL de prueba (NO usar cuando el bus real esté corriendo) ===
    def listen_for_transactions(self, service_name="auth_"):
        """
        Modo loopback para pruebas sin el contenedor del bus.
        No lo uses en Docker junto al soabus porque choca con :5000.
        """
        host = "0.0.0.0"
        port = self.bus_port

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.listen(5)
            print(f"[worker-local] Escuchando en {host}:{port} …")

            while True:
                conn, addr = s.accept()
                with conn:
                    rx = conn.recv(4096).decode()
                    if not rx:
                        continue
                    body_len = int(rx[:5])
                    service  = rx[5:10]
                    datos    = rx[10:5+body_len]

                    status, datos_resp = self.process_transaction(service, datos)

                    resp_body = f"{service}{status}{datos_resp}"
                    resp = f"{len(resp_body):05d}{resp_body}"
                    conn.sendall(resp.encode())

    def process_transaction(self, service: str, datos: str):
        """
        Autenticación de demo:
        Acepta 'auth_' + LOGIN con formato:
        - "LOGIN;user;pass"  (legacy)
        - "LOGIN user pass"  (espacios)
        - "LOGIN,user,pass"  (comas)
        - "LOGIN  user   pass" (múltiples espacios)
        Nota: SIN separadores absolutamente (p.ej. 'LOGINuserpass') NO es un
        formato determinable; define una regla si quieres soportarlo.
        """
        if service != "auth_":
            return "NK", "motivo=not_implemented"

        cmd = (datos or "").strip()
        if not cmd.startswith("LOGIN"):
            return "NK", "motivo=formato_login_invalido"

        tail = cmd[5:]  # todo lo que viene después de 'LOGIN'
        # Normalizar: convertir cualquier secuencia de separadores comunes a un solo espacio
        # separadores aceptados: ; , espacios, tabs
        tail_norm = re.sub(r"[;,\s]+", " ", tail).strip()

        parts = tail_norm.split(" ")
        if len(parts) >= 2 and parts[0] and parts[1]:
            user, passwd = parts[0], parts[1]
            # Aquí harías tu validación real; por ahora, demo OK siempre:
            return "OK", "token=falso"

        return "NK", "motivo=credenciales_incompletas"

