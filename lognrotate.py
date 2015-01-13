from math import log

def backups_to_keep(n):
	if n == 0:
		return set()
	elif n == 1:
		return set([1])
	else:
		return set([n]) | backups_to_keep(n - 2**(int(log(n, 2)) - 1))

class Log2Rotate(object):
	def backups_to_keep(self, state):
		state_sorted = sorted(state, cmp=self.cmp)

		if len(state_sorted) < 2:
			return state_sorted
		else:
			last = state_sorted[-1]
			first = state_sorted[0]

			n = self.sub(last, first) + 1

			r = backups_to_keep(n)

			new_state = []
			for b in state:
				n0 = self.sub(last, b) + 1

				if n0 in r:
					new_state.append(b)

			return new_state

	def cmp(self, x, y):
		return cmp(x, y)

	def sub(self, x, y):
		return x - y

class Log2RotateStr(Log2Rotate):

	def cmp(self, x, y):
		x2 = self.strptime(x)
		y2 = self.strptime(y)

		return cmp(x2, y2)

	def sub(self, x, y):
		x2 = self.strptime(x)
		y2 = self.strptime(y)

		return (x2 - y2).days

if __name__ == '__main__':
	unittest.main()
