import socket

class BusCommunication:
    def __init__(self, bus_host="soabus", bus_port=5000):
        self.bus_host = bus_host
        self.bus_port = bus_port

    def send_transaction(self, service, data):
        """
        Envia una transacción al bus y espera la respuesta.
        La transacción tiene el formato: NNNNNSSSSSDATOS
        """
        # Formatear la transacción: longitud total + nombre del servicio + datos
        transaction = f"{len(data) + 10:05d}{service:5s}{data}"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.bus_host, self.bus_port))  # Conectar al bus
            s.sendall(transaction.encode())  # Enviar la transacción
            response = s.recv(1024).decode()  # Recibir la respuesta

        return response

    def listen_for_transactions(self):
        """
        Escucha las transacciones entrantes en el bus (puerto 5000).
        """
        host = "0.0.0.0"
        port = self.bus_port

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen(5)
            print(f"Escuchando en {host}:{port}...")

            while True:
                conn, addr = s.accept()
                with conn:
                    print("Conexión recibida")
                    transaction = conn.recv(1024).decode()  # Recibir la transacción
                    if transaction:
                        print(f"Transacción recibida: {transaction}")
                        response_status = self.process_transaction(transaction)
                        response = f"{len(response_status + transaction) + 10:05d}auth_s{response_status}{transaction[10:]}"
                        conn.sendall(response.encode())  # Enviar la respuesta

    def process_transaction(self, data):
        """
        Lógica para procesar las transacciones (por ejemplo, autenticación).
        """
        # Aquí podemos implementar la lógica real de autenticación.
        if data.startswith("usuario1234"):  # Ejemplo simple de autenticación
            return "OK"
        return "NK"
