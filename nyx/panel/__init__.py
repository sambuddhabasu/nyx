# Copyright 2010-2016, Damian Johnson and The Tor Project
# See LICENSE for licensing information

"""
Panels consisting the nyx interface.

**Module Overview:**

::

  KeyHandler - keyboard input a panel accepts
    +- handle - triggers the keyboard action

  Panel - panel within the interface
    |- DaemonPanel - panel that triggers actions at a set rate
    |  |- run - starts triggering daemon actions
    |  +- stop - stops triggering daemon actions
    |
    |- get_top - top position we're rendered into on the screen
    |- set_top - sets top position within the screen
    |- get_height - height occupied by the panel
    |
    |- set_visible - toggles panel visiblity
    |- key_handlers - keyboard input accepted by the panel
    +- redraw - renders the panel content
"""

import collections
import inspect
import threading
import time

import nyx.curses

__all__ = [
  'config',
  'connection',
  'graph',
  'header',
  'interpreter',
  'log',
  'torrc',
]


class KeyHandler(collections.namedtuple('Help', ['key', 'description', 'current'])):
  """
  Action that can be taken via a given keybinding.

  :var str key: key the user can press
  :var str description: description of what it does
  :var str current: optional current value

  :param str key: key the user can press
  :param str description: description of what it does
  :param func action: action to be taken, this can optionally take a single
    argument which is the keypress
  :param str current: current value to be displayed
  :param func key_func: custom function to determine if this key was pressed
  """

  def __new__(self, key, description = None, action = None, current = None, key_func = None):
    instance = super(KeyHandler, self).__new__(self, key, description, current)
    instance._action = action
    instance._key_func = key_func
    return instance

  def handle(self, key):
    """
    Triggers action if our key was pressed.

    :param nyx.curses.KeyInput key: keypress to be matched against
    """

    if self._action:
      is_match = self._key_func(key) if self._key_func else key.match(self.key)

      if is_match:
        if inspect.getargspec(self._action).args == ['key']:
          self._action(key)
        else:
          self._action()


class Panel(object):
  """
  Panel within the nyx interface.
  """

  def __init__(self):
    self._top = 0
    self._visible = False

    self._last_draw_top = 0
    self._last_draw_size = nyx.curses.Dimensions(0, 0)

  def get_top(self):
    """
    Provides our top position in the overall screen.

    :returns: **int** with the top coordinate
    """

    return self._top

  def set_top(self, top):
    """
    Changes the position where we're rendered in the screen.

    :param int top: top position within the sceen
    """

    self._top = top

  def get_height(self):
    """
    Provides the height occupied by this panel.

    :returns: **int** for the height of the panel
    """

    return max(0, nyx.curses.screen_size().height - self._top)

  def set_visible(self, is_visible):
    """
    Toggles if the panel is visible or not.

    :param bool is_visible: shows panel if **True**, hides otherwise
    """

    self._visible = is_visible

  def key_handlers(self):
    """
    Provides keyboard input this panel supports.

    :returns: **tuple** of :class:`~nyx.panel.KeyHandler` instances
    """

    return ()

  def redraw(self, force = True):
    """
    Renders our panel's content to the screen.

    :param bool force: if **False** only redraws content if the panel's
      dimensions have changed
    """

    if not self._visible:
      return  # not currently visible

    if not force and self._last_draw_top == self._top:
      draw_dimension = self._last_draw_size
    else:
      draw_dimension = None  # force redraw

    self._last_draw_top = self._top
    self._last_draw_size = nyx.curses.draw(self._draw, top = self._top, height = self.get_height(), draw_if_resized = draw_dimension)

  def _draw(self, subwindow):
    pass


class DaemonPanel(Panel, threading.Thread):
  """
  Panel that triggers its _update() method at a set rate.
  """

  def __init__(self, update_rate):
    Panel.__init__(self)
    threading.Thread.__init__(self)
    self.setDaemon(True)

    self._pause_condition = threading.Condition()
    self._halt = False  # terminates thread if true
    self._update_rate = update_rate

  def _update(self):
    pass

  def run(self):
    """
    Performs our _update() action at the given rate.
    """

    import nyx.controller

    last_ran = -1
    nyx_controller = nyx.controller.get_controller()

    while not self._halt:
      if nyx_controller.is_paused() or (time.time() - last_ran) < self._update_rate:
        with self._pause_condition:
          if not self._halt:
            self._pause_condition.wait(0.2)

        continue  # done waiting, try again

      self._update()
      last_ran = time.time()

  def stop(self):
    """
    Halts further resolutions and terminates the thread.
    """

    with self._pause_condition:
      self._halt = True
      self._pause_condition.notifyAll()
