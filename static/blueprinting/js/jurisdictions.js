/**
 * Texas Jurisdiction Database
 * City-specific building code amendments, requirements, and constraints.
 * Based on 2025-2026 Texas building codes and local amendments.
 */

const JURISDICTIONS = {
  houston: {
    name: "Houston",
    population: 2_300_000,
    adoptedCode: "IRC 2021 with local amendments",
    energyCode: "IECC 2015",
    requiresPESealedFoundation: true,
    requiresSurvey: true,
    selfCertification: false,
    minLotSize: 3000, // SB 15 effective Sep 1 2025
    setbacks: {
      front: 25,
      rear: 5,
      sideInterior: 5,
      sideCorner: 10,
    },
    maxLotCoverage: 0.80,
    maxHeight: 35,
    permitRequirements: [
      "Texas registered survey or complete site plan",
      "Foundation plans with beam details and steel bar layout",
      "Floor plans with room dimensions",
      "IECC 2015 energy compliance documentation",
      "Structural calculations for spans > 16ft",
    ],
    foundationNotes: "PE-sealed foundation plans required for all new residential construction",
    localAmendments: [
      "No minimum parking requirements for residential (2024 amendment)",
      "ADU permitted on all single-family lots",
      "Rain sensor required on all irrigation systems",
    ],
    floodZone: true,
    floodRequirements: "Must comply with Chapter 19 floodplain regulations; BFE + 2ft freeboard",
  },

  austin: {
    name: "Austin",
    population: 1_000_000,
    adoptedCode: "IRC 2021 with local amendments",
    energyCode: "IECC 2021 (Austin Energy Code)",
    requiresPESealedFoundation: true,
    requiresSurvey: true,
    selfCertification: true,
    selfCertNote: "AI Pre-Check beta (Archistar) available; self-cert for Certified Building Designers and TX-licensed Architects",
    minLotSize: 3000,
    setbacks: {
      front: 25,
      rear: 10,
      sideInterior: 5,
      sideCorner: 15,
    },
    maxLotCoverage: 0.45,
    maxHeight: 35,
    permitRequirements: [
      "Site plan showing setbacks and impervious cover",
      "Foundation plan (PE sealed)",
      "Floor plans and elevations",
      "Energy compliance (Austin Energy Code)",
      "Tree survey if lot has protected trees",
    ],
    foundationNotes: "PE-sealed foundation plans required; geotechnical report recommended for expansive clay soils",
    localAmendments: [
      "Impervious cover limits apply (varies by zoning)",
      "Heritage tree ordinance — survey required",
      "Rainwater harvesting incentives available",
      "HOME Phase 2 zoning reform — up to 3 units on single-family lots",
    ],
    floodZone: true,
    floodRequirements: "Atlas 14 flood standards; compensating cut-and-fill required in floodplain",
  },

  dallas: {
    name: "Dallas",
    population: 1_300_000,
    adoptedCode: "IRC 2021 with local amendments",
    energyCode: "IECC 2015",
    requiresPESealedFoundation: true,
    requiresSurvey: true,
    selfCertification: false,
    minLotSize: 3000,
    setbacks: {
      front: 25,
      rear: 5,
      sideInterior: 5,
      sideCorner: 15,
    },
    maxLotCoverage: 0.60,
    maxHeight: 36,
    permitRequirements: [
      "Plat or survey",
      "Foundation plan (PE sealed)",
      "Floor plans with dimensions",
      "Elevations (all sides)",
      "Energy compliance documentation",
    ],
    foundationNotes: "PE-sealed foundation plan required; soil report may be required",
    localAmendments: [
      "Accessory dwelling units permitted in single-family zones",
      "Residential proximity slope requirements near highways",
    ],
    floodZone: true,
    floodRequirements: "FEMA floodplain compliance required; 2ft freeboard above BFE",
  },

  san_antonio: {
    name: "San Antonio",
    population: 1_500_000,
    adoptedCode: "IRC 2021 with local amendments",
    energyCode: "IECC 2015",
    requiresPESealedFoundation: true,
    requiresSurvey: true,
    selfCertification: false,
    minLotSize: 3000,
    setbacks: {
      front: 25,
      rear: 5,
      sideInterior: 5,
      sideCorner: 10,
    },
    maxLotCoverage: 0.65,
    maxHeight: 35,
    permitRequirements: [
      "Property survey",
      "Foundation plan with PE seal",
      "Architectural plans (floor plans, elevations)",
      "Energy code compliance",
      "SAWS water/sewer availability letter",
    ],
    foundationNotes: "PE-sealed foundation required; Edwards Aquifer zone may require additional review",
    localAmendments: [
      "Edwards Aquifer protection zone impervious cover limits",
      "Historic district review for designated areas",
      "Water conservation fixtures required (SAWS)",
    ],
    floodZone: true,
    floodRequirements: "FEMA floodplain compliance; no-rise certification for floodway",
  },

  fort_worth: {
    name: "Fort Worth",
    population: 960_000,
    adoptedCode: "IRC 2021 with local amendments",
    energyCode: "IECC 2015",
    requiresPESealedFoundation: true,
    requiresSurvey: true,
    selfCertification: false,
    minLotSize: 3000,
    setbacks: {
      front: 25,
      rear: 5,
      sideInterior: 5,
      sideCorner: 15,
    },
    maxLotCoverage: 0.55,
    maxHeight: 35,
    permitRequirements: [
      "Survey or plat",
      "Foundation plan (PE sealed)",
      "Floor plans and elevations",
      "Energy compliance",
    ],
    foundationNotes: "PE-sealed foundation required for new construction",
    localAmendments: [
      "Neighborhood conservation overlay districts may impose additional restrictions",
    ],
    floodZone: true,
    floodRequirements: "Trinity River Vision floodplain requirements apply in affected areas",
  },

  unincorporated: {
    name: "Unincorporated Area (County)",
    population: 0,
    adoptedCode: "IRC 2021 (state minimum)",
    energyCode: "IECC 2015 (state minimum)",
    requiresPESealedFoundation: false,
    requiresSurvey: false,
    selfCertification: false,
    minLotSize: null,
    setbacks: {
      front: 0,
      rear: 0,
      sideInterior: 0,
      sideCorner: 0,
    },
    maxLotCoverage: 1.0,
    maxHeight: null,
    permitRequirements: [
      "On-site sewage facility (OSSF) permit if no municipal sewer",
      "Floodplain development permit if in FEMA flood zone",
    ],
    foundationNotes: "No PE requirement for single-family under state exemption thresholds",
    localAmendments: [
      "No building permit required in most unincorporated areas",
      "County may enforce floodplain and OSSF regulations only",
    ],
    floodZone: false,
    floodRequirements: "FEMA requirements apply regardless of incorporation status",
  },
};

