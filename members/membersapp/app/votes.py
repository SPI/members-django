from django.db import connection
from .openstv.openstv.plugins import getMethodPlugins

from .models import Members, VoteOption


VOTE_SYSTEMS = [(0, "Condorcet (ignore unspecified)"),
                (1, "Condorcet (unspecified ranked lowest)"),
                (2, "Scottish STV"),
                ]


class CondorcetVS(object):
    """Implementation of the Condorcet voting system"""
    def __init__(self, vote, membervotes, ignoremissing=True):
        self.vote = vote
        self.membervotes = membervotes
        self.ignoremissing = ignoremissing
        # Initialise our empty beat matrix
        self.beatmatrix = {}
        options = VoteOption.objects.filter(election_ref=self.vote)
        for row in options:
            self.beatmatrix[row.ref] = {}
            for col in options:
                self.beatmatrix[row.ref][col.ref] = 0
        self.tie = False
        self.winners = [None] * len(options)
        self.wincount = {}

    @property
    def description(self):
        if self.ignoremissing:
            return "Condorcet (ignore unspecified)"
        else:
            return "Condorcet (unspecified ranked lowest)"

    def run(self):
        """Run the vote"""
        options = [x.ref for x in VoteOption.objects.filter(election_ref=self.vote)]

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
            else:
                self.winners[wins] = VoteOption.object.get(ref=row).description

    def results(self):
        """Return an array of the vote winners"""
        return reversed(self.winners)


class OpenSTVVS(object):
    """Implementation of various STV voting systems using OpenSTV"""
    def __init__(self, vote, membervotes, system="ScottishSTV"):
        self.vote = vote
        self.membervotes = membervotes
        self.tie = False
        methods = getMethodPlugins("byName", exclude0=False)
        if system not in methods:
            raise Exception("Unknown OpenSTV method " + system)
        self.system = methods[system]
        self.election = None

    @property
    def description(self):
        """Return a text string describing the voting system"""
        return self.system.longMethodName + " (OpenSTV)"

    def run(self):
        """Run the vote using the OpenSTV backend"""
        loader = SPIBallotLoader(self.vote, self.membervotes)
        dirty = openstv.ballots.Ballots()
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
            return [self.election.b.names[c] for c in winners]
