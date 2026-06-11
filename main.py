import sys
import json
import dataclasses
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
    """Responsible for doing the work requested by the message.

    Returns a payload which contains "type" attribute
    and other arbitrary attributes, see
    https://github.com/jepsen-io/maelstrom/blob/main/doc/protocol.md#message-bodies
    """

    type: str

    def __init__(self, node_delegate: Node) -> None:
        """Initialize with a Node instance for node-specific info e.g. msg_id counter."""

    def __call__(self, payload: MessageBody) -> MessageBody:
        """Handle a message with body of type returned by self.get_type"""


class EchoMessageHandler:
    type = "echo"

    def __init__(self, node_delegate: Node) -> None:
        self.node_delegate = node_delegate

    def __call__(self, payload: MessageBody) -> MessageBody:
        reply_payload = {}
        for key, value in payload.items():
            reply_payload[key] = value
        reply_payload["type"] = "echo_ok"
        reply_payload["msg_id"] = self.node_delegate.node_message_id
        reply_payload["in_reply_to"] = payload["msg_id"]
        return reply_payload


class Node:
    """Maelstrom node

    The node receives messages from stdin,
    sends to stdout, and prints any
    encountered errors to stderr.

    https://github.com/jepsen-io/maelstrom/blob/cb7f07239012d85d2c0595fd942ddb4613205905/doc/protocol.md#nodes-and-networks
    """

    def __init__(
        self,
        handlers: Sequence[type[MessageHandler]],
        in_: TextIO | None = None,
        out: TextIO | None = None,
        err: TextIO | None = None,
    ) -> None:
        if in_ is None:
            in_ = sys.stdin
        if out is None:
            out = sys.stdout
        if err is None:
            err = sys.stderr
        self.in_, self.out, self.err = in_, out, err
        self.handlers: Mapping[str, MessageHandler] = {}
        for handler in handlers:
            self.handlers[handler.type] = handler(node_delegate=self)
        self.node_id = "n1"  # since init not implemented
        self.node_message_id = 1  # TODO: implement msg_id counter

    def run(self) -> None:
        for request in self.receive():
            try:
                result = self.process(request)
            except MessageHandlerMissingError as exc:
                print(exc, file=self.err)
            else:
                self.reply(
                    src=self.node_id,
                    dest=request.src,
                    payload=result,
                )

    def reply(self, src: str, dest: str, payload: MessageBody) -> None:
        reply = Message(
            src=src,
            dest=dest,
            body=payload,
        )
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

    def send(self, message: Message) -> None:
        print(json.dumps(dataclasses.asdict(message)), file=self.out)

    def process(self, request: Message) -> MessageBody:
        """Process the request and generate the reply.

        :raises: MessageHandlerMissingError when no handler is found
                 for the message body type is passed
        """
        request_type = str(request.body.get("type", ""))
        handler = self.handlers.get(request_type)
        if handler is None:
            raise MessageHandlerMissingError("no handler for provided type")
        return handler(request.body)


if __name__ == "__main__":
    node = Node(handlers=[EchoMessageHandler])
    node.run()
