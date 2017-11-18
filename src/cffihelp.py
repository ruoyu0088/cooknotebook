def import_file(name, filename):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cffi_build(cdef, source, disable_py_limited_api=True, force=False, tmpdir=".\\__pycache__"):
    import cffi
    import time
    import hashlib
    import imp
    from os import path
    from distutils.sysconfig import get_config_var
    tmpdir = path.abspath(tmpdir)
    suffix = get_config_var('EXT_SUFFIX')
    key = cdef + source
    if force:
        key += time.time()
    filename = "_cffi_" + hashlib.md5(str(key).encode("utf-8")).hexdigest()
    full_filename = path.join(tmpdir, filename + suffix)
    if not path.exists(full_filename):
        ffi = cffi.FFI()
        extra_compile_args = ["-D_CFFI_USE_EMBEDDING"] if disable_py_limited_api else []
        ffi.set_source(filename, source, extra_compile_args=extra_compile_args)
        ffi.cdef(cdef)
        full_filename = ffi.compile(tmpdir=tmpdir)
    return import_file(filename, path.join(tmpdir, full_filename))