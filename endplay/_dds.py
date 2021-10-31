"""
Python bindings for Bo Haglund's DDS library. This provides a very low-level
ctypes wrapper around the C++ library. The only extra convenience provided is
to wrap all of the dds functions so that instead of returning error codes they
raise a `DDSError`.
"""

__all__ = [
	"init", "MAXNOOFBOARDS", "MAXNOOFTABLES", "SolveBoard", "SolveBoardPBN", "CalcDDtable",
	"CalcDDtablePBN", "CalcAllTables", "CalcAllTablesPBN", "SolveAllBoards", "SolveAllBoardsBin",
	"SolveAllChunksBin", "SolveAllChunks", "SolveAllChunksPBN", "Par", "DealerPar", "DealerParBin",
	"ConvertToDealerTextFormat", "SidesPar", "SidesParBin", "ConvertToSidesTextFormat", "CalcPar",
	"CalcParPBN", "AnalysePlayBin", "AnalysePlayPBN", "AnalyseAllPlaysBin", "AnalyseAllPlaysPBN",
	"SetMaxThreads", "FreeMemory", "DDSError"
]

import ctypes
import os
import re
from typing import Iterable, Optional
from warnings import warn
from functools import wraps

#----------------------------------------------------
# Key for the various encodings used by the DDS
# library
#
# Suits
#   Spades     0
#   Hearts     1
#   Diamonds   2
#   Clubs      3
#   NT         4
# Hand
#   North      0
#   East       1
#   South      2
#   West       3
# Vulnerable
#   None       0
#   Both       1
#   NS Only    2
#   EW Only    3
# Side
#   NS         0
#   EW         1
# Card
#   2          0x4
#   3          0x8
#   ...
#   K          0x2000
#   A          0x4000


#----------------------------------------------------
# Meta functionality required accessing the
# underlying shared library from Python


# Handle to the DDS shared library
_dll_path = os.path.dirname(os.path.abspath(__file__))
if os.name == "nt":
	_dll = ctypes.WinDLL(os.path.join(_dll_path, ".libs", "dds.dll"))
else:
	_dll = ctypes.CDLL(os.path.join(_dll_path, ".libs", "dds.so"))

# Hard coded constants from the DDS library (used for the size of stack-allocated arrays and stuff)
MAXNOOFBOARDS = 200
MAXNOOFTABLES = 40

def init(dds_libfile: Optional[str] = None, dds_header: Optional[str] = None, max_threads: int = 0):
	"""
	Initialize the library by finding the dds shared library and
	using this to set the `_dll` variable. If the `dds_header` is
	provided, then this is used to try and set the values of
	MAXNOOFBOARDS and MAXNOOFTABLES, although these shouldn't change
	"""
	global _dll, MAXNOOFBOARDS, MAXNOOFTABLES

	if dds_libfile is None:
		# Examine environment variables for DDS_LIBFILE
		if "DDS_LIBFILE" in os.environ:
			dds_libfile = os.environ["DDS_LIBFILE"]
		# Search through PATH to see if we can find it
		else:
			name = "dds." + ("dll" if os.name == "nt" else "so")
			path = os.environ["PATH"].split(os.pathsep)
			for p in path:
				libfile = os.path.join(p, name)
				if os.path.isfile(libfile):
					dds_libfile = libfile
					break
			else:
				dds_libfile = name
	try:
		if os.name == "nt":
			_dll = ctypes.WinDLL(dds_libfile)
		else:
			_dll = ctypes.CDLL(dds_libfile)
	except OSError as e:
		raise OSError(f"_dds: Loading shared library {dds_libfile} failed with the following error: {e}")
		
	SetMaxThreads(max_threads)

	if dds_header is not None:
		defines = {}
		directive = re.compile(r"#define\s+(\w+)(?:\s+(.*))?")
		with open(dds_header) as f:
			for line in f:
				m = directive.match(line)
				if m:
					defines[m.group(1)] = m.group(2)
		if "MAXNOOFBOARDS" in defines:
			MAXNOOFBOARDS = int(defines["MAXNOOFBOARDS"])
		if "MAXNOOFTABLES" in defines:
			MAXNOOFTABLES = int(defines["MAXNOOFTABLES"])


#----------------------------------------------------
# Datatypes exported by DDS

class deal(ctypes.Structure):
	_fields_ = [
		("trump", ctypes.c_int),
		("first", ctypes.c_int),
		("currentTrickSuit", ctypes.c_int * 3),
		("currentTrickRank", ctypes.c_int * 3),
		("remainCards", (ctypes.c_uint * 4) * 4)
	]

class dealPBN(ctypes.Structure):
	_fields_ = [
		("trump", ctypes.c_int),
		("first", ctypes.c_int),
		("currentTrickSuit", ctypes.c_int * 3),
		("currentTrickRank", ctypes.c_int * 3),
		("remainCards", ctypes.c_char * 80)
	]

