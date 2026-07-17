[out:json][timeout:900];
area["ISO3166-1"="EG"][admin_level=2]->.egypt;

(
  // Military zones — no entry
  nwr["military"](area.egypt);
  nwr["landuse"="military"](area.egypt);

  // Protected areas — no drone, restricted access
  nwr["leisure"="nature_reserve"](area.egypt);
  nwr["boundary"="national_park"](area.egypt);
  nwr["boundary"="protected_area"](area.egypt);

  // Access-restricted features
  nwr["access"="no"]["historic"](area.egypt);
  nwr["access"="no"]["tourism"](area.egypt);
  nwr["access"="restricted"]["historic"](area.egypt);
  nwr["access"="restricted"]["tourism"](area.egypt);
  nwr["access"="permissive"]["historic"](area.egypt);
  nwr["access"="private"]["historic"](area.egypt);

  // Heritage sites with known access limits
  nwr["heritage"]["access"="no"](area.egypt);
  nwr["heritage"]["access"="restricted"](area.egypt);

  // No-go buffer zones
  nwr["boundary"="military"](area.egypt);
  nwr["boundary"="security"](area.egypt);

  // Nuclear / industrial danger zones
  nwr["landuse"="industrial"]["operator"="nuclear"](area.egypt);
  nwr["man_made"="explosive"](area.egypt);

  // Danger areas
  nwr["hazard"]["access"="no"](area.egypt);
  nwr["area":"hazard"]["access"="no"](area.egypt);
);

out geom;
