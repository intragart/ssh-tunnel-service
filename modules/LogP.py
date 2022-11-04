# import general modules
import datetime
import shlex
import subprocess

class LogP():

    def __init__(self, filename, print_to_shell = True):
        """Class to be used for process logging.

        Keyword arguments:
        filename -- absolute or relative path with name to the logfile
        print_to_shell -- defines if the log messages should be printed on the shell as well (default = True)
        """

        self.filename = filename
        self.print_to_shell = print_to_shell

    def __compute_log(self, timestamp, log_entry):
        """Appends the log-entry to the file specified for this class and
        prints it to the screen if self.print_to_shell is true. If an
        error occurs during file-operation an error is printed to the screen
        instead of the log-entry.

        Keyword arguments:
        timestamp -- timestamp to be used for this log message
        log_entry -- log message
        """

        try:

            #try to open the logfile in append-mode with the utf-8 encoding
            with open(self.filename, mode='a', encoding='utf-8') as f:

                # write the log entry to the file
                f.write(timestamp + ' ' + log_entry + '\r\n')

            # print the log entry to the screen
            if self.print_to_shell:
                print(timestamp + ' ' + log_entry)
            
            return 0

        except:

            # something went wrong during file-operation
            print(timestamp + ' [FATAL LOG ERROR] Something went wrong during file-operation')
            return 1

    def log_command(self, command):
        """This Function executes a Unix command, logs the output and returns
        the returncode of the command.

        Keyword arguments:
        command -- command to be executed
        """

        # try to execute the command
        try:

            # set the output variable and start the command
            strOutput = None
            proc = subprocess.Popen(shlex.split(command), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')
            
            # loop as long as the command is executing
            while True:

                # check for new output
                strOutput = proc.stdout.readline()

                # when command is finished proc.poll() doesn't return None and the loop ends
                if proc.poll() is not None:
                    break

                # if there is new output log it
                if strOutput:
                    self.log(strOutput.strip(), 4)

            # returns the returncode of the command
            return proc.returncode

        except Exception as e:

            # exception during execution
            self.log('Exception while executing: ' + str(command), 4)
            self.log(str(e), 4)

            return 1

    def log(self, msg, log_type = 0):
        """ Log the given message. Types that can be used are:
        0: [INFO]
        1: [ERROR]
        2: [WARNING]
        3: [LOG ERROR]
        4: [EXT CMD]

        Keyword arguments:
        msg -- Message contents
        log_type -- Which type of log message shoud be used (default = 0)
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
                self.__compute_log(timestamp, modes[3] + ' ' + 'Invalid Parameter \'log_type\' has been defined')
                return 1

        else:

            # 'mode' is not an integer, return error
            self.__compute_log(timestamp, modes[3] + ' ' + 'Parameter \'log_type\' of function \'Logp.log\' has to be integer')
            return 1
    