import { api } from "./client.js";

/**
 * News API client + dropdown option lists for the UI.
 *
 * Talks to the backend's `/news` endpoint (detailed headline feed) and
 * exposes the static option lists the FiltersBar needs:
 *
 *   - CATEGORIES        : full NewsData.io top-headline categories.
 *   - COUNTRIES         : every ISO-3166-1 alpha-2 country NewsData.io accepts.
 *   - REGIONS_BY_COUNTRY: per-country subdivision lists (states / provinces /
 *                         emirates / etc.) for the country picker.
 *
 * NewsData.io has no native subdivision filter, so when the user picks a
 * region we forward its name as `qInTitle` (title-only keyword search) -
 * this gives much tighter, region-specific results than folding the name
 * into the broad `q` parameter would.
 */

function buildParams({ category, country, q, qInTitle, page, pageSize }) {
  const params = {};
  if (category) params.category = category;
  if (country) params.country = country;
  if (q) params.q = q;
  if (qInTitle) params.q_in_title = qInTitle;
  if (page) params.page = page;
  if (pageSize) params.page_size = pageSize;
  return params;
}

export async function fetchNews(filters = {}) {
  const { data } = await api.get("/news", {
    params: buildParams(filters),
  });
  return data;
}

// ---------------------------------------------------------------------------
// Categories - the full NewsData.io supported list.
// ---------------------------------------------------------------------------

export const CATEGORIES = [
  "business",
  "crime",
  "domestic",
  "education",
  "entertainment",
  "environment",
  "food",
  "health",
  "lifestyle",
  "other",
  "politics",
  "science",
  "sports",
  "technology",
  "top",
  "tourism",
  "world",
];

// ---------------------------------------------------------------------------
// Countries - every ISO-3166-1 alpha-2 code NewsData.io accepts (2026).
// Sorted alphabetically by display label so the picker is easy to scan.
// ---------------------------------------------------------------------------

