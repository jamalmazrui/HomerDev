# Research and Validation

## Search sequence

1. Search organization + year + convention; verify dates, property, address, and current content. A page path or heading alone is insufficient.
2. Search organizer site for orientation, walking guide, travel guide, hotel layout, navigating the hotel, venue access, dog relief, tactile map, and program.
3. Search the hotel's official meetings/events and accessibility pages; follow floor-plan and brochure links. Distinguish room-only drawings from a connected property plan.
4. Search Braille Forum and Braille Monitor with the hotel's name, nearby city, and current/prior years. Use historical articles for writing methods unless venue continuity is confirmed. Search official affiliate mailing-list archives and newsletters where national pages are blocked.
5. Search blind-authored video/audio walkthroughs and transcripts. Attribute opinions and check whether the author visited the same property and floor.
6. Search current app listings and blind-user reviews separately; reconcile price changes and hardware requirements.

## Audience and writing

Default public convention guides to all attendees. Keep personal schedules and device assumptions only in a guide explicitly for one traveler. Produce an attendee guide (about 1,500 words or fewer, roughly ninth-grade language) and a separate organizer worksheet. Put provenance, filenames, private senders, source conflicts, and the full field-check list in the worksheet. Explain short status tags once; do not repeat generic cautions after every destination.

## Source record

For every material source record title, author/organization, event/property, date or unknown date, URL or uploaded filename, pages/sections inspected, supported claims, conflicts, and last access date. Avoid redistributing whole copyrighted guides when original synthesis and links suffice.

## Floor-plan interpretation

- Render at readable resolution. Enlarge symbols, doors, ramps, stairs, and elevator landings. OCR when needed, then verify visually.
- Establish floors, north arrow if present, scale if present, main entrance, reception, elevators, lobbies, corridors, public restrooms, meeting rooms, service spaces, outside doors, and relief area.
- Treat room label placement as a label, not an entrance. Treat emergency arrows as evacuation information, not proof of an everyday route.
- Build a graph of spaces connected by clearly drawn public doors/passages. Record unresolved edges. Do not route through kitchens, offices, storage, or service laundries merely because two rooms touch.
- Note stair/ramp alternatives without inferring a step-free connection where the drawing stops short. Diagram dimensions are not measured walking distances.
- Do not merge isolated room diagrams into a whole-hotel floor plan. Preserve uncertainty about current movable walls, furniture, and event entrances.

## Field-check questions

Ask a checker to record starting position and facing direction, each junction and turn, landmark location, actual entrance, accessible alternatives, floor changes, endpoint cue, reverse route, after-hours locks, and current temporary obstructions. Ask a cane user and a guide dog handler to review when feasible; do not claim either review occurred if it did not.

Prioritize: arrival-to-desk; desk-to-elevators; elevators-to-convention hub; hub-to-session/exhibits; restrooms; meals; guide dog relief and return; transport pickup. Add pool, fitness, business center, shop, and guest laundry only if present and relevant.

Also check guest-floor numbering, accessible elevator controls and announcements, different banks, shuttle stop at each property, and the pedestrian route from drop-off to registration. When the main hotel sells out, treat overflow orientation as a separate subtask. Check neighborhood sidewalk/crossing continuity before calling a restaurant walkable. Missing information can remain missing after a documented public-source search; do not turn unknowns into many pages of attendee “ask staff” instructions.

## Date and time check

Verify every printed weekday/date pair with a calendar. Use the venue's time zone at the actual event dates, not the current offset. Check a daylight-saving transition within a week of the event and split time zones when necessary. Regression case: November 6–8, 2026 is Friday–Sunday in Eastern Standard Time; the clock change is November 1, not November 8. October 22–25, 2026 is Thursday–Sunday in Eastern Daylight Time.

## Acceptance checks

- Event/property/year identity and intended audience are consistent throughout.
- All weekdays, dates, time-zone labels, and clock-change statements were checked.
- Attendee guide and organizer worksheet are separate; main guide is concise.
- No private sender, uploaded-file inventory, or personal device appears in a public guide.
- Short tags are used; common cautions are not repeated needlessly.
- iPhone-only suggestions have an Android alternative or an explicit no-equivalent note.
- Guest floors, shuttle stops, overflow connections, and nearby food were considered.
- BOM/CRLF preferences are met for user documents; SKILL.md has no BOM.
- Every actual turn has a justified orientation.
- Each usable route includes a supported confirmation cue and recovery point where known; no sensory clue was inferred from a diagram.
- Boarding, drop-off, exact entrance, and destination handoffs are either connected or explicitly incomplete.
- Static provider facts, live changes, and traveler reports remain distinguishable, with dates.
- App links lead to the correct current service, with no unrelated redirects or substituted app IDs.
- Coverage of venue-dependent technology is verified for the property or stated unknown.
- No route hides an unresolved stair/door/corridor connection.
- Provisional and incomplete routes are labeled locally.
- No route implies emergency-only doors permit reentry.
- App recommendations have both actual blind-user experience and current cost/platform evidence.
- Sources are linked; unknown dates and historical examples are explicit.
- TOC anchors work; no raw tool citations or placeholders remain in the attendee guide.
- Archive opens and contains the requested filenames and complete skill resources.

## Evaluation prompts

Use raw tasks such as: “Use this skill to write a guide from these two convention programs and this floor plan,” including a previous-year program and a mismatched hotel map. Judge whether the output detects identity conflicts without being prompted. Test an isolated meeting-room plan and confirm that it does not generate hotel corridor turns. Test a phone lacking LiDAR and confirm that dependent features are not recommended as available.

Test a public program request mentioning a single traveler's phone and verify that the published guide remains general. Test the November 2026 date regression above. Test a sold-out main hotel and confirm that airport and interhotel shuttle schedules remain distinct.

Test a historical directory containing a repurposed navigation domain and a previous-city guide with detailed floor assignments. Confirm that no old-domain availability, foreign room numbers, or imagined sensory cues are imported. Test an airport-to-hotel itinerary with an address but no door-level route; confirm the missing handoff remains explicit. See learning-and-route-data.md for the expanded record.
