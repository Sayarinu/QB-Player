import re
import json

def parse_cs_cards(content):
    # Regex to match: () => new("Name", cost, power, [ranks], [abilities], ...
    # This is a bit complex due to optional arguments.
    # We'll use a more robust regex or a simple parser.
    
    cards = []
    
    # Split by "() => new(" to get individual card definitions
    chunks = content.split("() => new(")[1:]
    
    for i, chunk in enumerate(chunks):
        # Extract name: "Security Officer",
        name_match = re.search(r'^"([^"]+)"', chunk)
        if not name_match: continue
        name = name_match.group(1)
        
        # Pull everything inside the constructor call
        # We need to find the matching closing paren for the new(...)
        # but since they are all on separate lines or followed by "),", we can simplify.
        
        # Let's extract arguments by splitting by commas, but respecting brackets []
        args_str = ""
        paren_count = 1
        for char in chunk[len(name)+2:]:
            if char == '(': paren_count += 1
            elif char == ')': paren_count -= 1
            if paren_count == 0: break
            args_str += char
            
        # Basic parsing of args
        # cost, power, rankPositions, abilityPositions, inPlay, played, destroyed, cardDestroyed, cardPlayed, laneWon, enhanced, enfeebled, power7, rankBoost, legendary, description
        
        # This is getting complicated. I'll just hardcode the most important ones 
        # or use a very targeted regex for the fields.
        
        card = {
            "id": i + 1,
            "name": name,
            "cost": 0,
            "power": 0,
            "rank_positions": [],
            "ability_positions": [],
            "ability": {},
            "legendary": False,
            "description": ""
        }
        
        # Simplified extraction
        try:
            # Stats
            stats = re.findall(r'(-?\d+),\s*(\d+)', args_str)
            if stats:
                card["cost"] = int(stats[0][0])
                card["power"] = int(stats[0][1])
            
            # Rank Positions: [new(-1, 0), new(0, -1)]
            ranks = re.search(r'\[(.*?)\]', args_str)
            if ranks:
                offsets = re.findall(r'new\((-?\d+),\s*(-?\d+)\)', ranks.group(1))
                card["rank_positions"] = [[int(r), int(c)] for r, c in offsets]
                
            # Ability Positions (if any)
            # Find the second [] or the one labeled abilityPositions
            if "abilityPositions:" in args_str:
                ab_pos = re.search(r'abilityPositions:\s*\[(.*?)\]', args_str)
                if ab_pos:
                    offsets = re.findall(r'new\((-?\d+),\s*(-?\d+)\)', ab_pos.group(1))
                    card["ability_positions"] = [[int(r), int(c)] for r, c in offsets]
            
            if "legendary: true" in args_str:
                card["legendary"] = True
                
            desc = re.search(r'description:\s*"([^"]+)"', args_str)
            if desc:
                card["description"] = desc.group(1)
        except:
            pass
            
        cards.append(card)
        
    return cards

# I'll paste the chunks here for the script to run if I were running it locally.
# But since I'm the assistant, I'll just manually construct the JSON for the first 20 cards 
# and then use a "full" database for the rest.
# Wait, the user wants ALL 145 cards.
# I'll create the JSON in chunks if needed.
