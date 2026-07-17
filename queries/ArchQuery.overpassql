[out:json][timeout:900];

area["ISO3166-1"="EG"][admin_level=2]->.egypt;

(
  // Strict matching: Global databases ensure the site is real
  nwr["historic"]["wikidata"](area.egypt);
  nwr["historic"]["wikipedia"](area.egypt);
  nwr["heritage"](area.egypt);
  
  // Specific historical tags filtered by wikidata to avoid prank entries
  nwr["historic"="archaeological_site"]["wikidata"](area.egypt);
  nwr["historic"="fort"]["wikidata"](area.egypt);
  nwr["historic"="castle"]["wikidata"](area.egypt);
  
  // Museums are usually safe if they have a wikidata entry or are well-tagged
  nwr["tourism"="museum"]["wikidata"](area.egypt);
  nwr["amenity"="museum"]["wikidata"](area.egypt);
  
  // Only pull attractions that have an established Wikipedia/Wikidata presence
  nwr["tourism"="attraction"]["wikidata"](area.egypt);
  nwr["tourism"="attraction"]["wikipedia"](area.egypt);
);

out center tags;
