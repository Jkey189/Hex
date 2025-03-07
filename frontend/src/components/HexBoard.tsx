import React from "react";
import { BoardState, Player } from "../types/game";

interface HexBoardProps {
  board: BoardState;
  currentPlayer: Player;
  gameStatus: "playing" | "won";
  onCellClick: (row: number, col: number) => void;
}

const HexBoard: React.FC<HexBoardProps> = ({ board, gameStatus, onCellClick }) => {
  return (
    <div className="relative">
      {/* Red borders (top and bottom) */}
      <div className="absolute top-0 left-0 w-full h-2 bg-red-600 transform -translate-y-2 z-10"></div>
      <div className="absolute bottom-0 left-0 w-full h-2 bg-red-600 transform translate-y-2 z-10"></div>
      
      {/* Blue borders (left and right) */}
      <div className="absolute top-0 left-0 h-full w-2 bg-blue-500 transform -translate-x-2 z-10"></div>
      <div className="absolute top-0 right-0 h-full w-2 bg-blue-500 transform translate-x-2 z-10"></div>
      
      {/* Hex board container */}
      <div className="relative">
        {board.map((row, rowIndex) => (
          <div 
            key={`row-${rowIndex}`} 
            className="flex" 
            style={{ 
              marginLeft: `${rowIndex * 20}px`,
              marginTop: rowIndex === 0 ? "0" : "-10px"
            }}
          >
            {row.map((cell, colIndex) => (
              <div 
                key={`cell-${rowIndex}-${colIndex}`}
                className={`
                  w-10 h-10 m-0.5
                  flex items-center justify-center
                  cursor-pointer transition-all duration-200
                  ${cell === "red" ? "bg-red-500" : cell === "blue" ? "bg-blue-500" : "bg-gray-700 hover:bg-gray-600"}
                  ${cell === null && gameStatus === "playing" ? "hover:bg-gray-600" : ""}
                  border border-gray-800
                `}
                style={{
                  clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
                }}
                onClick={() => onCellClick(rowIndex, colIndex)}
              >
                {cell && (
                  <div className="w-2 h-2 bg-white opacity-50 rounded-full"></div>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default HexBoard;
