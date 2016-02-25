import subprocess
import os
import json
import logging

log = logging.getLogger(__name__)


class Terraform:
    def __init__(self, targets=None, state='terraform.tfstate', variables=None):
        self.targets = [] if targets is None else targets
        self.variables = dict() if variables is None else variables
        
        self.state_filename = state
        self.state_data = dict()
        self.parallelism = 50

    def apply(self, targets=None, variables=None, **kargs):
        """
        refer to https://terraform.io/docs/commands/apply.html
        :param variables: variables in dict type
        :param targets: targets in list
        :returns return_code, stdout, stderr
        """
        variables = self.variables if variables is None else variables
        targets = self.targets if targets is None else targets

        parameters = []
        parameters += self._generate_targets(targets)
        parameters += self._generate_var_string(variables)
        parameters += self._gen_param_string(kargs)

        parameters = \
            ['terraform', 'apply', '-state=%s' % self.state_filename] + parameters

        cmd = ' '.join(parameters)
        return self._run_cmd(cmd)

    def _gen_param_string(self, kargs):
        params = []
        for key, value in kargs.items():
            params += ['%s=%s' % (key, value)]
        return params

    def _run_cmd(self, cmd):
        log.debug('command: ' + cmd)

        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        ret_code = p.returncode
        log.debug('output: ' + out)

        if ret_code == 0:
            log.debug('error: ' + err)
            self.read_state_file()
        return ret_code, out, err

    def destroy(self, targets=None, variables=None, **kwargs):
        variables = self.variables if variables is None else variables
        targets = self.targets if targets is None else targets

        parameters = []
        parameters += self._generate_targets(targets)
        parameters += self._generate_var_string(variables)

        parameters = \
            ['terraform', 'destroy', '-force', '-state=%s' % self.state_filename] + \
            parameters
        cmd = ' '.join(parameters)
        return self._run_cmd(cmd)

    def refresh(self, targets=None, variables=None):
        variables = self.variables if variables is None else variables
        targets = self.targets if targets is None else targets

        parameters = []
        parameters += self._generate_targets(targets)
        parameters += self._generate_var_string(variables)
        parameters = \
            ['terraform', 'refresh', '-state=%s' % self.state_filename] + \
            parameters
        cmd = ' '.join(parameters)
        return self._run_cmd(cmd)

    def read_state_file(self):
        """
        read .tfstate file
        :return: states file in dict type
        """
        if os.path.exists(self.state_filename):
            with open(self.state_filename) as f:
                json_data = json.load(f)
            self.state_data = json_data
            log.debug("state_data=%s" % str(self.state_data))
            return json_data

        return dict()

    def is_any_aws_instance_alive(self):
        self.refresh()
        if not os.path.exists(self.state_filename):
            log.debug("can't find %s " % self.state_data)
            return False

        self.read_state_file()
        try:
            main_module = self._get_main_module()
            for resource_key, info in main_module['resources'].items():
                if 'aws_instance' in resource_key:
                    log.debug("%s is found when read state" % resource_key)
                    return True
            log.debug("no aws_instance found in resource key")
            return False
        except KeyError as err:
            log.debug(str(err))
            return False
        except TypeError as err:
            log.debug(str(err))
            return False

    def _get_main_module(self):
        return self.state_data['modules'][0]

    def get_aws_instances(self):
        instances = dict()

        try:
            main_module = self._get_main_module()
            for resource_key, info in main_module['resources'].items():
                if 'aws_instance' in resource_key:
                    instances[resource_key] = info
        except KeyError:
            return instances
        except TypeError:
            return instances

        return instances

    def get_aws_instance(self, resource_name):
        """
        :param resource_name:
            name of terraform resource, make source count is attached
        :return: return None if not exist, dict type if exist
        """
        try:
            return self.get_aws_instances()[resource_name]
        except KeyError:
            return None

    def get_output_value(self, output_name):
        """

        :param output_name:
        :return:
        """
        try:
            main_module = self._get_main_module()
            return main_module['outputs'][output_name]
        except KeyError:
            return None

    @staticmethod
    def _generate_var_string(d):
        str_t = []
        for k, v in d.iteritems():
            str_t += ['-var'] + ["%s=%s" % (k, v)]

        return str_t

    @staticmethod
    def _generate_targets(targets):
        str_t = []
        for t in targets:
            str_t += ['-target=%s' % t]
        return str_t



