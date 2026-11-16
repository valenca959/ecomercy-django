from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render

from authentication.forms import (
    AddressForm,
    ClientProfileForm,
    ClientSignupForm,
    SellerProfileForm,
    SellerSignupForm,
)
from authentication.models import CustomUser

MAX_LOGIN_FAILURES = 5
LOGIN_BLOCK_SECONDS = 15 * 60


class RateLimitedLoginView(auth_views.LoginView):
    """Login por sessão que bloqueia o IP após várias senhas erradas seguidas."""
    template_name = 'authentication/login.html'

    def _failures_key(self):
        return f"login-fail:{self.request.META.get('REMOTE_ADDR', 'desconhecido')}"

    def post(self, request, *args, **kwargs):
        if cache.get(self._failures_key(), 0) >= MAX_LOGIN_FAILURES:
            return HttpResponse(
                'Muitas tentativas de login. Tente novamente em alguns minutos.', status=429)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        cache.delete(self._failures_key())
        return super().form_valid(form)

    def form_invalid(self, form):
        key = self._failures_key()
        cache.add(key, 0, LOGIN_BLOCK_SECONDS)
        cache.incr(key)
        return super().form_invalid(form)


def _signup(request, form_class, title, kind):
    form = form_class(request.POST or None)
    address_form = AddressForm(request.POST or None, prefix='address')

    if request.method == 'POST':
        form_ok = form.is_valid()
        address_ok = address_form.is_valid()
        if form_ok and address_ok:
            with transaction.atomic():
                address = address_form.save()
                user = form.save(address=address)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Conta criada com sucesso!')
            return redirect('home')

    return render(request, 'authentication/signup.html', {
        'form': form,
        'address_form': address_form,
        'title': title,
        'kind': kind,
    })


def signup_client(request):
    return _signup(request, ClientSignupForm, 'Criar conta de cliente', 'cliente')


def signup_seller(request):
    return _signup(request, SellerSignupForm, 'Criar conta de vendedor', 'vendedor')


@login_required
def account(request):
    user = request.user
    form_class = SellerProfileForm if user.type == CustomUser.Type.SELLER else ClientProfileForm
    form = form_class(request.POST or None, instance=user)
    address_form = AddressForm(request.POST or None, instance=user.address, prefix='address')

    if request.method == 'POST':
        form_ok = form.is_valid()
        address_ok = address_form.is_valid()
        if form_ok and address_ok:
            with transaction.atomic():
                address = address_form.save()
                updated = form.save(commit=False)
                updated.address = address
                updated.save()
            messages.success(request, 'Dados atualizados.')
            return redirect('account')

    return render(request, 'authentication/account.html', {
        'form': form,
        'address_form': address_form,
    })
