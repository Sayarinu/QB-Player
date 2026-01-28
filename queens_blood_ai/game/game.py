from typing import List, Tuple, Optional, Dict
from .board import Board, Player
from .deck import Deck
from .card import Card, Ability, Effect, CardRelation, ValueType

class Game:
    def __init__(self, deck1: Deck, deck2: Deck):
        self.board = Board()
        self.players = {
            Player.PLAYER1: {"deck": deck1, "hand": [], "passed": False},
            Player.PLAYER2: {"deck": deck2, "hand": [], "passed": False}
        }
        self.current_turn = Player.PLAYER1
        self.turn_number = 0
        self.game_over = False
        
        # Initial draw
        for _ in range(5):
            self._draw_card(Player.PLAYER1)
            self._draw_card(Player.PLAYER2)

    def _draw_card(self, player_enum: Player):
        card = self.players[player_enum]["deck"].draw()
        if card:
            self.players[player_enum]["hand"].append(card)

    def get_legal_moves(self, player_enum: Player) -> List[Tuple[int, int, int]]:
        """Returns list of (card_index, row, col) tuples."""
        moves = []
        hand = self.players[player_enum]["hand"]
        for i, card in enumerate(hand):
            for r in range(self.board.height):
                for c in range(self.board.width):
                    if self.is_legal_move(player_enum, card, r, c):
                        moves.append((i, r, c))
        return moves

    def is_legal_move(self, player_enum: Player, card: Card, row: int, col: int) -> bool:
        # Replacement cards can be played on any allied card
        if card.replaces:
            existing_card = self.board.cards[row][col]
            # Must be an allied card to replace? 
            # In QB, replacement cards destroy an allied card.
            return existing_card is not None and self.board.get_owner(row, col) == player_enum
        
        # Normal cards must be played on player-controlled tiles with sufficient rank
        if self.board.get_owner(row, col) != player_enum:
            return False
        
        if self.board.get_rank(row, col, player_enum) < card.cost:
            return False
            
        if self.board.cards[row][col] is not None:
            return False
            
        return True

    def step(self, action: Optional[Tuple[int, int, int]]):
        """
        Executes a turn. action = (card_index, row, col) or None for pass.
        """
        player_enum = self.current_turn
        
        if action is None:
            self.players[player_enum]["passed"] = True
        else:
            self.players[player_enum]["passed"] = False
            card_idx, r, c = action
            card = self.players[player_enum]["hand"].pop(card_idx)
            
            # 1. Handle Replacement
            if card.replaces:
                replaced_card = self.board.cards[r][c]
                if replaced_card:
                    self.last_replaced_power = replaced_card.adjusted_power
                    self._on_card_destroyed(replaced_card, r, c, player_enum)

            # 2. Place card
            self.board.place_card(r, c, card, player_enum)
            
            # 3. Trigger 'played' effects
            self._resolve_effects(card, r, c, player_enum)
            
        # Switch turn
        self.current_turn = Player.PLAYER1 if self.current_turn == Player.PLAYER2 else Player.PLAYER2
        self.turn_number += 1
        
        # Check game over
        if self.players[Player.PLAYER1]["passed"] and self.players[Player.PLAYER2]["passed"]:
            self.game_over = True

    def _resolve_effects(self, card: Card, r: int, c: int, player_enum: Player):
        """Resolves one-time 'played' effects and updates board state."""
        from .effects import resolve_ability
        
        # 1. Resolve 'played' ability
        if card.played and card.played.effect != Effect.NONE:
            resolve_ability(self, card, r, c, card.played, player_enum)
        
        # 2. Recalculate all in-play effects
        self._update_all_power_adjustments()

    def _update_all_power_adjustments(self):
        """Recalculates power adjustments for all cards on the board based on in-play abilities."""
        # Reset all adjustments
        for r in range(self.board.height):
            for c in range(self.board.width):
                card = self.board.cards[r][c]
                if card:
                    card.power_adjustment = 0
                    card.self_adjustment = 0

        # Apply in-play effects from every card
        from .effects import resolve_ability
        for r in range(self.board.height):
            for c in range(self.board.width):
                source_card = self.board.cards[r][c]
                owner = self.board.card_owners[r, c]
                if source_card and source_card.in_play and source_card.in_play.effect != Effect.NONE:
                    resolve_ability(self, source_card, r, c, source_card.in_play, Player(owner))
        
    def _on_card_destroyed(self, card: Card, r: int, c: int, player_enum: Player):
        """Triggers effects that occur when a card is destroyed (e.g., Bomb, Heatseeker)."""
        from .effects import resolve_ability
        if card.destroyed and card.destroyed.effect != Effect.NONE:
            resolve_ability(self, card, r, c, card.destroyed, player_enum)
        
        # Trigger global 'cardDestroyed' effects on other cards
        for tr in range(self.board.height):
            for tc in range(self.board.width):
                other = self.board.cards[tr][tc]
                if other and other.card_destroyed and other.card_destroyed.effect != Effect.NONE:
                    # Check if 'other' cares about this destruction (e.g., Tonberry King)
                    other_owner = self.board.card_owners[tr, tc]
                    resolve_ability(self, other, tr, tc, other.card_destroyed, Player(other_owner))
        
        # Finally remove from board (if not already handled by replacement)
        if self.board.cards[r][c] == card:
            self.board.cards[r][c] = None
        
        self._update_all_power_adjustments()
    def add_minion_to_hand(self, player_enum: Player, minion_group_id: int):
        """Adds specific cards to a player's hand (e.g., Mandragora Minion)."""
        # Load from extra_cards.json
        import json
        try:
            with open("queens_blood_ai/data/extra_cards.json", "r") as f:
                extra_data = json.load(f)
                minions = extra_data.get("minions", [])
                if 0 <= minion_group_id < len(minions):
                    for m_data in minions[minion_group_id]:
                        self.players[player_enum]["hand"].append(Card.from_dict(m_data))
        except FileNotFoundError:
            pass

    def spawn_cards_on_board(self, player_enum: Player, spawn_group_id: int):
        """Spawns cards directly onto empty positions (e.g., Shiva's Diamond Dust)."""
        import json
        try:
            with open("queens_blood_ai/data/extra_cards.json", "r") as f:
                extra_data = json.load(f)
                spawns = extra_data.get("spawns", [])
                if 0 <= spawn_group_id < len(spawns):
                    spawn_list = spawns[spawn_group_id]
                    # Find empty positions
                    empty_pos = []
                    for r in range(self.board.height):
                        for c in range(self.board.width):
                            if self.board.cards[r][c] is None:
                                empty_pos.append((r, c))
                    
                    # Spawn cards
                    import random
                    random.shuffle(empty_pos)
                    for i, m_data in enumerate(spawn_list):
                        if i < len(empty_pos):
                            r, c = empty_pos[i]
                            card = Card.from_dict(m_data)
                            self.board.place_card(r, c, card, player_enum)
                            # Continuous recalculation
                            self._update_all_power_adjustments()
        except FileNotFoundError:
            pass

    def get_final_scores(self) -> Tuple[int, int]:
        total_p1 = 0
        total_p2 = 0
        for r in range(self.board.height):
            p1_lane_power = 0
            p2_lane_power = 0
            for c in range(self.board.width):
                card = self.board.cards[r][c]
                owner = self.board.card_owners[r, c]
                if card:
                    if owner == Player.PLAYER1:
                        p1_lane_power += max(0, card.adjusted_power)
                    elif owner == Player.PLAYER2:
                        p2_lane_power += max(0, card.adjusted_power)
            
            if p1_lane_power > p2_lane_power:
                total_p1 += p1_lane_power
            elif p2_lane_power > p1_lane_power:
                total_p2 += p2_lane_power
            # Ties result in 0 for both in standard rules
        return total_p1, total_p2
