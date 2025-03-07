export type Player = "red" | "blue" | null;
export type BoardState = Player[][];
export type GameStatus = "playing" | "won";

export interface GameState {
  board: BoardState;
  current_player: Player;
  game_status: GameStatus;
  timers: {
    red: number;
    blue: number;
  };
  // game_id: string;
  players: {
    red: string | null;
    blue: string | null;
  };
  winner: Player | null;
}

export interface TimerUpdate {
  timers: {
    red: number;
    blue: number;
  };
  current_player: Player;
}

export interface MoveRequest {
  row: number;
  col: number;
  current_player: Player;
}

export interface PlayerJoinedEvent {
  player_id: string;
  color: "red" | "blue";
  game_state: GameState;
}

export interface PlayerLeftEvent {
  player_id: string;
}
