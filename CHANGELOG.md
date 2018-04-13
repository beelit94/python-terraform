# Changelog
## [0.9.1]
1. [#10] log handler error on Linux environment
1. [#11] Fix reading state file for remote state and support backend config for
         init command
## [0.9.0]
### Fixed
1. [#12] Output function doesn't accept parameter 'module'
1. [#16] Handle empty space/special characters when passing string to command line options
1. Tested with terraform 0.10.0

## [0.10.0]
### Fixed
1. [#27] No interaction for apply function
1. [#18] Return access to the subprocess so output can be handled as desired
1. [#24] Full support for output(); support for raise_on_error