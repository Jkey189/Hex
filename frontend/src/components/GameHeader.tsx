import React from "react";
import {Player} from "../types/game"

interface GameHeaderProps {
  currentPlayer: Player
  redTimer: number
  blueTimer: number
}

export const GameHeader: React.FC<GameHeaderProps> = ({currentPlayer, redTimer, blueTimer}) => {
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };
  return (
    <div className="w-full max-w-4xl flex justify-between items-center mb-8">
      {/* Red player */}
      <div className={`flex items-center ${currentPlayer === 'red' ? 'text-red-500' : 'text-red-700'}`}>
        <div className="bg-red-500 w-4 h-4 rounded-full mr-2"></div>
        <div className="font-bold">Player 1</div>
        <div className="ml-2 text-gray-300">{formatTime(redTimer)}</div>
      </div>
      
      {/* Game title */}
      <h1 className="text-3xl font-bold text-white">HEX</h1>
      
      {/* Blue player */}
      <div className={`flex items-center ${currentPlayer === 'blue' ? 'text-blue-400' : 'text-blue-700'}`}>
        <div className="ml-2 text-gray-300">{formatTime(blueTimer)}</div>
        <div className="font-bold ml-2">Player 2</div>
        <div className="bg-blue-500 w-4 h-4 rounded-full ml-2"></div>
      </div>
    </div>
  );
}
