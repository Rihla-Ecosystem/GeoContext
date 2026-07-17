[out:json][timeout:900];
area["ISO3166-1"="EG"][admin_level=2]->.egypt;

(
  // Mosques
  nwr["building"="mosque"](area.egypt);
  nwr["amenity"="place_of_worship"]["religion"="muslim"](area.egypt);

  // Islamic historic sites
  nwr["historic"="mosque"](area.egypt);
  nwr["historic:civilization"="islamic"](area.egypt);
  nwr["historic:era"="islamic"](area.egypt);

  // Madrasas (Islamic schools)
  nwr["historic"="madrasa"](area.egypt);
  nwr["building"="madrasa"](area.egypt);

  // Other Islamic religious buildings
  nwr["building"="minaret"](area.egypt);
  nwr["historic"="minaret"](area.egypt);
  nwr["historic"="sabil"](area.egypt);
  nwr["historic"="wikala"](area.egypt);

  // Sufi sites
  nwr["building"="zawiya"](area.egypt);
  nwr["historic"="zawiya"](area.egypt);
  nwr["building"="tekke"](area.egypt);
  nwr["tomb"="mausoleum"]["religion"="muslim"](area.egypt);

  // Islamic cemeteries
  nwr["cemetery"="muslim"](area.egypt);
  nwr["landuse"="cemetery"]["religion"="muslim"](area.egypt);

  // Forts/castles with Islamic origin
  nwr["historic"="fort"]["historic:civilization"="islamic"](area.egypt);
  nwr["historic"="castle"]["historic:civilization"="islamic"](area.egypt);
);

out center tags;
