from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, FormView, DeleteView, UpdateView
from django.urls import reverse_lazy
from .forms import UserCreationForm, UserLoginForm, EditProfileForm, CSVImportForm
from .models import User
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import logout
from teams.models import Team
from .csv_import import import_teams_csv, import_match_results_csv, import_users_csv




from .models import User



# Create your views here.
class HomeView(LoginRequiredMixin,TemplateView): 
    template_name = 'home/index.html'
    login_url = '/login/'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.request.user.teams.first()
        return  context
   

class SignUpView(FormView):
    template_name = 'user/signup.html'
    form_class = UserCreationForm
    ## le due password devono essere uguali
    def form_valid(self, form):
        if form.cleaned_data['password1'] != form.cleaned_data['password2']:
            form.add_error('password2', 'Le password non coincidono')
            return self.form_invalid(form)

        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'],
            paese=form.cleaned_data.get('paese', ''),
            phone_number=form.cleaned_data.get('phone_number', ''),
    
        )
        login(self.request, user)
        return super().form_valid(form)
    def get_success_url(self):
        return '/'

class LogoutView(FormView):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('/login/')

class EditProfileView(LoginRequiredMixin, FormView):
    template_name = 'user/edit-profile.html'
    login_url = '/login/'
    form_class = EditProfileForm
    def form_valid(self, form):
        user = self.request.user
        if form.cleaned_data['username']:
            user.username = form.cleaned_data['username']
        if form.cleaned_data['password']:
            user.set_password(form.cleaned_data['password'])
        if form.cleaned_data['paese']:
            user.paese = form.cleaned_data['paese']
        if form.cleaned_data['phone_number']:
            user.phone_number = form.cleaned_data['phone_number']
        if form.cleaned_data['profile_picture']:
            user.profile_picture = form.cleaned_data['profile_picture']
        if form.cleaned_data['steam_url']:
            user.steam_url = form.cleaned_data['steam_url']
        if form.cleaned_data['email']:
            user.email = form.cleaned_data['email']
        user.save()
        return redirect('/')

class LoginView(FormView):
    template_name = 'user/login.html'
    form_class = UserLoginForm

    def form_valid(self, form):

        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )

        if user:
            login(self.request, user)
            return redirect('/')
        
        # errore di login
        form.add_error(None, "Username o password non corretti")

        return self.form_invalid(form)

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'user/profile.html'
    login_url = '/login/'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['country_flag'] = f"{self.request.user.paese.lower()}" if self.request.user.paese else None
        return context

class DeleteAccountView(LoginRequiredMixin, TemplateView):
    template_name = 'user/delete_account.html'
    login_url = '/login/'

    def post(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        logout(request)
        return redirect('/login/')
class CSVImportView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Import massivo via CSV, accessibile solo agli admin (is_staff).
    Non fa redirect dopo il submit: rimane sulla stessa pagina mostrando
    il riepilogo (righe create + eventuali errori riga per riga)."""
    template_name = 'user/csv_import.html'
    form_class = CSVImportForm
    login_url = '/login/'
 
    def test_func(self):
        return self.request.user.is_staff
 
    def form_valid(self, form):
        import_type = form.cleaned_data['import_type']
        csv_file = form.cleaned_data['csv_file']
 
        if import_type == 'teams':
            result = import_teams_csv(csv_file)
        elif import_type == 'match_results':
            result = import_match_results_csv(csv_file)
        else:
            result = import_users_csv(csv_file)
 
        context = self.get_context_data(form=self.form_class(), result=result)
        return self.render_to_response(context)




