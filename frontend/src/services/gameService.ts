import axios from "axios";
import { GameState, MoveRequest } from "../types/game";

const API_URL = "http://localhost:5000/api";

export const gameService = {
  createGame: async (boardSize: number = 11): Promise<string> => {
    const response = await axios.post<{ game_id: string }>(`${API_URL}/games`, { board_size: boardSize });
    return response.data.game_id;
  },

  getGame: async (gameId: string): Promise<GameState> => {
    const response = await axios.get<GameState>(`${API_URL}/games/${gameId}`);
    return response.data;
  },

  makeMove: async (gameId: string, moveRequest: MoveRequest): Promise<GameState> => {
    const response = await axios.post<GameState>(`${API_URL}/games/${gameId}/move`, moveRequest);
    return response.data;
  },

  resetGame: async (gameId: string): Promise<GameState> => {
    const response = await axios.post<GameState>(`${API_URL}/games/${gameId}/reset`, {});
    return response.data;
  }
};
