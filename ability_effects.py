import random
def check_immunity(ability_effect, move_type):
    if ability_effect.startswith("immunity:"):
        immune_type = ability_effect.split(":")[1]
        return move_type == immune_type
    return False

def prevent_status(ability_effect, status):
    if ability_effect.startswith("prevent_status:"):
        blocked = ability_effect.split(":")[1]
        return status == blocked
    return False

def modify_speed(mon, weather, ability_effect):
    if ability_effect == "boost_spe_if_sun" and weather == "Sun":
        return mon.stats["spe"] * 2
    if ability_effect == "boost_spe_if_rain" and weather == "Rain":
        return mon.stats["spe"] * 2
    return mon.stats["spe"]

def modify_attack(mon, ability_effect, status_effects):
    if ability_effect == "boost_atk_if_status":
        if any([
            status_effects.get(mon.name, {}).get("burned", False),
            status_effects.get(mon.name, {}).get("poisoned", False),
            status_effects.get(mon.name, {}).get("paralyzed", False),
            status_effects.get(mon.name, {}).get("asleep", 0) > 0,
            status_effects.get(mon.name, {}).get("confused", False),
        ]):
            return mon.stats["atk"] * 1.5
    return mon.stats["atk"]

def boost_type_if_lowhp(mon, move_type, ability_effect, hp_ratio):
    if ability_effect.startswith("boost_type_if_lowhp:"):
        boost_type = ability_effect.split(":")[1]
        if move_type == boost_type and hp_ratio < 0.333:
            return 1.5
    return 1.0

def apply_contact_ability(defender, attacker, ability_effect, status_effects):
    if ability_effect == "contact_paralyze":
        if random.random() <= 0.3:
            status_effects[attacker.name]["paralyzed"] = True
            return "paralyzed"
    if ability_effect == "contact_burn":
        if random.random() <= 0.3:
            status_effects[attacker.name]["burned"] = True
            return "burned"
    if ability_effect == "chanceinfatuate":
        if random.random() <= 0.3:
            status_effects[attacker.name]["infatuated"] = True
            return "infatuated"
    return None

def on_entry_lower_stat(ability_effect, stat, target_stats):
    if ability_effect == f"on_entry_lower:{stat}":
        target_stats[stat] = max(1, int(target_stats[stat] * 0.67))  # reduce stat
        return True
    return False

def should_heal_on_hit(ability_effect, move_type):
    if ability_effect.startswith("heal_on_hit:"):
        heal_type = ability_effect.split(":")[1]
        return move_type == heal_type
    return False
