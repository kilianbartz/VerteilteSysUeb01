import socket
import time
import random
import sys
import threading

lamport_counter = 0
lamport_lock = threading.Lock()
stop_event = threading.Event()

def wait_and_roll(name, s, spieler_latenz):
    global lamport_counter
    try:
        wait_time = random.uniform(0, spieler_latenz)
        print(f"Waiting for {wait_time} seconds...")
        if stop_event.wait(timeout=wait_time):
            print("STOP signal received. Skipping roll.")
            return  # STOP signal received, exit the thread
        
        wurf = random.randint(1, 100)
        with lamport_lock:
            lamport_counter += 1
            s.sendall(f"{lamport_counter}:{name}:{wurf}".encode())
            print(f"Sent with counter: {lamport_counter}")
    except Exception as e:
        print(f"Error in wait_and_roll: {e}")

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
            with lamport_lock:
                lamport_counter = max(lamport_counter, lc_sender) + 1
                print(f"Updated counter to: {lamport_counter}")
            if msg == "START":
                stop_event.clear()
                threading.Thread(target=wait_and_roll, args=(name, s, spieler_latenz)).start()
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
