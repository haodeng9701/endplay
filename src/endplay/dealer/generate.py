﻿__all__ = ['generate_deal', 'generate_deals']

from endplay.dealer.constraint import ConstraintInterpreter, Expr
from endplay.types import *
from numpy.random import RandomState # guaranteed to be stable for numpy>=1.16
from typing import Iterator, Optional, Union
import warnings
from tqdm import trange

class DealNotGeneratedError(RuntimeError):
	pass

class DealNotGeneratedWarning(Warning):
	pass

class InconsistentSwappingAlgorithmWarning(Warning):
	pass

def generate_deal(
	*constraints: Union[Expr, str], 
	predeal: Deal = Deal(), 
	swapping: int = 0, 
	seed: Optional[int] = None,
	max_attempts: int = 1000000, 
	env: dict = {}) -> Deal:
	"""
	Generates a random deal satisfying the constraints, giving 13 cards to each player.
	The constraints should be supplied as functions taking a whole deal and returning
	a boolean, for example `lambda d: hcp(d.north) > 10`, or as expressions compatible 
	with the dealer expression syntax (see https://www.bridgebase.com/tools/dealer/Manual/input.html#expr)

	:param constraints: Constraints, as callables or strings
	:param predeal: A `Deal` object which may be partially filled with cards; these will not
		be shuffled, allowing you to specify that players should have particular holdings.
	:param swapping: An integer representing the type of swapping algorithm to use, either
		0 (no swapping), 2 (swapping EW) or 3 (swapping EWS)
	:param seed: The number to seed the random generator with. A `numpy` random generator is
		used which is guaranteed to be stable between Python releases.
	:param max_attempts: Maximum number of shuffles to perform when finding a deal which
		matches the constraints. Set to -1 for infinite
	:param env: A dictionary of the environment used when evaluating constraints
	"""
	# We just call generate deals and return the first deal that is yielded. The parameters
	# are the same and so are just forwarded onwards, with the exception that we always set
	# exhaustion_is_error to True (as it really *is* an error to not generate a single hand)
	# and we set show_progress to False as this would show all zeros right until the one hand
	# we want to produce is produced.
	deals = generate_deals(
		*constraints, 
		predeal = predeal,
		swapping = swapping, 
		show_progress = False,
		produce = 1,
		seed = seed, 
		max_attempts = max_attempts, 
		env = env,
		strict = True)
	return next(deals)

def generate_deals(
	*constraints: Union[Expr, str], 
	predeal: Deal = Deal(), 
	swapping: int = 0, 
	show_progress: bool = False,
	produce: int = 40,
	seed: Optional[int] = None,
	max_attempts: int = 1000000, 
	env: dict = {},
	strict: bool = False) -> Iterator[Deal]:
	"""
	Generates `produce` random deals satisfying the constraints which should
	be given as for `generate_deal`. `produce` and `max_attemps` are upper limits,
	the first to be reached terminates the program

	:param constraints: Constraints, as callables or strings
	:param predeal: A `Deal` object which may be partially filled with cards; these will not
		be shuffled, allowing you to specify that players should have particular holdings.
	:param swapping: An integer representing the type of swapping algorithm to use, either
		0 (no swapping), 2 (swapping EW) or 3 (swapping EWS)
	:param show_progress: If True, a progress bar is displayed with information on how many hands
		have been generated so far
	:param produce: The total number of hands satisfying the constraints to find.
	:param seed: The number to seed the random generator with. A `numpy` random generator is
		used which is guaranteed to be stable between Python releases.
	:param max_attempts: Maximum number of shuffles to perform when finding a deal which
		matches the constraints. Set to -1 for infinite
	:param env: A dictionary of the environment used when evaluating constraints
	:param strict: If True, a `RuntimeError` is raised if `max_attempts` is reached before
		`produce` hands are produced. Otherwise, a warning is generated
	"""
	if swapping == 2 and (len(predeal.west) > 0 or len(predeal.east) > 0):
		warnings.warn("2-way swapping is incompatible with E/W predealt, output may be unexpected", InconsistentSwappingAlgorithmWarning)
	elif swapping == 3 and (len(predeal.west) > 0 or len(predeal.east) > 0 or len(predeal.south) > 0):
		warnings.warn("3-way swapping is incompatible with E/W/S predealt, output may be unexpected", InconsistentSwappingAlgorithmWarning)

	rs = RandomState(seed)

	ci = ConstraintInterpreter()
	for name, val in env.items():
		ci.set_env(name, val)
	constraints = [ci.lambdify(c) if not callable(c) else c for c in constraints]
	cards = set(Card(suit=denom, rank=rank) for denom in Denom.suits() for rank in Rank)
	cards = list(cards.difference(predeal.to_hand()))
	split = [sum([13 - len(hand) for hand in predeal][:i]) for i in range(5)]
	res = []
	generated = 0
	if show_progress:
		prange = trange(produce, desc="Produced", unit="deals")
	else:
		prange = range(produce)
	for p in prange:
		if show_progress and p > 0:
			prange.set_postfix({"success": f"{100*p/generated:.2f}%"})
		produced = False
		while not produced:
			if generated == max_attempts:
				if show_progress:
					prange.close()
				message = f"Only {p} out of {produce} hands were generated before max_attempts (set to {max_attempts}) was reached"
				if strict:
					raise DealNotGeneratedError(message)
				else:
					warnings.warn(message, DealNotGeneratedWarning)
					return generated
			generated += 1
			rs.shuffle(cards)
			deal = predeal.copy()
			for i, player in enumerate(Player):
				deal[player].extend(cards[split[i]:split[i+1]])
			for perm in _generate_swaps(deal, swapping):
				if all(c(perm) for c in constraints):
					yield perm
					produced = True
					break
	return generated

def _generate_swaps(deal: Deal, swapping: int):
	if swapping == 0:
		yield deal
	elif swapping == 2:
		yield deal
		deal.swap(1, 3)
		yield deal
	elif swapping == 3:
		for _ in range(3):
			deal.swap(1, 2)
			yield deal
			deal.swap(2, 3)
			yield deal
	else:
		raise ValueError(f"Invalid swapping value {swapping} used")
