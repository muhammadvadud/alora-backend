import django_filters

from apps.catalog.models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.UUIDFilter(field_name="category_id")
    style = django_filters.CharFilter(field_name="style", lookup_expr="iexact")
    room = django_filters.CharFilter(method="filter_room")
    segment = django_filters.CharFilter(field_name="segment", lookup_expr="iexact")
    price_unit = django_filters.CharFilter(field_name="variants__price_unit", lookup_expr="iexact", distinct=True)
    min_price = django_filters.NumberFilter(field_name="variants__price", lookup_expr="gte", distinct=True)
    max_price = django_filters.NumberFilter(field_name="variants__price", lookup_expr="lte", distinct=True)
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Product
        fields = ["category", "style", "segment"]

    def filter_room(self, queryset, name, value):
        # recommended_rooms JSONField, filter contains value
        return queryset.filter(recommended_rooms__contains=[value])

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(name__icontains=value) | 
            Q(code__icontains=value) |
            Q(description__icontains=value) |
            Q(tags__contains=[value])
        ).distinct()
