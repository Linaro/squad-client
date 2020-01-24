# Squad-Client

`squad-client` is a tool for accessing data from a [SQUAD](https://github.com/Linaro/squad) instance through its API. We try to make it look as close as possible to SQUAD's [data model](https://squad.readthedocs.io/en/latest/intro.html#core-data-model), by using classes and methods that hopefully will be intuitive for any user familiar with SQUAD terms.

It is still in early development stages so please report bugs :)

# Use cases

The main purpose of this tool is to ease report customization based on one's specific needs. 

## Report generation

Here is a snippet of code that would help one list all groups of a SQUAD instance:

```python
from squad_client.api import SquadApi
from squad_client.models import Squad
from jinja2 import Template

SquadApi.configure(url='https://qa-reports.linaro.org/')
groups = Squad().groups()

template = Template('Groups: {% for group in groups %} {{ group.name }} {% endfor %}!')
with open('report', 'w') as report:
    report.write(template.render(groups=groups.values()))
```

More complex filtering and data retrieval are available. Here is an example of getting a specific build:

```python
from squad_client.api import SquadApi
from squad_client.models import Squad

SquadApi.configure(url='https://qa-reports.linaro.org/')

group = Squad().group('lkft')
project = group.project('linux-stable-rc-4.14-oe-sanity')
build = project.build('v4.14.74')

# or this could be a single chained line
build = Squad().group('lkft').project('linux-stable-rc-4.14-oe-sanity').build('v4.14.74')

# filtering is also available
complete_builds = Squad().group('lkft').project('linux-stable-rc-4.14-oe-sanity').builds(complete=True)
```

For more examples, see `examples` folder.
