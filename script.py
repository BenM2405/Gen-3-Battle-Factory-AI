import pandas as pd
from pokemon import Pokemon
from type_chart import type_chart
from move_types_full import move_types
import random

def effectiveness(attacking_type, defending_type):
    return type_chart.get(attacking_type, {}).get(defending_type, 1.0)

base_stats_df = pd.read_csv("basestats.csv")
base_stats_df.columns = [col.strip().lower().replace(" ", "_") for col in base_stats_df.columns]
base_stats_df.set_index("name", inplace=True)

#turns our silly little pokemon into data
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
        print(f"Could not find base stats for: {name}")
        stats = {key: 100 for key in ['hp', 'atk', 'def', 'spa', 'spd', 'spe']}


    return Pokemon(name, types, moves, stats)

ALL_DEFENDING_TYPES = set(type_chart['Fire'].keys())

#chooses a team based off stats
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

#checks move uses
def score_move(pokemon, move_name, turn_count=1, current_hp=1.0, defender=None, status_effects=None):
    move_data = move_types.get(move_name, {})
    effect = move_data.get('effect', '')
    power = move_data.get('power', 0)
    category = move_data.get('category', '')

    effect_key = 'infatuated' if effect == 'infatuate' else 'confused'

    score = 0

    # desperate play
    if current_hp < 0.3 and effect in ['infatuate', 'confuse']:
        if defender and not status_effects[defender.name][effect_key]:
            score += 7
        else:
            score -= 5

    # setup moves
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

    elif effect == 'infatuate':
        if defender and not status_effects[defender.name][effect_key]:
            score += 2
        else:
            score -= 5
    elif effect == 'confuse':
        if defender and not status_effects[defender.name][effect_key]:
            score += 2
        else:
            score -= 5


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


#looks at what the move would do
def choose_best_move(attacker, defender, turn_count=1, current_hp=1.0, status_effects=None):
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
        hp_ratio = current_hp
        score += score_move(attacker, move, turn_count, hp_ratio, defender, status_effects)

        print(f"Evaluating {move}: score={score}")

        if score > best_score:
            best_score = score
            best_move = move
        
    return best_move


