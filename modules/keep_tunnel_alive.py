"""A threading class to maintain an active connection to a network tunnel.
"""
import os
import time
import threading
import subprocess

from modules.log_process import LogProcess

class KeepTunnelAlive(threading.Thread):
    """A threading class to maintain an active connection to a network tunnel.

    This class inherits from threading.Thread and creates a ssh-command from the given config_obj.
    Once the tread is started it constantly checks if the tunnel itself is still alive and
    reconnects if neccessary.
    """
    def __init__(self, log_path, config_obj):
        """Initializes the thread for a given ssh site.

        Args:
            log_path (str): path and filename to be used for thread output.
            config_obj (dict): Dictionary that contains all settings for the ssh-command of the
            current thread
        """
        threading.Thread.__init__(self)

        # threading.Event object that indicates whether the
        # thread should be terminated
        self.stop_flag = threading.Event()

        # set log_file for this thread
        self.log_file = log_path + '/' + config_obj['sitename'] + '.log'

        # parse yml dictionary to shell command
        self.shell_command = self.create_ssh_from_yml(config_obj)

        # create own loging object for thread
        self.log_process = LogProcess(self.log_file, True)


    def run(self):
        """This code is being executed within the given thread. As long as there's no stop flag
        being set the execution continues. The code starts the ssh tunnel by executing the command
        generated earlier and watches if the own subprocess (ssh-command) has died or a reset reason
        has been encountered. If the ssh-command has died or needs reset the thread will do so.
        """
        self.log_process.log(f'Thread #{self.ident} started')

        tunnel_pid = 0
        tunnel_reset = False
        proc = None

        # create command string for log file
        self.log_process.log(f'Using command: {" ".join(self.shell_command)}')

        while not self.stop_flag.is_set():

            # set standard sleep time
            sleep_time = 1

            if tunnel_pid == 0:

                self.log_process.log('Starting Subprocess ...')

                # no subprocess yet or subprocess has died
                # start new subprocess for tunnel
                proc = subprocess.Popen(self.shell_command, stdout=subprocess.PIPE,\
                stderr=subprocess.STDOUT, universal_newlines=True)

                # wait for the process to start
                time.sleep(3)

                # get pid for tunnel process
                tunnel_pid = proc.pid

                # log pid
                self.log_process.log(f'Started Subprocess with PID #{tunnel_pid}')

            # indicator for reseting the tunnel has been set
            # try to terminate the subprocess and wait for 15 seconds
            elif tunnel_reset:
                tunnel_reset = False
                self.log_process.log('Subprocess needs to be restarted', 1)
                try:
                    self.log_process.log(f'Terminating Subprocess with PID #{proc.pid}')
                    proc.terminate()
                except Exception as e: # pylint: disable=W0718
                    self.log_process.log(f'Exception: {e}', 1)
                tunnel_pid = 0
                self.log_process.log('Waiting 15 seconds before restarting the Subprocess')
                sleep_time = 15

            # normal operation, continue checking for problems
            else:

                # get stdout, stderr from subprocess
                proc_output = proc.stdout.readline().strip()

                # check for new output
                if proc_output != '':
                    self.log_process.log(proc_output, 4)
                    sleep_time = 0

                    # check if output indicates that the tunnel needs to be reseted
                    # if there is the need to reset the tunnel mark it via tunnel_reset = True
                    # in the next iteration where no new output was found an error message will
                    # be shown and the subprocess will be reseted
                    reset_reasons = ['remote port forwarding failed',
                                    'client_loop: send disconnect: Broken pipe']
                    for reset_reason in reset_reasons:
                        if reset_reason in proc_output:
                            tunnel_reset = True

                # subprocess should be running
                # check if subprocess has terminated
                elif proc.poll() is not None:
                    # subprocess ist not running, try to restart
                    self.log_process.log(f'Subprocess with PID #{tunnel_pid} died, Returncode '+\
                                        f'{proc.poll()}', 2)
                    tunnel_pid = 0

            # print('running ...') # debug message
            time.sleep(sleep_time)

        # terminate ssh tunnel
        if proc is not None:
            self.log_process.log(f'Terminating Subprocess with PID #{proc.pid}')
            proc.terminate()

        self.log_process.log(f'Thread #{self.ident} stopped')


    def create_ssh_from_yml(self, yml_dict):
        """This function creates a ssh-command and returns it.

        Args:
            yml_dict (dict): Dictionary for one site created from siteconfig.yml that contains all
            settings for the ssh-command.

        Returns:
            str: ssh-command
        """
        # ssh to be run in background
        shell_command = ['ssh', '-nNT']

        # forward local ports
        if 'local-ports' in yml_dict:
            for forwarded_port in yml_dict['local-ports']:
                shell_command.append('-L')
                shell_command.append(forwarded_port)

        # forward remote ports
        if 'remote-ports' in yml_dict:
            for forwarded_port in yml_dict['remote-ports']:
                shell_command.append('-R')
                shell_command.append(forwarded_port)

        # use specific port
        if 'ssh-port' in yml_dict:
            shell_command.append('-p')
            shell_command.append(str(yml_dict['ssh-port']))

        # use identity file
        if 'identity-file' in yml_dict:
            shell_command.append('-i')
            shell_command.append(yml_dict['identity-file'])

        # hostkey verification
        if 'hostkey' in yml_dict:
            shell_command.append('-o')
            shell_command.append(f'UserKnownHostsFile={self.add_hostkey(yml_dict)}')

        # add user@fqdn
        shell_command.append(yml_dict['user'] + '@' + yml_dict['fqdn'])

        return shell_command

    def add_hostkey(self, yml_dict):
        """This function creates a known_hosts file for the given configuration inside the script
        directory and returns the complete path of this file.

        Args:
            yml_dict (dict): Dictionary for one site created from siteconfig.yml that contains all
            settings for the ssh-command.

        Returns:
            srt: full path to known_hosts file
        """
        # create a .ssh folder in current working directory
        ssh_folder = os.path.join(yml_dict['cwd'], '.ssh')
        if not os.path.exists(ssh_folder):
            os.makedirs(ssh_folder)

        # create the known_hosts file for this specific site
        known_hosts = os.path.join(ssh_folder, yml_dict['sitename'])
        file_content = f'{yml_dict['fqdn']} {yml_dict['hostkey']}'
        with open(known_hosts, 'w', encoding='utf-8') as kh_file:
            kh_file.write(file_content)

        return known_hosts
