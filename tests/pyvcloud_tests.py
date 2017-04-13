from nose.tools import with_setup
from testconfig import config
import pkg_resources

def test_0001():
    """Check version"""
    # print('version=%s' % pkg_resources.require("pyvcloud")[0].version)
    assert '16' == pkg_resources.require("pyvcloud")[0].version
