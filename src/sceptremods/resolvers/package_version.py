import importlib
import sys
from sceptre.resolvers import Resolver

class PackageVersion(Resolver):

    def __init__(self, *args, **kwargs):
        super(PackageVersion, self).__init__(*args, **kwargs)

    def resolve(self):
        package_name = self.argument
        importlib.import_module(package_name)
        self.logger.debug('package_version: {}'.format(
                getattr(sys.modules[package_name], "__version__")))
        return getattr(sys.modules[package_name], "__version__", str())

