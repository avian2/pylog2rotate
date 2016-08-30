from math import log
import datetime
import unittest

from log2rotate import backups_to_keep, Log2RotateStr, run, Log2RotateUnsafeError

def print_set(r):
	l = []
	for n in range(1, max(r)+1):
		if n in r:
			l.append('X')
		else:
			l.append(' ')
	
	print(''.join(l))
		

class TestBackupsToKeep(unittest.TestCase):

	def test_zero(self):
		self.assertEqual(set(), backups_to_keep(0))

	def test_one(self):
		self.assertEqual(set([1]), backups_to_keep(1))

	def test_four(self):
		self.assertEqual(set([1, 2, 4]), backups_to_keep(4))

	def test_seven(self):
		self.assertEqual(set([1, 2, 3, 5, 7]), backups_to_keep(7))

	def test_spacing(self):
		for n in range(3, 10000):
			r = backups_to_keep(n)

			# Always keep the oldest backup
			self.assertTrue(n in r)
			# Always keep the newest backup
			self.assertTrue(1 in r)

			# Number of backups is always between log2(n) and 2*log2(n)
			self.assertGreaterEqual(len(r), log(n, 2))
			self.assertLess(len(r), 2*log(n, 2))

	def test_spacing_incremental(self):
		state = set()
		for n in range(1, 10000):
			state = set([1] + [i+1 for i in state])

			f = backups_to_keep(max(state))
			state &= f

			# If the algorithm is applied incrementally, the state of
			# the backups should be identical to the state recommended by 
			# the backups_to_keep function.
			self.assertEqual(f, state)

			#print_set(state)

from log2rotate import Log2Rotate, Log2RotatePeriodError

class TestFuzzyRange(unittest.TestCase):
	def test_zero(self):
		self.assertEqual([0], Log2Rotate.fuzzy_range(0))

	def test_one(self):
		self.assertEqual([0, 1, -1], Log2Rotate.fuzzy_range(1))

	def test_two(self):
		self.assertEqual([0, 1, -1, 2, -2], Log2Rotate.fuzzy_range(2))

class TestLog2Rotate(unittest.TestCase):
	def test_simple(self):
		l2r = Log2Rotate()

		state = [ 1, 2, 3, 4 ]
		self.assertEqual([1, 3, 4], l2r.backups_to_keep(state))

	def test_duplicates(self):
		l2r = Log2Rotate()

		state = [ 1, 1, 2, 2, 3, 3, 4, 4 ]
		self.assertRaises(Log2RotatePeriodError, l2r.backups_to_keep, state)

def _gen_state(n, fmt):
	now = datetime.datetime(2015, 1, 1)
	td = datetime.timedelta(days=1)

	state = []

	for i in range(n):
		state.append(now.strftime(fmt))
		now += td

	return state

