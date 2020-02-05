from LMP.single import SingleLMP
from umsgpack import pack

class _LoggerForLMPManager:
    def __init__(self, fp, columns):
        self.fp = fp
        self.columns = columns

    def init(self):
        if isinstance(self.fp, str):
            self.fp = open(self.fp, "wb")

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
    remote_names = ["log"]

    def __init__(self, fp, columns):
        super(SingleProcessLogger, self).__init__()
        self.fp = fp
        self.columns = columns

    def run(self) -> None:
        if isinstance(self.fp, str):
            self.fp = open(self.fp, "wb")
        super(SingleProcessLogger, self).run()
        if hasattr(self.fp, "close"):
            self.fp.close()

    def write(self, *data):
        pack(data, self.fp)
