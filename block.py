class Block:
    identifier: str
    value: str

    def __init__(self, identifier: str, value:str = ""):
        self.identifier = identifier
        self.value = value

    def getValue(self) -> str:
            return self.value    

    def setValue(self, value: str) -> None:
        self.value = value

    def getIdentifier(self) -> str:
        return self.identifier

    @staticmethod
    def tupleToBlock(rawBlock: tuple[str, str]) -> "Block":
        return Block(rawBlock[0], rawBlock[1])

    @staticmethod
    def tupleListToBlocks(rawBlockList: list[tuple[str, str]]) -> list["Block"]:
        blocks: list[Block] = []

        for rawBlock in rawBlockList:
            blocks.append(Block.tupleToBlock(rawBlock))
        
        return blocks