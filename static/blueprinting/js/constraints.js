/**
 * Texas Residential Blueprinting Constraint Engine
 *
 * Implements the seven constraint layers (L₁–L₇) derived from
 * Texas Occupations Code, Engineering Practice Act, IRC, IECC,
 * and municipal amendments.
 *
 * Each constraint returns: { id, name, status, message, witness, layer }
 * where status is "pass" | "warn" | "fail"
 */

class ConstraintEngine {
  constructor() {
    this.results = [];
  }

  /**
   * Run all constraints against a project.
   * @param {object} project - The full project data model
   * @returns {Array} Array of constraint results
   */
  check(project) {
    this.results = [];
    const jurisdiction = JURISDICTIONS[project.jurisdiction] || JURISDICTIONS.unincorporated;
    const buildingType = BUILDING_TYPES[project.buildingType] || BUILDING_TYPES["single-family"];

    this.checkL1_ArchitectExemption(project, jurisdiction, buildingType);
    this.checkL2_PERequirement(project, jurisdiction, buildingType);
    this.checkL3_FoundationEngineering(project, jurisdiction);
    this.checkL4_IRCCompliance(project, jurisdiction);
    this.checkL5_EnergyCode(project, jurisdiction);
    this.checkL6_LocalAmendments(project, jurisdiction);
    this.checkL7_SurveySetback(project, jurisdiction);

    return this.results;
  }

  /**
   * L₁: Architect Exemption (Texas Occupations Code §1051.606)
   */
  checkL1_ArchitectExemption(project, jurisdiction, buildingType) {
    const units = buildingType.maxUnits;
    const stories = project.stories || 1;

    // Check unit count
    if (units > TX_STATE.architectExemptionMaxUnits) {
      this.results.push({
        id: "L1-units",
        name: "Architect Exemption",
        layer: 1,
        status: "fail",
        message: "Building exceeds 4 dwelling units — licensed architect required",
        witness: `${buildingType.label} has ${units} units; Texas exemption caps at ${TX_STATE.architectExemptionMaxUnits} units`,
        resolution: "Engage a Texas-licensed architect for buildings with more than 4 units",
      });
      return;
    }

    // Check story limits based on unit count
    if (units <= 2 && stories > TX_STATE.architectExemptionMaxStories_2unit) {
      this.results.push({
        id: "L1-stories",
        name: "Architect Exemption",
        layer: 1,
        status: "fail",
        message: `${stories}-story ${buildingType.label} exceeds architect exemption limit`,
        witness: `1-2 family dwellings exempt up to ${TX_STATE.architectExemptionMaxStories_2unit} stories; you have ${stories}`,
        resolution: "Reduce to 3 stories or fewer, or engage a licensed architect",
      });
      return;
    }

    if (units > 2 && stories > TX_STATE.architectExemptionMaxStories_withCode) {
      this.results.push({
        id: "L1-stories-multi",
        name: "Architect Exemption",
        layer: 1,
        status: "fail",
        message: `${stories}-story ${buildingType.label} exceeds architect exemption for 3-4 unit buildings`,
        witness: `3-4 unit buildings exempt only up to ${TX_STATE.architectExemptionMaxStories_withCode} stories in a municipality with a building code; you have ${stories}`,
        resolution: "Reduce to 2 stories or engage a licensed architect",
      });
      return;
    }

    // 3-4 units requires municipality with building code
    if (units > 2 && jurisdiction.name === "Unincorporated Area (County)") {
      this.results.push({
        id: "L1-municipality",
        name: "Architect Exemption",
        layer: 1,
        status: "warn",
        message: "3-4 unit exemption requires municipality with adopted building code",
        witness: `${buildingType.label} in unincorporated area — the exemption for 3-4 unit buildings only applies in municipalities that have adopted a building or residential code`,
        resolution: "Verify your area has adopted a building code, or engage a licensed architect",
      });
      return;
    }

    this.results.push({
      id: "L1",
      name: "Architect Exemption",
      layer: 1,
      status: "pass",
      message: `${buildingType.label} (${stories} story) qualifies for architect exemption under §1051.606`,
      witness: null,
      resolution: null,
    });
  }

