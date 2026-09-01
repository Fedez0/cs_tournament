import django.forms as forms
from .models import Team, TeamInvite
#importo il mio user personalizzato
from core.models import User

class TeamForm(forms.Form):
    
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), required=False)
    icon = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), required=False)
    is_open = forms.BooleanField(
        required=False,
        initial=True,
        label='Rendi il team visibile nel Squad Finder e aperto alle richieste',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    members = forms.CharField(widget=forms.HiddenInput(), required=False)  # IDs separati da virgola: utenti da invitare
    def clean_name(self):

        name = self.cleaned_data['name']

        if Team.objects.filter(name__iexact=name).exists():

            raise forms.ValidationError(

                "Esiste già un team con questo nome."

            )

        return name
    
    def clean_members(self):
        raw = self.cleaned_data.get('members', '')

        if not raw:
            return []
        try:
            ids = [int(i) for i in raw.split(',') if i.strip()]
        except ValueError:
            raise forms.ValidationError("Dati non validi.")
        if len(ids) > 4:  # max 4 + te stesso = 5
            raise forms.ValidationError("Puoi aggiungere al massimo 4 membri.")
        return User.objects.filter(pk__in=ids, teams__isnull=True)

class ExitTeamForm(forms.Form):
    
    pass


class InviteMemberForm(forms.Form):
    """Invita un singolo utente a un team già esistente (crea un invito pending)."""

    user_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, team=None, **kwargs):
        self.team = team
        super().__init__(*args, **kwargs)

    def clean_user_id(self):
        user_id = self.cleaned_data['user_id']
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise forms.ValidationError("Utente non valido.")

        if self.team is None:
            raise forms.ValidationError("Team non valido.")

        if self.team.is_full:
            raise forms.ValidationError("Il team ha già raggiunto il numero massimo di membri.")

        if self.team.members.filter(pk=user.pk).exists():
            raise forms.ValidationError("Questo utente è già nel team.")

        if TeamInvite.objects.filter(team=self.team, invited_user=user, status=TeamInvite.STATUS_PENDING).exists():
            raise forms.ValidationError("Esiste già un invito in attesa per questo utente.")

        return user

class EditTeamForm(forms.ModelForm):
    new_leader = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label='Trasferisci leadership a',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Team
        fields = ['name', 'description', 'icon', 'is_open']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'icon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_open': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['new_leader'].queryset = self.instance.members.exclude(pk=self.instance.leader_id)
            self.fields['new_leader'].empty_label = 'Mantieni leadership attuale'
