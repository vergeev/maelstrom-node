import sys
from typing import TypedDict, Literal, TextIO


type Json = dict[str, "Json"] | list["Json"] | str | int | float | bool | None


class Message(TypedDict):
    """Maelstrom message

    https://github.com/jepsen-io/maelstrom/blob/cb7f07239012d85d2c0595fd942ddb4613205905/doc/protocol.md#messages
    """

    src: str
    dest: str
    body: Json


class InitMessage(TypedDict):
    """Initialization message to the node

    https://github.com/jepsen-io/maelstrom/blob/cb7f07239012d85d2c0595fd942ddb4613205905/resources/protocol-intro.md#initialization
    """

    type: Literal["init"]
    msg_id: int
    node_id: str
    node_ids: list[str]


def create_init_message(body: Json) -> InitMessage:
    if body["type"] != "init":
        raise ValueError("expected 'init' message type")
    return InitMessage(
        type="init",
        msg_id=body["msg_id"],
        node_id=body["node_id"],
        node_ids=body["node_ids"],
    )


class Node:
    """Maelstrom node

    The node receives messages from stdin,
    sends to stdout, and prints any
    encountered errors to stderr.

    https://github.com/jepsen-io/maelstrom/blob/cb7f07239012d85d2c0595fd942ddb4613205905/doc/protocol.md#nodes-and-networks
    """

    def __init__(
        self,
        in_: TextIO | None = None,
        out: TextIO | None = None,
        err: TextIO | None = None,
    ):
        if in_ is None:
            self.in_ = sys.stdin
        if out is None:
            self.out = sys.stdout
        if err is None:
            self.err = sys.stderr

    def init(self, m: InitMessage): ...

    def run(self):
        for message in self.receive():
            self.send(message)

    def receive(self) -> str:
        yield from self.in_

    def send(self, message: str) -> None:
        print(message, file=self.out)

    def process_message(self, msg: Message): ...


if __name__ == "__main__":
    node = Node()
    node.run()
