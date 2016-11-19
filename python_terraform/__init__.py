import subprocess
import os
import json
import logging

from python_terraform.tfstate import Tfstate

log = logging.getLogger(__name__)


class IsFlagged:
    pass


class IsNotFlagged:
    pass


class Terraform:
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
                 terraform_bin_path=None):
        """
        :param working_dir: the folder of the working folder, if not given, will be where python
        :param targets: list of target
        :param state: path of state file relative to working folder
        :param variables: variables for apply/destroy/plan command
        :param parallelism: parallelism for apply/destroy command
        :param var_file: if specified, variables will not be used
        :param terraform_bin_path: binary path of terraform
        """
        self.working_dir = working_dir
        self.state = state
        self.targets = [] if targets is None else targets
        self.variables = dict() if variables is None else variables
        self.parallelism = parallelism
        self.terraform_bin_path = terraform_bin_path \
            if terraform_bin_path else 'terraform'
        self.var_file = var_file

        # store the tfstate data
        self.tfstate = dict()

    def apply(self,
              dir=None,
              is_no_color=True,
              is_input=False,
              **kwargs):
        """
        refer to https://terraform.io/docs/commands/apply.html
        :raise RuntimeError when return code is not zero
        :param is_no_color: if True, add flag -no-color
        :param is_input: if True, add option -input=true
        :param dir: folder relative to working folder
        :param kwargs: same as kwags in method 'cmd'
        :returns return_code, stdout, stderr
        """

        args, option_dict = self._create_cmd_args(is_input,
                                                  is_no_color,
                                                  dir,
                                                  kwargs)

        return self.cmd('apply', *args, **option_dict)

    def _create_cmd_args(self, is_input, is_no_color, dir, kwargs):
        option_dict = dict()
        option_dict['state'] = self.state
        option_dict['target'] = self.targets
        option_dict['var'] = self.variables
        option_dict['var_file'] = self.var_file
        option_dict['parallelism'] = self.parallelism
        if is_no_color:
            option_dict['no_color'] = IsFlagged
        option_dict['input'] = is_input
        option_dict.update(kwargs)
        args = [dir] if dir else []
        return args, option_dict

    def destroy(self, working_dir=None, is_force=True,
                is_no_color=True, is_input=False, **kwargs):
        """
        refer to https://www.terraform.io/docs/commands/destroy.html
        :raise RuntimeError when return code is not zero
        :return: ret_code, stdout, stderr
        """

        args, option_dict = self._create_cmd_args(is_input,
                                                  is_no_color,
                                                  working_dir,
                                                  kwargs)
        if is_force:
            option_dict['force'] = IsFlagged

        return self.cmd('destroy', *args, **option_dict)

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

            if type(v) is dict:
                for sub_k, sub_v in v.items():
                    cmds += ["-{k}='{var_k}={var_v}'".format(k=k,
                                                             var_k=sub_k,
                                                             var_v=sub_v)]
                continue

            # simple flag,
            if v is IsFlagged:
                cmds += ['-{k}'.format(k=k)]
                continue

            if v is IsNotFlagged:
                continue

            if not v:
                continue

            if type(v) is bool:
                v = 'true' if v else 'false'

            cmds += ['-{k}={v}'.format(k=k, v=v)]

        cmds += args
        cmd = ' '.join(cmds)
        return cmd

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
        :return: ret_code, out, err
        """
        cmd_string = self.generate_cmd_string(cmd, *args, **kwargs)
        log.debug('command: {c}'.format(c=cmd_string))

        working_folder = self.working_dir if self.working_dir else None

        p = subprocess.Popen(cmd_string, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True,
                             cwd=working_folder)
        out, err = p.communicate()
        ret_code = p.returncode
        log.debug('output: {o}'.format(o=out))

        if ret_code == 0:
            self.read_state_file()
        else:
            log.warn('error: {e}'.format(e=err))
        return ret_code, out.decode('utf-8'), err.decode('utf-8')

    def output(self, name):
        """
        https://www.terraform.io/docs/commands/output.html
        :param name: name of output
        :return: output value
        """
        ret, out, err = self.cmd('output', name, json=IsFlagged)

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
