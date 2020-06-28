import subprocess
import os
import sys
import json
import logging
import tempfile


##
## Setup Logger
##
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

class IsFlagged:
    pass

class IsNotFlagged:
    pass

class TerraformCommandError(subprocess.CalledProcessError):
    def __init__(self, ret_code, cmd, out, err):
        super(TerraformCommandError, self).__init__(ret_code, cmd)
        self.out = out
        self.err = err

class Terraform(object):
    ##
    ##Wraps terraform command line tool
    ##https://www.terraform.io/
    ##

    def __init__(self, working_dir=None,
                 targets=None,
                 state=None,
                 variables=None,
                 parallelism=None,
                 var_file=None,
                 terraform_bin_path=None,
                 is_env_vars_included=True,
                 ):

        ##
        ##Params:
        ## working_dir: the directory of the directory in which to execute, if not specified
        ## will be the current directory.
        ## targets: list of targets for the terraform operation.
        ## state: path to the state file, relative to working_dir.
        ## variables: dictionary of variables to pass to terraform operation.
        ## parallelism: default parallelism for terraform operations.
        ## var_file: variables file to pass with -var-file option
        ## terraform_bin_path: path to terraform binary
        ## is_env_vars_invluded: bool to indicate if env_vars are included for operation.
        ##

        self.is_env_vars_included = is_env_vars_included
        self.working_dir = working_dir
        self.state = state
        self.targets = [] if targets is None else targets
        self.variables = {} if variables is None else variables
        self.parallelism = parallelism
        self.terraform_bin_path = terraform_bin_path if terraform_bin_path else 'terraform'
        self.var_file = var_file
        self.temp_var_files = VariableFiles()
