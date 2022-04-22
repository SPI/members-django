from django.forms import ModelForm
from .models import Members


class MemberForm(ModelForm):
    class Meta:
        model = Members
        fields = ['sub_private']
