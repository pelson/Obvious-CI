import nose
from nose.tools import assert_equal, assert_false, assert_true, assert_not_equal
from unittest import expectedFailure
from conda_build.metadata import MetaData

import os

from obvci.conda_tools.build import build, upload
from obvci.conda_tools.build_directory import recipes_to_build, fetch_metas, sort_dependency_order
from obvci.conda_tools.inspect_binstar import distribution_exists
from obvci.conda_tools.inspect_binstar import distribution_exists_on_channel, add_distribution_to_channel

from binstar_client.utils import get_binstar
from argparse import Namespace


def clear_binstar(cli, owner):
    """
    Empty all distributions for a user.
    
    The "rm -rf *" of the binstar world.

    """
    for channel in cli.list_channels(owner):
        cli.remove_channel(owner, channel)

    for package in cli.user_packages(owner):
        cli.remove_package(owner, package['name'])


OWNER = 'Obvious-ci-tests'
CLIENT = get_binstar(Namespace(token=os.environ['BINSTAR_TOKEN'], site=None))
RECIPES_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'recipes')
RECIPES_DIR = os.path.join(RECIPES_ROOT, 'recipes_directory')
RECIPE_DEV = os.path.join(RECIPES_ROOT, 'recipe1_dev')


def test_distribution_exists():
    clear_binstar(CLIENT, OWNER)
 
    # Build a recipe.
    meta = MetaData(RECIPE_DEV)
    meta = build(meta)
 
    # Check distribution exists returns false when there is no distribution.
    assert_false(distribution_exists(CLIENT, OWNER, meta))
 
    # upload the distribution 
    upload(CLIENT, meta, OWNER, channels=['testing'])
 
    # Check the distribution exists. Notice there is no channel being supplied here.
    assert_true(distribution_exists(CLIENT, OWNER, meta))
 
    # Check the distribution is on testing but not on main.
    assert_true(distribution_exists_on_channel(CLIENT, OWNER, meta, channel='testing'))
    assert_false(distribution_exists_on_channel(CLIENT, OWNER, meta, channel='main'))
 
    add_distribution_to_channel(CLIENT, OWNER, meta, channel='main')
    # Check that the distribution has been added.
    assert_true(distribution_exists_on_channel(CLIENT, OWNER, meta, channel='main'))


def test_leaky_add_to_channel():
    # A newer distribution (e.g. v0.2.0.dev) on a dev channel was getting promoted to the main channel
    # when an earlier version (e.g. v0.1.0) was being linked to main.
    clear_binstar(CLIENT, OWNER)
    # Build a recipe and upload the recipe to the testing channel.
    meta = MetaData(RECIPE_DEV)
    meta = build(meta)
    upload(CLIENT, meta, OWNER, channels=['testing'])

    # Build a recipe and upload the recipe to the testing channel.
    meta_eariler = MetaData(os.path.join(RECIPES_DIR, 'recipe1'))
    meta_eariler = build(meta_eariler)
    upload(CLIENT, meta_eariler, OWNER, channels=['testing'])
    
    add_distribution_to_channel(CLIENT, OWNER, meta_eariler, channel='main')

    assert_true(distribution_exists_on_channel(CLIENT, OWNER, meta_eariler, channel='main'))
    assert_false(distribution_exists_on_channel(CLIENT, OWNER, meta, channel='main'))


def assert_metas_equal(result_metas, expected_metas):
    meta_name = lambda meta: meta.name()
    message = 'Metas differ:\n  LHS: {}\n  RHS: {}'.format(map(meta_name, result_metas),
                                                          map(meta_name, expected_metas))
    assert_equal(result_metas, expected_metas, msg=message)


def assert_metas_not_equal(result_metas, expected_metas):
    meta_name = lambda meta: meta.name()
    message = "Metas don't differ:\n  LHS: {}\n  RHS: {}".format(map(meta_name, result_metas),
                                                          map(meta_name, expected_metas))
    assert_not_equal(result_metas, expected_metas, msg=message)


def test_recipes_to_build():
    clear_binstar(CLIENT, OWNER)
  
    # Build a recipe.
    meta = build(MetaData(os.path.join(RECIPES_DIR, 'recipe1')))
    upload(CLIENT, meta, OWNER, channels=['testing'])
  
    metas = fetch_metas(RECIPES_DIR)
    metas.sort(key=lambda meta: meta.name())
  
    result = list(recipes_to_build(CLIENT, OWNER, channel='testing', recipe_metas=metas))
    # The ones we need to build are all but the first.
    assert_metas_equal(result, metas[1:])


def test_meta_sorting():
    metas = fetch_metas(RECIPES_DIR)
    unsorted_metas = sorted(metas, key=lambda meta: meta.name(), reverse=True)
    # The recipes have been constructed to sort in alphabetical order.
    assert_metas_equal(sort_dependency_order(unsorted_metas), [metas[0], metas[2], metas[1]])
    # Check that that is what was going on.
    assert_metas_not_equal(unsorted_metas, metas)


if __name__ == '__main__':
    nose.runmodule(argv=['-s', '--with-doctest'], exit=False)
