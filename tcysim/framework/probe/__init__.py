from .action import ProbeAction
from .manager import ProbeManager
from .processor import ProbeProcessor


def on_probe(prob_name):
    def wrapper(func):
        return ProbeAction(prob_name, func)
    return wrapper