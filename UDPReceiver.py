import socket
import os

HOST = '0.0.0.0'
PORT = 32200

host_ip = os.getenv('HOST_IP')
if not host_ip:
    raise ValueError('Environment variable "HOST_IP" not set')

recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.bind((HOST, PORT))
# Create a UDP socket for sending responses
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Listening for UDP broadcasts on {HOST}:{PORT}")

while True:
    data, sender_addr = recv_sock.recvfrom(1024)  # Buffer size can be adjusted

    if data == b"ESP32 MGMT IP request":
        print(f'{sender_addr[0]}:{sender_addr[1]} requests MGMT IP')

        # Prepare and send response
        response_message = host_ip.encode()
        response_size = int(len(response_message)).to_bytes(4, byteorder='little')
        send_sock.sendto(response_size + response_message, sender_addr)

recv_sock.close()
send_sock.close()
