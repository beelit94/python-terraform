## Introduction

python-terraform is a python module provide a wrapper of `terraform` command line tool. 
`terraform` is a tool made by Hashicorp, please refer to https://terraform.io/

### Status
[![Build Status](https://travis-ci.org/beelit94/python-terraform.svg?branch=develop)](https://travis-ci.org/beelit94/python-terraform)

## Installation
    pip install python-terraform

## Implementation
IMHO, how terraform design boolean options is confusing. 
Take `input=True` and `-no-color` option of `apply` command for example,
they're all boolean value but with different option type. 
This make api caller don't have a general rule to follow but to do 
a exhaustive method implementation which I don't prefer to.
Therefore I end-up with using `IsFlagged` or `IsNotFlagged` as value of option 
like `-no-color` and `True/False` value reserved for option like 

## Usage
For any terraform command

    from python_terraform import Terraform
    t = Terraform()
    return_code, stdout, stderr = t.<cmd_name>(*arguments, **options)
    
For any options
    
    if there's a dash in the option name, use under line instead of dash,
        ex. -no-color --> no_color
    if it's a simple flag with no value, value should be IsFlagged
        ex. cmd('taint', allow＿missing=IsFlagged)
    if it's a boolean value flag like "-refresh=true", assign True or False
    if it's a flag could be used multiple times, assign list to it's value
    if it's a "var" variable flag, assign dictionary to it
    if a value is None, will skip this option

## Examples
### Have a test.tf file under folder "/home/test" 
#### 1. apply with variables a=b, c=d, refresh=false, no color in the output
In shell:

    cd /home/test
    terraform apply -var='a=b' -var='c=d' -refresh=false -no-color
    
In python-terraform:

    from python_terraform import Terraform
    tf = Terraform(working_dir='/home/test')
    tf.apply(no_color=IsFlagged, refresh=False, var={'a':'b', 'c':'d'})
    
or

    from python_terraform import Terraform
    tf = Terraform()
    tf.apply('/home/test', no_color=IsFlagged, refresh=False, var={'a':'b', 'c':'d'})
    
#### 2. fmt command, diff=true
In shell:

    cd /home/test
    terraform fmt -diff=true 
    
In python-terraform:
    
    from python_terraform import Terraform
    tf = terraform(working_dir='/home/test')
    tf.fmt(diff=True)
    

    
    