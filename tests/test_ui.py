import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import ui


class UiWidthTests(unittest.TestCase):
    def test_terminal_width_clamps_to_narrow_terminal(self):
        with patch.object(ui.shutil, "get_terminal_size", return_value=ui.os.terminal_size((36, 24))):
            self.assertEqual(ui.terminal_width(60), 32)

    def test_header_and_question_use_narrow_terminal_width(self):
        output = io.StringIO()
        with patch.object(ui.shutil, "get_terminal_size", return_value=ui.os.terminal_size((36, 24))):
            with redirect_stdout(output):
                ui.header("A very long header that must fit")
                ui.display_question(1, "Storage", "Which option is correct?", ["A", "B", "C", "D"])

        lines = [line for line in output.getvalue().splitlines() if line]
        plain_lines = [ui.strip_ansi(line) for line in lines]
        self.assertTrue(all(len(line) <= 36 for line in plain_lines))

