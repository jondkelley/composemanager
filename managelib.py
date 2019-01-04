#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8


import re
import logging
import os
import sys
from paver.easy import path, pushd
from paver.easy import sh as bash


logger = logging.getLogger(__name__)


def docker_implode(args):
    """
    implodes a docker environment
    """
    pass

def docker_purge(args):
    """
    purges docker images
    """
    pass

if sys.version_info >= (3, 0):
    # Python 3
    class TempRsaKey():
        """
        a context manager class to *temporarily* copy an ssh keyfile to a docker
        build space. on class __exit__ the ssh key is replaced with dummy_key_content

        usage example:
            temporary_rsa_key = TempRsaKey(keyfile="~/.ssh/id_rsa", location="build/id_rsa")

        """

        def __init__(self, key=None, location=None, ):
            logger.warn('__init__')
            self.key = key  # original private key location
            self.templocation = location  # location to copy temp file to
            self.dummy_key_content = "------ REPLACE WITH YOUR PRIVATE KEY ------"

        def __enter__(self):
            """
            __enter__ is a python magic function that is called on class instantication
            """
            logger.warn('__enter__')
            if self.key:
                bash("cp -fv {key} {location}".format(key=self.key,
                                                      location=self.templocation))
                bash(
                    "chmod -v 0600 {location}".format(location=self.templocation))
                logger.warn("SSH key copied over dummy key (pre build)")
            return self

        def __exit__(self, exc_type, exc_value, exc_traceback):
            """
            __exit__ is a python magic function that is called on context termination
            """
            logger.warn('__exit__')
            if exc_type:
                print('exc_type: {exc_type}'.format(exc_type=exc_type))
                print('exc_value: {exc_value}'.format(exec_value=exec_value))
                print('exc_traceback: {exc_traceback}'.format(
                    exec_traceback=exec_traceback))
            if self.key:
                with open(self.templocation, "w") as file:
                    file.write(self.dummy_key_content)
                logger.warn("SSH key replaced with a dummy key (post build)")
else:
    # Python 2
    class TempRsaKey(object):
        def __init__(self, key=None, location=None):
            self.key = key
            self.templocation = location
            self.dummy_key_content = "------ REPLACE WITH YOUR PRIVATE KEY ------"

        def __enter__(self):
            logger.warn('__enter__')
            if self.key:
                bash("cp -fv {key} {location}".format(key=self.key,
                                                      location=self.templocation))
                bash(
                    "chmod -v 0600 {location}".format(location=self.templocation))
                logger.warn("SSH key copied over dummy key (pre build)")
            return self

        def __exit__(self, type, value, traceback):
            if self.key:
                with open(self.templocation, "w") as file:
                    file.write(self.dummy_key_content)
                logger.warn("SSH key replaced with a dummy key (post build)")
# endif

def inject_env_vars(env_vars, **kwargs):
    """
    helper function
    inject additional environment variables into an existing string of EXPORT statements.
    takes a string of arguements to append into the existing export string.
    """
    reg = re.compile('(?P<name>\w+)(\=(?P<value>.+))*')
    logger.warn("-")
    print("{green}***************************************************\n"
          "ENVIRONMENT VARIABLES ({red}from manage.py{green})\n"
          "    Exporting to docker-compose for your Dockerfile\n"
          "***************************************************{reset}".format(
              red=AnsiColor.red, green=AnsiColor.green, reset=AnsiColor.end
          )
          )
    if sys.version_info >= (3, 0):
        # Python 3
        for k, v in kwargs.items():
            if v:
                env_vars = "{env_vars} export {k}={v};".format(
                    env_vars=env_vars, k=k, v=v)
                print("{green}export {key}={value}{reset}".format(
                    green=AnsiColor.green, key=k, value=v, reset=AnsiColor.end))
    else:
        # Python2
        for k, v in kwargs.iteritems():
            if v:
                env_vars = "{env_vars} export {k}={v};".format(
                    env_vars=env_vars, k=k, v=v)
                print("{green}export {key}={value}{reset}".format(
                    green=AnsiColor.green, key=k, value=v, reset=AnsiColor.end))
    return env_vars


