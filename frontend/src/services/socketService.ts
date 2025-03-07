import { io, Socket } from "socket.io-client";
import { GameState, TimerUpdate, PlayerJoinedEvent, PlayerLeftEvent } from "../types/game";

const SOCKET_URL = "http://localhost:5000";

class SocketService {
  private socket: Socket | null = null;
  private gameId: string | null = null;

  connect() {
    this.socket = io(SOCKET_URL);
    
    this.socket.on("connect", () => {
      console.log("Connected to socket server");
    });
    
    this.socket.on("disconnect", () => {
      console.log("Disconnected from socket server");
    });
    
    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  getGameId(): string | null {
    return this.gameId;
  }

  joinGame(gameId: string, color?: "red" | "blue") {
    if (!this.socket) {
      this.connect();
    }
    
    this.gameId = gameId;
    this.socket?.emit("join_game", { game_id: gameId, color });
  }

  onGameUpdate(callback: (gameState: GameState) => void) {
    this.socket?.on("game_update", callback);
    return () => {
      this.socket?.off("game_update", callback);
    };
  }

  onTimerUpdate(callback: (timerUpdate: TimerUpdate) => void) {
    this.socket?.on("timer_update", callback);
    return () => {
      this.socket?.off("timer_update", callback);
    };
  }

  onPlayerJoined(callback: (event: PlayerJoinedEvent) => void) {
    this.socket?.on("player_joined", callback);
    return () => {
      this.socket?.off("player_joined", callback);
    };
  }

  onPlayerLeft(callback: (event: PlayerLeftEvent) => void) {
    this.socket?.on("player_left", callback);
    return () => {
      this.socket?.off("player_left", callback);
    };
  }

  onError(callback: (error: { message: string }) => void) {
    this.socket?.on("error", callback);
    return () => {
      this.socket?.off("error", callback);
    };
  }
}

export const socketService = new SocketService();
