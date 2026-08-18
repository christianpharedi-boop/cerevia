from pyedflib import EdfReader
import sys
reader = EdfReader(sys.argv[1])
try:
    print('signals', reader.signals_in_file)
    print('duration', reader.file_duration)
    print('annotations', reader.readAnnotations())
finally:
    reader.close()
