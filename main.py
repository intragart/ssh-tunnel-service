import os
import yaml
import time
import signal

from modules.KeepTunnelAlive import KeepTunnelAlive
from modules.ServiceStopping import ServiceStopping

def service_stop(signum, frame):
    print(f'Received signal {signum}')
    raise ServiceStopping

def main():

    # set handler for asynchronous events
    signal.signal(signal.SIGTERM, service_stop)
    signal.signal(signal.SIGINT, service_stop)

    # get current working dir
    cwd = os.getcwd()

    # load configuration from config.yml
    with open(f'{cwd}/config.yml', 'r') as file:
        config = yaml.safe_load(file)

    # load site configuration
    with open(f'{cwd}/{config["siteconfig"]}', 'r') as file:
        sites = yaml.safe_load(file)

    # create log directory
    os.makedirs(f'{cwd}/{config["log-path"]}', exist_ok=True)

    # empty array that holds all thread objects
    active_threads = []

    try:

        # create a thread for each site
        for siteconfig in sites.keys():
            if sites[siteconfig]['active'] == True:
                active_threads.append(KeepTunnelAlive(f'{cwd}/{config["log-path"]}', sites[siteconfig]))

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