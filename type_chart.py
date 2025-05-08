type_chart = {
    'Normal': {
        'Rock': 0.5, 'Ghost': 0.0, 'Steel': 0.5
    },
    'Fighting': {
        'Normal': 2.0, 'Rock': 2.0, 'Steel': 2.0, 'Ice': 2.0, 'Dark': 2.0,
        'Flying': 0.5, 'Poison': 0.5, 'Bug': 0.5, 'Psychic': 0.5, 'Ghost': 0.0
    },
    'Flying': {
        'Fighting': 2.0, 'Bug': 2.0, 'Grass': 2.0,
        'Rock': 0.5, 'Steel': 0.5, 'Electric': 0.5
    },
    'Poison': {
        'Grass': 2.0,
        'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5, 'Steel': 0.0
    },
    'Ground': {
        'Poison': 2.0, 'Rock': 2.0, 'Steel': 2.0, 'Fire': 2.0, 'Electric': 2.0,
        'Bug': 0.5, 'Grass': 0.5, 'Flying': 0.0
    },
    'Rock': {
        'Flying': 2.0, 'Bug': 2.0, 'Fire': 2.0, 'Ice': 2.0,
        'Fighting': 0.5, 'Ground': 0.5, 'Steel': 0.5
    },
    'Bug': {
        'Grass': 2.0, 'Psychic': 2.0, 'Dark': 2.0,
        'Fighting': 0.5, 'Flying': 0.5, 'Poison': 0.5, 'Ghost': 0.5, 'Steel': 0.5, 'Fire': 0.5
    },
    'Ghost': {
        'Ghost': 2.0, 'Psychic': 2.0,
        'Dark': 0.5, 'Steel': 0.5, 'Normal': 0.0
    },
    'Steel': {
        'Rock': 2.0, 'Ice': 2.0,
        'Steel': 0.5, 'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5
    },
    'Fire': {
        'Bug': 2.0, 'Steel': 2.0, 'Grass': 2.0, 'Ice': 2.0,
        'Rock': 0.5, 'Fire': 0.5, 'Water': 0.5, 'Dragon': 0.5
    },
    'Water': {
        'Ground': 2.0, 'Rock': 2.0, 'Fire': 2.0,
        'Water': 0.5, 'Grass': 0.5, 'Dragon': 0.5
    },
    'Grass': {
        'Ground': 2.0, 'Rock': 2.0, 'Water': 2.0,
        'Flying': 0.5, 'Poison': 0.5, 'Bug': 0.5, 'Steel': 0.5, 'Fire': 0.5, 'Grass': 0.5, 'Dragon': 0.5
    },
    'Electric': {
        'Flying': 2.0, 'Water': 2.0,
        'Grass': 0.5, 'Electric': 0.5, 'Dragon': 0.5, 'Ground': 0.0
    },
    'Psychic': {
        'Fighting': 2.0, 'Poison': 2.0,
        'Steel': 0.5, 'Psychic': 0.5, 'Dark': 0.0
    },
    'Ice': {
        'Flying': 2.0, 'Ground': 2.0, 'Grass': 2.0, 'Dragon': 2.0,
        'Steel': 0.5, 'Fire': 0.5, 'Water': 0.5, 'Ice': 0.5
    },
    'Dragon': {
        'Dragon': 2.0,
        'Steel': 0.5
    },
    'Dark': {
        'Ghost': 2.0, 'Psychic': 2.0,
        'Fighting': 0.5, 'Dark': 0.5, 'Steel': 0.5
    }
}
