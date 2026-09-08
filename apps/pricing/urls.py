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
router.register("calc-rules", CalcRuleViewSet, basename="calc-rule")
router.register("services", ServicePriceViewSet, basename="service-price")
router.register("discount-tiers", DiscountTierViewSet, basename="discount-tier")
router.register("discount-policy", DiscountPolicyViewSet, basename="discount-policy")
router.register("order-defaults", OrderDefaultsViewSet, basename="order-defaults")
router.register("model-pricings", ModelPricingViewSet, basename="model-pricing")

calc_rule_root = CalcRuleViewSet.as_view({"get": "list", "patch": "partial_update"})
service_price_root = ServicePriceViewSet.as_view({"get": "list", "patch": "partial_update"})
discount_policy_root = DiscountPolicyViewSet.as_view({"get": "retrieve", "patch": "partial_update"})
order_defaults_root = OrderDefaultsViewSet.as_view({"get": "retrieve", "patch": "partial_update"})

urlpatterns = [
    path("calc-rules/", calc_rule_root, name="calc-rule-root"),
    path("services/", service_price_root, name="service-price-root"),
    path("discount-policy/", discount_policy_root, name="discount-policy-root"),
    path("order-defaults/", order_defaults_root, name="order-defaults-root"),
    path("calc/preview/", calc_preview_view, name="calc-preview"),
    path("", include(router.urls)),
]
