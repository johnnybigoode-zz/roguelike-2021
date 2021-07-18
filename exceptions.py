class Impossible(Exception):
    """exception raised when something impossible to be performed

    the reason is given as the exception message"""


class QuitWithoutSaving(SystemExit):
    """can be raised to exit game without automatically saving"""
