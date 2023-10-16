"""from django.http import HttpResponse
from .models import Category, Product, Client, Order
from django.shortcuts import get_object_or_404


# Create your views here.

def index(request):
    cat_list = Category.objects.all().order_by('id')[:10]
    product_list = Product.objects.all().order_by('-price')[:5]
    response = HttpResponse()
    heading1 = '<p>' + 'List of categories: ' + '</p>'
    response.write(heading1)

    for category in cat_list:
        para = '<p>' + str(category.id) + ': ' + str(category) + '</p>'
        response.write(para)
    response.write(content='<br>')
    heading2 = '<p>' + 'List of products: ' + '</p>'
    response.write(heading2)
    for product in product_list:
        para = '<p>' + str(product.id) + ': ' + str(product) + '</p>'
        response.write(para)
    return response


def about(request):
    return HttpResponse("This is an Online Store APP")


def detail(request, cat_no):
    category = get_object_or_404(Category, pk=cat_no)
    products = Product.objects.filter(category=category)
    detail_response = HttpResponse()
    heading = '<p>' + 'Warehouse location - ' + category.warehouse + '</p>'
    heading += '<p>' + 'List of products for the category:' + '</p>'
    detail_response.write(heading)
    for product in products:
        para = '<p>' + str(product.id) + ': ' + str(product) + '</p>'
        detail_response.write(para)
    return detail_response
"""
import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Category, Product, Client, Order
from datetime import datetime, timezone
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect, HttpResponseRedirect
from django.urls import reverse
from .models import Category, Product, Client, Order
from .forms import OrderForm, InterestForm, LoginForm, RegisterForm, Password_ResetForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf.global_settings import EMAIL_HOST_USER
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail, BadHeaderError
from django.utils import timezone
from django.contrib.auth.models import User
import hashlib
import random
import string
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .models import Category, Product, Client, Order
from datetime import datetime

# Create your views here.


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('myapp:login'))


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                current_time = datetime.now()
                request.session['last_login'] = json.dumps(current_time, default=str)
                request.session.set_expiry(3600)
                print(request.POST['from_orders'])
                if request.POST['from_orders']:
                    return redirect('/myapp/myorders/')
                return redirect('/myapp/')
            else:
                return HttpResponse('Your account is disabled.')
        else:
            return HttpResponse('Invalid login details.')
    else:
        if request.user.is_authenticated:
            return redirect('/myorders/')
        return render(request, 'myapp/login.html', {'LoginForm': LoginForm})


def index(request):
    cat_list = Category.objects.all().order_by('id')[:10]
    msg = ""
    last_login = "You are logged out"
    format_data = '"%Y-%m-%d %H:%M:%S.%f"'
    if request.session.get('last_login', False):
        last_login = datetime.strptime(request.session.get('last_login'), format_data)
        time = datetime.now() - last_login
        if time.total_seconds() > 3600:
            last_login = "Your last login was more than one hour ago"
            logout(request)
    return render(request, 'myapp/index.html', {'cat_list': cat_list, 'last_login': last_login, 'user': request.user})


def about(request):
    # return HttpResponse("This is an Online Store APP")
    # return render(request, 'myapp/about0.html')
    # return render(request, 'myapp/about.html')

    if 'about_visits' in request.COOKIES:
        count_visited = int(request.COOKIES['about_visits'])
        response = render(request, 'myapp/about.html', {'no_of_times_visited': count_visited + 1})
        response.set_cookie('about_visits', count_visited + 1, max_age=300)
    else:
        response = render(request, 'myapp/about.html', {'no_of_times_visited': 1})
        response.set_cookie('about_visits', 1)
    return response


def detail(request, cat_no):
    category = get_object_or_404(Category, pk=cat_no)
    products = Product.objects.filter(category=category)
    # return render(request, 'myapp/detail0.html', {'category': category, 'products': products})
    return render(request, 'myapp/detail.html', {'category': category, 'products': products})
    # detail_response = HttpResponse()
    # heading = '<p>' + 'Warehouse location - ' + category.warehouse + '</p>'
    # heading += '<p>' + 'List of products for the category:' + '</p>'
    # detail_response.write(heading)
    #
    # for product in products:
    #     para = '<p>' + str(product.id) + ': ' + str(product) + '</p>'
    #     detail_response.write(para)
    # return detail_response


