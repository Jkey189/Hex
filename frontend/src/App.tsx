import { useState, useEffect } from "react";
import { Share2, Copy } from "lucide-react";
import HexBoard from "./components/HexBoard";
import { GameHeader } from "./components/GameHeader";
import WinnerModal from "./components/WinnerModal";
import GameLobby from "./components/GameLobby";
import { gameService } from "./services/gameService";
import { socketService } from "./services/socketService";
import { GameState } from "./types/game";

function App() {
  // Game state
  const [gameId, setGameId] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [playerColor, setPlayerColor] = useState<"red" | "blue" | null>(null);
  const [showLobby, setShowLobby] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Handle game creation
  const handleGameCreated = (newGameId: string) => {
    setGameId(newGameId);
    setShowLobby(false);
    socketService.joinGame(newGameId);
  };

  // Handle joining a game
  const handleGameJoined = (joinGameId: string) => {
    setGameId(joinGameId);
    setShowLobby(false);
    socketService.joinGame(joinGameId);
  };

  // Handle cell click
  const handleCellClick = async (row: number, col: number) => {
    if (!gameId || !gameState || !playerColor) return;
    if (gameState.game_status !== "playing") return;
    if (gameState.current_player !== playerColor) return;
    if (gameState.board[row][col] !== null) return;

    try {
      await gameService.makeMove(gameId, {
        row,
        col,
        current_player: playerColor
      });
    } catch (err) {
      // Safely log error without potential Symbol issues
      console.error("Failed to make move:", err instanceof Error ? err.message : String(err));
      setError("Failed to make move. Please try again.");
    }
  };

  // Handle game reset
  const handleResetGame = async () => {
    if (!gameId) return;

    try {
      await gameService.resetGame(gameId);
    } catch (err) {
      // Safely log error without potential Symbol issues
      console.error("Failed to reset game:", err instanceof Error ? err.message : String(err));
      setError("Failed to reset game. Please try again.");
    }
  };

  // Copy game ID to clipboard
  const copyGameId = () => {
    if (!gameId) return;
    
    navigator.clipboard.writeText(gameId)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(err => {
        // Safely log error without potential Symbol issues
        console.error("Failed to copy game ID:", err instanceof Error ? err.message : String(err));
      });
  };

  // Set up socket listeners
  useEffect(() => {
    const socket = socketService.connect();

    const gameUpdateUnsubscribe = socketService.onGameUpdate((updatedGameState) => {
      setGameState(updatedGameState);
    });

    const timerUpdateUnsubscribe = socketService.onTimerUpdate((timerUpdate) => {
      if (gameState) {
        setGameState(prev => prev ? {
          ...prev,
          timers: timerUpdate.timers,
          current_player: timerUpdate.current_player
        } : null);
      }
    });

    const playerJoinedUnsubscribe = socketService.onPlayerJoined((event) => {
      setGameState(event.game_state);
      
      // If this is us joining, set our color
      if (socket && event.player_id === socket.id) {
        setPlayerColor(event.color);
      }
    });

    const errorUnsubscribe = socketService.onError((error) => {
      setError(error.message);
    });

    return () => {
      gameUpdateUnsubscribe();
      timerUpdateUnsubscribe();
      playerJoinedUnsubscribe();
      errorUnsubscribe();
      socketService.disconnect();
    };
  }, []);

  // If we"re in the lobby, show the lobby component
  if (showLobby) {
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
        <GameLobby 
          onGameCreated={handleGameCreated}
          onGameJoined={handleGameJoined}
        />
      </div>
    );
  }

  // If we"re waiting for game state, show loading
  if (!gameState) {
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
        <div className="text-white text-xl">Loading game...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
      {error && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded shadow-lg z-50">
          {error}
          <button 
            className="ml-2 text-white font-bold"
            onClick={() => setError(null)}
          >
            ×
          </button>
        </div>
      )}
      
      {/* Game ID display */}
      {gameId && (
        <div className="absolute top-4 left-4 bg-gray-800 text-white px-3 py-2 rounded-lg flex items-center space-x-2">
          <span className="text-sm">Game ID:</span>
          <code className="bg-gray-700 px-2 py-1 rounded text-xs">{gameId}</code>
          <button 
            className="text-gray-400 hover:text-white"
            onClick={copyGameId}
            title="Copy Game ID"
          >
            {copied ? <Share2 size={16} /> : <Copy size={16} />}
          </button>
        </div>
      )}
      
      {/* Player indicator */}
      {playerColor && (
        <div className="absolute top-4 right-4 bg-gray-800 text-white px-3 py-2 rounded-lg flex items-center">
          <span className="text-sm mr-2">You are:</span>
          <div className={`w-4 h-4 rounded-full ${playerColor === "red" ? "bg-red-500" : "bg-blue-500"}`}></div>
        </div>
      )}
      
      {/* Game header */}
      <GameHeader 
        currentPlayer={gameState.current_player}
        redTimer={gameState.timers.red}
        blueTimer={gameState.timers.blue}
      />
      
      {/* Game board */}
      <HexBoard 
        board={gameState.board}
        currentPlayer={gameState.current_player}
        gameStatus={gameState.game_status}
        onCellClick={handleCellClick}
      />
      
      {/* Winner modal */}
      {gameState.game_status === "won" && gameState.winner && (
        <WinnerModal 
          winner={gameState.winner}
          onReset={handleResetGame}
        />
      )}
    </div>
  );
}

export default App;
