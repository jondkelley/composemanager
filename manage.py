#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

# pip install paver==1.3.4

"""

Usage:
    manage.py build --force (--phpfpm | --memcached | --nginx | --all ) [-e OVERLOAD_ENVIRONMENT, -v ENVIRONMENT]
    manage.py up (--phpfpm | --memcached | --nginx | --all ) [--force] [-e OVERLOAD_ENVIRONMENT, -v ENVIRONMENT]
    manage.py devil_up (--phpfpm | --memcached | --nginx | --all ) [--force] [-e OVERLOAD_ENVIRONMENT, -v ENVIRONMENT]
    manage.py start (--phpfpm | --memcached | --nginx | --all ) [--force] [-e OVERLOAD_ENVIRONMENT, -v ENVIRONMENT]
    manage.py stop (--phpfpm | --memcached | --nginx | --all ) [--force] [-e OVERLOAD_ENVIRONMENT, -v ENVIRONMENT]
    manage.py restart (--phpfpm | --memcached | --nginx | --all ) [--force] [-e OVERLOAD_ENVIRONMENT, -v ENVIRONMENT]
    manage.py kill (--phpfpm | --memcached | --nginx | --all ) [--force] [-e OVERLOAD_ENVIRONMENT, -v ENVIRONMENT]
    manage.py rm (--phpfpm | --memcached | --nginx | --all ) [--force] [-e OVERLOAD_ENVIRONMENT, -v ENVIRONMENT]
    manage.py top --all
    manage.py ps --all
    manage.py images --all
    manage.py implode [--force]
    manage.py prune [--force]
    manage.py open

Arguments:
    ENVIRONMENT             relative file path (for default environment vars)
    OVERLOAD_ENVIRONMENT    relative file path (for overloading environment vars)
    SSH_KEYFILE             path to ssh key file (RSA/DSA)

Options:
    -h                                                                 show this message
    -v ENVIRONMENT, --default_environment ENVIRONMENT                  default inherited ENVIRONMENT VARS file for this environment.
                                                                       [default: ./env_vars/local.env]
    -e OVERLOAD_ENVIRONMENT, --env_overload OVERLOAD_ENVIRONMENT       overload default ENVIRONMENT VARS with development values
    -k SSH_KEYFILE, --sshkey SSH_KEYFILE                               if not using --sourcecode local, define path to your ssh key
                                                                       [default: ~/.ssh/id_rsa]
    --force                                                            force option

"""
try:
    from paver.easy import path, pushd
    from paver.easy import sh as bash
except:
    x = "*"*128
    message = ("{x}\n{x}\n{x}\nYou're missing the paver module,"
               " you are going to get pushd() or bash() undefin"
               "ed errors.\n    Please run:\n        pip instal"
               "l paver==1.3.4\n{x}\n{x}\n{x}\n").format(x=x)
    print(message)
    exit(1)
from operator import methodcaller
from docopt import docopt
from manageutil import get_arg_option
from manageutil import print_arguements
from manageutil import export_environment_from_file
from manageutil import build_env_vars
from manageutil import q_confirm
from manageutil import move_source_code_to_build_space
from manageutil import AnsiColor as color
from manageutil import inject_env_vars
from manageutil import TempRsaKey
from manageutil import docker_implode
from manageutil import docker_purge
import managelog
from managelog import log as logger
import sys
import os


def log_compose_complete():
    """
    log when docker compose completes, for some defining seperating in build output
    """
    FULLOFSTARS = "*"*14
    logger.debug(
        "{stars}docker-compose completed{stars}".format(stars=FULLOFSTARS))


def log_star(message):
    """
    log stars around some text
    """
    FULLOFSTARS = "*"*3
    logger.debug("{stars}{message}{stars}".format(
        message=message, stars=FULLOFSTARS))

