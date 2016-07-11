"""
Unit tests for nyx.panel.interpreter.
"""

import unittest

import nyx.curses
import nyx.panel.interpreter
import test

EXPECTED_PANEL = """
Control Interpreter:
>>> to use this panel press enter
""".strip()

EXPECTED_PANEL_INPUT_MODE = """
Control Interpreter (enter "/help" for usage or a blank line to stop):
>>> to use this panel press enter
""".strip()

EXPECTED_MULTILINE_PANEL = """
Control Interpreter:
>>> GETINFO version
250-version=0.2.4.27 (git-412e3f7dc9c6c01a)
""".strip()

EXPECTED_SCROLLBAR_PANEL = ' |>>> to use this panel press enter'


class TestInterpreter(unittest.TestCase):
  def test_ansi_to_output(self):
    ansi_text = '\x1b[32;1mthis is some sample text'
    output_line, attrs = nyx.panel.interpreter.ansi_to_output(ansi_text, [])

    self.assertEqual('this is some sample text', output_line[0][0])
    self.assertEqual('Green', output_line[0][1])
    self.assertEqual('Bold', output_line[0][2])
    self.assertEqual(['Green', 'Bold'], attrs)

  def test_format_input(self):
    user_input = 'getinfo'
    output = nyx.panel.interpreter.format_input(user_input)
    self.assertEqual(2, len(output))
    self.assertEqual(('>>> ', 'Green', 'Bold'), output[0])
    self.assertEqual(('getinfo ', 'Green', 'Bold'), output[1])

    user_input = 'getinfo version'
    output = nyx.panel.interpreter.format_input(user_input)
    self.assertEqual(3, len(output))
    self.assertEqual(('>>> ', 'Green', 'Bold'), output[0])
    self.assertEqual(('getinfo ', 'Green', 'Bold'), output[1])
    self.assertEqual(('version', 'Cyan', 'Bold'), output[2])

    user_input = '/help'
    output = nyx.panel.interpreter.format_input(user_input)
    self.assertEqual(2, len(output))
    self.assertEqual(('>>> ', 'Green', 'Bold'), output[0])
    self.assertEqual(('/help', 'Magenta', 'Bold'), output[1])

  def test_panel_name(self):
    panel = nyx.panel.interpreter.InterpreterPanel()
    self.assertEqual(panel.get_name(), 'interpreter')

  def test_rendering_panel(self):
    panel = nyx.panel.interpreter.InterpreterPanel()
    self.assertEqual(EXPECTED_PANEL, test.render(panel.draw).content)

    panel._is_input_mode = True
    self.assertEqual(EXPECTED_PANEL_INPUT_MODE, test.render(panel.draw).content)

  def test_rendering_multiline_panel(self):
    panel = nyx.panel.interpreter.InterpreterPanel()
    panel.prompt_line = [[('>>> ', 'Green', 'Bold'), ('GETINFO', 'Green', 'Bold'), (' version', 'Cyan')]]
    panel.prompt_line.append([('250-version=0.2.4.27 (git-412e3f7dc9c6c01a)', 'Blue')])
    self.assertEqual(EXPECTED_MULTILINE_PANEL, test.render(panel.draw).content)

  def test_scrollbar(self):
    panel = nyx.panel.interpreter.InterpreterPanel()
    self.assertIsInstance(panel._scroller, nyx.curses.Scroller)

    height = panel.get_preferred_size()[0]
    panel._last_content_height = height
    output_lines = test.render(panel.draw).content.split('\n')
    self.assertEqual(height, len(output_lines))
    self.assertEqual(EXPECTED_SCROLLBAR_PANEL, output_lines[1])

  def test_key_handlers(self):
    panel = nyx.panel.interpreter.InterpreterPanel()
    output = panel.key_handlers()
    self.assertEqual(2, len(output))
    self.assertEqual('enter', output[0].key)
    self.assertEqual('arrows', output[1].key)
