import os
import sys
print("Current dir:", os.getcwd())
print("Files:", os.listdir())
print("Modules path exists:", os.path.exists("modules/content_parser.py"))
print("Modules in sys.path:", sys.path)
