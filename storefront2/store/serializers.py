from decimal import Decimal
from rest_framework import serializers
from .models import Product, Collection

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'products_count']
    products_count = serializers.IntegerField()

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'slug', 'inventory', 'unit_price', 'price_with_tax', 'collection']
    # id = serializers.IntegerField()
    # title = serializers.CharField(max_length=255)
    # price = serializers.DecimalField(max_digits=6, decimal_places=2, source='unit_price')
    price_with_tax = serializers.SerializerMethodField(method_name='calculate_tax')
    # Hyperlinks
    # Overrides collection in Meta.fields
    # collection = serializers.HyperlinkedRelatedField(
    #     queryset = Collection.objects.all(),
    #     view_name = 'collection-detail'
    # )
    #Representing Relationships
        # Collection Object
        # collection = CollectionSerializer()
        # Just String
        # collection = serializers.StringRelatedField()
        # Just id
        # collection = serializers.PrimaryKeyRelatedField(
        #     queryset=Collection.objects.all()
        # )


    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1) 

    # Examples for overriding creating and updating objects
    # def create(self, validated_data):
    #     product = Product(**validated_data)
    #     # Other data goes here
    #     # product.other = 1
    #     product.save()
    #     return product

    # def update(self, instance, validated_data):
    #     instance.unit_price = validated_data.get('unit_price')
    #     instance.save()
    #     return instance

    # Toy example of custom validation
    # def validate(self, data):
    #     if data['password'] != data['confirm_password']:
    #         return serializers.ValidationError('Passwords do not match.')
    #     return data