#Battle Test
def run_battle(p1, p2):
    print(f"Battle Start: {p1.name} vs. {p2.name}!\n")

    hp = {p1.name: 100, p2.name: 100}
    MAX_TURNS = 50
    turn = 1

    status_effects = {
        p1.name : {'infatuated': False, 
                   'confused': False, 
                   'turns_volatile': 0,
                   'paralyzed': False,
                   'asleep': 0,
                   'burned': False,
                   'poisoned': False,
                   'toxic_counter': 0,
                   },
        p2.name : {'infatuated': False, 
                   'confused': False, 
                   'turns_volatile': 0,
                   'paralyzed': False,
                   'asleep': 0,
                   'burned': False,
                   'poisoned': False,
                   'toxic_counter': 0,
                   },
    }

    #speed check
    while hp[p1.name] > 0 and hp[p2.name] > 0 and turn <= MAX_TURNS:
        print(f"Turn {turn}")

        if p1.stats['spe'] > p2.stats['spe']:
            first, second = p1, p2
        else:
            first, second = p2, p1

        #each AI chooses a move
        first_move = choose_best_move(first, second, turn, hp[first.name] / 100, status_effects)
        second_move = choose_best_move(second, first, turn, hp[second.name] / 100, status_effects)

        #calculates attacks
        for attacker, defender, move in [(first, second, first_move), (second, first, second_move)]:
            if hp[defender.name] <= 0:
                continue #if they're fainted its over

            effects = status_effects[attacker.name]

            #confusion/infatuation check
            if effects['infatuated'] or effects['confused']:
                if random.random() < 0.3:
                    print(f"Checking if {attacker.name} passes check to snap out of it")
                    effects['infatuated'] = False
                    effects['confused'] = False
                    effects['turns_volatile'] = 0
                    print(f"{attacker.name} snapped out of it!")
                else:
                    print(f"Checking if {attacker.name} passes check to attack")
                    if random.random() < 0.5:
                        print(f"{attacker.name} is too lost to move!")
                        effects['turns_volatile'] += 1
                        continue

            #status checks
            if effects['paralyzed']:
                if random.random() <= 0.25:
                    print(f"{attacker.name} is fully paralyzed!")
                    continue
            
            if effects['burned']:
                burn_damage = max(1, hp[attacker.name] // 8)
                print(f"{attacker.name} is hurt by it's burn!")
                hp[attacker.name] -= burn_damage
            
            if effects['poisoned']:
                if effects['toxic_counter'] > 0:
                    print(f"{attacker.name} is badly poisoned!")
                    toxic_damage = max(1, hp[attacker.name] * effects['toxic_counter'] // 16)
                    hp[attacker.name] -= toxic_damage
                    effects['toxic_counter'] += 1
                else:
                    print(f"{attacker.name} is hurt by poison!")
                    poison_damage = max(1, hp[attacker.name] // 8)
                    hp[attacker.name] -= poison_damage
            
            if effects['asleep'] > 0:
                print(f"{attacker.name} is fast asleep!")
                effects['asleep'] -= 1
                continue

            
            move_data = move_types.get(move, {})
            move_type = move_data.get('type', '')
            power = move_data.get('power', 0) #0 if no damage

            #check if move can give effects
            if move_data.get('effect') == 'infatuate':
                status_effects[defender.name]['infatuated'] = True
                print(f"{attacker.name} used {move}. {defender.name} is in love!")
            elif move_data.get('effect') == 'confuse':
                status_effects[defender.name]['confused'] = True
                print(f'{attacker.name} used {move}. {defender.name} is confused!')
            elif move_data.get('effect') == 'paralyze':
                status_effects[defender.name]['paralyzed'] = True
                print(f"{attacker.name} used {move}. {defender.name} is paralyzed! It may be unable to move!")
            elif move_data.get('effect') == 'burn':
                status_effects[defender.name]['burned'] = True
                print(f"{attacker.name} used {move}. {defender.name} was burned!")
            elif move_data.get('effect') == 'toxic':
                status_effects[defender.name]['poisoned'] = True
                status_effects[defender.name]['toxic_counter'] = 1
                print(f"{attacker.name} used {move}. {defender.name} is badly poisoned!")

            
            #checks if its a status
            if move_data.get('category') == 'Status' or power == 0:
                print(f"{attacker.name} used {move} — no damage dealt (status move or non-damaging).")
                continue

            #PS split
            if move_data.get('category') == 'Special':
                atk = attacker.stats['spa']
                defense = defender.stats['spd']
            else:
                atk = attacker.stats['atk']
                defense = defender.stats['def']
            
            eff = 1.0
            for t in defender.types:
                eff *= effectiveness(move_type, t)
            
            if eff == 0.0:
                print(f"{attacker.name} used {move}... but it had no effect!")
                continue

            #gen 3 formula (heavily simplified)
            modifier = eff * random.uniform(0.85, 1.0)
            damage = int((((2 * 50 / 5 + 2) * power * atk / defense) / 50 + 2) * modifier)

            hp[defender.name] -= damage
            hp[defender.name] = max(0, hp[defender.name])
            #annoying (xD) effectiveness flavor text
            print(f"{attacker.name} used {move}! It's {'super effective' if eff > 1 else 'not very effective' if eff < 1 else 'effective'}! {defender.name} took {damage} damage. (HP: {hp[defender.name]}/100)")
            
            if hp[defender.name] == 0:
                print(f"{defender.name} fainted!\n")
                break

        turn += 1
        if turn > MAX_TURNS:
            print("The battle lasted too long and ended in a draw!")
            break
    winner = p1.name if hp[p1.name] > 0 else p2.name
    print(f"{winner} wins the battle!")

if __name__ == "__main__":
    df = pd.read_csv("L50R1P.csv")
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    pokemon_list = [row_to_pokemon(row) for _, row in df.iterrows()]
    print(pokemon_list[423])
    print(pokemon_list[129])

    ben_mon = pokemon_list[423]
    enemy_mon = pokemon_list[129]
    run_battle(ben_mon, enemy_mon)
    
