import io
import pytest
from typing import Sequence
from maelstrom_node.main import Node, EchoMessageHandler, MessageHandler


@pytest.mark.parametrize(
    "intext, outtext, errtext, handlers",
    [
        # Node tests
        pytest.param(
            "\n",
            "",
            "Expecting value: line 2 column 1 (char 1)\n",
            [],
            id="empty_line",
        ),
        pytest.param(
            "\n\n",
            "",
            "Expecting value: line 2 column 1 (char 1)\n"
            "Expecting value: line 2 column 1 (char 1)\n",
            [],
            id="processes_messages_after_error",
        ),
        pytest.param(
            "{}\n",
            "",
            "Message.__init__() missing 3 required positional arguments: 'src', 'dest', and 'body'\n",
            [],
            id="no_attributes",
        ),
        pytest.param(
            '{"src": null, "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "",
            "src cannot be null or empty\n",
            [],
            id="null_src",
        ),
        pytest.param(
            '{"src": "", "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "",
            "src cannot be null or empty\n",
            [],
            id="empty_src",
        ),
        pytest.param(
            '{"src": "c1", "dest": null, "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "",
            "dest cannot be null or empty\n",
            [],
            id="null_dest",
        ),
        pytest.param(
            '{"src": "c1", "dest": "", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "",
            "dest cannot be null or empty\n",
            [],
            id="empty_dest",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": null}\n',
            "",
            "body cannot be null or empty\n",
            [],
            id="null_body",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": ""}\n',
            "",
            "body cannot be null or empty\n",
            [],
            id="empty_body",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": ["echo"]}\n',
            "",
            "body has to be some type of mapping\n",
            [],
            id="body_not_map",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": {"type": ""}}\n',
            "",
            "no handler for provided type\n",
            [],
            id="body_type_empty",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": {"type": 1}}\n',
            "",
            "type has to be a string\n",
            [],
            id="body_type_non_string",
        ),
        # EchoMessageHandler tests
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            '{"src": "n1", "dest": "c1", "body": {"msg_id": 1, "type": "echo_ok", "echo": "hello there", "in_reply_to": 1}}\n',
            "",
            [EchoMessageHandler],
            id="single_line_echo_handler_test",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n'
            '{"src": "c2", "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            '{"src": "n1", "dest": "c1", "body": {"msg_id": 1, "type": "echo_ok", "echo": "hello there", "in_reply_to": 1}}\n'
            '{"src": "n1", "dest": "c2", "body": {"msg_id": 2, "type": "echo_ok", "echo": "hello there", "in_reply_to": 1}}\n',
            "",
            [EchoMessageHandler],
            id="two_line_echo_handler_test",
        ),
        pytest.param(
            "\n"
            '{"src": "c1", "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            '{"src": "n1", "dest": "c1", "body": {"msg_id": 1, "type": "echo_ok", "echo": "hello there", "in_reply_to": 1}}\n',
            "Expecting value: line 2 column 1 (char 1)\n",
            [EchoMessageHandler],
            id="parsed_after_error_echo_handler_test",
        ),
    ],
)
def test_node(
    intext: str, outtext: str, errtext: str, handlers: Sequence[type[MessageHandler]]
) -> None:
    stdin_mock = io.StringIO(intext)
    stdout_mock = io.StringIO()
    stderr_mock = io.StringIO()
    node = Node(
        handlers=handlers,
        in_=stdin_mock,
        out=stdout_mock,
        err=stderr_mock,
    )

    node.run()

    assert stdout_mock.getvalue() == outtext
    assert stderr_mock.getvalue() == errtext
