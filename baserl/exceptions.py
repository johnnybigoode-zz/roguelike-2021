class Impossible(Exception):
    """exception raised when something impossible to be performed
    
    the reason is given as the exception message"""

class QuitWithoutSaving(SystemExit):
   """Can be raised to exit the game without automatically saving."""