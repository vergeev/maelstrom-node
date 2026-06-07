import io
import pytest
from main import Node, EchoMessageHandler


@pytest.mark.parametrize(
    "intext, outtext, errtext",
    [
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "PARSED: c1|n1|echo\n",
            "",
            id="single_line",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n'
            '{"src": "c2", "dest": "n2", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "PARSED: c1|n1|echo\nPARSED: c2|n2|echo\n",
            "",
            id="two_line",
        ),
        pytest.param(
            "\n",
            "",
            "Expecting value: line 2 column 1 (char 1)\n",
            id="empty_line",
        ),
        pytest.param(
            "\n"
            '{"src": "c1", "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "PARSED: c1|n1|echo\n",
            "Expecting value: line 2 column 1 (char 1)\n",
            id="parsed_after_error",
        ),
        pytest.param(
            "{}\n",
            "",
            "Message.__init__() missing 3 required positional arguments: 'src', 'dest', and 'body'\n",
            id="no_attributes",
        ),
        pytest.param(
            '{"src": null, "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "",
            "src cannot be null or empty\n",
            id="null_src",
        ),
        pytest.param(
            '{"src": "", "dest": "n1", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "",
            "src cannot be null or empty\n",
            id="empty_src",
        ),
        pytest.param(
            '{"src": "c1", "dest": null, "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "",
            "dest cannot be null or empty\n",
            id="null_dest",
        ),
        pytest.param(
            '{"src": "c1", "dest": "", "body": {"msg_id": 1, "type": "echo", "echo": "hello there"}}\n',
            "",
            "dest cannot be null or empty\n",
            id="empty_dest",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": null}\n',
            "",
            "body cannot be null or empty\n",
            id="null_body",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": ""}\n',
            "",
            "body cannot be null or empty\n",
            id="empty_body",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": ["echo"]}\n',
            "",
            "body has to be some type of mapping\n",
            id="body_not_map",
        ),
        pytest.param(
            '{"src": "c1", "dest": "n1", "body": {"type": ""}}\n',
            "",
            "no handler for provided type\n",
            id="body_type_empty",
        ),
    ],
)
def test_node(intext, outtext, errtext):
    stdin_mock = io.StringIO(intext)
    stdout_mock = io.StringIO()
    stderr_mock = io.StringIO()
    node = Node(
        handlers=[EchoMessageHandler()],
        in_=stdin_mock,
        out=stdout_mock,
        err=stderr_mock,
    )

    node.run()

    assert stdout_mock.getvalue() == outtext
    assert stderr_mock.getvalue() == errtext
