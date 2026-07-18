[out:json][timeout:180];

// Target the entire country of Egypt using its ISO 3166-1 code
area["ISO3166-1"="EG"]->.searchArea;

(
  // Checkpoints — proxy for controlled access
  nwr["barrier"="checkpoint"](area.searchArea);
  nwr["barrier"="border_control"](area.searchArea);

  // Government/security infrastructure
  nwr["amenity"="police"](area.searchArea);
  nwr["office"="government"](area.searchArea);

  // Prisons
  nwr["amenity"="prison"](area.searchArea);

  // Embassies/consulates
  nwr["office"="diplomatic"](area.searchArea);
  nwr["diplomatic"="embassy"](area.searchArea);

  // Critical infrastructure
  nwr["power"="plant"](area.searchArea);
  nwr["man_made"="water_works"](area.searchArea);
  nwr["man_made"="communications_tower"]["access"="no"](area.searchArea);
);

out center;