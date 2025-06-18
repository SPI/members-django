from django.db import connection
from openstv.MethodPlugins import ScottishSTV
from openstv.plugins import LoaderPlugin
from openstv.ballots import Ballots
import openstv

from .models import Members, VoteOption


VOTE_SYSTEMS = [(0, "Condorcet (ignore unspecified)"),
                (1, "Condorcet (unspecified ranked lowest)"),
                (2, "Scottish STV"),
                ]


class CondorcetVS(object):
    """Implementation of the Condorcet voting system"""
    def __init__(self, ballot, membervotes, ignoremissing=True):
        self.ballot = ballot
        self.membervotes = membervotes
        self.ignoremissing = ignoremissing
        # Initialise our empty beat matrix
        self.beatmatrix = {}
        options = VoteOption.objects.filter(ballot_ref=self.ballot)
        for row in options:
            self.beatmatrix[row.ref] = {}
            for col in options:
                self.beatmatrix[row.ref][col.ref] = 0
        self.tie = False
        self.winners = [None] * len(options)
        self.wincount = {}
        self.winners_count = [0] * len(options)

    @property
    def description(self):
        if self.ignoremissing:
            return "Condorcet (ignore unspecified)"
        else:
            return "Condorcet (unspecified ranked lowest)"

    def run(self):
        """Run the vote"""
        options = [x.ref for x in VoteOption.objects.filter(ballot_ref=self.ballot)]

        # Fill the beat matrix. bm[x][y] is the number of times x was
        # preferred over y.
        for membervote in self.membervotes:
            votecounted = {}
            for curpref, pref in enumerate(membervote.votes):
                votecounted[pref.ref] = True
                for lesspref in membervote.votes[curpref + 1:]:
                    self.beatmatrix[pref.ref][lesspref.ref] += 1

                # If we're not ignoring missing options then treat them
                # as lower preference than anyone who was listed.
                if not self.ignoremissing:
                    for missing in options:
                        # Check it's actually missing
                        if missing not in votecounted:
                            for counted in votecounted:
                                self.beatmatrix[counted][missing] += 1

        for row in options:
            wins = 0
            self.wincount[row] = {}
            for col in options:
                if row != col:
                    self.wincount[row][col] = (self.beatmatrix[row][col] -
                                               self.beatmatrix[col][row])
                    if self.wincount[row][col] > 0:
                        wins += 1

            self.wincount[row]['wins'] = wins

            if self.winners[wins]:
                self.tie = True
                self.winners[wins] += " AND "
                self.winners[wins] += VoteOption.object.get(ref=row).description
                self.winners_count[wins] += 1
            else:
                self.winners[wins] = VoteOption.object.get(ref=row).description
                self.winners_count[wins] = 1

    def results(self):
        """Return an array of the vote winners"""
        # Confusingly, several variables with similar names here:
        # - self.ballot.winners is the number of winners in the ballot
        # - self.winners contains an array of pairwise wins
        # - winners declared below contains an array of the winners names
        winners = []
        losers = []
        nb_registered = 0
        for i in range(len(self.winners) - 1, -1, -1):
            if self.winners[i] is not None:
                if nb_registered < self.ballot.winners:
                    nb_registered += self.winners_count[i]
                    winners.append(self.winners[i])
                else:
                    losers.append(self.winners[i])
        return {"winners": winners, "losers": losers}


class OpenSTVVS(object):
    """Implementation of various STV voting systems using OpenSTV"""
    def __init__(self, ballot, membervotes, system="ScottishSTV"):
        self.ballot = ballot
        self.membervotes = membervotes
        self.tie = False
        self.system = ScottishSTV.ScottishSTV
        self.election = None

    @property
    def description(self):
        """Return a text string describing the voting system"""
        return self.system.longMethodName + " (OpenSTV)"

    def run(self):
        """Run the vote using the OpenSTV backend"""
        loader = SPIBallotLoader(self.ballot, self.membervotes)
        dirty = Ballots()
        dirty.loader = loader
        loader.loadballots(dirty)
        clean = dirty.getCleanBallots()
        self.election = self.system(clean)
        self.election.runElection()

    def results(self):
        """Return an array of the vote winners"""
        winners = list(self.election.winners)
        winners.sort()
        if len(winners) == 0:
            return None
        else:
            return {'winners': [self.election.b.names[c] for c in winners], 'losers': []}


class SPIBallotLoader(LoaderPlugin):
    "OpenSTV Ballot loader class for SPI Membership Website"

    def __init__(self, ballot, membervotes):
        self.ballot = ballot
        self.membervotes = membervotes
        LoaderPlugin.__init__(self)
        self.options = VoteOption.objects.filter(ballot_ref=ballot)

    def loadballots(self, ballots):
        "Load data from the database into an OpenSTV ballot object"

        ballots.numCandidates = len(self.options)
        ballots.numSeats = self.ballot.winners
        ballots.title = self.ballot.title
        # Make a textual array
        ballots.names = []
        optionmap = {}
        for (index, option) in enumerate(sorted(self.options,
                                                key=lambda option:
                                                option.option_character)):
            ballots.names.append(option.description)
            optionmap[option.option_character] = index

        for vote in self.membervotes:
            ballot = []

            for rank in vote.votes:
                ballot.append(optionmap[rank.option_character])

            ballots.appendBallot(ballot)
