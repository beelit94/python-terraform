## Introduction

python-terraform is a python module provide a wrapper of `terraform` command line tool. 
`terraform` is a tool made by Hashicorp, please refer to https://terraform.io/

### Status
[![Build Status](https://travis-ci.org/beelit94/python-terraform.svg?branch=develop)](https://travis-ci.org/beelit94/python-terraform)

## Installation
    pip install python-terraform
    
## Usage
#### For any terraform command

    from python_terraform import *
    t = Terraform()
    return_code, stdout, stderr = t.<cmd_name>(*arguments, **options)

**Note**: method name same as reserved keyword like `import` won't be accepted by python interpreter,
to be able to call the method, you could call cmd_name by adding `_cmd` after command name, for example,
`import` here could be called by

    from python_terraform import *
    t = Terraform()
    return_code, stdout, stderr = t.import_cmd(*arguments, **options)

or just call cmd method directly

    from python_terraform import *
    t = Terraform()
    return_code, stdout, stderr = t.cmd(<cmd_name>, *arguments, **options)
    
#### For any argument
simply pass the string to arguments of the method, for example,

    terraform apply target_dir 
        --> <instance>.apply('target_dir')
    terraform import aws_instance.foo i-abcd1234 
        --> <instance>.import('aws_instance.foo', 'i-abcd1234')

#### For any options
    
* dash to underscore

    remove first dash, and then use underscore to replace dash symbol as option name
        
        ex. -no-color --> no_color

* for a simple flag option

    use ```IsFlagged/None``` as value for raising/not raising flag, for example, 
    
        terraform taint -allow-missing 
           --> <instance>.taint(allow＿missing=IsFlagged)
        terraform taint 
           --> <instance>.taint(allow＿missing=None) or <instance>.taint()
        terraform apply -no-color
           --> <instance>.apply(no_color=IsFlagged)
        
* for a boolean value option
    
    assign True or False, for example,
    
        terraform apply -refresh=true --> <instance>.apply(refresh=True)
         
* if a flag could be used multiple times, assign a list to it's value
        
        terraform apply -target=aws_instance.foo[1] -target=aws_instance.foo[2]
        ---> 
        <instance>.apply(target=['aws_instance.foo[1]', 'aws_instance.foo[2]'])
* for the "var" flag, assign dictionary to it

        terraform apply -var='a=b' -var='c=d'
        --> tf.apply(var={'a':'b', 'c':'d'})
* if an option with None as value, it won't be used

#### Terraform Output

By default, stdout and stderr are captured and returned. This causes the application to appear to hang. To print terraform output in real time, provide the `capture_output` option with any value other than `None`. This will cause the output of terraform to be printed to the terminal in real time. The value of `stdout` and `stderr` below will be `None`.


    from python_terraform import Terraform
    t = Terraform()
    return_code, stdout, stderr = t.<cmd_name>(capture_output=False)

## Examples
### Have a test.tf file under folder "/home/test" 
#### 1. apply with variables a=b, c=d, refresh=false, no color in the output
In shell:

    cd /home/test
    terraform apply -var='a=b' -var='c=d' -refresh=false -no-color
    
In python-terraform:

    from python_terraform import *
    tf = Terraform(working_dir='/home/test')
    tf.apply(no_color=IsFlagged, refresh=False, var={'a':'b', 'c':'d'})
    
or

    from python_terraform import *
    tf = Terraform()
    tf.apply('/home/test', no_color=IsFlagged, refresh=False, var={'a':'b', 'c':'d'})

or

    from python_terraform import *
    tf = Terraform(working_dir='/home/test', variables={'a':'b', 'c':'d'})
    tf.apply(no_color=IsFlagged, refresh=False)
    
#### 2. fmt command, diff=true
In shell:

    cd /home/test
    terraform fmt -diff=true 
    
In python-terraform:
    
    from python_terraform import *
    tf = terraform(working_dir='/home/test')
    tf.fmt(diff=True)

    
## default values
for apply/plan/destroy command, assign with following default value to make 
caller easier in python

1. ```input=False```, in this case process won't hang because you missing a variable
1. ```no_color=IsFlagged```, in this case, stdout of result is easier for parsing

## Implementation
IMHO, how terraform design boolean options is confusing. 
Take `input=True` and `-no-color` option of `apply` command for example,
they're all boolean value but with different option type. 
This make api caller don't have a general rule to follow but to do 
a exhaustive method implementation which I don't prefer to.
Therefore I end-up with using `IsFlagged` or `IsNotFlagged` as value of option 
like `-no-color` and `True/False` value reserved for option like `refresh=true`




    

    
    
