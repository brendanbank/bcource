#!/usr/bin/env python3

import time
from bcource.automation import init_app_scheduler, start_app_sscheduler
import config
from bcource.automation.lock import acquire_socket_lock, release_socket_lock
import config
import sys
import logging
from bcource import create_app
logger = logging.getLogger(__name__)


def main():
    app_config = config.Config()
    
    # lock
    lock_socket = acquire_socket_lock(app_config.BCOURSE_LOCK_HOST, app_config.BCOURSE_LOCK_PORT)
    if not lock_socket:
        sys.exit (1)
    
    app = create_app()
    app_scheduler = start_app_sscheduler()

    init_app_scheduler(app, app_scheduler)
    # keep it running
    
    try:
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nScript interrupted by user.")
    finally:
        release_socket_lock(lock_socket)
        logger.info("Script finished.")


if __name__ == "__main__":
    main()