class ddTableDeal(ctypes.Structure):
	_fields_ = [
		("cards", (ctypes.c_uint * 4) * 4)	
	]

class ddTableDealPBN(ctypes.Structure):
	_fields_ = [
		("cards", ctypes.c_char * 80)	
	]

class ddTableDeals(ctypes.Structure):
	_fields_ = [
		("noOfTables", ctypes.c_int),
		("ddTableDeal", ddTableDeal * (MAXNOOFTABLES * 5))
	]

class ddTableDealsPBN(ctypes.Structure):
	_fields_ = [
		("noOfTables", ctypes.c_int),
		("ddTableDealPBN", ddTableDealPBN * (MAXNOOFTABLES * 5))
	]

class boards(ctypes.Structure):
	_fields_ = [
		("noOfBoards", ctypes.c_int),
		("deals", deal * MAXNOOFBOARDS),
		("target", ctypes.c_int * MAXNOOFBOARDS),
		("solutions", ctypes.c_int * MAXNOOFBOARDS),
		("mode", ctypes.c_int * MAXNOOFBOARDS)
	]

class boardsPBN(ctypes.Structure):
	_fields_ = [
		("noOfBoards", ctypes.c_int),
		("deals", dealPBN * MAXNOOFBOARDS),
		("target", ctypes.c_int * MAXNOOFBOARDS),
		("solutions", ctypes.c_int * MAXNOOFBOARDS),
		("mode", ctypes.c_int * MAXNOOFBOARDS)
	]

class futureTricks(ctypes.Structure):
	_fields_ = [
		("nodes", ctypes.c_int),
		("cards", ctypes.c_int),
		("suit", ctypes.c_int * 13),
		("rank", ctypes.c_int * 13),
		("equals", ctypes.c_int * 13),
		("score", ctypes.c_int * 13)
	]

class solvedBoards(ctypes.Structure):
	_fields_ = [
		("noOfBoards", ctypes.c_int),
		("solvedBoard", futureTricks * MAXNOOFBOARDS)
	]

class ddTableResults(ctypes.Structure):
	_fields_ = [
		("resTable", (ctypes.c_int * 4) * 5)	
	]

class ddTablesRes(ctypes.Structure):
	_fields_ = [
		("noOfBoards", ctypes.c_int),
		("results", ddTableResults * (MAXNOOFTABLES * 5))
	]

class parResults(ctypes.Structure):
	_fields_ = [
		("parScore", (ctypes.c_char * 2) * 16),
		("parContractsString", (ctypes.c_char * 2) * 128)
	]

class allParResults(ctypes.Structure):
	_fields_ = [
		("presults", parResults * MAXNOOFTABLES)	
	]

class parResultsDealer(ctypes.Structure):
	_fields_ = [
		("number", ctypes.c_int),
		("score", ctypes.c_int),
		("contracts", (ctypes.c_char * 10) * 10)
	]

class contractType(ctypes.Structure):
	_fields_ = [
		("underTricks", ctypes.c_int),
		("overTricks", ctypes.c_int),
		("level", ctypes.c_int),
		("denom", ctypes.c_int),
		("seats", ctypes.c_int)
	]

class parResultsMaster(ctypes.Structure):
	_fields_ = [
		("score", ctypes.c_int),
		("number", ctypes.c_int),
		("contracts", contractType * 10)
	]

class parTextResults(ctypes.Structure):
	_fields_ = [
		("parText", (ctypes.c_char * 2) * 128),
		("equal", ctypes.c_int)
	]

class DDSInfo(ctypes.Structure):
	_fields_ = [
		("major", ctypes.c_int),
		("minor", ctypes.c_int),
		("patch", ctypes.c_int),
		("versionString", ctypes.c_char * 10),
		("system", ctypes.c_int),
		("compiler", ctypes.c_int),
		("constructor", ctypes.c_int),
		("threading", ctypes.c_int),
		("noOfThreads", ctypes.c_int),
		("systemString", ctypes.c_char * 512)
	]

class playTraceBin(ctypes.Structure):
	_fields_ = [
		("number", ctypes.c_int),
		("suit", ctypes.c_int * 52),
		("rank", ctypes.c_int * 52)
	]

class playTracePBN(ctypes.Structure):
	_fields_ = [
		("number", ctypes.c_int),
		("cards", ctypes.c_char * 106)	
	]

class playTracesBin(ctypes.Structure):
	_fields_ = [
		("noOfBoards", ctypes.c_int),
		("plays", playTraceBin * MAXNOOFBOARDS)
	]

class playTracesPBN(ctypes.Structure):
	_fields_ = [
		("noOfBoards", ctypes.c_int),
		("plays", playTracePBN * MAXNOOFBOARDS)
	]

