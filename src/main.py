import abc
from typing import override
import sys
import json
import dataclasses
from json import JSONDecodeError
from dataclasses import dataclass
from typing import TextIO, Iterator, Mapping, Sequence


type Json = Mapping[str, "Json"] | Sequence["Json"] | str | int | float | bool | None


type MessageBody = Mapping[str, Json]


def get_type(body: MessageBody) -> str:
    request_type = body.get("type")
    if isinstance(request_type, str):
        return request_type
    raise InvalidMessageError("type has to be a string")


def get_msg_id(body: MessageBody) -> int:
    msg_id = body.get("msg_id")
    if isinstance(msg_id, int):
        return msg_id
    raise InvalidMessageError("msg_id must be int")


class MessageHandlerMissingError(Exception):
    """No message handler for the provided type is registered"""

    @override
    def __str__(self) -> str:
        return "no message handler is registered for the type passed"


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

    def __post_init__(self) -> None:
        if not self.src:
            raise InvalidMessageError("src cannot be null or empty")
        if not self.dest:
            raise InvalidMessageError("dest cannot be null or empty")
        if not self.body:
            raise InvalidMessageError("body cannot be null or empty")
        if not isinstance(self.body, Mapping):
            raise InvalidMessageError("body has to be some type of mapping")


class RequestHandler:
    """Responsible for doing the work requested by the message.

    Returns a payload which contains "type" attribute
    and other arbitrary attributes, see
    https://github.com/jepsen-io/maelstrom/blob/main/doc/protocol.md#message-bodies
    """

    type: str
    reply_type: str

    def __init__(self, node: Node, request: MessageBody) -> None:
        """Initialize the handler with the request.

        This is where the validation happens.

        This is also when the response gets its unique id.

        Initialization can throw InvalidMessageError.
        If it doesn't, the rest of the class is going to have
        the invariant "request has a correct schema".
        """
        request_type = get_type(request)
        if request_type != self.type:
            raise InvalidMessageError
        self.node = node
        self.request = request
        self.response: dict[str, Json] = {
            "type": self.reply_type,
            "in_reply_to": get_msg_id(self.request),
            "msg_id": self.node.node_message_id,
        }


    def __call__(self) -> MessageBody:
        """Process a message body.

        Never throws an error because nothing is ever
        going wrong while processing a request.

        Returns a message reply body.
        """
        return self.response


class EchoRequestHandler(RequestHandler):
    type = "echo"
    reply_type = "echo_ok"

    def __call__(self) -> MessageBody:
        for key, value in self.request.items():
            if key not in self.response:
                self.response[key] = value
        return super().__call__()


class InitMessageHandler:
    type = "init"
    reply_type = "init_ok"

    # TODO: cliffhanger -- rewrite in terms of the new abstract class
    def __init__(self, node_delegate: Node) -> None:
        # TODO: validate init-specific schema
        self.node_delegate = node_delegate

    def __call__(self, payload: MessageBody) -> MessageBody:
        node_id = payload.get("node_id")
        if isinstance(node_id, str):
            self.node_delegate.node_id = node_id
        else:
            raise TypeError("node_id must be present and be a string")
        node_ids = payload.get("node_ids")
        if isinstance(node_ids, list):
            # until we define input/output schema for MessageHandler,
            # pyrefly: ignore [bad-assignment]
            self.node_delegate.node_neighbor_ids = node_ids
        else:
            raise TypeError("node_ids must be present and be a list of strings")
        return {}


class Node:
    """Maelstrom node

    The node receives messages from stdin,
    sends to stdout, and prints any
    encountered errors to stderr.

    https://github.com/jepsen-io/maelstrom/blob/cb7f07239012d85d2c0595fd942ddb4613205905/doc/protocol.md#nodes-and-networks
    """

    node_id: str
    node_neighbor_ids: Sequence[str]

    def __init__(
        self,
        handlers: Sequence[type[RequestHandler]],
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
        self.handlers: Mapping[str, type[RequestHandler]] = {}
        for handler in handlers:
            self.handlers[handler.type] = handler
        self.node_id = "n1"
        self.node_neighbor_ids = []
        self._node_message_id = -1

    @property
    def node_message_id(self) -> int:
        self._node_message_id += 1
        return self._node_message_id

    def run(self) -> None:
        for request in self.receive():
            try:
                handler = self.choose_request_handler(request)
            except MessageHandlerMissingError as exc:
                self.send_err(exc)
                continue
            try:
                handle = handler(node, request.body)
            except InvalidMessageError as exc:
                self.send_err(exc)
                continue
            reply = handle()
            if reply is not None:
                self.send(
                    dest=request.src,
                    payload=reply,
                )

    def send(self, dest: str, payload: MessageBody) -> None:
        message = Message(
            src=self.node_id,
            dest=dest,
            body=payload,
        )
        print(json.dumps(dataclasses.asdict(message)), file=self.out)

    def send_err(self, exc: Exception) -> None:
        print(exc, file=self.err)

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

    def process(self, request: Message) -> MessageBody:
        """Process the request and generate the reply.

        :raises: MessageHandlerMissingError when no handler is found
                 for the message body type is passed
        """
        handler = self.choose_request_handler(request)
        return handler(request.body)

    def choose_request_handler(self, request: Message) -> type[RequestHandler]:
        """Chooses a handler among the registered ones based of request body type.

        Throws MessageHandlerMissingError in case the type is incorrect or there's
        no handler registered for the type.
        """
        try:
            request_type = get_type(request.body)
        except InvalidMessageError as exc:
            raise MessageHandlerMissingError from exc
        handler = self.handlers.get(request_type)
        if handler is None:
            raise MessageHandlerMissingError
        return handler


if __name__ == "__main__":
    node = Node(handlers=[EchoRequestHandler, InitMessageHandler])
    node.run()
