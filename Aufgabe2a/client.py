import socket
import time
import random
import sys

def play_game(name, host, port, spieler_latenz):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(name.encode())

        while True:
            msg = s.recv(1024)
            if msg == b'START':
                time.sleep(random.uniform(0, spieler_latenz))
                wurf = random.randint(1, 100)
                s.sendall(f"{name}:{wurf}".encode())
            elif msg == b'STOP':
                continue

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python player.py <NAME> <HOST> <PORT> <SPIELER_LATENZ>")
        sys.exit(1)

    NAME = sys.argv[1]
    HOST = sys.argv[2]
    PORT = int(sys.argv[3])
    SPIELER_LATENZ = int(sys.argv[4])

    play_game(NAME, HOST, PORT, SPIELER_LATENZ)
