import sys
import json
from dataclass import dataclass
from typing import TypedDict, Literal, TextIO, Iterator


type Json = dict[str, "Json"] | list["Json"] | str | int | float | bool | None


class InvalidMessage(Exception):
    """The message does not conform to the protocol"""


class MessageHandlerMissing(Exception):
    """No message handler for the provided type is registered"""


@dataclass
class Message:
    """Maelstrom message

    https://github.com/jepsen-io/maelstrom/blob/cb7f07239012d85d2c0595fd942ddb4613205905/doc/protocol.md#messages
    """

    src: str
    dest: str
    body: Json

    def __post_init__(self):
        if not self.src:
            raise InvalidMessage("src cannot be None or empty")
        if not self.dest:
            raise InvalidMessage("dest cannot be None or empty")
        if not body:
            raise InvalidMessage("body cannot be None or empty")


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

    def init(self): ...

    def run(self):
        for request in self.receive():
            reply = self.process(request)
            self.send(reply)

    def receive(self) -> Iterator[Message]:
        for line in self.in_:
            try:
                parsed = json.loads(line)
            except (JSONDecodeError, UnicodeDecodeError) as exc:
                print(exc, file=self.err)
                continue
            try:
                request = Message(parsed)
            except InvalidMessage as exc:
                print(exc, file=self.err)
                continue
            yield request

    def send(self, message: str) -> None:
        print(message, file=self.out)

    def process(self, request: Message):
        request_type = str(request.body.get("type", ""))
        # case "echo":
        #     ...
        # case "init":
        #     ...
        # case _:
        #     raise MessageHandlerMissing()


if __name__ == "__main__":
    node = Node()
    node.run()