def products(request):
    prodlist = Product.objects.all().order_by('id')[:10]
    return render(request, 'myapp/products.html', {'prodlist': prodlist})


def place_order(request):
    msg = ''
    prodlist = Product.objects.all()
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            product_name = form.cleaned_data['product']
            order = form.save(commit=False)
            if order.num_units <= order.product.stock:
                order.save()
                product = Product.objects.get(name=product_name)
                product.stock = product.stock - order.num_units
                product.save()
                msg = 'Your order has been placed successfully.'
            else:
                msg = 'We do not have sufficient stock to fill your order !!!'
                return render(request, 'myapp/order_response.html', {'msg': msg})
    else:
        form = OrderForm()
    return render(request, 'myapp/placeorder.html', {'form': form, 'msg': msg, 'prodlist': prodlist})


def productdetail(request, prod_id):
    try:
        msg = ''
        product = Product.objects.get(id=prod_id)
        # product = get_object_or_404(Product, pk=prod_id)
        if request.method == 'GET':
            form = InterestForm()
        elif request.method == 'POST':
            form = InterestForm(request.POST)
            if form.is_valid():
                interested = form.cleaned_data['interested']
                print("Interested: ", interested)
                if int(interested) == 1:
                    product.interested += 1
                    product.save()
                    print('form is valid')
                    return redirect(reverse('myapp:index'))
        # else:
        #     form = InterestForm()
        return render(request, 'myapp/productdetail.html', {'form': form, 'msg': msg, 'product': product})
    except Product.DoesNotExist:
        msg = 'The requested product does not exist. Please provide correct product id !!!'
        return render(request, 'myapp/productdetail.html', {'msg': msg})


def myorders(request):
    if request.user.is_authenticated:
        try:
            user = request.user
            print(user)
            client = Client.objects.get(username=user.username)
            orders = Order.objects.filter(client=client)
            msg = f'Orders placed by {client} :-'
            if orders.count() == 0:
                msg = 'Client has not placed any orders'
            return render(request, 'myapp/myorders.html', {'orders': orders, 'msg': msg})
        except Client.DoesNotExist:
            msg = 'You are not a registered client'
            return render(request, 'myapp/myorders.html', {'msg': msg})
    else:
        return render(request, 'myapp/login.html', {'from_orders':
                                                   True})


def user_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            return redirect("myapp:login")
        else:
            print('form invalid')
    else:
        form = RegisterForm()
    return render(request=request, template_name="myapp/register.html", context={"register_form": form})


def password_reset(request):
    if request.method == 'POST':
        email = request.POST['email']
        user = User.objects.filter(email=email)
        print(user)
        if user:
            user = user[0]
            new_password = generate_password()
            user.set_password(new_password)
            user.save()

            print(new_password)

            # Email settings
            subject = "New Password"
            email_template_name = "myapp/password_reset.txt"
            c = {
                "email": user.email,
                'domain': '127.0.0.1:8000',
                'site_name': 'Website',
                "user": user,
                'protocol': 'http',
                'new_password': new_password,
            }
            email = render_to_string(email_template_name, c)
            try:
                send_mail(subject, email, EMAIL_HOST_USER, [user.email], fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')

            return redirect('myapp:password_reset_done', 1)
        else:
            return redirect('myapp:password_reset_done', 0)
    else:
        if request.user.is_authenticated:
            return redirect('myorders')
        password_reset_form = Password_ResetForm()
        return render(request, 'myapp/password_reset.html', {'form': password_reset_form})


def generate_password():
    characters = list(string.ascii_letters + string.digits + "!@#$%^&*()")
    password_length = 8
    random.shuffle(characters)

    password = []
    for i in range(password_length):
        password.append(random.choice(characters))

    random.shuffle(password)
    return "".join(password)


def password_reset_done(request, done):
    return render(request, 'myapp/password_reset_done.html', {'done': done})

