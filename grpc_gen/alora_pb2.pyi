from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ChatRequest(_message.Message):
    __slots__ = ("session_id", "user_id", "tenant_id", "message", "locale", "context")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    LOCALE_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    user_id: str
    tenant_id: str
    message: str
    locale: str
    context: _containers.ScalarMap[str, str]
    def __init__(self, session_id: _Optional[str] = ..., user_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., message: _Optional[str] = ..., locale: _Optional[str] = ..., context: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ChatEvent(_message.Message):
    __slots__ = ("kind", "content", "tool", "args", "result", "error", "usage", "products")
    KIND_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TOOL_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    USAGE_FIELD_NUMBER: _ClassVar[int]
    PRODUCTS_FIELD_NUMBER: _ClassVar[int]
    kind: str
    content: str
    tool: str
    args: str
    result: str
    error: str
    usage: Usage
    products: _containers.RepeatedCompositeFieldContainer[ProductRef]
    def __init__(self, kind: _Optional[str] = ..., content: _Optional[str] = ..., tool: _Optional[str] = ..., args: _Optional[str] = ..., result: _Optional[str] = ..., error: _Optional[str] = ..., usage: _Optional[_Union[Usage, _Mapping]] = ..., products: _Optional[_Iterable[_Union[ProductRef, _Mapping]]] = ...) -> None: ...

class Usage(_message.Message):
    __slots__ = ("provider", "model", "prompt_tokens", "completion_tokens", "cached_tokens", "reasoning_tokens", "stt_seconds", "tts_chars", "tool_calls_json", "latency_ms", "cost_usd", "cost_uzs")
    PROVIDER_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    PROMPT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    COMPLETION_TOKENS_FIELD_NUMBER: _ClassVar[int]
    CACHED_TOKENS_FIELD_NUMBER: _ClassVar[int]
    REASONING_TOKENS_FIELD_NUMBER: _ClassVar[int]
    STT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    TTS_CHARS_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALLS_JSON_FIELD_NUMBER: _ClassVar[int]
    LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    COST_USD_FIELD_NUMBER: _ClassVar[int]
    COST_UZS_FIELD_NUMBER: _ClassVar[int]
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    reasoning_tokens: int
    stt_seconds: float
    tts_chars: int
    tool_calls_json: str
    latency_ms: int
    cost_usd: float
    cost_uzs: float
    def __init__(self, provider: _Optional[str] = ..., model: _Optional[str] = ..., prompt_tokens: _Optional[int] = ..., completion_tokens: _Optional[int] = ..., cached_tokens: _Optional[int] = ..., reasoning_tokens: _Optional[int] = ..., stt_seconds: _Optional[float] = ..., tts_chars: _Optional[int] = ..., tool_calls_json: _Optional[str] = ..., latency_ms: _Optional[int] = ..., cost_usd: _Optional[float] = ..., cost_uzs: _Optional[float] = ...) -> None: ...

class ProductRef(_message.Message):
    __slots__ = ("variant_id", "product_name", "color_name", "color_hex", "price", "image_url", "sku")
    VARIANT_ID_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_NAME_FIELD_NUMBER: _ClassVar[int]
    COLOR_NAME_FIELD_NUMBER: _ClassVar[int]
    COLOR_HEX_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_URL_FIELD_NUMBER: _ClassVar[int]
    SKU_FIELD_NUMBER: _ClassVar[int]
    variant_id: str
    product_name: str
    color_name: str
    color_hex: str
    price: float
    image_url: str
    sku: str
    def __init__(self, variant_id: _Optional[str] = ..., product_name: _Optional[str] = ..., color_name: _Optional[str] = ..., color_hex: _Optional[str] = ..., price: _Optional[float] = ..., image_url: _Optional[str] = ..., sku: _Optional[str] = ...) -> None: ...

class VoiceChunk(_message.Message):
    __slots__ = ("audio_data", "format", "sample_rate", "chunk_sequence", "is_final")
    AUDIO_DATA_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    CHUNK_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    IS_FINAL_FIELD_NUMBER: _ClassVar[int]
    audio_data: bytes
    format: str
    sample_rate: int
    chunk_sequence: int
    is_final: bool
    def __init__(self, audio_data: _Optional[bytes] = ..., format: _Optional[str] = ..., sample_rate: _Optional[int] = ..., chunk_sequence: _Optional[int] = ..., is_final: _Optional[bool] = ...) -> None: ...

class VoiceEvent(_message.Message):
    __slots__ = ("kind", "content", "audio_data", "audio_format", "error", "chat_event")
    KIND_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    AUDIO_DATA_FIELD_NUMBER: _ClassVar[int]
    AUDIO_FORMAT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    CHAT_EVENT_FIELD_NUMBER: _ClassVar[int]
    kind: str
    content: str
    audio_data: bytes
    audio_format: str
    error: str
    chat_event: ChatEvent
    def __init__(self, kind: _Optional[str] = ..., content: _Optional[str] = ..., audio_data: _Optional[bytes] = ..., audio_format: _Optional[str] = ..., error: _Optional[str] = ..., chat_event: _Optional[_Union[ChatEvent, _Mapping]] = ...) -> None: ...

class ResetRequest(_message.Message):
    __slots__ = ("session_id", "user_id")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    user_id: str
    def __init__(self, session_id: _Optional[str] = ..., user_id: _Optional[str] = ...) -> None: ...

class ResetResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...

class HealthResponse(_message.Message):
    __slots__ = ("status", "version", "active_sessions", "last_error")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_SESSIONS_FIELD_NUMBER: _ClassVar[int]
    LAST_ERROR_FIELD_NUMBER: _ClassVar[int]
    status: str
    version: str
    active_sessions: int
    last_error: str
    def __init__(self, status: _Optional[str] = ..., version: _Optional[str] = ..., active_sessions: _Optional[int] = ..., last_error: _Optional[str] = ...) -> None: ...

class SnapshotRequest(_message.Message):
    __slots__ = ("page_token", "page_size")
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    page_token: str
    page_size: int
    def __init__(self, page_token: _Optional[str] = ..., page_size: _Optional[int] = ...) -> None: ...

class CatalogSnapshot(_message.Message):
    __slots__ = ("version", "products", "categories", "calc_rules", "knowledge_rules", "next_page_token", "total_count", "service_prices", "discount_tiers", "discount_policy", "order_defaults", "fasons", "prompt")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    PRODUCTS_FIELD_NUMBER: _ClassVar[int]
    CATEGORIES_FIELD_NUMBER: _ClassVar[int]
    CALC_RULES_FIELD_NUMBER: _ClassVar[int]
    KNOWLEDGE_RULES_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    SERVICE_PRICES_FIELD_NUMBER: _ClassVar[int]
    DISCOUNT_TIERS_FIELD_NUMBER: _ClassVar[int]
    DISCOUNT_POLICY_FIELD_NUMBER: _ClassVar[int]
    ORDER_DEFAULTS_FIELD_NUMBER: _ClassVar[int]
    FASONS_FIELD_NUMBER: _ClassVar[int]
    PROMPT_FIELD_NUMBER: _ClassVar[int]
    version: int
    products: _containers.RepeatedCompositeFieldContainer[CatalogProduct]
    categories: _containers.RepeatedCompositeFieldContainer[CatalogCategory]
    calc_rules: _containers.RepeatedCompositeFieldContainer[CatalogCalcRule]
    knowledge_rules: _containers.RepeatedCompositeFieldContainer[CatalogKnowledgeRule]
    next_page_token: str
    total_count: int
    service_prices: _containers.RepeatedCompositeFieldContainer[CatalogServicePrice]
    discount_tiers: _containers.RepeatedCompositeFieldContainer[CatalogDiscountTier]
    discount_policy: CatalogDiscountPolicy
    order_defaults: CatalogOrderDefaults
    fasons: _containers.RepeatedCompositeFieldContainer[CatalogFason]
    prompt: CatalogPrompt
    def __init__(self, version: _Optional[int] = ..., products: _Optional[_Iterable[_Union[CatalogProduct, _Mapping]]] = ..., categories: _Optional[_Iterable[_Union[CatalogCategory, _Mapping]]] = ..., calc_rules: _Optional[_Iterable[_Union[CatalogCalcRule, _Mapping]]] = ..., knowledge_rules: _Optional[_Iterable[_Union[CatalogKnowledgeRule, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ..., service_prices: _Optional[_Iterable[_Union[CatalogServicePrice, _Mapping]]] = ..., discount_tiers: _Optional[_Iterable[_Union[CatalogDiscountTier, _Mapping]]] = ..., discount_policy: _Optional[_Union[CatalogDiscountPolicy, _Mapping]] = ..., order_defaults: _Optional[_Union[CatalogOrderDefaults, _Mapping]] = ..., fasons: _Optional[_Iterable[_Union[CatalogFason, _Mapping]]] = ..., prompt: _Optional[_Union[CatalogPrompt, _Mapping]] = ...) -> None: ...

class CatalogServicePrice(_message.Message):
    __slots__ = ("key", "name", "price", "unit", "is_active")
    KEY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    key: str
    name: str
    price: str
    unit: str
    is_active: bool
    def __init__(self, key: _Optional[str] = ..., name: _Optional[str] = ..., price: _Optional[str] = ..., unit: _Optional[str] = ..., is_active: _Optional[bool] = ...) -> None: ...

class CatalogDiscountTier(_message.Message):
    __slots__ = ("id", "min_amount", "percent", "is_active")
    ID_FIELD_NUMBER: _ClassVar[int]
    MIN_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    PERCENT_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    id: str
    min_amount: str
    percent: str
    is_active: bool
    def __init__(self, id: _Optional[str] = ..., min_amount: _Optional[str] = ..., percent: _Optional[str] = ..., is_active: _Optional[bool] = ...) -> None: ...

class CatalogDiscountPolicy(_message.Message):
    __slots__ = ("manual_max_percent_employee", "manual_max_percent_manager", "stack_with_tier")
    MANUAL_MAX_PERCENT_EMPLOYEE_FIELD_NUMBER: _ClassVar[int]
    MANUAL_MAX_PERCENT_MANAGER_FIELD_NUMBER: _ClassVar[int]
    STACK_WITH_TIER_FIELD_NUMBER: _ClassVar[int]
    manual_max_percent_employee: str
    manual_max_percent_manager: str
    stack_with_tier: bool
    def __init__(self, manual_max_percent_employee: _Optional[str] = ..., manual_max_percent_manager: _Optional[str] = ..., stack_with_tier: _Optional[bool] = ...) -> None: ...

class CatalogOrderDefaults(_message.Message):
    __slots__ = ("prepayment_percent", "delivery_amount", "deadline_days")
    PREPAYMENT_PERCENT_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_DAYS_FIELD_NUMBER: _ClassVar[int]
    prepayment_percent: str
    delivery_amount: str
    deadline_days: int
    def __init__(self, prepayment_percent: _Optional[str] = ..., delivery_amount: _Optional[str] = ..., deadline_days: _Optional[int] = ...) -> None: ...

class CatalogFasonPart(_message.Message):
    __slots__ = ("id", "role", "name", "width_share", "height_share", "default_coef", "sort_order")
    ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    WIDTH_SHARE_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_SHARE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_COEF_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    id: str
    role: str
    name: str
    width_share: str
    height_share: str
    default_coef: str
    sort_order: int
    def __init__(self, id: _Optional[str] = ..., role: _Optional[str] = ..., name: _Optional[str] = ..., width_share: _Optional[str] = ..., height_share: _Optional[str] = ..., default_coef: _Optional[str] = ..., sort_order: _Optional[int] = ...) -> None: ...

class CatalogFasonAccessory(_message.Message):
    __slots__ = ("id", "category", "default_qty", "qty_formula")
    ID_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_QTY_FIELD_NUMBER: _ClassVar[int]
    QTY_FORMULA_FIELD_NUMBER: _ClassVar[int]
    id: str
    category: str
    default_qty: str
    qty_formula: str
    def __init__(self, id: _Optional[str] = ..., category: _Optional[str] = ..., default_qty: _Optional[str] = ..., qty_formula: _Optional[str] = ...) -> None: ...

class CatalogFason(_message.Message):
    __slots__ = ("id", "name", "style", "rooms", "image_url", "part_count", "parts", "accessories")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STYLE_FIELD_NUMBER: _ClassVar[int]
    ROOMS_FIELD_NUMBER: _ClassVar[int]
    IMAGE_URL_FIELD_NUMBER: _ClassVar[int]
    PART_COUNT_FIELD_NUMBER: _ClassVar[int]
    PARTS_FIELD_NUMBER: _ClassVar[int]
    ACCESSORIES_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    style: str
    rooms: _containers.RepeatedScalarFieldContainer[str]
    image_url: str
    part_count: int
    parts: _containers.RepeatedCompositeFieldContainer[CatalogFasonPart]
    accessories: _containers.RepeatedCompositeFieldContainer[CatalogFasonAccessory]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., style: _Optional[str] = ..., rooms: _Optional[_Iterable[str]] = ..., image_url: _Optional[str] = ..., part_count: _Optional[int] = ..., parts: _Optional[_Iterable[_Union[CatalogFasonPart, _Mapping]]] = ..., accessories: _Optional[_Iterable[_Union[CatalogFasonAccessory, _Mapping]]] = ...) -> None: ...

class CatalogPrompt(_message.Message):
    __slots__ = ("version", "content", "updated_at")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    version: int
    content: str
    updated_at: str
    def __init__(self, version: _Optional[int] = ..., content: _Optional[str] = ..., updated_at: _Optional[str] = ...) -> None: ...

class CatalogProduct(_message.Message):
    __slots__ = ("id", "category_id", "name", "code", "description", "fabric_type", "pattern", "style", "transparency", "density", "composition", "care", "recommended_rooms", "recommended_coef", "default_width_m", "is_sewing_required", "segment", "tags_json", "variants", "image_urls")
    ID_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    FABRIC_TYPE_FIELD_NUMBER: _ClassVar[int]
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    STYLE_FIELD_NUMBER: _ClassVar[int]
    TRANSPARENCY_FIELD_NUMBER: _ClassVar[int]
    DENSITY_FIELD_NUMBER: _ClassVar[int]
    COMPOSITION_FIELD_NUMBER: _ClassVar[int]
    CARE_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_ROOMS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_COEF_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_WIDTH_M_FIELD_NUMBER: _ClassVar[int]
    IS_SEWING_REQUIRED_FIELD_NUMBER: _ClassVar[int]
    SEGMENT_FIELD_NUMBER: _ClassVar[int]
    TAGS_JSON_FIELD_NUMBER: _ClassVar[int]
    VARIANTS_FIELD_NUMBER: _ClassVar[int]
    IMAGE_URLS_FIELD_NUMBER: _ClassVar[int]
    id: str
    category_id: str
    name: str
    code: str
    description: str
    fabric_type: str
    pattern: str
    style: str
    transparency: str
    density: float
    composition: str
    care: str
    recommended_rooms: _containers.RepeatedScalarFieldContainer[str]
    recommended_coef: float
    default_width_m: float
    is_sewing_required: bool
    segment: str
    tags_json: str
    variants: _containers.RepeatedCompositeFieldContainer[CatalogVariant]
    image_urls: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., category_id: _Optional[str] = ..., name: _Optional[str] = ..., code: _Optional[str] = ..., description: _Optional[str] = ..., fabric_type: _Optional[str] = ..., pattern: _Optional[str] = ..., style: _Optional[str] = ..., transparency: _Optional[str] = ..., density: _Optional[float] = ..., composition: _Optional[str] = ..., care: _Optional[str] = ..., recommended_rooms: _Optional[_Iterable[str]] = ..., recommended_coef: _Optional[float] = ..., default_width_m: _Optional[float] = ..., is_sewing_required: _Optional[bool] = ..., segment: _Optional[str] = ..., tags_json: _Optional[str] = ..., variants: _Optional[_Iterable[_Union[CatalogVariant, _Mapping]]] = ..., image_urls: _Optional[_Iterable[str]] = ...) -> None: ...

class CatalogVariant(_message.Message):
    __slots__ = ("id", "product_id", "sku", "color_name", "color_hex", "width_m", "price", "price_unit", "old_price", "is_active")
    ID_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_ID_FIELD_NUMBER: _ClassVar[int]
    SKU_FIELD_NUMBER: _ClassVar[int]
    COLOR_NAME_FIELD_NUMBER: _ClassVar[int]
    COLOR_HEX_FIELD_NUMBER: _ClassVar[int]
    WIDTH_M_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    PRICE_UNIT_FIELD_NUMBER: _ClassVar[int]
    OLD_PRICE_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    id: str
    product_id: str
    sku: str
    color_name: str
    color_hex: str
    width_m: float
    price: float
    price_unit: str
    old_price: float
    is_active: bool
    def __init__(self, id: _Optional[str] = ..., product_id: _Optional[str] = ..., sku: _Optional[str] = ..., color_name: _Optional[str] = ..., color_hex: _Optional[str] = ..., width_m: _Optional[float] = ..., price: _Optional[float] = ..., price_unit: _Optional[str] = ..., old_price: _Optional[float] = ..., is_active: _Optional[bool] = ...) -> None: ...

class CatalogCategory(_message.Message):
    __slots__ = ("id", "name", "slug", "parent_id", "sort_order")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SLUG_FIELD_NUMBER: _ClassVar[int]
    PARENT_ID_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    slug: str
    parent_id: str
    sort_order: int
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., slug: _Optional[str] = ..., parent_id: _Optional[str] = ..., sort_order: _Optional[int] = ...) -> None: ...

class CatalogCalcRule(_message.Message):
    __slots__ = ("key", "value", "unit", "description", "applies_to_json")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    APPLIES_TO_JSON_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: float
    unit: str
    description: str
    applies_to_json: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ..., unit: _Optional[str] = ..., description: _Optional[str] = ..., applies_to_json: _Optional[str] = ...) -> None: ...

