#!/usr/bin/env python3
"""
A file to start the server
"""
from __init__ import app
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    if app.config['DEBUG']:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : %(name)s : %(levelname)s : %(message)s')
        logger.debug('Running in debug mode')
        logger.debug(app.config)
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(name)s : %(levelname)s : %(message)s')
        logger.info('Running in production mode')
    app.run(host='0.0.0.0', threaded=True)
