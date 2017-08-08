# -*- coding: utf-8 -*-
# above is for compatibility of python2.7.11

import subprocess
import os
import sys
import json
import logging
import tempfile

from python_terraform.tfstate import Tfstate

log = logging.getLogger(__name__)


class IsFlagged:
    pass


class IsNotFlagged:
    pass


class Terraform(object):
    """
    Wrapper of terraform command line tool
    https://www.terraform.io/
    """

    def __init__(self, working_dir=None,
                 targets=None,
                 state=None,
                 variables=None,
                 parallelism=None,
                 var_file=None,
                 terraform_bin_path=None,
                 is_env_vars_included=True):
        """
        :param working_dir: the folder of the working folder, if not given,
                            will be current working folder
        :param targets: list of target
                        as default value of apply/destroy/plan command
        :param state: path of state file relative to working folder,
                    as a default value of apply/destroy/plan command
        :param variables: default variables for apply/destroy/plan command,
                        will be override by variable passing by apply/destroy/plan method
        :param parallelism: default parallelism value for apply/destroy command
        :param var_file: passed as value of -var-file option,
                could be string or list, list stands for multiple -var-file option
        :param terraform_bin_path: binary path of terraform
        :type is_env_vars_included: bool
        :param is_env_vars_included: included env variables when calling terraform cmd
        """
        self.is_env_vars_included = is_env_vars_included
        self.working_dir = working_dir
        self.state = state
        self.targets = [] if targets is None else targets
        self.variables = dict() if variables is None else variables
        self.parallelism = parallelism
        self.terraform_bin_path = terraform_bin_path \
            if terraform_bin_path else 'terraform'
        self.var_file = var_file
        self.temp_var_files = VariableFiles()

        # store the tfstate data
        self.tfstate = None
        self.read_state_file(self.state)

    def __getattr__(self, item):
        def wrapper(*args, **kwargs):
            cmd_name = str(item)
            if cmd_name.endswith('_cmd'):
                cmd_name = cmd_name[:-4]
            logging.debug('called with %r and %r' % (args, kwargs))
            return self.cmd(cmd_name, *args, **kwargs)

        return wrapper

    def apply(self, dir_or_plan=None, input=False, no_color=IsFlagged, **kwargs):
        """
        refer to https://terraform.io/docs/commands/apply.html
        no-color is flagged by default
        :param no_color: disable color of stdout
        :param input: disable prompt for a missing variable
        :param dir_or_plan: folder relative to working folder
        :param kwargs: same as kwags in method 'cmd'
        :returns return_code, stdout, stderr
        """
        default = kwargs
        default['input'] = input
        default['no_color'] = no_color
        option_dict = self._generate_default_options(default)
        args = self._generate_default_args(dir_or_plan)
        return self.cmd('apply', *args, **option_dict)

    def _generate_default_args(self, dir_or_plan):
        return [dir_or_plan] if dir_or_plan else []

    def _generate_default_options(self, input_options):
        option_dict = dict()
        option_dict['state'] = self.state
        option_dict['target'] = self.targets
        option_dict['var'] = self.variables
        option_dict['var_file'] = self.var_file
        option_dict['parallelism'] = self.parallelism
        option_dict['no_color'] = IsFlagged
        option_dict['input'] = False
        option_dict.update(input_options)
        return option_dict

    def destroy(self, dir_or_plan=None, force=IsFlagged, **kwargs):
        """
        refer to https://www.terraform.io/docs/commands/destroy.html
        force/no-color option is flagged by default
        :return: ret_code, stdout, stderr
        """
        default = kwargs
        default['force'] = force
        options = self._generate_default_options(default)
        args = self._generate_default_args(dir_or_plan)
        return self.cmd('destroy', *args, **options)

    def plan(self, dir_or_plan=None, detailed_exitcode=IsFlagged, **kwargs):
        """
        refert to https://www.terraform.io/docs/commands/plan.html
        :param detailed_exitcode: Return a detailed exit code when the command exits.
        :param dir_or_plan: relative path to plan/folder
        :param kwargs: options
        :return: ret_code, stdout, stderr
        """
        options = kwargs
        options['detailed_exitcode'] = detailed_exitcode
        options = self._generate_default_options(options)
        args = self._generate_default_args(dir_or_plan)
        return self.cmd('plan', *args, **options)

    def generate_cmd_string(self, cmd, *args, **kwargs):
        """
        for any generate_cmd_string doesn't written as public method of terraform

        examples:
        1. call import command,
        ref to https://www.terraform.io/docs/commands/import.html
        --> generate_cmd_string call:
                terraform import -input=true aws_instance.foo i-abcd1234
        --> python call:
                tf.generate_cmd_string('import', 'aws_instance.foo', 'i-abcd1234', input=True)

        2. call apply command,
        --> generate_cmd_string call:
                terraform apply -var='a=b' -var='c=d' -no-color the_folder
        --> python call:
                tf.generate_cmd_string('apply', the_folder, no_color=IsFlagged, var={'a':'b', 'c':'d'})

        :param cmd: command and sub-command of terraform, seperated with space
                    refer to https://www.terraform.io/docs/commands/index.html
        :param args: arguments of a command
        :param kwargs: same as kwags in method 'cmd'
        :return: string of valid terraform command
        """
        cmds = cmd.split()
        cmds = [self.terraform_bin_path] + cmds

        for k, v in kwargs.items():
            if '_' in k:
                k = k.replace('_', '-')

            if type(v) is list:
                for sub_v in v:
                    cmds += ['-{k}={v}'.format(k=k, v=sub_v)]
                continue

            # right now we assume only variables will be passed as dict
            # since map type sent in string won't work, create temp var file for
            # variables, and clean it up later
            if type(v) is dict:
                filename = self.temp_var_files.create(v)
                cmds += ['-var-file={0}'.format(filename)]
                continue

            # simple flag,
            if v is IsFlagged:
                cmds += ['-{k}'.format(k=k)]
                continue

            if v is None or v is IsNotFlagged:
                continue

            if type(v) is bool:
                v = 'true' if v else 'false'

            cmds += ['-{k}={v}'.format(k=k, v=v)]

        cmds += args
        return cmds

    def cmd(self, cmd, *args, **kwargs):
        """
        run a terraform command, if success, will try to read state file
        :param cmd: command and sub-command of terraform, seperated with space
                    refer to https://www.terraform.io/docs/commands/index.html
        :param args: arguments of a command
        :param kwargs:  any option flag with key value without prefixed dash character
                if there's a dash in the option name, use under line instead of dash,
                    ex. -no-color --> no_color
                if it's a simple flag with no value, value should be IsFlagged
                    ex. cmd('taint', allow＿missing=IsFlagged)
                if it's a boolean value flag, assign True or false
                if it's a flag could be used multiple times, assign list to it's value
                if it's a "var" variable flag, assign dictionary to it
                if a value is None, will skip this option
                if the option 'capture_output' is passed (with any value other than
                    True), terraform output will be printed to stdout/stderr and
                    "None" will be returned as out and err.
        :return: ret_code, out, err
        """

        capture_output = kwargs.pop('capture_output', True)
        if capture_output is True:
            stderr = subprocess.PIPE
            stdout = subprocess.PIPE
        else:
            stderr = sys.stderr
            stdout = sys.stdout

        cmds = self.generate_cmd_string(cmd, *args, **kwargs)
        log.debug('command: {c}'.format(c=' '.join(cmds)))

        working_folder = self.working_dir if self.working_dir else None

        environ_vars = {}
        if self.is_env_vars_included:
            environ_vars = os.environ.copy()

        p = subprocess.Popen(cmds, stdout=stdout, stderr=stderr,
                             cwd=working_folder, env=environ_vars)
        out, err = p.communicate()
        ret_code = p.returncode
        log.debug('output: {o}'.format(o=out))

        if ret_code == 0:
            self.read_state_file()
        else:
            log.warn('error: {e}'.format(e=err))

        self.temp_var_files.clean_up()
        if capture_output is True:
            return ret_code, out.decode('utf-8'), err.decode('utf-8')
        else:
            return ret_code, None, None

    def output(self, name, *args, **kwargs):
        """
        https://www.terraform.io/docs/commands/output.html
        :param name: name of output
        :return: output value
        """

        ret, out, err = self.cmd(
            'output', name, json=IsFlagged, *args, **kwargs)

        log.debug('output raw string: {0}'.format(out))
        if ret != 0:
            return None
        out = out.lstrip()

        output_dict = json.loads(out)
        return output_dict['value']

    def read_state_file(self, file_path=None):
        """
        read .tfstate file
        :param file_path: relative path to working dir
        :return: states file in dict type
        """

        if not file_path:
            file_path = self.state

        if not file_path:
            file_path = 'terraform.tfstate'

        if self.working_dir:
            file_path = os.path.join(self.working_dir, file_path)

        self.tfstate = Tfstate.load_file(file_path)

    def __exit__(self, exc_type, exc_value, traceback):
        self.temp_var_files.clean_up()


class VariableFiles(object):
    def __init__(self):
        self.files = []

    def create(self, variables):
        with tempfile.NamedTemporaryFile('w+t', delete=False) as temp:
            log.debug('{0} is created'.format(temp.name))
            self.files.append(temp)
            log.debug('variables wrote to tempfile: {0}'.format(str(variables)))
            temp.write(json.dumps(variables))
            file_name = temp.name

        return file_name

    def clean_up(self):
        for f in self.files:
            os.unlink(f.name)

        self.files = []
