from django.contrib.auth.views import LoginView

from .forms import CustomAuthenticationForm


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)

        # Remember me
        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)

        return response