  /**
   * L₂: PE Requirement (Texas Engineering Practice Act §1001.056)
   */
  checkL2_PERequirement(project, jurisdiction, buildingType) {
    const stories = project.stories || 1;
    const units = buildingType.maxUnits;
    const totalArea = this.calcTotalArea(project);
    const maxSpan = this.calcMaxSpan(project);

    const issues = [];

    // Multi-story check
    if (stories > TX_STATE.engineerExemptionMaxStories) {
      issues.push({
        id: "L2-stories",
        name: "PE Requirement — Stories",
        layer: 2,
        status: "fail",
        message: `${stories}-story building requires PE-sealed structural plans`,
        witness: `Engineering exemption limited to ${TX_STATE.engineerExemptionMaxStories} stories; you have ${stories}`,
        resolution: "Engage a licensed Professional Engineer for structural design",
      });
    }

    // Clear span check
    if (maxSpan > TX_STATE.peClearSpanThreshold) {
      issues.push({
        id: "L2-span",
        name: "PE Requirement — Span",
        layer: 2,
        status: "fail",
        message: `Clear span of ${maxSpan.toFixed(1)}ft exceeds ${TX_STATE.peClearSpanThreshold}ft — PE seal required`,
        witness: `A room or structural bay has a clear span of ${maxSpan.toFixed(1)}ft on the narrow dimension; the engineering exemption caps at ${TX_STATE.peClearSpanThreshold}ft`,
        resolution: `Reduce the narrowest room dimension to ≤${TX_STATE.peClearSpanThreshold}ft, or add a supporting wall/beam, or engage a PE`,
      });
    }

    // Single-story area check
    if (stories === 1 && totalArea > TX_STATE.peSingleStoryAreaThreshold) {
      issues.push({
        id: "L2-area",
        name: "PE Requirement — Area",
        layer: 2,
        status: "fail",
        message: `Single-story floor area of ${totalArea.toFixed(0)} sqft exceeds ${TX_STATE.peSingleStoryAreaThreshold} sqft — PE seal required`,
        witness: `Single-story buildings over ${TX_STATE.peSingleStoryAreaThreshold} sqft require PE-sealed structural plans`,
        resolution: `Reduce total floor area to ≤${TX_STATE.peSingleStoryAreaThreshold} sqft or engage a PE`,
      });
    }

    // Unit count check
    if (units > TX_STATE.engineerExemptionMaxUnits) {
      issues.push({
        id: "L2-units",
        name: "PE Requirement — Units",
        layer: 2,
        status: "fail",
        message: `${units} dwelling units exceeds engineering exemption limit of ${TX_STATE.engineerExemptionMaxUnits}`,
        witness: `Engineering exemption limited to ${TX_STATE.engineerExemptionMaxUnits} units per building`,
        resolution: "Engage a licensed Professional Engineer",
      });
    }

    if (issues.length > 0) {
      this.results.push(...issues);
    } else {
      // Warn about span approaching threshold
      if (maxSpan > TX_STATE.peClearSpanThreshold * 0.85) {
        this.results.push({
          id: "L2-span-warn",
          name: "PE Requirement — Span",
          layer: 2,
          status: "warn",
          message: `Max span ${maxSpan.toFixed(1)}ft is approaching the ${TX_STATE.peClearSpanThreshold}ft PE threshold`,
          witness: `Room span at ${((maxSpan / TX_STATE.peClearSpanThreshold) * 100).toFixed(0)}% of the limit`,
          resolution: "Consider adding interior support if expanding this room",
        });
      } else {
        this.results.push({
          id: "L2",
          name: "PE Requirement",
          layer: 2,
          status: "pass",
          message: `Design within engineering exemption limits (${totalArea.toFixed(0)} sqft, ${maxSpan.toFixed(1)}ft max span, ${stories} story)`,
          witness: null,
          resolution: null,
        });
      }
    }
  }

