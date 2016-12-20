from python_terraform import *
import pytest
import os
import logging
import re
import shutil

logging.basicConfig(level=logging.DEBUG)
current_path = os.path.dirname(os.path.realpath(__file__))

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
    ['method', 'expected_output'],
    [
        [
            lambda x: x.cmd('plan', 'var_to_output', no_color=IsFlagged, var={'test_var': 'test'}) ,
            "doesn't need to do anything"
        ]
    ]
]

@pytest.fixture()
def fmt_test_file(request):
    target = os.path.join(current_path, 'bad_fmt', 'test.backup')
    orgin = os.path.join(current_path, 'bad_fmt', 'test.tf')
    shutil.copy(orgin,
                target)

    def td():
        shutil.move(target, orgin)

    request.addfinalizer(td)
    return


class TestTerraform(object):
    def teardown_method(self, method):
        """ teardown any state that was previously setup with a setup_method
        call.
        """

        def purge(dir, pattern):
            for f in os.listdir(dir):
                if re.search(pattern, f):
                    if os.path.isfile(f):
                        os.remove(os.path.join(dir, f))

        purge('.', '.tfstate')

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
    def test_cmd(self, method, expected_output):
        tf = Terraform(working_dir=current_path)
        ret, out, err = method(tf)
        assert expected_output in out
        assert ret == 0

    @pytest.mark.parametrize(
        ("folder", "variables", "var_files", "expected_output"),
        [
            ("var_to_output", {'test_var': 'test'}, None, "test_output=test"),
            ("var_to_output", {'test_list_var': ['c', 'd']}, None, "test_list_output=[c,d]"),
            ("var_to_output", {'test_map_var': {"c": "c", "d": "d"}}, None, "test_map_output={a=ab=bc=cd=d}"),
            ("var_to_output", {'test_map_var': {"c": "c", "d": "d"}}, 'var_to_output/test_map_var.json', "test_map_output={a=ab=bc=cd=de=ef=f}")
        ])
    def test_apply(self, folder, variables, var_files, expected_output):
        tf = Terraform(working_dir=current_path, variables=variables, var_file=var_files)
        ret, out, err = tf.apply(folder)
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
        ret, out, err = tf.apply(folder, var={'test_var': 'test2'},
                                 no_color=IsNotFlagged)
        out = out.replace('\n', '')
        assert '\x1b[0m\x1b[1m\x1b[32mApply' in out

    def test_get_output(self):
        tf = Terraform(working_dir=current_path, variables={'test_var': 'test'})
        tf.apply('var_to_output')
        assert tf.output('test_output') == 'test'

    def test_destroy(self):
        tf = Terraform(working_dir=current_path, variables={'test_var': 'test'})
        ret, out, err = tf.destroy('var_to_output')
        assert ret == 0
        assert 'Destroy complete! Resources: 0 destroyed.' in out

    def test_fmt(self):
        tf = Terraform(working_dir=current_path, variables={'test_var': 'test'})
        ret, out, err = tf.fmt(diff=True)
        assert ret == 0
