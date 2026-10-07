// Conservation status of each voice. A recording takes its population's status where that population has its own
// assessment, stock report or legal listing, and its species' IUCN Red List category otherwise. Every count names the
// year it describes, and every entry its sources (IUCN assessments, NOAA stock assessment reports, census reports).
// Kept apart from resources/follow-music.json, whose hash is part of every piece id.

import type { Source, Species } from "./types.ts";

/**
 * IUCN Red List categories. A population's own listing takes the category of the same name (ESA "Endangered" → EN);
 * "Threatened" has no IUCN equivalent, so such a population keeps its species' category and names the listing in words.
 */
export type Category = "CR" | "EN" | "VU" | "NT" | "LC" | "DD";
export type Trend = "increasing" | "decreasing" | "stable" | "unknown";
export interface Reference { label: string; url: string }

export interface Status {
  /** Who the status describes: a species worldwide or one population. */
  group: string;
  category: Category;
  /** The listing in words, with its year. */
  listing: string;
  /** How the listing has changed over the years. */
  history?: string;
  /** A published count or estimate, with the year it describes. */
  count?: string;
  trend: Trend;
  /** The trend in the source's own terms, or what the count is compared with. */
  trendNote?: string;
  threats?: string;
  /** Protection in place for this group, where a source describes it. */
  protection?: string;
  refs: Reference[];
}

/** What a recording adds to its species: a population with its own status, or a note where none exists. */
interface Voice { population?: Status; note?: string; noteRefs?: Reference[] }

export const CATEGORY: Record<Category, string> = {
  CR: "Critically Endangered", EN: "Endangered", VU: "Vulnerable", NT: "Near Threatened", LC: "Least Concern", DD: "Data Deficient",
};
/** Categories the map and the chairs mark. */
export const THREATENED: ReadonlySet<Category> = new Set(["CR", "EN", "VU"]);
const SEVERITY: Category[] = ["LC", "DD", "NT", "VU", "EN", "CR"];
export const TREND_WORD: Record<Trend, string> = { increasing: "increasing", decreasing: "decreasing", stable: "not growing", unknown: "trend unknown" };
export const TREND_ARROW: Record<Trend, string> = { increasing: "↑", decreasing: "↓", stable: "→", unknown: "" };

const iucn = (path: string): Reference => ({ label: "IUCN Red List assessment", url: `https://www.iucnredlist.org/species/${path}` });
const noaa = (label: string, url: string): Reference => ({ label: `NOAA stock assessment report, ${label}`, url });

