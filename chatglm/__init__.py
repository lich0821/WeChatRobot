import sys


class UnsupportedPythonVersionError(Exception):
    def __init__(self, error_msg: str):
        super().__init__(error_msg)


python_version_info = sys.version_info
if not sys.version_info >= (3, 9):
    msg = "当前Python版本: " + ".".join(map(str, python_version_info[:3])) + (', 需要python版本 >= 3.9, 前往下载: '
                                                                              'https://www.python.org/downloads/')
    raise UnsupportedPythonVersionError(msg)