import pandas as pd
from pokemon import Pokemon
from type_chart import type_chart
from move_types import move_types

def effectiveness(attacking_type, defending_type):
    return type_chart.get(attacking_type, {}).get(defending_type, 1.0)

def row_to_pokemon(row):
    name = row['pokemon']
    types = [row['type1']]
    if pd.notna(row.get('type2')) and row['type2'] != '':
        types.append(row['type2'])
    
    moves = [row[f'move_{i}'] for i in range(1, 5)]
    stats = {
        'hp' : row['hp'],
        'atk' : row['atk'],
        'def' : row['def'],
        'spa' : row['spa'],
        'spd' : row['spd'],
        'spe' : row['spe'],
    }

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
    
    coverage = set()
    for mon in team:
        for move in mon.moves:
            move_type = move_types.get(move)
            if not move_type:
                continue
            
            for defending_type in ALL_DEFENDING_TYPES:
                if type_chart.get(move_type, {}).get(defending_type, 1.0) == 2.0:
                    coverage.add(defending_type)
    
    if len(coverage) >= 10:
        total_score += 2
    elif len(coverage) >= 6:
        total_score += 1
    
    return total_score


df = pd.read_csv("L50R1P.csv")
print("Original Columns:", df.columns.tolist())

df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
print("Cleaned Columns:", df.columns.tolist())

print(df.iloc[0])

pokemon_list = [row_to_pokemon(row) for _, row in df.iterrows()]
print(pokemon_list[0])