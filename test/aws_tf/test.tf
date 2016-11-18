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
}