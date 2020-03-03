import os

from tcysim.utils.lmp import SingleLMP
import msgpack

pack = msgpack.pack


class _LoggerForLMPManager:
    def __init__(self, fp, columns):
        self.fp = fp
        self.columns = columns

    def init(self):
        if isinstance(self.fp, str):
            self.fp = open(self.fp, "wb")
        pack(self.columns, self.fp)

    def finish(self):
        if hasattr(self.fp, "close"):
            self.fp.close()

    def write(self, *data):
        pack(data, self.fp)


class LoggingManagerBase(SingleLMP):
    def __init__(self):
        super(LoggingManagerBase, self).__init__()
        self.loggers = []

    def create_logger(self, fp_or_path, columns):
        logger = _LoggerForLMPManager(fp_or_path, columns)
        self.loggers.append(logger)
        return logger

    def run(self) -> None:
        for logger in self.loggers:
            logger.init()
        super(LoggingManagerBase, self).run()
        for logger in self.loggers:
            logger.finish()

class SingleProcessLogger(SingleLMP):
    def __init__(self, fp, columns=None, start=False):
        super(SingleProcessLogger, self).__init__()
        self.packer = None
        self.fp = fp
        self.columns = columns
        if start:
            self.start()

    def run(self) -> None:
        if isinstance(self.fp, str):
            dir_path = os.path.split(os.path.abspath(self.fp))[0]
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            self.fp = open(self.fp, "wb")
        self.packer = msgpack.Packer()
        if self.columns:
            self.fp.write(self.packer.pack(self.columns))
            # pack(self.columns, self.fp)
        super(SingleProcessLogger, self).run()
        if hasattr(self.fp, "close"):
            self.fp.close()

    def write(self, *data):
        self.fp.write(self.packer.pack(data))
        # pack(data, self.fp)
