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
CARDS = {"Ace": 11, "Two": 2, "Three": 3, "Four": 4, "Five": 5, }