class solvedPlay(ctypes.Structure):
	_fields_ = [
		("number", ctypes.c_int),
		("tricks", ctypes.c_int * 53)
	]

class solvedPlays(ctypes.Structure):
	_fields_ = [
		("noOfBoards", ctypes.c_int),
		("solved", solvedPlay * MAXNOOFBOARDS)
	]


#----------------------------------------------------
# Functions exposed by DDS related to internal state

def SetMaxThreads(userThreads: int):
	"""
	Used at initial start and can also be called with 
	a request for allocating memory for a specified 
	number of threads. Is apparently¸mandatory on Linux 
	and Mac (optional on Windows)
	"""
	return _dll.SetMaxThreads(userThreads)
	
def FreeMemory():
	"Frees DDS allocated dynamical memory."
	return _dll.FreeMemory()

#----------------------------------------------------
# DDSError and _try_call allow the conversion of
# error codes returned by the DDS functions into
# Python exceptions

def ErrorMessage(code: int, line: str):
	"Turns a return code into an error message string"
	return _dll.ErrorMessage(code, line)

class DDSError(RuntimeError):
	"Exception class indicating an error is returned from a DDS function"
	def __init__(self, code):
		self.code = code
		msg = ctypes.create_string_buffer(80)
		_dll.ErrorMessage(code, msg)
		super().__init__(msg.value.decode('utf-8'))
		
def _try_call(func):
	@wraps(func)
	def wrapper(*args):
		if _dll is None:
			init()
		res = func(*args)
		if res != 1:
			raise DDSError(res)
	return wrapper


#----------------------------------------------------
# Functions exposed by DDS related to hand
# calculations. These are all wrapped with the
# _try_call decorator which converts the return code 
# into an DDSError exception if an error is indicated.

@_try_call
def SolveBoard(dl: deal, target: int, solutions: int, mode: int, futp: futureTricks, threadIndex: int):
	"The most basic function, solves a single hand from the beginning or from later play"
	return _dll.SolveBoard(dl, target, solutions, mode, ctypes.byref(futp), threadIndex)

@_try_call
def SolveBoardPBN(dlPBN: dealPBN, target: int, solutions: int, mode: int, futp: futureTricks, threadIndex: int):
	"As SolveBoard, but with PBN deal format."
	return _dll.SolveBoardPBN(dlPBN, target, solutions, mode, ctypes.byref(futp), threadIndex)

@_try_call
def CalcDDtable(tableDeal: ddTableDeal, tablep: ddTableResults):
	"Solves an initial hand for all possible declarers and denominations (up to 20 combinations.)"
	return _dll.CalcDDtable(tableDeal, ctypes.byref(tablep))

@_try_call
def CalcDDtablePBN(tableDealPBN: ddTableDealPBN, tablep: ddTableResults):
	"As CalcDDtable, but with PBN deal format."
	return _dll.CalcDDtablePBN(tableDealPBN, ctypes.byref(tablep))

@_try_call
def CalcAllTables(dealsp: ddTableDeals, mode: int, trumpFilter: Iterable[int], resp: ddTablesRes, presp: allParResults):
	"Solves a number of hands in parallel. Multi-threaded."
	return _dll.CalcAllTables(ctypes.byref(dealsp), mode, (ctypes.c_int * 5)(*trumpFilter), ctypes.byref(resp), ctypes.byref(presp))

@_try_call
def CalcAllTablesPBN(dealsp: ddTableDealsPBN, mode: int, trumpFilter: Iterable[int], resp: ddTablesRes, presp: allParResults):
	"As CalcAllTables, but with PBN deal format."
	return _dll.CalcAllTablesPBN(ctypes.byref(dealsp), mode, (ctypes.c_int * 5)(*trumpFilter), ctypes.byref(resp), ctypes.byref(presp))

@_try_call
def SolveAllBoards(bop: boardsPBN, solvedp: solvedBoards):
	"Solves a number of hands in parallel. Multi-threaded."
	return _dll.SolveAllBoards(ctypes.byref(bop), ctypes.byref(solvedp))

@_try_call
def SolveAllBoardsBin(bop: boards, solvedp: solvedBoards):
	"Similar to SolveAllBoards, but with binary input."
	return _dll.SolveAllBoardsBin(ctypes.byref(bop), ctypes.byref(solvedp))

@_try_call
def SolveAllChunksBin(bop: boards, solvedp: solvedBoards, chunkSize: int):
	"Alias for SolveAllBoardsBin; don't use!"
	warn("Use SolveAllBoardsBin instead", DeprecationWarning)
	return _dll.SolveAllChunksBin(ctypes.byref(bop), ctypes.byref(solvedp), chunkSize)

