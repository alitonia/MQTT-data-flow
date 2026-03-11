import os
import random

os.makedirs('edge/data', exist_ok=True)
with open('edge/data/train_FD001.txt', 'w') as f:
    for unit in range(1, 4): # 3 units
        for time in range(1, 51): # 50 cycles each
            settings = [round(random.uniform(-1, 1), 4) for _ in range(3)]
            sensors = [round(random.uniform(10, 100), 2) for _ in range(21)]
            row = [unit, time] + settings + sensors
            f.write(" ".join(map(str, row)) + "\n")
print("Mock data generated at edge/data/train_FD001.txt")
