from fastapi import FastAPI
from mediator import GameState, Mediator

app = FastAPI()
mediator = Mediator()
# with open("my_file.txt", "a") as file:
#     file.write("*****************\n" + body.state)


@app.post("/mage/{gameId}")
async def getMove(gameId: str, body: GameState):
    return await mediator.getMove(gameId, body)


@app.get("/agent/match")
async def matchGame():
    return await mediator.matchGame()


@app.get("/agent/{gameId}/{actionId}")
async def getState(gameId: str, actionId: int):
    return await mediator.getState(gameId, actionId)
