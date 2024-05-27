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
    def __init__(self, host, port, dauer_der_runde):
        self.host = host
        self.port = port
        self.dauer_der_runde = dauer_der_runde
        self.players = []
        self.lock = threading.Lock()
        self.results = []

    def handle_player(self, conn, addr):
        name = conn.recv(1024).decode()
        self.players.append((name, conn))
        if len(self.players) == 3:
            threading.Thread(target=self.start_game).start()
            print("Game started.")
        print(f"Player {name} from {addr} has joined the game.")

        while True:
            try:
                msg = conn.recv(1024).decode()
                if msg:
                    print(f"Received: {msg}")
                    name, wurf = msg.split(":")
                    wurf = int(wurf)
                    with self.lock:
                        self.results.append((name, wurf))
            except:
                break

    def start_game(self):
        for i in range(TOTAL_ROUNDS):
            print(f"Starting round {i+1}")
            with self.lock:
                self.results = []

            for name, conn in self.players:
                conn.sendall(b"START")

            time.sleep(self.dauer_der_runde)

            for name, conn in self.players:
                conn.sendall(b"STOP")

            with self.lock:
                entries = len(self.results)
                winner = ("'Nobody participated'", 0)
                if entries > 0:
                    winner = max(self.results, key=lambda x: x[1])
                print(f"Round Winner: {winner[0]} with a roll of {winner[1]}")
                rounds.append(
                    {
                        "round": i + 1,
                        "winner": winner[0],
                        "roll": winner[1],
                        "participants": [name for name, _ in self.results],
                    }
                )
            # stop server
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
    # try:
    #     gm.start_game()
    # except KeyboardInterrupt:
    #     print("Game interrupted by keyboard.")
    #     sys.exit(0)
