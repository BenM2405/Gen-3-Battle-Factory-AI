class Pokemon:
    def __init__(self, name, types, moves, stats, item, ability):
        self.name = name
        self.types = types
        self.moves = moves
        self.stats = stats
        self.item = item
        self.ability = ability
    
    def __str__(self):
        return f"{self.name} ({'/'.join(self.types)}): {', '.join(self.moves)}"
    
    def __repr__(self):
        return self.__str__()