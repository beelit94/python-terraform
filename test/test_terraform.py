from terraform import Terraform


class TestTerraform:
	def test_apply(self):
		tf = Terraform()
		
		tf.apply()

	def test_refresh(self):
		tf = Terraform()

		tf.refresh()

	def test_destroy(self):
		tf = Terraform()

		tf.destroy()

	