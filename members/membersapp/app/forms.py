from django.forms import ModelForm, DateInput

from .models import Members, Applications


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
            'manager_date': DateInput(),
            'approve_date': DateInput()
        }


class ContribApplicationForm(ModelForm):
    class Meta:
        model = Applications
        fields = ['contrib']
