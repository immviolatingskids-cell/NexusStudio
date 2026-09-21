from pool_models import PoolEntry

POOL = (
    PoolEntry("skin_fair_neutral", "fair neutral complexion", {"fair_skin", "natural"}, metadata={"category": "complexion", "label": "fair neutral complexion"}),
    PoolEntry("skin_warm_olive", "warm olive complexion", {"olive_skin", "warm_skin"}, metadata={"category": "complexion", "label": "warm olive complexion"}),
    PoolEntry("skin_natural_freckles", "natural freckles", {"freckles", "natural"}, metadata={"category": "skin_detail", "label": "natural freckles"}),
    PoolEntry("skin_rosy_cheeks", "naturally rosy cheeks", {"rosy_cheeks", "natural"}, metadata={"category": "skin_detail", "label": "naturally rosy cheeks"}),
    PoolEntry("skin_realistic_texture", "realistic natural skin texture", {"skin_texture", "natural"}, metadata={"category": "skin_detail", "label": "realistic natural skin texture"}),
)