def export_environment_from_file(file, overload=False):
    """
    helper function
    Opens an environment file and runs BASH exports to the os.environ
    (in PHP this is commonly known as $_ENV)
    """
    vars = {}
    overload_text = [
        "ENVIRONMENT VARIABLES ({red}from {file}{green})".format(
            red=AnsiColor.red, file=file, green=AnsiColor.green
        ) if not overload
        else
        "{red}%%%%%%%%%%%%%% OVERLOADED VARIABLES %%%%%%%%%%%%%%% from {source}{green}".format(
            source=file, red=AnsiColor.red, green=AnsiColor.green
        )
    ][0]
    reg = re.compile('(?P<name>\w+)(\=(?P<value>.+))*')
    logger.warn("-")
    print("{green}***************************************************\n"
          "{overload_text}\n"
          "    Exporting to docker-compose for your Dockerfile\n"
          "***************************************************{reset}".format(
              overload_text=overload_text,
              green=AnsiColor.green,
              reset=AnsiColor.end
          )
          )
    try:
        for line in open(file):
            m = reg.match(line)
            if m:
                name = m.group('name')
                value = ''
                if m.group('value'):
                    value = m.group('value')
                #os.putenv(name, value)
                print("{green}export {name}={value}{reset}".format(
                    green=AnsiColor.green, name=name, value=value, reset=AnsiColor.end))
                os.environ[name] = value
                vars[name] = value
    except Exception as e:
        logger.error(
            "Exception: Couldnt load environment from file: {}".format(e))
        exit(1)
    return vars


def build_env_vars(build_env_file=None, overload=False, current_environment=None):
    """
    helper function
    Sources the OS.ENVIRON variables used by docker as Dockerfile ENV parameters
    By default, local dev variables are loaded.
    A developer can change these and provide the `build_env_file` to load them from.
    """
    #print_banner("Source environment variables for docker boot")
    if overload:
        # overloading is a hack to allow a custom environment file load on top of a default.
        # this works by later EXPORT statements loading right on top of the pre-existing defaults
        if not build_env_file:
            logger.error(
                "build_env_vars(overload=true) requires the build_env_file parameter")
        if not current_environment:
            logger.error(
                "build_env_vars(overload=true) requires the current_environment parameter")
        overload_args = ""

        if sys.version_info >= (3, 0):
            # Python 3
            for key, value in export_environment_from_file(build_env_file, overload=True).items():
                overload_args = "{} export {}={};".format(
                    overload_args, key, value)
        else:
            # Python 2
            for key, value in export_environment_from_file(build_env_file, overload=True).iteritems():
                overload_args = "{} export {}={};".format(
                    overload_args, key, value)

        return current_environment + overload_args
    else:
        if not build_env_file:
            build_env_file = "env_vars/local.env"
        args = ""

        if sys.version_info >= (3, 0):
            # Python 3
            for key, value in export_environment_from_file(build_env_file, overload=False).items():
                args = "{} export {}={};".format(args, key, value)
        else:
            # Python 2
            for key, value in export_environment_from_file(build_env_file, overload=False).iteritems():
                args = "{} export {}={};".format(args, key, value)
        return args


def get_arg_option(args):
    for key, value in args.items():
        if (key != '--force' and key.startswith('--') and
                isinstance(value, bool) and value):
            return key.replace('-', '')


def print_arguements(args):
    """
    prints a pretty format version of yorktown arguements
    """
    dash = '-' * 40
    print(AnsiColor.red)
    print("{}\n              Arguements\n{}".format(dash, dash))
    print("{}{{{}".format(AnsiColor.blue, AnsiColor.yellow))

    if sys.version_info >= (3, 0):
        for key, val in args.items():
            print('     {:<10s}: {:<10s}'.format(key, str(val)))
    else:
        for key, val in args.iteritems():
            print('     {:<10s}: {:<10s}'.format(key, str(val)))
    print("{}}}".format(AnsiColor.blue))
    print(AnsiColor.red)
    print("{}{}".format(dash, AnsiColor.end))


class AnsiColor(object):
    """
    life is better in color
    """
    header = '\033[95m'
    blue = '\033[1;94m'
    green = '\033[1;92m'
    yellow = '\033[93m'
    red = '\033[91m'
    end = '\033[0m'
    bold = '\033[1m'
    magenta = '\033[35m'
    underline = '\033[4m'
