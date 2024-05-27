import socket
import time
import random
import sys
import threading

stop_event = threading.Event()


def wait_and_roll(name, s, spieler_latenz):
    try:
        wait_time = random.uniform(0, spieler_latenz)
        print(f"Waiting for {wait_time} seconds...")
        if stop_event.wait(timeout=wait_time):
            print("STOP signal received. Skipping roll.")
            return  # STOP signal received, exit the thread
        wurf = random.randint(1, 100)
        s.sendall(f"{name}:{wurf}".encode())
    except Exception as e:
        print(f"Error in wait_and_roll: {e}")


def play_game(name, host, port, spieler_latenz):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(name.encode())
        print(f"Connected to server as {name}.")

        while True:
            msg = s.recv(1024).decode()
            print(f"Received: {msg}")
            if msg == "START":
                stop_event.clear()
                threading.Thread(
                    target=wait_and_roll, args=(name, s, spieler_latenz)
                ).start()
            elif msg == "STOP":
                stop_event.set()
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
