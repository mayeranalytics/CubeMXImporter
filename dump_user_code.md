# dump\_user\_code.py #

## Overview ##

This tool just scans through all source code files and prints out the user code so that it can be manually inserted later - if necessary.

See [cubemximporter.md](cubemximporter.md) for more details on the why and how.

## Usage ##

``` bash
usage: dump_user_code.py [-h] eclipse_project_folder

Dump the user code sections for all files in file tree.

The output will look something like this:
************************** my_project/src/main.c **************************
>36: USER CODE 'Includes'
#include "my_project.h"
// Etc.
********************** my_project/src/stm32l4xx_it.c **********************
>38: USER CODE '0'
// my code 1
>84: USER CODE 'EXTI4_IRQn 1'
// my code 2
// Etc.

positional arguments:
  eclipse_project_folder
                        Path to the eclipse project

optional arguments:
  -h, --help            show this help message and exit
```

## Todo ##
* make python3 compatible