# test_bus_communication.py (cliente)
from bus_communication import BusCommunication

bus = BusCommunication(bus_host="localhost", bus_port=5000)
raw_rx = bus.send_transaction("auth_", "LOGIN;luna;luna123")
svc, status, datos = BusCommunication.parse_rx(raw_rx)
print("status:", status)
print("datos:", datos)

# Extra: validar que el token tenga 3 partes (header.payload.signature)
tok = datos.split("token=")[1].split()[0]
assert len(tok.split(".")) == 3
print("token:", tok)
