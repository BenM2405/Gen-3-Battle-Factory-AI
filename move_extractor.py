import pandas as pd

df = pd.read_csv('L50R1P.csv')
df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

move_columns = [col for col in df.columns if col.startswith('move_')]

all_moves = []
for col in move_columns:
    all_moves.extend(df[col].dropna().astype(str).str.strip())

unique_moves = sorted(set(all_moves))

for move in unique_moves:
    print(move)

with open('unique_moves.txt', 'r', encoding='utf-8') as f:
    moves = [line.strip() for line in f if line.strip()]

move_types = {move: '' for move in moves}

with open('move_types.py', 'w', encoding='utf-8') as f:
    f.write('move_types = {\n')
    for move in sorted(move_types):
        f.write(f"    '{move}': '', \n")
    f.write("}\n")

print("dictionary scaffold written to move_types.py")