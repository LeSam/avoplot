#Copyright (C) Nial Peters 2013
#
#This file is part of AvoPlot.
#
#AvoPlot is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#AvoPlot is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with AvoPlot.  If not, see <http://www.gnu.org/licenses/>.

import sys
import shutil
import os
import stat
import string

from distutils.command.build_py import build_py as _build_py
from distutils.command.install import install
from distutils.core import setup

#get the absolute path of this setup script
setup_script_path = os.path.dirname(os.path.abspath(sys.argv[0]))


####################################################################
#                    CONFIGURATION
####################################################################

required_modules = [("matplotlib", "the Matplotlib plotting library"),
                    ("numpy", "NumPy (Numerical Python)"),
                    ("wx", "wxPython"),
                    ("magic", "the libmagic Python bindings (python-magic)")
                   ]

#check that all the required modules are available
print "Checking for required Python modules..."
for mod, name in required_modules:
    try:
        print "importing %s..."%mod
        __import__(mod)
    except ImportError:
        print ("Failed to import \'%s\'. Please ensure that %s "
               "is correctly installed, then re-run this "
               "installer."%(mod,name))
        sys.exit(1)

#platform specific configuration
scripts_to_install = [os.path.join('src','AvoPlot.py')]  

if sys.platform == "win32":
    #on windows we need to install the post-installation script too
    scripts_to_install.append(os.path.join('misc', 
                                           'avoplot_win32_postinstall.py'))
      


####################################################################
#                    BUILD/INSTALL
####################################################################


class build_py(_build_py):
    """build_py command
    
    This build_py command will modify a build_info module so that
    contains information on installation prefixes afterwards.
    """
    def build_module (self, module, module_file, package):
        if type(package) is str:
            _package = string.split(package, '.')
        elif type(package) not in (list, tuple):
            raise TypeError("'package' must be a string (dot-separated), "
                            "list, or tuple")
        else:
            _package = package
        
        if (module == 'build_info' and len(_package) == 1 and 
            _package[0] == 'avoplot'):
            iobj = install(self.distribution)
            iobj.finalize_options()

            with open(module_file, 'w') as module_fp:
                module_fp.write(avoplot.SRC_FILE_HEADER)
                module_fp.write('\n#This file is auto-generated by the %s '
                                'setup.py script.\n\n'%avoplot.PROG_SHORT_NAME)
                
                if sys.platform == "linux2":
                    #we want our sys_runtime_files dir to be in prefix/share
                    #global DATA_DIR
                    DATA_DIR = os.path.join(iobj.install_data, 'share')
                    module_fp.write("DATA_DIR = '%s'\n"%DATA_DIR)
                else:
                    #global DATA_DIR
                    DATA_DIR =iobj.install_data
                    module_fp.write("DATA_DIR = '%s'\n" %DATA_DIR)
                    
                module_fp.write("LIB_DIR = '%s'\n"%(iobj.install_lib))
                module_fp.write("SCRIPT_DIR = '%s'\n"%(iobj.install_scripts))

        _build_py.build_module(self, module, module_file, package)


def create_desktop_file():
    """
    Function to create the .desktop file for Linux installations.
    For now the file will just be put into /usr/share/applications.
    Future versions may implement creating it in 'non-root' locations.
    """
    #TODO - allow installation into ~/.local/share/applications if desired
    apps_folder = '/usr/share/applications'
    
    desktop_file_path = os.path.join(apps_folder,'avoplot.desktop')
    
    with open(desktop_file_path,'w') as ofp:
        ofp.write('[Desktop Entry]\n')
        ofp.write('Version=%s\n'%avoplot.VERSION)
        ofp.write('Type=Application\n')
        ofp.write('Exec=%s\n'%os.path.join(avoplot.build_info.SCRIPT_DIR,
                                           'AvoPlot.py'))
        ofp.write('Comment=%s\n'%avoplot.SHORT_DESCRIPTION)
        ofp.write('NoDisplay=false\n')
        ofp.write('Categories=Science;Education;Geology;\n')
        ofp.write('Name=%s\n'%avoplot.PROG_SHORT_NAME)
        ofp.write('Icon=%s\n'%os.path.join(avoplot.get_avoplot_icons_dir(),
                                           '64x64','avoplot.png'))
    
    return_code = os.system("chmod 644 " + os.path.join(apps_folder, 
                                                        'avoplot.desktop'))
    if return_code != 0:
        print "Error! Failed to change permissions on \'" + os.path.join(apps_folder, 'avoplot.desktop') + "\'"
                

def install_icons():
    icon_dest_dir = avoplot.get_avoplot_icons_dir()
    
    #create the destination folders if they don't already exist
    #and then copy the icons into them
    dirs = [d for d in os.listdir('icons') if os.path.isdir(os.path.join('icons',d))]
    for d in dirs:
        if d.startswith('.'):
            continue
        try:
            os.makedirs(os.path.join(icon_dest_dir,d))
        except OSError:
            pass
        
        icon_files = os.listdir(os.path.join('icons',d))
        for f in icon_files:
            shutil.copy(os.path.join('icons',d,f), os.path.join(icon_dest_dir,d))
    
    #if we're in Windows, then install the .ico file too
    if sys.platform == "win32":
        shutil.copy(os.path.join('icons','avoplot.ico'), icon_dest_dir)
    

try:
    #create a temporary build_info module - this will be populated during the build process
    #Note that we define DATA_DIR so that we can import avoplot without errors.
    build_info_name = os.path.join(setup_script_path, 'src', 'avoplot', 'build_info.py')
    with open(build_info_name, 'w') as ofp:
        ofp.write("#Temporary file created by setup.py. It should be deleted again"
                  " when setup.py exits.\n\n"
                  "DATA_DIR = None\n")
    
    #now import the avoplot module to give us access to all the information
    #about it, author name etc. This must be done after the temp build_info
    #file is created, otherwise the import will fail
    import src.avoplot as avoplot
    
    #do the build/installation
    setup(cmdclass={'build_py':build_py}, #override the default builder with our build_py class
          name=avoplot.PROG_SHORT_NAME,
          version=avoplot.VERSION,
          description=avoplot.SHORT_DESCRIPTION,
          author=avoplot.AUTHOR,
          author_email=avoplot.AUTHOR_EMAIL,
          url=avoplot.URL,
          package_dir={'':'src'},
          packages=['avoplot', 'avoplot.gui', 'avoplot.plugins', 'avoplot.plugins.avoplot_fromfile_plugin'],
          scripts=scripts_to_install
          )
    
    #now the build_info.py file will have been populated, so re-import it
    os.remove(build_info_name+'c') #remove the old compiled file first
    reload(avoplot)
    reload(avoplot.build_info)

    

    ####################################################################
    #                    POST INSTALL
    ####################################################################
    
    if sys.argv.count('install') != 0:
        install_icons()
        if sys.platform == "linux2":
            create_desktop_file()
            

#final tidy up            
finally:
    os.remove(build_info_name)
    os.remove(build_info_name+'c') #remove compiled build_info file