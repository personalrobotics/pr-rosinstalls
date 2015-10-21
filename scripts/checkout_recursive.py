#!/usr/bin/env python
from __future__ import print_function
from collections import namedtuple
import argparse
import sys
import os
import vcstools
import yaml
import rospkg
from catkin_pkg.package import parse_package

DEPENDENCY_TYPES =  [
    'build_depends',
    'build_export_depends',
    'buildtool_depends',
    'buildtool_export_depends',
    'doc_depends',
    'exec_depends',
    'test_depends',
]

class Repository(object):
    def __init__(self, name, options):
        self.name = name
        self.location = None

        source_dict = options.get('source')
        if source_dict is None:
            raise ValueError(
                'Repository "{:s}" is missing the "source" key.'.format(name))

        self.vcs_version = source_dict.get('version')
        self.packages = source_dict.get('packages', [name])

        self.vcs_type = source_dict.get('type')
        if self.vcs_type is None:
            raise ValueError(
                'Repository "{:s}" source settings is missing the "type"'
                ' field.'.format(name))

        self.vcs_uri = source_dict.get('url')
        if self.vcs_uri is None:
            raise ValueError(
                'Repository "{:s}" source settings is missing the "url"'
                ' field.'.format(name))


class Package(object):
    def __init__(self, name, repository):
        self.name = name
        self.repository = repository
        self.location = None


class WstoolClient(object):
    def __init__(self, directory, filename='.rosinstall'):
        self.directory = directory
        self.filename = filename

    def __enter__(self):
        import os.path.join

        self.rosinstall_file = open(
            os.path.join(self.directory, self.filename), 'r')
        self.rosinstall_file.__enter__()

        return self

    def __exit__(self, type, value, traceback):
        return self.rosinstall_file.__exit__(type, value, traceback)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=str, default='.')
    parser.add_argument('distribution_file', type=str)
    parser.add_argument('package_names', type=str, nargs='+')
    args = parser.parse_args()

    # Load the distribution file.
    with open(args.distribution_file, 'rb') as distribution_file:
        distribution_raw = yaml.load(distribution_file)

    packages_raw = distribution_raw.get('repositories')
    if packages_raw is None:
        raise ValueError('Distribution is missing the "repositories" key.')

    repositories = {
        name: Repository(name, options)
        for name, options in packages_raw.iteritems() }

    # Build a map from package name to the repository that contains it, based
    # soley on the information in the distribution file.
    distribution_package_map = dict()

    for repository in repositories.itervalues():
        for package_name in repository.packages:
            existing_repository = distribution_package_map.get(package_name)
            if existing_repository is not None:
                raise ValueError(
                    'Duplicate package "{:s}" in repositories "{:s}" and'
                    ' "{:s}".'.format(
                        package_name, existing_repository.name,
                        repository.name))

            distribution_package_map[package_name] = Package(
                package_name, repository)

    # Aggregate a map of packages that we know about.
    package_map = dict(distribution_package_map)
    done_packages = set() # installed and processed
    installed_packages = set() # installed, but not processed yet
    pending_packages = set(args.package_names)

    while pending_packages:
        package_name = pending_packages.pop()

        print('Processing package "{:s}"'.format(package_name))

        package = package_map.get(package_name)
        if package is None:
            raise ValueError(
                'Package "{:s}" is not in the distribution.'.format(
                    package_name))

        # Checkout the repository.
        repository = package.repository

        if repository.location is None:
            repository.location = os.path.join(args.workspace, repository.name)

            print('  Checking out "{:s}" repository => {:s}'.format(
                repository.name, repository.location))

            client = vcstools.get_vcs_client(
                repository.vcs_type, repository.location)

            if client.detect_presence():
                detected_url = client.get_url()

                if not client.url_matches(detected_url, repository.vcs_uri):
                    raise ValueError(
                        'Directory "{:s}" already contains a VCS repository with'
                        ' URL "{:s}". This does not match the requested URL'
                        ' "{:s}".'.format(repository_name, detected_url, repository.vcs_uri))

                client.update(version=repository.vcs_version)
            else:
                client.checkout(repository.vcs_uri, version=repository.vcs_version)

            # Search for packages in the repository.
            repository_package_map = dict()
            rospkg.list_by_path(
                manifest_name='package.xml',
                path=repository.location,
                cache=repository_package_map)

            if package.name not in repository_package_map:
                raise ValueError(
                    'Repository "{:s}" checked out from the "{:s}" repository'
                    ' "{:s}" does not contain the package "{:s}".'.format(
                        repository.name, repository.vcs_type,
                        repository.vcs_uri, package.name))

            # Mark all of these packages as installed.
            for package_name, location in repository_package_map.iteritems():
                installed_package = package_map.get(package_name)

                if installed_package is None:
                    installed_package = Package(package_name, repository)
                    package_map[package_name] = installed_package
                elif (installed_package.repository != repository or
                      installed_package.location is not None):
                    raise ValueError(
                        'Repository "{:s} installed duplicate package "{:s}"'
                        ' in directory "{:s}". This package was already installed'
                        ' by repository "{:s}" in directory "{:s}".'.format(
                            repository.name, package_name, location,
                            installed_package.repository.name,
                            installed_package.location))

                installed_package.location = location

                print('    Found package "{:s}" => {:s}'.format(
                    installed_package.name, installed_package.location))

            installed_packages.update(repository_package_map.iterkeys())

        # Crawl dependencies.
        package_xml_path = os.path.join(package.location, 'package.xml')
        package_manifest = parse_package(package_xml_path)

        all_depends = set()
        for dependency_type in DEPENDENCY_TYPES:
            for dependency in getattr(package_manifest, dependency_type):
                all_depends.add(dependency.name)

        # Only keep the dependencies that we know about.
        def annotate_package_name(package_name):
            if package_name in done_packages:
                return package_name + '*'
            elif package_name in installed_packages:
                return package_name + '^'
            else:
                return package_name

        known_depends = all_depends.intersection(
            distribution_package_map.iterkeys())
        if known_depends:
            print('  Depends on:', ' '.join(
                sorted(map(annotate_package_name, known_depends))))

        pending_packages.update(known_depends)

if __name__ == '__main__':
    main()
