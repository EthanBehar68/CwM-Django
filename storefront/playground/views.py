from django.contrib.contenttypes.models import ContentType
from django.forms import DecimalField
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.db import transaction, connection
from django.db.models import Q, F, Value, Func, ExpressionWrapper
from django.db.models.aggregates import Count, Max, Min, Avg, Sum
from django.db.models.functions import Concat

from store.models import Cart, CartItem, Collection, Customer, Order, OrderItem, Product
from tags.models import TaggedItem

# all() returns a query set object
# queryset = Product.objects.all()

# get returns an object
# pk == primary key - wild card for any primary key
# product = Product.objects.get(pk=1)

# query_sets are lazy - scenarios that trigger the sql
# Triggers Query 1
# for product in query_set:
#     print(product)

# Triggers Query 2
# list(query_set)

# Trigger Query 3
# query_set[0:5]

# Makes whole function a transaction
# @transaction.atomic()
def say_hello(request):
    # Keyword/value
    # queryset = Product.objects.filter(unit_price__gt=20)
    # queryset = Product.objects.filter(unit_price__range=(20, 30))
    # queryset = Product.objects.filter(collection__id__range=(1, 2, 3))
    # queryset = Product.objects.filter(title__icontains='coffee')
    # queryset = Product.objects.filter(last_update__year=2021)
    # queryset = Product.objects.filter(description__isnull=True)
    # queryset = Customer.objects.filter(email__icontains='.com')
    # queryset = Collection.objects.filter(featured_product__isnull=True)
    # queryset = Product.objects.filter(inventory__lt=10)
    # queryset = Order.objects.filter(customer__id=1)
    # queryset = OrderItem.objects.filter(product__collection__id=3)

    # Need to change html for non-Product calls

    # And operation
    queryset = Product.objects.filter(inventory__lt=10).filter(unit_price__lt=20)
    # Or operation (can use & for and but just use above)
    # ~ <- is negation
    queryset = Product.objects.filter(Q(inventory__lt=10) | Q(unit_price__lt=20))

    # F is for Field
    queryset = Product.objects.filter(inventory=F('unit_price'))
    queryset = Product.objects.filter(inventory=F('collection__id'))

    # Descending
    queryset = Product.objects.order_by('-title')
    # Ascending
    queryset = Product.objects.order_by('title')
    # Double Sorting
    queryset = Product.objects.order_by('unit_price', '-title')

    queryset = Product.objects.order_by('unit_price', '-title').reverse()
    
    queryset = Product.objects.filter(collection__id=3).order_by('unit_price')

    # Returns query set but we access just first element so we get a product object
    product = Product.objects.order_by('unit_price')[0]
    # Kinda the same as above (latest will get reverse of earliest)
    # Returns a product object
    product = Product.objects.earliest('unit_price')

    # Limit results
    # 0 - 4
    queryset = Product.objects.all()[:5]
    # 5 - 9
    queryset = Product.objects.all()[5:10]

    # Limiting fields
    # dictionary result
    queryset = Product.objects.values('id', 'title', 'collection__title')
    # tuple result
    queryset = Product.objects.values_list('id', 'title', 'collection__title')

    
    # queryset = OrderItem.objects.values('product_id')
    # queryset = OrderItem.objects.values('product_id').distinct()
    queryset = Product.objects.filter(
        id__in=OrderItem.objects.values('product_id')
        .distinct()).order_by('title')

    # Deferring Fields
    # Dangerous methods - causes queries under the hood
    queryset = Product.objects.only('id', 'title')
    queryset = Product.objects.defer('description')

    # Selecting Related Objects
    # Pre-loads collection field and sorta handles issue from above
    # Creates inner join between products and collection
    # Used when 1 instance (Collection)
    queryset = Product.objects.select_related('collection').all()
    # Used when many instance (Promotions)
    queryset = Product.objects.prefetch_related('promotions').all()
    # Can use together - order shouldn't matter
    queryset = Product.objects.prefetch_related('promotions').select_related('collection')

    queryset = Order.objects.select_related(
        'customer').prefetch_related(
            'orderitem_set__product').order_by( '-placed_at')[:5]

    # Aggrgating Objects
    # Count all objects with id (ie all objects) using a null field will exclude nulls
    result = Product.objects.aggregate(counta=Count('id'), min_price=Min('unit_price'))

    # How many orders do we have?
    result = Order.objects.aggregate(count=Count('id'))
    # How many units of product 1 have we sold?
    result = OrderItem.objects.filter(product__id=1).aggregate(unit_sold=Sum('quantity'))
    # How many orders has customer 1 placed?
    result = Order.objects.filter(customer__id=1).aggregate(count=Count('id'))
    # What is the min, max, and avg price of products in collection 1?
    result = Product.objects.filter(collection__id=3).aggregate(
        min_price=Min('unit_price'), 
        max_price=Max('unit_price'), 
        avg_price=Avg('unit_price'))

    # Annotating Objects
    queryset = Customer.objects.annotate(is_new=Value(True))
    queryset = Customer.objects.annotate(new_id=F('id') + 1) # <- can do computation

    # Database Functions
    queryset = Customer.objects.annotate(
        full_name=Func(F('first_name'), Value(' '), F('last_name'), function='CONCAT'))
    # Another way - same as above
    queryset = Customer.objects.annotate(
        full_name=Concat('first_name', Value(' '), 'last_name'))

    # Grouping Data
    queryset = Customer.objects.annotate(
        orders_count=Count('order')
    )

    # Working with Expression Wrappers (Value, F, Func, Aggregate, ExpressionWrapper)
    discounted_price = ExpressionWrapper(F('unit_price') * 0.14, output_field=DecimalField())
    queryset = Product.objects.annotate(
        discounted_price=discounted_price
    )

    # Customer and their last order ID
    queryset = Customer.objects.annotate(last_order_id=Max('order__id'))
    # Collections and count of their products
    queryset = Collection.objects.annotate(products_count=Count('product'))
    # Customers with more than 5 orders
    queryset = Customer.objects.annotate(order_count=Count('order')).filter(order_count__gt=5)
    # Customers and the total amount they've spend
    queryset = Customer.objects.annotate(
        total_spent=Sum(
            F('order__orderitem__unit_price') * 
            F('order__orderitem__quantity')
        )
    )
    # Top 5 best-selling products and their total sales
    queryset = Product.objects.annotate(
        total_sales=Sum(
            F('orderitem__unit_price') *
            F('orderitem__quantity')
        )
    ).order_by('-total_sales')[:5]

    # Querying Generic Relationships
    content_type_instance = ContentType.objects.get_for_model(Product)
    # Product id 1
    # \ = line continuation for python
    content_queryset = TaggedItem.objects \
        .select_related('tag') \
        .filter(content_type=content_type_instance, object_id=1)

    # Customer Manager
    # See TaggedItem file
    content_queryset = TaggedItem.objects.get_tags_for(Product, 1)

    #QuerySet Cache
    queryset = Product.objects.all()
    list(queryset) # gets DB now
    queryset[0] # this won't be cached - only caches when full queryset is used
    list(queryset) # read result from cache
    queryset[0] # read result from cache

    # Creating Objects
    collection = Collection()
    collection.title = 'Video Games'
    collection.featured_product = Product(pk=1)
    # collection.featured_product_id = 1 same as above
    
    # No intelli-sense with this approach
    # Keyword arguments don't get updated when using renaming functionality (F2 usage)
    collection2 = Collection(title='Video games2')
    # Same CONs as above
    # collection = Collections.objects.create(...)

    # Treated as insert b/c no id is supplied in objects
    # collection.save()
    # collection2.save()

    # Updateing Objects
    collection = Collection(pk=11)
    collection.title = 'Video Games Updated'
    collection.featured_product = None
    # collection.save()

    # Preserve data already there
    # If we use new object Django will overwrite data with nulls where we didn't set new data
    # ie title would = ''
    collection = Collection.objects.get(pk=11)
    collection.featured_product = None
    # collection.save()

    # Deleting objects
    # Single
    collection = Collection(pk=11)
    collection.delete()

    # Multiple
    Collection.objects.filter(id__gt=5).delete()

    # Create cart n save
    cart = Cart()
    cart.save()

    # Cart CartItem set to cart above and save
    item1 = CartItem()
    item1.cart = cart
    item1.product_id = 1
    item1.quantity = 1
    item1.save()

    # Update cart
    item1 = CartItem.objects.get(pk=1)
    item1.quantity = 2
    item1.save

    # Delete cart also deletes CartItem b/c of CASCADE option
    cart = Cart(pk=1)
    cart.delete()

    # Transactions
    with transaction.atomic():
        order = Order()
        order.customer_id = 1
        order.save()

        item = OrderItem()
        item.order = order
        item.product_id = 1 # django-created
        item.quantity = 1
        item.unit_price = 10
        item.save()

    # Raw SQL Query
    # This is a raw query set and doesn't have filter and other methods
    # Use this approach when making complex queries and SQL could be cleaner
    rawset = Product.objects.raw('SELECT * FROM store_product')
    rawset = Product.objects.raw('SELECT id, title FROM store_product')

    # Raw SQL without Model Objects
    with connection.cursor() as cursor:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM store_product')
        # cursor.callproc('get_customers_example', [1, 2, 3]) <- calls stored procedure
        # cursor.close() <- with handles the close! ALWAYS CLOSE!


    return render(request, 'hello.html', {'name': 'Mosh', 'result': result, 'orders': list(queryset)})
