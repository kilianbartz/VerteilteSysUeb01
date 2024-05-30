import socket
import random
import sys
import threading
import json
import uuid

lamport_counter = 0
lamport_lock = threading.Lock()
stop_event = threading.Event()


def wait_and_roll(my_uuid, s, spieler_latenz):
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
            roll = {"uuid": my_uuid, "value": wurf, "lamport_counter": lamport_counter}
            s.sendall(json.dumps(roll).encode())
            print(f"Sent with counter: {lamport_counter}")
    except Exception as e:
        print(f"Error in wait_and_roll: {e}")


def play_game(name, host, port, spieler_latenz):
    global lamport_counter
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        join = {"name": f"client_{str(uuid.uuid4())}"}
        s.sendall(json.dumps(join).encode())
        print(f"Connected to server as {name}.")
        msg = s.recv(1024).decode()
        print(f"Received message: {msg}")
        my_uuid = json.loads(msg)["uuid"]

        while True:
            msg = s.recv(1024).decode()
            print(f"Received message: {msg}")
            msg = json.loads(msg)
            with lamport_lock:
                lamport_counter = max(lamport_counter, msg["lamport_counter"]) + 1
                print(f"Updated counter to: {lamport_counter}")
            if msg["command"] == "StartRound":
                stop_event.clear()
                threading.Thread(
                    target=wait_and_roll, args=(my_uuid, s, spieler_latenz)
                ).start()
            else:
                stop_event.set()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python player.py <NAME> <HOST> <PORT> <SPIELER_LATENZ>")
        sys.exit(1)

    NAME = sys.argv[1]
    HOST = sys.argv[2]
    PORT = int(sys.argv[3])
    SPIELER_LATENZ = int(sys.argv[4])

    play_game(NAME, HOST, PORT, SPIELER_LATENZ)