class TestLog2RotateStr(unittest.TestCase):
	def setUp(self):
		self.fmt = "backup-%Y%m%d"
		self.l2r = Log2RotateStr(fmt=self.fmt)

	def test_zero(self):
		self.assertEqual(set(), self.l2r.backups_to_keep([]))

	def _gen_state(self, n):
		return _gen_state(n, self.fmt)

	def test_zero(self):
		self.assertEqual([], self.l2r.backups_to_keep([]))

	def test_one(self):
		state = self._gen_state(1)
		self.assertEqual(["backup-20150101"], self.l2r.backups_to_keep(state))

	def test_four(self):
		state = self._gen_state(4)
		self.assertEqual([	"backup-20150101",
					"backup-20150103",
					"backup-20150104"], self.l2r.backups_to_keep(state))

	def test_seven(self):
		state = self._gen_state(7)
		self.assertEqual([	"backup-20150101",
					"backup-20150103",
					"backup-20150105",
					"backup-20150106",
					"backup-20150107"], self.l2r.backups_to_keep(state))

	def test_twenty(self):
		state = self._gen_state(20)
		self.assertEqual([	"backup-20150101",
					"backup-20150109",
					"backup-20150113",
					"backup-20150117",
					"backup-20150119",
					"backup-20150120"], self.l2r.backups_to_keep(state))

	def test_twenty_fuzz(self):
		state = self._gen_state(20)
		del state[8]

		self.assertEqual([	"backup-20150101",
					"backup-20150108",
					"backup-20150113",
					"backup-20150117",
					"backup-20150119",
					"backup-20150120"], self.l2r.backups_to_keep(state, fuzz=1))

	def test_twenty_fuzz(self):
		state = [	"backup-20150101",
				"backup-20150110",
				"backup-20150113",
				"backup-20150117",
				"backup-20150119",
				"backup-20150120"]

		self.assertEqual(state, self.l2r.backups_to_keep(state, fuzz=1))

	def test_twenty_fuzz_list_1(self):
		state = [	"backup-20150101",
				"backup-20150110", # offset +1
				"backup-20150113",
				"backup-20150117",
				"backup-20150119",
				"backup-20150120"]

		fuzz_list = []

		state2 = self.l2r.backups_to_keep(state, fuzz=1, fuzz_list=fuzz_list)

		self.assertEqual(state, state2)
		self.assertEqual(1, len(fuzz_list))

	def test_twenty_fuzz_list_2(self):
		state = [	"backup-20150101",
				"backup-20150108", # offset -1
				"backup-20150113",
				"backup-20150117",
				"backup-20150119",
				"backup-20150120"]

		fuzz_list = []

		state2 = self.l2r.backups_to_keep(state, fuzz=1, fuzz_list=fuzz_list)

		self.assertEqual(state, state2)
		self.assertEqual(1, len(fuzz_list))

	def test_spacing(self):
		n = 10000
		state = self._gen_state(n)

		new_state = self.l2r.backups_to_keep(state)

		# Always keep the oldest backup
		self.assertTrue(state[0] in new_state)
		# Always keep the newest backup
		self.assertTrue(state[-1] in new_state)

		# Number of backups is always between log2(n) and 2*log2(n)
		self.assertGreaterEqual(len(new_state), log(n, 2))
		self.assertLess(len(new_state), 2*log(n, 2))

	def test_idempotency(self):
		state = self._gen_state(10000)

		state_1 = self.l2r.backups_to_keep(state)
		state_2 = self.l2r.backups_to_keep(state_1)

		self.assertEqual(state_1, state_2)

	def test_incremental(self):
		n = 200

		state = self._gen_state(n)

		inc_state = []
		for n in range(n):
			inc_state.append(state[n])
			inc_state = self.l2r.backups_to_keep(inc_state)

			self.assertEqual(inc_state, self.l2r.backups_to_keep(state[:n+1]))

	def test_incremental_fuzz(self):
		# this tests, if incrementally rotating backups yields the
		# same result as rotating all at once.
		#
		# all combinations with one backup missing are tested.
		n0 = 50

		state = self._gen_state(n0)

		for m in range(n0):
			inc_state = []
			state0 = []
			for n in range(n0):
				if n != m:
					inc_state.append(state[n])
					state0.append(state[n])

				inc_state = self.l2r.backups_to_keep(inc_state, fuzz=1)

				self.assertEqual(inc_state, self.l2r.backups_to_keep(state0, fuzz=1))

	def test_compare_fuzz_nofuzz(self):
		n0 = 50

		state = self._gen_state(n0)

		for m in range(n0):
			state0 = []
			state0_nofuzz = []

			for n in range(n0):
				if n != m:
					state0.append(state[n])
				state0_nofuzz.append(state[n])

			rstate = self.l2r.backups_to_keep(state0, fuzz=1)
			rstate_nofuzz = self.l2r.backups_to_keep(state0_nofuzz)

			o = len(rstate)
			o_nofuzz = len(rstate_nofuzz)

			self.assertGreaterEqual(o_nofuzz, o)
			self.assertLessEqual(o_nofuzz - o, 1)

	def test_oldest_backup_gone(self):
		# We have a rotated set of backups. The oldest backup
		# disappears. Another rotation should not remove anything.
		n = 100

		state = self._gen_state(n)
		state2 = self.l2r.backups_to_keep(state)

		state2 = set(state2)
		state2.remove(min(state2))

		state3 = set(self.l2r.backups_to_keep(state2))

		self.assertEqual(state3, state2)

	def test_unsafe(self):
		# algorithm says "backup-20150103" should be kept, but
		# is missing in input list
		state = [	"backup-20150101",
				"backup-20150104" ]

		self.assertRaises(Log2RotateUnsafeError, self.l2r.backups_to_keep, state)

class TestLog2RotateUnsafeError(unittest.TestCase):
	def test_unsafe(self):
		state = [	"backup-20150101",
				"backup-20150104" ]

		fmt = "backup-%Y%m%d"
		l2r = Log2RotateStr(fmt=fmt)

		#l2r.backups_to_keep(state)
		try:
			l2r.backups_to_keep(state)
		except Log2RotateUnsafeError as e:
			self.assertEqual(str(e), "missing a backup between \'backup-20150101\' and \'backup-20150104\' (fuzz 1)")
		else:
			self.fail("did not raise Log2RotateUnsafeError")

