import typing
from pathlib import Path

from PackageRef import BasePackageRef, PackageRef, VersionedPackageRef

class FilesPackageMapping():
	__slots__ = ("ref", "files")
	
	def __init__(self, ref: BasePackageRef=None, files: typing.Iterable[Path]=None):
		self.ref = ref
		self.files = files

class IFile2Package():
	def __getitem__(self, file: typing.Union[str, Path]) -> BasePackageRef:
		raise NotImplementedError()

class IFile2PackagePopulator():
	ID = None
	def __call__(self) -> (int, typing.Iterable[FilesPackageMapping]):
		raise NotImplementedError

