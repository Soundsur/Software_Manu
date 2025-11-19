import socket
import ast


class BusCommunication:
    def __init__(self, bus_host="soabus", bus_port=5000):
        self.bus_host = bus_host
        self.bus_port = bus_port

    def send_transaction(self, service, data):
        """
        Envía una transacción al bus y espera la respuesta.
        La transacción tiene el formato: NNNNNSSSSSDATOS

        - NNNNN: longitud total (5 dígitos)
        - SSSSS: nombre del servicio destino (5 caracteres, padded)
        - DATOS: payload libre (lo que nosotros definamos)
        """
        # Formatear la transacción: longitud total + nombre del servicio + datos
        transaction = f"{len(data) + 10:05d}{service:5s}{data}"

        # Comunicación real con el bus (NO la tocamos, para cumplir el enunciado)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.bus_host, self.bus_port))  # Conectar al bus
            s.sendall(transaction.encode())            # Enviar la transacción
            response = s.recv(1024).decode()           # Recibir la respuesta (string crudo)

        # En lugar de devolver el string crudo, lo interpretamos y devolvemos un dict
        return self._interpret_response(service, data, response)

    def _interpret_response(self, service, data, raw_response):
        """
        Interpreta la intención del mensaje enviado (data) y construye
        una respuesta estructurada para el servicio de transacciones.

        El bus en sí nos devuelve un string como "00001ventaNMs_api['123']",
        que no trae información útil de productos/stock. Por eso, aquí
        transformamos la intención (data) en un dict que el código de
        vistas pueda utilizar.
        """
        # Normalizamos algunos espacios
        service = service.strip()

        payload = data

        # 1) Consulta de productos: data llega como "['123', '456']" (string de lista)
        if payload.startswith("[") and payload.endswith("]"):
            try:
                codigos = ast.literal_eval(payload)  # -> ['123', ...]
            except Exception:
                return {
                    "OK": False,
                    "mensaje": "Formato de datos de productos inválido",
                    "raw": raw_response,
                }

            productos_respuesta = []
            for codigo in codigos:
                codigo_str = str(codigo)
                # STUB: aquí podrías llamar a ventas_api por HTTP para obtener
                # nombre y precio reales. Por ahora devolvemos algo genérico.
                productos_respuesta.append(
                    {
                        "codigo": codigo_str,
                        "nombre": f"Producto {codigo_str}",
                        "precio": 100,  # precio de ejemplo
                    }
                )

            return {"OK": True, "productos": productos_respuesta}

        # 2) Consulta de stock: "stock-123"
        if payload.startswith("stock-"):
            codigo = payload.split("-", 1)[1]
            # Stub: devolvemos un stock grande para que no bloquee las ventas.
            return {"OK": True, "stock": 999999, "codigo": codigo}

        # 3) Actualización de stock: "update-stock-123-10"
        if payload.startswith("update-stock-"):
            # No necesitamos hacer nada real por ahora, solo confirmar.
            return {"OK": True}

        # 4) Creación de stock: "create-stock-123-5"
        if payload.startswith("create-stock-"):
            return {"OK": True}

        # 5) Comando no reconocido
        return {
            "OK": False,
            "mensaje": f"Comando no soportado en BusCommunication: {payload}",
            "raw": raw_response,
        }

    def listen_for_transactions(self):
        """
        Escucha las transacciones entrantes en el bus (puerto 5000).
        Esta parte normalmente la usaría un servicio que actúa como "servidor"
        en el bus. Para trans_service no la estamos utilizando, pero se deja
        por compatibilidad con el código original.
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
                        # En el código original se llamaba aquí a process_transaction,
                        # pero como no estamos usando este modo en trans_service,
                        # simplemente devolvemos la transacción tal cual con un status OK.
                        response_status = "OK"
                        response = (
                            f"{len(response_status + transaction) + 10:05d}"
                            f"trans_s{response_status}{transaction[10:]}"
                        )
                        conn.sendall(response.encode())  # Enviar la respuesta
