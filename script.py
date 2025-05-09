import pandas as pd
from pokemon import Pokemon
from type_chart import type_chart
from move_types_full import move_types

def effectiveness(attacking_type, defending_type):
    return type_chart.get(attacking_type, {}).get(defending_type, 1.0)

base_stats_df = pd.read_csv("basestats.csv")
base_stats_df.columns = [col.strip().lower().replace(" ", "_") for col in base_stats_df.columns]
base_stats_df.set_index("name", inplace=True)
def row_to_pokemon(row):
    name = row['species']
    types = row['type'].split() if pd.notna(row['type']) else []
    moves = [row[f'move_{i}'] for i in range(1, 5)]
    ev_map = {
        'hp': 'hp',
        'atk': 'attack',
        'def': 'defense',
        'spa': 'sp._atk',
        'spd': 'sp._def',
        'spe': 'speed',
    }
    
    try:
        base = base_stats_df.loc[name]
        stats = {
            'hp': base['hp'],
            'atk': base['attack'],
            'def': base['defense'],
            'spa': base['sp._atk'],
            'spd': base['sp._def'],
            'spe': base['speed'],
        }

        ev_string = str(row.get('ev_spread', '')).lower()
        ev_stats = [label for label in ev_map if label in ev_string]
        if ev_stats:
            ev_per_stat = 510 // len(ev_stats)
            for stat in ev_stats:
                stats[stat] += ev_per_stat // 4

    except KeyError:
        print(f"⚠️ Could not find base stats for: {name}")
        stats = {key: 100 for key in ['hp', 'atk', 'def', 'spa', 'spd', 'spe']}


    return Pokemon(name, types, moves, stats)

ALL_DEFENDING_TYPES = set(type_chart['Fire'].keys())

def score_team(team):
    total_score = 0

    for mon in team:
        stat_total = sum(mon.stats.values())
        #general base stat check
        if stat_total >= 500:
            total_score += 1
        
        #speed is generally favorable, since attacking first is crucial to some pokemon
        if mon.stats['spe'] > 90:
            total_score +=1
    
    all_types = set(t for mon in team for t in mon.types)
    if len(all_types) >= 5:
        total_score += 1
    
    all_moves = set(move for mon in team for move in mon.moves)
    if len(all_moves) >= 8:
        total_score += 1

    status_bonus = sum(score_move(mon, move, 1, 1.0) for mon in team for move in mon.moves)
    total_score += min(status_bonus // 3, 2)
    
    coverage = set()
    for mon in team:
        for move in mon.moves:
            move_data = move_types.get(move)
            if not move_data:
                continue
            move_type = move_data['type']
            
            for defending_type in ALL_DEFENDING_TYPES:
                if type_chart.get(move_type, {}).get(defending_type, 1.0) == 2.0:
                    coverage.add(defending_type)
    
    if len(coverage) >= 10:
        total_score += 2
    elif len(coverage) >= 6:
        total_score += 1
    
    return total_score

def score_move(pokemon, move_name, turn_count = 1, current_hp = 1.0):

    move_data = move_types.get(move_name, {})
    effect = move_data.get('effect', '')
    score = 0

    if effect in ['atk_up', 'spa_spd_up', 'atk_def_up', 'atk_spe_up']:
        if turn_count <= 2 and current_hp > 0.7:
            score += 3
        else:
            score -= 1
    
    elif effect == 'heal':
        if current_hp < 0.4:
            score += 3
        else:
            score -= 2
    
    elif effect in ['toxic', 'paralyze', 'sleep']:
        if turn_count <= 3:
            score += 2 if effect != 'sleep' else 3
    
    elif effect in ['confuse', 'infatuate']:
        score += 1
    
    elif effect in ['rain', 'sun']:
        if 'Water' in pokemon.types and effect == 'rain':
            score += 2
        elif 'Fire' in pokemon.types and effect == 'sun':
            score += 2
    
    elif effect == 'protect':
        score += 2

    elif effect == 'substitute':
        if current_hp > 0.5:
            score += 2

    return score

def choose_best_move(attacker, defender, turn_count=1, current_hp=1.0):
    best_score = float('-inf')
    best_move = None

    for move in attacker.moves:
        move_data = move_types.get(move, {})
        move_type = move_data.get('type', '')
        score = 0

        #checks to make sure it actually hits lol
        if any(effectiveness(move_type, def_type) == 0.0 for def_type in defender.types):
            print(f"Skipping {move} — no effect on at least one of {defender.name}'s types.")
            continue

        #STAB
        if move_data.get('type') in attacker.types:
            score += 2
        
        #effectiveness
        for def_type in defender.types:
            score += 3 if effectiveness(move_data.get('type', ''), def_type) == 2.0 else 0
        
        #status/setup moves
        score += score_move(attacker, move, turn_count, current_hp)
        
        print(f"Evaluating {move}: score={score}")

        if score > best_score:
            best_score = score
            best_move = move
        
    return best_move


if __name__ == "__main__":
    df = pd.read_csv("L50R1P.csv")
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    pokemon_list = [row_to_pokemon(row) for _, row in df.iterrows()]
    print(pokemon_list[0])
    print(pokemon_list[1])

    ben_mon = pokemon_list[0]
    enemy_mon = pokemon_list[1]
    print("Ben should use:", choose_best_move(ben_mon, enemy_mon))
