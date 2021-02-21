#run this from the command line: python py2exe_setup.py py2exe

from distutils.core import setup
import py2exe

setup(
    options = {
		"py2exe": 
		{
            "dll_excludes": ["crypt32.dll","MSVCP90.dll"],
			"excludes":  ["numpy"],
            "compressed": 1, "optimize": 0,
			"includes": ["lxml.etree", "lxml._elementpath", "gzip"],
		} 
	},
    zipfile = None,
    windows=[
		{
			"script":"k40_whisperer.py",
			"icon_resources":[(0,"scorchworks.ico"),(1,"scorchworks.ico")]
		}
	],
)

