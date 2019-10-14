import warnings

from. import interfaces

def discoverBackends():
	import pkg_resources
	pts = list(pkg_resources.iter_entry_points(group="file_2_package"))
	return dict(( (b.name, b) for b in pts ))

discoveredBackends = discoverBackends()

def selectBackend(name:str):
	b = discoveredBackends[name]
	init = b.load()
	cls = init(interfaces)
	cls.ID = name
	return cls