export const COUNTRIES = [
  { code: "af", label: "Afghanistan" },
  { code: "al", label: "Albania" },
  { code: "dz", label: "Algeria" },
  { code: "ad", label: "Andorra" },
  { code: "ao", label: "Angola" },
  { code: "ar", label: "Argentina" },
  { code: "am", label: "Armenia" },
  { code: "au", label: "Australia" },
  { code: "at", label: "Austria" },
  { code: "az", label: "Azerbaijan" },
  { code: "bs", label: "Bahamas" },
  { code: "bh", label: "Bahrain" },
  { code: "bd", label: "Bangladesh" },
  { code: "bb", label: "Barbados" },
  { code: "by", label: "Belarus" },
  { code: "be", label: "Belgium" },
  { code: "bz", label: "Belize" },
  { code: "bj", label: "Benin" },
  { code: "bm", label: "Bermuda" },
  { code: "bt", label: "Bhutan" },
  { code: "bo", label: "Bolivia" },
  { code: "ba", label: "Bosnia and Herzegovina" },
  { code: "bw", label: "Botswana" },
  { code: "br", label: "Brazil" },
  { code: "bn", label: "Brunei" },
  { code: "bg", label: "Bulgaria" },
  { code: "bf", label: "Burkina Faso" },
  { code: "bi", label: "Burundi" },
  { code: "kh", label: "Cambodia" },
  { code: "cm", label: "Cameroon" },
  { code: "ca", label: "Canada" },
  { code: "cv", label: "Cape Verde" },
  { code: "ky", label: "Cayman Islands" },
  { code: "cf", label: "Central African Republic" },
  { code: "td", label: "Chad" },
  { code: "cl", label: "Chile" },
  { code: "cn", label: "China" },
  { code: "co", label: "Colombia" },
  { code: "km", label: "Comoros" },
  { code: "cg", label: "Congo" },
  { code: "cd", label: "Congo (DRC)" },
  { code: "cr", label: "Costa Rica" },
  { code: "ci", label: "Cote d'Ivoire" },
  { code: "hr", label: "Croatia" },
  { code: "cu", label: "Cuba" },
  { code: "cy", label: "Cyprus" },
  { code: "cz", label: "Czechia" },
  { code: "dk", label: "Denmark" },
  { code: "dj", label: "Djibouti" },
  { code: "dm", label: "Dominica" },
  { code: "do", label: "Dominican Republic" },
  { code: "ec", label: "Ecuador" },
  { code: "eg", label: "Egypt" },
  { code: "sv", label: "El Salvador" },
  { code: "gq", label: "Equatorial Guinea" },
  { code: "er", label: "Eritrea" },
  { code: "ee", label: "Estonia" },
  { code: "sz", label: "Eswatini" },
  { code: "et", label: "Ethiopia" },
  { code: "fj", label: "Fiji" },
  { code: "fi", label: "Finland" },
  { code: "fr", label: "France" },
  { code: "ga", label: "Gabon" },
  { code: "gm", label: "Gambia" },
  { code: "ge", label: "Georgia" },
  { code: "de", label: "Germany" },
  { code: "gh", label: "Ghana" },
  { code: "gi", label: "Gibraltar" },
  { code: "gr", label: "Greece" },
  { code: "gd", label: "Grenada" },
  { code: "gt", label: "Guatemala" },
  { code: "gn", label: "Guinea" },
  { code: "gw", label: "Guinea-Bissau" },
  { code: "gy", label: "Guyana" },
  { code: "ht", label: "Haiti" },
  { code: "hn", label: "Honduras" },
  { code: "hk", label: "Hong Kong" },
  { code: "hu", label: "Hungary" },
  { code: "is", label: "Iceland" },
  { code: "in", label: "India" },
  { code: "id", label: "Indonesia" },
  { code: "ir", label: "Iran" },
  { code: "iq", label: "Iraq" },
  { code: "ie", label: "Ireland" },
  { code: "il", label: "Israel" },
  { code: "it", label: "Italy" },
  { code: "jm", label: "Jamaica" },
  { code: "jp", label: "Japan" },
  { code: "jo", label: "Jordan" },
  { code: "kz", label: "Kazakhstan" },
  { code: "ke", label: "Kenya" },
  { code: "ki", label: "Kiribati" },
  { code: "kw", label: "Kuwait" },
  { code: "kg", label: "Kyrgyzstan" },
  { code: "la", label: "Laos" },
  { code: "lv", label: "Latvia" },
  { code: "lb", label: "Lebanon" },
  { code: "ls", label: "Lesotho" },
  { code: "lr", label: "Liberia" },
  { code: "ly", label: "Libya" },
  { code: "li", label: "Liechtenstein" },
  { code: "lt", label: "Lithuania" },
  { code: "lu", label: "Luxembourg" },
  { code: "mo", label: "Macao" },
  { code: "mk", label: "North Macedonia" },
  { code: "mg", label: "Madagascar" },
  { code: "mw", label: "Malawi" },
  { code: "my", label: "Malaysia" },
  { code: "mv", label: "Maldives" },
  { code: "ml", label: "Mali" },
  { code: "mt", label: "Malta" },
  { code: "mh", label: "Marshall Islands" },
  { code: "mr", label: "Mauritania" },
  { code: "mu", label: "Mauritius" },
  { code: "mx", label: "Mexico" },
  { code: "fm", label: "Micronesia" },
  { code: "md", label: "Moldova" },
  { code: "mc", label: "Monaco" },
  { code: "mn", label: "Mongolia" },
  { code: "me", label: "Montenegro" },
  { code: "ma", label: "Morocco" },
  { code: "mz", label: "Mozambique" },
  { code: "mm", label: "Myanmar" },
  { code: "na", label: "Namibia" },
  { code: "nr", label: "Nauru" },
  { code: "np", label: "Nepal" },
  { code: "nl", label: "Netherlands" },
  { code: "nz", label: "New Zealand" },
  { code: "ni", label: "Nicaragua" },
  { code: "ne", label: "Niger" },
  { code: "ng", label: "Nigeria" },
  { code: "kp", label: "North Korea" },
  { code: "no", label: "Norway" },
  { code: "om", label: "Oman" },
  { code: "pk", label: "Pakistan" },
  { code: "pw", label: "Palau" },
  { code: "ps", label: "Palestine" },
  { code: "pa", label: "Panama" },
  { code: "pg", label: "Papua New Guinea" },
  { code: "py", label: "Paraguay" },
  { code: "pe", label: "Peru" },
  { code: "ph", label: "Philippines" },
  { code: "pl", label: "Poland" },
  { code: "pt", label: "Portugal" },
  { code: "pr", label: "Puerto Rico" },
  { code: "qa", label: "Qatar" },
  { code: "ro", label: "Romania" },
  { code: "ru", label: "Russia" },
  { code: "rw", label: "Rwanda" },
  { code: "ws", label: "Samoa" },
  { code: "sm", label: "San Marino" },
  { code: "st", label: "Sao Tome and Principe" },
  { code: "sa", label: "Saudi Arabia" },
  { code: "sn", label: "Senegal" },
  { code: "rs", label: "Serbia" },
  { code: "sc", label: "Seychelles" },
  { code: "sl", label: "Sierra Leone" },
  { code: "sg", label: "Singapore" },
  { code: "sk", label: "Slovakia" },
  { code: "si", label: "Slovenia" },
  { code: "sb", label: "Solomon Islands" },
  { code: "so", label: "Somalia" },
  { code: "za", label: "South Africa" },
  { code: "kr", label: "South Korea" },
  { code: "es", label: "Spain" },
  { code: "lk", label: "Sri Lanka" },
  { code: "sd", label: "Sudan" },
  { code: "sr", label: "Suriname" },
  { code: "se", label: "Sweden" },
  { code: "ch", label: "Switzerland" },
  { code: "sy", label: "Syria" },
  { code: "tw", label: "Taiwan" },
  { code: "tj", label: "Tajikistan" },
  { code: "tz", label: "Tanzania" },
  { code: "th", label: "Thailand" },
  { code: "tl", label: "Timor-Leste" },
  { code: "tg", label: "Togo" },
  { code: "to", label: "Tonga" },
  { code: "tt", label: "Trinidad and Tobago" },
  { code: "tn", label: "Tunisia" },
  { code: "tr", label: "Turkey" },
  { code: "tm", label: "Turkmenistan" },
  { code: "tv", label: "Tuvalu" },
  { code: "ug", label: "Uganda" },
  { code: "ua", label: "Ukraine" },
  { code: "ae", label: "United Arab Emirates" },
  { code: "gb", label: "United Kingdom" },
  { code: "us", label: "United States" },
  { code: "uy", label: "Uruguay" },
  { code: "uz", label: "Uzbekistan" },
  { code: "vu", label: "Vanuatu" },
  { code: "va", label: "Vatican City" },
  { code: "ve", label: "Venezuela" },
  { code: "vn", label: "Vietnam" },
  { code: "ye", label: "Yemen" },
  { code: "zm", label: "Zambia" },
  { code: "zw", label: "Zimbabwe" },
];

