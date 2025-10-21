import socket

def test_connection():
    host = "soabus"  # Nombre del contenedor del bus en la red Docker
    port = 5000      # Puerto donde el bus está escuchando

    # Crear un socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Intentar conectar al bus
            s.connect((host, port))
            print(f"Conexión exitosa a {host}:{port}")
        except Exception as e:
            print(f"No se pudo conectar a {host}:{port}. Error: {e}")

test_connection()

