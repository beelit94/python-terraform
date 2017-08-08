try:
    from cStringIO import StringIO      # Python 2
except ImportError:
    from io import StringIO
from python_terraform import *
import pytest
import os
import logging
import re
import shutil
import fnmatch

logging.basicConfig(level=logging.DEBUG)
root_logger = logging.getLogger()
current_path = os.path.dirname(os.path.realpath(__file__))

FILE_PATH_WITH_SPACE_AND_SPACIAL_CHARS = "test 'test.out!"
STRING_CASES = [
     [
         lambda x: x.generate_cmd_string('apply', 'the_folder',
                                         no_color=IsFlagged),
         "terraform apply -no-color the_folder"
     ],
     [
         lambda x: x.generate_cmd_string('push', 'path', vcs=True,
                                         token='token',
                                         atlas_address='url'),
         "terraform push -vcs=true -token=token -atlas-address=url path"
     ],
 ]

CMD_CASES = [
    ['method', 'expected_output', 'expected_ret_code', 'expected_logs', 'folder'],
    [
        [
            lambda x: x.cmd('plan', 'var_to_output', no_color=IsFlagged, var={'test_var': 'test'}) ,
            "doesn't need to do anything",
            0,
            '',
            'var_to_output'
        ],
        # try import aws instance
        [
            lambda x: x.cmd('import', 'aws_instance.foo', 'i-abcd1234', no_color=IsFlagged),
            '',
            1,
            'command: terraform import -no-color aws_instance.foo i-abcd1234',
            ''
        ],
        # test with space and special character in file path
        [
            lambda x: x.cmd('plan', 'var_to_output', out=FILE_PATH_WITH_SPACE_AND_SPACIAL_CHARS),
            '',
            0,
            '',
            'var_to_output'
        ]
    ]
]


@pytest.fixture(scope='function')
def fmt_test_file(request):
    target = os.path.join(current_path, 'bad_fmt', 'test.backup')
    orgin = os.path.join(current_path, 'bad_fmt', 'test.tf')
    shutil.copy(orgin,
                target)

    def td():
        shutil.move(target, orgin)

    request.addfinalizer(td)
    return


@pytest.fixture()
def string_logger(request):
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    root_logger.addHandler(handler)

    def td():
        root_logger.removeHandler(handler)
        log_stream.close()

    request.addfinalizer(td)
    return lambda: str(log_stream.getvalue())


