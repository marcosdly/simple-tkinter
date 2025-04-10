from typing import Union, final
from simple_tkinter.app import App
from simple_tkinter.state import State
from simple_tkinter.bases import HasChildren
from uuid import uuid4, UUID

@final
class Widget(HasChildren):
    def __init__(self, parent: Union["App", "Widget"]):
        self.parent = parent
        if isinstance(parent, App):
            self.app = parent
        else:
            self.app = parent.app
        self.instance_id:UUID = uuid4()
        self.state = State(self.instance_id)

        super().__init__()
