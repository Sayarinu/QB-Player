import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
import json
import os
from typing import List, Tuple, Dict, Optional, Any
from ..game.game import Game, Player
from ..game.deck import Deck
from ..game.card import Card

class QueensBloodEnv(gym.Env):
    def __init__(self, card_db: List[Card]):
        super().__init__()
        self.card_db = card_db
        # Action space: (card_in_hand_index [0-9], row [0-2], col [0-4]) + 1 for pass
        # Total = 10 * 3 * 5 + 1 = 151
        self.action_space = spaces.Discrete(151)
        
        # Observation space:
        # 3x5 grid with several layers:
        # 0: P1 Ranks
        # 1: P2 Ranks
        # 2: Card ID (normalized)
        # 3: Card Power
        # 4: Ownership (1 for P1, -1 for P2)
        # + Hand cards (10 slots)
        self.observation_space = spaces.Dict({
            "board": spaces.Box(low=-100, high=100, shape=(5, 3, 5), dtype=np.float32),
            "hand": spaces.Box(low=0, high=len(card_db), shape=(10,), dtype=np.int32),
            "turn": spaces.Discrete(2)
        })

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Determine decks to use
        decks_file = "queens_blood_ai/data/decks.json"
        archetypes = {}
        if os.path.exists(decks_file):
            with open(decks_file, "r") as f:
                archetypes = json.load(f)
        
        def get_random_deck():
            if archetypes and random.random() < 0.7: # 70% chance to use an archetype
                name = random.choice(list(archetypes.keys()))
                card_ids = archetypes[name]
                # Map IDs to card objects
                deck_cards = []
                for cid in card_ids:
                    # Find card with ID
                    for card in self.card_db:
                        if getattr(card, 'id', -1) == cid:
                            deck_cards.append(card)
                            break
                # Fill up to 15 if missing
                if len(deck_cards) < 15:
                    deck_cards.extend(random.sample(self.card_db, 15 - len(deck_cards)))
                return Deck(deck_cards)
            else:
                return Deck(random.sample(self.card_db, 15))

        deck1 = get_random_deck()
        deck2 = get_random_deck()
        
        self.game = Game(deck1, deck2)
        return self._get_obs(), {}

    def step(self, action):
        current_player = self.game.current_turn
        
        if action == 150: # Pass
            self.game.step(None)
        else:
            card_idx = action // 15
            pos_idx = action % 15
            row = pos_idx // 5
            col = pos_idx % 5
            
            hand = self.game.players[current_player]["hand"]
            if card_idx < len(hand):
                card = hand[card_idx]
                if self.game.is_legal_move(current_player, card, row, col):
                    self.game.step((card_idx, row, col))
                else:
                    # Illegal move: count as pass for now but with a small penalty
                    self.game.step(None)
            else:
                self.game.step(None)

        terminated = self.game.game_over
        reward = 0
        if terminated:
            s1, s2 = self.game.get_final_scores()
            # Win/Loss reward
            if s1 > s2: reward = 1.0 if current_player == Player.PLAYER1 else -1.0
            elif s2 > s1: reward = 1.0 if current_player == Player.PLAYER2 else -1.0
            else: reward = 0.0
            
        return self._get_obs(), reward, terminated, False, {}

    def _get_obs(self):
        # Construct the observation arrays
        board_obs = np.zeros((5, 3, 5), dtype=np.float32)
        
        # Layer 0: P1 Ranks
        # Layer 1: P2 Ranks
        board_obs[0] = self.game.board.ranks[Player.PLAYER1] / 3.0
        board_obs[1] = self.game.board.ranks[Player.PLAYER2] / 3.0
        
        # Layer 2: Ownership (1 for P1, -1 for P2)
        for r in range(3):
            for c in range(5):
                owner = self.game.board.owner[r, c]
                if owner == Player.PLAYER1.value: board_obs[2, r, c] = 1.0
                elif owner == Player.PLAYER2.value: board_obs[2, r, c] = -1.0
        
        # Layer 3: Card Power
        # Layer 4: Card ID (normalized)
        for r in range(3):
            for c in range(5):
                card = self.game.board.cards[r][c]
                if card:
                    board_obs[3, r, c] = card.adjusted_power / 20.0 # Heuristic normalization
                    board_obs[4, r, c] = getattr(card, 'id', 0) / len(self.card_db)

        hand_obs = np.zeros(10, dtype=np.int32)
        hand = self.game.players[self.game.current_turn]["hand"]
        for i in range(min(len(hand), 10)):
            # Use card index in DB (offset by 1 to keep 0 for empty)
            card_name = hand[i].name
            for idx, c_ref in enumerate(self.card_db):
                if c_ref.name == card_name:
                    hand_obs[i] = idx + 1
                    break
            
        return {
            "board": board_obs,
            "hand": hand_obs,
            "turn": np.array([1 if self.game.current_turn == Player.PLAYER1 else 0], dtype=np.int32)
        }
