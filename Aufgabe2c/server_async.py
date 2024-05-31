import socket
import threading
import time
import sys
import json
import os
import signal

TOTAL_ROUNDS = 300
NUMBER_PARTICIPANTS = int(sys.argv[3])
print(f"Number of participants: {NUMBER_PARTICIPANTS}")

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
        print(
            f"Player {name} from {addr} has joined the game.",
            f"{len(self.players)} / {NUMBER_PARTICIPANTS}",
        )
        if len(self.players) == NUMBER_PARTICIPANTS:
            threading.Thread(target=self.start_game).start()
            print("Game started.")

        while True:
            try:
                msg = conn.recv(1024).decode()
                if msg:
                    # print(f"Received: {msg}")
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
            starttime = time.time()
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
                        print(f"Player {name} disconnected.")
                        self.players.remove((name, conn))

            time.sleep(self.dauer_der_runde)

            with self.lock:
                self.lamport_counter += 1
                self.last_stop = self.lamport_counter
                print(f"Stopping round with counter: {self.lamport_counter}")
                for name, conn in self.players:
                    try:
                        conn.sendall(f"{self.lamport_counter}:STOP".encode())
                    except:
                        print(f"Player {name} disconnected.")
                        self.players.remove((name, conn))
                winner = (-1, "'Nobody participated'", 0)
                punctual = [
                    entry
                    for entry in self.results
                    if entry[0] > self.last_start and entry[0] < self.last_stop
                ]
                entries = len(punctual)
                if entries > 0:
                    winner = max(punctual, key=lambda x: x[2])
                print(f"Round Winner: {winner[1]} with a roll of {winner[2]}")
                rounds.append(
                    {
                        "round": i + 1,
                        "start_lc": self.last_start,
                        "end_lc": self.last_stop,
                        "winner": winner[1],
                        "roll": winner[2],
                        "participants": punctual,
                        "time_per_round": f"{time.time() - starttime} seconds",
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
    if len(sys.argv) != 4:
        print(
            "Usage: python game_master.py <DAUER_DER_RUNDE> <PORT> <NUMBER_PARTICIPANTS>"
        )
        sys.exit(1)

    DAUER_DER_RUNDE = int(sys.argv[1])
    PORT = int(sys.argv[2])

    gm = GameMaster("0.0.0.0", PORT, DAUER_DER_RUNDE)
    threading.Thread(target=gm.start_server).start()
