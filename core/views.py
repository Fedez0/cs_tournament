from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, FormView
from .forms import UserCreationForm, UserLoginForm, EditProfileForm
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from teams.models import Team


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




