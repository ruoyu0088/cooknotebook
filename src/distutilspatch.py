import sys
import copy
import os
from subprocess import check_output
from distutils import cygwinccompiler
from distutils.cygwinccompiler import UnixCCompiler, CygwinCCompiler, write_file


def get_msvcr():
    msc_pos = sys.version.find('MSC v.')
    if msc_pos != -1:
        msc_ver = sys.version[msc_pos+6:msc_pos+10]
        if msc_ver == '1300':
            # MSVC 7.0
            return ['msvcr70']
        elif msc_ver == '1310':
            # MSVC 7.1
            return ['msvcr71']
        elif msc_ver == '1400':
            # VS2005 / MSVC 8.0
            return ['msvcr80']
        elif msc_ver == '1500':
            # VS2008 / MSVC 9.0
            return ['msvcr90']
        elif msc_ver == '1600':
            # VS2010 / MSVC 10.0
            return ['msvcr100']
        elif msc_ver == '1700': #* Add new MSVC versions *#
            # Visual Studio 2012 / Visual C++ 11.0
            return ['msvcr110']
        elif msc_ver == '1800':
            # Visual Studio 2013 / Visual C++ 12.0
            return ['msvcr120']
        elif msc_ver == '1900':
            return ['msvcr140'] #
        else:
            raise ValueError("Unknown MS Compiler version %s " % msc_ver)

cygwinccompiler.__dict__["get_msvcr"] = get_msvcr


def link(self, target_desc, objects, output_filename, output_dir=None,
            libraries=None, library_dirs=None, runtime_library_dirs=None,
            export_symbols=None, debug=0, extra_preargs=None,
            extra_postargs=None, build_temp=None, target_lang=None):
    """Link the objects."""
    # use separate copies, so we can modify the lists
    extra_preargs = copy.copy(extra_preargs or [])
    libraries = copy.copy(libraries or [])
    objects = copy.copy(objects or [])

    # Additional libraries
    libraries.extend(self.dll_libraries)

    # handle export symbols by creating a def-file
    # with executables this only works with gcc/ld as linker
    if ((export_symbols is not None) and
        (target_desc != self.EXECUTABLE or self.linker_dll == "gcc")):
        # (The linker doesn't do anything if output is up-to-date.
        # So it would probably better to check if we really need this,
        # but for this we had to insert some unchanged parts of
        # UnixCCompiler, and this is not what we want.)

        # we want to put some files in the same directory as the
        # object files are, build_temp doesn't help much
        # where are the object files
        temp_dir = os.path.dirname(objects[0])
        # name of dll to give the helper files the same base name
        (dll_name, dll_extension) = os.path.splitext(
            os.path.basename(output_filename))

        # generate the filenames for these files
        def_file = os.path.join(temp_dir, dll_name + ".def")
        lib_file = os.path.join(temp_dir, 'lib' + dll_name + ".a")

        # Generate .def file
        contents = [
            'LIBRARY "%s"' % os.path.basename(output_filename),
            "EXPORTS"]
        for sym in export_symbols:
            contents.append(sym)
        self.execute(write_file, (def_file, contents),
                        "writing %s" % def_file)

        # next add options for def-file and to creating import libraries

        # dllwrap uses different options than gcc/ld
        if self.linker_dll == "dllwrap":
            extra_preargs.extend(["--output-lib", lib_file])
            # for dllwrap we have to use a special option
            extra_preargs.extend(["--def", def_file])
        # we use gcc/ld here and can be sure ld is >= 2.9.10
        else:
            # doesn't work: bfd_close build\...\libfoo.a: Invalid operation
            #extra_preargs.extend(["-Wl,--out-implib,%s" % lib_file])
            # for gcc/ld the def-file is specified as any object files
            objects.append(def_file)

    #end: if ((export_symbols is not None) and
    #        (target_desc != self.EXECUTABLE or self.linker_dll == "gcc")):

    # who wants symbols and a many times larger output file
    # should explicitly switch the debug mode on
    # otherwise we let dllwrap/ld strip the output file
    # (On my machine: 10KB < stripped_file < ??100KB
    #   unstripped_file = stripped_file + XXX KB
    #  ( XXX=254 for a typical python extension))
    if not debug:
        extra_preargs.append("-s")

    UnixCCompiler.link(self, target_desc, objects, output_filename,
                        output_dir, libraries, library_dirs,
                        runtime_library_dirs,
                        None, # export_symbols, we do this in our def-file
                        debug, extra_preargs, extra_postargs, build_temp,
                        target_lang)

CygwinCCompiler.link = link

def is_cygwingcc():
    out_string = check_output(['gcc', '-dumpmachine'], shell=True) #* add shell=True *#
    return out_string.strip().endswith(b'cygwin')

cygwinccompiler.__dict__["is_cygwingcc"] = is_cygwingcc