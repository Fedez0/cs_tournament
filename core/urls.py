from django.urls import path
from .views import (
    HomeView,
    SignUpView,
    LoginView,
    LogoutView,
    EditProfileView,
    ProfileView,
    DeleteAccountView,
    CSVImportView,
    send_test_email,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('edit-profile/', EditProfileView.as_view(), name='edit_profile'),
    path('profile/', ProfileView.as_view(), name='view_profile'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('import-csv/', CSVImportView.as_view(), name='csv_import'),
    path('send-test-email/', send_test_email, name='send_test_email'),
]