// Building type definitions
const BUILDING_TYPES = {
  "single-family": {
    label: "Single-Family Residence",
    maxUnits: 1,
    maxStoriesArchExempt: 3,
    maxStoriesEngExempt: 2,
    description: "Detached single-family dwelling",
  },
  duplex: {
    label: "Duplex",
    maxUnits: 2,
    maxStoriesArchExempt: 3,
    maxStoriesEngExempt: 2,
    description: "Two-family dwelling",
  },
  triplex: {
    label: "Triplex",
    maxUnits: 3,
    maxStoriesArchExempt: 2,
    maxStoriesEngExempt: 2,
    description: "Three-family dwelling (requires municipality with building code)",
  },
  fourplex: {
    label: "Fourplex",
    maxUnits: 4,
    maxStoriesArchExempt: 2,
    maxStoriesEngExempt: 2,
    description: "Four-family dwelling (requires municipality with building code)",
  },
  adu: {
    label: "Accessory Dwelling Unit",
    maxUnits: 1,
    maxStoriesArchExempt: 2,
    maxStoriesEngExempt: 2,
    description: "Secondary dwelling on single-family lot",
  },
  garage: {
    label: "Detached Garage / Storage",
    maxUnits: 0,
    maxStoriesArchExempt: 3,
    maxStoriesEngExempt: 2,
    description: "Accessory structure (no dwelling units)",
  },
  townhome: {
    label: "Townhome",
    maxUnits: 1,
    maxStoriesArchExempt: 3,
    maxStoriesEngExempt: 2,
    description: "Attached single-family (SB 15 — min 3,000 sqft lot in large cities)",
  },
};