const SPECIES_STATUS: Record<Species, Status> = {
  humpback: {
    group: "Humpback whales worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2018)",
    history: "Endangered in 1986 and 1988, Vulnerable 1990–2008, Least Concern since 2008",
    count: "about 135,000 (2018)", trend: "increasing", trendNote: "back above 1942 levels in every major ocean region",
    refs: [iucn("13006/50362794"), { label: "IUCN, 2008: the humpback's road to recovery", url: "https://www.iucn.org/content/humpback-whale-road-recovery-reveals-iucn-red-list" }],
  },
  "right whale": {
    group: "North Atlantic right whales", category: "CR", listing: "IUCN Red List: Critically Endangered (2020)",
    history: "Endangered 2008–2018, Critically Endangered since 2020",
    count: "384 (2024)", trend: "increasing", trendNote: "fell by a quarter in 2011–2020 to a low of 358, slowly rising since",
    threats: "Entanglement in fishing gear and vessel strikes; only about 70 breeding females.",
    refs: [
      { label: "North Atlantic Right Whale Consortium estimate, 2025", url: "https://www.neaq.org/right-whale-population-estimate-2025/" },
      noaa("2023", "https://www.fisheries.noaa.gov/s3/2024-12/2023-sar-narw.pdf"),
      iucn("41712/178589687"),
      { label: "NOAA Fisheries species page", url: "https://www.fisheries.noaa.gov/species/north-atlantic-right-whale" },
    ],
  },
  "fin whale": {
    group: "Fin whales worldwide", category: "VU", listing: "IUCN Red List: Vulnerable (2018)",
    history: "Endangered 1996–2018, Vulnerable since 2018",
    count: "about 100,000 mature whales (2018)", trend: "increasing", trendNote: "around 45% of the 1940 level",
    refs: [iucn("2478/50349982")],
  },
  "blue whale": {
    group: "Blue whales worldwide", category: "EN", listing: "IUCN Red List: Endangered (2018)", history: "Endangered since 1986",
    count: "5,000–15,000 mature whales (2018)", trend: "increasing", trendNote: "3–11% of the 1926 level",
    refs: [iucn("2477/156923585")],
  },
  "minke whale": {
    group: "Common minke whales worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2018)",
    history: "Insufficiently Known 1994, Lower Risk 1996, Least Concern since 2008",
    count: "about 200,000 in the North Atlantic and North Pacific summer ranges", trend: "unknown",
    refs: [iucn("2474/50348265")],
  },
  "bowhead whale": {
    group: "Bowhead whales worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2018)",
    history: "Endangered in 1986 and 1988, Vulnerable 1990–1994, Least Concern since 2008",
    count: "likely more than 25,000 (2018)", trend: "increasing", refs: [iucn("2467/50347659")],
  },
  "sperm whale": {
    group: "Sperm whales worldwide", category: "VU", listing: "IUCN Red List: Vulnerable (2025)", history: "Vulnerable since 1996",
    count: "about 845,000 (model, 2022)", trend: "unknown", trendNote: "recovering a little from whaling, against about 1.95 million before it",
    refs: [
      { label: "IUCN Red List: sperm whale", url: "https://www.iucnredlist.org/search?query=Physeter%20macrocephalus&searchType=species" },
      { label: "Whitehead & Shin 2022, global sperm whale numbers", url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC9663694/" },
    ],
  },
  "killer whale": {
    group: "Killer whales worldwide", category: "DD", listing: "IUCN Red List: Data Deficient (2017)",
    history: "Data Deficient since 2008; the Strait of Gibraltar subpopulation is Critically Endangered (2019)",
    count: "at least tens of thousands of mature whales", trend: "unknown", refs: [iucn("15421/50368125")],
  },
  "false killer whale": {
    group: "False killer whales worldwide", category: "NT", listing: "IUCN Red List: Near Threatened (2018)",
    history: "Data Deficient 2008–2018, Near Threatened since 2018", count: "at least 59,000 (sum of estimates, mostly old)", trend: "unknown",
    refs: [iucn("18596/145357488")],
  },
  "pilot whale": {
    group: "Short-finned pilot whales worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2018)",
    history: "Data Deficient 2008–2018, Least Concern since 2018", count: "about 700,000 (sum of estimates)", trend: "unknown",
    refs: [iucn("9249/50355227")],
  },
  dolphin: {
    group: "Common bottlenose dolphins worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2019)",
    history: "Data Deficient 1996, Least Concern since 2008", count: "at least 750,000, with most of the range never surveyed", trend: "unknown",
    refs: [iucn("22563/156932432")],
  },
  "common dolphin": {
    group: "Common dolphins worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2021)",
    history: "Least Concern since 2008; since 2021 the species includes the former long-beaked common dolphin",
    count: "several million (sum of estimates, 2020)", trend: "unknown", refs: [iucn("134817215/286179278")],
  },
  "spinner dolphin": {
    group: "Spinner dolphins worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2018)",
    history: "Data Deficient 2008–2018, Least Concern since 2018. The eastern Pacific subspecies is Vulnerable (2008) because of tuna purse-seine bycatch",
    count: "more than 1 million (sum of estimates, 2018)", trend: "unknown",
    refs: [iucn("20733/156927622"), { label: "IUCN Red List: eastern spinner dolphin", url: "https://www.iucnredlist.org/species/133712/17838296" }],
  },
  "striped dolphin": {
    group: "Striped dolphins worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2019)",
    history: "Least Concern since 2008; the Mediterranean subpopulation is Vulnerable",
    count: "more than 2 million (sum of estimates, 2018)", trend: "unknown", refs: [iucn("20731/50374282")],
  },
  "rough-toothed dolphin": {
    group: "Rough-toothed dolphins worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2019)",
    history: "Data Deficient 1996, Least Concern since 2008", count: "about 220,000 (sum of estimates, 2018)", trend: "unknown",
    refs: [iucn("20738/178929751")],
  },
  "Atlantic spotted dolphin": {
    group: "Atlantic spotted dolphins worldwide", category: "LC", listing: "IUCN Red List: Least Concern (2018, provisional)",
    history: "Data Deficient 1996–2018, Least Concern since 2018", count: "about 82,000 (US estimates only)", trend: "unknown",
    refs: [iucn("20732/50375312")],
  },
};

const COSEWIC_ORCA: Reference = { label: "COSEWIC killer whale assessment, 2023", url: "https://www.canada.ca/en/environment-climate-change/services/species-risk-public-registry/cosewic-assessments-status-reports/killer-whale-2023.html" };
const SOUTHERN_RESIDENTS: Status = {
  group: "Southern Resident killer whales", category: "EN", listing: "Endangered in the US (2005) and Canada (2003)",
  history: "Canada: Threatened 1999, Endangered since 2001",
  count: "74 (1 July 2025)", trend: "decreasing", trendNote: "about 1% a year since a peak of 98–99 in 1995",
  refs: [
    { label: "Center for Whale Research, 2025 census", url: "https://www.whaleresearch.com/orca-population" },
    noaa("2024", "https://www.fisheries.noaa.gov/s3/2026-08/final_2024-mmsar_killer-whale.pdf"), COSEWIC_ORCA,
  ],
};
const ANTARCTIC_BLUE: Status = {
  group: "Antarctic blue whales", category: "CR", listing: "IUCN Red List: Critically Endangered (2018)",
  history: "Endangered 1996, Critically Endangered since 2008",
  count: "about 6,500, 3,000 of them mature (IUCN model, 2018)", trend: "increasing",
  trendNote: "about 8% a year (Branch 2007) and 10–11% in a 2025 photo-ID study, from 125,000 mature whales in 1926",
  refs: [
    iucn("41713/50226962"),
    { label: "Branch 2007, Journal of Cetacean Research and Management", url: "https://journal.iwc.int/index.php/jcrm/article/view/674" },
    { label: "Olson et al. 2025, Marine Mammal Science", url: "https://doi.org/10.1111/mms.13215" },
  ],
};
const WASHINGTON_HUMPBACKS: Status = {
  group: "Humpback whales off Washington and southern British Columbia", category: "LC",
  listing: "Canada: Special Concern (2011, confirmed 2022). In US law they mix three populations: Hawaiʻi (not listed), Mexico (Threatened) and Central America (Endangered)",
  history: "Canada: Threatened 1985, Special Concern since 2011",
  count: "396 photographed in the Salish Sea in 2022, up from 293 in 2017", trend: "increasing",
  trendNote: "4–8% a year in British Columbia waters, 2004–2018",
  refs: [
    { label: "COSEWIC assessment, 2022", url: "https://www.canada.ca/en/environment-climate-change/services/species-risk-public-registry/cosewic-assessments-status-reports/humpback-whale-2022.html" },
    { label: "Humpbacks in the Salish Sea, 2022 (MERS)", url: "https://mersociety.org/wp-content/uploads/2023/11/2022-humpbacks-in-the-salish-sea-2022-12-13.pdf" },
    { label: "US listing by population, 50 CFR 224.101", url: "https://www.law.cornell.edu/cfr/text/50/224.101" },
  ],
};

const OFFSHORE_ORCA: Voice = {
  population: {
    group: "Offshore killer whales", category: "DD", listing: "Threatened in Canada (2011); not listed in the US",
    count: "300 (photo-ID 1988–2012)", trend: "stable", trendNote: "the only estimate, from 2012",
    refs: [noaa("2018", "https://media.fisheries.noaa.gov/dam-migration/killer_whale_enp_offshorefinal2018.pdf"), COSEWIC_ORCA],
  },
};
const EILAT: Voice = {
  note: "The Dolphin Reef pod in Eilat descends from Black Sea bottlenose dolphins, a subspecies listed Endangered in the wild (IUCN 2008, marked as needing an update). In 2019–2024 the pod was five dolphins free to swim out to sea; in 2019–2020 one of them was a wild Indo-Pacific bottlenose dolphin.",
  noteRefs: [
    { label: "IUCN Red List: Black Sea bottlenose dolphin", url: "https://www.iucnredlist.org/species/133714/17771698" },
    { label: "OpenWhistle dataset paper, 2026", url: "https://arxiv.org/abs/2609.34839" },
    { label: "Mustun et al. 2024, bioRxiv", url: "https://www.biorxiv.org/content/10.1101/2024.10.15.618471" },
  ],
};
const EASTERN_CARIBBEAN_SPERM: Status = {
  group: "Eastern Caribbean sperm whales", category: "VU", listing: "No separate listing; the species is Vulnerable",
  count: "414 adults from St Kitts to Grenada (2019–2020)", trend: "decreasing", trendNote: "Dominica's family units shrank about 4.5% a year from around 2010",
  protection: "Dominica's Sperm Whale Reserve, announced in 2023; the 2025 Act sets it at about 1,231 km² off the west coast.",
  refs: [
    { label: "Gero & Whitehead 2016, PLOS ONE", url: "https://pmc.ncbi.nlm.nih.gov/articles/PMC5051958/" },
    { label: "Vachon et al. 2024, Marine Mammal Science", url: "https://doi.org/10.1111/mms.13116" },
    { label: "Government of Dominica, 2025: Sperm Whale Reserve Bill", url: "https://pressroomopm.gov.dm/dominica-parliament-approves-historic-bill-to-establish-worlds-first-sperm-whale-reserve/" },
  ],
};

/** Recordings whose population has its own figures, or a note where it has none, by catalog id. */
const VOICES: Record<string, Voice> = {
  "humpback-a": { population: WASHINGTON_HUMPBACKS },
  "humpback-b": { population: WASHINGTON_HUMPBACKS },
  "humpback-cape-elizabeth": { population: WASHINGTON_HUMPBACKS },
  "orca-orcasound-lab": { population: SOUTHERN_RESIDENTS },
  "orca-bush-point": { population: SOUTHERN_RESIDENTS },
  "orca-tekteksen": { population: SOUTHERN_RESIDENTS },
  "orca-cape-elizabeth": {
    population: {
      group: "Bigg's (West Coast transient) killer whales", category: "DD", listing: "Threatened in Canada (2003); not listed in the US",
      count: "385 in British Columbia's coastal waters, 243 of them mature (2024)", trend: "increasing", trendNote: "about 2–3% a year since 1994",
      refs: [
        { label: "Towers et al. 2025, Fisheries and Oceans Canada", url: "https://publications.gc.ca/site/eng/9.956233/marcXml.html?MODS=1" },
        noaa("2020", "https://www.fisheries.noaa.gov/s3/2023-06/KILLERWHALEOrcinusorcaWestCoastTransientStock.pdf"), COSEWIC_ORCA,
      ],
    },
  },
  "orca-montague": OFFSHORE_ORCA,
  "sperm-a": { population: EASTERN_CARIBBEAN_SPERM },
  "right-whale-stellwagen": {},
  "fin-whale-stellwagen": {
    population: {
      group: "Western North Atlantic fin whales", category: "VU", listing: "US Endangered Species Act: Endangered since 1970, as is the whole species",
      count: "6,802 from Florida to Newfoundland (2016)", trend: "unknown", trendNote: "too little data; signs of decline in the northern Gulf of St Lawrence",
      refs: [noaa("2023", "https://www.fisheries.noaa.gov/s3/2024-12/2023-sar-fin-whale-wna.pdf")],
    },
  },
  "blue-whale-channel-islands": {
    population: {
      group: "Eastern North Pacific blue whales", category: "EN", listing: "US Endangered Species Act: Endangered since 1970",
      count: "1,898 (2018)", trend: "unknown", trendNote: "possibly close to what the ecosystem can support (about 97% in 2013)",
      threats: "Ship strikes: an estimated 18 deaths a year, against a sustainable limit of 4.1.",
      refs: [noaa("2023", "https://www.fisheries.noaa.gov/s3/2024-12/2023-sar-blue-whale-enp.pdf")],
    },
  },
  "blue-whale-weddell-69s": { population: ANTARCTIC_BLUE },
  "blue-whale-weddell-59s": { population: ANTARCTIC_BLUE },
  "minke-whale-niihau": {
    population: {
      group: "Hawaiʻi minke whales", category: "LC", listing: "Not listed in the US", count: "438 (2017 survey, very uncertain)", trend: "unknown",
      refs: [noaa("2020", "https://media.fisheries.noaa.gov/2021-08/2020-Pacific-SARS-minke.pdf")],
    },
  },
  "dolphin-a": EILAT,
  "spinner-dolphin-palmyra": {
    note: "No population estimate exists for the spinner dolphins of Palmyra Atoll; NOAA's reports cover only the Hawaiian Islands and American Samoa.",
    noteRefs: [{ label: "NOAA stock assessment reports by species", url: "https://www.fisheries.noaa.gov/national/marine-mammal-protection/marine-mammal-stock-assessment-reports-species-stock" }],
  },
  "striped-dolphin-nwhi": {
    population: {
      group: "Hawaiʻi striped dolphins", category: "LC", listing: "Not listed in the US", count: "64,343 (2020)", trend: "unknown",
      trendNote: "estimates vary too much to show a trend", refs: [noaa("2023", "https://www.fisheries.noaa.gov/s3/2024-12/2023-sar-striped-dolphin-hawaii.pdf")],
    },
  },
  "rough-toothed-dolphin-kure": {
    population: {
      group: "Hawaiʻi rough-toothed dolphins", category: "LC", listing: "Not listed in the US", count: "83,915 (2020)", trend: "unknown",
      trendNote: "confidence intervals too broad to show a trend", threats: "Longline fishing: about 3 deaths or serious injuries a year inside Hawaiian waters (2017–2021).",
      refs: [noaa("2023", "https://www.fisheries.noaa.gov/s3/2024-12/2023-sar-rough-toothed-dolphin-hawaii.pdf")],
    },
  },
  "atlantic-spotted-dolphin-mid-atlantic": {
    population: {
      group: "Western North Atlantic spotted dolphins", category: "LC", listing: "Not listed in the US",
      count: "31,506 (2021), down from 50,978 in 2004", trend: "decreasing", trendNote: "a significant decrease since 2004, which may be a shift in distribution",
      refs: [noaa("2023", "https://www.fisheries.noaa.gov/s3/2024-12/2023-sar-atlantic-spotted-dolphin-wna.pdf")],
    },
  },
};

export const VOICE_IDS = Object.keys(VOICES);

/** The status a recording shows on the map and its chair: its population's where it has one. */
export function statusOf(source: Pick<Source, "id" | "species">): Status {
  return VOICES[source.id]?.population ?? SPECIES_STATUS[source.species];
}

/** Everything the voice card shows: the population, the species worldwide, and a note where a population has no figures. */
export function voiceInfo(source: Pick<Source, "id" | "species">): { population?: Status; species: Status; note?: string; noteRefs: Reference[] } {
  const voice = VOICES[source.id] ?? {};
  return { population: voice.population, species: SPECIES_STATUS[source.species], note: voice.note, noteRefs: voice.noteRefs ?? [] };
}

/** The most threatened status among several recordings, as one site shows it. */
export function mostThreatened(statuses: Status[]): Status | undefined {
  return statuses.reduce<Status | undefined>((worst, s) => !worst || SEVERITY.indexOf(s.category) > SEVERITY.indexOf(worst.category) ? s : worst, undefined);
}

/** One line for cards and tooltips: who, listing, count and trend. */
export function statusLine(status: Status): string {
  const trend = status.trend === "unknown" ? status.trendNote : `${TREND_WORD[status.trend]}${status.trendNote ? `, ${status.trendNote}` : ""}`;
  return [status.group, status.listing, status.count, trend].filter(Boolean).join(" · ");
}
