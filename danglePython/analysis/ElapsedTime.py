from contextlib import contextmanager
from timeit import default_timer

@contextmanager
def elapsedTime(name, printAtEnd = True):
	start = default_timer()
	elapsed = lambda: default_timer() - start
	yield lambda: elapsed()
	end = default_timer()
	elapsed = end - start
	if printAtEnd:
		print(f"{name} elapsed: {elapsed:.3f}secs")
