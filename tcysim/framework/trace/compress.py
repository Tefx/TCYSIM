import msgpack
import os


class CompressDict:
    def __init__(self, file):
        self.file = file
        self._map = None
        self.idx = 0
        self.packer = None

    def compress(self, name):
        if self.packer is None:
            self.packer = msgpack.Packer()
        if self._map is None:
            self._map = {}
        if name not in self._map:
            self._map[name] = self.idx
            self.idx += 1
            self.file.write(self.packer.pack(name))
            # os.fsync(self.file.fileno())
        return self._map[name]

    def decompress(self, id):
        if self._map is None:
            unpacker = msgpack.Unpacker(self.file, use_list=False)
            self._map = tuple(unpacker)
        info = self._map[id]
        if isinstance(info, bytes):
            return info.decode("utf-8")
