import socket
import threading
import time
import sys

class GameMaster:

    lamport_counter: int = 0

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
        print(f"Player {name} from {addr} has joined the game.")
        
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
        while True:
            with self.lock:
                self.results = []
            
            with self.lock:
                self.lamport_counter += 1
                print(f"Starting round with counter: {self.lamport_counter}")
                for name, conn in self.players:
                    conn.sendall(f"{self.lamport_counter}:START".encode())
            
            time.sleep(self.dauer_der_runde)

            stop_event: int
            with self.lock:
                self.lamport_counter += 1
                stop_event = self.lamport_counter
                print(f"Stopping round with counter: {self.lamport_counter}")
                for name, conn in self.players:
                    conn.sendall(f"{self.lamport_counter}:STOP".encode())
            
            with self.lock:
                if self.results:
                    for entry in self.results:
                        if entry[0] >= stop_event:
                            print(f"Player {entry[1]} missed the stop event.")
                            self.results.remove(entry)
                    winner = max(self.results, key=lambda x: x[2])
                    print(f"Round Winner: {winner[1]} with a roll of {winner[2]}")
                    with open("game_results.txt", "a") as f:
                        f.write(f"Winner: {winner[1]}, Roll: {winner[2]}\n")

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

    gm = GameMaster('0.0.0.0', PORT, DAUER_DER_RUNDE)
    threading.Thread(target=gm.start_server).start()
    try:
        gm.start_game()
    except KeyboardInterrupt:
        print("Game interrupted by keyboard.")
        sys.exit(0)
