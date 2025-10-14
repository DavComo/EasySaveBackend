"""
Block data model for hierarchical data storage.

This module defines the Block class, which represents a unit of data storage
with a hierarchical identifier and string value. Blocks are used to store
user data in a structured, path-like format.
"""


class Block:
    """
    Represents a data block with an identifier and value.
    
    A Block is the fundamental unit of data storage in the system. Each block
    has a unique hierarchical identifier (e.g., "prod.username.folder.item")
    and a string value containing the actual data.
    
    Attributes:
        identifier (str): The hierarchical path identifier for this block.
        value (str): The data content stored in this block.
    
    Example:
        block = Block("prod.johndoe.documents.report1", "Report content here")
        print(block.getIdentifier())  # "prod.johndoe.documents.report1"
        print(block.getValue())        # "Report content here"
    """
    identifier: str
    value: str

    def __init__(self, identifier: str, value:str = ""):
        """
        Initialize a new Block instance.
        
        Args:
            identifier (str): The hierarchical identifier path for this block.
            value (str, optional): The data content to store. Defaults to empty string.
        """
        self.identifier = identifier
        self.value = value

    def getValue(self) -> str:
        """
        Get the value stored in this block.
        
        Returns:
            str: The data content of this block.
        """
        return self.value    

    def setValue(self, value: str) -> None:
        """
        Set the value of this block.
        
        Args:
            value (str): The new data content to store in this block.
        """
        self.value = value

    def getIdentifier(self) -> str:
        """
        Get the identifier of this block.
        
        Returns:
            str: The hierarchical identifier path of this block.
        """
        return self.identifier

    @staticmethod
    def tupleToBlock(rawBlock: tuple[str, str]) -> "Block":
        """
        Convert a tuple to a Block object.
        
        This factory method creates a Block instance from a tuple containing
        an identifier and value, typically from database query results.
        
        Args:
            rawBlock (tuple[str, str]): A tuple containing (identifier, value).
        
        Returns:
            Block: A new Block instance with the provided identifier and value.
        
        Example:
            raw = ("prod.user.item", "data content")
            block = Block.tupleToBlock(raw)
        """
        return Block(rawBlock[0], rawBlock[1])

    @staticmethod
    def tupleListToBlocks(rawBlockList: list[tuple[str, str]]) -> list["Block"]:
        """
        Convert a list of tuples to a list of Block objects.
        
        This factory method creates multiple Block instances from a list of tuples,
        typically from database query results that return multiple rows.
        
        Args:
            rawBlockList (list[tuple[str, str]]): A list of tuples, each containing
                (identifier, value).
        
        Returns:
            list[Block]: A list of Block instances created from the tuples.
        
        Example:
            raw_list = [
                ("prod.user.item1", "content1"),
                ("prod.user.item2", "content2")
            ]
            blocks = Block.tupleListToBlocks(raw_list)
        """
        blocks: list[Block] = []

        for rawBlock in rawBlockList:
            blocks.append(Block.tupleToBlock(rawBlock))
        
        return blocks