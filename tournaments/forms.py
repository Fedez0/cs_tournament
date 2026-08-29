from .models import Tournament
import django.forms as forms 
import datetime
from django.utils import timezone
class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'date', 'location','prize', 'max_teams', 'icon', 'banner']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'prize': forms.TextInput(attrs={'class': 'form-control'}),
            'max_teams': forms.NumberInput(attrs={'class': 'form-control'}),
            'icon': forms.FileInput(attrs={'class': 'form-control'}),
            'banner': forms.FileInput(attrs={'class': 'form-control'}),
        }
    def clean_max_teams(self):
        max_teams = self.cleaned_data['max_teams']

        if max_teams < 2 or (max_teams & (max_teams - 1)) != 0:
            raise forms.ValidationError("Il numero massimo di squadre deve essere una potenza di 2 (4, 8, 16...).")
        
        if max_teams < 2:
            raise forms.ValidationError("Il numero massimo di squadre deve essere almeno 2.")
        return max_teams
    def clean_name(self):

        name = self.cleaned_data['name']

        if Tournament.objects.filter(name__iexact=name).exists():

            raise forms.ValidationError(

                "Esiste già un torneo con questo nome."

            )

        return name
    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.now().date():
            raise forms.ValidationError("La data del torneo non può essere nel passato.")
        return date
    def clean_prize(self):
        prize = self.cleaned_data['prize']
        if not prize:
            raise forms.ValidationError("Il premio del torneo non può essere vuoto.")
        return prize

    
class TournamentEdit(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'date', 'location','prize', 'max_teams', 'icon', 'banner']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'prize': forms.TextInput(attrs={'class': 'form-control'}),
            'max_teams': forms.NumberInput(attrs={'class': 'form-control'}),
            'icon': forms.FileInput(attrs={'class': 'form-control'}),
            'banner': forms.FileInput(attrs={'class': 'form-control'}),
            
        }
    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.now().date():
            raise forms.ValidationError("La data del torneo non può essere nel passato.")
        return date

    def clean_name(self):
        name = self.cleaned_data['name']
        if Tournament.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "Esiste già un torneo con questo nome."
            )
        return name
    def clean_max_teams(self):
        max_teams = self.cleaned_data['max_teams']
        ## controlla se il numero di iscritte è maggiore del numero massimo di squadre, se si allora non permette di modificare il numero massimo di squadre
        if max_teams < 2 or (max_teams & (max_teams - 1)) != 0:
                    raise forms.ValidationError("Il numero massimo di squadre deve essere una potenza di 2 (4, 8, 16...).")
                
        if self.instance.teams.count() > max_teams:
            raise forms.ValidationError("Il numero massimo di squadre non può essere inferiore al numero di squadre già iscritte.")
        if max_teams < 2:
            raise forms.ValidationError("Il numero massimo di squadre deve essere almeno 2.")
        return max_teams
class MatchResultForm(forms.Form):
    score_team1 = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    score_team2 = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
