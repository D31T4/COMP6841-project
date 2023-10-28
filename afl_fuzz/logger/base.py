from abc import ABC

class ILogger(ABC):
    def write(self, msg: str):
        '''
        write log

        Arguments:
        ---
        - msg: log message
        '''
        pass

devNullLogger = ILogger()