class CatalogKnowledgeRule(_message.Message):
    __slots__ = ("id", "kind", "condition_json", "recommendation", "priority")
    ID_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    CONDITION_JSON_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    id: str
    kind: str
    condition_json: str
    recommendation: str
    priority: int
    def __init__(self, id: _Optional[str] = ..., kind: _Optional[str] = ..., condition_json: _Optional[str] = ..., recommendation: _Optional[str] = ..., priority: _Optional[int] = ...) -> None: ...

class WatchRequest(_message.Message):
    __slots__ = ("from_version", "tenant_id")
    FROM_VERSION_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    from_version: int
    tenant_id: str
    def __init__(self, from_version: _Optional[int] = ..., tenant_id: _Optional[str] = ...) -> None: ...

class CatalogDelta(_message.Message):
    __slots__ = ("version", "entity", "entity_id", "action", "tenant_id", "payload_json")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    ENTITY_FIELD_NUMBER: _ClassVar[int]
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_JSON_FIELD_NUMBER: _ClassVar[int]
    version: int
    entity: str
    entity_id: str
    action: str
    tenant_id: str
    payload_json: str
    def __init__(self, version: _Optional[int] = ..., entity: _Optional[str] = ..., entity_id: _Optional[str] = ..., action: _Optional[str] = ..., tenant_id: _Optional[str] = ..., payload_json: _Optional[str] = ...) -> None: ...

