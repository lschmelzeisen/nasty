from inspect import stack


def disrespect_robotstxt(f):
    """Decorator to mark call stacks that should ignore robots.txt requirements.

    Specifically, this is used to designate Timeline to ignore the Crawl-Delay
    statement in robots.txt. This means that you are deliberately
    - hitting the Twitter servers with a much higher frequency,
    - violating the Twitter Terms of Service which ask you to obey robots.txt.
    Only use this, if you are sure you know what you are doing, and you have
    verified that you actually need the performance improvement as it often
    turns out to be negligible in practice anyways.

    This is used in the test cases, as we are using RequestsCache anyway to
    avoid hitting the Twitter servers repeatedly.

    A function can use is_ignore_robotstxt() to find out if this decorator is
    used anywhere in its call stack. This functionality is implemented with this
    complicated decorator logic instead of a simple function parameter to hide
    this functionality so that people don't use this in an uneducated fashion.
    """
    def disrespect_robotstxt_marker(*args, **kwargs):
        return f(*args, **kwargs)

    return disrespect_robotstxt_marker


def is_ignoring_robotstxt():
    result = False
    for frame in stack():
        if frame.function == 'disrespect_robotstxt_marker':
            result = True

        # Need to explicitly delete frame reference to avoid reference cycle.
        # For details, see:
        # https://docs.python.org/3/library/inspect.html#the-interpreter-stack
        del frame

        if result:
            break
    return result