@_try_call
def SolveAllChunks(bop: boards, solvedp: solvedBoards, chunkSize: int):
	"Alias for SolveAllBoards; don't use!"
	warn("Use SolveAllBoards instead", DeprecationWarning)
	return _dll.SolveAllChunks(ctypes.byref(bop), ctypes.byref(solvedp), chunkSize)

@_try_call
def SolveAllChunksPBN(bop: boardsPBN, solvedp: solvedBoards, chunkSize: int):
	"Alias for SolveAllBoards; don't use!"
	warn("Use SolveAllBoards instead", DeprecationWarning)
	return _dll.SolveAllChunksPBN(ctypes.byref(bop), ctypes.byref(solvedp), chunkSize)

@_try_call
def Par(tablep: ddTableResults, presp: parResults, vulnerable: int):
	"Solves for the par contracts given a DD result table."
	return _dll.Par(ctypes.byref(tablep), ctypes.byref(presp), vulnerable)

@_try_call
def DealerPar(tablep: ddTableResults, presp: parResultsMaster, dealer: int, vulnerable: int):
	"Similar to Par(), but requires and uses knowledge of the dealer."
	return _dll.DealerPar(ctypes.byref(tablep), ctypes.byref(presp), dealer, vulnerable)

@_try_call
def DealerParBin(tablep: ddTableResults, presp: parResultsMaster, dealer: int, vulnerable: int):
	"Similar to DealerPar, but with binary output."
	return _dll.DealerParBin(ctypes.byref(tablep), ctypes.byref(presp), dealer, vulnerable)

@_try_call
def ConvertToDealerTextFormat(pres: parResultsMaster, resp: ctypes.c_char_p):
	"Example of text output from DealerParBin."
	return _dll.ConvertToDealerTextFormat(ctypes.byref(pres), resp)

@_try_call
def SidesPar(tablep: ddTableResults, presp: parResultsDealer, vulnerable: int):
	"Par results are given for sides with the DealerPar output format."
	return _dll.SidesPar(ctypes.byref(tablep), ctypes.byref(presp), vulnerable)

@_try_call
def SidesParBin(tablep: ddTableResults, sidesRes: parResultsMaster * 2, vulnerable: int):
	"Similar to SidesPar, but with binary output."
	return _dll.SidesParBin(ctypes.byref(tablep), ctypes.byref(sidesRes), vulnerable)

@_try_call
def ConvertToSidesTextFormat(pres: parResultsMaster, resp: parTextResults):
	"Example of text output from SidesParBin."
	return _dll.ConvertToDealerTextFormat(ctypes.byref(pres), ctypes.byref(resp))

@_try_call
def CalcPar(tableDeal: ddTableDeal, vulnerable: int, CalcDDtablePBN: ddTableResults, presp: parResults):
	"Solves for both the DD result table and the par contracts. Is deprecated, use a CalcDDtable function plus Par() instead!"
	warn("Use CalcDDtable + Par instead", DeprecationWarning)
	return _dll.CalcPar(tableDeal, vulnerable, ctypes.byref(tablep), ctypes.byref(presp))

@_try_call
def CalcParPBN(tableDealPBN: ddTableDealPBN, tablep: ddTableResults, vulnerable: int, presp: parResults):
	"As CalcPar, but with PBN input format. Is deprecated, use a CalcDDtable function plus Par() instead!"
	warn("Use CalcDDtable + Par instead", DeprecationWarning)
	return _dll.CalcParPBN(tableDealPBN, ctypes.byref(tablep), vulnerable, ctypes.byref(presp))

@_try_call
def AnalysePlayBin(dl: deal, play: playTraceBin, solvedp: solvedPlay, thrId: int):
	"Returns the par result after each card in a particular play sequence."
	return _dll.AnalysePlayBin(dl, play, ctypes.byref(solvedp), thrId)

@_try_call
def AnalysePlayPBN(dlPBN: dealPBN, playPBN: playTracePBN, solvedp: solvedPlay, thrId: int):
	"As AnalysePlayBin, but with PBN deal format."
	return _dll.AnalysePlayPBN(dlPBN, playPBN, ctypes.byref(solvedp), thrId)

@_try_call
def AnalyseAllPlaysBin(bop: boards, plp: playTracesBin, solvedp: solvedPlays, chunkSize: int):
	"Solves a number of hands with play sequences in parallel. Multi-threaded."
	return _dll.AnalyseAllPlaysBin(ctypes.byref(bop), ctypes.byref(plp), ctypes.byref(solvedp), chunkSize)

@_try_call
def AnalyseAllPlaysPBN(bopPBN: boardsPBN, plpPBN: playTracesPBN, solvedp: solvedPlays, chunkSize: int):
	"As AnalyseAllPlaysBin, but with PBN deal format."
	return _dll.AnalyseAllPlaysPBN(ctypes.byref(bopPBN), ctypes.byref(plpPBN), ctypes.byref(solvedp), chunkSize)
