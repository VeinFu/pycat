#! /usr/bin/python

from setuptools import setup, find_packages
import platform
import re
import os

PLATFORM_LINUX = 10
PLATFORM_WINDOWS = 20

def get_platform():
    plat = platform.platform()
    ret = re.search("[Ll][Ii][Nn][Uu][Xx]", plat)
    if ret != None:
        return PLATFORM_LINUX
    else:
        ret = re.search("[Ww][Ii][Nn][Dd][Oo][Ww][Ss]", plat)
        if ret != None:
            return PLATFORM_WINDOWS
        else:
            raise ValueError("Unknown platform: %s" % plat)

def find_sysconfig_dir():
    sysconfig_dir = None
    plat = get_platform()
    if plat == PLATFORM_LINUX:
        sysconfig_dir = "/usr/etc/pycat"
    elif plat == PLATFORM_WINDOWS:
        sysconfig_dir =  "C:\User\Public\Documents\pycat\config"
    return sysconfig_dir

SYSCONFIG_DIR = find_sysconfig_dir()
PLUGIN_DIR = os.path.join(SYSCONFIG_DIR, "basic")
PMCSES_DIR = os.path.join(SYSCONFIG_DIR, "pmcses")
LSISES_DIR = os.path.join(SYSCONFIG_DIR, "lsises")
README = file("README.txt")

setup(
    name = "pycat",
    packages = find_packages(),
    version = "0.0.15",
    description = "Complex Analytic Test",
    long_description = README.read(),
    author = "VienFu",
    author_email = "chunfu@celestica.com",
    url = "https://sites.google.com/a/celestica.com/pycat/",
    classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Development Status :: 1 - Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    data_files = [(SYSCONFIG_DIR, ["README.txt",
                                   "COPYING.txt",
                                   "data/pycat.xml"]),
                  (PLUGIN_DIR, ["data/basic/ac-cycle.xml",
                                "data/basic/ac-source.xml",
                                "data/basic/bbu-performance.xml",
                                "data/basic/command-local-duration.xml",
                                "data/basic/command-local-loop.xml",
                                "data/basic/command-ssh.xml",
                                "data/basic/command-uart.xml",
                                "data/basic/command.xsd",
                                "data/basic/dc-cycle.xml",
                                "data/basic/fhd.xml",
                                "data/basic/fpga.xml",
                                "data/basic/os-device.xml"
                               ]),
                  (PMCSES_DIR, [
                                "data/pmcses/fw.xml",
                                "data/pmcses/i2c.xml",
                                "data/pmcses/phy.xml",
                                "data/pmcses/vpd.xml",
                                "data/pmcses/pmcses.xsd"]),
                  (LSISES_DIR, ["data/lsises/lsises.xml",
                                "data/lsises/lsises.xsd"])
                  ],
    install_requires = ["lxml", "paramiko"],
    entry_points = {
        "console_scripts" : [
            "cat-session = pycat.session:main"
        ],
       "pycat.plugin" : [
            "basic = basicplugin",
            "pmcses = pmcses",
            "lsises = lsises"
        ]
    }
)
