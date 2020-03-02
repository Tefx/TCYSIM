import os.path


def get_include():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)),
            "../libtcy/src/core")
        )
