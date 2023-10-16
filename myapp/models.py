from django.db import models
import datetime
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

import decimal


class Category(models.Model):
    name = models.CharField(max_length=200)
    warehouse = models.CharField(max_length=20, default='Windsor')

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=100, validators=[MinValueValidator(0),MaxValueValidator(1000)])
    available = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    interested = models.PositiveIntegerField(choices=[(1, 'Yes'), (0, 'No')], default=0)

    def refill(self):
        self.stock += 100
        self.save()

    def __str__(self):
        return self.name


class Client(User):
    PROVINCE_CHOICES = [('AB', 'Alberta'), ('MB', 'Manitoba'), ('ON', 'Ontario'), ('QC', 'Quebec'), ]
    company = models.CharField(max_length=50, blank=True)
    shipping_address = models.CharField(max_length=300, null=True, blank=True)
    city = models.CharField(max_length=20, default='Windsor')
    province = models.CharField(max_length=2, choices=PROVINCE_CHOICES, default='ON')
    interested_in = models.ManyToManyField(Category)
    clientImage = models.ImageField(upload_to='clientImages/', blank=True)

    def __str__(self):
        return self.first_name+' '+self.last_name


class Order(models.Model):
    product = models.ForeignKey(Product, related_name='orders', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, related_name='orders', on_delete=models.CASCADE)
    num_units = models.PositiveIntegerField()
    ORDER_STAGES = [(0, 'Order Cancelled'), (1, 'Order Placed'), (2, 'Order Shipped'), (3, 'Order Delivered'), ]
    order_status = models.IntegerField(choices=ORDER_STAGES, default=1)
    status_date = models.DateField(auto_now=True)

    def __str__(self):
        return self.product.__str__()+'--'+self.client.__str__()

    def total_cost(self):
        return self.product.price*self.num_units

