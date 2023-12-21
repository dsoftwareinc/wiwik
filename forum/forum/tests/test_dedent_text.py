import os
from pathlib import Path

from common.utils import dedent_code
from forum.tests.base import ForumApiTestCase

markdown_text = """
```mermaid
graph LR
    subgraph localhost
        wiwik -- 5432 --> postgres
        wiwik -- 6379--> redis
        redis -- 6379--> wiwik-worker
        subgraph docker
            postgres
            redis
        end
    end
    user -- 8000 --> wiwik
```

## Step by step

A step by step series of examples that tell you how to get a development env
running locally:

1. clone repository

    ```
    git clone https://github.com/dsoftwareinc/wiwik
    ```

2. In the local repository directory, create a virtual environment and activate
   it.

    ```
    virtualenv env -p `which python3.10`
    source env/bin/activate
    ```

3. Install dependencies required for the project

    ```
        pip install -r requirements.txt
    ```
"""

dedented_text = """
```mermaid
graph LR
    subgraph localhost
        wiwik -- 5432 --> postgres
        wiwik -- 6379--> redis
        redis -- 6379--> wiwik-worker
        subgraph docker
            postgres
            redis
        end
    end
    user -- 8000 --> wiwik
```

## Step by step

A step by step series of examples that tell you how to get a development env
running locally:

1. clone repository

    ```
    git clone https://github.com/dsoftwareinc/wiwik
    ```

2. In the local repository directory, create a virtual environment and activate
   it.

    ```
    virtualenv env -p `which python3.10`
    source env/bin/activate
    ```

3. Install dependencies required for the project

    ```
    pip install -r requirements.txt
    ```
"""


class TestDedent(ForumApiTestCase):
    def test_dedent_code(self):
        assert dedent_code(markdown_text) == dedented_text

    def test_dedent_existing_markdown_files(self):
        directory = "../private/export"
        try:
            filenames = sorted(os.listdir(directory))
        except FileNotFoundError:
            return
        for filename in filenames:
            _markdown_text = Path(os.path.join(directory, filename)).read_text()

            self.assertEqual(
                dedent_code(_markdown_text),
                _markdown_text,
                f"File {filename} is not dedented",
            )
