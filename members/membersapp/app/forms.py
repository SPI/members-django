import datetime

from django.forms import Form, CharField, IntegerField, ModelForm, DateInput, ChoiceField, HiddenInput

from .models import Members, Applications, VoteElection, VoteBallot, VoteOption
from .votes import VOTE_SYSTEMS


class DateInput(DateInput):
    input_type = 'date'


class MemberForm(ModelForm):
    class Meta:
        model = Members
        fields = ['sub_private']


class ApplicationForm(ModelForm):
    class Meta:
        model = Applications
        fields = ['contrib', 'manager', 'manager_date', 'comment', 'approve', 'approve_date']
        widgets = {
            'manager_date': DateInput(format=('%Y-%m-%d'), attrs={'class': 'datepicker', 'value': datetime.datetime.now().strftime("%Y-%m-%d")}),
            'approve_date': DateInput(format=('%Y-%m-%d'), attrs={'class': 'datepicker', 'value': datetime.datetime.now().strftime("%Y-%m-%d")})
        }


class ContribApplicationForm(ModelForm):
    class Meta:
        model = Applications
        fields = ['contrib']


class CreateVoteForm(ModelForm):
    class Meta:
        model = VoteElection
        fields = ['title', 'period_start', 'period_stop']
        widgets = {
            'period_start': DateInput(),
            'period_stop': DateInput()
        }


class CreateVoteFormBallot(ModelForm):
    class Meta:
        model = VoteBallot
        fields = ['title', 'description', 'system', 'allow_blank']

    def __init__(self, *args, **kwargs):
        super(CreateVoteFormBallot, self).__init__(*args, **kwargs)
        limited_choices = [(choice[0], choice[1]) for choice in VOTE_SYSTEMS]
        self.fields['system'] = ChoiceField(choices=limited_choices)


class EditVoteForm(CreateVoteForm):
    class Meta:
        model = VoteElection
        fields = ['title', 'period_start', 'period_stop']
        widgets = {
            'period_start': DateInput(),
            'period_stop': DateInput()
        }


class EditVoteFormBallot(CreateVoteFormBallot):
    ref = IntegerField(required=True, widget=HiddenInput())

    class Meta:
        model = VoteBallot
        fields = ['ref', 'title', 'description', 'system', 'winners']


class VoteOptionForm(ModelForm):
    class Meta:
        model = VoteOption
        fields = ['option_character', 'description', 'sort']
        exclude = ['ballot_ref']

    def __init__(self, *args, **kwargs):
        super(VoteOptionForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        if initial is not None:
            voteoptions = VoteOption.objects.filter(ballot_ref=initial['ballot_ref'])
            if len(voteoptions) == 0:
                self.fields['option_character'].initial = 'A'
            else:
                nextchar = chr(max([ord(x.option_character) for x in voteoptions]) + 1)
                self.fields['option_character'].initial = str(nextchar)


class VoteVoteForm(Form):
    vote = CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(VoteVoteForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        if initial is not None and initial['allow_blank'] is not None:
            self.fields['vote'].required = not initial['allow_blank']
