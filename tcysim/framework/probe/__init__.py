from .action import ProbeActionTemplate
from .manager import ProbeManager
from .processor import ProbeProcessor


def on_probe(probe_name):
    def wrapper(func):
        return ProbeActionTemplate(probe_name, func)
    return wrapper