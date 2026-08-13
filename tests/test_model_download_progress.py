import contextlib
import io

from app import suppress_library_output


def test_suppress_library_output_blocks_terminal_noise():
    captured = io.StringIO()

    with contextlib.redirect_stdout(captured):
        with suppress_library_output():
            print("terminal progress noise")

    assert "terminal progress noise" not in captured.getvalue()