class TestLog2RotateStrSkip(unittest.TestCase):
	def setUp(self):
		self.fmt = "backup-%Y%m%d"
		self.l2r = Log2RotateStr(fmt=self.fmt, skip=3)

	def _gen_state(self, n):
		return _gen_state(n, self.fmt)

	def test_skip_7(self):
		state = self._gen_state(7)

		self.assertEqual([	"backup-20150101",
					"backup-20150103",
					"backup-20150104",
					"backup-20150105",
					"backup-20150106",
					"backup-20150107"], self.l2r.backups_to_keep(state))

	def test_skip_3(self):
		state = self._gen_state(3)
		self.assertEqual(state, self.l2r.backups_to_keep(state))

	def test_skip_3_fuzz(self):
		state = [	"backup-20150101",
				"backup-20150103" ]
		fuzz_list = []
		self.assertEqual(state, self.l2r.backups_to_keep(state, fuzz_list=fuzz_list, fuzz=1))
		self.assertEqual(len(fuzz_list), 1)

	def test_skip_unsafe(self):
		state = [	"backup-20150101",
				"backup-20150103" ]

		self.assertRaises(Log2RotateUnsafeError, self.l2r.backups_to_keep, state)

class MockArgs(object):
	def __init__(self):
		self.fmt = "%Y-%m-%d"
		self.skip = 0
		self.fuzz = 0

	def __getattr__(self, name):
		return None

class TestMain(unittest.TestCase):
	def test_default_keep(self):
		args = MockArgs()
		args.show_keep = True

		inp = _gen_state(4, "%Y-%m-%d")

		out = run(args, inp)

		self.assertEqual(set([	"2015-01-01",
					"2015-01-03",
					"2015-01-04"]), set(out))

	def test_default_delete(self):
		args = MockArgs()
		args.show_delete = True

		inp = _gen_state(4, "%Y-%m-%d")

		out = run(args, inp)

		self.assertEqual(set([	"2015-01-02"]), set(out))

	def test_skip_keep(self):
		args = MockArgs()
		args.show_keep = True
		args.skip = 3

		inp = _gen_state(7, "%Y-%m-%d")

		out = run(args, inp)

		self.assertEqual(set([	"2015-01-01",
					"2015-01-03",
					"2015-01-04",
					"2015-01-05",
					"2015-01-06",
					"2015-01-07"]), set(out))

	def test_skip_delete(self):
		args = MockArgs()
		args.show_delete = True
		args.skip = 3

		inp = _gen_state(7, "%Y-%m-%d")

		out = run(args, inp)

		self.assertEqual(set([	"2015-01-02"]), set(out))

	def test_always_keep_invalid(self):
		args = MockArgs()
		args.show_keep = True

		inp = _gen_state(4, "%Y-%m-%d")
		inp.append("strange")

		out = run(args, inp)

		self.assertEqual(set([	"strange",
					"2015-01-01",
					"2015-01-03",
					"2015-01-04"]), set(out))

	def test_never_delete_invalid(self):
		args = MockArgs()
		args.show_delete = True

		inp = _gen_state(4, "%Y-%m-%d")
		inp.append("strange")

		out = run(args, inp)

		self.assertEqual(set([	"2015-01-02"]), set(out))

	def test_unsafe(self):
		args = MockArgs()
		args.show_keep = True

		inp = [	"2015-01-01",
			"2015-01-04" ]

		self.assertRaises(Log2RotateUnsafeError, run, args, inp)

	def test_unsafe_force(self):
		args = MockArgs()
		args.show_keep = True
		args.unsafe = True

		inp = [	"2015-01-01",
			"2015-01-04" ]

		out = run(args, inp)

		self.assertEqual(set([	"2015-01-01",
					"2015-01-04"]), set(out))

	def test_fuzz(self):
		args = MockArgs()
		args.fuzz = 1
		args.show_keep = True

		inp = [	"2015-01-01",
			"2015-01-04" ]

		out = run(args, inp)

		self.assertEqual(set(inp), set(out))

	def test_duplicates_ignored_keep(self):
		args = MockArgs()
		args.show_keep = True

		inp = _gen_state(4, "%Y-%m-%d")

		self.assertEqual(	run(args, inp),
					run(args, inp*2) )

	def test_duplicates_ignored_delete(self):
		args = MockArgs()
		args.show_delete = True

		inp = _gen_state(4, "%Y-%m-%d")

		self.assertEqual(	run(args, inp),
					run(args, inp*2) )
if __name__ == '__main__':
	unittest.main()
