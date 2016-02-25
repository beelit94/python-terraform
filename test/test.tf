variable "access_key" {}
variable "secret_key" {}

provider "aws" {
    access_key = "${var.access_key}"
    secret_key = "${var.secret_key}"
    region = "us-west-2"
}

resource "aws_instance" "ubuntu-1404" {
  ami = "ami-9abea4fb"
  instance_type = "t2.micro"
  security_groups = ["terraform-salty-splunk"]
  tags {
    Name = "python-terraform-test"
  }
//  key_name = "${aws_key_pair.key.key_name}"
//  connection {
//    type = "ssh"
//    user = "ubuntu"
//    key_file = "${var.key_path}"
//    timeout = "10m"
//  }
}