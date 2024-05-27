import socket
import threading
import time
import sys
import json
import os
import signal

TOTAL_ROUNDS = 300

rounds = []


class GameMaster:

    lamport_counter: int = 0

    def __init__(self, host, port, dauer_der_runde):
        self.host = host
        self.port = port
        self.dauer_der_runde = dauer_der_runde
        self.players = []
        self.lock = threading.Lock()
        self.results = []
        self.last_start = 0
        self.last_stop = 0

    def handle_player(self, conn, addr):
        name = conn.recv(1024).decode()
        self.players.append((name, conn))
        print(f"Player {name} from {addr} has joined the game.")
        if len(self.players) == 3:
            threading.Thread(target=self.start_game).start()
            print("Game started.")

        while True:
            try:
                msg = conn.recv(1024).decode()
                if msg:
                    print(f"Received: {msg}")
                    lc, name, wurf = msg.split(":")
                    lc = int(lc)
                    with self.lock:
                        self.lamport_counter = max(self.lamport_counter, lc) + 1
                        wurf = int(wurf)
                        self.results.append((lc, name, wurf))
            except:
                break

    def start_game(self):
        for i in range(TOTAL_ROUNDS):
            print(f"Starting round {i+1}")
            with self.lock:
                self.results = []

            with self.lock:
                self.lamport_counter += 1
                self.last_start = self.lamport_counter
                print(f"Starting round with counter: {self.lamport_counter}")
                for name, conn in self.players:
                    try:
                        conn.sendall(f"{self.lamport_counter}:START".encode())
                    except:
                        try:
                            time.sleep(2)
                            conn.sendall(f"{self.lamport_counter}:START".encode())
                        except:
                            time.sleep(4)
                            conn.sendall(f"{self.lamport_counter}:START".encode())
                        # self.players.remove((name, conn))

            time.sleep(self.dauer_der_runde)

            with self.lock:
                self.lamport_counter += 1
                self.last_stop = self.lamport_counter
                print(f"Stopping round with counter: {self.lamport_counter}")
                for name, conn in self.players:
                    try:
                        conn.sendall(f"{self.lamport_counter}:STOP".encode())
                    except:
                        try:
                            time.sleep(2)
                            conn.sendall(f"{self.lamport_counter}:STOP".encode())
                        except:
                            time.sleep(4)
                            conn.sendall(f"{self.lamport_counter}:STOP".encode())
                        # self.players.remove((name, conn))

            with self.lock:
                winner = (-1, "'Nobody participated'", 0)
                for entry in self.results:
                    if entry[0] <= self.last_start or entry[0] >= self.last_stop:
                        print(f"Player {entry[1]} missed the stop event.")
                        self.results.remove(entry)
                entries = len(self.results)
                if entries > 0:
                    winner = max(self.results, key=lambda x: x[2])
                print(f"Round Winner: {winner[1]} with a roll of {winner[2]}")
                rounds.append(
                    {
                        "round": i + 1,
                        "winner": winner[1],
                        "roll": winner[2],
                        "participants": [name for _, name, _ in self.results],
                    }
                )
        print(f"Game concluded after {TOTAL_ROUNDS} rounds.")
        with open("results.json", "w") as f:
            json.dump(rounds, f, indent=2)
        os.kill(os.getpid(), signal.SIGINT)

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"GameMaster listening on {self.host}:{self.port}")

            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_player, args=(conn, addr)).start()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python game_master.py <DAUER_DER_RUNDE> <PORT>")
        sys.exit(1)

    DAUER_DER_RUNDE = int(sys.argv[1])
    PORT = int(sys.argv[2])

    gm = GameMaster("0.0.0.0", PORT, DAUER_DER_RUNDE)
    threading.Thread(target=gm.start_server).start()
