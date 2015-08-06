# TODO: Pull this back together with conda_manifest.
import os
from contextlib import contextmanager

import conda.resolve
from conda.resolve import MatchSpec
import conda_build.config
# import conda_manifest.config

import logging
from conda.resolve import stdoutlog, dotlog

conda_stdoutlog = stdoutlog
# TODO: Handle the amount of standard out that conda is producing.


from conda.console import SysStdoutWriteHandler


class StdoutNewline(SysStdoutWriteHandler):
    def emit(self, record):
        record.msg += '\n'
        SysStdoutWriteHandler.emit(self, record)


stdout = logging.getLogger('obvci.stdoutlog')
stdout.addHandler(StdoutNewline())
stdout.setLevel(logging.WARNING)


@contextmanager
def override_conda_logging(level):
    # Override the conda logging handlers.

    # We need to import conda.fetch and conda.resolve to trigger the
    # creation of the loggers in the first place.
    import conda.fetch
    import conda.resolve

    levels = {}
    handlers = {}
    loggers = ['progress', 'progress.start', 'progress.update',
               'progress.stop', 'stdoutlog', 'stderrlog',
               'conda.resolve', 'dotupdate']

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        levels[logger_name] = logger.level
        handlers[logger_name] = logger.handlers

        logger.setLevel(level)
        logger.handlers = []
    yield
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(levels[logger_name])
        logger.handlers = handlers[logger_name]


@contextmanager
def setup_vn_mtx_case(case):
    orig_npy = conda_build.config.config.CONDA_NPY
    orig_py = conda_build.config.config.CONDA_PY

    for pkg, version in case:
        version = int(version.replace('.', ''))
        if pkg == 'python':
            conda_build.config.config.CONDA_PY = version
        elif pkg == 'numpy':
            conda_build.config.config.CONDA_NPY = version
        else:
            raise NotImplementedError('Package {} not yet implemented.'
                                      ''.format(pkg))
    yield
    conda_build.config.config.CONDA_NPY = orig_npy
    conda_build.config.config.CONDA_PY = orig_py


def conda_special_versions(meta, index, version_matrix=None):
    """
    Returns a generator which configures conda build's PY and NPY versions
    according to the given version matrix. If no version matrix is given, it
    will be computed by :func:`special_case_version_matrix`.

    """
    if version_matrix is None:
        version_matrix = special_case_version_matrix(meta, index)

    for case in version_matrix:
        with setup_vn_mtx_case(case):
            yield case


def special_case_version_matrix(meta, index):
    """
    Return the non-orthogonal version matrix for special software within conda
    (numpy, python).

    For example, supposing there was a numpy 1.8 & 1.9 for python 2.7,
    but only a numpy 1.9 for python 3.5, the matrix should be:

        ([('python', '2.7.0'), ('numpy', '1.8.0')],
         [('python', '2.7.0'), ('numpy', '1.9.0')],
         [('python', '3.5.0'), ('numpy', '1.9.0')])

    Packages which don't depend on any of the special cases will return an
    iterable with an empty list, so that code such as:

    for case in special_case_version_matrix(...):
        ... setup the case ...
        ... build ...

    can be written provided that the process which handles the cases can handle
    an empty list.

    .. note::

        This algorithm does not deal with PERL and R versions at this time.

    """
    r = conda.resolve.Resolve(index)
    requirements = meta.get_value('requirements/build', [])
    requirement_specs = {MatchSpec(spec).name: MatchSpec(spec)
                         for spec in requirements}

    # Thanks to https://github.com/conda/conda-build/pull/493 we no longer need to
    # compute the complex matrix for numpy versions unless a specific version has
    # been defined.
    np_spec = requirement_specs.get('numpy')
    if np_spec and np_spec.spec == 'numpy':
        # A simple spec (just numpy) has been defined, so we can drop it from the
        # special cases.
        requirement_specs.pop('numpy')

    def minor_vn(version_str):
        """
        Take an string of the form 1.8.2, into integer form 1.8
        """
        return '.'.join(version_str.split('.')[:2])

    cases = []

    with override_conda_logging(logging.WARN):
        if 'numpy' in requirement_specs:
            np_spec = requirement_specs.pop('numpy')
            for numpy_pkg in r.get_pkgs(np_spec):
                np_vn = minor_vn(index[numpy_pkg.fn]['version'])
                numpy_deps = index[numpy_pkg.fn]['depends']
                numpy_deps = {MatchSpec(spec).name: MatchSpec(spec)
                              for spec in numpy_deps}
                # This would be problematic if python wasn't a dep of numpy.
                for python_pkg in r.get_pkgs(numpy_deps['python']):
                    # XXX Get the python spec here too...?
                    py_vn = minor_vn(index[python_pkg.fn]['version'])
                    case = (('python', py_vn),
                            ('numpy', np_vn),
                            )
                    if case not in cases:
                        cases.append(case)
        elif 'python' in requirement_specs:
            py_spec = requirement_specs.pop('python')
            for python_pkg in r.get_pkgs(py_spec):
                py_vn = minor_vn(index[python_pkg.fn]['version'])
                case = (('python', py_vn), )
                if case not in cases:
                    cases.append(case)

        if 'perl' in requirement_specs:
            raise NotImplementedError('PERL version matrix not yet implemented.')
        if 'r' in requirement_specs:
            raise NotImplementedError('R version matrix not yet implemented.')

    # We only want the special cases.
#     cases = list(filter_cases(cases, index, requirement_specs.keys()))

    # Put an empty case in to allow simple iteration of the results.
    if not cases:
        cases.append(())

    return set(cases)


def filter_cases(cases, index, extra_specs):
    """
    cases might look like:

        cases = ([('python', '2.7'), ('numpy', '1.8')],
                 [('python', '2.7'), ('numpy', '1.9')],
                 [('python', '3.5'), ('numpy', '1.8')],
                 )

    Typically extra_specs comes from the environment specification.

    """
    r = conda.resolve.Resolve(index)
    additional_specs = []
    for spec in extra_specs:
        try:
            # no stdout, stderror logging unless in "crazy" mode.
            r.get_pkgs(conda.resolve.MatchSpec(conda.resolve.MatchSpec(spec).name))
        except conda.resolve.NoPackagesFound:
            pass
        else:
            additional_specs.append(spec)
    for case in cases:
        specs = ['{} {}.*'.format(pkg, version) for pkg, version in case]
        specs = additional_specs + ['{} {}.*'.format(pkg, version)
                               for pkg, version in case]
        try:
            with override_conda_logging(logging.WARN):
                r.solve(specs, max_only=False)
        except SystemExit as err:
            # Output the useful message along the lines of "the following
            # packages conflict with each other".
            stdout.debug(str(err) + '\n')
        else:
            yield case

