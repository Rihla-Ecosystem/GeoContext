[out:json][timeout:900];
area["ISO3166-1"="EG"][admin_level=2]->.egypt;

(
  // Protected areas — no drone, restricted access
  nwr["leisure"="nature_reserve"](area.egypt);
  nwr["boundary"="national_park"](area.egypt);
  nwr["boundary"="protected_area"](area.egypt);
);

out geom;