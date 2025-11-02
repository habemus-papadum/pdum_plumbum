# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/habemus-papadum/pdum_plumbum/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                    |    Stmts |     Miss |   Cover |   Missing |
|---------------------------------------- | -------: | -------: | ------: | --------: |
| src/pdum/plumbum/\_\_init\_\_.py        |        5 |        0 |    100% |           |
| src/pdum/plumbum/aiterops.py            |       21 |        0 |    100% |           |
| src/pdum/plumbum/aiterops\_internals.py |       71 |       14 |     80% |18, 27-30, 35, 37, 50, 52, 58-60, 67, 85 |
| src/pdum/plumbum/async\_pipeline.py     |       76 |       12 |     84% |16, 82, 86, 94-96, 100-104, 109, 112 |
| src/pdum/plumbum/core.py                |       41 |        3 |     93% |37, 58, 81 |
| src/pdum/plumbum/iterops.py             |       16 |        0 |    100% |           |
|                               **TOTAL** |  **230** |   **29** | **87%** |           |


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