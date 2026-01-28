from typing import List, Tuple, Optional, Dict
from enum import IntEnum
import numpy as np

class Player(IntEnum):
    NEUTRAL = 0
    PLAYER1 = 1
    PLAYER2 = 2

class Board:
    """
    Represents the 3x5 Queen's Blood board.
    Grid coordinates: (row, col) where row is 0-2 and col is 0-4.
    """
    def __init__(self):
        self.width = 5
        self.height = 3
        # Ranks for each player on each tile
        self.ranks = {
            Player.PLAYER1: np.zeros((self.height, self.width), dtype=int),
            Player.PLAYER2: np.zeros((self.height, self.width), dtype=int)
        }
        # Ownership of each tile
        self.owner = np.full((self.height, self.width), Player.NEUTRAL, dtype=int)
        # Cards on each tile
        self.cards: List[List[Optional[Any]]] = [[None for _ in range(self.width)] for _ in range(self.height)]
        # Owner of the card on each tile
        self.card_owners = np.full((self.height, self.width), Player.NEUTRAL, dtype=int)
        
        # Initial setup: Player 1 controls left column, Player 2 controls right column (mirrored in real game, but we assume P1 is left, P2 is right)
        # In QB, P1 starts with Rank 1 in col 0, P2 starts with Rank 1 in col 4
        for r in range(self.height):
            self.set_tile(r, 0, Player.PLAYER1, 1)
            self.set_tile(r, 4, Player.PLAYER2, 1)

    def set_tile(self, row: int, col: int, player: Player, rank: int):
        if 0 <= row < self.height and 0 <= col < self.width:
            self.owner[row, col] = player
            self.ranks[player][row, col] = min(3, rank)
            # If a player captures a tile, the other player's rank there becomes 0
            other_player = Player.PLAYER1 if player == Player.PLAYER2 else Player.PLAYER2
            self.ranks[other_player][row, col] = 0

    def get_rank(self, row: int, col: int, player: Player) -> int:
        return self.ranks[player][row, col]

    def get_owner(self, row: int, col: int) -> Player:
        return Player(self.owner[row, col])

    def place_card(self, row: int, col: int, card: Any, player: Player):
        """Places a card and updates board ranks based on card patterns."""
        self.cards[row][col] = card
        self.card_owners[row, col] = player
        # Replacement cards keep the owner but change the card
        # Normal cards must be placed on player-owned tiles
        
        # Apply rank patterns
        for dr, dc in card.rank_positions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.height and 0 <= nc < self.width:
                self.update_rank(nr, nc, player, card.rank_boost)

    def update_rank(self, row: int, col: int, player: Player, amount: int):
        current_owner = self.get_owner(row, col)
        if current_owner == Player.NEUTRAL:
            self.set_tile(row, col, player, amount)
        elif current_owner == player:
            self.ranks[player][row, col] = min(3, self.ranks[player][row, col] + amount)
        else:
            # Capturing enemy tile if our rank increase makes it higher?
            # Actually QB rules: if you activate an enemy tile, it lowers their rank by 1.
            # If it hits 0, it becomes neutral? No, it becomes YOURS with Rank 1.
            # "If an opponent's space is highlighted, its rank is reduced by 1. 
            # If the rank drops to 0 or lower, you take control of it as a rank 1 space."
            enemy_rank = self.ranks[current_owner][row, col]
            if enemy_rank > amount:
                self.ranks[current_owner][row, col] -= amount
            else:
                self.set_tile(row, col, player, 1)

    def get_lane_scores(self) -> List[Tuple[int, int]]:
        """Returns (score_p1, score_p2) for each of the 3 lanes."""
        scores = []
        for r in range(self.height):
            p1_score = 0
            p2_score = 0
            for c in range(self.width):
                card = self.cards[r][c]
                if card:
                    # In a real game, card ownership is tracked separately from tile ownership
                    # but usually card on tile = tile owner's card.
                    # We'll assume the card object has an owner attribute or we track it.
                    # For now, let's assume we store (card, owner) in the board.
                    pass
            scores.append((p1_score, p2_score))
        return scores
