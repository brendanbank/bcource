import socket
import logging
logger = logging.getLogger(__name__)

# Choose a port that is unlikely to be used by other applications.
# It should be > 1023 (non-privileged ports).

def acquire_socket_lock(LOCK_HOST,LOCK_PORT):
    try:
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set SO_REUSEADDR to allow the socket to be bound to a port in TIME_WAIT state
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the host and port
        sock.bind((LOCK_HOST, LOCK_PORT))
        logger.info(f"Socket lock acquired on {LOCK_HOST}:{LOCK_PORT}")
        return sock
    except socket.error as e:
        logger.info(f"Could not acquire socket lock on {LOCK_HOST}:{LOCK_PORT}. Another instance might be running.")
        logger.info(f"Error: {e}")
        return None

def release_socket_lock(sock):
    if sock:
        sock.close()
        logger.info(f"Socket lock released")
        
