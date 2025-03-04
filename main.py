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


def create_siteconfig_from_env(target_file):
    """This function creates a siteconfig.yml file based on available environment variables. This
    function is only intended to be executed within a docker container with a configuration through
    environment variables

    Args:
        target_file (str): absolute or relative path and filename of the desired siteconfig.yml file
    """
    with open(target_file, 'w', encoding='utf-8') as yml_site:
        # The used docker base image has the following env variables build in:
        # HOSTNAME, HOME, GPG_KEY, PYTHON_SHA256, TERM, PATH, LANG, PYTHON_VERSION, PWD
        yml_site.write('---\n')
        yml_site.write('default:\n')
        yml_site.write('  active: True\n')

        # FQDN is mandatory
        yml_site.write(f'  fqdn: {os.getenv("FQDN")}\n')

        if os.getenv('SSH_PORT') is not None:
            yml_site.write(f'  ssh-port: {os.getenv("SSH_PORT")}\n')

        # USER is mandatory
        yml_site.write(f'  user: {os.getenv("USER")}\n')

        if os.getenv('PASSWORD') is not None:
            yml_site.write(f'  password: {os.getenv("PASSWORD")}\n')

        if os.getenv('IDENTITY_FILE') is not None:
            yml_site.write(f'  identity-file: {os.getenv("IDENTITY_FILE")}\n')

        if os.getenv('HOSTKEY') is not None:
            yml_site.write(f'  hostkey: {os.getenv("HOSTKEY")}\n')

        # the contents for local-ports are a list. The environment variable is expected to be a
        # comma seperated list of values.
        if os.getenv('LOCAL_PORTS') is not None:
            yml_site.write('  local-ports:\n')
            for list_item in os.getenv('LOCAL_PORTS').split(','):
                yml_site.write(f'    - {list_item}\n')

        # the contents for remote-ports are a list. The environment variable is expected to be a
        # comma seperated list of values.
        if os.getenv('REMOTE_PORTS') is not None:
            yml_site.write('  remote-ports:\n')
            for list_item in os.getenv('REMOTE_PORTS').split(','):
                yml_site.write(f'    - {list_item}\n')

        # the contents for ssh options are a list. The environment variable is expected to be a
        # comma seperated list of values. keys and values are seperated by double digits ':' with no
        # space in between.
        if os.getenv('OPTIONS') is not None:
            yml_site.write('  options:\n')
            for list_item in os.getenv('OPTIONS').split(','):
                cleaned_item = list_item.replace(': ', ':')
                split_item = cleaned_item.split(':')
                yml_site.write(f'    - {split_item[0]}: {split_item[1]}\n')


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

    # detect if docker container is using environment variables
    docker_with_env = False
    if os.getenv('FQDN') is not None and os.getenv('DOCKER_CONTAINER') is not None:
        docker_with_env = True

    # check if config/config.yml exists or if environment variables are being used. If no config.yml
    # exists or environment variables are being used copy template to config location.
    config_file = f'{cwd}/config/config.yml'
    config_was_copied = False
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    if not os.path.isfile(config_file) or docker_with_env:
        config_was_copied = True
        shutil.copy2('templates/config.example.yml',config_file)

    # load configuration from config/config.yml
    with open(f'{cwd}/config/config.yml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)

    # create log directory and log object
    os.makedirs(config['log-path'], exist_ok=True)
    log_process = LogProcess(f'{config["log-path"]}/main.log', True)

    # Log that config file has been copied
    if config_was_copied:
        log_process.log('Copied standard config from templates/config.example.yml to' + \
                        'config/config.yml', 0)

    # When environment variables are being used the siteconfig.yml is being recreated using those.
    # The config.yml file has already been reset earlier when environment variables are being used.
    if docker_with_env:
        log_process.log('Usage of environment variables detected. Rebuilding siteconfig.yml')
        create_siteconfig_from_env(config["siteconfig"])

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
