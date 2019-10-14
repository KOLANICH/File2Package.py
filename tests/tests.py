#!/usr/bin/env python3
import sys
from pathlib import Path
from collections import OrderedDict
import unittest

thisFile = Path(__file__).absolute()
thisDir = thisFile.parent.absolute()
repoMainDir = thisDir.parent.absolute()
sys.path.append(str(repoMainDir))

dict = OrderedDict

from AnyVer import AnyVer
from File2Package import File2Package, IFile2PackagePopulator, FilesPackageMapping
from PackageRef import PackageRef, VersionedPackageRef, BasePackageRef

class ExamplePackagePopulator(IFile2PackagePopulator):
	ID = "Example"
	def __call__(self):
		return 1, (
			FilesPackageMapping(VersionedPackageRef("sqlite3", arch="amd64", version=AnyVer("3.29.0")), [Path("/usr/bin/sqlite3")]),
			FilesPackageMapping(BasePackageRef("ffsgsfsf", arch="amd64"), [Path("/ffsgsfsf/ffsgsfsf/ffsgsfsf")])
		)

class SimpleTests(unittest.TestCase):
	def testOperation(self):
		cacheDBPath = thisDir / "package2fileCache.sqlite"
		if cacheDBPath.exists():
			cacheDBPath.unlink()
		
		with File2Package(ExamplePackagePopulator(), cacheDB=cacheDBPath) as f2p:
			etalonRef = VersionedPackageRef("sqlite3", arch="amd64", version=AnyVer("3.29.0"))
			self.assertEqual(f2p[Path("/usr/bin/sqlite3")], etalonRef)
			self.assertEqual(f2p[etalonRef], etalonRef)
			self.assertEqual(f2p[etalonRef.clone(cls=PackageRef)], etalonRef)
			self.assertEqual(f2p[etalonRef.clone(cls=BasePackageRef)], etalonRef)
			self.assertEqual(f2p[Path("/ffsgsfsf/ffsgsfsf/ffsgsfsf")], BasePackageRef("ffsgsfsf", arch="amd64"))


if __name__ == "__main__":
	unittest.main()
