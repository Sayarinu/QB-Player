from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple, Dict, Optional, Any

class Effect(Enum):
    NONE = auto()
    ENFEEBLE = auto()
    ENHANCE = auto()
    DESTROY = auto()
    ADD_CARD = auto()
    ADD_SCORE = auto()
    PARTY_ANIMAL = auto()
    SPAWN_CARDS = auto()

class CardRelation(Enum):
    NONE = auto()
    ALLY = auto()
    ENEMY = auto()
    BOTH = auto()
    SELF = auto()

class ValueType(Enum):
    POWER = auto()
    REPLACED_POWER = auto()
    ENFEEBLED = auto()
    ENHANCED = auto()

@dataclass
class Ability:
    effect: Effect
    target_type: CardRelation
    value: int = 0
    value_type: ValueType = ValueType.POWER
    target_trigger: CardRelation = CardRelation.SELF

    @staticmethod
    def none():
        return Ability(Effect.NONE, CardRelation.NONE)

@dataclass
class Card:
    name: str
    cost: int
    power: int
    rank_positions: List[Tuple[int, int]] = field(default_factory=list)
    ability_positions: List[Tuple[int, int]] = field(default_factory=list)
    in_play: Ability = field(default_factory=Ability.none)
    played: Ability = field(default_factory=Ability.none)
    destroyed: Ability = field(default_factory=Ability.none)
    card_destroyed: Ability = field(default_factory=Ability.none)
    card_played: Ability = field(default_factory=Ability.none)
    lane_won: Ability = field(default_factory=Ability.none)
    enhanced: Ability = field(default_factory=Ability.none)
    enfeebled: Ability = field(default_factory=Ability.none)
    power7: Ability = field(default_factory=Ability.none)
    rank_boost: int = 1
    legendary: bool = False
    description: str = "This card has no abilities."
    replaces: bool = False

    def __post_init__(self):
        self.replaces = (self.cost == -1)
        self.base_power = self.power
        self.power_adjustment = 0
        self.self_adjustment = 0
        self.has_been_enfeebled = False
        self.has_been_enhanced = False
        self.has_hit_power7 = False

    @property
    def adjusted_power(self) -> int:
        return self.power + self.power_adjustment + self.self_adjustment

    def to_dict(self) -> Dict[str, Any]:
        """Convert card to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "cost": self.cost,
            "power": self.power,
            "rank_positions": self.rank_positions,
            "ability_positions": self.ability_positions,
            "abilities": {
                "in_play": self._ability_to_dict(self.in_play),
                "played": self._ability_to_dict(self.played),
                "destroyed": self._ability_to_dict(self.destroyed),
                "card_destroyed": self._ability_to_dict(self.card_destroyed),
                "card_played": self._ability_to_dict(self.card_played),
                "lane_won": self._ability_to_dict(self.lane_won),
                "enhanced": self._ability_to_dict(self.enhanced),
                "enfeebled": self._ability_to_dict(self.enfeebled),
                "power7": self._ability_to_dict(self.power7)
            },
            "rank_boost": self.rank_boost,
            "legendary": self.legendary,
            "description": self.description
        }

    def _ability_to_dict(self, ability: Ability) -> Optional[Dict[str, Any]]:
        if ability.effect == Effect.NONE:
            return None
        return {
            "effect": ability.effect.name,
            "target_type": ability.target_type.name,
            "value": ability.value,
            "value_type": ability.value_type.name,
            "target_trigger": ability.target_trigger.name
        }
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Card':
        """Load card from flat dictionary format."""
        # Map flat keys to Ability objects
        abilities = {}
        for key in ["in_play", "inPlay", "played", "destroyed", "cardDestroyed", "card_destroyed", "cardPlayed", "card_played", "lane_won", "laneWon", "enhanced", "enfeebled", "power7"]:
            if key in data and data[key]:
                ab_data = data[key]
                if isinstance(ab_data, dict):
                    abilities[key.lower().replace("play", "_play").replace("won", "_won").replace("destroyed", "_destroyed")] = Ability(
                        effect=Effect[ab_data.get("effect", "NONE").upper()],
                        target_type=CardRelation[ab_data.get("target", "SELF").upper().replace("TARGET_TYPE", "")],
                        value=ab_data.get("value", 0),
                        value_type=ValueType[ab_data.get("value_type", "POWER").upper()],
                        target_trigger=CardRelation[ab_data.get("trigger", "SELF").upper()]
                    )
        
        return Card(
            name=data["name"],
            cost=data["cost"],
            power=data["power"],
            rank_positions=[tuple(p) for p in data.get("rank_positions", [])],
            ability_positions=[tuple(p) for p in data.get("ability_positions", [])],
            in_play=abilities.get("in_play", Ability.none()),
            played=abilities.get("played", Ability.none()),
            destroyed=abilities.get("destroyed", Ability.none()),
            card_destroyed=abilities.get("card_destroyed", Ability.none()),
            card_played=abilities.get("card_played", Ability.none()),
            lane_won=abilities.get("lane_won", Ability.none()),
            enhanced=abilities.get("enhanced", Ability.none()),
            enfeebled=abilities.get("enfeebled", Ability.none()),
            power7=abilities.get("power7", Ability.none()),
            rank_boost=data.get("rank_boost", 1),
            legendary=data.get("legendary", False),
            description=data.get("description", "No description.")
        )
