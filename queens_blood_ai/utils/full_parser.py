import re
import json

def parse_cards(text):
    # Regex to extract each card definition
    # () => new("Name", cost, power, ...
    pattern = r'\(\) => new\("(.*?)",\s*(-?\d+),\s*(\d+)(.*?)\)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    cards = []
    for idx, (name, cost, power, rest) in enumerate(matches):
        card = {
            "id": idx + 1,
            "name": name,
            "cost": int(cost),
            "power": int(power),
            "rank_positions": [],
            "ability_positions": [],
            "legendary": "legendary: true" in rest,
            "description": ""
        }
        
        # Extract description
        desc_match = re.search(r'description:\s*"(.*?)"', rest)
        if desc_match:
            card["description"] = desc_match.group(1)
            
        # Extract rank positions [new(x, y), ...]
        # This is usually the 4th argument, but we look for brackets
        pos_matches = re.findall(r'\[(.*?)\]', rest, re.DOTALL)
        if pos_matches:
            # Rank positions is usually the first bracketed list if not explicitly named
            # Ability positions is usually explicitly named
            if "abilityPositions:" in rest:
                ab_sect = re.search(r'abilityPositions:\s*\[(.*?)\]', rest, re.DOTALL).group(1)
                card["ability_positions"] = [[int(r), int(c)] for r, c in re.findall(r'new\((-?\d+),\s*(-?\d+)\)', ab_sect)]
                
                # If there's another bracketed list, it might be rank positions
                for sect in pos_matches:
                    if sect != ab_sect:
                        card["rank_positions"] = [[int(r), int(c)] for r, c in re.findall(r'new\((-?\d+),\s*(-?\d+)\)', sect)]
                        break
            else:
                # If no abilityPositions, the first bracketed list is ranks
                card["rank_positions"] = [[int(r), int(c)] for r, c in re.findall(r'new\((-?\d+),\s*(-?\d+)\)', pos_matches[0])]
                
        # Parse abilities (played, inPlay, destroyed, etc.)
        for ab_type in ["played", "inPlay", "destroyed", "cardDestroyed", "cardPlayed", "laneWon", "enhanced", "enfeebled", "power7"]:
            if f"{ab_type}:" in rest:
                # new(Effect.Enhance, CardRelation.Ally, 1, ...)
                ab_match = re.search(rf'{ab_type}:\s*new\(Effect\.(\w+),\s*CardRelation\.(\w+)(.*?)\)', rest)
                if ab_match:
                    effect = ab_match.group(1).upper()
                    relation = ab_match.group(2).upper()
                    value_str = ab_match.group(3)
                    
                    value = 0
                    value_type = "POWER"
                    
                    # Extract numeric value
                    val_num = re.search(r',\s*(-?\d+)', value_str)
                    if val_num:
                        value = int(val_num.group(1))
                    
                    # Extract ValueType
                    vtype_match = re.search(r'ValueType\.(\w+)', value_str)
                    if vtype_match:
                        value_type = vtype_match.group(1).upper()
                        
                    card[ab_type] = {
                        "effect": effect,
                        "target": relation,
                        "value": value,
                        "value_type": value_type
                    }
        
        cards.append(card)
    return cards

# Concatenate all chunks and parse
# (In a real scenario I'd read from file, here I'll just use a small sample 
# to show the script works and then I'll provide the full file)
