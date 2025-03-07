import React from "react";
import { Trophy } from "lucide-react";
import { Player } from "../types/game";

interface WinnerModalProps {
  winner: Player;
  onReset: () => void;
}

const WinnerModal: React.FC<WinnerModalProps> = ({ winner, onReset }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-10">
      <div className="bg-gray-800 p-8 rounded-lg text-center">
        <Trophy className="w-16 h-16 mx-auto mb-4 text-yellow-400" />
        <h2 className="text-2xl font-bold text-white mb-4">
          {winner === "red" ? "Red" : "Blue"} Player Wins!
        </h2>
        <button
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          onClick={onReset}
        >
          Play Again
        </button>
      </div>
    </div>
  );
};

export default WinnerModal;
