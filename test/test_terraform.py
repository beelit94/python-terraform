from python_terraform import Terraform


class TestTerraform:
    def test_apply_and_destory(self):
        tf = Terraform()
        ret_code, out, err = tf.apply()

        print out
        print err
        # assert ret_code, 0

        ret_code, out, err = tf.destroy()

        assert ret_code, 0
