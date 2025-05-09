item_effects = {
    "Brightpowder": {
        "trigger": "on_hit",
        "effect": "evasion_boost",
        "value": 0.9
    },
    "Charcoal": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Fire",
        "multiplier": 1.1
    },
    "Cheri Berry": {
        "trigger": "status",
        "effect": "cure_status",
        "status": "paralyzed"
    },
    "Chesto Berry": {
        "trigger": "status",
        "effect": "cure_status",
        "status": "asleep"
    },
    "Dragon Fang": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Dragon",
        "multiplier": 1.1
    },
    "Focus Band": {
        "trigger": "fatal_hit",
        "effect": "survive_1hp",
        "chance": 0.1
    },
    "Hard Stone": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Rock",
        "multiplier": 1.1
    },
    "King's Rock": {
        "trigger": "on_hit",
        "effect": "flinch_chance",
        "chance": 0.1
    },
    "Leftovers": {
        "trigger": "end_turn",
        "effect": "heal_percent",
        "value": 6.25
    },
    "Liechi Berry": {
        "trigger": "low_hp",
        "effect": "boost_stat",
        "stat": "atk",
        "stages": 1,
        "threshold": 0.25
    },
    "Lum Berry": {
        "trigger": "status",
        "effect": "cure_all_status"
    },
    "Mental Herb": {
        "trigger": "status",
        "effect": "cure_status",
        "status": "infatuated"
    },
    "Metal Coat": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Steel",
        "multiplier": 1.1
    },
    "Mystic Water": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Water",
        "multiplier": 1.1
    },
    "Nevermeltice": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Ice",
        "multiplier": 1.1
    },
    "Pecha Berry": {
        "trigger": "status",
        "effect": "cure_status",
        "status": "poisoned"
    },
    "Persim Berry": {
        "trigger": "status",
        "effect": "cure_status",
        "status": "confused"
    },
    "Poison Barb": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Poison",
        "multiplier": 1.1
    },
    "Scope Lens": {
        "trigger": "on_move",
        "effect": "crit_boost",
        "multiplier": 1.5
    },
    "Sharp Beak": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Flying",
        "multiplier": 1.1
    },
    "Shell Bell": {
        "trigger": "on_damage_dealt",
        "effect": "heal_fraction_damage",
        "multiplier": 0.125
    },
    "Silk Scarf": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Normal",
        "multiplier": 1.1
    },
    "Silverpowder": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Bug",
        "multiplier": 1.1
    },
    "Sitrus Berry": {
        "trigger": "low_hp",
        "effect": "heal_flat",
        "value": 30,
        "threshold": 0.5
    },
    "Soft Sand": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Ground",
        "multiplier": 1.1
    },
    "Spell Tag": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Ghost",
        "multiplier": 1.1
    },
    "Twistedspoon": {
        "trigger": "on_move",
        "effect": "boost_type",
        "type": "Psychic",
        "multiplier": 1.1
    },
    "White Herb": {
        "trigger": "stat_drop",
        "effect": "cure_stat_drops"
    }
}
