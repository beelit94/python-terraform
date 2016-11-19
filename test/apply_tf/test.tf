variable "test_var" {}

provider "archive" {
}

output "test_output" {
  value = "${var.test_var}"
}