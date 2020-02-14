from multiprocessing import SimpleQueue as Queue, Process
import umsgpack
# msgpack.compatibility = True

pack = umsgpack.pack


class LogStream(Process):
    def __init__(self, fp, columns):
        super(LogStream, self).__init__()
        self.fp = fp
        self.queue = Queue()
        self.columns = columns

    def finish(self):
        self.queue.put(None)
        self.join()
        self.fp.close()

    def run(self) -> None:
        if isinstance(self.fp, str):
            self.fp = open(self.fp, "wb")
        pack(self.columns, self.fp)
        while True:
            data = self.queue.get()
            if data is None:
                break
            else:
                pack(data, self.fp)

    def write(self, *data):
        self.queue.put(data)


class StreamLoggingManager(Process):
    class Logger:
        def __init__(self, queue, idx, fp, columns):
            self.queue = queue
            self.fp = fp
            self.columns = columns
            self.idx = idx

        def init(self):
            if isinstance(self.fp, str):
                self.fp = open(self.fp, "wb")
            pack(self.columns, self.fp)

        def write(self, *data):
            self.queue.put((self.idx, data))

        def save(self, data):
            pack(data, self.fp)

        def finish(self):
            if not isinstance(self.fp, str):
                self.fp.close()

    def __init__(self):
        super(StreamLoggingManager, self).__init__()
        self.queue = Queue()
        self.loggers = []

    def create_logger(self, fp_or_path, columns):
        logger = self.Logger(self.queue, len(self.loggers), fp_or_path, columns)
        self.loggers.append(logger)
        return logger

    def finish(self):
        self.queue.put((None, None))
        self.join()
        for logger in self.loggers:
            logger.finish()

    def run(self) -> None:
        for logger in self.loggers:
            logger.init()
        while True:
            idx, data = self.queue.get()
            if idx is None:
                break
            else:
                self.loggers[idx].save(data)
        for logger in self.loggers:
            logger.finish()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()


