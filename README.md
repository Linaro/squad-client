# Squad-Client

`squad-client` is a tool for accessing data from a [SQUAD](https://github.com/Linaro/squad) instance through its API. We try to make it look as close as possible to SQUAD's [data model](https://squad.readthedocs.io/en/latest/intro.html#core-data-model), by using classes and methods that hopefully will be intuitive for any user familiar with SQUAD terms.


# Use cases

The main purpose of this tool is to ease report customization based on one's specific needs. 

## Report generation

Here is an example of using squad-client to get a total number of tests for a specific
Company over a period of time.

The example below is based on getting the number of tests from Qualcomm, which uses environment
names as `dbc485`. The goal is to get the total amount of tests run on that board over the year
of 2022 across all projects in LKFT group.

```python
from squad_client.core.api import SquadApi
from squad_client.core.models import Squad

SquadApi.configure(url='https://qa-reports.linaro.org/')
report = open("report.txt", "w")

# Get all environment ids that match dragonboard-410c on group lkft
lkft = Squad().group("lkft")
total = 0
for project in lkft.projects().values():
    print(f"Checking {project.slug}:")
    env = project.environment("dragonboard-410c")
    if env is None:
        # No dragonboard for this project
        print("    - it has no dragonboard-410c environment")
        continue

    print(f"    env.id = {env.id}")

    filters = {
        "environment_id": env.id,
        "datetime__gte": "2022-01-01T00:00:00Z",
        "datetime__lte": "2022-12-31T00:00:00Z",
    }
    testruns = Squad().testruns(**filters)
    if len(testruns) == 0:
        # No dragonboard runs in 2022
        print("    - it has no runs for dragonboard-410c in 20222")
        continue

    # Rebuild filters, now from status object
    filters = {f"test_run__{k}": v for k, v in filters.items()}
    filters["count"] = -1

    # Get all statuses of the given environments from test runs that were run in 2022
    statuses = Squad().statuses(**filters).values()
    tests_total = sum([s.tests_total for s in statuses])
    tests_pass = sum([s.tests_pass for s in statuses])

    line = f"{project.slug}: tests pass {tests_pass:<10} | tests total {tests_total:<10}"
    print("    " + line)
    report.write(line + "\n")

    total += tests_total

print(f"Total: {total}")
report.write(f"\nTotal: {total}\n")

```


## Built-in tools

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
