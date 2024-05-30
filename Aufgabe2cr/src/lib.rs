use serde::{Deserialize, Serialize};

#[derive(Deserialize, Serialize, Debug, Clone)]
pub struct ClientDiceRoll {
    pub uuid: String,
    pub value: u8,
    pub lamport_counter: u64,
}

impl PartialEq for ClientDiceRoll {
    fn eq(&self, other: &Self) -> bool {
        self.value == other.value
    }
}
impl Eq for ClientDiceRoll {}

impl PartialOrd for ClientDiceRoll {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        self.value.partial_cmp(&other.value)
    }
}
impl Ord for ClientDiceRoll {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.value.cmp(&other.value)
    }
}

#[derive(Deserialize, Serialize, Debug)]
pub enum Commands {
    StartRound,
    EndRound,
}
#[derive(Deserialize, Serialize, Debug)]
pub struct ServerMessage {
    pub command: Commands,
    pub lamport_counter: u64,
}
#[derive(Deserialize, Serialize, Debug)]
pub struct ClientJoin {
    pub name: String,
}
#[derive(Deserialize, Serialize, Debug)]
pub struct ClientJoinResponse {
    pub uuid: String,
}

#[derive(Debug)]
pub struct RoundStats {
    pub number_rolls: u64,
    pub max_roll: ClientDiceRoll,
}
