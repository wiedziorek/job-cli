from job.plugin import PluginManager, PluginType


class FileOptionReader(PluginManager):
	name = "FileOptionReader"
	type = PluginType.OptionReader
	def register_signals(self):
		print "I am %s and register as the %s" % (self.name, self.type)
	def run(self):
		print "running..." 