  /**
   * L₃: Foundation Engineering
   */
  checkL3_FoundationEngineering(project, jurisdiction) {
    if (jurisdiction.requiresPESealedFoundation) {
      this.results.push({
        id: "L3",
        name: "Foundation Engineering",
        layer: 3,
        status: "warn",
        message: `${jurisdiction.name} requires PE-sealed foundation plans for new construction`,
        witness: jurisdiction.foundationNotes,
        resolution: "Budget for a foundation engineer (PE) — this is standard in most Texas cities and typically costs $500-$2,000",
      });
    } else {
      this.results.push({
        id: "L3",
        name: "Foundation Engineering",
        layer: 3,
        status: "pass",
        message: "No PE foundation requirement for this jurisdiction/building type",
        witness: jurisdiction.foundationNotes || "State exemption thresholds apply",
        resolution: null,
      });
    }
  }

  /**
   * L₄: IRC Compliance
   */
  checkL4_IRCCompliance(project, jurisdiction) {
    const rooms = project.rooms || [];
    const issues = [];

    for (const room of rooms) {
      const roomType = ROOM_TYPES[room.type];
      if (!roomType) continue;

      const area = room.width * room.height;
      const minDim = Math.min(room.width, room.height);

      // Minimum area check for habitable rooms
      if (roomType.minArea > 0 && area < roomType.minArea) {
        issues.push({
          id: `L4-area-${room.id}`,
          name: "IRC — Room Area",
          layer: 4,
          status: "fail",
          message: `${roomType.label} "${room.label || room.id}" is ${area.toFixed(0)} sqft — minimum is ${roomType.minArea} sqft`,
          witness: `IRC R304.1 requires habitable rooms to be at least ${roomType.minArea} sqft; this room is ${area.toFixed(1)} sqft (${room.width}' × ${room.height}')`,
          resolution: `Increase room to at least ${roomType.minArea} sqft`,
        });
      }

      // Minimum dimension check
      if (roomType.minDimension > 0 && minDim < roomType.minDimension) {
        issues.push({
          id: `L4-dim-${room.id}`,
          name: "IRC — Room Dimension",
          layer: 4,
          status: "fail",
          message: `${roomType.label} "${room.label || room.id}" narrow dimension is ${minDim.toFixed(1)}ft — minimum is ${roomType.minDimension}ft`,
          witness: `IRC R304.2: no habitable room dimension less than ${roomType.minDimension}ft; this room's narrow side is ${minDim.toFixed(1)}ft`,
          resolution: `Widen room to at least ${roomType.minDimension}ft on all sides`,
        });
      }

      // Egress window check for bedrooms
      if (roomType.requiresEgress && room.type === "bedroom") {
        if (!room.hasEgressWindow) {
          issues.push({
            id: `L4-egress-${room.id}`,
            name: "IRC — Egress Window",
            layer: 4,
            status: "warn",
            message: `Bedroom "${room.label || room.id}" needs an egress window (min 5.7 sqft opening, max 44" sill height)`,
            witness: `IRC R310.1 requires emergency escape openings in sleeping rooms`,
            resolution: "Add an egress-compliant window to this bedroom",
          });
        }
      }
    }

    // Check minimum bedroom count
    const bedrooms = rooms.filter(r => r.type === "bedroom");
    if (rooms.length > 0 && bedrooms.length === 0 && project.buildingType !== "garage") {
      issues.push({
        id: "L4-no-bedroom",
        name: "IRC — Habitable Space",
        layer: 4,
        status: "warn",
        message: "No bedrooms in plan — dwelling requires at least one sleeping room",
        witness: "IRC R304 requires habitable space including sleeping rooms in dwellings",
        resolution: "Add at least one bedroom to the floor plan",
      });
    }

    // Check for bathroom
    const bathrooms = rooms.filter(r => r.type === "bathroom");
    if (rooms.length > 0 && bathrooms.length === 0 && project.buildingType !== "garage") {
      issues.push({
        id: "L4-no-bathroom",
        name: "IRC — Sanitary Facilities",
        layer: 4,
        status: "warn",
        message: "No bathroom in plan — dwelling requires sanitary facilities",
        witness: "IRC P2701: each dwelling must have at minimum one water closet, one lavatory, one bathtub or shower",
        resolution: "Add at least one bathroom to the floor plan",
      });
    }

    // Hallway width check
    const hallways = rooms.filter(r => r.type === "hallway");
    for (const hall of hallways) {
      const minDim = Math.min(hall.width, hall.height);
      if (minDim < TX_STATE.minHallwayWidth) {
        issues.push({
          id: `L4-hall-${hall.id}`,
          name: "IRC — Hallway Width",
          layer: 4,
          status: "fail",
          message: `Hallway "${hall.label || hall.id}" is ${minDim.toFixed(1)}ft wide — minimum is ${TX_STATE.minHallwayWidth}ft`,
          witness: `IRC R311.6: hallways shall be not less than ${TX_STATE.minHallwayWidth}ft in width`,
          resolution: `Widen hallway to at least ${TX_STATE.minHallwayWidth}ft`,
        });
      }
    }

    if (issues.length > 0) {
      this.results.push(...issues);
    } else if (rooms.length > 0) {
      this.results.push({
        id: "L4",
        name: "IRC Compliance",
        layer: 4,
        status: "pass",
        message: "All rooms meet IRC minimum requirements",
        witness: null,
        resolution: null,
      });
    } else {
      this.results.push({
        id: "L4",
        name: "IRC Compliance",
        layer: 4,
        status: "warn",
        message: "No rooms defined yet — add rooms to check IRC compliance",
        witness: null,
        resolution: "Use the room tools to add rooms to your floor plan",
      });
    }
  }

