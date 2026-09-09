from rest_framework.permissions import BasePermission


class IsConversationOwnerOrManager(BasePermission):
    """
    Suhbatga ruxsat:
    - Xodim (employee) faqat o'zining suhbatini ko'ra oladi.
    - Menejer (manager) o'zining tenant'idagi barcha suhbatlarni ko'ra oladi.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
            
        role = getattr(request.user, "role", "employee")
        if role == "employee":
            return obj.user_id == request.user.id
            
        return obj.tenant_id == request.user.tenant_id
