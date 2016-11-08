#!/usr/bin/env python2
from __future__ import division
import math
import paho.mqtt.client as mqtt

def mean(values):
	return sum(values) / len(values)

class Meh:
	def __init__(self, mean, err):
		self.mean = mean
		self.err = err

	def __repr__(self):
		return "{:.1f}+{:.1f}".format(self.mean, self.err)

	def __mul__(self, other):
		assert isinstance(other, float)
		return Meh(self.mean * other, self.err * other)

	def __add__(self, other):
		if isinstance(other,self.__class__):
			return Meh(
				self.mean + other.mean,
				math.hypot(self.err, other.err))
		else:
			return Meh(
				self.mean + other,
				self.err)

	def __sub__(self, other):
		if isinstance(other,self.__class__):
			return Meh(
				self.mean - other.mean,
				math.hypot(self.err, other.err))
		else:
			return Meh(
				self.mean - other,
				self.err)

class Average:
	def __init__(self, n=10):
		self.n = n
		self.values = []

	def __call__(self):
		return Meh(self.mean, self.meanerr)

	def __repr__(self):
		return repr(self())

	def is_full(self):
		return len(self.values) >= self.n

	def clear(self):
		self.values = []

	@property
	def mean(self):
		if len(self.values):
			return mean(self.values)
		else:
			return float('nan')

	def __float__(self):
		return self.mean

	@property
	def meanerr(self):
		if len(self.values) >= 2:
			m = self.mean
			return sum([abs(x - m) for x in self.values]) / (len(self.values) - 1)
		else:
			return float('inf')

	def sigma(self, value):
		meanerr = self.meanerr
		if meanerr > 0:
			return abs((value - self.mean) / self.meanerr)
		else:
			return float('inf')

	def add(self, value):
		self.values.append(value)
		self.values = self.values[-self.n:]

class Weight:
	def __init__(self, gram_per_lsb=None):
		self.eps = 50 # grams
		self.gram_per_lsb = gram_per_lsb
		self.zero = Average()
		self.value = Average()

	def add(self, nval):
		if (not self.zero.is_full()) or (abs((nval - self.zero.mean) * self.gram_per_lsb) < self.eps):
			self.zero.add(nval)
			self.value.clear()
		else:
			self.value.add(nval)
			return self.value() - self.zero()

if __name__ == '__main__':
	#(topic, lsb_per_gram) = sys.argv[1:]
	topic = "weight"
	gram_per_lsb = None
	gram_per_lsb = 908.75 / 21228.700
	gram_per_lsb = 2614 / 60004.600

	weight = Weight(gram_per_lsb)

	def on_connect(client, userdata, rc):
		client.subscribe(topic)

	def on_message(client, userdata, msg):
		#topic = msg.topic

		#is_text = all(32 <= c <= 127 for c in msg.payload)
		payload = msg.payload.decode('latin1')
		adcval = int(payload)
		print("")
		print("zero:  {!r} (+{:.1f} g)".format(weight.zero, weight.zero.meanerr * gram_per_lsb))
		print("value: {!r}".format(weight.value))
		rv = weight.add(adcval)

		if rv is not None:
			print("-> {!r}".format(rv))

			if gram_per_lsb:
				rv *= gram_per_lsb

			print("-> {!r}".format(rv))

	client = mqtt.Client()
	client.on_connect = on_connect
	client.on_message = on_message

	client.connect("mqtt.space.aachen.ccc.de", 1883, 60)

	client.loop_forever()
