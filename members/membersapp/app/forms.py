from django.forms import ModelForm
from .models import Members, Applications


class MemberForm(ModelForm):
    class Meta:
        model = Members
        fields = ['sub_private']


class ApplicationForm(ModelForm):
    class Meta:
        model = Applications
        fields = ['contrib', 'manager', 'manager_date', 'comment', 'approve', 'approve_date']
