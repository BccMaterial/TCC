import importlib
import inspect
import pkgutil
import sys

package = sys.modules[__name__]

for loader, name, is_pkg in pkgutil.walk_packages(
    package.__path__, package.__name__ + "."
):
    module = importlib.import_module(name)
    for attr_name, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__:
            setattr(package, attr_name, obj)
