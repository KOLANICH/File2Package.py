import typing
from pathlib import Path
import re
from collections import defaultdict

import sqlite3
import datrie
from MempipedPath import *
import threading

from pantarei import chosenProgressReporter

from PackageRef import BasePackageRef, VersionedPackageRef
from .interfaces import *
from .BackendsDiscoverer import selectBackend

defaultCacheDir = None

import lzma
filters = [{"id":lzma.FILTER_DELTA, "dist": 5}, {"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "mf": lzma.MF_BT4, "mode": lzma.MODE_NORMAL}]
compressorParams = {
	"format": lzma.FORMAT_RAW,
	"check": lzma.CHECK_NONE,
	"preset": None,
	"filters": filters
}
decompressorParams = {
	"format": lzma.FORMAT_RAW,
	"memlimit": None,
	"filters": filters
}


def populateDefaultCacheDirIfNeeded():
	import appdirs
	global defaultCacheDir
	if defaultCacheDir is None:
		try:
			thisModuleName = __spec__.name
		except:
			thisFile = Path(__file__)
			thisModuleName = thisFile.stem
		defaultCacheDir = Path(appdirs.user_cache_dir("python_File2Package"))


class File2Package(IFile2Package):
	__slots__ = ("populator", "db", "dbPath", "dt", "trieWasModified")
	def __init__(self, populator:typing.Union[IFile2PackagePopulator, str], cacheDB:typing.Optional[typing.Union[str, Path]]=None):
		"""`populator` is an object fetching mapping from filenames to packages from a system.
		`cacheDB` is either a string (then it is a name) or a full path to an SQLIte file.
		"""
		if isinstance(populator, str):
			populatorClass = selectBackend(populator)
			populator = populatorClass()
		elif isinstance(populator, tuple):
			populatorBackendName = populator[0]
			populatorArgs = populator[1:]
			populatorClass = selectBackend(populator)
			populator = populatorClass(populatorArgs)
		
		if cacheDB is None:
			cacheDB = populator.ID

		if isinstance(cacheDB, Path):
			self.dbPath = cacheDB
			self.db = None
		elif isinstance(cacheDB, str):
			populateDefaultCacheDirIfNeeded()
			self.dbPath = defaultCacheDir / (cacheDB + ".sqlite")
			self.db = None
		else:
			self.dbPath = None
			self.db = cacheDB
		
		self.populator = populator
		self.dt = None
	
	def getTables(self):
		for tr in self.db.execute('select `name` from `sqlite_master` where `type` = "table";',):
			yield tr[0]
	
	mandatoryTables = ("blobs", "packages", "architectures")
	
	def drop(self):
		for tableName in self.__class__.mandatoryTables:
			try:
				self.db.executescript("DROP TABLE "+tableName+";");
			except:
				pass
	
	def isInitialized(self):
		curTables = set(self.getTables())
		for tableName in self.__class__.mandatoryTables:
			if tableName not in curTables:
				return False
		return True
	
	def __enter__(self):
		needCreate = False
		if not self.db:
			needCreate = needCreate and not self.dbPath.exists()
			dbDir = self.dbPath.parent
			dbDir.mkdir(parents=True, exist_ok=True)
			self.db = sqlite3.connect(str(self.dbPath))
			if not self.isInitialized():
				self.initDB()
		
		self.dt = self.loadTrie()
		if self.dt is None:
			self.dt = datrie.BaseTrie(ranges=[("\0", '\U0010ffff')]) # whole unicode
			needCreate = True

		self.trieWasModified = False
		
		if needCreate:
			self.createDB()
			self.save()

		return self
	
	def loadBlob(self, k:str):
		try:
			v = next(self.db.execute("SELECT `value` FROM `blobs` WHERE `key` = ?;", (k,)))[0];
			return lzma.LZMADecompressor(**decompressorParams).decompress(v)
		except StopIteration:
			pass
	
	def saveBlob(self, k:str, v:bytes):
		compressor = lzma.LZMACompressor(**compressorParams)
		v = compressor.compress(v) + compressor.flush()
		self.db.execute("INSERT OR REPLACE INTO `blobs` (`key`, `value`) values (?, ?);", (k, v));
	
	def loadTrie(self):
		trieBlob = self.loadBlob("trie")
		if trieBlob:
			res = None
			with MempipedPathTmp(trieBlob) as p:
				res = datrie.BaseTrie.load(p.file)
			return res
	
	def saveTrie(self):
		if self.trieWasModified:
			if hasattr(self.dt, "__bytes__"):
				data = bytes(self.dt)
			else:
				with MempipedPathTmp(None, read=False, write=True) as p:
					#print("Saving trie")
					self.dt.save(p.file)
					#print("The lib has exported the trie")
				data = p.data
			
			self.saveBlob("trie", data)
	
	def save(self):
		self.db.commit()
		self.saveTrie()
		self.db.commit()
	
	def __exit__(self, *args, **kwargs):
		self.save()
		self.db.close()
		self.db = None
	
	def initDB(self):
		self.drop()
		self.initSchema()
	
	def initSchema(self):
		self.db.executescript(
			"""
			CREATE TABLE blobs (
				key TEXT PRIMARY KEY,
				value BLOB
			);
			
			CREATE TABLE architectures (
				id INTEGER NOT NULL PRIMARY KEY,
				name TEXT NOT NULL
			);

			CREATE TABLE packages (
				id INTEGER NOT NULL PRIMARY KEY,
				name TEXT NOT NULL,
				arch INTEGER NOT NULL,
				version TEXT,
				FOREIGN KEY(arch) REFERENCES architectures(id)
			);
			CREATE INDEX archz ON `architectures` (`name`);
			
			CREATE INDEX pkgs1 ON `packages` (`name`, `arch`);
			CREATE INDEX pkgs2 ON `packages` (`name`);
			"""
		)
		self.insertArch_("any", 0)
		self.db.commit();

	def insertArch_(self, name, selfId=None):
		return self.db.execute("INSERT OR REPLACE INTO `architectures` (`name`, `id`) values (?, " +  ("?" if selfId is not None else "NULL") + ");", (name,)+((selfId,) if selfId is not None else ())).lastrowid

	def insertPackage_(self, name, archId, version=None, selfId=None):
		return self.db.execute("INSERT OR REPLACE INTO `packages` (`name`, `arch`, `version`, `id`) values (?, ?, ?, ?);", (name, archId, (str(version) if version is not None else None), (selfId if selfId is not None else None))).lastrowid
	

	def getArch_(self, name):
		try:
			return next(self.db.execute("SELECT `id` FROM `architectures` where `name` = ?;", (name,)))[0]
		except StopIteration:
			pass

	def getPackageByNameAndArch_(self, name, archId):
		try:
			return next(self.db.execute("SELECT `id` FROM `packages` where `name` = ? and `arch` = ?;", (name, archId)))[0]
		except StopIteration:
			pass

	def getPackageVersionByNameAndArch_(self, name, arch):
		try:
			return next(self.db.execute("SELECT p.`version` FROM `packages` p INNER JOIN `architectures` a ON a.`id` = p.`arch` where p.`name` = ? and a.`name` = ?;", (name, arch)))[0]
		except StopIteration:
			pass


	def getPackageStringsById_(self, id):
		try:
			return next(self.db.execute("SELECT p.`name` as `name`, a.`name` as `arch`, p.`version` as `version` FROM `packages` p INNER JOIN `architectures` a ON a.`id` = p.`arch` WHERE p.`id` = ?;", (id, )))
		except StopIteration:
			pass
	
	def createDB(self):
		self.trieWasModified = True
		
		pkgCount, pkgs = self.populator()
		with chosenProgressReporter(pkgCount, "Populating database") as pb:
			for fi in pkgs:
				name = fi.ref.name
				arch = fi.ref.arch
				archId = self.getArch_(arch)
				if archId is None:
					archId = self.insertArch_(arch)
				
				pkgId = self.getPackageByNameAndArch_(name, archId)
				if pkgId is None:
					if isinstance(fi.ref, VersionedPackageRef):
						pkgId = self.insertPackage_(name, archId, str(fi.ref.version))
					else:
						pkgId = self.insertPackage_(name, archId)
				
				for f in fi.files:
					self.dt[str(f)] = pkgId
				pb.report(fi.ref)
	
	def getByFile(self, file: typing.Union[str, Path]) -> BasePackageRef:
		pkgId = self.dt[str(file)]
		if pkgId is not None:
			return self.__class__.constructRef(*self.getPackageStringsById_(pkgId))
	
	def getVersionedByRef(self, ref: typing.Union[BasePackageRef]) -> BasePackageRef:
		ver = self.getPackageVersionByNameAndArch_(ref.name, ref.arch)
		if ver is not None:
			return ref.clone(cls=VersionedPackageRef, version=ver)
		else:
			return ref
	
	@classmethod
	def constructRef(cls, name, arch, version):
		if not version:
			return BasePackageRef(name, arch=arch)
		else:
			return VersionedPackageRef(name, arch=arch, version=version)
	
	def __getitem__(self, fileOrRef: typing.Union[str, Path, BasePackageRef]) -> BasePackageRef:
		if isinstance(fileOrRef, (str, Path)):
			return self.getByFile(fileOrRef)
		elif isinstance(fileOrRef, (BasePackageRef,)):
			return self.getVersionedByRef(fileOrRef)
		else:
			raise TypeError("Unsupported type of argument `fileOrRef`", fileOrRef)
