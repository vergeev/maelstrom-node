import sys
import json
from json import JSONDecodeError
from dataclasses import dataclass
from typing import TextIO, Iterator, Mapping, Sequence, Protocol


type Json = Mapping[str, "Json"] | Sequence["Json"] | str | int | float | bool | None
type MessageBody = Mapping[str, Json]


class MessageHandlerMissingError(Exception):
    """No message handler for the provided type is registered"""


class InvalidMessageError(Exception):
    """The message does not conform to the protocol"""


@dataclass
class Message:
    """Maelstrom message

    https://github.com/jepsen-io/maelstrom/blob/cb7f07239012d85d2c0595fd942ddb4613205905/doc/protocol.md#messages
    """

    src: str
    dest: str
    body: MessageBody

    def __post_init__(self):
        if not self.src:
            raise InvalidMessageError("src cannot be null or empty")
        if not self.dest:
            raise InvalidMessageError("dest cannot be null or empty")
        if not self.body:
            raise InvalidMessageError("body cannot be null or empty")
        if not isinstance(self.body, Mapping):
            raise InvalidMessageError("body has to be some type of mapping")


class MessageHandler(Protocol):
    type: str

    def __call__(self, message: Message) -> str:
        """Handle a message with body of type returned by self.get_type"""


class EchoMessageHandler:
    type = "echo"

    def __call__(self, message: Message) -> str:
        return f"PARSED: {message.src}|{message.dest}|{self.type}"


class Node:
    """Maelstrom node

    The node receives messages from stdin,
    sends to stdout, and prints any
    encountered errors to stderr.

    https://github.com/jepsen-io/maelstrom/blob/cb7f07239012d85d2c0595fd942ddb4613205905/doc/protocol.md#nodes-and-networks
    """

    def __init__(
        self,
        handlers: Sequence[MessageHandler],
        in_: TextIO | None = None,
        out: TextIO | None = None,
        err: TextIO | None = None,
    ):
        if in_ is None:
            in_ = sys.stdin
        if out is None:
            out = sys.stdout
        if err is None:
            err = sys.stderr
        self.in_, self.out, self.err = in_, out, err
        self.handlers: Mapping[str, MessageHandler] = {}
        for handler in handlers:
            self.handlers[handler.type] = handler

    def run(self):
        for request in self.receive():
            try:
                reply = self.process(request)
            except MessageHandlerMissingError as exc:
                print(exc, file=self.err)
            else:
                self.send(reply)

    def receive(self) -> Iterator[Message]:
        """Get new message.

        Together with send, responsible
        for handling the representation logic of
        the protocol: dealing with stdin and json,
        so that other parts of the code do not have to
        deal with them or know about them.
        """
        for line in self.in_:
            try:
                parsed = json.loads(line)
            except (JSONDecodeError, UnicodeDecodeError) as exc:
                print(exc, file=self.err)
                continue
            try:
                request = Message(**parsed)
            except (TypeError, InvalidMessageError) as exc:
                print(exc, file=self.err)
                continue
            yield request

    def send(self, message: str) -> None:
        print(message, file=self.out)

    def process(self, request: Message) -> str:
        """Process the request and generate the reply.

        :raises: MessageHandlerMissingError when no handler is found
                 for the message body type is passed
        """
        request_type = str(request.body.get("type", ""))
        handler = self.handlers.get(request_type)
        if handler is None:
            raise MessageHandlerMissingError("no handler for provided type")
        return handler(request)


if __name__ == "__main__":
    node = Node(handlers=[EchoMessageHandler()])
    node.run()
