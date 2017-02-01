# This installs plugins from plugins submodule. 
# This might be too early, don't we think?
# On the other hand we could place here custom search
# path for user plugins...
# Plugin manager prevends from loading plugins which don't like
# to be initialzed, so theroretically plugin refusing to initialize
# won't break anyting.
import plugins
import schematics
import schema