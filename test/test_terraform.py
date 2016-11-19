from python_terraform import *
import pytest
import os
import logging
import re

logging.basicConfig(level=logging.WARN)


STRING_CASES = [
     [
         lambda x: x.generate_cmd_string('apply', 'the_folder',
                                         no_color=IsFlagged,
                                         var={'a': 'b', 'c': 'd'}),
         "terraform apply -var='a=b' -var='c=d' -no-color the_folder"
     ],
     [
         lambda x: x.generate_cmd_string('push', 'path',
                                         var={'a': 'b'}, vcs=True,
                                         token='token',
                                         atlas_address='url'),
         "terraform push -var='a=b' -vcs=true -token=token -atlas-address=url path"
     ],
 ]

CMD_CASES = [
    ['method', 'expected_output'],
    [
        [
            lambda x: x.cmd('plan', 'apply_tf', no_color=IsFlagged, var={'test_var': 'test'}) ,
            "doesn't need to do anything"
        ]
    ]
]


class TestTerraform:
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
        tf = Terraform()
        result = method(tf)

        strs = expected.split()
        for s in strs:
            assert s in result

    @pytest.mark.parametrize(*CMD_CASES)
    def test_cmd(self, method, expected_output):
        tf = Terraform()
        ret, out, err = method(tf)
        assert expected_output in out
        assert ret == 0

    def test_state_data(self):
        tf = Terraform(working_dir='test_tfstate_file', state='tfstate.test')
        tf.read_state_file()
        assert tf.tfstate.modules[0]['path'] == ['root']

    def test_apply(self):
        tf = Terraform(working_dir='apply_tf', variables={'test_var': 'test'})
        ret, out, err = tf.apply(var={'test_var': 'test2'})
        assert ret == 0

    def test_get_output(self):
        tf = Terraform(working_dir='apply_tf', variables={'test_var': 'test'})
        tf.apply()
        assert tf.output('test_output') == 'test'

    def test_destroy(self):
        tf = Terraform(working_dir='apply_tf', variables={'test_var': 'test'})
        ret, out, err = tf.destroy()
        assert ret == 0
        assert 'Destroy complete! Resources: 0 destroyed.' in out
