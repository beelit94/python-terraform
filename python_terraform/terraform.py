import json
import logging
import os
import subprocess
import sys
import tempfile
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type, Union

from python_terraform.tfstate import Tfstate

logger = logging.getLogger(__name__)

COMMAND_WITH_SUBCOMMANDS = {"workspace"}


class TerraformFlag:
    pass


class IsFlagged(TerraformFlag):
    pass


class IsNotFlagged(TerraformFlag):
    pass


CommandOutput = Tuple[Optional[int], Optional[str], Optional[str]]


class TerraformCommandError(subprocess.CalledProcessError):
    def __init__(self, ret_code: int, cmd: str, out: Optional[str], err: Optional[str]):
        super(TerraformCommandError, self).__init__(ret_code, cmd)
        self.out = out
        self.err = err
        logger.error("Error with command %s. Reason: %s", self.cmd, self.err)


class Terraform:
    """Wrapper of terraform command line tool.

    https://www.terraform.io/
    """

    def __init__(
        self,
        working_dir: Optional[str] = None,
        targets: Optional[Sequence[str]] = None,
        state: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        parallelism: Optional[str] = None,
        var_file: Optional[str] = None,
        terraform_bin_path: Optional[str] = None,
        is_env_vars_included: bool = True,
    ):
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
        self.terraform_bin_path = (
            terraform_bin_path if terraform_bin_path else "terraform"
        )
        self.var_file = var_file
        self.temp_var_files = VariableFiles()

        # store the tfstate data
        self.tfstate = None
        self.read_state_file(self.state)

    def __getattr__(self, item: str) -> Callable:
        def wrapper(*args, **kwargs):
            cmd_name = str(item)
            if cmd_name.endswith("_cmd"):
                cmd_name = cmd_name[:-4]
            logger.debug("called with %r and %r", args, kwargs)
            return self.cmd(cmd_name, *args, **kwargs)

        return wrapper

    def apply(
        self,
        dir_or_plan: Optional[str] = None,
        input: bool = False,
        skip_plan: bool = True,
        no_color: Type[TerraformFlag] = IsFlagged,
        **kwargs,
    ) -> CommandOutput:
        """Refer to https://terraform.io/docs/commands/apply.html

        no-color is flagged by default
        :param no_color: disable color of stdout
        :param input: disable prompt for a missing variable
        :param dir_or_plan: folder relative to working folder
        :param skip_plan: force apply without plan (default: false)
        :param kwargs: same as kwags in method 'cmd'
        :returns return_code, stdout, stderr
        """
        if not skip_plan:
            return self.plan(dir_or_plan=dir_or_plan, **kwargs)
        default = kwargs.copy()
        default["input"] = input
        default["no_color"] = no_color
        default["auto-approve"] = True  # a False value will require an input
        option_dict = self._generate_default_options(default)
        args = self._generate_default_args(dir_or_plan)
        return self.cmd("apply", *args, **option_dict)

    def _generate_default_args(self, dir_or_plan: Optional[str]) -> Sequence[str]:
        return [dir_or_plan] if dir_or_plan else []

    def _generate_default_options(
        self, input_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "state": self.state,
            "target": self.targets,
            "var": self.variables,
            "var_file": self.var_file,
            "parallelism": self.parallelism,
            "no_color": IsFlagged,
            "input": False,
            **input_options,
        }

    def destroy(
        self,
        dir_or_plan: Optional[str] = None,
        force: Type[TerraformFlag] = IsFlagged,
        **kwargs,
    ) -> CommandOutput:
        """Refer to https://www.terraform.io/docs/commands/destroy.html

        force/no-color option is flagged by default
        :return: ret_code, stdout, stderr
        """
        default = kwargs.copy()
        default["force"] = force
        options = self._generate_default_options(default)
        args = self._generate_default_args(dir_or_plan)
        return self.cmd("destroy", *args, **options)

    def plan(
        self,
        dir_or_plan: Optional[str] = None,
        detailed_exitcode: Type[TerraformFlag] = IsFlagged,
        **kwargs,
    ) -> CommandOutput:
        """Refer to https://www.terraform.io/docs/commands/plan.html

        :param detailed_exitcode: Return a detailed exit code when the command exits.
        :param dir_or_plan: relative path to plan/folder
        :param kwargs: options
        :return: ret_code, stdout, stderr
        """
        options = kwargs.copy()
        options["detailed_exitcode"] = detailed_exitcode
        options = self._generate_default_options(options)
        args = self._generate_default_args(dir_or_plan)
        return self.cmd("plan", *args, **options)

    def init(
        self,
        dir_or_plan: Optional[str] = None,
        backend_config: Optional[Dict[str, str]] = None,
        reconfigure: Type[TerraformFlag] = IsFlagged,
        backend: bool = True,
        **kwargs,
    ) -> CommandOutput:
        """Refer to https://www.terraform.io/docs/commands/init.html

        By default, this assumes you want to use backend config, and tries to
        init fresh. The flags -reconfigure and -backend=true are default.

        :param dir_or_plan: relative path to the folder want to init
        :param backend_config: a dictionary of backend config options. eg.
                t = Terraform()
                t.init(backend_config={'access_key': 'myaccesskey',
                'secret_key': 'mysecretkey', 'bucket': 'mybucketname'})
        :param reconfigure: whether or not to force reconfiguration of backend
        :param backend: whether or not to use backend settings for init
        :param kwargs: options
        :return: ret_code, stdout, stderr
        """
        options = kwargs.copy()
        options.update(
            {
                "backend_config": backend_config,
                "reconfigure": reconfigure,
                "backend": backend,
            }
        )
        options = self._generate_default_options(options)
        args = self._generate_default_args(dir_or_plan)
        return self.cmd("init", *args, **options)

    def generate_cmd_string(self, cmd: str, *args, **kwargs) -> List[str]:
        """For any generate_cmd_string doesn't written as public method of Terraform

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
        if cmd in COMMAND_WITH_SUBCOMMANDS:
            args = list(args)
            subcommand = args.pop(0)
            cmds.append(subcommand)

        for option, value in kwargs.items():
            if "_" in option:
                option = option.replace("_", "-")

            if isinstance(value, list):
                for sub_v in value:
                    cmds += [f"-{option}={sub_v}"]
                continue

            if isinstance(value, dict):
                if "backend-config" in option:
                    for bk, bv in value.items():
                        cmds += [f"-backend-config={bk}={bv}"]
                    continue

                # since map type sent in string won't work, create temp var file for
                # variables, and clean it up later
                elif option == "var":
                    # We do not create empty var-files if there is no var passed.
                    # An empty var-file would result in an error: An argument or block definition is required here
                    if value:
                        filename = self.temp_var_files.create(value)
                        cmds += [f"-var-file={filename}"]

                    continue

            # simple flag,
            if value is IsFlagged:
                cmds += [f"-{option}"]
                continue

            if value is None or value is IsNotFlagged:
                continue

            if isinstance(value, bool):
                value = "true" if value else "false"

            cmds += [f"-{option}={value}"]

        cmds += args
        return cmds

    def cmd(
        self,
        cmd: str,
        *args,
        capture_output: Union[bool, str] = True,
        raise_on_error: bool = True,
        synchronous: bool = True,
        **kwargs,
    ) -> CommandOutput:
        """Run a terraform command, if success, will try to read state file

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
                if the option 'raise_on_error' is passed (with any value that evaluates to True),
                    and the terraform command returns a nonzerop return code, then
                    a TerraformCommandError exception will be raised. The exception object will
                    have the following properties:
                      returncode: The command's return code
                      out: The captured stdout, or None if not captured
                      err: The captured stderr, or None if not captured
        :return: ret_code, out, err
        """
        if capture_output is True:
            stderr = subprocess.PIPE
            stdout = subprocess.PIPE
        elif capture_output == "framework":
            stderr = None
            stdout = None
        else:
            stderr = sys.stderr
            stdout = sys.stdout

        cmds = self.generate_cmd_string(cmd, *args, **kwargs)
        logger.info("Command: %s", " ".join(cmds))

        working_folder = self.working_dir if self.working_dir else None

        environ_vars = {}
        if self.is_env_vars_included:
            environ_vars = os.environ.copy()

        p = subprocess.Popen(
            cmds, stdout=stdout, stderr=stderr, cwd=working_folder, env=environ_vars
        )

        if not synchronous:
            return None, None, None

        out, err = p.communicate()
        ret_code = p.returncode
        logger.info("output: %s", out)

        if ret_code == 0:
            self.read_state_file()
        else:
            logger.warning("error: %s", err)

        self.temp_var_files.clean_up()
        if capture_output is True:
            out = out.decode()
            err = err.decode()
        else:
            out = None
            err = None

        if ret_code and raise_on_error:
            raise TerraformCommandError(ret_code, " ".join(cmds), out=out, err=err)

        return ret_code, out, err

    def output(
        self, *args, capture_output: bool = True, **kwargs
    ) -> Union[None, str, Dict[str, str], Dict[str, Dict[str, str]]]:
        """Refer https://www.terraform.io/docs/commands/output.html

        Note that this method does not conform to the (ret_code, out, err) return
        convention. To use the "output" command with the standard convention,
        call "output_cmd" instead of "output".

        :param args:   Positional arguments. There is one optional positional
                       argument NAME; if supplied, the returned output text
                       will be the json for a single named output value.
        :param kwargs: Named options, passed to the command. In addition,
                          'full_value': If True, and NAME is provided, then
                                        the return value will be a dict with
                                        "value', 'type', and 'sensitive'
                                        properties.
        :return: None, if an error occured
                 Output value as a string, if NAME is provided and full_value
                    is False or not provided
                 Output value as a dict with 'value', 'sensitive', and 'type' if
                    NAME is provided and full_value is True.
                 dict of named dicts each with 'value', 'sensitive', and 'type',
                    if NAME is not provided
        """
        kwargs["json"] = IsFlagged
        if capture_output is False:
            raise ValueError("capture_output is required for this method")

        ret, out, _ = self.output_cmd(*args, **kwargs)

        if ret:
            return None

        return json.loads(out.lstrip())

    def read_state_file(self, file_path=None) -> None:
        """Read .tfstate file

        :param file_path: relative path to working dir
        :return: states file in dict type
        """

        working_dir = self.working_dir or ""

        file_path = file_path or self.state or ""

        if not file_path:
            backend_path = os.path.join(file_path, ".terraform", "terraform.tfstate")

            if os.path.exists(os.path.join(working_dir, backend_path)):
                file_path = backend_path
            else:
                file_path = os.path.join(file_path, "terraform.tfstate")

        file_path = os.path.join(working_dir, file_path)

        self.tfstate = Tfstate.load_file(file_path)

    def set_workspace(self, workspace, *args, **kwargs) -> CommandOutput:
        """Set workspace

        :param workspace: the desired workspace.
        :return: status
        """
        return self.cmd("workspace", "select", workspace, *args, **kwargs)

    def create_workspace(self, workspace, *args, **kwargs) -> CommandOutput:
        """Create workspace

        :param workspace: the desired workspace.
        :return: status
        """
        return self.cmd("workspace", "new", workspace, *args, **kwargs)

    def delete_workspace(self, workspace, *args, **kwargs) -> CommandOutput:
        """Delete workspace

        :param workspace: the desired workspace.
        :return: status
        """
        return self.cmd("workspace", "delete", workspace, *args, **kwargs)

    def show_workspace(self, **kwargs) -> CommandOutput:
        """Show workspace, this command does not need the [DIR] part

        :return: workspace
        """
        return self.cmd("workspace", "show", **kwargs)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.temp_var_files.clean_up()


class VariableFiles:
    def __init__(self):
        self.files = []

    def create(self, variables: Dict[str, str]) -> str:
        with tempfile.NamedTemporaryFile(
            "w+t", suffix=".tfvars.json", delete=False
        ) as temp:
            logger.debug("%s is created", temp.name)
            self.files.append(temp)
            logger.debug("variables wrote to tempfile: %s", variables)
            temp.write(json.dumps(variables))
            file_name = temp.name

        return file_name

    def clean_up(self):
        for f in self.files:
            os.unlink(f.name)

        self.files = []
