import typing
import sys
from plumbum import cli

from . import *
from .BackendsDiscoverer import discoveredBackends

class File2PackageCLI(cli.Application):
	pass

@File2PackageCLI.subcommand("backends")
class File2PackageCLIListBackends(cli.Application):
	def main(self):
		from pprint import pprint
		pprint(discoveredBackends)

cacheDBAttr = cli.SwitchAttr(["-D","--db"], str, help="Either a path to SQLite db file or just a name. In the case of a name the file will be created in cache dir.")

def file2PackageWithStringFilePath(backend:str, cacheDB:str):
	try:
		cacheDBPath = Path(cacheDB).absolute()
		if cacheDBPath.is_file() or cacheDBPath.suffix.lower in {".sqlite", ".db"}:
			return File2Package(backend, cacheDB=cacheDBPath)
	except:
		pass
	
	return File2Package(backend, cacheDB=cacheDB)

@File2PackageCLI.subcommand("refresh")
class File2PackageCLIRefresh(cli.Application):
	"""Recreates the database for the backend"""
	def main(self, backend:str, cacheDB:str=None):
		with file2PackageWithStringFilePath(backend, cacheDB=cacheDB) as f2p:
			f2p.createDB()

@File2PackageCLI.subcommand("lookup")
class File2PackageCLILookup(cli.Application):
	"""Prints list of packages to which files belong"""
	cacheDb = cacheDBAttr
	json = cli.Flag(["-J","--json"], help="print JSON")
	def main(self, backend:str, *files):
		from collections import OrderedDict
		res = OrderedDict()
		import json
		
		with file2PackageWithStringFilePath(backend, cacheDB=self.cacheDb) as f2p:
			for f in files:
				fp = Path(f).absolute()
				pkg=f2p[fp]
				res[str(fp)] = (pkg.name, pkg.arch)
		
		if self.json:
			print(json.dumps(res, indent="\t"))
		else:
			print("\n".join(":".join(v) for v in res.values()))

if __name__ == "__main__":
	File2PackageCLI.run()
