import pandas as pd
import random
import matplotlib.pyplot as plt
import csv
from itertools import combinations
from pokemon import Pokemon
from type_chart import type_chart
from move_types_full import move_types
from items import item_effects
from abilities import abilities as ability_lookup
from ability_effects import (
    check_immunity,
    modify_attack,
    modify_speed,
    boost_type_if_lowhp,
    apply_contact_ability,
    should_heal_on_hit,
    prevent_status,
    on_entry_lower_stat
)


def effectiveness(attacking_type, defending_type):
    return type_chart.get(attacking_type, {}).get(defending_type, 1.0)

base_stats_df = pd.read_csv("basestats.csv")
base_stats_df.columns = [col.strip().lower().replace(" ", "_") for col in base_stats_df.columns]
base_stats_df.set_index("name", inplace=True)
ALL_STATUSES = ['paralyzed', 'burned', 'poisoned', 'confused', 'infatuated', 'asleep', 'spd_down', 'spa_down', 'atk_down', 'def_down']

#choose random set
def parse_random_ability(possible):
    if pd.isna(possible):
        return None
    options = [a.strip() for a in possible.split("/")]
    return random.choice(options)

#parse pokemon and random ability
def build_rental_pool(df, count=6):
    pool_rows = df.sample(n=count)
    updated_rows = []
    for _, row in pool_rows.iterrows():
        row = row.copy()
        row["ability"] = parse_random_ability(row["possible_ability"])
        updated_rows.append(row_to_pokemon(row))
    return updated_rows

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
    
    item = row['item']

    return Pokemon(name, types, moves, stats, item=item, ability=row.get("ability", None))

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

def choose_top_team(pokemon_list, team_size = 3):
    best_team = None
    best_score = float('-inf')

    for combo in combinations(pokemon_list, team_size):
        score = score_team(combo)
        if score > best_score:
            best_score = score
            best_team = combo
    
    return list(best_team)

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

def should_switch(current, team, opponent, hp):
    curr_hp = hp[current.name]
    curr_spe = modify_speed(current, None, ability_lookup.get(current.ability, {}).get("effect", ""))
    opp_spe = modify_speed(opponent, None, ability_lookup.get(opponent.ability, {}).get("effect", ""))

    # if faster, get that last hit
    if curr_hp < 30 and curr_spe >= opp_spe:
        return None

    # guess incoming move danger
    highest_threat = 0
    for move in opponent.moves:
        move_data = move_types.get(move, {})
        move_type = move_data.get("type", "")
        move_power = move_data.get("power", 0)
        if any(effectiveness(move_type, t) > 1.0 for t in current.types):
            highest_threat += move_power

    # if they're a big threat, just dont switch
    if highest_threat >= curr_hp:
        return None

    # who would be better???
    for candidate in team:
        if candidate.name == current.name or hp[candidate.name] <= 0:
            continue
        for move in opponent.moves:
            m = move_types.get(move, {})
            move_type = m.get("type", "")
            if any(effectiveness(move_type, t) < 1.0 for t in candidate.types):
                return candidate
    
    return None


