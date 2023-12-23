from django.shortcuts import render

from login.forms import LoginForm


# Create your views here.
def login_view(request):
    form = LoginForm()
    return render(request, 'login.html', {'form': form})
