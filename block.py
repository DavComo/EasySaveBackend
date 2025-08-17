import utils

class Block:
    IDENTIFIER: str
    value: str

    def __init__(self, identifier: str, value:str = ""):
        self.IDENTIFIER = identifier
        self.value = value

    def getValue(self) -> str:
            return self.value    

    def setValue(self, value: str) -> None:
        self.value = value

    def getIdentifier(self) -> str:
        return self.IDENTIFIER

    @staticmethod
    def tupleToBlock(rawBlock: tuple[str, str]) -> Block:
        return Block(tuple[0], tuple[1])

    @staticmethod
    def tupleListToBlocks(rawBlockList: list[tuple[str, str]]) -> list[Block]:
        blocks: list[Block] = []

        for rawBlock in rawBlockList:
            blocks.append(tupleToBlock(rawBlock))
        
        return blocks