#Battle Test
def run_battle(player_team, enemy_team):
    p1_active = player_team[0]
    p2_active = enemy_team[0]
    print(f"Battle Start: {p1_active.name} vs. {p2_active.name}!\n")

    hp = {mon.name: 100 for mon in player_team + enemy_team}
    pp = {p1_active.name: {move: 10 for move in p1_active.moves}, p2_active.name: {move: 10 for move in p2_active.moves},}
    MAX_TURNS = 50
    turn = 1

    active_turns = {p1_active.name: 0, p2_active.name: 0}

    item_used = {p1_active.name: False, p2_active.name: False}
    status_effects = {
        p1_active.name : {'infatuated': False, 
                   'confused': False, 
                   'turns_volatile': 0,
                   'paralyzed': False,
                   'asleep': 0,
                   'burned': False,
                   'poisoned': False,
                   'toxic_counter': 0,
                   'flinched': False,
                   },
        p2_active.name : {'infatuated': False, 
                   'confused': False, 
                   'turns_volatile': 0,
                   'paralyzed': False,
                   'asleep': 0,
                   'burned': False,
                   'poisoned': False,
                   'toxic_counter': 0,
                   'flinched': False,
                   },
    }
    weather = {'type': None, 'turns': 0}
    def ensure_mon_initialized(mon):
        if mon.name not in status_effects:
            status_effects[mon.name] = {
                k: (0 if 'down' in k or k in ['asleep', 'toxic_counter', 'turns_volatile'] else False)
                for k in ALL_STATUSES + ['turns_volatile', 'toxic_counter', 'flinched']
            }
        if mon.name not in pp:
            pp[mon.name] = {move: 10 for move in mon.moves}
        if mon.name not in item_used:
            item_used[mon.name] = False
        if mon.name not in active_turns:
            active_turns[mon.name] = 0

    #basically intimidate check
    for source, target in [(p1_active, p2_active), (p2_active, p1_active)]:
        effect = ability_lookup.get(source.ability, {}).get('effect', '')
        if effect.startswith('on_entry_lower:'):
            stat = effect.split(":")[1]
            lowered = on_entry_lower_stat(effect, stat, target.stats)
            if lowered:
                print(f"{source.name}'s {source.ability} lowered {target.name}'s {stat}!")

    #speed check
    while hp[p1_active.name] > 0 and hp[p2_active.name] > 0 and turn <= MAX_TURNS:
        print(f"Turn {turn}")

        p1_active_spe = modify_speed(p1_active, weather['type'], ability_lookup.get(p1_active.ability, {}).get("effect", ""))
        p2_active_spe = modify_speed(p2_active, weather['type'], ability_lookup.get(p2_active.ability, {}).get("effect", ""))
        # Switching phase
        p1_switch = should_switch(p1_active, player_team, p2_active, hp)
        if p1_switch:
            print(f"{p1_active.name} switches out! {p1_switch.name} is sent in!")
            p1_active = p1_switch

        p2_switch = should_switch(p2_active, enemy_team, p1_active, hp)
        if p2_switch:
            print(f"{p2_active.name} switches out! {p2_switch.name} is sent in!")
            p2_active = p2_switch
        
        ensure_mon_initialized(p1_active)
        ensure_mon_initialized(p2_active)
        # calculate speed and turn order AFTER switching
        p1_active_spe = modify_speed(p1_active, weather['type'], ability_lookup.get(p1_active.ability, {}).get("effect", ""))
        p2_active_spe = modify_speed(p2_active, weather['type'], ability_lookup.get(p2_active.ability, {}).get("effect", ""))
        if p1_active_spe > p2_active_spe:
            first, second = p1_active, p2_active
        else:
            first, second = p2_active, p1_active

        #each AI chooses a move
        first_move = choose_best_move(first, second, turn, hp[first.name] / 100, status_effects)
        second_move = choose_best_move(second, first, turn, hp[second.name] / 100, status_effects)

        #calculates attacks
        for attacker, defender, move in [(first, second, first_move), (second, first, second_move)]:
            active_turns[attacker.name] += 1
            #pp check
            if pp[attacker.name][move] <= 0:
                print(f"{attacker.name} tried to use {move}, but it has no PP left!")
                continue
            pp[attacker.name][move] -= 1
            if ability_lookup.get(defender.ability, {}).get("effect") == "ppdrop":
                pp[attacker.name][move] = max(0, pp[attacker.name][move] - 1)
                print(f"{defender.name}'s Pressure caused {move} to lose 2 PP!")

            if hp[defender.name] <= 0:
                continue #if they're fainted its over

            effects = status_effects[attacker.name]
            # check flinch
            if effects['flinched']:
                print(f"{attacker.name} flinched and couldn't move!")
                effects['flinched'] = False
                continue
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

            # move hindering status checks
            if effects['paralyzed']:
                if random.random() <= 0.25:
                    print(f"{attacker.name} is fully paralyzed!")
                    continue
            if effects['asleep'] > 0:
                print(f"{attacker.name} is fast asleep!")
                effects['asleep'] -= 1
                continue

            #basically sitrus berry check
            item = item_effects.get(attacker.item, {})
            if (
                not item_used[attacker.name]
                and item.get('trigger') == 'low_hp'
                and hp[attacker.name] <= 100 * item['threshold']
            ):
                if item['effect'] == 'heal_flat':
                    hp[attacker.name] = min(100, hp[attacker.name] + item['value'])
                    item_used[attacker.name] = True
                    print(f"{attacker.name} restored health using its {attacker.item}!")

            
            move_data = move_types.get(move, {})
            move_type = move_data.get('type', '')
            power = move_data.get('power', 0) #0 if no damage

            #check accuracy
            if move == "Thunder" and weather['type'] == 'Rain':
                accuracy = 100
            accuracy = move_data.get('accuracy', 100) #100 by default since most are 100
            if random.randint(1, 100) > accuracy:
                print(f"{attacker.name} used {move}... but it missed!")
                continue


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

            #cure items
            item = item_effects.get(defender.item, {})

            if not item_used[defender.name] and item.get('trigger') == 'status':
                effect = item.get('effect')
                status_to_cure = item.get('status')
                #cureall (lum)
                if effect == "cure_all_status":
                    for k in ALL_STATUSES:
                        status_effects[defender.name][k] = False if isinstance(status_effects[defender.name][k], bool) else 0
                    item_used[defender.name] = True
                    print(f"{defender.name}'s {defender.item} cured all status conditions!")
                #cure some (pecha, rawst, etc)
                elif status_to_cure and status_effects[defender.name].get(status_to_cure):
                    if isinstance(status_effects[defender.name][status_to_cure], bool):
                        status_effects[defender.name][status_to_cure] = False
                    else:
                        status_effects[defender.name][status_to_cure] = 0
                    item_used[defender.name] = True
                    print(f"{defender.name}'s {defender.item} cured its {status_to_cure}!")
            
            #checks if its a status
            if move_data.get('category') == 'Status' or power == 0:
                print(f"{attacker.name} used {move} — no damage dealt (status move or non-damaging).")
                continue
            #weather
            if move_data.get('effect') == 'rain':
                weather['type'] = 'Rain'
                weather['turns'] = 5
                print('It started to rain!')
            elif move_data.get('effect') == 'sun':
                weather['type'] = 'Sun'
                weather['turns'] = 5
                print('The sunlight turned harsh!')
            #P/S split
            if move_data.get('category') == 'Special':
                atk = attacker.stats['spa']
                defense = defender.stats['spd']
            else:
                atk = attacker.stats['atk']
                defense = defender.stats['def']
            atk = modify_attack(attacker, ability_lookup.get(attacker.ability, {}).get("effect", ""), status_effects)
            eff = 1.0
            for t in defender.types:
                eff *= effectiveness(move_type, t)
            
            defender_effect = ability_lookup.get(defender.ability, {}).get('effect', '')
            if check_immunity(defender_effect, move_type):
                print(f"{attacker.name} used {move}... but {defender.name}'s {defender.ability} made it immune!")
                continue
            if eff == 0.0:
                print(f"{attacker.name} used {move}... but it had no effect!")
                continue

            #attack boosters (Nevermeltice, metal coat, etc.)
            if attacker.item in item_effects:
                item = item_effects[attacker.item]
                if item['trigger'] == 'on_move' and item.get('type') == move_type:
                    power = max(1, power)
                    power = int(power * item['multiplier'])
                    print(f"{attacker.name}'s {attacker.item} boosted its {move_type} move!")
            #weather boosts
            if weather['type'] == 'Rain':
                if move_type == 'Water':
                    power = int(power * 1.5)
                elif move_type == 'Fire':
                    power = int(power * 0.5)
            elif weather['type'] == 'Sun':
                if move_type == 'Fire':
                    power = int(power * 1.5)
                elif move_type == 'Water':
                    power = int(power * 0.5)
            #crits
            crit_chance = 6.25
            if attacker.item == "Scope Lens":
                crit_chance = 12.5
            
            if random.uniform(0, 100) < crit_chance:
                power = int(power * 2)
                print("A Critical Hit!")
            
            #gen 3 formula (heavily simplified)
            power = int(power * boost_type_if_lowhp(attacker, move_type, ability_lookup.get(attacker.ability, {}).get("effect", ""), hp[attacker.name] / 100))
            modifier = eff * random.uniform(0.85, 1.0)
            damage = int((((2 * 50 / 5 + 2) * power * atk / defense) / 50 + 2) * modifier)

            #check healing abilities
            attacker_effect = ability_lookup.get(defender.ability, {}).get("effect", "")
            if should_heal_on_hit(attacker_effect, move_type):
                heal_amt = int(100 * 0.25)
                hp[defender.name] = min(100, hp[defender.name] + heal_amt)
                print(f"{defender.name} absorbed the {move_type}-type move and healed!")
                continue
            hp[defender.name] -= damage
            hp[defender.name] = max(0, hp[defender.name])

            #status infliction check
            status = move_data.get('status')
            chance = move_data.get('status_chance', 0)

            if status and random.randint(1, 100) <= chance:
                if not status_effects[defender.name].get(status):
                    if isinstance(status_effects[defender.name][status], bool):
                        status_effects[defender.name][status] = True
                    else:
                        status_effects[defender.name][status] = 1
                    print(f"{defender.name} was affected by {status}!")

            #annoying (xD) effectiveness flavor text
            print(f"{attacker.name} used {move}! It's {'super effective' if eff > 1 else 'not very effective' if eff < 1 else 'effective'}! {defender.name} took {damage} damage. (HP: {hp[defender.name]}/100)")
            
            #contact ability check
            contact_effect = ability_lookup.get(defender.ability, {}).get("effect", "")
            result = apply_contact_ability(defender, attacker, contact_effect, status_effects)
            if result:
                print(f"{attacker.name} was {result} due to contact with {defender.name}!")
            
            #also annoying shell bell check
            if attacker.item == 'Shell Bell' and damage > 0:
                heal = max(1, int(damage * item_effects['Shell Bell']['multiplier']))
                hp[attacker.name] = min(100, hp[attacker.name] + heal)
                print(f"{attacker.name} regained HP with its Shell Bell!")
            
            #Focus band check
            if defender.item == "Focus Band" and damage >= hp[defender.name]:
                if random.random() < item_effects['Focus Band']['chance']:
                    damage = hp[defender.name] - 1
                    print(f"{defender.name} held on with its Focus Band!")
            

            #damaging status effect checks
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
            # chance to flinch the opponent
            if move == "Fake Out":
                if active_turns[attacker.name] == 1:
                    if ability_lookup.get(defender.ability, {}).get("effect") != "noflinch":
                        status_effects[defender.name]['flinched'] = True
                        print(f"{defender.name} flinched from Fake Out!")
            else:
                if move_data.get('status') == 'flinch':
                    if random.randint(1, 100) <= move_data.get('status_chance', 0):
                        if ability_lookup.get(defender.ability, {}).get("effect") != "noflinch":
                            status_effects[defender.name]['flinched'] = True
                            print(f"{defender.name} flinched!")
            if attacker.item == "King's Rock":
                if random.random() <= item_effects["King's Rock"]["chance"]:
                    if ability_lookup.get(defender.ability, {}).get("effect") != "noflinch":
                        status_effects[defender.name]['flinched'] = True
                        print(f"{defender.name} flinched from King's Rock!")
            #weather tick
            if weather['type']:
                weather['turns'] -= 1
                if weather['turns'] == 0:
                    print(f"The {weather['type']} faded.")
                    weather['type'] = None
                else:
                    print(f"The {weather['type']} continues...")

            #leftovers & other after turn items
            for mon in [p1_active,p2_active]:
                item = item_effects.get(mon.item, {})
                if item.get('trigger') == 'end_turn' and item['effect'] == 'heal_percent':
                    heal = max(1, int(hp[mon.name] * (item['value'] / 100)))
                    hp[mon.name] = min(100, hp[mon.name] + heal)
                    print(f"{mon.name} restored a little HP using its {mon.item}!")
                turn += 1
                if turn > MAX_TURNS:
                    print("The battle lasted too long and ended in a draw!")
                    break
            #check if they've fainted
            if hp[defender.name] == 0:
                print(f"{defender.name} fainted!\n")

                #check if they have more mons
                team = player_team if defender.name in [m.name for m in player_team] else enemy_team
                available = [mon for mon in team if hp[mon.name] > 0]

                if available:
                    next_mon = available[0]
                    print(f"{defender.name}'s trainer sends out {next_mon.name}!")
                    if defender == p1_active:
                        p1_active = next_mon
                    else:
                        p2_active = next_mon

                    #initialize everything
                    ensure_mon_initialized(p1_active)
                    ensure_mon_initialized(p2_active)

                    break  # continue w next mon
                else:
                    break  # u lost bro...

    if any(hp[mon.name] > 0 for mon in player_team):
        print(f"{p1_active.name} wins the battle!")
    elif any(hp[mon.name] > 0 for mon in enemy_team):
        print(f"{p2_active.name} wins the battle!")
    else:
        print("Both teams fainted! It's a draw!")

    if any(hp[mon.name] > 0 for mon in player_team):
        return "player"
    elif any(hp[mon.name] > 0 for mon in enemy_team):
        return "enemy"
    else:
        return "draw"

