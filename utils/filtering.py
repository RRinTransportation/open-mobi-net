import inspect


def filter_args(args, class_instance):
    expected_parameters = inspect.signature(class_instance.__init__).parameters.keys()
    filtered_args = {key: value for key, value in args.__dict__.items() if key in expected_parameters}
    return filtered_args
