from math import log
import datetime
import unittest

from lognrotate import backups_to_keep, Log2RotateStr

def print_set(r):
	l = []
	for n in range(1, max(r)+1):
		if n in r:
			l.append('X')
		else:
			l.append(' ')
	
	print ''.join(l)
		

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

class Log2RotateTarsnap(Log2RotateStr):
	def strptime(self, s):
		return datetime.datetime.strptime(s, "backup-%Y%m%d")

class TestLog2RotateStr(unittest.TestCase):
	def setUp(self):
		self.l2r = Log2RotateTarsnap()

	def test_zero(self):
		self.assertEqual(set(), self.l2r.backups_to_keep([]))

	def _gen_state(self, n):
		now = datetime.datetime(2015, 1, 1)
		td = datetime.timedelta(days=1)

		state = []

		for i in range(n):
			state.append(now.strftime("backup-%Y%m%d"))
			now += td

		return state

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


if __name__ == '__main__':
	unittest.main()