  /**
   * L₅: Energy Code (IECC)
   */
  checkL5_EnergyCode(project, jurisdiction) {
    const totalArea = this.calcTotalArea(project);
    const windowArea = this.calcWindowArea(project);
    const wallArea = this.calcExteriorWallArea(project);

    // Window-to-wall ratio check (IECC limit is typically 15-30% depending on zone)
    if (wallArea > 0 && windowArea > 0) {
      const wwr = windowArea / wallArea;
      if (wwr > 0.30) {
        this.results.push({
          id: "L5-wwr",
          name: "Energy Code — Window Ratio",
          layer: 5,
          status: "warn",
          message: `Window-to-wall ratio is ${(wwr * 100).toFixed(0)}% — may exceed ${jurisdiction.energyCode} limits without trade-off`,
          witness: `IECC prescriptive path typically limits glazing to 15-30% of wall area; REScheck trade-off analysis may be required`,
          resolution: "Reduce window area or use REScheck to demonstrate compliance via trade-offs",
        });
      } else {
        this.results.push({
          id: "L5",
          name: "Energy Code",
          layer: 5,
          status: "pass",
          message: `Window-to-wall ratio ${(wwr * 100).toFixed(0)}% within ${jurisdiction.energyCode} prescriptive limits`,
          witness: null,
          resolution: null,
        });
      }
    } else {
      this.results.push({
        id: "L5",
        name: "Energy Code",
        layer: 5,
        status: "pass",
        message: `${jurisdiction.energyCode} applies — ensure envelope meets prescriptive requirements or run REScheck`,
        witness: `Texas Climate Zone 2-3; R-13 wall insulation, R-38 ceiling insulation typical`,
        resolution: null,
      });
    }
  }

