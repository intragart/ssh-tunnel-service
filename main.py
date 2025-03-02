"""This module starts and stopps the ssh-tunnel-service.

Raises:
    ServiceStopping: Custom Exception that does nothing other than being used to terminate all
    threads.
"""
import os
import time
import signal
import yaml

from modules.keep_tunnel_alive import KeepTunnelAlive
from modules.service_stopping import ServiceStopping

def service_stop(signum, frame):
    """This function is being called when the program is being terminated. For example when the user
    presses Ctrl+C. To terminate all threads within the process a custom exception is being called.

    Args:
        signum (int): Received signal number to terminate all threads.
        frame (frame): Received frame objekt to terminate all threads.

    Raises:
        ServiceStopping: Custom Exception that does nothing other than being used to terminate all
        threads.
    """
    print(f'Received signal {signum}, {frame}')
    raise ServiceStopping


def main():
    """This function reads all config items, creates needed subdirectories and starts the individual
    threads for each site. This main thread keeps running until exception ServiceStopping is being
    called to terminate each thread.
    """
    # set handler for asynchronous events
    signal.signal(signal.SIGTERM, service_stop)
    signal.signal(signal.SIGINT, service_stop)

    # get current working dir
    cwd = os.path.dirname(__file__)

    # load configuration from config.yml
    with open(f'{cwd}/config/config.yml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)

    # load site configuration
    with open(config['siteconfig'], 'r', encoding='utf-8') as file:
        sites = yaml.safe_load(file)

    # create log directory
    os.makedirs(config['log-path'], exist_ok=True)

    # empty array that holds all thread objects
    active_threads = []

    try:

        # create a thread for each site
        for siteconfig in sites.keys():
            if sites[siteconfig]['active']:
                active_threads.append(KeepTunnelAlive(config['log-path'], sites[siteconfig]))

        # start threads
        for current_thread in active_threads:
            current_thread.start()

        # keep the main thread running
        while True:
            time.sleep(1)

    except ServiceStopping:
        # Terminate the running threads.
        # Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
        for current_thread in active_threads:
            current_thread.stop_flag.set()

        # wait for each thread to be closed
        for current_thread in active_threads:
            current_thread.join()

    print('Service stopped.')


# start main program
if __name__ == '__main__':
    main()
