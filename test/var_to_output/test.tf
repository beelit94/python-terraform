variable "test_var" {
  default = ""
}

provider "archive" {}

variable "test_list_var" {
  type    = list(string)
  default = ["a", "b"]
}

variable "test_map_var" {
  type = map

  default = {
    "a" = "a"
    "b" = "b"
  }
}

output "test_output" {
  value = var.test_var
}

output "test_list_output" {
  value = var.test_list_var
}

output "test_map_output" {
  value = var.test_map_var
}
