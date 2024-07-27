import requests
import random

from constants import PLAYER_A_VICTORY, PLAYER_B_VICTORY

request = requests.get("http://127.0.0.1:8000/agent/match")
gameId, state, actionSize = request.json()
action = random.randint(0, actionSize - 1)

while True:
    nextState = requests.get(
        f"http://127.0.0.1:8000/agent/{gameId}/{action}")
    state, actionSize = nextState.json()
    if state == PLAYER_A_VICTORY or state == PLAYER_B_VICTORY:
        break
    action = random.randint(0, actionSize - 1)

print(f"Game Ended for {gameId}")
