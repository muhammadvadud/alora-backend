from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.pricing.views import (
    CalcRuleViewSet,
    DiscountPolicyViewSet,
    DiscountTierViewSet,
    ModelPricingViewSet,
    OrderDefaultsViewSet,
    ServicePriceViewSet,
    calc_preview_view,
)

router = DefaultRouter()
router.register("discount-tiers", DiscountTierViewSet, basename="discount-tier")
router.register("model-pricings", ModelPricingViewSet, basename="model-pricing")

calc_rule_list = CalcRuleViewSet.as_view({"get": "list", "patch": "partial_update"})
calc_rule_detail = CalcRuleViewSet.as_view({"get": "retrieve"})
service_price_list = ServicePriceViewSet.as_view({"get": "list", "patch": "partial_update"})
service_price_detail = ServicePriceViewSet.as_view({"get": "retrieve"})
discount_policy_detail = DiscountPolicyViewSet.as_view({"get": "retrieve", "patch": "partial_update"})
order_defaults_detail = OrderDefaultsViewSet.as_view({"get": "retrieve", "patch": "partial_update"})

urlpatterns = [
    path("calc-rules/", calc_rule_list, name="calc-rule-root"),
    path("calc-rules/<str:key>/", calc_rule_detail, name="calc-rule-detail"),
    path("services/", service_price_list, name="service-price-root"),
    path("services/<str:key>/", service_price_detail, name="service-price-detail"),
    path("discount-policy/", discount_policy_detail, name="discount-policy-root"),
    path("order-defaults/", order_defaults_detail, name="order-defaults-root"),
    path("calc/preview/", calc_preview_view, name="calc-preview"),
    path("", include(router.urls)),
]