def first(_dict):
    return next(iter(_dict.values()))

def parse_test_name(name):
    suite_name, test_name = name.split('/', 1)
    return (suite_name, test_name)

def parse_metric_name(name):
    return parse_test_name(name)
