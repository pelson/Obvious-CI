#!/usr/bin/env python
import os
import subprocess
import yaml


def conda_packages(conda_package_root):
    """A generator of (package_name, package_dir, meta_yaml_filename)."""
    for package_name in os.listdir(conda_package_root):
        package_dir = os.path.join(conda_package_root, package_name)
        meta_yaml = os.path.join(package_dir, 'meta.yaml') 
        if os.path.isdir(package_dir) and os.path.exists(meta_yaml):
            yield (package_name, package_dir, meta_yaml)


def build_deps(meta_yaml_fname):
    """
    Return a list of the build dependencies listed in the
    given meta.yaml fname.

    """
    with open(meta_yaml_fname, 'r') as fh:
        meta = yaml.load(fh)
        build_req = meta.get('requirements', {}).get('build', [])
    return [build_dep.split(' ', 1)[0] for build_dep in (build_req or [])]


def conda_package_dependencies(packages):
    """
    Return the build dependencies for each package which are to be built
    as conda recipes before the named package can be built.

    The return value is a dictionary mapping:

        {package_name: [packages_to_build_before_the_named_package]}

    """
    package_names = [name for (name, _, _) in packages]

    package_deps = {}
    for name, directory, meta_yaml_fname in packages:
        dependencies = package_deps.setdefault(name, [])
        for build_dep in build_deps(meta_yaml_fname):
            if build_dep in package_names:
                dependencies.append(build_dep)

    return package_deps


def resolve_dependencies(package_dependencies):
    """
    Given a dictionary mapping a package to its dependencies, return a
    generator of packages to install, sorted by the required install
    order.

    >>> deps = resolve_dependencies({'a': ['b', 'c'], 'b': ['c'],
                                     'c': ['d'], 'd': []})
    >>> list(deps)
    ['d', 'c', 'b', 'a']

    """
    remaining_dependencies = package_dependencies.copy()
    completed_packages = []

    # A maximum of 10000 iterations. Beyond that and there is probably a
    # problem.
    for failsafe in xrange(10000):
        for package, deps in sorted(remaining_dependencies.copy().items()):
            if all(dependency in completed_packages for dependency in deps):
                completed_packages.append(package)
                remaining_dependencies.pop(package)
                yield package
            else:
                # Put a check in to ensure that all the dependencies were
                # defined as packages, otherwise we will never succeed.
                for dependency in deps:
                    if dependency not in package_dependencies:
                        msg = ('The package {} depends on {}, but it was not '
                               'part of the package_dependencies dictionary.'
                               ''.format(package, dependency))
                        raise ValueError(msg)

        # Close off the loop if we've completed the dependencies.
        if not remaining_dependencies:
            break
    else:
        raise ValueError('Dependencies could not be resolved. '
                         'Remaining dependencies: {}'
                         ''.format(remaining_dependencies))


def build_package(package_name, root):
    # Note: dependencies need to be installed - this is not currently implemented.
    return subprocess.check_call(['conda', 'build', package_name], cwd=root)


def package_exists_on_binstar(package, root_dir):
    package_fname = subprocess.check_output(['conda', 'build', package, '--output'],
                                            cwd=root_dir).strip()

    # Figure out if this package has already been uploaded.
    binstar = get_binstar()
    try:
        package_info = binstar.package('pelson', package)
    except binstar_client.errors.NotFound:
        package_exists = False
    else:
        package_exists = True

    base_package_fname = os.path.basename(package_fname)
    package_os = os.path.basename(os.path.dirname(package_fname))
    upload_name = '{}/{}'.format(package_os, base_package_fname)

    if package_exists:
        exists = False
        for release in package_info['releases']:
            if upload_name in release['distributions']:
                exists = True
                break
    return exists


def main():
    # Look in ../../ from this script.
    conda_recipes_root = os.path.dirname(os.path.dirname(
                                os.path.dirname(os.path.abspath(__file__))))
    print('Looking for packages in {}'.format(conda_recipes_root))
    packages = sorted(conda_packages(conda_recipes_root))

    names = [name for name, _, _ in packages]
    print('Found {} packages: \n\t{}'.format(len(packages),
                                               '\n\t'.join(sorted(names))))

    package_dependencies = conda_package_dependencies(packages)
    resolved_dependencies = list(resolve_dependencies(package_dependencies))
    print('Resolved dependencies, will be built in the following order: \n\t{}'.format(
               '\n\t'.join(resolved_dependencies)))
    for package in resolved_dependencies:
        print('\n'.join(['-' * 80] * 4))
        print('Building {} from {}'.format(package, conda_recipes_root))
        print('\n'.join(['-' * 80] * 4))
        if not package_exists_on_binstar(package):
            build_package(package, root=conda_recipes_root)


if __name__ == '__main__':
    main()
