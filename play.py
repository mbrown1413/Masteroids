#!/usr/bin/python3

import sys
if sys.version_info < (3, 2):
    raise RuntimeError("Python version 3.2 or greater is required")

import masteroids.interface

if __name__ == "__main__":
    interface = masteroids.interface.GameInterface()
    interface.main_loop()