class ActionClass(object):
    """
    base class methods for meta functions (up/stop/restart/kill/rm) etc
    for inheritance / code de-duplication
    argument:
        args (dict): the docopt arguements
    """

    def __init__(self, args):
        print_arguements(args)
        self.all_project_directories = ['./docker-composes/shipping_cluster', './docker-composes/calls_cluster', './docker-composes/contact_cluster',
                './docker-composes/billing_cluster', './docker-composes/warehouse_cluster', './docker-composes/ordering_cluster']
        self.args = args
        # arg parsing
        environment_file = self.args['--default_environment']
        environment_overload_file = self.args.get('--env_overload', None)
        self.environment_vars = build_env_vars(environment_file)
        if environment_overload_file:
            self.environment_vars = build_env_vars(
                environment_overload_file, overload=True, current_environment=self.environment_vars)
        if self.args.get('--force', False):
            self.forceflag = "-f"
        else:
            self.forceflag = ""

        # end arg parsing
        self.daemonflag = ""
        self.action_verb = ""

    def all(self):
        """ chain it all together """
        self.phpfpm()
        self.memcached()
        self.nginx()

    def phpfpm(self):
        """
        service target
        """
        compose_service = "php"
        compose_cmd = "{env_vars} docker-compose {cmd} {dflag} {fflag} {svc}".format(
            fflag=self.forceflag, dflag=self.daemonflag, cmd=self.docker_compose_action, svc=compose_service,
            env_vars=self.environment_vars)
        logger.info("{action} container {svc}...".format(action=self.action_verb, svc=compose_service))
        # with pushd('./run/local'):
        #     bash(compose_cmd)
        try:
            bash("cp -fv devilbox.d/docker-compose.override.yml run/devilboxx/docker-compose.override.yml")
            bash("cp -fv run/devilboxx/env-example run/devilboxx/.env")
        except:
            pass # theres an arg to bash() but the paver docs suck ass for me right now
        with pushd('./run'):
            with pushd('./devilboxx'):
                bash(compose_cmd)
            bash("rm -fv devilboxx/docker-compose.override.yml")

    def memcached(self):
        """
        service target
        """
        compose_service = "memcd"
        compose_cmd = "{env_vars} docker-compose {cmd} {dflag} {fflag} {svc}".format(
            fflag=self.forceflag, dflag=self.daemonflag, cmd=self.docker_compose_action, svc=compose_service,
            env_vars=self.environment_vars)
        logger.info("{action} container {svc}...".format(action=self.action_verb, svc=compose_service))
        # with pushd('./run/local'):
        #     bash(compose_cmd)
        try:
            bash("cp -fv devilbox.d/docker-compose.override.yml run/devilboxx/docker-compose.override.yml")
            bash("cp -fv run/devilboxx/env-example run/devilboxx/.env")
        except:
            pass # theres an arg to bash() but the paver docs suck ass for me right now
        with pushd('./run'):
            with pushd('./devilboxx'):
                bash(compose_cmd)
            bash("rm -fv devilboxx/docker-compose.override.yml")

    def nginx(self):
        """
        service target
        """
        compose_service = "httpd"
        compose_cmd = "{env_vars} docker-compose {cmd} {dflag} {fflag} {svc}".format(
            fflag=self.forceflag, dflag=self.daemonflag, cmd=self.docker_compose_action, svc=compose_service,
            env_vars=self.environment_vars)
        logger.info("{action} container {svc}...".format(action=self.action_verb, svc=compose_service))
        # with pushd('./run/local'):
        #     bash(compose_cmd)
        bash("cp -fv devilbox.d/docker-compose.override.yml run/devilboxx/docker-compose.override.yml")
        bash("cp -fv run/devilboxx/env-example run/devilboxx/.env")

        with pushd('./run'):
            with pushd('./devilboxx'):
                bash(compose_cmd)
            bash("rm -fv devilboxx/docker-compose.override.yml")

class Build(ActionClass):
    """
    builds local containers
    argument:
        args (dict): the docopt arguements
    """

    def __init__(self, args):
        super(Build, self).__init__(args) # magic to call ActionClass().__init__()

        if self.args.get('--force', False):
            self.forceflag = "--force-rm --no-cache"
        else:
            self.forceflag = ""
        self.docker_compose_action = "build"
        self.action_verb = "building"

class Up(ActionClass):
    """
    brings containers up (builds if needed)
    argument:
        args (dict): the docopt arguements
    """

    def __init__(self, args):
        super(Up, self).__init__(args) # magic to call ActionClass().__init__()
        self.docker_compose_action = "up"
        self.daemonflag = "-d"
        if self.forceflag != "":
            self.forceflag = "--build"
        else:
            self.forceflag = ""
        self.action_verb = "starting"


class Kill(ActionClass):
    """
    force stop containers
    argument:
        args (dict): the docopt arguements
    """

    def __init__(self, args):
        super(Kill, self).__init__(args) # magic to call ActionClass().__init__()
        self.docker_compose_action = "kill"
        self.action_verb = "killing"
        if self.forceflag != "":
            logger.error("ignoring --force unsupported option")
            self.forceflag = "" # force flag wont work


