from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
from Cython.Distutils import build_ext
import os
import sysconfig
import numpy as np

def get_ext_filename_without_platform_suffix(filename):
    name, ext = os.path.splitext(filename)
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    if ext_suffix == ext:
        return filename
    ext_suffix = ext_suffix.replace(ext, '')
    idx = name.find(ext_suffix)
    if idx == -1:
        return filename
    else:
        return name[:idx] + ext


class BuildExtWithoutPlatformSuffix(build_ext):
    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        return get_ext_filename_without_platform_suffix(filename)


numpy_include = np.get_include()
extensions = [Extension("*", ["*.pyx"],include_dirs=[numpy_include])]
setup(
        cmdclass={'build_ext': BuildExtWithoutPlatformSuffix},
        ext_modules=cythonize(extensions)
        
)
#setup(ext_modules=cythonize("nms.pyx"), include_dirs=[numpy_include])
