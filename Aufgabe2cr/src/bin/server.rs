use aufgabe2cr::*;
use std::collections::HashMap;
use std::env;
use std::sync::{Arc, Mutex};
use std::vec;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::tcp::{OwnedReadHalf, OwnedWriteHalf};
use tokio::net::TcpListener;
use tokio::time::{sleep, Duration};

type Resultslist = Arc<Mutex<Vec<ClientDiceRoll>>>;

#[tokio::main]
async fn main() {
    let args: Vec<String> = env::args().collect();
    let listener = TcpListener::bind("127.0.0.1:12345").await.unwrap();
    let mut clients: Vec<OwnedWriteHalf> = Vec::new();
    let mut uuids: HashMap<String, String> = HashMap::new();
    let num_clients: i32 = args[1].parse().unwrap();
    println!("Waiting for {} clients to join...", num_clients);
    let results = Arc::new(Mutex::new(Vec::new()));

    for _ in 0..num_clients {
        let (socket, _) = listener.accept().await.unwrap();
        let (mut reader, mut writer) = socket.into_split();
        let my_results = results.clone();

        // read the join message and assign client an uuid which is sent back
        let mut buf = vec![0; 1024];
        let n = reader.read(&mut buf).await.unwrap();
        let buf = &buf[..n];
        let buf = std::str::from_utf8(buf).unwrap();
        let message: ClientJoin = serde_json::from_str(buf).unwrap();
        let uuid = uuid::Uuid::new_v4().to_string();
        println!("Client joined: {}", message.name);
        uuids.insert(uuid.clone(), message.name);
        let response = ClientJoinResponse { uuid };
        let response = serde_json::to_string(&response);
        let response = response.unwrap();
        let response = response.as_bytes();
        writer.write_all(&response).await.unwrap();

        clients.push(writer);

        // spawn a new task to handle the client
        tokio::spawn(async move {
            process_client(reader, my_results).await;
        });
    }
    println!("Starting game...");
    let mut round_stats: Vec<RoundStats> = Vec::new();
    for round in 0..10 {
        println!("started Round {}", round);
        let stats = handle_round(round, &mut clients, results.clone()).await;
        round_stats.push(stats);
    }
    println![
        "Round stats: {:?}",
        round_stats
            .iter()
            .map(|stats| stats.number_rolls)
            .collect::<Vec<u64>>()
    ];
}
async fn process_client(mut reader: OwnedReadHalf, results: Resultslist) {
    let mut buf = vec![0; 1024];
    loop {
        let n = reader.read(&mut buf).await.unwrap();
        if n == 0 {
            break;
        }
        let buf = &buf[..n];
        let buf = std::str::from_utf8(buf).unwrap();
        let message: ClientDiceRoll = serde_json::from_str(&buf).unwrap();
        let mut results = results.lock().unwrap();
        results.push(message);
    }
}

async fn handle_round(
    round_nr: u64,
    clients: &mut Vec<OwnedWriteHalf>,
    results: Resultslist,
) -> RoundStats {
    let start_message = ServerMessage {
        command: Commands::StartRound,
        lamport_counter: round_nr,
    };
    let start_message = serde_json::to_string(&start_message).unwrap();
    let start_message = start_message.as_bytes();
    for client in clients.iter_mut() {
        client.write_all(&start_message).await.unwrap();
    }
    println!("Sent all clients StartRound message {}", round_nr);
    // round goes for 3 seconds
    sleep(Duration::from_secs(3)).await;
    let mut results = results.lock().unwrap();
    let default_roll = ClientDiceRoll {
        uuid: "".to_string(),
        value: 0,
        lamport_counter: 0,
    };
    let max_roll = results.iter().max().cloned().unwrap_or(default_roll);
    let number_rolls = results.len() as u64;
    let message = ServerMessage {
        command: Commands::EndRound,
        lamport_counter: round_nr,
    };
    let message = serde_json::to_string(&message).unwrap();
    let message = message.as_bytes();
    for client in clients.iter_mut() {
        client.write_all(&message).await.unwrap();
    }
    println!(
        "Sent all clients {} EndRound message {}",
        clients.len(),
        round_nr
    );
    let stats = RoundStats {
        number_rolls,
        max_roll,
    };
    results.clear();
    println!("Round {} stats: {:?}", round_nr, stats);
    stats
}
