import argparse
import datetime
from math import log
import sys

def backups_to_keep(n):
	if n == 0:
		return set()
	elif n == 1:
		return set([1])
	else:
		return set([n]) | backups_to_keep(n - 2**(int(log(n, 2)) - 1))

class Log2RotateUnsafeError(ValueError): pass

class Log2RotatePeriodError(ValueError): pass

class Log2Rotate(object):
	def __init__(self, **kwargs):
		pass

	def _offset_to_backup_dict(self, last, state):
		n0_to_b = {}
		for b in state:
			n0 = self.sub(last, b) + 1
			if n0 in n0_to_b:
				raise Log2RotatePeriodError
			else:
				n0_to_b[n0] = b
		return n0_to_b

	def backups_to_keep(self, state, unsafe=False, fuzz=0, fuzz_list=None):
		for ref in state:
			# "ref" is just a random item from the iterable - it doesn't
			# matter which.
			state_sorted = sorted(state, key=lambda x: self.sub(x, ref))
			break
		else:
			# if "state" is empty, just return it.
			return state

		if len(state_sorted) < 2:
			return state_sorted
		else:
			last = state_sorted[-1]
			first = state_sorted[0]

			n0_to_b = self._offset_to_backup_dict(last, state)
			n = self.sub(last, first) + 1

			r = self.pattern(n)

			new_state_set = set()
			new_state = []
			for n0 in sorted(r, reverse=True):
				for m in self.fuzzy_range(fuzz):
					if n0+m in n0_to_b:
						b = n0_to_b[n0+m]
						if b not in new_state_set:
							new_state.append(b)
							new_state_set.add(b)
						if m > 0 and fuzz_list is not None:
							fuzz_list.append(1)
						break
				else:
					if not unsafe:
						raise Log2RotateUnsafeError

			return new_state

	@staticmethod
	def fuzzy_range(fuzz):
		return sorted(reversed(range(-fuzz, fuzz+1)), key=lambda x:abs(x))

	def pattern(self, n):
		"""Returns a pattern of backups to keep, given history of n backups.

		Returned value is a set of integers, where each integer
		represents a backup to keep.

		The latest backup is numbered 1. The oldest backup is numbered n.
		"""

		return backups_to_keep(n)

	# Algorithm above assumes that sub(x, y) == 0 iff x == y.
	#
	# This  assumption can break for instance if you have hourly backups
	# and sub() assumes daily backups.
	def sub(self, x, y):
		return x - y

class Log2RotateDatetime(Log2Rotate):
	def __init__(self, **kwargs):
		self.fmt = kwargs['fmt']
		super(Log2RotateDatetime, self).__init__(**kwargs)

	def strptime(self, s):
		return datetime.datetime.strptime(s, self.fmt)

	def sub(self, x, y):
		x2 = self.strptime(x)
		y2 = self.strptime(y)

		return (x2 - y2).days

class Log2RotateSkip(Log2Rotate):
	def __init__(self, **kwargs):
		self.skip = kwargs.get('skip', 0)
		super(Log2RotateSkip, self).__init__(**kwargs)

	def pattern(self, n):
		assert self.skip >= 0

		r = set(range(1, self.skip+1))

		if n > self.skip:
			r2 = backups_to_keep(n - self.skip)
			r |= set(self.skip + i for i in r2)

		return r

class Log2RotateStr(Log2RotateDatetime, Log2RotateSkip, Log2Rotate):
	pass

def run(args, inp):

	l2r = Log2RotateStr(fmt=args.fmt, skip=args.skip, fuzz=args.fuzz)

	inp_orig = set(inp)

	# filter out all lines that do not conform to format
	# we always want to keep these.
	def parseable(s):
		try:
			l2r.strptime(s)
		except ValueError:
			return False
		else:
			return True

	inp = set(filter(parseable, inp))
	out = list(inp_orig - inp)
	if out:
		sys.stderr.write("warning: keeping %d backups with unparseable names\n" % (len(out,)))

	# if there are any backups left that need to be rotated,
	# run them through log2rotate and append the result to
	# the list of backups to keep.
	if inp:
		fuzz_list = []
		out += l2r.backups_to_keep(inp, unsafe=args.unsafe, fuzz_list=[])

		if fuzz_list:
			sys.stderr.write("warning: used fuzzy matching for %d backups\n" % (len(fuzz_list),))

	if args.show_keep:
		return out
	else:
		return inp_orig - set(out)

def main():
	parser = argparse.ArgumentParser(description="rotate backups using exponentially-growing periods.")

	parser.add_argument('-d', '--delete', action='store_true', dest='show_delete',
			help="show backups to delete")
	parser.add_argument('-k', '--keep', action='store_true', dest='show_keep',
			help="show backups to keep")
	parser.add_argument('-u', '--unsafe', action='store_true', dest='unsafe',
			help="make unsafe recommendations")
	parser.add_argument('-s', '--skip', metavar='NUM', type=int, dest='skip', default=0,
			help="always keep NUM latest backups")
	parser.add_argument('-F', '--fuzz', metavar='NUM', type=int, dest='fuzz', default=0,
			help="do fuzzy matching for up to NUM missing backups in series")
	parser.add_argument('-f', '--format', metavar='FMT', dest='fmt', default="%Y-%m-%d",
			help="use FMT for parsing date from backup name")

	args = parser.parse_args()

	if (not args.show_keep and not args.show_delete) or (args.show_keep and args.show_delete):
		sys.stderr.write("error: please specify either --keep or --delete\n")
		sys.exit(1)

	if args.skip < 0:
		sys.stderr.write("error: argument to --skip should be non-negative\n")
		sys.exit(1)

	if args.fuzz < 0:
		sys.stderr.write("error: argument to --fuzz should be non-negative\n")
		sys.exit(1)

	inp = [ line.strip() for line in sys.stdin ]

	try:
		out = run(args, inp)
	except Log2RotateUnsafeError:
		sys.stderr.write("error: backups that should have been kept are missing from the input list (use --unsafe to proceed anyway or use higher --fuzz)\n")
	except Log2RotatePeriodError:
		sys.stderr.write("error: seen multiple backups within one backup period (log2rotate currently assumes daily backups)\n")
	else:
		for line in out:
			print(line)

if __name__ == '__main__':
	main()
