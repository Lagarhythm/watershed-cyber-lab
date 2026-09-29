from pathlib import Path
import anywidget
import traitlets
from .engine import Simulation

class WatershedSimulation(anywidget.AnyWidget):
    """One isolated Python simulation per widget/kernel, with a local browser UI."""
    _esm = Path(__file__).parent / 'app.js'
    _css = Path(__file__).parent / 'style.css'
    state = traitlets.Dict().tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = Simulation()
        self.state = self.engine.snapshot()
        self.on_msg(self._action)

    def _action(self, widget, content, buffers):
        self.engine.dispatch(content)
        self.state = self.engine.snapshot()
