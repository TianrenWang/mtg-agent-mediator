from pydantic import BaseModel
from datetime import datetime
from constants import PLAYER_A_VICTORY, PLAYER_B_VICTORY
import asyncio
import subprocess

mageSimulationCommand = [
    'mvn', 'test', '"-Dsurefire.failIfNoSpecifiedTests=false"',  '-Dtest=SimulationPerformanceAITest#test_card_order']
mageDirectory = '../mage'


class GameState(BaseModel):
    state: str
    actionSize: int


class Mediator:
    def __init__(self):
        self.unmatchedGames = {}
        self.states = {}
        self.moves = {}
        self.gameEvents = {}
        self.unmatchedAgentsQueue = []
        self.unmatchedGameEvent = asyncio.Event()
        self.replenishGames()

    def replenishGames(self):
        numberOfGames = len(self.unmatchedGames.keys()) + \
            len(self.states) + len(self.moves)
        if numberOfGames < 5:
            print(f"There are {numberOfGames} games. Replenishing.")
            for i in range(3):
                subprocess.Popen(mageSimulationCommand, cwd=mageDirectory,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async def getMove(self, gameId: str, body: GameState):
        if gameId not in self.moves:
            self.unmatchedGames[gameId] = [body.state, body.actionSize]
            print(f"Game {gameId} just joined queued.")
            if len(self.unmatchedGames.items()) == 1:
                self.unmatchedGameEvent.set()
        else:
            self.states[gameId] = [body.state, body.actionSize]
            if gameId not in self.moves:
                raise Exception(f"No previous move for {gameId}.")
            del self.moves[gameId]

            if gameId not in self.gameEvents:
                raise Exception(f"No new-state event for {gameId}.")
            self.gameEvents[gameId].set()

            if body.state == PLAYER_A_VICTORY or body.state == PLAYER_B_VICTORY:
                print(f"Mage delivered state, game {gameId} ended.")
                return -1

        # print("Mage delivered state, waiting for move: " + gameId)

        event = asyncio.Event()
        self.gameEvents[gameId] = event
        await event.wait()

        if gameId not in self.moves:
            raise Exception(f"No new move for {gameId}.")

        # print(f"Mage finished waiting next move for {gameId}")
        return self.moves[gameId]

    async def matchGame(self):
        matchEvent = asyncio.Event()
        self.unmatchedAgentsQueue.append(matchEvent)
        if len(self.unmatchedAgentsQueue) == 1:
            matchEvent.set()

        print("Agent waiting in match queue")
        await matchEvent.wait()
        if not len(self.unmatchedGames.items()):
            print("Agent waiting for match")
            await self.unmatchedGameEvent.wait()

        response = None
        for gameId, game in self.unmatchedGames.items():
            self.states[gameId] = [game[0], game[1]]
            response = [gameId, game[0], game[1]]
            del self.unmatchedGames[gameId]
            if not len(self.unmatchedGames.items()):
                self.unmatchedGameEvent = asyncio.Event()
            break

        self.unmatchedAgentsQueue.pop(0)
        if len(self.unmatchedAgentsQueue):
            self.unmatchedAgentsQueue[0].set()
        print("Agent finished matching")
        return response

    async def getState(self, gameId: str, actionId: int):
        if gameId not in self.states:
            raise Exception(f"No previous state for {gameId}.")
        del self.states[gameId]
        self.moves[gameId] = actionId
        if gameId not in self.gameEvents:
            raise Exception(f"No new-move event for {gameId}.")
        self.gameEvents[gameId].set()

        event = asyncio.Event()
        self.gameEvents[gameId] = event

        # print("MuZero delivered move, waiting for next state: " + gameId)
        beforeWaitTime = datetime.now()
        asyncio.wait_for(await event.wait(), 2)
        waitedTime = (datetime.now() - beforeWaitTime).total_seconds()
        if waitedTime > 1.9:
            event.set()
            del self.gameEvents[gameId]
            del self.moves[gameId]
            raise Exception(f"Game {gameId} crashed.")

        if gameId not in self.states:
            raise Exception(f"No new state for {gameId}.")

        # print("MuZero got next state for " + gameId)
        state = self.states[gameId][0]
        actionSize = self.states[gameId][1]
        if state == PLAYER_A_VICTORY or state == PLAYER_B_VICTORY:
            print(f"Agent received victory state for game {gameId}.")
            del self.gameEvents[gameId]
            del self.states[gameId]
            self.replenishGames()
        return [state, actionSize]
