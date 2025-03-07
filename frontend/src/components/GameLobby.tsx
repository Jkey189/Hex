import React, { useState } from "react";
import { gameService } from "../services/gameService";

interface GameLobbyProps {
  onGameCreated: (gameId: string) => void;
  onGameJoined: (gameId: string) => void;
}

const GameLobby: React.FC<GameLobbyProps> = ({ onGameCreated, onGameJoined }) => {
  const [gameId, setGameId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateGame = async () => {
    try {
      setLoading(true);
      setError(null);
      const newGameId = await gameService.createGame();
      onGameCreated(newGameId);
    } catch (err) {
      setError("Failed to create game. Please try again.");
      // Avoid logging the full error object which might contain non-clonable symbols
      console.error("Error creating game:", err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleJoinGame = () => {
    if (!gameId.trim()) {
      setError("Please enter a game ID");
      return;
    }
    
    onGameJoined(gameId.trim());
  };

  return (
    <div className="bg-gray-800 p-8 rounded-lg shadow-lg max-w-md w-full">
      <h1 className="text-3xl font-bold text-white text-center mb-8">HEX Game</h1>
      
      {error && (
        <div className="bg-red-500 text-white p-3 rounded mb-4 text-sm">
          {error}
        </div>
      )}
      
      <div className="space-y-6">
        <div>
          <button
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded transition-colors"
            onClick={handleCreateGame}
            disabled={loading}
          >
            {loading ? "Creating..." : "Create New Game"}
          </button>
        </div>
        
        <div className="text-center text-gray-400">- OR -</div>
        
        <div className="space-y-3">
          <input
            type="text"
            placeholder="Enter Game ID"
            className="w-full bg-gray-700 text-white px-4 py-3 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={gameId}
            onChange={(e) => setGameId(e.target.value)}
          />
          
          <button
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded transition-colors"
            onClick={handleJoinGame}
            disabled={loading}
          >
            Join Game
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameLobby;
