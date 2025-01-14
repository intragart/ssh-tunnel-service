import time
import threading
import subprocess

from modules.LogP import LogP

class KeepTunnelAlive(threading.Thread):

    def __init__(self, log_path, config_obj):

        threading.Thread.__init__(self)
 
        # threading.Event object that indicates whether the
        # thread should be terminated
        self.stop_flag = threading.Event()

        # set log_file for this thread
        self.log_file = log_path + '/' + config_obj['fqdn'] + '.log'

        # parse yml dictionary to shell command
        self.shell_command = self.create_ssh_from_yml(config_obj)

        # create own loging object for thread
        self.LogP = LogP(self.log_file, True)
 
    def run(self):

        self.LogP.log(f'Thread #{self.ident} started')

        tunnel_pid = 0
        tunnel_reset = False
        proc = None

        # create command string for log file
        self.LogP.log(f'Using command: {" ".join(self.shell_command)}')
 
        while not self.stop_flag.is_set():

            # set standard sleep time
            sleep_time = 1

            if tunnel_pid == 0:

                self.LogP.log('Starting Subprocess ...')

                # no subprocess yet or subprocess has died
                # start new subprocess for tunnel
                proc = subprocess.Popen(self.shell_command, stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, universal_newlines=True)

                # wait for the process to start
                time.sleep(3)

                # get pid for tunnel process
                tunnel_pid = proc.pid

                # log pid
                self.LogP.log(f'Started Subprocess with PID #{tunnel_pid}')

            # indicator for reseting the tunnel has been set
            # try to terminate the subprocess and wait for 15 seconds
            elif tunnel_reset == True:
                tunnel_reset = False
                self.LogP.log('Subprocess needs to be restarted', 1)
                try:
                    self.LogP.log(f'Terminating Subprocess with PID #{proc.pid}')
                    proc.terminate()
                except Exception as e:
                    self.LogP.log(f'Exception: {e}', 1)
                tunnel_pid = 0
                self.LogP.log('Waiting 15 seconds before restarting the Subprocess')
                sleep_time = 15

            # normal operation, continue checking for problems
            else:

                # get stdout, stderr from subprocess
                proc_output = proc.stdout.readline().strip()

                # check for new output
                if proc_output != '':
                    self.LogP.log(proc_output, 4)
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
                    self.LogP.log(f'Subprocess with PID #{tunnel_pid} died, Returncode {proc.poll()}', 2)
                    tunnel_pid = 0

            # print('running ...') # debug message
            time.sleep(sleep_time)
 
        # terminate ssh tunnel
        if proc is not None:
            self.LogP.log(f'Terminating Subprocess with PID #{proc.pid}')
            proc.terminate()

        self.LogP.log(f'Thread #{self.ident} stopped')

    def create_ssh_from_yml(self, yml_dict):

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

        # user@fqdn
        shell_command.append(yml_dict['user'] + '@' + yml_dict['fqdn'])

        return shell_command
