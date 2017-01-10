import sys
from random import shuffle

import numpy as np
import scipy.stats as stats
import pylab as pl
import matplotlib.pyplot as plt

from importer.StrategyImporter import StrategyImporter


GAMES = 20000
SHOE_SIZE = 6
SHOE_PENETRATION = 0.25
BET_SPREAD = 20.0

DECK_SIZE = 52.0
CARDS = {"Ace": 11, "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8, "Nine": 9, "Ten": 10, "Jack": 10, "Queen": 10, "King": 10}
BASIC_OMEGA_II = {"Ace": 0, "Two": 1, "Three": 1, "Four": 2, "Five": 2, "Six": 2, "Seven": 1, "Eight": 0, "Nine": -1, "Ten": -2, "Jack": -2, "Queen": -2, "King": -2}

BLACKJACK_RULES = {
	'triple7': False, #Count 3x7 as a blackjack
}

HARD_STRATEGY = {}
SOFT_STRATEGY = {}
PAIR_STRATEGY = {}


class Card(object):
	"""
	Represents a card with name and value.
	"""
	def __init__(self, name, value):
		self.name = name
		self.value = value

	def __str__(self):
		return "%s" % self.name
		

class Shoe(object):
	"""
	Represents the shoe, which consists of a number of card decks.
	"""
	reshuffle = False

	def __init__(self, decks):
		self.count = 0
		self.count_history = []
		self.ideal_count = {}
		self.decks = decks
		self.cards = self.init_cards()
		self.init_count()

	def __str__(self):
		s = ""
		for c in self.cards:
			s += "%s\n" % c
		return s

	def init_cards(self):
		"""
		Initialize the shoe with shuffled playing cards and set count to zero.
		"""
		self.count = 0
		self.count_history.append(self.count)

		cards = []
		for d in range(self.decks):
			for c in CARDS:
				for i in range(0, 4):
					cards.append(CArd(c, CARDS[c]))
		shuffle(cards)
		return cards

	def init_count(self):
		"""Keep track of the number of occurences for each card in the shoe in the course over the game.
		   ideal_count is a dict containing (card name - number of occurences in shoe) pairs.
		"""

		for card in cards:
			self.ideal_count[card] = 4 * SHOE_SIZE

	def deal(self):
		"""
		Returns: The next card in the shoe. If the shoe penetration is reached, the shoe gets reshuffled.
		"""
		if self.shoe_penetration() < SHOE_PENETRATION:
			self.reshuffle = True
		card = self.cards.pop()

		assert self.ideal_count[card.name] > 0, "Either a cheater or bug!"
		self.ideal_count[card.name] -= 1

		self.do_count(card)
		return card

	def do_count(self, card):
		"""
		Add the dealt card to current count.
		"""
		self.count += BASIC_OMEGA_II[card.name]
		self.count_history.append(self.truecount())

	def truecount(self):
		"""
		Return: The current true count.
		"""
		return self.count / (self.decks * self.shoe_penetration())

	def shoe_penetration(self):
		"""
		Returns: Ratio of cards that are still in the show to all initial cards.
		"""
		return len(self.cards) / (DECK_SIZE * self.decks)


class Hand(object):
		"""
	Represents a hand, either from the dealer or the player
	"""
	_value = 0
	_aces = []
	_aces_soft = 0
	splithand = False
	surrender = False
	doubled = False

	def __init__(self, cards):
		self.cards = cards
		
	def __str__(self):
		h = ""
		for c in self.cards:
			h += "%s " % c
		return h

	@property
	def value(self):
		"""
		Returns: The current value of the hand(aces are either counted as 1 or 11).
		"""
		self._value = 0
		for c in self.cards:
			self._value += c.value

		if self._value > 21 and self.aces_soft > 0:
			for ace in self.aces:
				if ace.value == 11:
					self._value -= 10
					ace.value = 1
					if self._value <= 21:
						break
		return self._value

	@property
	def aces(self):
		"""
		Return: All the aces in the current hand
		"""
		self._aces = []
		for c in self.cards:
			if c.name == "Ace":
				self._aces.append(c)
		return self._aces

	@property
	def aces_soft(self):
		"""
		Returns: The number of aces values as 11
		"""
		self._aces_soft = 0
		for ace in self.aces:
			if ace.value == 11:
				self._aces_soft += 1
		return self._aces_soft

	def soft(self):
		"""
		Determines whether the current hand is soft (soft means that it consists of aces valued at 11)
		"""
		if self.aces_soft > 0:
			return True
		else:
			return False

	def splitable(self):
		"""
		Determines if the current hand can be splited
		"""
		if self.length() == 2 and self.cards[0].name == self.cards[1].name:
			return True
		else:
			return False

	def blackjack(self):
		"""
		Check a hand for blackjack. Taking the defined BLACKJACK_RULES into account.
		"""
		if not self.splithand and self.value == 21:
			if all(c.value == 7 for c in self.cards) and BLACKJACK_RULES['triple7']:
				return True
			elif self.length() == 2:
				return True
			else:
				return False
		else:
			return False

	def busted(self):
		"""
		Checks if the hand is busted.
		"""
		if self.value > 21:
			return True
		else:
			return False

	def add_card(self, card):
		"""
		Add a card to the current hand.
		"""
		self.cards.append(card)

	def split(self):
		"""
		Split the current hand.
		Returns: The new hand created from the split.
		"""
		self.splithand = True
		c = self.cards.pop()
		new_hand = Hand([c])
		new_hand.splithand = True
		return new_hand

	def length(self):
		"""
		Returns: The number of cards in the current hand.
		"""
		return len(self.cards)