if __name__ == "__main__":
    df = pd.read_csv("L50R1P.csv")
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    all_pokemon_list = [row_to_pokemon(row) for _, row in df.iterrows()]
    rental_pool_player = build_rental_pool(df)
    rental_pool_enemy = build_rental_pool(df)

    player_team = choose_top_team(rental_pool_player)
    enemy_team = choose_top_team(rental_pool_enemy)

    # Currently run_battle only supports 1v1; this runs the lead matchup
    # run_battle(player_team, enemy_team)

results = {"player": 0, "enemy": 0, "draw": 0}
results_log = []
for i in range(500):  # try 100 to start, scale up later
    player_team = random.sample(all_pokemon_list, 3)
    enemy_team = random.sample(all_pokemon_list, 3)
    winner = run_battle(player_team, enemy_team)
    results[winner] += 1
    results_log.append(winner)
    print(f"Game {i+1}: {winner}")


labels = results.keys()
values = results.values()

plt.bar(labels, values, color=['green', 'red', 'gray'])
plt.title("AI Battle Outcomes (3v3)")
plt.xlabel("Winner")
plt.ylabel("Number of Wins")
plt.show()

with open("battle_logs.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Match", "Winner"])
    for i, result in enumerate(results_log):
        writer.writerow([i+1, result])


    
