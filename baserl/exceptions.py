"""
Module will define exceptions for the baserl module.
"""
class Impossible(Exception):
    """
    Exception raised when something impossible to be performed
    The reason is given as the exception message
    """

class QuitWithoutSaving(SystemExit):
   """Can be raised to exit the game without automatically saving."""