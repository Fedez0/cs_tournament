import resend
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import FormView, TemplateView

from .csv_import import import_match_results_csv, import_teams_csv, import_users_csv
from .forms import CSVImportForm, EditProfileForm, UserCreationForm, UserLoginForm
from .models import User


# Create your views here.
class HomeView(LoginRequiredMixin, TemplateView):
    """View for the home page."""

    template_name = "home/index.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        """Costruisce il contesto della home per l'utente autenticato.

        Args:
            **kwargs: Argomenti aggiuntivi forniti dalla vista generica.

        Returns:
            Il contesto con l'utente corrente e il suo primo team.
        """
        context = super().get_context_data(**kwargs)
        context["team"] = self.request.user.teams.first()
        context["user"] = self.request.user
        return context


@login_required(login_url="/login/")
@require_POST
def send_test_email(request):
    """Invia una email di prova e mostra l'esito all'utente.

    Args:
        request: Richiesta HTTP autenticata che avvia l'invio.

    Returns:
        Un redirect alla home con un messaggio di successo o di errore.
    """

    resend.api_key = settings.RESEND_API_KEY
    try:
        resend.Emails.send(
            {
                "from": "Acme <onboarding@germiniasi.com>",
                "to": ["germiniasi.federico@gmail.com"],
                "subject": "Test email CS Tournament",
                "html": "<p>Questa è una email di test da CS Tournament.</p>",
            }
        )
    except Exception:
        messages.error(request, "Invio email non riuscito.")
    else:
        messages.success(request, "Email di test inviata.")
    return redirect("home")


class SignUpView(FormView):
    """View for user signup."""

    template_name = "user/signup.html"
    form_class = UserCreationForm

    ## le due password devono essere uguali
    def form_valid(self, form):
        """Crea l'utente e avvia la sessione dopo una registrazione valida.

        Args:
            form: Modulo di registrazione già validato da Django.

        Returns:
            La risposta della vista dopo il salvataggio del nuovo utente.
        """
        if form.cleaned_data["password1"] != form.cleaned_data["password2"]:
            form.add_error("password2", "Le password non coincidono")
            return self.form_invalid(form)

        user = User.objects.create_user(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password1"],
            paese=form.cleaned_data.get("paese", ""),
            phone_number=form.cleaned_data.get("phone_number", ""),
        )
        login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        """Restituisce l'URL della pagina iniziale dopo la registrazione."""
        return "/"


class LogoutView(FormView):
    def get(self, request, *args, **kwargs):
        """Chiude la sessione corrente e reindirizza al login.

        Args:
            request: Richiesta HTTP della sessione da terminare.
            *args: Argomenti posizionali aggiuntivi della vista.
            **kwargs: Argomenti nominati aggiuntivi della vista.

        Returns:
            Un redirect alla pagina di login.
        """
        logout(request)
        return redirect("/login/")


class EditProfileView(LoginRequiredMixin, FormView):
    template_name = "user/edit-profile.html"
    login_url = "/login/"
    form_class = EditProfileForm

    def form_valid(self, form):
        """Aggiorna i dati del profilo con i valori presenti nel modulo.

        Args:
            form: Modulo del profilo già validato da Django.

        Returns:
            Un redirect alla home dopo il salvataggio.
        """
        user = self.request.user
        if form.cleaned_data["username"]:
            user.username = form.cleaned_data["username"]
        if form.cleaned_data["password"]:
            user.set_password(form.cleaned_data["password"])
        if form.cleaned_data["paese"]:
            user.paese = form.cleaned_data["paese"]
        if form.cleaned_data["phone_number"]:
            user.phone_number = form.cleaned_data["phone_number"]
        if form.cleaned_data["profile_picture"]:
            user.profile_picture = form.cleaned_data["profile_picture"]
        if form.cleaned_data["steam_url"]:
            user.steam_url = form.cleaned_data["steam_url"]
        if form.cleaned_data["email"]:
            user.email = form.cleaned_data["email"]
        user.save()
        return redirect("/")


class LoginView(FormView):
    template_name = "user/login.html"
    form_class = UserLoginForm

    def form_valid(self, form):
        """Autentica l'utente e apre la sessione se le credenziali sono valide.

        Args:
            form: Modulo di login già validato da Django.

        Returns:
            Un redirect alla home oppure il modulo con un errore di login.
        """

        user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])

        if user:
            login(self.request, user)
            return redirect("/")

        # errore di login
        form.add_error(None, "Username o password non corretti")

        return self.form_invalid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "user/profile.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        """Costruisce il contesto del profilo e il codice della bandiera.

        Args:
            **kwargs: Argomenti aggiuntivi forniti dalla vista generica.

        Returns:
            Il contesto con l'utente corrente e la bandiera del paese.
        """
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["country_flag"] = f"{self.request.user.paese.lower()}" if self.request.user.paese else None
        return context


class DeleteAccountView(LoginRequiredMixin, TemplateView):
    template_name = "user/delete_account.html"
    login_url = "/login/"

    def post(self, request, *args, **kwargs):
        """Elimina l'account corrente e termina la sessione.

        Args:
            request: Richiesta HTTP dell'utente da eliminare.
            *args: Argomenti posizionali aggiuntivi della vista.
            **kwargs: Argomenti nominati aggiuntivi della vista.

        Returns:
            Un redirect alla pagina di login.
        """
        user = request.user
        user.delete()
        logout(request)
        return redirect("/login/")


class CSVImportView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "user/csv_import.html"
    form_class = CSVImportForm
    login_url = "/login/"

    def test_func(self):
        """Verifica che l'utente corrente abbia privilegi di staff.

        Returns:
            `True` se l'utente è staff, altrimenti `False`.
        """
        return self.request.user.is_staff

    def form_valid(self, form):
        """Importa il file CSV usando il tipo selezionato nel modulo.

        Args:
            form: Modulo di importazione già validato da Django.

        Returns:
            La pagina di importazione con il risultato dell'operazione.
        """
        import_type = form.cleaned_data["import_type"]
        csv_file = form.cleaned_data["csv_file"]

        if import_type == "teams":
            result = import_teams_csv(csv_file)
        elif import_type == "match_results":
            result = import_match_results_csv(csv_file)
        else:
            result = import_users_csv(csv_file)

        context = self.get_context_data(form=self.form_class(), result=result)
        return self.render_to_response(context)
