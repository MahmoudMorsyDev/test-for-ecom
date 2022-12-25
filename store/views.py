from django.shortcuts import render, redirect
from .models import *
from django.http import JsonResponse
import json
import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .utils import cookieCart, cartData, guestOrder
from .forms import User, RegForm
# Create your views here.

def loginPage(request):
    page='login'
    if request.user.is_authenticated:
        return redirect('store')
    if request.method == "POST":
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "user does not exist")  

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('store')
        else:
            messages.error(request, "username or password does not exist")

    context = {'page':page}
    return render(request, 'store/login-register.html', context)

def registerPage(request):
    form = RegForm
    if request.method == "POST":
        form = RegForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            cutomer = Customer.objects.create(
                user=user,
                name = user.username,
                email= user.email,

            )
            login(request, user)
            
            return redirect('store')
        else:
            messages.error(request, 'an error occuired during registration')

    context={"form":form}
    return render(request, 'store/login-register.html', context)

def store(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    products = Product.objects.all()
    context={'products':products, 'cartItems':cartItems} 
    return render(request, 'store/store.html', context)


def cart(request):
    # so if the user is logged in we get his customer name, then we find his order if existed
    #otherwise we create it
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    context={'items':items, 'order':order, 'cartItems':cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    context = {'items':items, 'order':order,'cartItems':cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data ['action']
    print('Action:', action)
    print('Product:', productId)
    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
    if action == 'add':
        orderItem.quantity = (orderItem.quantity +1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity -1)
    orderItem.save()
    if orderItem.quantity <= 0:
        orderItem.delete()        

    return JsonResponse('item was added', safe=False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        
    else:
        customer, order = guestOrder(request, data)
    total = float(data['form']['total'])
    order.transaction_id = transaction_id
    if total == order.get_cart_total:
        order.complete = True
    order.save()          
    if order.shipping == True:
            ShippingAddress.objects.create(
                customer=customer,
                order = order,
                address = data['shipping']['address'],
                city= data['shipping']['city'],
                state = data['shipping']['state'],
                zipcode = data['shipping']['zipcode'],
            )  
    return JsonResponse('Payemnt submitted..', safe=False)

def logoutUser(request):
    logout(request)
    return redirect('store')