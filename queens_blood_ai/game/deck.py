import random
from typing import List, Optional
from .card import Card

class Deck:
    def __init__(self, cards: List[Card]):
        if len(cards) != 15:
            # We'll allow different sizes for testing, but real QB is 15
            pass
        self.cards = list(cards)
        self.remaining = list(cards)
        self.discards = []

    def shuffle(self):
        random.shuffle(self.remaining)

    def draw(self) -> Optional[Card]:
        if not self.remaining:
            return None
        return self.remaining.pop(0)

    def add_to_bottom(self, card: Card):
        self.remaining.append(card)

    def __len__(self):
        return len(self.remaining)
