"""Class to be used for process logging into a file and to terminal.
"""
import datetime
import shlex
import subprocess

class LogProcess():
    """Class to be used for process logging into a file and to terminal.
    """
    def __init__(self, filename, print_to_shell = True):
        """Initializes the class for logging.

        Args:
            filename (str): absolute or relative path with name to the logfile
            print_to_shell (bool, optional): defines if the log messages should be printed on the
            shell as well. Defaults to True.
        """

        self.filename = filename
        self.print_to_shell = print_to_shell

    def __compute_log(self, timestamp, log_entry):
        """Appends the log-entry to the file specified for this class and prints it to the screen if
        self.print_to_shell is true. If an error occurs during file-operation an error is printed to
        the screen instead of the log-entry.

        Args:
            timestamp (str): timestamp to be used for this log message
            log_entry (str): log message

        Returns:
            int: Returns 0 if no errors occured.
        """

        try:

            #try to open the logfile in append-mode with the utf-8 encoding
            with open(self.filename, mode='a', encoding='utf-8') as f:

                # write the log entry to the file
                f.write(timestamp + ' ' + log_entry + '\n')

            # print the log entry to the screen
            if self.print_to_shell:
                print(timestamp + ' ' + log_entry)

            return 0

        except Exception as e: # pylint: disable=W0718

            # something went wrong during file-operation
            print(f'{timestamp} [FATAL LOG ERROR] {e}')
            return 1

    def log_command(self, command):
        """This Function executes a Unix command, logs the output and returns the returncode of the
        command.

        Args:
            command (str): command to be executed

        Returns:
            int: Returncode of the command that has been executed.
        """

        # try to execute the command
        try:

            # set the output variable and start the command
            command_printout = None
            proc = subprocess.Popen(shlex.split(command), shell=False, stdout=subprocess.PIPE,\
                    stderr=subprocess.STDOUT, encoding='utf8')

            # loop as long as the command is executing
            while True:

                # check for new output
                command_printout = proc.stdout.readline()

                # when command is finished proc.poll() doesn't return None and the loop ends
                if proc.poll() is not None:
                    break

                # if there is new output log it
                if command_printout:
                    self.log(command_printout.strip(), 4)

            # returns the returncode of the command
            return proc.returncode

        except Exception as e: # pylint: disable=W0718

            # exception during execution
            self.log('Exception while executing: ' + str(command), 4)
            self.log(str(e), 4)

            return 1

    def log(self, msg, log_type = 0):
        """Log the given message. Types that can be used are:
        0: [INFO]
        1: [ERROR]
        2: [WARNING]
        3: [LOG ERROR]
        4: [EXT CMD]

        Args:
            msg (str): Message contents
            log_type (int, optional): Which type of log message shoud be used. Defaults to 0.

        Returns:
            _type_: _description_
        """

        # get current timestamp
        timestamp = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')

        # define modes
        modes = {0: '[INFO]',
                1: '[ERROR]',
                2: '[WARNING]',
                3: '[LOG ERROR]',
                4: '[EXT CMD]'}

        # check if log_type is int
        if isinstance(log_type, int):

            if log_type in modes:

                # Valid mode has been defined. Compute the Log-Message
                return self.__compute_log(timestamp, modes[log_type] + ' ' + msg)

            else:

                # Invalid mode has been defined
                self.__compute_log(timestamp, modes[3] + ' ' +\
                                    'Invalid Parameter \'log_type\' has been defined')
                return 1

        else:

            # 'mode' is not an integer, return error
            self.__compute_log(timestamp, modes[3] + ' ' +\
                                'Parameter \'log_type\' of function \'Logp.log\' has to be integer')
            return 1
