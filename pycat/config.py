#! /usr/bin/python

"""
Config Module for pycat
"""

import os
import platform
import re
from lxml import etree

from pycat import log

_LOGGER = log.getLogger("log.config")

#--------------------------------------------------------------------------
#    config and cache
#--------------------------------------------------------------------------
PLATFORM_LINUX = 10
PLATFORM_WINDOWS = 20

def measure_platform():
    """
    Find out the platform type. Only support Linux and Windows.
    """
    plat = platform.platform()
    _LOGGER.debug("Run on %s", plat)
    ret = re.search("[Ll][Ii][Nn][Uu][Xx]", plat)
    if ret != None:
        return PLATFORM_LINUX
    else:
        ret = re.search("[Ww][Ii][Nn][Dd][Oo][Ww][Ss]", plat)
        if ret != None:
            return PLATFORM_WINDOWS
        else:
            raise ValueError("Unknown platform: %s" % plat)

WINDOWS_SYSCONFIG_DIR = r"C:\User\Public\Documents\pycat\config"
WINDOWS_CACHE_DEFAULT = [r"C:\User\Public\Documents\pycat\cache",
                         r"C:\pycat\cache"]
LINUX_SYSCONFIG_DIR = "/usr/etc/pycat"
LINUX_CACHE_DEFAULT = ["/var/pycat"]

class SysConfig(object):
    """
    A SysConfig instance will find the system config of pycat. If
    there's no config file existed, it will create a new one. The system
    config file named as 'pycat.xml'.

    pycat.xml:
    <pycat>
        <cache-list>
            <cache>dir</cache>
        <./cache-list>
    </pycat>

    On Linux, the default config directory is '/usr/etc/pycat'. On
    Windows, the default config directory is 'C:\\User\\Public\\Documents
    \\pycat\\config'. The 'pycat.xml' is stored in the config directory
    and every plugin will create a subdirectory under it. The directory
    tree looks like:
      config-dir
      |--pycat.xml
      |--basic
      |  |--command.xml
      |  |--command.xsd
      |...
    """
    config_dir = None
    config_file = "pycat.xml"
    config_fullpath = None
    def __init__(self, sysconfig_dir=None):
        if self.config_dir == None:
            if sysconfig_dir != None:
                self.config_dir = sysconfig_dir
            else:
                plat = measure_platform()
                if plat == PLATFORM_LINUX:
                    self.config_dir = LINUX_SYSCONFIG_DIR
                elif plat == PLATFORM_WINDOWS:
                    self.config_dir = WINDOWS_SYSCONFIG_DIR
            self._set_sysconfig()

    def _set_sysconfig(self):
        """
        Set the 'pycat.xml'. If it exists, validate it. If it's invalid or
        doesn't exist, create a new one.
        """
        reset = False
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, mode=0755)
        self.config_fullpath = os.path.join(self.config_dir, self.config_file)
        if os.path.exists(self.config_fullpath):
            # validate XML
            source = file(self.config_fullpath)
            try:
                tree = etree.parse(source)
                root = tree.getroot()
                if root.tag != "pycat":
                    reset = True
            except etree.XMLSyntaxError:
                reset = True
            source.close()
        else:
            reset = True
        if reset == True:
            file(self.config_fullpath, 'w')
            os.chmod(self.config_fullpath, 0777)
            root = etree.XML("<pycat/>")
            tree = etree.ElementTree(root)
            tree.write(self.config_fullpath)

    def get_sysconfig_dir(self):
        """
        Get system config directory.
        """
        return self.config_dir

    def get_sysconfig(self):
        """
        Get system config file path.
        """
        return self.config_fullpath

    def get_plugin_config_dir(self, plugin):
        """
        Get the config directory of a plugin.
        """
        plugin_dir = os.path.join(self.config_dir, plugin)
        return plugin_dir

class Cache(object):
    """
    A Cache instance supplys methods to access and modify cache directory.

    The paths of cache directories are stored in 'pycat.xml'(See 'class
    SysConfig'.) The default on Linux is '/tmp/pycat' and the default on
    Windows is 'C:\\User\\Public\\Documents\\pycat\\cache'.
    """
    cache_list = list()
    def __init__(self):
        if len(self.cache_list) == 0:
            sysconf = SysConfig()
            confsource = file(sysconf.get_sysconfig(), "a+")
            tree = etree.parse(confsource)
            root = tree.getroot()
            # Set default value
            cache_list_node = root.find("cache-list")
            cache_nodes = root.findall(".//cache")
            if cache_list_node == None or cache_nodes == None:
                plat = measure_platform()
                if plat == PLATFORM_LINUX:
                    cache_list = LINUX_CACHE_DEFAULT
                elif plat == PLATFORM_WINDOWS:
                    cache_list = WINDOWS_CACHE_DEFAULT
                if cache_list_node == None:
                    cache_list_node = etree.Element("cache-list")
                    root.append(cache_list_node)
                for cache in cache_list:
                    node = etree.Element("cache")
                    node.text = cache
                    cache_list_node.append(node)
                confsource.close()
            # Load cache from sysconfig to memory.
            cache_list_node = root.find("cache-list")
            for node in cache_list_node:
                self.cache_list.append(node.text)
                if not os.path.exists(node.text):
                    os.makedirs(node.text, 0755)
            tree.write(sysconf.get_sysconfig())

    def get_cache(self, subdir=None):
        """
        Get the directory of the cache which is using. If 'subdir' is given,
        this method will join the cache directory and the 'subdir' and return
        the full path.

        @todo wilson, Use the last one in cache list instead of the first one.
        """
        if not subdir:
            return self.cache_list[0]

        assert isinstance(subdir, str)
        cache_path = os.path.join(self.cache_list[0], subdir)
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        return cache_path

    def append(self, cache_path):
        """
        Append a new directory into the cache list.
        """
        assert isinstance(cache_path, str)
        if not os.path.exists(cache_path):
            os.makedirs(cache_path, 0755)
        sysconf = SysConfig()
        confsource = file(sysconf.get_sysconfig(), "a+")
        tree = etree.parse(confsource)
        root = tree.getroot()
        cache_list_node = root.find("cache-list")
        node = etree.Element("cache")
        node.text = cache_path
        cache_list_node.append(node)
        tree.write(sysconf.get_sysconfig())
        confsource.close()
        self.cache_list.append(cache_path)

    def remove(self, cache_path):
        """
        Remove a directory from the cache list.
        """
        assert isinstance(cache_path, str)
        sysconf = SysConfig()
        confsource = file(sysconf.get_sysconfig(), "a+")
        tree = etree.parse(confsource)
        root = tree.getroot()
        cache_list_node = root.find("cache-list")
        for node in cache_list_node:
            if node.text == cache_path:
                cache_list_node.remove(node)
        try:
            self.cache_list.remove(cache_path)
        except ValueError:
            pass
        tree.write(sysconf.get_sysconfig())

