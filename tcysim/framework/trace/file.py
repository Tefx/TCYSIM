import os
import shutil


class FileTree:
    def __init__(self, path, erase=False):
        self.path = path
        self.root = {}

        if os.path.exists(self.path):
            if erase:
                shutil.rmtree(self.path)
                os.makedirs(self.path)
        else:
            os.makedirs(self.path)

    def close_files(self, d=None):
        if d is None:
            d = self.root
        for item in d.values():
            if isinstance(item, dict):
                self.close_files(item)
            else:
                item.close()

    def __del__(self):
        self.close_files(self.root)

    def get_file_w(self, *names):
        path = self.path
        d = self.root
        for name in names[:-1]:
            path = os.path.join(path, str(name))
            if name not in d:
                os.makedirs(path)
                d[name] = {}
            d = d[name]
        name = names[-1]
        if name not in d:
            file_path = os.path.join(path, str(name))
            d[name] = open(file_path, "wb", buffering=0)
        return d[name]

    def get_file_r(self, *names):
        path = self.path
        d = self.root
        for name in names[:-1]:
            path = os.path.join(path, str(name))
            if not os.path.exists(path):
                return None
            if name not in d:
                d[name] = {}
            d = d[name]
        name = names[-1]
        if name not in d:
            file_path = os.path.join(path, str(name))
            if not os.path.exists(file_path):
                return None
            d[name] = open(file_path, "rb")
        return d[name]
