import pytest

from apps.chat.models import Conversation


@pytest.fixture
def conversation_factory(tenant):
    def make_conversation(user=None, title="Test Conv", **kwargs):
        from django.apps import apps
        from django.contrib.auth import get_user_model
        
        tenant_val = kwargs.pop("tenant", tenant)
        if tenant_val:
            Tenant = apps.get_model("accounts", "Tenant")
            if not Tenant.objects.filter(id=tenant_val.id).exists():
                tenant_val.save(force_insert=True)
                
        if not user:
            from apps.common.factories import EmployeeFactory
            user = EmployeeFactory.build(tenant=tenant_val)
            
        User = get_user_model()
        if not User.objects.filter(id=user.id).exists():
            user.tenant = tenant_val
            user.save(force_insert=True)
            
        kwargs.setdefault("session_id", str(__import__("uuid").uuid4()))
        return Conversation.objects.create(
            tenant=tenant_val,
            user=user,
            title=title,
            **kwargs
        )
    return make_conversation
