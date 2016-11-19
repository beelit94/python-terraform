## Introduction

python-terraform is a python module provide a wrapper of `terraform` command line tool. 
`terraform` is a tool made by Hashicorp, please refer to https://terraform.io/

### Status
[![Build Status](https://travis-ci.org/beelit94/python-terraform.svg?branch=develop)](https://travis-ci.org/beelit94/python-terraform)

## Installation
    pip install git+https://github.com/beelit94/python-terraform.git@develop

## Usage
For any terraform command

    def cmd(self, cmd, *args, **kwargs):
    """
    run a terraform command, if success, will try to read state file
    :param cmd: command and sub-command of terraform, seperated with space
                refer to https://www.terraform.io/docs/commands/index.html
    :param args: arguments of a command
    :param kwargs:  any option flag with key value without prefixed dash character
            if there's a dash in the option name, use under line instead of dash,
                ex. -no-color --> no_color
            if it's a simple flag with no value, value should be IsFlagged
                ex. cmd('taint', allow＿missing=IsFlagged)
            if it's a boolean value flag, assign True or false
            if it's a flag could be used multiple times, assign list to it's value
            if it's a "var" variable flag, assign dictionary to it
            if a value is None, will skip this option
    :return: ret_code, out, err

For apply/destroy method, the flag options, like, `-no-color` or `-force`
have been implemented as boolean argument. simply use `is_no_color=True/False` for
apply/destroy method


## Examples
### Have a test.tf file under folder "/home/test"
#### apply with variables a=b, c=d, refresh=False, no color in the output
In shell:

    cd /home/test
    terraform apply -var='a=b' -var='c=d' -refresh=false -no-color
    
In python-terraform:

    from python_terraform import Terraform
    tf = terraform(working_dir='/home/test')
    tf.apply(is_no_color=True, refresh=False, var={'a':'b', 'c':'d'})
#### taint command, allow-missing and no color
In shell:

    cd /home/test
    terraform taint -allow-missing -no-color
    
In python-terraform:
    
    from python_terraform import Terraform
    tf = terraform(working_dir='/home/test')
    tf.cmd('taint', allow_missing=IsFlagged, no_color=IsFlagged)
    

    
    