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
					cards.append(Card(c, CARDS[c]))
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


class Player(object):
	"""
	Represent a player
	"""
	def __init__(self, hand=None, dealer_hand=None):
		self.hands = [hand]
		self.dealer_hand = dealer_hand

	def set_hands(self, new_hand, new_dealer_hand):
		self.hands = [new_hand]
		self.dealer_hand = new_dealer_hand

	def play(self, shoe):
		for hand in self.hands:
			# print "Playing hand: %s" % hand
			self.play_hand(hand, shoe)

	def play_hand(self, hand, shoe):
		if hand.length() < 2:
			if hand.cards[0].name == "Ace":
				hand.cards[0].value = 11
			self.hhit(hand, shoe)

		while not hand.busted() and not hand.blackjack():
			if hand.soft():
				flag = SOFT_STRATEGY[hand.value][self.dealer_hand.cards[0].name]
			elif hand.splitable():
				flag = PAIR_STRATEGY[hand.value][self.dealer_hand.cards[0].name]
			else:
				flag = HARD_STRATEGY[hand.value][self.dealer_hand.cards[0].name]

			if flag == 'D':
				if hand.length() == 2:
					# print "Double Down"
					hand.doubled = True
					self.hit(hand, shoe)
					break
				else:
					flag = 'H'

			if flag == 'H':
				self.hit(hand, shoe)

			if flag == 'P':
				self.split(hand, shoe)

			if flag == 'S':
				break


	def hit(self, hand, shoe):
		c = shoe.deal()
		hand.add_card(c)
		# print "Hit %s" % hand
		self.play_hand(hand, shoe)

	def split(self, hand, shoe):
		self.hands.append(hand.split())
		# print "Split %s" % hand
		self.play_hand(hand, shoe)

class Dealer(object):
  """
  Represent the dealer
  """
  def __init__(self, hand=None):
      self.hand = hand

  def set_hand(self, new_hand):
      self.hand = new_hand

  def play(self, shoe):
      while self.hand.value < 17:
          self.hit(shoe)

  def hit(self, shoe):
      c = shoe.deal()
      self.hand.add_card(c)
      # print "Dealer hitted: %s" %c

  # Returns an array of 6 numbers representing the probability that the final score of the dealer is
  # [17, 18, 19, 20, 21, Busted] '''
  # TODO Differentiate 21 and BJ
  # TODO make an actual tree, this is false AF
  def get_probabilities(self) :
      start_value = self.hand.value
      # We'll draw 5 cards no matter what an count how often we got 17, 18, 19, 20, 21, Busted
