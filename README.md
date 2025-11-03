# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/habemus-papadum/pdum_plumbum/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                    |    Stmts |     Miss |   Cover |   Missing |
|---------------------------------------- | -------: | -------: | ------: | --------: |
| src/pdum/plumbum/\_\_init\_\_.py        |       18 |        0 |    100% |           |
| src/pdum/plumbum/aiterops.py            |      213 |        2 |     99% |   350-351 |
| src/pdum/plumbum/aiterops\_internals.py |       71 |        0 |    100% |           |
| src/pdum/plumbum/async\_pipeline.py     |       94 |        3 |     97% |37, 122, 148 |
| src/pdum/plumbum/core.py                |       65 |        2 |     97% |    58, 62 |
| src/pdum/plumbum/iterops.py             |      128 |        0 |    100% |           |
| src/pdum/plumbum/jq/\_\_init\_\_.py     |        6 |        0 |    100% |           |
| src/pdum/plumbum/jq/async\_operators.py |       50 |        3 |     94% | 22, 33-34 |
| src/pdum/plumbum/jq/operators.py        |      248 |       52 |     79% |21, 24, 40, 55-57, 64-69, 77, 82-83, 85-89, 96-98, 114-118, 123, 127, 141, 148-149, 153-158, 167, 175, 195, 239, 292, 305, 309, 313, 324, 335, 338, 340, 360-361 |
| src/pdum/plumbum/jq/paths.py            |      266 |      101 |     62% |43, 46, 48, 76, 79, 87, 93, 106, 109, 132-135, 138-145, 160-162, 171, 179, 186, 212, 216, 222-231, 234-247, 252, 262, 273, 277, 286-298, 303, 307, 311, 316, 319-340, 350, 356-361 |
| src/pdum/plumbum/jq/typing.py           |       25 |        0 |    100% |           |
|                               **TOTAL** | **1184** |  **163** | **86%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/habemus-papadum/pdum_plumbum/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/habemus-papadum/pdum_plumbum/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/habemus-papadum/pdum_plumbum/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/habemus-papadum/pdum_plumbum/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fhabemus-papadum%2Fpdum_plumbum%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/habemus-papadum/pdum_plumbum/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.