from .card import Ability, Effect, CardRelation, ValueType, Card
from .board import Player, Board
from typing import List, Tuple, Any

def resolve_ability(game: Any, source_card: Card, r: int, c: int, ability: Ability, player: Player):
    if ability.effect == Effect.NONE:
        return

    # Determine target tiles based on source position and ability pattern
    target_tiles = []
    if ability.target_type == CardRelation.SELF:
        target_tiles = [(r, c)]
    else:
        for dr, dc in source_card.ability_positions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < game.board.height and 0 <= nc < game.board.width:
                target_tiles.append((nr, nc))

    for tr, tc in target_tiles:
        target_card = game.board.cards[tr][tc]
        
        # Check relation
        if ability.target_type == CardRelation.ALLY:
            if game.board.get_owner(tr, tc) != player: continue
        elif ability.target_type == CardRelation.ENEMY:
            owner = game.board.get_owner(tr, tc)
            if owner == Player.NEUTRAL or owner == player: continue
        
        # Apply effect
        if ability.effect == Effect.ENHANCE:
            if target_card:
                amount = calculate_value(game, ability, source_card, player)
                if ability.target_type == CardRelation.SELF:
                    source_card.self_adjustment += amount
                else:
                    target_card.power_adjustment += amount
        elif ability.effect == Effect.ENFEEBLE:
            if target_card:
                amount = calculate_value(game, ability, source_card, player)
                if ability.target_type == CardRelation.SELF:
                    source_card.self_adjustment -= amount
                else:
                    target_card.power_adjustment -= amount
        elif ability.effect == Effect.DESTROY:
            if target_card:
                game._on_card_destroyed(target_card, tr, tc, Player(game.board.card_owners[tr, tc]))
        elif ability.effect == Effect.ADD_CARD:
            # Add specific card to hand from card adds database
            if hasattr(game, "add_minion_to_hand"):
                game.add_minion_to_hand(player, ability.value)
        elif ability.effect == Effect.SPAWN_CARDS:
            # Spawn cards on empty tiles
            if hasattr(game, "spawn_cards_on_board"):
                game.spawn_cards_on_board(player, ability.value)
        elif ability.effect == Effect.PARTY_ANIMAL:
            # Special end game effect: winner takes all lane scores
            game.party_animal_active = True

def calculate_value(game: Any, ability: Ability, source_card: Card, player: Player) -> int:
    if ability.value_type == ValueType.POWER:
        return ability.value
    elif ability.value_type == ValueType.REPLACED_POWER:
        # This will be set by the REPLACE logic in Game.step
        return getattr(game, 'last_replaced_power', 0)
    elif ability.value_type in [ValueType.ENHANCED, ValueType.ENFEEBLED]:
        # Count cards matching the criteria
        count = 0
        target_relation = ability.target_trigger # e.g., ALLY, ENEMY, BOTH
        
        for r in range(game.board.height):
            for c in range(game.board.width):
                card = game.board.cards[r][c]
                owner = game.board.card_owners[r, c]
                if not card: continue
                if card == source_card: continue # Don't count self
                
                # Check relation
                is_correct_owner = False
                if target_relation == CardRelation.ALLY:
                    is_correct_owner = (owner == player)
                elif target_relation == CardRelation.ENEMY:
                    is_correct_owner = (owner != player and owner != Player.NEUTRAL)
                elif target_relation == CardRelation.BOTH:
                    is_correct_owner = (owner != Player.NEUTRAL)
                
                if not is_correct_owner: continue
                
                # Check condition
                if ability.value_type == ValueType.ENHANCED and card.power_adjustment > 0:
                    count += 1
                elif ability.value_type == ValueType.ENFEEBLED and card.power_adjustment < 0:
                    count += 1
                    
        return count * ability.value
    return 0
