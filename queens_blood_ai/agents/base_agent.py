from abc import ABC, abstractmethod
import random
from typing import List, Tuple, Optional

class BaseAgent(ABC):
    def __init__(self, player_id: int):
        self.player_id = player_id

    @abstractmethod
    def select_action(self, state: dict, legal_moves: list) -> Optional[Tuple[int, int, int]]:
        """Returns (card_idx, row, col) or None for pass."""
        pass

class RandomAgent(BaseAgent):
    def select_action(self, state: dict, legal_moves: list) -> Optional[Tuple[int, int, int]]:
        if not legal_moves:
            return None
        return random.choice(legal_moves)

class GreedyAgent(BaseAgent):
    def select_action(self, state: dict, legal_moves: list) -> Optional[Tuple[int, int, int]]:
        if not legal_moves:
            return None
        
        # Heuristic: Pick the move that places the highest power card
        # Or better: Pick move that maximizes current lane score
        best_move = random.choice(legal_moves)
        best_power = -1
        
        hand = state.get("hand_objs", [])
        for move in legal_moves:
            card_idx, r, c = move
            if card_idx < len(hand):
                if hand[card_idx].power > best_power:
                    best_power = hand[card_idx].power
                    best_move = move
                    
        return best_move