// Room type definitions with IRC minimum requirements
const ROOM_TYPES = {
  living: {
    label: "Living Room",
    color: "#4a90d9",
    minArea: 120,
    minDimension: 10,
    requiresWindow: true,
    requiresEgress: false,
  },
  bedroom: {
    label: "Bedroom",
    color: "#7b68ee",
    minArea: 70,
    minDimension: 7,
    requiresWindow: true,
    requiresEgress: true,
    egressMinWidth: 20, // inches
    egressMinHeight: 24, // inches
    egressMinArea: 5.7, // sqft
    egressMaxSillHeight: 44, // inches
  },
  kitchen: {
    label: "Kitchen",
    color: "#e8a838",
    minArea: 50,
    minDimension: 5,
    requiresWindow: false,
    requiresEgress: false,
  },
  bathroom: {
    label: "Bathroom",
    color: "#50c878",
    minArea: 35,
    minDimension: 5,
    requiresWindow: false,
    requiresEgress: false,
    requiresVentilation: true,
  },
  dining: {
    label: "Dining Room",
    color: "#d4956a",
    minArea: 80,
    minDimension: 8,
    requiresWindow: false,
    requiresEgress: false,
  },
  garage_room: {
    label: "Garage",
    color: "#888888",
    minArea: 200,
    minDimension: 10,
    requiresWindow: false,
    requiresEgress: false,
  },
  laundry: {
    label: "Laundry",
    color: "#9dc183",
    minArea: 20,
    minDimension: 4,
    requiresWindow: false,
    requiresEgress: false,
  },
  closet: {
    label: "Closet",
    color: "#c4a882",
    minArea: 6,
    minDimension: 2,
    requiresWindow: false,
    requiresEgress: false,
  },
  hallway: {
    label: "Hallway",
    color: "#b0b0b0",
    minArea: 0,
    minDimension: 3,
    requiresWindow: false,
    requiresEgress: false,
  },
  utility: {
    label: "Utility / Mechanical",
    color: "#a0a0a0",
    minArea: 12,
    minDimension: 3,
    requiresWindow: false,
    requiresEgress: false,
  },
  porch: {
    label: "Porch / Patio",
    color: "#8fbc8f",
    minArea: 0,
    minDimension: 4,
    requiresWindow: false,
    requiresEgress: false,
    exterior: true,
  },
};

// Texas state-level constants
const TX_STATE = {
  architectExemptionMaxUnits: 4,
  architectExemptionMaxStories_withCode: 2, // 3-4 units needs municipality with building code
  architectExemptionMaxStories_2unit: 3, // 1-2 units max 3 stories
  engineerExemptionMaxUnits: 4,
  engineerExemptionMaxStories: 2,
  peClearSpanThreshold: 24, // feet
  peSingleStoryAreaThreshold: 5000, // sqft
  peMultiStoryRequired: true,
  minCeilingHeight: 7, // feet (IRC R305.1)
  minHabitableRoomArea: 70, // sqft (IRC R304.1)
  minHabitableRoomDimension: 7, // feet (IRC R304.2)
  minHallwayWidth: 3, // feet (IRC R311.6)
  minStairWidth: 36, // inches (IRC R311.7.1)
  minDoorWidth: 32, // inches egress door clear width
  minDoorHeight: 78, // inches
  sb15MinLotSize: 3000, // SB 15 effective Sep 1 2025
  sb15PopulationThreshold: 250000, // cities above this population
};
