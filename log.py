import logging

def createLog(name, file):
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs INFO
    logHandlerFile = logging.FileHandler(file)
    logHandlerFile.setLevel(logging.INFO)

    # create console handler with a higher log level
    logHandlerCon = logging.StreamHandler()
    logHandlerCon.setLevel(logging.DEBUG)

    # Create formatter and add it to the handlers
    logFormat = logging.Formatter('%(asctime)s [%(levelname)s] : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logHandlerFile.setFormatter(logFormat)
    logHandlerCon.setFormatter(logFormat)

    # add the handlers to the logger
    logger.addHandler(logHandlerFile)
    logger.addHandler(logHandlerCon)

    return logger