class Stop(ActionClass):
    """
    gracefully stops containers
    argument:
        args (dict): the docopt arguements
    """

    def __init__(self, args):
        super(Stop, self).__init__(args) # magic to call ActionClass().__init__()
        self.docker_compose_action = "stop"
        self.action_verb = "stopping"
        if self.forceflag != "":
            logger.error("ignoring --force unsupported option")
            self.forceflag = "" # force flag wont work


class Restart(ActionClass):
    """
    restarts containers
    argument:
        args (dict): the docopt arguements
    """

    def __init__(self, args):
        super(Restart, self).__init__(args)
        self.docker_compose_action = "restart"
        self.action_verb = "restarting"
        if self.forceflag != "":
            logger.error("ignoring --force unsupported option")
            self.forceflag = "" # force flag wont work

class Rm(ActionClass):
    """
    deletes container images
    argument:
        args (dict): the docopt arguements
    """

    def __init__(self, args):
        super(Rm, self).__init__(args)
        self.docker_compose_action = "rm"
        self.action_verb = "removing"

class Top(ActionClass):
    """
    docker-compose top
    """
    def __init__(self, args):
        super(Top, self).__init__(args)

    def all(self):
        compose_cmd = "{env_vars} docker-compose top".format(env_vars=self.environment_vars)
        for directory in self.all_project_directories:
            with pushd(directory):
                logger.info("running top from {}/docker-compose.yml".format(directory))
                bash(compose_cmd)

class Ps(ActionClass):
    """
    docker-compose ps
    """
    def __init__(self, args):
        super(Ps, self).__init__(args)

    def all(self):
        compose_cmd = "{env_vars} docker-compose ps".format(env_vars=self.environment_vars)
        for directory in self.all_project_directories:
            logger.info("running ps from {}/docker-compose.yml".format(directory))
            with pushd(directory):
                bash(compose_cmd)
        logger.info("raw docker ps outpout".format(directory))
        bash("docker ps")

class Images(ActionClass):
    """
    docker-compose images
    """
    def __init__(self, args):
        super(Images, self).__init__(args)

    def all(self):
        compose_cmd = "{env_vars} docker-compose images".format(env_vars=self.environment_vars)
        for directory in self.all_project_directories:
            with pushd(directory):
                logger.info("getting images from {}/docker-compose.yml".format(directory))
                bash(compose_cmd)
        logger.info("raw docker images outpout".format(directory))
        bash("docker images")

def arg_to_class_adapter(args, name):
    """
    dynamically instanciate a special class to accept our commands by function name and stuff
    """
    class_by_name = getattr(sys.modules[__name__], name)
    _metaclass = class_by_name(args)
    _metaargs = get_arg_option(args)
    getattr(_metaclass, _metaargs)()


def main():
    """
    parse top level cli interface and invoke subcommands
    """
    args = docopt(__doc__, version="0.2.0")

    call_main = methodcaller('main')

    # test if a top level command is sent, then dynamically spawn the corresponding
    # class if neccessary
    if if args.get('build', None):
        arg_to_class_adapter(name="Build", args=args)
        bash("docker images")
    elif args.get('up', None):
        arg_to_class_adapter(name="Up", args=args)
        bash("docker ps")
    elif args.get('start', None):
        arg_to_class_adapter(name="Up", args=args)
        bash("docker ps")
    elif args.get('kill', None):
        arg_to_class_adapter(name="Kill", args=args)
    elif args.get('stop', None):
        arg_to_class_adapter(name="Stop", args=args)
    elif args.get('restart', None):
        arg_to_class_adapter(name="Restart", args=args)
    elif args.get('rm', None):
        arg_to_class_adapter(name="Rm", args=args)
    elif args.get('top', None):
        arg_to_class_adapter(name="Top", args=args)
    elif args.get('ps', None):
        arg_to_class_adapter(name="Ps", args=args)
    elif args.get('images', None):
        arg_to_class_adapter(name="Images", args=args)
    elif args.get('implode', None):
        docker_implode(args)
    elif args.get('prune', None):
        docker_purge(args)
    elif args.get('open', None):
        bash("open http://localhost")
    else:
        raise ArguementError("Invalid arguement and docopt failed to catch it!!!")

if __name__ == '__main__':
    main()
