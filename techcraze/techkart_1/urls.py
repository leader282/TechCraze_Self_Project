from django.contrib import admin
from django.urls import path, include
from .views import HomeView, ItemDetailView, OrderSummaryView, CheckoutView, PaymentView, SuccessView, CancelledView, add_to_cart, remove_from_cart, remove_single_item_from_cart, lView, pView, wView, tView, stripe_config, create_checkout_session, stripe_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('home', HomeView.as_view(), name='home'),
    path('l', lView, name='laptop'),
    path('p', pView, name='phone'),
    path('w', wView, name='watch'),
    path('t', tView, name='tv'),
    path('products/<slug>/', ItemDetailView.as_view(), name='product'),
    path('checkout', CheckoutView.as_view(), name='checkout'),
    path('add-to-cart/<slug>/', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart, name='remove_single_item_from_cart'),
    path('order-summary', OrderSummaryView.as_view(), name='order-summary'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('config/', stripe_config, name='stripe_config'),
    path('create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('success/', SuccessView.as_view()),
    path('cancelled/', CancelledView.as_view()),
    path('webhook/', stripe_webhook),
]