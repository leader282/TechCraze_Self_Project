from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from .models import Item, Order, OrderItem, BillingAddress, Payment
from .forms import CheckoutForm
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import stripe
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse, HttpResponse

# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY


def product(request):
    context = {
        'items' : Item.objects.all()
    }
    return render(request, 'product-page.html', context)

def checkout(request):
    context = {
        'items' : Item.objects.all()
    }
    return render(request, 'checkout-page.html', context)

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item = item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user = request.user, ordered = False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug = item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated")
        else:
            messages.info(request, "Your order was added to the cart")
            order.items.add(order_item)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date = ordered_date)
        order.items.add(order_item)
        messages.info(request, "Your order was added to the cart")
    return(redirect('order-summary'))

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user = request.user, ordered = False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug = item.slug).exists():
            order_item = OrderItem.objects.filter(user=request.user, item=item, ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart")
            return(redirect('order-summary'))
        else:
            messages.info(request, "This item was not in your cart")
            return(redirect('product', slug=slug))
    else:
        messages.info(request, "You dont have an active order")
        return(redirect('product', slug=slug))

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user = request.user, ordered = False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug = item.slug).exists():
            order_item = OrderItem.objects.filter(user=request.user, item=item, ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
                messages.info(request, "This item quantity was updated")
            else:
                order.items.remove(order_item)
                messages.info(request, "This item was removed from your cart")
            return(redirect('order-summary'))
        else:
            messages.info(request, "This item was not in your cart")
            return(redirect('product', slug=slug))
    else:
        messages.info(request, "You dont have an active order")
        return(redirect('product', slug=slug))

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'http://localhost:8000/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            order = Order.objects.get(user=request.user, ordered=False)
            print(int(order.get_total()))
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=request.user.id if request.user.is_authenticated else None,
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='payment',
                line_items=[
                    {
                        'name': 'All items in your cart',
                        'quantity': 1,
                        'currency': 'inr',
                        'amount': str(int(order.get_total()*100)),
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        print("Payment was successful.")
        # TODO: run some custom code here

    return HttpResponse(status=200)

class HomeView(ListView):
    model = Item
    paginate_by = 4
    template_name = 'home-page.html'

def lView(request):
    result = Item.objects.filter(category='L')
    context = {
        'result': result
    }
    return render(request, 'category_page.html', context)

def pView(request):
    result = Item.objects.filter(category='P')
    context = {
        'result': result
    }
    return render(request, 'category_page.html', context)

    
def wView(request):
    result = Item.objects.filter(category='W')
    context = {
        'result': result
    }
    return render(request, 'category_page.html', context)
    

def tView(request):
    result = Item.objects.filter(category='T')
    context = {
        'result': result
    }
    return render(request, 'category_page.html', context)

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order,
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, 'You donot have an active order')
            return redirect('/')

class ItemDetailView(DetailView):
    model = Item
    template_name = 'product-page.html'

class CheckoutView(View):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            try:
                form = CheckoutForm()
                order = Order.objects.get(user=self.request.user, ordered=False)
                context = {
                    'form': form,
                    'object': order
                }
                return render(self.request, 'checkout-page.html', context)
            except:
                messages.error(self.request, 'You donot have an active order')
                return redirect('/')
        else:
            return redirect('accounts/login')
    
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data['street_address']
                apartment_address = form.cleaned_data['apartment_address']
                country = form.cleaned_data['country']
                zip = form.cleaned_data['zip']
                # same_shipping_address = form.cleaned_data('same_shipping_address')
                # save_info = form.cleaned_data('save_info')
                payment_option = form.cleaned_data['payment_option']
                billing_address = BillingAddress(
                    user = self.request.user,
                    street_address = street_address,
                    apartment_address = apartment_address,
                    country = country,
                    zip = zip
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_option == 'S':
                    return redirect('payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('payment', payment_option='paypal')
                else:
                    messages.warning(self.request, "No payment option selected")
                    return redirect('checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, 'You donot have an active order')
            return redirect('order-summary')

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered = False)
        context = {
            'order': order
        }
        return render(self.request, 'payment.html', context)
    
    def post(self, *args, **kwargs):
        return redirect('/')

class SuccessView(View):
    def get(self, *args, **kwargs):
        order_qs = Order.objects.filter(user = self.request.user, ordered = False)
        if order_qs.exists():
            order = order_qs[0]
            for order_item in OrderItem.objects.filter(user=self.request.user, ordered=False):
                order.items.remove(order_item)
            messages.success(self.request, 'Your order has been placed successfully.')
            return(redirect('/'))

class CancelledView(View):
    def get(self, *args, **kwargs):
        return render(self.request, 'cancelled.html')