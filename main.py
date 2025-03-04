"""This module starts and stopps the ssh-tunnel-service.

Raises:
    ServiceStopping: Custom Exception that does nothing other than being used to terminate all
    threads.
"""
import os
import sys
import time
import shutil
import signal
import yaml

from modules.keep_tunnel_alive import KeepTunnelAlive
from modules.log_process import LogProcess
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

    # check if config/config.yml exists. If not copy template to config location. load configuration
    # from config/config.yml
    config_file = f'{cwd}/config/config.yml'
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    if not os.path.isfile(config_file):
        shutil.copy2('templates/config.example.yml',config_file)
    with open(f'{cwd}/config/config.yml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)

    # create log directory and log object
    os.makedirs(config['log-path'], exist_ok=True)
    log_process = LogProcess(f'{config["log-path"]}/main.log', True)

    # load site configuration
    if not os.path.isfile(config['siteconfig']):
        log_process.log(f'Missing file "{config["siteconfig"]}"', 1)
        sys.exit(1)
    with open(config['siteconfig'], 'r', encoding='utf-8') as file:
        sites = yaml.safe_load(file)

    # empty array that holds all thread objects
    active_threads = []

    try:

        # create a thread for each site
        for siteconfig in sites.keys():
            if sites[siteconfig]['active']:
                sites[siteconfig]['sitename'] = siteconfig
                sites[siteconfig]['cwd'] = cwd
                # check if either identity-file or password has been defined for this site.
                if 'password' in sites[siteconfig] and 'identity-file' in sites[siteconfig]:
                    log_process.log('Can\'t have both, password and identity-file for site '+ \
                                    f'\'{siteconfig}\'. Skipping this site.', 1)
                    continue
                if 'password' not in sites[siteconfig] and 'identity-file' not in sites[siteconfig]:
                    log_process.log('Password or identity-file has to be set for site '+ \
                                    f'\'{siteconfig}\'. Skipping this site.', 1)
                    continue
                active_threads.append(KeepTunnelAlive(config['log-path'], sites[siteconfig]))

        # start threads
        for current_thread in active_threads:
            current_thread.start()

        # keep the main thread running
        if len(active_threads) > 0:
            while True:
                time.sleep(1)
        else:
            log_process.log('No active/working site configuration found. Exiting ...', 2)

    except ServiceStopping:
        # Terminate the running threads.
        # Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
        for current_thread in active_threads:
            current_thread.stop_flag.set()

        # wait for each thread to be closed
        for current_thread in active_threads:
            current_thread.join()

    log_process.log('Service stopped.')


# start main program
if __name__ == '__main__':
    main()
