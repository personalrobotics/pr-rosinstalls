#!/usr/bin/env python
from __future__ import print_function
from collections import namedtuple
import argparse
import sys
import yaml

class Repository(object):
    def __init__(self, name, options):
        self.packages = []

        source_dict = options.get('source')
        if source_dict is None:
            raise ValueError(
                'Repository "{:s}" is missing the "source" key.'.format(name))

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

        self.vcs_version = source_dict.get('version')
        self.packages = source_dict.get('packages', [name])


def main():
    parser = argparse.ArgumentParser()
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

    # Build a map from package name to the repository that contains it.
    package_map = dict()

    for repository in repositories.itervalues():
        for package_name in repository.packages:
            existing_repository = package_map.get(package_name)
            if existing_repository is not None:
                raise ValueError(
                    'Duplicate package "{:s}" in repositories "{:s}" and'
                    ' "{:s}".'.format(
                        package_name, existing_repository.name,
                        repository.name))

            package_map[package_name] = repository

    # 
    target_packages = list(args.package_names)
    pending_packages = set(target_packages)
    installed_packages = set()

    for package_name in pending_packages:
        repository = package_map.get(package_name)
        if repository is None:
            raise ValueError(
                'Package "{:s}" is not in the distribution.'.format(
                    package_name))

        print('TODO: checkout', repository.vcs_uri)
        installed_packages.union(repository.packages)

if __name__ == '__main__':
    main()
