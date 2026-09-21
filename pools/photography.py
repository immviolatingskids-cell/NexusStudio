from pool_models import PoolEntry

CAMERA = (
    PoolEntry("iphone_16_pro", "iPhone 16 Pro rear camera, native iOS camera pipeline", frozenset({"camera", "phone_camera"}), metadata={"device_type":"phone", "sensor_class":"phone", "fixed_lens":False, "preferred_modes":["lifestyle","hobby"]}),
    PoolEntry("sony_a7r_v", "Sony A7R V full-frame mirrorless camera body", frozenset({"camera","mirrorless","full_frame"}), metadata={"device_type":"mirrorless","sensor_class":"full_frame","fixed_lens":False,"preferred_modes":["portrait","workplace"]}),
    PoolEntry("fujifilm_x100vi", "Fujifilm X100VI compact digital camera", frozenset({"camera","compact_camera","fixed_lens"}), metadata={"device_type":"compact","sensor_class":"aps_c","fixed_lens":True,"fixed_equivalent_focal_length":35,"preferred_modes":["lifestyle","environmental"]}),
    PoolEntry("sony_fx3", "Sony FX3 full-frame cinema camera", frozenset({"camera","cinema_camera","full_frame"}), metadata={"device_type":"cinema","sensor_class":"full_frame","fixed_lens":False,"preferred_modes":["hobby","environmental"]}),
)
LENS = (
    PoolEntry("lens_24", "24mm equivalent wide-angle lens, subtle perspective distortion", frozenset({"lens","wide_angle","environmental_framing"}), metadata={"focal_length_mm":24,"aperture":"variable","lens_class":"wide","best_for_modes":["environmental","hobby"]}),
    PoolEntry("lens_35", "35mm f/1.8 handheld street lens, natural eye-level field of view", frozenset({"lens","normal_lens","environmental_framing"}), metadata={"focal_length_mm":35,"aperture":"f/1.8","lens_class":"normal","best_for_modes":["lifestyle","workplace","full_body"]}),
    PoolEntry("lens_50", "50mm f/1.4 prime lens, sharp focal plane and natural perspective", frozenset({"lens","normal_lens","shallow_dof"}), metadata={"focal_length_mm":50,"aperture":"f/1.4","lens_class":"normal","best_for_modes":["portrait","lifestyle","workplace"]}),
    PoolEntry("lens_85", "85mm f/1.4 portrait lens, creamy smooth background bokeh", frozenset({"lens","portrait_lens","shallow_dof"}), metadata={"focal_length_mm":85,"aperture":"f/1.4","lens_class":"portrait","best_for_modes":["portrait","full_body"]}),
    PoolEntry("lens_105", "105mm f/2.8 portrait lens, flattering compression and shallow depth of field", frozenset({"lens","portrait_lens","compressed_perspective","shallow_dof"}), metadata={"focal_length_mm":105,"aperture":"f/2.8","lens_class":"portrait","best_for_modes":["portrait"]}),
)
AMBIENT = (
    PoolEntry("overcast", "soft overcast daylight", frozenset({"ambient_light","daylight","cool_light"}), metadata={"indoor_outdoor":"outdoor","temperature":"cool","preferred_modes":["portrait","workplace","environmental"]}),
    PoolEntry("golden_afternoon", "golden afternoon sunlight", frozenset({"ambient_light","daylight","golden_hour","warm_light"}), metadata={"indoor_outdoor":"outdoor","temperature":"warm","preferred_modes":["lifestyle","environmental"]}),
    PoolEntry("warm_evening_room", "warm late-evening indoor light", frozenset({"ambient_light","evening","warm_light"}), metadata={"indoor_outdoor":"indoor","temperature":"warm","preferred_modes":["hobby","workplace"]}),
    PoolEntry("dim_night_room", "dim nighttime room lighting", frozenset({"ambient_light","night","cool_light"}), metadata={"indoor_outdoor":"indoor","temperature":"cool","preferred_modes":["hobby"]}),
    PoolEntry("studio", "soft studio lighting", frozenset({"ambient_light","studio_light"}), metadata={"indoor_outdoor":"indoor","temperature":"neutral","preferred_modes":["portrait"]}),
)
PRACTICAL = (
    PoolEntry("window_left", "window light from the left", frozenset({"practical_light","window_light","daylight"}), metadata={"source_type":"window","best_for_modes":["portrait","workplace","lifestyle"]}),
    PoolEntry("tv_glow", "TV screen glow", frozenset({"practical_light","tv_glow","cool_light"}), metadata={"source_type":"screen","best_for_modes":["hobby"]}),
    PoolEntry("monitor", "monitor light", frozenset({"practical_light","monitor_glow","cool_light"}), metadata={"source_type":"screen","best_for_modes":["hobby"]}),
    PoolEntry("bedside_lamp", "warm bedside lamp", frozenset({"practical_light","lamp_light","warm_light"}), metadata={"source_type":"lamp","best_for_modes":["hobby","lifestyle"]}),
)
SUBJECT = (
    PoolEntry("soft_face", "soft light falling across her face", frozenset({"subject_light","warm_light"}), metadata={"effect_type":"face_fill","supports":["window_left","golden_afternoon"]}),
    PoolEntry("cool_cheeks", "cool blue reflections across her cheeks", frozenset({"subject_light","cool_light"}), metadata={"effect_type":"reflection","supports":["monitor","tv_glow"]}),
    PoolEntry("jaw_contour", "subtle shadow contouring around the jawline", frozenset({"subject_light"}), metadata={"effect_type":"contour","supports":["window_left","studio"]}),
    PoolEntry("mixed_face", "mixed warm and cool light across the face", frozenset({"subject_light","mixed_light"}), metadata={"effect_type":"mixed","supports":["monitor","tv_glow"]}),
)
MOOD = (
    PoolEntry("natural", "clean natural realism", frozenset({"lighting_mood"}), metadata={"mood_family":"natural","supports":["overcast","golden_afternoon","studio"]}),
    PoolEntry("cozy", "cozy and intimate", frozenset({"lighting_mood","warm_light"}), metadata={"mood_family":"intimate","supports":["warm_evening_room","dim_night_room"]}),
    PoolEntry("mixed", "cinematic mixed-light atmosphere", frozenset({"lighting_mood","mixed_light"}), metadata={"mood_family":"cinematic","supports":["warm_evening_room","dim_night_room"]}),
    PoolEntry("editorial", "focused editorial clarity", frozenset({"lighting_mood"}), metadata={"mood_family":"editorial","supports":["studio","overcast"]}),
)