  /**
   * L₆: Local Amendments
   */
  checkL6_LocalAmendments(project, jurisdiction) {
    const totalArea = this.calcTotalArea(project);
    const lotArea = (project.lotWidth || 50) * (project.lotDepth || 100);

    // Lot coverage check
    if (jurisdiction.maxLotCoverage && jurisdiction.maxLotCoverage < 1.0) {
      const coverage = totalArea / lotArea;
      if (coverage > jurisdiction.maxLotCoverage) {
        this.results.push({
          id: "L6-coverage",
          name: "Local — Lot Coverage",
          layer: 6,
          status: "fail",
          message: `Building coverage ${(coverage * 100).toFixed(0)}% exceeds ${jurisdiction.name} maximum of ${(jurisdiction.maxLotCoverage * 100).toFixed(0)}%`,
          witness: `Total building footprint: ${totalArea.toFixed(0)} sqft on ${lotArea.toFixed(0)} sqft lot = ${(coverage * 100).toFixed(1)}% coverage`,
          resolution: `Reduce building footprint to ≤${(lotArea * jurisdiction.maxLotCoverage).toFixed(0)} sqft or add a second story`,
        });
      } else {
        this.results.push({
          id: "L6-coverage",
          name: "Local — Lot Coverage",
          layer: 6,
          status: "pass",
          message: `Lot coverage ${(coverage * 100).toFixed(0)}% within ${jurisdiction.name} limit of ${(jurisdiction.maxLotCoverage * 100).toFixed(0)}%`,
          witness: null,
          resolution: null,
        });
      }
    }

    // Height check
    if (jurisdiction.maxHeight) {
      const estHeight = (project.stories || 1) * 10 + 3; // rough: 10ft per story + 3ft roof
      if (estHeight > jurisdiction.maxHeight) {
        this.results.push({
          id: "L6-height",
          name: "Local — Height",
          layer: 6,
          status: "fail",
          message: `Estimated height ~${estHeight}ft exceeds ${jurisdiction.name} limit of ${jurisdiction.maxHeight}ft`,
          witness: `${project.stories} stories × ~10ft + roof = ~${estHeight}ft`,
          resolution: `Reduce stories or floor-to-floor height`,
        });
      }
    }

    // Lot size check (SB 15)
    if (jurisdiction.minLotSize && lotArea < jurisdiction.minLotSize) {
      this.results.push({
        id: "L6-lotsize",
        name: "Local — Lot Size",
        layer: 6,
        status: "fail",
        message: `Lot area ${lotArea.toFixed(0)} sqft below ${jurisdiction.name} minimum of ${jurisdiction.minLotSize} sqft`,
        witness: `SB 15 (eff. Sep 1, 2025) sets minimum at ${jurisdiction.minLotSize} sqft for cities over ${TX_STATE.sb15PopulationThreshold.toLocaleString()} population`,
        resolution: `Lot must be at least ${jurisdiction.minLotSize} sqft`,
      });
    }

    // Flood zone check
    if (jurisdiction.floodZone) {
      this.results.push({
        id: "L6-flood",
        name: "Local — Flood Zone",
        layer: 6,
        status: "warn",
        message: `${jurisdiction.name} has flood zone requirements — verify your lot's flood designation`,
        witness: jurisdiction.floodRequirements,
        resolution: "Check FEMA flood map for your lot; additional requirements may apply",
      });
    }

    // Show local amendments as informational
    if (jurisdiction.localAmendments && jurisdiction.localAmendments.length > 0) {
      this.results.push({
        id: "L6-info",
        name: "Local Amendments",
        layer: 6,
        status: "pass",
        message: `${jurisdiction.name} local amendments noted`,
        witness: jurisdiction.localAmendments.join("; "),
        resolution: null,
      });
    }
  }

