import django.forms as forms
import pycountry
from .models import User


class UserCreationForm(forms.Form):
    model = User
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Conferma password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    def clean_username(self):

        username = self.cleaned_data['username']

        if User.objects.filter(username__iexact=username).exists():

            raise forms.ValidationError(

                "Esiste già un utente con questo username."

            )

        return username
    



class EditProfileForm(forms.Form):
    model = User
    COUNTRIES = [(country.alpha_2, country.name) for country in pycountry.countries]
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False

    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=False
    )
    paese = forms.ChoiceField(
        ## fai che di default sia italia, così se non lo selezionano è già impostato
        choices=COUNTRIES,
        initial='IT',
        
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'  # Bootstrap 5 (meglio di form-control)
        })
    )
    phone_number = forms.CharField(

    required=False,

    widget=forms.TextInput(attrs={

        'class': 'form-control',

        'inputmode': 'tel',

        'placeholder': '+39 333 123 4567'

    })

)
    profile_picture = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=False
    )
    steam_url = forms.URLField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )


class UserLoginForm(forms.Form):
    model = User

    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
class CSVImportForm(forms.Form):
    IMPORT_CHOICES = [
        ('teams', 'Squadre (name, description, leader_username)'),
        ('match_results', 'Risultati match (match_id, score_team1, score_team2)'),
        ('users', 'Utenti (username, password, email, paese, phone_number, steam_url)'),
    ]
    import_type = forms.ChoiceField(
        choices=IMPORT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    csv_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
 
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.lower().endswith('.csv'):
            raise forms.ValidationError("Il file deve essere un .csv")
        return csv_file
 