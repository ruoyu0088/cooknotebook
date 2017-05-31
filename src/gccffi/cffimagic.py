import hashlib
import sys
import os
from os import path
import time
import subprocess
import tempfile
import warnings
from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.paths import get_ipython_cache_dir
from IPython.core import magic_arguments
import cffi
from pycparser import parse_file, c_ast, c_generator


FakeIncludePath = path.join(path.dirname(__file__), "fake_libc_include")


def get_c_declares(filename, include_folders=(), cpp_path="gcc"):
    include_folders = (FakeIncludePath, ) + include_folders
    includes = ["-I{}".format(folder) for folder in include_folders]
    ast = parse_file(filename, use_cpp=True, cpp_path=cpp_path,
                     cpp_args=["-E"] + includes)
    declares = []
    generator = c_generator.CGenerator()

    for child in ast.ext:
        if isinstance(child, c_ast.FuncDef):
            declares.append(generator.visit(child.decl))
        else:
            declares.append(generator.visit(child))
    code = ";\n".join(declares) + ";"
    return code


class CffiBuilder:

    def __init__(self, code, folder=None, filename=None):
        self.code = code
        if folder is None:
            self.folder = tempfile.mkdtemp()
        else:
            self.folder = folder

        if filename is None:
            self.src_filename = tempfile.mktemp(suffix=".c", dir=self.folder)
        else:
            self.src_filename = path.join(self.folder, filename + ".c")

        self.dll_filename = path.splitext(self.src_filename)[0] + ".dll"

        try:
            self.gcc_path = subprocess.check_output(["where", "gcc"], shell=True).decode().split("\n")[0].strip()
        except subprocess.CalledProcessError:
            raise FileNotFoundError("Can't find gcc command in PATH")

    def build(self):
        with open(self.src_filename, "w") as f:
            f.write(self.code)

        cmd = ["gcc", "-shared", "-o", self.dll_filename, self.src_filename]
        subprocess.call(cmd, cwd=self.folder, shell=True)

    def load(self):
        ffi = cffi.FFI()
        ffi.cdef(get_c_declares(self.src_filename, cpp_path=self.gcc_path))

        lib = ffi.dlopen(self.dll_filename)
        return ffi, lib


class FlattenAttr:

    def __init__(self, *objs):
        self.__names = []
        for name, obj in objs:
            self.__dict__[name] = obj
            self.__names.append(name)

    def __getattr__(self, attr):
        for name in self.__names:
            obj = self.__dict__[name]
            res = getattr(obj, attr, None)
            if res is not None:
                return res

    def __str__(self):
        objs = [(name, self.__dict__[name]) for name in self.__names]
        return self.__class__.__name__ + str(objs)

    def __repr__(self):
        return str(self)


@magics_class
class CffiMagic(Magics):
    def __init__(self, shell):
        super().__init__(shell)

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '-n', '--name', default="c",
        help="Specify a name for the return object"
    )
    @magic_arguments.argument(
        '-i', '--insert', action='store_true', default=False,
        help="Insert functions to ipython namespace"
    )
    @magic_arguments.argument(
        '-f', '--force', action='store_true', default=False,
        help="Force the compilation"
    )
    @cell_magic
    def cffi(self, line, cell):
        """Compile c code to DLL by gcc and load it by cffi
        """
        args = magic_arguments.parse_argstring(self.cffi, line)
        lib_dir = path.join(get_ipython_cache_dir(), 'cffibuilder')
        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)

        key = cell, sys.version_info, sys.executable
        if args.force:
            key += time.time()

        filename = "_cffi_" + hashlib.md5(str(key).encode("utf-8")).hexdigest()

        builder = CffiBuilder(cell, folder=lib_dir, filename=filename)

        if not all(path.exists(path.join(lib_dir, filename + ext)) for ext in (".c", ".dll")):
            builder.build()

        try:
            current_obj = self.shell.ev(args.name)
            if current_obj.__class__.__name__ != "FlattenAttr":
                warnings.warn("{} overwrited".format(args.name))
        except NameError:
            pass

        ffi, lib = builder.load()
        res = FlattenAttr(("ffi", ffi), ("lib", lib))
        self.shell.push({args.name: res})

        if args.insert:
            self.shell.push({name:getattr(lib, name) for name in dir(lib)})