  /**
   * L₇: Survey & Setback
   */
  checkL7_SurveySetback(project, jurisdiction) {
    // Survey requirement
    if (jurisdiction.requiresSurvey && !project.surveyUploaded) {
      this.results.push({
        id: "L7-survey",
        name: "Survey Required",
        layer: 7,
        status: "warn",
        message: `${jurisdiction.name} requires a registered survey or site plan for permit`,
        witness: "Survey must show property boundaries, easements, and existing structures",
        resolution: "Upload a survey or mark the survey as provided in project settings",
      });
    }

    // Setback checks
    const rooms = project.rooms || [];
    if (rooms.length > 0) {
      const setbacks = jurisdiction.setbacks;
      const lotW = project.lotWidth || 50;
      const lotD = project.lotDepth || 100;

      // Find building bounding box
      let minX = Infinity, maxX = -Infinity;
      let minY = Infinity, maxY = -Infinity;
      for (const room of rooms) {
        if (ROOM_TYPES[room.type] && ROOM_TYPES[room.type].exterior) continue;
        minX = Math.min(minX, room.x);
        maxX = Math.max(maxX, room.x + room.width);
        minY = Math.min(minY, room.y);
        maxY = Math.max(maxY, room.y + room.height);
      }

      if (minX !== Infinity) {
        const buildableLeft = setbacks.sideInterior;
        const buildableRight = lotW - setbacks.sideInterior;
        const buildableFront = setbacks.front;
        const buildableRear = lotD - setbacks.rear;

        const violations = [];

        if (minX < buildableLeft) {
          violations.push(`Left side: building at ${minX.toFixed(1)}ft, setback requires ${buildableLeft}ft`);
        }
        if (maxX > buildableRight) {
          violations.push(`Right side: building extends to ${maxX.toFixed(1)}ft, max is ${buildableRight.toFixed(1)}ft (${setbacks.sideInterior}ft setback from ${lotW}ft lot)`);
        }
        if (minY < buildableFront) {
          violations.push(`Front: building at ${minY.toFixed(1)}ft from front, setback requires ${buildableFront}ft`);
        }
        if (maxY > buildableRear) {
          violations.push(`Rear: building extends to ${maxY.toFixed(1)}ft, max is ${buildableRear.toFixed(1)}ft (${setbacks.rear}ft setback from ${lotD}ft lot)`);
        }

        if (violations.length > 0) {
          this.results.push({
            id: "L7-setback",
            name: "Setback Violation",
            layer: 7,
            status: "fail",
            message: `Building violates ${jurisdiction.name} setback requirements`,
            witness: violations.join("\n"),
            resolution: "Move or resize building to fit within the buildable area (shown as dashed lines on the canvas)",
          });
        } else {
          this.results.push({
            id: "L7-setback",
            name: "Setbacks",
            layer: 7,
            status: "pass",
            message: "Building within all setback lines",
            witness: `Front: ${setbacks.front}ft, Rear: ${setbacks.rear}ft, Sides: ${setbacks.sideInterior}ft`,
            resolution: null,
          });
        }
      }
    }
  }

  // ── Utility calculations ──

  calcTotalArea(project) {
    return (project.rooms || [])
      .filter(r => !ROOM_TYPES[r.type]?.exterior)
      .reduce((sum, r) => sum + r.width * r.height, 0);
  }

  calcMaxSpan(project) {
    return (project.rooms || [])
      .filter(r => !ROOM_TYPES[r.type]?.exterior)
      .reduce((max, r) => Math.max(max, Math.min(r.width, r.height)), 0);
  }

  calcWindowArea(project) {
    return (project.rooms || [])
      .reduce((sum, r) => sum + (r.windowArea || 0), 0);
  }

  calcExteriorWallArea(project) {
    if (!project.rooms || project.rooms.length === 0) return 0;
    const ceilingH = 9; // assume 9ft ceilings
    // Rough: perimeter of bounding box × ceiling height
    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    for (const room of project.rooms) {
      if (ROOM_TYPES[room.type]?.exterior) continue;
      minX = Math.min(minX, room.x);
      maxX = Math.max(maxX, room.x + room.width);
      minY = Math.min(minY, room.y);
      maxY = Math.max(maxY, room.y + room.height);
    }
    if (minX === Infinity) return 0;
    const perimeter = 2 * ((maxX - minX) + (maxY - minY));
    return perimeter * ceilingH;
  }

  // Summary helpers
  static summarize(results) {
    const fails = results.filter(r => r.status === "fail");
    const warns = results.filter(r => r.status === "warn");
    const passes = results.filter(r => r.status === "pass");
    return { fails, warns, passes, total: results.length };
  }

  static worstStatus(results) {
    if (results.some(r => r.status === "fail")) return "fail";
    if (results.some(r => r.status === "warn")) return "warn";
    return "pass";
  }
}
