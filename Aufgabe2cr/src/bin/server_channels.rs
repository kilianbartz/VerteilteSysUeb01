use aufgabe2cr::*;
use std::collections::HashMap;
use std::vec;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::tcp::{OwnedReadHalf, OwnedWriteHalf};
use tokio::net::TcpListener;
use tokio::sync::mpsc;
use tokio::sync::mpsc::Receiver;
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() {
    let listener = TcpListener::bind("127.0.0.1:12345").await.unwrap();
    let mut clients: Vec<OwnedWriteHalf> = Vec::new();
    let mut uuids: HashMap<String, String> = HashMap::new();
    let (tx, mut rx) = mpsc::channel::<ClientDiceRoll>(32);
    const NUM_CLIENTS: i32 = 2;

    for _ in 0..NUM_CLIENTS {
        let (socket, _) = listener.accept().await.unwrap();
        let (mut reader, mut writer) = socket.into_split();
        let my_tx = tx.clone();

        // read the join message and assign client an uuid which is sent back
        let mut buf = vec![0; 1024];
        let n = reader.read(&mut buf).await.unwrap();
        let message: ClientJoin = bincode::deserialize(&buf[..n]).unwrap();
        let uuid = uuid::Uuid::new_v4().to_string();
        println!("Client joined: {}", message.name);
        uuids.insert(uuid.clone(), message.name);
        let response = ClientJoinResponse { uuid };
        let response = bincode::serialize(&response).unwrap();
        writer.write_all(&response).await.unwrap();

        clients.push(writer);

        // spawn a new task to handle the client
        tokio::spawn(async move {
            process_client(reader, my_tx).await;
        });
    }
    println!("Starting game...");
    let mut round_stats: Vec<RoundStats> = Vec::new();
    for round in 0..10 {
        println!("started Round {}", round);
        let stats = handle_round(round, &mut clients, &mut rx).await;
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
async fn process_client(mut reader: OwnedReadHalf, tx: mpsc::Sender<ClientDiceRoll>) {
    let mut buf = vec![0; 1024];
    loop {
        let n = reader.read(&mut buf).await.unwrap();
        if n == 0 {
            break;
        }
        let message: ClientDiceRoll = bincode::deserialize(&buf).unwrap();
        tx.send(message).await.unwrap();
    }
}

async fn handle_round(
    round_nr: u64,
    clients: &mut Vec<OwnedWriteHalf>,
    rx: &mut Receiver<ClientDiceRoll>,
) -> RoundStats {
    let start_message = ServerMessage {
        command: Commands::StartRound,
        lamport_counter: round_nr,
    };
    for client in clients.iter_mut() {
        let start_message = bincode::serialize(&start_message).unwrap();
        client.write_all(&start_message).await.unwrap();
    }
    println!("Sent all clients StartRound message");
    // round goes for 3 seconds
    let start = std::time::Instant::now();
    let mut number_rolls = 0;
    let mut max_roll: ClientDiceRoll = ClientDiceRoll {
        uuid: "".to_string(),
        value: 0,
        lamport_counter: 0,
    };
    sleep(Duration::from_secs(3)).await;
    while let Some(message) = rx.recv().await {
        if start.elapsed().as_secs() >= 3 {
            // empty the channel without processing messages arrived too late
            println!("uuid: {} arrived too late", message.uuid);
            continue;
        }
        println!("uuid: {} rolled: {}", message.uuid, message.value);
        number_rolls += 1;
        if message > max_roll {
            max_roll = message;
        }
    }
    let message = ServerMessage {
        command: Commands::EndRound,
        lamport_counter: round_nr,
    };
    for client in clients.iter_mut() {
        let message = bincode::serialize(&message).unwrap();
        client.write_all(&message).await.unwrap();
    }
    let stats = RoundStats {
        number_rolls,
        max_roll,
    };
    println!("Round {} stats: {:?}", round_nr, stats);
    stats
}
