__author__ = 'miltador'
'''
Setup script for building win32 aceproxy dist with python, executable and installer using cx_Freeze
Command to make a distro: python setup_win32.py bdist_msi

!!! IMPORTANT NOTICE !!!
By default cx_Freeze created installer will generate shortcuts without working dir that's why plugins will not load.
To overcome this you need to edit one line in cx_Freeze\windist.py, see guide here:
    http://stackoverflow.com/questions/24195311/how-to-set-shortcut-working-directory-in-cx-freeze-msi-bundle
Hope that will be fixed soon or the author will do much easier way to set working dir.
'''

from cx_Freeze import setup, Executable

build_exe_options = {"excludes": ["email", "unittest", "aceconfig", "plugins"],
                     "includes": ["xml.dom.minidom"],
                     "include_files": ["aceconfig.py", "plugins"],
                     "compressed": True}

setup(name="AceProxy",
      version="0.9",
      description="AceProxy",
      options={"build_exe": build_exe_options},
      executables=[
          Executable("acehttp.py", base="Win32GUI", targetName="aceproxy_silent.exe",
                     shortcutName="AceProxy Silent mode", shortcutDir="DesktopFolder"),
          Executable("acehttp.py", targetName="aceproxy_console.exe",
                     shortcutName="AceProxy Console mode", shortcutDir="DesktopFolder")])