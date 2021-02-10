##
## NB testing purpose
###
from black import reformat_many, FileMode, WriteBack, Report
from pathlib import Path

reformat_many({Path(".")},False,WriteBack.DIFF,FileMode(),Report(False,True,False,True))
# result = format_file_in_place(Path("black_linter.py"),False,FileMode(),WriteBack.DIFF)