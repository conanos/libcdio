from conans import ConanFile, tools, MSBuild
from conanos.build import config_scheme
import os, shutil


class LibcdioConan(ConanFile):
    name = "libcdio"
    version = "2.0.0"
    description = "The GNU Compact Disc Input and Control library (libcdio) contains a library for CD-ROM and CD image access"
    url = "https://github.com/conanos/libcdio"
    homepage = "https://www.gnu.org/software/libcdio/"
    license = "GPL-v3.0"
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = { 'shared': True, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def source(self):
        url_ = 'https://github.com/ShiftMediaProject/libcdio/archive/release-{version}.tar.gz'
        tools.get(url_.format(version=self.version))
        extracted_dir = self.name + "-release-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def requirements(self):
        self.requires.add("libiconv/1.15@conanos/stable")

    def build(self):
        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"SMP")):
                replacements = {
                    "iconvd.lib"      :  "iconv.lib",
                }
                for proj in ["libcdio.vcxproj"]:
                    for s, r in replacements.items():
                        tools.replace_in_file(proj, s,r,strict=False)
                
                msbuild = MSBuild(self)
                build_type = str(self.settings.build_type) + ("DLL" if self.options.shared else "")
                msbuild.build("libcdio.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'},build_type=build_type)

    def package(self):
        if self.settings.os == 'Windows':
            platforms={'x86': 'Win32', 'x86_64': 'x64'}
            rplatform = platforms.get(str(self.settings.arch))
            self.copy("*", dst=os.path.join(self.package_folder,"include"), src=os.path.join(self.build_folder,"..", "msvc","include"))
            if self.options.shared:
                for i in ["lib","bin"]:
                    self.copy("*", dst=os.path.join(self.package_folder,i), src=os.path.join(self.build_folder,"..","msvc",i,rplatform))
            self.copy("*", dst=os.path.join(self.package_folder,"licenses"), src=os.path.join(self.build_folder,"..", "msvc","licenses"))

            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))
            shutil.copyfile(os.path.join(self.build_folder,self._source_subfolder,"libcdio.pc.in"),
                            os.path.join(self.package_folder,"lib","pkgconfig", "libcdio.pc"))
            lib = "-lcdiod" if self.options.shared else "-lcdio"
            replacements = {
                "@prefix@"                        : self.package_folder,
                "@exec_prefix@"                   : "${prefix}/bin",
                "@libdir@"                        : "${prefix}/lib",
                "@includedir@"                    : "${prefix}/include",
                "@PACKAGE_NAME@"                  : self.name,
                "@PACKAGE_VERSION@"               : self.version,
                "@LIBS@"                          : "",
                "@LTLIBICONV@"                    : "",
                "@DARWIN_PKG_LIB_HACK@"           : "",
                "-lcdio"                          : lib
            }
            for s, r in replacements.items():
                tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig", "libcdio.pc"),s,r)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

