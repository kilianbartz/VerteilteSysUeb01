import socket
import time
import random
import sys

lamport_counter = 0

def play_game(name, host, port, spieler_latenz):
    global lamport_counter
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(name.encode())
        print(f"Connected to server as {name}.")

        while True:
            msg = s.recv(1024).decode()
            print(f"Received: {msg}")
            lc_sender, msg = msg.split(":")
            lc_sender = int(lc_sender)
            if msg == "START":
                lamport_counter = max(lamport_counter, lc_sender) + 1
                time.sleep(random.uniform(0, spieler_latenz))
                wurf = random.randint(1, 100)
                lamport_counter += 1
                s.sendall(f"{lamport_counter}:{name}:{wurf}".encode())
            else:
                lamport_counter = max(lamport_counter, lc_sender) + 1
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
