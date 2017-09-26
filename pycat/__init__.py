"""
Complex Analytic Test
"""

from pkg_resources import iter_entry_points

def load_plugin(plugin):
    """
    Load a python module which has installed as a plugin of pycat.
    """
    points = iter_entry_points(group="pycat.plugin", name=plugin)
    mod = None
    for point in points:
        mod = point.load()
    if mod == None:
        raise ValueError("Unknown plugin: %s" % (plugin))
    return mod
 