class TestTerraform(object):
    def teardown_method(self, method):
        """ teardown any state that was previously setup with a setup_method
        call.
        """

        def purge(dir, pattern):
            for root, dirnames, filenames in os.walk(dir):
                for filename in fnmatch.filter(filenames, pattern):
                    f = os.path.join(root, filename)
                    os.remove(f)
                for dirname in fnmatch.filter(dirnames, pattern):
                    d = os.path.join(root, dirname)
                    shutil.rmtree(d)

        purge('.', '*.tfstate')
        purge('.', '*.terraform')
        purge('.', FILE_PATH_WITH_SPACE_AND_SPACIAL_CHARS)

    @pytest.mark.parametrize([
                 "method", "expected"
             ], STRING_CASES)
    def test_generate_cmd_string(self, method, expected):
        tf = Terraform(working_dir=current_path)
        result = method(tf)

        strs = expected.split()
        for s in strs:
            assert s in result

    @pytest.mark.parametrize(*CMD_CASES)
    def test_cmd(self, method, expected_output, expected_ret_code, expected_logs, string_logger, folder):
        tf = Terraform(working_dir=current_path)
        tf.init(folder)
        ret, out, err = method(tf)
        logs = string_logger()
        logs = logs.replace('\n', '')
        assert expected_output in out
        assert expected_ret_code == ret
        assert expected_logs in logs

    @pytest.mark.parametrize(
        ("folder", "variables", "var_files", "expected_output", "options"),
        [
            ("var_to_output",
             {'test_var': 'test'}, None, "test_output=test", {}),
            ("var_to_output", {'test_list_var': ['c', 'd']}, None, "test_list_output=[c,d]", {}),
            ("var_to_output", {'test_map_var': {"c": "c", "d": "d"}}, None, "test_map_output={a=ab=bc=cd=d}", {}),
            ("var_to_output", {'test_map_var': {"c": "c", "d": "d"}}, 'var_to_output/test_map_var.json', "test_map_output={a=ab=bc=cd=de=ef=f}", {}),
            ("var_to_output", {}, None, "\x1b[0m\x1b[1m\x1b[32mApplycomplete!", {"no_color": IsNotFlagged})
        ])
    def test_apply(self, folder, variables, var_files, expected_output, options):
        tf = Terraform(working_dir=current_path, variables=variables, var_file=var_files)
        # after 0.10.0 we always need to init
        tf.init(folder)
        ret, out, err = tf.apply(folder, **options)
        assert ret == 0
        assert expected_output in out.replace('\n', '').replace(' ', '')
        assert err == ''

    @pytest.mark.parametrize(
        ['cmd', 'args', 'options'],
        [
            # bool value
            ('fmt', ['bad_fmt'], {'list': False, 'diff': False})
        ]
    )
    def test_options(self, cmd, args, options, fmt_test_file):
        tf = Terraform(working_dir=current_path)
        ret, out, err = getattr(tf, cmd)(*args, **options)
        assert ret == 0
        assert out == ''

    def test_state_data(self):
        cwd = os.path.join(current_path, 'test_tfstate_file')
        tf = Terraform(working_dir=cwd, state='tfstate.test')
        tf.read_state_file()
        assert tf.tfstate.modules[0]['path'] == ['root']

    def test_pre_load_state_data(self):
        cwd = os.path.join(current_path, 'test_tfstate_file')
        tf = Terraform(working_dir=cwd, state='tfstate.test')
        assert tf.tfstate.modules[0]['path'] == ['root']

    @pytest.mark.parametrize(
        ("folder", 'variables'),
        [
            ("var_to_output", {'test_var': 'test'})
        ]
    )
    def test_override_default(self, folder, variables):
        tf = Terraform(working_dir=current_path, variables=variables)
        tf.init(folder)
        ret, out, err = tf.apply(folder, var={'test_var': 'test2'},
                                 no_color=IsNotFlagged)
        out = out.replace('\n', '')
        assert '\x1b[0m\x1b[1m\x1b[32mApply' in out
        out = tf.output('test_output')
        assert 'test2' in out

    @pytest.mark.parametrize(
        ("param"),
        [
            ({}),
            ({'module': 'test2'}),
        ]
    )
    def test_output(self, param, string_logger):
        tf = Terraform(working_dir=current_path, variables={'test_var': 'test'})
        tf.init('var_to_output')
        tf.apply('var_to_output')
        result = tf.output('test_output', **param)
        regex = re.compile("terraform output (-module=test2 -json|-json -module=test2) test_output")
        log_str = string_logger()
        if param:
            assert re.search(regex, log_str), log_str
        else:
            assert result == 'test'

    def test_destroy(self):
        tf = Terraform(working_dir=current_path, variables={'test_var': 'test'})
        tf.init('var_to_output')
        ret, out, err = tf.destroy('var_to_output')
        assert ret == 0
        assert 'Destroy complete! Resources: 0 destroyed.' in out

    @pytest.mark.parametrize(
        ("plan", "variables", "expected_ret"),
        [
            ('vars_require_input', {}, 1)
        ]
    )
    def test_plan(self, plan, variables, expected_ret):
        tf = Terraform(working_dir=current_path, variables=variables)
        ret, out, err = tf.plan(plan)
        assert ret == expected_ret

    def test_fmt(self, fmt_test_file):
        tf = Terraform(working_dir=current_path, variables={'test_var': 'test'})
        ret, out, err = tf.fmt(diff=True)
        assert ret == 0

    def test_import(self, string_logger):
        tf = Terraform(working_dir=current_path)
        tf.import_cmd('aws_instance.foo', 'i-abc1234', no_color=IsFlagged)
        assert 'command: terraform import -no-color aws_instance.foo i-abc1234' in string_logger()