class UsageRequest(_message.Message):
    __slots__ = ("session_id", "user_id", "tenant_id", "conversation_id", "message_id", "usage")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    USAGE_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    user_id: str
    tenant_id: str
    conversation_id: str
    message_id: str
    usage: Usage
    def __init__(self, session_id: _Optional[str] = ..., user_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., conversation_id: _Optional[str] = ..., message_id: _Optional[str] = ..., usage: _Optional[_Union[Usage, _Mapping]] = ...) -> None: ...

class OrderDraftRequest(_message.Message):
    __slots__ = ("session_id", "user_id", "tenant_id", "conversation_id", "customer_name", "customer_phone", "address", "items_json", "note")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_NAME_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_PHONE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_JSON_FIELD_NUMBER: _ClassVar[int]
    NOTE_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    user_id: str
    tenant_id: str
    conversation_id: str
    customer_name: str
    customer_phone: str
    address: str
    items_json: str
    note: str
    def __init__(self, session_id: _Optional[str] = ..., user_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., conversation_id: _Optional[str] = ..., customer_name: _Optional[str] = ..., customer_phone: _Optional[str] = ..., address: _Optional[str] = ..., items_json: _Optional[str] = ..., note: _Optional[str] = ...) -> None: ...

class OrderDraftResponse(_message.Message):
    __slots__ = ("order_id", "order_number", "success", "error")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_NUMBER_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    order_number: str
    success: bool
    error: str
    def __init__(self, order_id: _Optional[str] = ..., order_number: _Optional[str] = ..., success: _Optional[bool] = ..., error: _Optional[str] = ...) -> None: ...

class MessageLogRequest(_message.Message):
    __slots__ = ("session_id", "conversation_id", "role", "content", "tool_calls_json", "tool_result_json", "audio_url", "tokens_in", "tokens_out")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALLS_JSON_FIELD_NUMBER: _ClassVar[int]
    TOOL_RESULT_JSON_FIELD_NUMBER: _ClassVar[int]
    AUDIO_URL_FIELD_NUMBER: _ClassVar[int]
    TOKENS_IN_FIELD_NUMBER: _ClassVar[int]
    TOKENS_OUT_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    conversation_id: str
    role: str
    content: str
    tool_calls_json: str
    tool_result_json: str
    audio_url: str
    tokens_in: int
    tokens_out: int
    def __init__(self, session_id: _Optional[str] = ..., conversation_id: _Optional[str] = ..., role: _Optional[str] = ..., content: _Optional[str] = ..., tool_calls_json: _Optional[str] = ..., tool_result_json: _Optional[str] = ..., audio_url: _Optional[str] = ..., tokens_in: _Optional[int] = ..., tokens_out: _Optional[int] = ...) -> None: ...

class Ack(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...
