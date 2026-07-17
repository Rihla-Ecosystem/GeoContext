[out:json][timeout:900];
area["ISO3166-1"="EG"][admin_level=2]->.egypt;

(
  // Churches
  nwr["building"="church"](area.egypt);
  nwr["amenity"="place_of_worship"]["religion"="christian"](area.egypt);

  // Monasteries
  nwr["historic"="monastery"](area.egypt);
  nwr["building"="monastery"](area.egypt);
  nwr["amenity"="monastery"](area.egypt);
  nwr["leisure"="monastery"](area.egypt);
  nwr["man_made"="monastery"](area.egypt);

  // Coptic Christian sites specifically
  nwr["denomination"="coptic_orthodox"](area.egypt);
  nwr["denomination"="coptic_catholic"](area.egypt);
  nwr["historic:civilization"="coptic"](area.egypt);

  // Christian historic sites
  nwr["historic"="church"](area.egypt);
  nwr["historic"="cathedral"](area.egypt);
  nwr["historic:civilization"="christian"](area.egypt);
  nwr["historic:era"="byzantine"](area.egypt);
  nwr["historic:era"="coptic"](area.egypt);

  // Cathedrals
  nwr["building"="cathedral"](area.egypt);
  nwr["amenity"="place_of_worship"]["building"="cathedral"]["religion"="christian"](area.egypt);

  // Christian cemeteries
  nwr["cemetery"="christian"](area.egypt);
  nwr["cemetery"="coptic"](area.egypt);
  nwr["landuse"="cemetery"]["religion"="christian"](area.egypt);

  // Christian pilgrimage sites
  nwr["historic"="pilgrimage_site"]["religion"="christian"](area.egypt);
);

out center tags;