// ---------------------------------------------------------------------------
// Regions / states / provinces by country.
//
// Keyed by ISO-3166-1 alpha-2 country code. Countries without an entry
// just won't show a Region dropdown (which is the right default - we'd
// rather hide the picker than show a misleading "All states" with nothing
// in it).
//
// Selecting a region sends its name as `qInTitle` so headlines mentioning
// the region in the title are returned, regardless of country code support.
// ---------------------------------------------------------------------------

export const REGIONS_BY_COUNTRY = {
  in: [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
  ],
  us: [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming", "Washington DC",
  ],
  gb: ["England", "Scotland", "Wales", "Northern Ireland"],
  ca: [
    "Alberta", "British Columbia", "Manitoba", "New Brunswick",
    "Newfoundland and Labrador", "Nova Scotia", "Ontario",
    "Prince Edward Island", "Quebec", "Saskatchewan",
    "Northwest Territories", "Nunavut", "Yukon",
  ],
  au: [
    "New South Wales", "Victoria", "Queensland", "Western Australia",
    "South Australia", "Tasmania", "Australian Capital Territory",
    "Northern Territory",
  ],
  de: [
    "Baden-Wurttemberg", "Bavaria", "Berlin", "Brandenburg", "Bremen",
    "Hamburg", "Hesse", "Lower Saxony", "Mecklenburg-Vorpommern",
    "North Rhine-Westphalia", "Rhineland-Palatinate", "Saarland",
    "Saxony", "Saxony-Anhalt", "Schleswig-Holstein", "Thuringia",
  ],
  fr: [
    "Auvergne-Rhone-Alpes", "Bourgogne-Franche-Comte", "Brittany",
    "Centre-Val de Loire", "Corsica", "Grand Est", "Hauts-de-France",
    "Ile-de-France", "Normandy", "Nouvelle-Aquitaine", "Occitanie",
    "Pays de la Loire", "Provence-Alpes-Cote d'Azur",
  ],
  it: [
    "Abruzzo", "Aosta Valley", "Apulia", "Basilicata", "Calabria",
    "Campania", "Emilia-Romagna", "Friuli-Venezia Giulia", "Lazio",
    "Liguria", "Lombardy", "Marche", "Molise", "Piedmont", "Sardinia",
    "Sicily", "Trentino-Alto Adige", "Tuscany", "Umbria", "Veneto",
  ],
  es: [
    "Andalusia", "Aragon", "Asturias", "Balearic Islands", "Basque Country",
    "Canary Islands", "Cantabria", "Castile and Leon", "Castilla-La Mancha",
    "Catalonia", "Extremadura", "Galicia", "La Rioja", "Madrid", "Murcia",
    "Navarre", "Valencia",
  ],
  br: [
    "Acre", "Alagoas", "Amapa", "Amazonas", "Bahia", "Ceara",
    "Distrito Federal", "Espirito Santo", "Goias", "Maranhao",
    "Mato Grosso", "Mato Grosso do Sul", "Minas Gerais", "Para",
    "Paraiba", "Parana", "Pernambuco", "Piaui", "Rio de Janeiro",
    "Rio Grande do Norte", "Rio Grande do Sul", "Rondonia", "Roraima",
    "Santa Catarina", "Sao Paulo", "Sergipe", "Tocantins",
  ],
  mx: [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
    "Chiapas", "Chihuahua", "Coahuila", "Colima", "Durango", "Guanajuato",
    "Guerrero", "Hidalgo", "Jalisco", "Mexico City", "Mexico State",
    "Michoacan", "Morelos", "Nayarit", "Nuevo Leon", "Oaxaca", "Puebla",
    "Queretaro", "Quintana Roo", "San Luis Potosi", "Sinaloa", "Sonora",
    "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatan", "Zacatecas",
  ],
  ng: [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue",
    "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu",
    "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi",
    "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo",
    "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
    "Federal Capital Territory",
  ],
  za: [
    "Eastern Cape", "Free State", "Gauteng", "KwaZulu-Natal", "Limpopo",
    "Mpumalanga", "North West", "Northern Cape", "Western Cape",
  ],
  ae: [
    "Abu Dhabi", "Ajman", "Dubai", "Fujairah", "Ras Al Khaimah", "Sharjah",
    "Umm Al Quwain",
  ],
  pk: [
    "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan",
    "Islamabad Capital Territory", "Azad Kashmir", "Gilgit-Baltistan",
  ],
  bd: [
    "Barisal", "Chittagong", "Dhaka", "Khulna", "Mymensingh", "Rajshahi",
    "Rangpur", "Sylhet",
  ],
  np: [
    "Bagmati", "Gandaki", "Karnali", "Koshi", "Lumbini", "Madhesh",
    "Sudurpashchim",
  ],
  lk: [
    "Central", "Eastern", "North Central", "Northern", "North Western",
    "Sabaragamuwa", "Southern", "Uva", "Western",
  ],
  cn: [
    "Anhui", "Beijing", "Chongqing", "Fujian", "Gansu", "Guangdong",
    "Guangxi", "Guizhou", "Hainan", "Hebei", "Heilongjiang", "Henan",
    "Hong Kong", "Hubei", "Hunan", "Inner Mongolia", "Jiangsu", "Jiangxi",
    "Jilin", "Liaoning", "Macao", "Ningxia", "Qinghai", "Shaanxi",
    "Shandong", "Shanghai", "Shanxi", "Sichuan", "Taiwan", "Tianjin",
    "Tibet", "Xinjiang", "Yunnan", "Zhejiang",
  ],
  jp: [
    "Hokkaido", "Tohoku", "Kanto", "Chubu", "Kansai", "Chugoku",
    "Shikoku", "Kyushu", "Okinawa",
  ],
  ru: [
    "Central", "Northwestern", "Southern", "North Caucasian", "Volga",
    "Ural", "Siberian", "Far Eastern",
  ],
  id: [
    "Aceh", "Bali", "Banten", "Bengkulu", "Central Java", "Central Kalimantan",
    "Central Sulawesi", "East Java", "East Kalimantan", "East Nusa Tenggara",
    "Gorontalo", "Jakarta", "Jambi", "Lampung", "Maluku", "North Maluku",
    "North Sulawesi", "North Sumatra", "Papua", "Riau", "South Kalimantan",
    "South Sulawesi", "South Sumatra", "Southeast Sulawesi", "West Java",
    "West Kalimantan", "West Nusa Tenggara", "West Papua", "West Sumatra",
    "Yogyakarta",
  ],
  ph: [
    "Ilocos", "Cagayan Valley", "Central Luzon", "Calabarzon", "Mimaropa",
    "Bicol", "Western Visayas", "Central Visayas", "Eastern Visayas",
    "Zamboanga Peninsula", "Northern Mindanao", "Davao", "Soccsksargen",
    "Caraga", "Bangsamoro", "Cordillera", "Metro Manila",
  ],
};

/**
 * Return the list of regions for an ISO country code, or `[]` if there's
 * no entry. Used by FiltersBar to decide whether to render the Region
 * dropdown for the currently-selected country.
 */
export function regionsForCountry(countryCode) {
  if (!countryCode) return [];
  return REGIONS_BY_COUNTRY[countryCode.toLowerCase()] ?? [];
}
