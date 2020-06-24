# Squad-Client

`squad-client` is a tool for accessing data from a [SQUAD](https://github.com/Linaro/squad) instance through its API. We try to make it look as close as possible to SQUAD's [data model](https://squad.readthedocs.io/en/latest/intro.html#core-data-model), by using classes and methods that hopefully will be intuitive for any user familiar with SQUAD terms.

It is still in early development stages so please report bugs :)

# Use cases

The main purpose of this tool is to ease report customization based on one's specific needs. 

## Report generation

squad-client has a built-in feature that reads in a yaml file describing a basic report with simple data querying:

```yaml
squad_url: http://localhost:8000
reports:
    - name: Name of the report
      template: my_template.html.jinja2
      # output: generated_report.html  # will be printed to stdout if omitted
      context:
          # keys under this directive are going to be available in the template
          projects: # same as projects = Squad().projects(group__slug='lkft')
              type: Project
              filters:
                  group__slug: lkft  
```

Save that to a file named `my-report.yml`. Now write the report template:

```jinja2
{% for project_id, project in projects.items() %}
  {{ project.slug }}
{% endfor %}

```

Save that to `my_template.html.jinja2`. Now to generate that report described in `my-report.yml`, just run

```sh
./manage.py report --report-config my-report.yaml
```

The output of this command should look similar to:

```
    project: linaro-hikey-stable-rc-4.4-oe

    project: linux-developer-oe

    project: linux-mainline-oe

    project: linux-mainline-oe-sanity

    project: linux-next-oe

    project: linux-next-oe-new
    
    ...
```

#### Complex reports

More complex filtering and data retrieval are available. Here is an example of getting a specific build:

```python
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad

SquadApi.configure(url='https://qa-reports.linaro.org/')

group = Squad().group('lkft')
project = group.project('linux-stable-rc-4.14-oe-sanity')
build = project.build('v4.14.74')

# or this could be a single chained line
build = Squad().group('lkft').project('linux-stable-rc-4.14-oe-sanity').build('v4.14.74')

# filtering is also available
finished_builds = Squad().group('lkft').project('linux-stable-rc-4.14-oe-sanity').builds(status__finished=True)
```

For more examples, see `examples` folder.
