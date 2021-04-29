def init():
    from reader.app import register_services
    register_services()
    # from importlib.abc import MetaPathFinder, Loader
    # import importlib
    # import sys

    # class MyLoader(Loader):
    #     # def module_repr(self, module):
    #     #     return repr(module)

    #     def load_module(self, fullname):
    #         breakpoint()
    #         module = importlib.import_module(f"datastore_{fullname}")
    #         sys.modules[fullname] = module
    #         return module

    # class MyImport(MetaPathFinder):
    #     def find_module(self, fullname, path=None):
    #         names = fullname.split(".")
    #         if names[0] in ("reader", "shared"):
    #             breakpoint()
    #             return MyLoader()


    # sys.meta_path.append(MyImport())
