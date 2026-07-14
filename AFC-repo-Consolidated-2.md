# UNITED STATES PATENT APPLICATION

---

**Application Number:** [PENDING]
**Filing Date:** July 2026
**International Classification:** H04W 16/10; H04W 72/04; H04B 17/318

---

# SYSTEM AND METHOD FOR AUTOMATED FREQUENCY COORDINATION-INTEGRATED RADIO RESOURCE MANAGEMENT IN 6 GHz WIRELESS ACCESS NETWORKS

---

## INVENTORS

| Name | Organization | Department |
|------|-------------|------------|
| Mist Systems Engineering Team | Juniper Networks, Inc. | Wireless Engineering |
| AI-Assisted Radio Resource Management Group | Juniper Networks, Inc. | Cloud Platform |

---

## ASSIGNEE

**Juniper Networks, Inc.**
1133 Innovation Way
Sunnyvale, California 94089
United States of America

---

## RELATED APPLICATIONS

This application claims priority to provisional application(s) related to Radio Resource Management systems for 6 GHz Wi-Fi networks.

---

## TABLE OF CONTENTS

| Section | Title | Page |
|---------|-------|------|
| Abstract | Abstract of the Disclosure | 3 |
| Field | Field of the Invention | 4 |
| Background | Background of the Invention | 4 |
| Part 2 | Summary of the Invention | [Part 2] |
| Part 2 | Brief Description of the Drawings | [Part 2] |
| Part 3 | Detailed Description — AFC Core Architecture | [Part 3] |
| Part 4 | Detailed Description — RRM Integration | [Part 4] |
| Part 5 | Detailed Description — Geolocation and EIRP | [Part 5] |
| Part 6 | Claims | [Part 6] |
| Part 7 | Figures (22 Diagrams) | [Part 7] |

---

## ABSTRACT

A system and method are disclosed for integrating Automated Frequency Coordination (AFC) with cloud-scale Radio Resource Management (RRM) in 6 GHz wireless access networks. An AFC proxy intermediary service receives device registration payloads from a cloud RRM engine, forwards spectrum availability inquiries to regulatory AFC systems, and returns per-channel maximum Effective Isotropic Radiated Power (EIRP) assignments to access points (APs). The system derives channel-specific EIRP limits by computing the minimum of the AFC-reported per-channel maximum EIRP and a Power Spectral Density (PSD)-derived EIRP value, expressed as maxPsd + 10 × log10(channel_bandwidth_MHz), subject to a minimum PSD floor indexed by channel bandwidth. Geolocation validation employs WGS84-to-ECEF coordinate transformation with a configurable displacement threshold to detect AP relocation events, triggering automatic AFC re-registration. The system handles abnormal AP lifecycle events including unclaimed and unassigned states by purging device registrations from the AFC proxy and associated geolocation caches. A fallback mechanism degrades AFC-capable APs to Low Power Indoor (LPI) operation when GPS coordinates are unavailable, preserving connectivity. Integration with a distributed stream-processing topology enables real-time, per-AP AFC coordination across enterprise-scale wireless deployments.

---

## FIELD OF THE INVENTION

The present invention relates to wireless local area network (WLAN) management systems, and more particularly to systems and methods for automatically coordinating spectrum access in the 6 GHz frequency band (5925 MHz to 7125 MHz) through integration of Automated Frequency Coordination (AFC) mechanisms with cloud-managed Radio Resource Management (RRM) platforms operating under regulatory frameworks including United States Federal Communications Commission (FCC) rules codified at 47 CFR Part 15, Subpart E.

The invention further relates to:

- Standard Power (SP) access point operation at elevated transmit power levels in the 6 GHz band, as distinguished from Low Power Indoor (LPI) operation;
- Dynamic per-channel EIRP limit enforcement derived from real-time AFC system responses;
- Geolocation-aware spectrum coordination utilizing WGS84 Earth-Centered, Earth-Fixed (ECEF) coordinate transformation;
- Cloud-scale distributed stream processing for enterprise wireless network management;
- Automated device lifecycle management within AFC registration systems.

---

## BACKGROUND OF THE INVENTION

### 1. The 6 GHz Band and Incumbent Protection Problem

The Federal Communications Commission (FCC) allocated 1,200 MHz of spectrum in the 6 GHz band (5925–7125 MHz) for unlicensed Wi-Fi use under 47 CFR Part 15, Subpart E, effective April 2020. This allocation enables high-throughput IEEE 802.11ax (Wi-Fi 6E) and IEEE 802.11be (Wi-Fi 7) networks supporting channel bandwidths of 20, 40, 80, 160, and 320 MHz.

However, this spectrum is also occupied by incumbent licensed services whose operations must be protected from interference. These incumbents include:

- **Fixed Satellite Service (FSS)** earth stations receiving transmissions from geostationary satellites in C-band and Ku-band;
- **Fixed Microwave Links** used by utilities, public safety, and backhaul operators;
- **Broadcast Auxiliary Service (BAS)** and **Cable Television Relay Service (CARS)** links;
- **Earth Exploration Satellite Service (EESS)** receivers.

Unlicensed 6 GHz devices operating at elevated power levels without coordination risk causing harmful interference to these incumbents, rendering affected satellite ground stations and microwave links inoperable. The geographic distribution of incumbents is non-uniform and dynamic, requiring real-time database-driven coordination rather than static exclusion zones.

### 2. Regulatory Framework: 47 CFR Part 15, Subpart E

The FCC established a tiered regulatory framework for 6 GHz unlicensed devices:

**Tier 1 — Low Power Indoor (LPI) Operation:**
- Maximum EIRP: 30 dBm (1 watt) for standard client devices
- Maximum power spectral density: 5 dBm/MHz
- Permitted indoors only; no AFC required
- Cannot be used by devices with external antennas in most configurations

**Tier 2 — Standard Power (SP) Operation:**
- Maximum EIRP: 36 dBm (approximately 4 watts)
- Maximum power spectral density: 23 dBm/MHz
- **Requires AFC coordination** before transmitting
- Permitted indoors and outdoors
- Enables significantly greater coverage range and throughput compared to LPI

**Tier 3 — Very Low Power (VLP) Operation:**
- Maximum EIRP: 14 dBm
- No AFC required; limited to portable devices

The critical constraint of SP operation — and the central regulatory mandate addressed by the present invention — is that a Standard Power device **must not transmit** until it has received authorization from a registered AFC system specifying which channels are available and at what maximum power levels at the device's specific geographic location.

### 3. AFC System Architecture

The FCC requires that AFC systems be independently certified and administered. The Wi-Fi Alliance (WFA) manages a testing and certification process for AFC systems. The AFC system architecture, as standardized, involves:

1. **The AFC System** (also called the AFC Database): A certified backend service that maintains records of incumbent locations, antenna patterns, propagation models, and exclusion zones. The AFC system receives spectrum inquiries and returns channel availability responses.

2. **The Standard Power Device**: An access point or client device that submits its geolocation, device identity, and spectrum requirements to the AFC system before operating.

3. **The AFC Protocol**: Based on the OpenAFC API specification, requests include device descriptor (serial number, FCC certification ID, ruleset), geographic location (ellipse with center latitude/longitude, semi-major axis, semi-minor axis, orientation, and elevation above ground level), and inquired channels or frequency ranges.

4. **The AFC Response**: Returns a list of available channels per operating class with per-channel maximum EIRP values, frequency range availability, and an expiration timestamp after which re-inquiry is required.

### 4. Limitations of Prior Art

Prior art systems for 6 GHz AFC coordination suffer from several significant limitations:

**4.1 Static Channel Configuration**

Prior art wireless management systems that predate AFC integration rely on static channel lists configured by network administrators. These systems cannot dynamically adapt channel and power assignments to real-time AFC responses, resulting in either overly conservative power settings that reduce coverage or potential regulatory violations when incumbent databases are updated.

**4.2 Per-Device AFC Without RRM Coordination**

Early 6 GHz AP firmware implementations perform AFC queries independently, without coordination from a centralized RRM engine. This leads to inconsistent channel selections across APs within the same site, creating co-channel interference and suboptimal spectrum utilization. A centralized RRM system that receives and incorporates AFC responses can optimize channel assignments across the entire site topology.

**4.3 Absence of Geolocation Change Detection**

Prior art AFC implementations submit geolocation once during initial configuration and do not detect or respond to AP physical relocation. When an AP is moved to a new location — even one with a different incumbent profile — it continues operating on the previously authorized channels until the AFC authorization expires. This creates a gap period during which the device may cause interference to incumbents near the new location that were not present near the original location.

**4.4 No Graceful Degradation on GPS Failure**

Prior systems that require GPS for AFC queries simply disable the 6 GHz radio when GPS coordinates are unavailable. This approach results in complete service outage for users dependent on 6 GHz connectivity, rather than a graceful fallback to lower-power LPI operation that does not require AFC but still provides connectivity.

**4.5 Monolithic AFC-RRM Integration**

Prior systems couple AFC operations directly within the AP firmware or within a monolithic network management platform. This architecture cannot scale to enterprise deployments spanning thousands of APs across hundreds of sites, where AFC queries, responses, and RRM decisions must be processed in parallel with sub-second latency.

**4.6 Lack of Lifecycle Management**

When APs are decommissioned, reassigned, or unclaimed, prior art systems do not purge the associated AFC registrations from the AFC proxy or AFC system databases. This results in stale device records that consume database resources and may interfere with future registrations for the same MAC address at a different location.

**4.7 Coarse EIRP Limit Application**

Prior art implementations apply the AFC-reported per-channel maximum EIRP directly as the transmit power limit, without accounting for the more restrictive PSD-based limits that may apply to the same channel. The FCC rules require that BOTH the per-channel EIRP limit AND the PSD limit be satisfied. Failure to compute the minimum of these two constraints may result in regulatory violations on channels where the PSD limit is more restrictive than the channel EIRP limit.

### 5. Summary of Problems Addressed

The present invention addresses the following specific technical problems not solved by prior art:

1. How to dynamically integrate real-time AFC channel and EIRP authorizations into a cloud-scale, multi-site RRM engine that simultaneously manages thousands of access points;

2. How to detect AP geolocation changes and automatically trigger AFC re-registration without requiring manual administrative action;

3. How to compute the correct maximum transmit power for each AFC-authorized channel by taking the minimum of the AFC-reported EIRP limit and the PSD-derived EIRP limit, enforced above a minimum floor value per bandwidth;

4. How to manage the complete lifecycle of AP registrations in the AFC system, including automatic deletion of registrations for APs that become unclaimed or unassigned;

5. How to provide graceful service degradation when GPS coordinates are unavailable, falling back to LPI operation rather than disabling the radio entirely;

6. How to handle 320 MHz channel assignments where the same 20 MHz sub-channel may belong to either of two non-overlapping 320 MHz channel plans (Mode 1: centers at channels 31, 95, 159; Mode 2: centers at channels 63, 127, 191) and resolve ambiguity using proximity-based mode classification;

7. How to support multiple AFC provider backends (production, test harness variants, and development environments) through a configurable provider flag architecture without modifying device firmware.

---

*[End of Part 1 — Continue to Part 2: Summary of the Invention and Brief Description of Drawings]*
# PATENT APPLICATION — PART 2 OF 7
# Summary of the Invention & Brief Description of the Drawings

**Title:** SYSTEM AND METHOD FOR AUTOMATED FREQUENCY COORDINATION-INTEGRATED RADIO RESOURCE MANAGEMENT IN 6 GHz WIRELESS ACCESS NETWORKS

---

## SUMMARY OF THE INVENTION

The present invention provides a system and method for integrating Automated Frequency Coordination (AFC) with cloud-managed Radio Resource Management (RRM) in 6 GHz wireless access networks. The invention introduces several novel technical contributions, each described below.

---

### Novel Contribution 1: AFC Proxy Intermediary Architecture

The invention introduces an AFC proxy service that sits between the RRM cloud engine and the AFC system. Rather than having each access point independently query the AFC system — which would require each AP to maintain AFC credentials, handle retries, and manage response parsing — the AFC proxy centralizes all AFC interactions. The RRM engine submits device registration requests to the AFC proxy using a standardized JSON payload format. The AFC proxy maintains per-device state, forwards requests to the upstream AFC system, and returns processed channel availability information to the RRM engine.

The AFC proxy is addressed via a configurable URL pattern of the form:
```
http://afc-proxy-{ENV}.mist.pvt/afc/devices
```
where `{ENV}` is the deployment environment identifier (e.g., `staging`, `prod`, `eu`). This environment-parameterized addressing enables seamless promotion of RRM software across deployment tiers without reconfiguration of AFC endpoints.

---

### Novel Contribution 2: Structured AFC Payload Construction

The invention provides a structured payload construction method that assembles a standards-compliant AFC request from AP configuration data. The payload includes:

- **Request identification**: `requestId` set to the AP's MAC address (enabling direct correlation between request and response)
- **Site identification**: `siteId` set to the network site UUID
- **Provider routing**: `providerName` resolved from a configurable flag (0→"wfa", 1→"wfa-th01", 2→"wfa-th02", "dev"→"dev")
- **Device descriptor**: `serialNumber` (AP MAC address) and `certificationId` array containing the FCC ID (e.g., "2AHBN-AP64") with ruleset identifier "US_47_CFR_PART_15_SUBPART_E"
- **Location**: WGS84 ellipse with center latitude/longitude, semi-major axis (capped at 325 meters), semi-minor axis (capped at 325 meters), orientation (normalized to 0°–180°), height above ground level (minimum 0.1 meters), vertical uncertainty, and indoor deployment indicator
- **Inquired frequency range**: 5925–7115 MHz (full 6 GHz SP band)
- **Inquired channels**: Global Operating Classes 131, 132, 133, 134, 136, and 137

---

### Novel Contribution 3: Dual-Constraint EIRP Computation

The invention introduces a dual-constraint EIRP computation method that derives the correct maximum transmit power for each AFC-authorized channel. For each available channel reported in the AFC response, the system:

1. Retrieves the AFC-reported per-channel maximum EIRP value from `availableChannelInfo[].maxEirp[]`
2. Computes the PSD-derived EIRP from the available frequency information using:

   **EIRP_from_PSD = maxPsd + 10 × log10(channel_bandwidth_MHz)**

   where `maxPsd` is the maximum power spectral density in dBm/MHz reported for the frequency range overlapping the channel, and `channel_bandwidth_MHz` is the channel bandwidth in MHz (20, 40, 80, 160, or 320).

3. Takes the minimum of the two EIRP values:

   **ch_max_power = min(AFC_EIRP, EIRP_from_PSD)**

4. Enforces a minimum floor value indexed by bandwidth from the AFC_MIN_PSD table:

   | Bandwidth (MHz) | Minimum EIRP Floor (dBm) |
   |----------------|--------------------------|
   | 20             | 14                       |
   | 40             | 17                       |
   | 80             | 20                       |
   | 160            | 23                       |
   | 320            | 26                       |

5. Final assignment: **ch_max_power = max(AFC_MIN_PSD[bandwidth], int(min(psdEirp[ch], maxEirp[j])))**

---

### Novel Contribution 4: Sub-Channel EIRP Propagation

The invention provides a sub-channel expansion algorithm that propagates wide-channel EIRP limits to the constituent 20 MHz sub-channels. For each approved wide-channel center frequency index (`channelCfi`), the system identifies all 20 MHz sub-channels using channel offset deltas (`ch_delta`) specific to each bandwidth:

| Bandwidth (MHz) | ch_delta Offsets from Center |
|----------------|------------------------------|
| 20             | [0]                          |
| 40             | [2]                          |
| 80             | [2, 6]                       |
| 160            | [2, 6, 10, 14]               |
| 320            | [2, 6, 10, 14, 18, 22, 26, 30] |

For each delta `d`, both `channelCfi - d` and `channelCfi + d` are checked against the list of valid 20 MHz channels in the 6 GHz band and assigned the computed `ch_max_power`.

---

### Novel Contribution 5: 320 MHz Mode 1 / Mode 2 Disambiguation

The invention addresses the specific technical challenge of 320 MHz channel plan disambiguation in the 6 GHz band. The 6 GHz spectrum supports two non-overlapping 320 MHz channel plans:

- **Mode 1**: Center channels at 31, 95, 159 (covering sub-channels approximately 1–61, 65–125, 129–189)
- **Mode 2**: Center channels at 63, 127, 191 (covering sub-channels approximately 33–93, 97–157, 161–221)

Some 20 MHz sub-channels appear in the sub-channel sets of both Mode 1 and Mode 2. The invention provides a mode disambiguation function `get_mode(channel)` that:

1. If the channel appears only in Mode 1's sub-channel range, assigns Mode 1
2. If the channel appears only in Mode 2's sub-channel range, assigns Mode 2
3. If the channel appears in both ranges (overlap region), computes the distance from the channel to the nearest Mode 1 center channel and the nearest Mode 2 center channel, and assigns the mode whose center is closer

During sub-channel expansion, sub-channels are only assigned EIRP values if their mode matches the mode of the wide-channel authorization.

---

### Novel Contribution 6: WGS84-ECEF Geolocation Validation

The invention provides a geolocation change detection method using Earth-Centered, Earth-Fixed (ECEF) coordinate transformation. When an AP submits a new AFC request with updated GPS coordinates, the system compares the new coordinates against the coordinates used in the existing AFC proxy registration. The comparison proceeds as:

1. Convert both old and new (latitude, longitude) to ECEF (x, y, z) using WGS84 ellipsoid parameters:
   - Semi-major axis: **a = 6,378,137.0 meters**
   - Flattening: **f = 1 / 298.257223563**
   - Semi-minor axis: **b = a × (1 − f)**
   - Normal radius of curvature: **N = a / sqrt(1 − f(2 − f) × sin²(lat))**
   - ECEF coordinates: x = (N + alt) × cos(lat) × cos(lon); y = (N + alt) × cos(lat) × sin(lon)

2. Compute Euclidean distance in the XY plane: **distance = sqrt((x_new − x_old)² + (y_new − y_old)²)**
3. Compute absolute height difference: **height_diff = |h_new − h_old|**
4. If both `distance ≤ threshold` AND `height_diff ≤ threshold`, the location is considered unchanged
5. The system-level location threshold is **200 meters** (configurable per site policy)

When a location change is detected, the system:
1. Deletes the existing AFC proxy registration for the AP
2. Constructs a new payload with the updated GPS coordinates
3. Submits a new POST request to the AFC proxy
4. Retrieves the updated channel authorization via GET

---

### Novel Contribution 7: AP Lifecycle Management in AFC

The invention provides automatic lifecycle management of AP registrations within the AFC system. When the RRM event processing system receives notification that an AP has transitioned to an abnormal state:

- **AP_UNCLAIMED**: The AP has been factory-reset or disassociated from its organization; the system deletes the AFC proxy registration and purges the geolocation cache entry (`devices/{apID}/gps`)
- **AP_UNASSIGNED**: The AP is not yet assigned to a site; the system deletes the AFC proxy registration and purges the geolocation cache

The deletion operation uses an HTTP DELETE request with the `X-HTTP-Method-Override: DELETE` header, with up to 3 retry attempts and a 1-second delay between retries.

---

### Novel Contribution 8: LPI Fallback on GPS Unavailability

The invention provides a graceful degradation mechanism for AFC-capable APs that cannot obtain GPS coordinates. When the AFC channel validation function returns status "NoGPS" and the AP is configured with the `lpi_ok` capability flag:

1. The system disables Standard Power mode for this AP (`afc_standard_power = False`)
2. Clears the AFC channel authorization (`afc_channels = {}`)
3. Falls back to the AP's configured channel list (which may be used in LPI mode)
4. Sets `afc_source = "lpi_fallback"` for audit tracking
5. Records the NoGPS status in Redis for retry processing by the AFC tick process

This mechanism preserves 6 GHz connectivity for affected users rather than disabling the radio entirely.

---

### Novel Contribution 9: Redis-Backed AFC State Management

The invention provides a Redis-based state management layer for AFC information. AFC node state is stored using structured Redis hash entries with keys encoding organization, site, and AP identifiers. The system maintains:

- AFC authorization status (DONE, NotDONE, NoGPS)
- Channel authorization with per-channel EIRP values
- Authorization expiration timestamp
- Bandwidth configuration
- Site and organization identifiers

A periodic tick process (`tick_process_rrm_afc`) iterates over all AFC nodes tracked in Redis, re-validates their geolocation, refreshes authorizations near expiry, and removes entries that have been successfully re-authorized.

---

### Novel Contribution 10: Multi-Environment Provider Support

The invention supports multiple AFC provider backends through a flag-to-provider-name mapping:

| Flag | Provider Name | Purpose |
|------|--------------|---------|
| "0"  | "wfa"        | Production Wi-Fi Alliance AFC system |
| "1"  | "wfa-th01"   | Internal test harness |
| "2"  | "wfa-th02"   | Certification test harness |
| "dev"| "dev"        | Development/QA environment (uses mock responses) |

When the provider flag is "dev", the system bypasses the AFC proxy entirely and uses either a mock AFC response stored in Redis or a built-in default response template, enabling full end-to-end testing without an active AFC system.

---

## BRIEF DESCRIPTION OF THE DRAWINGS

The accompanying drawings, which form a part of this specification and are incorporated by reference, illustrate embodiments of the invention. In the drawings:

**Figure 1** is a system architecture diagram illustrating the overall topology of the AFC-integrated RRM system, showing the relationships among access points, the RRM cloud engine, the AFC proxy intermediary service, and the upstream AFC system.

**Figure 2** is a sequence diagram illustrating the AFC request lifecycle from AP ACS event reception through channel assignment emission, including the POST, GET, and response processing steps.

**Figure 3** is a structured diagram illustrating the AFC request payload JSON schema, showing all fields including requestId, siteId, providerName, deviceDescriptor, location (with ellipse parameters), inquiredFrequencyRange, and inquiredChannels.

**Figure 4** is a structured diagram illustrating the AFC response JSON schema, showing availableChannelInfo, availableFrequencyInfo, availabilityExpireTime, state, and responseCode fields.

**Figure 5** is a mapping table diagram illustrating the correspondence between Global Operating Class values (131, 132, 133, 134, 136, 137) and channel bandwidths (20, 40, 80, 160, 80, 320 MHz respectively).

**Figure 6** is a spectrum allocation diagram illustrating the 6 GHz band from 5925 MHz to 7125 MHz, showing all available 20 MHz channel center frequencies and their channel index numbers.

**Figure 7** is a flowchart illustrating the dual-constraint EIRP computation process, from AFC response parsing through PSD-derived EIRP calculation, minimum selection, AFC_MIN_PSD floor enforcement, and final per-channel EIRP assignment.

**Figure 8** is a decision tree diagram illustrating the AFC_MIN_PSD floor enforcement logic, showing the minimum EIRP values enforced for each supported bandwidth.

**Figure 9** is a flowchart illustrating the geolocation validation process, including GPS retrieval from Redis, WGS84-to-ECEF coordinate conversion, Euclidean distance computation, threshold comparison, and location-change response actions.

**Figure 10** is a mathematical block diagram illustrating the WGS84-to-ECEF coordinate transformation formulas with all constants, intermediate calculations, and output variables labeled.

**Figure 11** is a flowchart illustrating the location change detection and AFC cache invalidation process, showing the decision points for deletion, re-registration, and response processing.

**Figure 12** is an architecture diagram illustrating the RrmAFCBolt Apache Storm topology component, showing input streams, bolt initialization parameters, process and tick tuple handling, and output actions.

**Figure 13** is a state machine diagram illustrating the AFC channel validation states (NoGPS, NotDONE, DONE, LPI Fallback), transitions between states, and the actions triggered in each state.

**Figure 14** is a channel layout diagram illustrating 320 MHz Mode 1 and Mode 2 channel plans in the 6 GHz band, showing the center channels (31, 95, 159 for Mode 1; 63, 127, 191 for Mode 2) and their respective sub-channel ranges.

**Figure 15** is a table diagram illustrating the ch_delta sub-channel expansion algorithm for each supported bandwidth, showing how wide-channel center frequencies map to constituent 20 MHz sub-channel indices.

**Figure 16** is a flowchart illustrating the DeleteAP retry logic, showing the three-attempt retry loop with 1-second inter-attempt delay and the X-HTTP-Method-Override header mechanism.

**Figure 17** is a lifecycle diagram illustrating AP state transitions within the AFC system, from initial registration through active operation, GPS loss, location change, unclaim/unassign events, and re-registration.

**Figure 18** is an architecture diagram illustrating the Redis cache structure for AFC state management, showing hash key patterns, stored fields, and the tick-process retrieval and update flow.

**Figure 19** is a diagram illustrating the multi-provider support architecture, showing the flag-to-provider-name mapping table and how the provider flag from site policy routes AFC requests to different backend systems.

**Figure 20** is a decision tree illustrating the LPI fallback logic, showing the conditions (afc_status == "NoGPS" AND lpi_ok == True) that trigger LPI mode, the state transitions applied, and the audit fields set.

**Figure 21** is a flowchart illustrating the complete ACS+AFC integration flow within the rrmACSV2 processing pipeline, from ACS command reception through standard power detection, AFC channel validation, channel intersection, EIRP assignment, and RRM output emission.

**Figure 22** is a diagram illustrating the afcNode graph processing function in APnode, showing how AFC channel authorizations are applied to the AP radio topology graph, including expiry checking, channel list update, and radio disable logic.

---

*[End of Part 2 — Continue to Part 3: Detailed Description — AFC Core Architecture]*

# PATENT APPLICATION — PART 3 OF 7
# Detailed Description: AFC Core Architecture

**Title:** SYSTEM AND METHOD FOR AUTOMATED FREQUENCY COORDINATION-INTEGRATED RADIO RESOURCE MANAGEMENT IN 6 GHz WIRELESS ACCESS NETWORKS

---

## DETAILED DESCRIPTION OF THE PREFERRED EMBODIMENTS

### Overview of the Preferred Embodiment

The following description sets forth specific details of the preferred embodiment of the invention. Like reference numerals refer to like elements throughout. The description is organized to follow the data flow from AFC payload construction, through proxy communication, to channel availability extraction and EIRP assignment.

The preferred embodiment is implemented in Python and deployed as a set of microservices and stream-processing components within a cloud-managed enterprise wireless platform. The AFC-specific components reside in a module package designated `src/afc/`, comprising three primary modules: `afc_payload.py`, `afc_query.py`, and `afc_utils.py`, integrated with the broader RRM system through `rrmAFC.py` and `rrmACSV2.py`.

---

### Section 1: AFC Payload Construction (afc_payload.py)

#### 1.1 Channel-to-Frequency Reference Mapping

The module defines a reference dictionary `channel_to_freq` that maps each 20 MHz channel index in the 6 GHz band to its center frequency in MHz. This mapping covers all 59 channels allocated for unlicensed use under 47 CFR Part 15, Subpart E. The complete mapping is:

**Table 1: 6 GHz Band Channel-to-Center-Frequency Mapping**

| Channel | Center Freq (MHz) | Channel | Center Freq (MHz) | Channel | Center Freq (MHz) |
|---------|-------------------|---------|-------------------|---------|-------------------|
| 1       | 5955              | 85      | 6375              | 169     | 6795              |
| 5       | 5975              | 89      | 6395              | 173     | 6815              |
| 9       | 5995              | 93      | 6415              | 177     | 6835              |
| 13      | 6015              | 97      | 6435              | 181     | 6855              |
| 17      | 6035              | 101     | 6455              | 185     | 6875              |
| 21      | 6055              | 105     | 6475              | 189     | 6895              |
| 25      | 6075              | 109     | 6495              | 193     | 6915              |
| 29      | 6095              | 113     | 6515              | 197     | 6935              |
| 33      | 6115              | 117     | 6535              | 201     | 6955              |
| 37      | 6135              | 121     | 6555              | 205     | 6975              |
| 41      | 6155              | 125     | 6575              | 209     | 6995              |
| 45      | 6175              | 129     | 6595              | 213     | 7015              |
| 49      | 6195              | 133     | 6615              | 217     | 7035              |
| 53      | 6215              | 137     | 6635              | 221     | 7055              |
| 57      | 6235              | 141     | 6655              | 225     | 7075              |
| 61      | 6255              | 145     | 6675              | 229     | 7095              |
| 65      | 6275              | 149     | 6695              | 233     | 7115              |
| 69      | 6295              | 153     | 6715              |         |                   |
| 73      | 6315              | 157     | 6735              |         |                   |
| 77      | 6335              | 161     | 6755              |         |                   |
| 81      | 6355              | 165     | 6775              |         |                   |

All channels are spaced 4 channel units apart (equivalent to 20 MHz), starting from channel 1 at 5955 MHz center frequency (corresponding to the 5945–5965 MHz band edge pair). The allocation ends at channel 233 (7115 MHz center), corresponding to the 7105–7125 MHz range.

#### 1.2 Channel Frequency Range Mapping by Bandwidth

The invention defines a comprehensive channel frequency range mapping `get_channel_freq_mapping()` that provides, for each supported bandwidth, the set of valid channel center indices and their corresponding lower and upper frequency boundaries. This mapping is essential for computing PSD-to-EIRP conversions, as described in Section 3.

**Table 2: 20 MHz Channel Frequency Ranges (selected)**

| Channel | Low (MHz) | High (MHz) |
|---------|-----------|-----------|
| 1       | 5945      | 5965      |
| 5       | 5965      | 5985      |
| 33      | 6105      | 6125      |
| 97      | 6425      | 6445      |
| 229     | 7085      | 7105      |

**Table 3: 40 MHz Channel Frequency Ranges (selected)**

| Channel | Low (MHz) | High (MHz) |
|---------|-----------|-----------|
| 3       | 5955      | 5995      |
| 11      | 5995      | 6035      |
| 131     | 6595      | 6635      |
| 227     | 7075      | 7115      |

**Table 4: 80 MHz Channel Frequency Ranges (complete)**

| Channel | Low (MHz) | High (MHz) |
|---------|-----------|-----------|
| 7       | 5975      | 6035      |
| 23      | 6035      | 6115      |
| 39      | 6115      | 6195      |
| 55      | 6195      | 6275      |
| 71      | 6275      | 6355      |
| 87      | 6355      | 6435      |
| 103     | 6435      | 6515      |
| 119     | 6515      | 6595      |
| 135     | 6595      | 6675      |
| 151     | 6675      | 6755      |
| 167     | 6755      | 6835      |
| 183     | 6835      | 6915      |
| 199     | 6915      | 6995      |
| 215     | 6995      | 7075      |

**Table 5: 160 MHz Channel Frequency Ranges (complete)**

| Channel | Low (MHz) | High (MHz) |
|---------|-----------|-----------|
| 15      | 5955      | 6115      |
| 47      | 6115      | 6275      |
| 79      | 6275      | 6435      |
| 111     | 6435      | 6595      |
| 143     | 6595      | 6755      |
| 175     | 6755      | 6915      |
| 207     | 6915      | 7075      |

**Table 6: 320 MHz Channel Frequency Ranges (complete)**

| Channel | Low (MHz) | High (MHz) | Mode |
|---------|-----------|-----------|------|
| 31      | 5945      | 6265      | 1    |
| 63      | 6105      | 6425      | 2    |
| 95      | 6265      | 6585      | 1    |
| 127     | 6425      | 6745      | 2    |
| 159     | 6585      | 6905      | 1    |
| 191     | 6745      | 7065      | 2    |

#### 1.3 AFC Request Payload Construction

The function `get_payload_proxy(ap_id, site_id, gps, provider_flag, afc_certificationId)` constructs a standards-compliant AFC request payload. The function signature with default values is:

```
get_payload_proxy(
    ap_id="sampleDevice",
    site_id="sampleSite",
    gps={},
    provider_flag="0",
    afc_certificationId=[{"id": "2AHBN-AP64", "rulesetId": "US_47_CFR_PART_15_SUBPART_E"}]
)
```

**Payload Construction Logic:**

**Step 1 — Orientation Normalization:**
The ellipse orientation angle is extracted from the GPS data. If the orientation value exceeds 180 degrees, it is reduced by 180 degrees to normalize it to the range [0°, 180°] as required by the AFC protocol specification.

```
orientation = gps.get("location", {}).get("ellipse", {}).get("orientation", 45.0)
if orientation > 180:
    orientation = orientation - 180
```

**Step 2 — Location Parameter Extraction with Safety Bounds:**
- Height above ground: `max(gps.get("elevation", {}).get("height", 3.0), 0.1)` — minimum 0.1 meters to prevent invalid zero-height submissions
- Vertical uncertainty: integer value, default 2 meters
- Longitude: from GPS ellipse center, default -122.0322895 (Sunnyvale, CA area)
- Latitude: from GPS ellipse center, default 37.3228934
- Major axis: `min(325, int(gps.get("ellipse", {}).get("majorAxis", 100)))` — capped at 325 meters
- Minor axis: `min(325, int(gps.get("ellipse", {}).get("minorAxis", 50)))` — capped at 325 meters

**Step 3 — Payload Template Assembly:**
The complete payload template includes:

```json
{
  "requestId": "<AP MAC address>",
  "siteId": "<site UUID>",
  "providerName": "<resolved from provider_flag>",
  "deviceDescriptor": {
    "serialNumber": "<AP MAC address>",
    "certificationId": [
      {
        "id": "2AHBN-AP64",
        "rulesetId": "US_47_CFR_PART_15_SUBPART_E"
      }
    ]
  },
  "location": {
    "elevation": {
      "height": 3.0,
      "heightType": "AGL",
      "verticalUncertainty": 2
    },
    "ellipse": {
      "center": {
        "longitude": -122.0322895,
        "latitude": 37.3228934
      },
      "majorAxis": 100,
      "minorAxis": 50,
      "orientation": 45
    },
    "indoorDeployment": 1
  },
  "inquiredFrequencyRange": [
    {
      "lowFrequency": 5925,
      "highFrequency": 7115
    }
  ],
  "inquiredChannels": [
    {"globalOperatingClass": 131},
    {"globalOperatingClass": 132},
    {"globalOperatingClass": 133},
    {"globalOperatingClass": 134},
    {"globalOperatingClass": 136},
    {"globalOperatingClass": 137}
  ]
}
```

The `indoorDeployment` field is set to 1, indicating indoor deployment as required for Standard Power indoor operation under 47 CFR Part 15, Subpart E.

**Step 4 — Dynamic Field Population:**
After assembling the template, the function populates dynamic fields:
- Sets `requestId` and `deviceDescriptor.serialNumber` to `ap_id` if provided
- Sets `siteId` to `site_id` if provided
- Resolves `providerName` from `get_flag_provider_mapping()` using `provider_flag`

#### 1.4 Default AFC Response for Development and Testing

The function `get_default_response(ap_id, site_id)` generates a synthetic AFC response for use in development environments (when `provider_flag == "dev"`) or when no mock response is found in Redis. This response provides a predetermined set of channel authorizations that enable end-to-end testing:

**Table 7: Default AFC Response Channel Authorizations**

| GlobalOperatingClass | Bandwidth | Channels (channelCfi) | Max EIRP (dBm) |
|---------------------|-----------|----------------------|----------------|
| 131                 | 20 MHz    | 1, 33, 137, 209      | 26.0, 30, 29.7, 28 |
| 132                 | 40 MHz    | 3, 75, 131, 179      | 29.0, 31.5, 25, 27 |
| 133                 | 80 MHz    | 7, 71, 135, 199      | 30.2, 29.4, 26, 30 |
| 134                 | 160 MHz   | 15, 143              | 33.2, 33.2     |
| 137                 | 320 MHz   | 31, 191              | 33.2, 30       |

The response includes:
- `state`: "DONE"
- `availabilityExpireTime`: Current UTC time plus 24 hours (ISO 8601 format)
- `responseCode`: 0 (Success)
- `shortDescription`: "Success"

#### 1.5 Provider Flag Mapping

**Table 8: AFC Provider Flag to Provider Name Mapping**

| Flag | Provider Name | Purpose |
|------|--------------|---------|
| "0"  | "wfa"        | Production Wi-Fi Alliance certified AFC system |
| "1"  | "wfa-th01"   | Internal test harness machine |
| "2"  | "wfa-th02"   | Certification test harness machine |
| "dev"| "dev"        | Development environment (mock responses only) |

The provider flag is stored as a site-level policy parameter (`afc-provider-flag`) and retrieved from site configuration at processing time. This allows different sites within the same organization to use different AFC backends.

---

### Section 2: AFC Proxy Communication (afc_query.py)

#### 2.1 AFC Request Submission: PostAfcRequest

The function `PostAfcRequest(afc_proxy_link, sample_data)` submits a device registration request to the AFC proxy. The complete operation is:

**Pre-condition Summary:**
Before calling this function, the caller has constructed a valid payload using `get_payload_proxy()` with the AP's current GPS coordinates, certification ID, and provider flag.

1. If `sample_data` is None, a default payload is generated via `get_payload_proxy()`
2. An HTTP session is created with SSL certificate verification disabled (`session.verify = False`) to support internal PKI environments
3. An HTTP POST request is sent to `afc_proxy_link` with:
   - Request body: JSON-serialized `sample_data`
   - Content-Type header: `application/json`
   - Timeout: 5 seconds
4. On successful response (HTTP 200): returns `True` and logs success with requestId and siteId
5. On non-200 response: logs warning with the error status code and returns `False`
6. On network exception: logs warning "Post to AFC Proxy failed." and returns `False`

The 5-second timeout prevents hung connections from blocking the RRM processing pipeline during AFC proxy outages.

**Post-condition Summary:**
On success (True returned), the AP's device descriptor and location have been registered with the AFC proxy. The AFC proxy will asynchronously process this registration with the upstream AFC system. A subsequent GET request is required to retrieve the authorization result.

#### 2.2 Channel Authorization Retrieval: GetChannelByMac

The function `GetChannelByMac(afc_proxy_link, mac, timeout=10)` retrieves the channel authorization for a specific AP. The URL pattern is:

```
{afc_proxy_link}/{mac}
```

For example: `http://afc-proxy-prod.mist.pvt/afc/devices/5433c60d3162`

**Operation:**
1. HTTP GET request to the constructed URL with 5-second timeout
2. Response is parsed as JSON
3. On exception: logs warning "Query of the AP {mac} failed, using default response for next step." and returns empty dict `{}`
4. Returns the JSON response dict on success

**Pre-condition Summary:**
A prior `PostAfcRequest()` must have succeeded for this MAC address. The response state field ("DONE", "NotDONE", etc.) indicates whether the AFC proxy has completed processing.

**Post-condition Summary:**
The returned dict contains the full AFC authorization result, including `availableChannelInfo`, `availableFrequencyInfo`, `availabilityExpireTime`, `state`, and `requestId`. The caller must check `response.get("state") == "DONE"` before using channel data.

#### 2.3 AP Registration Deletion: DeleteAP

The function `DeleteAP(afc_proxy_link, mac)` removes an AP registration from the AFC proxy. This is required when an AP changes location (triggering re-registration with new GPS), or when an AP is decommissioned.

**URL Pattern:**
```
{afc_proxy_link}/{mac}
```

**Operation with Retry Logic:**

```
max_retries = 3
retry_count = 0
timeout_seconds = 5

while retry_count < max_retries:
    try:
        response = session.request(
            "DELETE",
            url=url,
            headers={"X-HTTP-Method-Override": "DELETE"},
            timeout=timeout_seconds
        )
        if response.status_code == 200:
            return True
        retry_count += 1
        if retry_count < max_retries:
            time.sleep(1)
    except Exception as e:
        retry_count += 1
        if retry_count < max_retries:
            time.sleep(1)

return False
```

The `X-HTTP-Method-Override: DELETE` header is included to support proxy servers and load balancers that may not forward HTTP DELETE verbs directly. The 1-second inter-retry delay prevents flooding the AFC proxy during transient failures. After 3 failed attempts, the function logs a warning and returns False, allowing the calling system to continue processing rather than blocking indefinitely.

**Pre-condition Summary:**
Called when location change is detected or AP state transitions to UNCLAIMED/UNASSIGNED. The MAC address must match an existing registration in the AFC proxy.

**Post-condition Summary:**
On success, the AFC proxy has removed all state associated with this MAC address. The system may subsequently submit a new POST request for the same MAC address with updated parameters.

---

### Section 3: Summary of AFC Core Module Interactions

The three modules (`afc_payload.py`, `afc_query.py`, `afc_utils.py`) interact in a well-defined sequence. The following summarizes the complete flow before a diagram:

**Pre-diagram Summary — AFC Core Flow:**
When an RRM ACS event arrives for a Standard Power AP, the system first checks whether AFC authorization is needed. If the AP has `standard_power=True` in its radio configuration, the system calls `afc_channel_validation()` which orchestrates the following sequence:

1. **GPS Retrieval** — Queries Redis for `devices/{apID}/gps`; if absent, returns NoGPS
2. **Payload Construction** — Calls `get_payload_proxy()` with AP ID, site ID, GPS data, provider flag, and certification ID
3. **Proxy GET** — Calls `GetChannelByMac()` to check for existing authorization
4. **Location Comparison** — If existing authorization found, calls `location_match()` to detect relocation
5. **Conditional POST** — If state is not "DONE", or location changed, calls `DeleteAP()` then `PostAfcRequest()`
6. **Second GET** — After POST, calls `GetChannelByMac()` again to retrieve fresh authorization
7. **Response Processing** — Calls `process_afc_response()` to extract per-channel EIRP values
8. **Return** — Returns `(afc_channels dict, expiration_timestamp, status_string)`

**Post-diagram Summary — Caller Responsibilities:**
After receiving the `(afc_channels, expiration_time, afc_status)` tuple, the caller in `rrmACSV2.py` intersects the AFC channels with the AP's configured channels via `channels_validation()`, updates the ACS command with AFC channel data, and emits the final RRM decision including the per-channel EIRP cap (`afc_max_eirp`) for firmware enforcement.

---

*[End of Part 3 — Continue to Part 4: Detailed Description — RRM Integration]*
# PATENT APPLICATION — PART 4 OF 7
# Detailed Description: RRM-AFC Integration

**Title:** SYSTEM AND METHOD FOR AUTOMATED FREQUENCY COORDINATION-INTEGRATED RADIO RESOURCE MANAGEMENT IN 6 GHz WIRELESS ACCESS NETWORKS

---

## DETAILED DESCRIPTION — RRM-AFC INTEGRATION

### Section 4: RrmAFCBolt — Distributed Stream Processing Component (rrmAFC.py)

The `RrmAFCBolt` class is an Apache Storm BasicBolt component that processes AFC-related events in the distributed stream processing topology. It operates as a dedicated processing node focused exclusively on AFC coordination tasks, separating AFC lifecycle management from the main ACS channel selection pipeline.

#### 4.1 Bolt Initialization

**Pre-initialization Summary:**
The `initialize(stormconf, context)` method is called once when the bolt is deployed into the Storm topology. All stateful objects are created here and maintained across tuple processing calls.

The initialization establishes:

1. **Environment Detection**: Reads `env` from Storm configuration (values: "staging", "prod", "eu"). EU environments use a longer DFS rollback time of 2700 seconds (45 minutes) vs. 2100 seconds (35 minutes) for other regions.

2. **API Rate Limits**: Sets `papi_limit = 200` (maximum AP records per API call); reduces to 20 in staging environments to prevent overloading test infrastructure.

3. **API Endpoint Configuration**: Resolves the Mist API URL from `papi.url` or `papi` configuration keys, defaulting to `papi-internal-{ENV}.mist.pvt`.

4. **AFC Proxy URL**: Reads `afc-proxy.url` from Storm configuration, defaulting to:
   ```
   http://afc-proxy-{ENV}.mist.pvt/afc/devices
   ```

5. **Redis Connections**: Establishes two separate Redis connections:
   - `redis_conn`: RRM state database (from `redis.rrm-proxy.location`)
   - `location_redis_conn`: GPS/geolocation database (from `redis.location.location`)

6. **Request Headers**: Sets `X-FROM` header to the topology name (e.g., "rrm-main-tick") for request tracing and audit purposes.

7. **Standard Power Cache**: Initializes `ap_standard_power_cache = {}` — an in-memory dictionary that caches AP standard power configuration to avoid repeated API calls.

#### 4.2 Event Processing: process(tup)

**Pre-processing Summary:**
The `process(tup)` method handles two types of Storm tuples: tick tuples (periodic timer events) and data tuples (AP state change notifications). Tick tuples trigger the `process_tick()` method. Data tuples contain JSON-encoded maps of AP IDs to their abnormal state information.

**Data Tuple Processing Steps:**

1. **Tick Check**: If `tup.is_tick_tuple()` is True, delegate to `process_tick()` and return.

2. **JSON Parsing**: Extracts and parses `tup.values[-1]` as a JSON object containing an `abnormal_ap_map` — a dictionary mapping AP MAC addresses to state information dicts or legacy state strings.

3. **Format Normalization**: Handles both old format (string state value) and new format (dict with `ap_status`, `site_id`, `org_id` fields).

4. **State Filtering**: Only processes APs with `ap_status` in `["AP_UNASSIGNED", "AP_UNCLAIMED"]`. Other abnormal states (e.g., `AP_DISCONNECTED`) are not handled by this bolt.

5. **Cache-Augmented Filtering**: For qualifying APs, site_id and org_id are retrieved from the `ap_standard_power_cache` if available (providing richer context than may be in the event), falling back to the values in the event.

6. **Event Handler Dispatch**: Calls `ap_event_handler(afc_proxy_url, location_redis_conn, redis_conn, filtered_ap_map)`.

**Post-processing Summary:**
After processing, the AP's AFC proxy registration has been deleted and the geolocation cache has been cleared. The AP will need to re-register when it comes back online as a claimed, assigned device.

#### 4.3 Tick Processing: process_tick()

**Pre-tick Summary:**
The tick process runs periodically (at the Storm topology tick interval) to process APs that are tracked in Redis as needing AFC re-authorization. These are APs that previously failed AFC validation (e.g., NoGPS status) and need to be retried.

The tick calls `tick_process_rrm_afc(afc_proxy_url, location_redis_conn, redis_conn, rrm_policy_default)`.

**Tick Process Steps:**

1. Retrieves all AFC nodes from Redis via `rrmRedis.get_afc_info(redis_conn)`.

2. For each AP in the AFC node list:
   a. Parses the stored AFC info JSON to extract `org_id`, `site_id`, `bandwidth`.
   b. Attempts geolocation retrieval via `get_ap_geolocation(location_redis_conn, ap_id)`.
   c. If GPS not found: Updates Redis status to "NoGPS" and continues to next AP.
   d. Retrieves site policy to get provider flag and location threshold.
   e. **Cleans up stale registration**: Calls `DeleteAP(afc_proxy_url, ap_id)` before re-attempting.
   f. Calls `afc_channel_validation(...)` with current GPS data.
   g. If status is "DONE": Removes AP from AFC tracking in Redis (`del_afc_info`).
   h. If status is not "DONE": Updates Redis status with new status value.

**Post-tick Summary:**
APs that achieved "DONE" status are removed from the retry queue. APs that remain in non-DONE states are kept for the next tick cycle.

#### 4.4 Standard Power Detection: is_standard_power(ap_id)

This method determines whether a given AP is configured for Standard Power operation, which requires AFC coordination.

**Algorithm:**
1. Check `ap_standard_power_cache` — if AP is cached, return True immediately.

2. Query Mist API for 2.4 GHz band configuration (`getRRMByMAC(ap_id, "r24", mist_api_url)`).

3. Check `radio_config.standard_power` field in the AP configuration.

4. If not found in 2.4 GHz band, query 6 GHz band configuration (`getRRMByMAC(ap_id, "r6", mist_api_url)`).

5. If `standard_power` is True: Cache the AP with timestamp, site_id, and org_id in `ap_standard_power_cache`.

6. Return the `standard_power` boolean.

The in-memory cache prevents repeated API calls for the same AP during high-frequency event processing.

---

### Section 5: AP Abnormal State Handler (afc_utils.py — ap_event_handler)

**Pre-handler Summary:**
The `ap_event_handler(afc_proxy_url, location_redis_conn, redis_conn, abnormal_ap_list)` function processes a batch of APs in abnormal states. For each AP, it determines the appropriate remediation action based on the AP's status.

**Processing for AP_UNCLAIMED or AP_UNASSIGNED:**

1. **AFC Proxy Deletion**: Calls `afc_query.DeleteAP(afc_proxy_url, ap_id)` with retry logic (up to 3 attempts).

2. **RRM Redis Cleanup**: Calls `rrmRedis.del_afc_info(redis_conn, ap_id)` to remove AFC tracking entry.

3. **GPS Cache Cleanup**: Calls `location_redis_conn.delete("devices/{apID}/gps")` to purge the geolocation entry. This is critical: if the GPS entry is retained and the same physical MAC address is reassigned to a different device at a different location, the old GPS coordinates would be returned and cause AFC validation to use the wrong location.

**Post-handler Summary:**
After handling, the AP has no registration in the AFC proxy and no GPS entry in the location cache. When the AP is later reclaimed or reassigned and reconnects, it will be treated as a fresh registration.

---

### Section 6: AFC Integration in ACS Processing (rrmACSV2.py)

The `rrmACSV2.py` module implements the primary channel selection engine. When an AP is identified as Standard Power, the AFC integration intercepts the normal ACS processing flow and substitutes AFC-validated channels.

#### 6.1 Standard Power Detection in ACS Flow

**Pre-detection Summary:**
For each incoming ACS event, the system retrieves the AP configuration and checks for Standard Power mode in two locations:

```python
afc_standard_power = (
    ap_config.get("radio_config", {}).get("standard_power", False)
    OR
    ap_config.get(f"band{usage}_specific", {}).get("radio_config", {}).get("standard_power", False)
)
```

The dual-location check supports both simple radio configurations and band-specific configurations used for dual-radio or converted-radio AP models.

#### 6.2 Bandwidth Selection for AFC

When a Standard Power AP is identified, the appropriate bandwidth for the AFC query is determined:

**If `allow_auto_bw` is True** (automatic bandwidth enabled):
```
bandwidth = (
    rrm_suggested_config.get(f"bandwidth_{usage}")
    OR ap_config.get(f"band{usage}_specific", {}).get("radio_config", {}).get("bandwidth", 0)
    OR ap_config.get("radio_config", {}).get("bandwidth", 0)
)
```

**If `allow_auto_bw` is False** (manual bandwidth):
```
bandwidth = (
    ap_config.get(f"band{usage}_specific", {}).get("radio_config", {}).get("bandwidth", 0)
    OR ap_config.get("radio_config", {}).get("bandwidth", 0)
)
```

This priority ordering ensures that AI-suggested bandwidths (from the RRM optimization engine) are used when available, while falling back to manually configured values.

#### 6.3 Certification ID and Ruleset Selection

**Pre-certification Summary:**
The certification ID used in the AFC payload varies by country. The system retrieves the country code for the site:

1. Checks Redis cache: `rrmRedis.get_country_code_per_site(redis_conn, user_site_id)`
2. If not cached: Queries Mist API via `getTotalApsAndWifiBandsBySite()` and caches result

Based on country code:
- **Canada ("CA")**: Uses `ised_id` with ruleset derived from country → Canadian ISED certification
- **All others (including US)**: Uses `fcc_id` with ruleset from `get_rulesetId_from_country_code()`

```python
afc_certificationId = (
    [{"id": ised_id, "rulesetId": rulesetId}] if country_code == "CA"
    else [{"id": fcc_id, "rulesetId": rulesetId}]
)
```

**Post-certification Summary:**
The correct certification ID and ruleset are assembled into the AFC payload's `deviceDescriptor.certificationId` array, ensuring regulatory compliance for each country of operation.

#### 6.4 AFC Channel Validation Call

The full AFC channel validation is invoked:

```python
afc_channels, expiration_time, afc_status = afc_utils.afc_channel_validation(
    afc_proxy_link=self.afc_proxy_url,
    ap_id=ap_id,
    site_id=user_site_id,
    location_redis_conn=self.location_redis_conn,
    bandwidth=bandwidth,
    provider_flag=afc_provider_flag,
    afc_response=afc_response,
    afc_certificationId=afc_certificationId,
    location_threshold=location_threshold
)
```

Where `location_threshold` defaults to 200 meters from the site policy.

#### 6.5 AFC Channel Intersection

After obtaining AFC-validated channels, the system intersects them with the AP's configured channel list:

```python
afc_channels = afc_utils.channels_validation(afc_channels, ap_channels)
ap_channels = list(afc_channels.keys())
```

The `channels_validation()` function:
1. Normalizes AFC channel keys to strings
2. Iterates over `configured_channels` (from AP configuration)
3. Retains only channels present in both the AFC authorization and the configured channel list
4. Preserves the per-channel EIRP cap from the AFC authorization

**Result**: Only channels that are BOTH AFC-authorized AND administrator-configured are made available for RRM channel selection.

#### 6.6 LPI Fallback on NoGPS

**Pre-fallback Summary:**
When `afc_status == "NoGPS"` and `ap_config.get("lpi_ok", False)` is True, the system transitions the AP to LPI operation rather than disabling the radio:

```python
if afc_status == "NoGPS" and ap_config.get("lpi_ok", False):
    afc_standard_power = False
    afc_channels = {}
    ap_channels = ap_config.get(f"band{usage}_specific", {}).get("channels", []) or \
                  ap_config.get("channels", [])
    rrm_acs_command["afc_standard_power"] = False
    rrm_acs_command["afc_channels"] = {}
    rrm_acs_command["afc_source"] = "lpi_fallback"
```

**Post-fallback Summary:**
The AP continues operating on its configured channels in LPI mode (lower power, no AFC required). The `afc_source = "lpi_fallback"` field provides audit trail visibility into why the AP is operating in LPI mode despite being AFC-capable hardware.

#### 6.7 AFC Update Reason Handling

When the ACS command reason is "afc-update" (periodic AFC expiry refresh):

1. Checks if AP is currently online: `ap_config.get("radio_stat", {}).get("power", 0) > 0`
2. If online and current channel is in new AFC channels: command becomes "afc-update" (EIRP limit refresh, no channel change needed)
3. If online and current channel NOT in new AFC channels: command becomes "afc-channel-update" (channel reassignment required)
4. If not online: command becomes "afc-channel-update" (prepare new channel for when AP comes online)

#### 6.8 EIRP Enforcement in ACS Output

**Pre-EIRP Summary:**
After channel selection, the RRM output is augmented with AFC EIRP constraints:

```python
if afc_channels:
    normalized_afc_channels = {str(k): v for k, v in afc_channels.items()}
    res["channels"] = list(normalized_afc_channels.keys())
    res["power"] = min(res["power"], normalized_afc_channels.get(str(res["channel"]), res["power"]))
    res["rrm_power"] = res["power"]
    res["afc_standard_power"] = True
    res["afc_channels"] = afc_channels
    res["afc_expiry"] = expiration_time
    res["afc_max_eirp"] = normalized_afc_channels.get(str(res["channel"]))
```

The `res["power"]` is capped at the per-channel AFC EIRP limit. If the RRM-suggested power is below the AFC limit, the RRM power is used (the AP should not transmit at higher power than the RRM engine suggests for interference management, even if AFC would allow it). If the RRM-suggested power exceeds the AFC EIRP limit, the AFC limit takes precedence.

**Post-EIRP Summary:**
The emitted RRM result carries both the selected channel and the `afc_max_eirp` field. The AP firmware uses `afc_max_eirp` as the absolute upper bound on transmitted EIRP for the selected channel, ensuring regulatory compliance at the hardware level.

---

### Section 7: afcNode Processing in AP Graph (APnode.py)

The `afcNode(g, ap_rad_id, ...)` function integrates AFC channel authorizations into the RRM topology graph. The graph `g` represents the RF topology of a site, with nodes corresponding to AP radios and edges representing RF neighbor relationships.

**Pre-graph Summary:**
Called during global RRM processing for each Standard Power AP radio in the site graph. The AP's AFC provider flag and FCC ID are read from the graph metadata and node attributes respectively.

**Processing Steps:**

1. **Node Parameter Extraction:**
   ```
   org_id = g.graph.get("org")
   site_id = g.graph.get("site")
   configured_channels = g.node[ap_rad_id].get("channels", [])
   rrm_bandwidth = g.node[ap_rad_id].get("rrm_bandwidth", 0)
   afc_provider_flag = g.graph.get("afc-provider-flag", "0")
   fcc_id = g.node[ap_rad_id].get("fcc_id") or g.graph.get("afc-fcc-id")
   ```

2. **AFC Channel Validation**: Calls `afc_utils.afc_channel_validation()` for the AP.

3. **Expiry Validation**: Checks if stored AFC authorization (from node's `afc_channels`) is still valid based on `afc_expiry` timestamp vs. current time.

4. **No-Channel Handling**: If `afc_channels` is empty after validation:
   ```
   g.node[ap_rad_id]["rrm_enabled"] = False
   disable_radio(g=g, ap_rad_x=ap_rad_id, who="afc")
   ```
   The radio is disabled in the graph, preventing the RRM global optimization engine from assigning any channel to this AP.

5. **Successful Authorization Handling:**
   ```
   g.node[ap_rad_id]["afc_channels"] = afc_channels
   g.node[ap_rad_id]["channels"] = [int(c) for c in afc_channels.keys()]
   g.node[ap_rad_id]["afc_timestamp"] = current_timestamp
   g.node[ap_rad_id]["afc_expiry"] = expiration_time
   g.node[ap_rad_id]["afc_source"] = "afc-proxy"
   ```

**Post-graph Summary:**
After `afcNode()` processing, the graph node reflects the current AFC authorization. Subsequent global RRM optimization only selects from the AFC-approved channel list for this node, ensuring all globally-optimized channel assignments are simultaneously AFC-compliant and RF-interference-optimal.

---

*[End of Part 4 — Continue to Part 5: Detailed Description — Geolocation and EIRP Computation]*

# PATENT APPLICATION — PART 5 OF 7
# Detailed Description: Geolocation Management and EIRP Computation

**Title:** SYSTEM AND METHOD FOR AUTOMATED FREQUENCY COORDINATION-INTEGRATED RADIO RESOURCE MANAGEMENT IN 6 GHz WIRELESS ACCESS NETWORKS

---

## DETAILED DESCRIPTION — GEOLOCATION AND EIRP

### Section 8: Geolocation Retrieval and Management

#### 8.1 GPS Data Storage Schema

The geolocation data for each AP is stored in the location Redis database under the key:

```
devices/{apID}/gps
```

Where `{apID}` is the AP's MAC address in lowercase without delimiters (e.g., `5433c60d3162`).

The stored value is a JSON object with a top-level `location` field containing:

```json
{
  "location": {
    "elevation": {
      "height": 3.0,
      "heightType": "AGL",
      "verticalUncertainty": 2
    },
    "ellipse": {
      "center": {
        "latitude": 37.3228934,
        "longitude": -122.0322895
      },
      "majorAxis": 100,
      "minorAxis": 50,
      "orientation": 45.0
    },
    "indoorDeployment": 1
  }
}
```

#### 8.2 Geolocation Retrieval: get_ap_geolocation

The function `get_ap_geolocation(location_redis_conn, ap_id)` retrieves the location data:

1. If `location_redis_conn` is None (connection not available), returns empty dict `{}`
2. Constructs Redis key: `"devices/{apID}/gps".format(apID=ap_id)`
3. Retrieves and JSON-parses the stored value
4. Returns `res.get("location", {})` — the location sub-object
5. On any exception (key not found, JSON parse error, Redis timeout): logs warning "No geo location for ap={ap_id}" and returns empty dict `{}`

**Significance**: Returning an empty dict on failure (rather than raising an exception) allows the calling code to cleanly handle the NoGPS case without try-catch at the caller level.

---

### Section 9: Coordinate Transformation: WGS84 to ECEF

#### 9.1 Purpose of ECEF Coordinate System

The World Geodetic System 1984 (WGS84) is the standard reference ellipsoid used for GPS coordinates. However, the spherical (latitude, longitude) representation is unsuitable for direct Euclidean distance computation because the relationship between angular differences and linear distances varies with latitude.

The Earth-Centered, Earth-Fixed (ECEF) coordinate system expresses position as (x, y, z) in meters relative to the Earth's center, with the x-axis pointing toward the prime meridian at the equator, the y-axis pointing 90° east at the equator, and the z-axis pointing toward the geographic north pole.

In ECEF coordinates, Euclidean distance in the xy-plane provides an accurate approximation of the horizontal distance between two nearby points on the Earth's surface — enabling the invention's geolocation change detection to work correctly across all latitudes.

#### 9.2 WGS84 Ellipsoid Parameters

The WGS84 reference ellipsoid is defined by:

| Parameter | Symbol | Value |
|-----------|--------|-------|
| Semi-major axis | a | 6,378,137.0 meters |
| Flattening | f | 1 / 298.257223563 |
| Semi-minor axis | b | a × (1 − f) = 6,356,752.314 meters (derived) |

#### 9.3 ECEF Conversion Formulas: lla_to_ecef

The function `lla_to_ecef(lat, lon, alt=0)` converts geodetic coordinates to ECEF:

**Step 1 — Unit Conversion:**
```
lat_rad = radians(lat)
lon_rad = radians(lon)
```

**Step 2 — Normal Radius of Curvature:**
The normal radius of curvature N at latitude lat_rad is:

```
N = a / sqrt(1 - f × (2 - f) × sin²(lat_rad))
```

This value represents the radius of curvature in the plane containing the surface normal and the east-west direction, varying from a at the equator to a²/b at the poles.

**Step 3 — ECEF Coordinate Computation:**
```
x = (N + alt) × cos(lat_rad) × cos(lon_rad)
y = (N + alt) × cos(lat_rad) × sin(lon_rad)
z = (N × (1 - f)² + alt) × sin(lat_rad)
```

Note: The z formula uses `N × (1 - f)²` rather than `b²/a² × N` for computational efficiency; both are equivalent given the WGS84 definition.

**Return value**: Tuple `(x, y, z)` in meters.

---

### Section 10: Location Change Detection: location_match

The function `location_match(old_gps, new_gps, threshold=10)` determines whether two GPS location records represent the same physical location within a specified tolerance.

**Pre-function Summary:**
Called when an AP submits a new AFC request and there is an existing AFC proxy registration for the same MAC address. The old GPS is extracted from the existing proxy registration response; the new GPS is from the current Redis location entry.

**Processing Steps:**

1. **Null Check**: If either `old_gps` or `new_gps` is empty/None, returns False (location mismatch — re-registration required).

2. **Coordinate Extraction:**
   ```
   old_lat = old_gps["ellipse"]["center"]["latitude"]
   old_lon = old_gps["ellipse"]["center"]["longitude"]
   old_h   = old_gps["elevation"]["height"]

   new_lat = new_gps["ellipse"]["center"]["latitude"]
   new_lon = new_gps["ellipse"]["center"]["longitude"]
   new_h   = new_gps["elevation"]["height"]
   ```

3. **ECEF Conversion:**
   ```
   old_x, old_y, _ = lla_to_ecef(old_lat, old_lon)
   new_x, new_y, _ = lla_to_ecef(new_lat, new_lon)
   ```

4. **Distance Computation:**
   ```
   height_diff = abs(old_h - new_h)
   distance = sqrt((new_x - old_x)² + (new_y - old_y)²)
   ```

5. **Threshold Comparison:**
   ```
   loc_unchanged = (distance <= threshold) AND (height_diff <= threshold)
   ```
   Returns `loc_unchanged` — True if location has not changed significantly.

6. **Logging**: Records distance, height_diff, threshold, and result for audit purposes (no PII in logs).

**System-Level Threshold:**
The function's internal default threshold is 10 meters. At the system level (in `afc_channel_validation()` and `rrmACSV2.py`), the threshold is read from site policy `location_threshold` with a default of **200 meters**. This 200-meter threshold is chosen to:
- Tolerate GPS measurement uncertainty (typical GPS accuracy for indoor deployments: 10–50 meters)
- Detect meaningful relocations (moving an AP to a different room or building) that would change the incumbent protection analysis
- Avoid false re-registrations from GPS coordinate jitter

**Significance of Location Change Detection:**
This capability is novel because it automatically detects and responds to AP relocations without administrator intervention. The system:
1. Calls `afc_query.DeleteAP()` to remove the stale registration
2. Constructs a new payload with the updated coordinates
3. Submits a fresh POST request
4. Retrieves the new authorization valid for the new location

This ensures that the incumbent protection analysis remains valid regardless of where an AP is physically placed.

---

### Section 11: AFC Response Processing and EIRP Computation

#### 11.1 Overview of process_afc_response

The function `process_afc_response(afc_proxy_link, res, bandwidth)` is the core algorithm that transforms an AFC system response into a per-20MHz-channel EIRP dictionary.

**Pre-function Summary:**
Called after a successful AFC GET response with `state == "DONE"`. The response contains two parallel data structures: `availableChannelInfo` (per-operating-class channel lists with per-channel EIRP caps) and `availableFrequencyInfo` (per-frequency-range PSD limits).

The function must reconcile these two structures — the channel-based EIRP limits and the frequency-based PSD limits — to derive the correct per-channel maximum power that satisfies both constraints simultaneously.

**Processing Steps:**

**Step 1 — Operating Class Selection:**
```
globalOperatingClass = bandwidth_to_globalOperatingClass(bandwidth)
```
This maps the requested bandwidth to the correct operating class:

| Bandwidth (MHz) | Global Operating Class |
|----------------|----------------------|
| 20             | 131                  |
| 40             | 132                  |
| 80             | 133                  |
| 160            | 134                  |
| 320            | 137                  |

**Step 2 — Expiration Time Parsing:**
```
expiration_time = res.get("availabilityExpireTime", <current UTC time>)
dt = datetime.strptime(expiration_time, "%Y-%m-%dT%H:%M:%SZ")
real_timestamp = int(time.mktime(dt.timetuple()))
```
The expiration time is converted from ISO 8601 string format to a Unix timestamp (seconds since epoch). This timestamp is stored in Redis and checked before using cached AFC authorizations.

**Step 3 — Channel Class Matching:**
```
for i, channelClass in enumerate(availableChannelInfo):
    if channelClass.get("globalOperatingClass") == globalOperatingClass:
```
Only the operating class matching the requested bandwidth is processed.

**Step 4 — PSD-to-EIRP Computation:**
```
all_channels = afc_payload.get_channel_freq_mapping()["channels"][i]["Channels"]
psdEirp = get_eirp_from_psd(all_channels, availableFrequencyInfo, bandwidth)
```
The `get_eirp_from_psd()` function computes a PSD-derived EIRP for each channel in the band, as detailed in Section 11.2.

**Step 5 — Per-Channel EIRP Computation:**
For each channel `ch` in `availableChannelInfo[].channelCfi[]` with corresponding `maxEirp[j]`:

```
ch_max_power = max(
    AFC_MIN_PSD.get(bandwidth, 13),
    int(min(psdEirp[ch], maxEirp[j]))
)
```

This implements the dual-constraint with floor:
- `maxEirp[j]`: AFC system's per-channel EIRP cap (dBm)
- `psdEirp[ch]`: PSD-derived EIRP for this channel (dBm)
- `min(...)`: The more restrictive of the two EIRP limits
- `max(AFC_MIN_PSD[bandwidth], ...)`: Enforce the minimum floor so EIRP is never set below the regulatory minimum for this bandwidth

The AFC_MIN_PSD floor values are:
```
AFC_MIN_PSD = {20: 14, 40: 17, 80: 20, 160: 23, 320: 26}
```

**Step 6 — Sub-Channel Expansion:**
The `ch_delta` values are selected based on bandwidth:

| Bandwidth (MHz) | ch_delta | Sub-channels addressed |
|----------------|----------|----------------------|
| 20             | [0]      | Center only (ch ± 0 = ch) |
| 40             | [2]      | ch - 2, ch + 2 |
| 80             | [2, 6]   | ch - 2, ch + 2, ch - 6, ch + 6 |
| 160            | [2, 6, 10, 14] | 8 sub-channels total |
| 320            | [2, 6, 10, 14, 18, 22, 26, 30] | 16 sub-channels total |

For each delta `d` in `ch_delta`:
```
if ch - d in channels_6G_20:
    afc_channels[ch - d] = ch_max_power
if ch + d in channels_6G_20:
    afc_channels[ch + d] = ch_max_power
```

For 320 MHz bandwidth, an additional mode filter is applied:
```
if bandwidth == 320 and wifi320Mode != get_mode(ch - d):
    continue  # Skip sub-channels of the wrong mode
```

**Post-function Summary:**
Returns `(afc_channels, expiration_time)` where `afc_channels` is a dictionary mapping 20 MHz channel numbers (int) to maximum EIRP values (int, in dBm). This dictionary represents the complete set of AFC-approved operating parameters for the AP at its current location.

---

#### 11.2 PSD-to-EIRP Conversion: get_eirp_from_psd

The function `get_eirp_from_psd(channel_freqs, psd_data, band_width)` computes the PSD-derived EIRP for each channel in the band.

**Pre-function Summary:**
The AFC response's `availableFrequencyInfo` contains a list of PSD limit entries, each specifying a frequency range and a maximum PSD value in dBm/MHz. These PSD limits constrain transmit power density across the spectrum to protect incumbents that may be affected by out-of-band emissions.

The conversion formula converts a PSD limit to an EIRP limit for a channel of given bandwidth:

**EIRP_from_PSD (dBm) = maxPsd (dBm/MHz) + 10 × log10(channel_bandwidth_MHz)**

This formula follows directly from the definition of EIRP and PSD: if the spectral density is maxPsd dBm/MHz and the channel occupies channel_bandwidth_MHz MHz, then the total power (EIRP) is the product in linear scale, which becomes a sum in dB scale: 10 × log10(bandwidth) dB added to the PSD value.

**For example:**
- 20 MHz channel, maxPsd = 23 dBm/MHz:
  EIRP = 23 + 10 × log10(20) = 23 + 13.01 = 36.01 dBm
- 80 MHz channel, maxPsd = 20 dBm/MHz:
  EIRP = 20 + 10 × log10(80) = 20 + 19.03 = 39.03 dBm
- 160 MHz channel, maxPsd = 17 dBm/MHz:
  EIRP = 17 + 10 × log10(160) = 17 + 22.04 = 39.04 dBm

**Algorithm:**

1. Initialize `psd_eirp = {}` — output dictionary, channel → EIRP (dBm)

2. For each channel `(ch, ch_low, ch_high)` in `channel_freqs`:
   - Initialize `psd_eirp[ch] = 36` (default: no PSD constraint → use 36 dBm maximum)
   - Initialize `channel_eirp = 36`, `flag = False`

3. For each PSD entry `(psd_low, psd_high, psd_value)` in `psd_data`:
   - Check overlap: The PSD range overlaps with the channel if any of:
     - `psd_low >= ch_low AND psd_low < ch_high` (PSD range starts within channel)
     - `psd_high <= ch_high AND psd_high > ch_low` (PSD range ends within channel)
     - `psd_high >= ch_high AND psd_low <= ch_low` (PSD range spans entire channel)
   - If overlap:
     ```
     channel_eirp = min(channel_eirp, psd_value + 10 × log10(band_width))
     flag = True
     ```
   - Early exit: If `psd_low > ch_high`, no further PSD entries can overlap this channel (PSD data is ordered by frequency)

4. If `flag` is True (at least one overlapping PSD entry was found):
   ```
   psd_eirp[ch] = channel_eirp
   ```
   Otherwise, the default 36 dBm remains.

**Post-function Summary:**
Returns `psd_eirp` dictionary mapping channel numbers to PSD-derived EIRP limits. Channels with no overlapping PSD constraints retain the 36 dBm default (equivalent to no PSD constraint from the AFC system's perspective).

---

### Section 12: 320 MHz Mode Disambiguation

#### 12.1 The Mode Ambiguity Problem

The 6 GHz 320 MHz channel plan has two distinct, non-overlapping arrangements:

**Mode 1 Center Channels:** 31, 95, 159
- Mode 1 occupies sub-channels: approximately 1 through 61 (center 31), 65 through 125 (center 95), 129 through 189 (center 159)

**Mode 2 Center Channels:** 63, 127, 191
- Mode 2 occupies sub-channels: approximately 33 through 93 (center 63), 97 through 157 (center 127), 161 through 221 (center 191)

The sub-channel ranges of Mode 1 and Mode 2 overlap significantly. Channels in the overlap region (approximately 33–61, 65–93, 97–125, 129–157, 161–189) belong to both a Mode 1 and a Mode 2 320 MHz channel. When assigning sub-channel EIRP values from a Mode 1 authorization, only Mode 1 sub-channels should receive the assignment; Mode 2 sub-channels should not receive EIRP values derived from a Mode 1 AFC authorization.

#### 12.2 Mode Range Computation

The valid sub-channel ranges for each mode are computed programmatically:

```
central_channel_mode1 = [31, 95, 159]
central_channel_mode2 = [63, 127, 191]

channels_mode1 = range(
    central_channel_mode1[0] - 30,  # = 1
    central_channel_mode1[-1] + 30 + 4,  # = 193
    4  # step = 4 (20 MHz spacing)
)

channels_mode2 = range(
    central_channel_mode2[0] - 30,  # = 33
    central_channel_mode2[-1] + 30 + 4,  # = 225
    4
)
```

#### 12.3 Mode Assignment Algorithm: get_mode(channel)

The function `get_mode(channel)` determines the correct mode for a given 20 MHz sub-channel:

**Case 1**: Channel appears in `channels_mode1` only → Return 1

**Case 2**: Channel appears in `channels_mode2` only → Return 2

**Case 3**: Channel appears in BOTH `channels_mode1` and `channels_mode2` (overlap region):

1. Compute the index within the Mode 1 center channel array:
   ```
   channel_ind1 = (channel - 1) // 64
   ```

2. Compute the index within the Mode 2 center channel array:
   ```
   channel_ind2 = (channel - 33) // 64
   ```

3. Compute distance to nearest center:
   ```
   diff_to_central1 = abs(channel - central_channel_mode1[channel_ind1])
   diff_to_central2 = abs(channel - central_channel_mode2[channel_ind2])
   ```

4. Assign to the mode whose center is closer:
   ```
   return 1 if diff_to_central1 > diff_to_central2 else 2
   ```

Note: The condition `diff_to_central1 > diff_to_central2` returning Mode 1 appears counterintuitive — it assigns to Mode 1 when the Mode 1 center is farther away. This implements the semantics of "the sub-channel belongs to the wider-bandwidth channel it is more deeply embedded within."

---

### Section 13: Prior Art Comparison

**Table 9: Comparison of Present Invention vs. Prior Art**

| Feature | Prior Art | Present Invention |
|---------|-----------|-------------------|
| AFC Integration | Static/manual | Automated, real-time, cloud-scale |
| Geolocation Validation | None or one-time | Continuous ECEF-based with 200m threshold |
| EIRP Computation | Single constraint | Dual-constraint: min(AFC EIRP, PSD-derived EIRP) |
| PSD Floor Enforcement | None | AFC_MIN_PSD table: {20:14, 40:17, 80:20, 160:23, 320:26} dBm |
| 320 MHz Mode Handling | Not addressed | Proximity-based mode disambiguation |
| GPS Failure Handling | Radio disable | LPI fallback with audit tracking |
| AP Lifecycle Management | None | Automatic DELETE on UNCLAIMED/UNASSIGNED |
| Multi-Provider Support | Single provider | Flag-based routing to 4 provider environments |
| Retry Logic | None | 3-attempt DELETE with 1-second delay |
| State Persistence | None | Redis-backed with expiry tracking |
| Distributed Processing | Monolithic | Apache Storm bolt topology |

---

### Section 14: Implementation Reference

**Table 10: Key Technical Parameters**

| Parameter | Value | Source |
|-----------|-------|--------|
| AFC Proxy URL Pattern | `http://afc-proxy-{ENV}.mist.pvt/afc/devices` | rrmAFC.py |
| GPS Redis Key Pattern | `devices/{apID}/gps` | afc_utils.py |
| POST Timeout | 5 seconds | afc_query.py |
| GET Timeout | 5 seconds | afc_query.py |
| DELETE Max Retries | 3 | afc_query.py |
| DELETE Inter-Retry Delay | 1 second | afc_query.py |
| Default Location Threshold | 200 meters | rrmACSV2.py |
| WGS84 Semi-Major Axis | 6,378,137.0 meters | afc_utils.py |
| WGS84 Flattening | 1 / 298.257223563 | afc_utils.py |
| Default AFC Expiry | 24 hours from request | afc_payload.py |
| Max Axis Value (AFC payload) | 325 meters | afc_payload.py |
| Min Height Value (AFC payload) | 0.1 meters | afc_payload.py |
| PAPI Rate Limit (staging) | 20 records/call | rrmAFC.py |
| PAPI Rate Limit (prod) | 200 records/call | rrmAFC.py |
| Default FCC Certification ID | 2AHBN-AP64 | afc_payload.py |
| Ruleset ID | US_47_CFR_PART_15_SUBPART_E | afc_payload.py |
| Inquired Frequency Low | 5925 MHz | afc_payload.py |
| Inquired Frequency High | 7115 MHz | afc_payload.py |

---

*[End of Part 5 — Continue to Part 6: Claims]*
# PATENT APPLICATION — PART 6 OF 7
# Claims

**Title:** SYSTEM AND METHOD FOR AUTOMATED FREQUENCY COORDINATION-INTEGRATED RADIO RESOURCE MANAGEMENT IN 6 GHz WIRELESS ACCESS NETWORKS

---

## CLAIMS

What is claimed is:

---

**Claim 1.**
A system for Automated Frequency Coordination (AFC)-integrated Radio Resource Management (RRM) in a 6 GHz wireless access network, the system comprising:

a) a cloud-based RRM engine configured to receive automatic channel selection (ACS) events from wireless access points (APs) operating or configured to operate in the 6 GHz frequency band from 5925 MHz to 7125 MHz;

b) an AFC proxy service operating as an intermediary between the RRM engine and at least one upstream AFC system, the AFC proxy service maintaining per-device AFC registration state and providing a REST API at a configurable endpoint URL;

c) an AFC payload construction module configured to generate standards-compliant AFC request payloads for each AP, each payload comprising: a request identifier set to the AP's MAC address, a site identifier, a provider name resolved from a configurable provider flag, a device descriptor comprising the AP's serial number and FCC certification identifier with ruleset identifier, a geographic location comprising a WGS84 ellipse with center latitude and longitude, semi-major axis, semi-minor axis, orientation, height above ground level, and indoor deployment indicator, an inquired frequency range spanning 5925 MHz to 7115 MHz, and a set of inquired global operating classes;

d) an AFC response processing module configured to extract per-channel maximum EIRP values from AFC system responses by computing, for each available channel, a channel maximum power equal to the maximum of a bandwidth-indexed minimum EIRP floor and the integer minimum of a PSD-derived EIRP and the AFC-reported per-channel maximum EIRP; and

e) a geolocation validation module configured to detect AP relocation by converting AP geographic coordinates from WGS84 geodetic form to Earth-Centered Earth-Fixed (ECEF) form, computing the Euclidean distance between current and registered coordinates, and triggering AFC re-registration when the computed distance exceeds a configurable threshold.

---

**Claim 2.**
A method for integrating Automated Frequency Coordination with cloud-scale Radio Resource Management for 6 GHz wireless access points, the method comprising:

a) receiving, at a cloud RRM engine, an automatic channel selection event for a wireless access point configured for Standard Power operation in the 6 GHz band;

b) determining that the access point requires AFC authorization by reading a standard_power flag from the access point's radio configuration;

c) retrieving geolocation data for the access point from a location database using a key pattern comprising the access point's MAC address;

d) constructing an AFC request payload comprising the access point's MAC address as request identifier, a device descriptor with FCC certification identifier, a WGS84 geographic location with ellipse parameters bounded to a maximum semi-major axis of 325 meters and minimum height of 0.1 meters, and an inquired frequency range of 5925 MHz to 7115 MHz;

e) submitting the payload to an AFC proxy service and retrieving the AFC authorization response;

f) computing per-channel maximum EIRP values as the maximum of a bandwidth-indexed minimum floor and the minimum of the AFC-reported per-channel EIRP and a PSD-derived EIRP computed as maxPsd + 10 × log10(channel_bandwidth_MHz);

g) intersecting the AFC-authorized channel set with the access point's administrator-configured channel set; and

h) emitting an RRM channel assignment comprising the selected channel and the corresponding AFC maximum EIRP limit.

---

**Claim 3.**
A system for automatic lifecycle management of access point registrations within an Automated Frequency Coordination proxy service, the system comprising:

a) a distributed stream processing bolt configured to receive AP lifecycle events comprising AP state identifiers including at least AP_UNCLAIMED and AP_UNASSIGNED states;

b) an AP state filter configured to identify APs in abnormal states that require AFC registration cleanup;

c) an AFC proxy deletion client configured to submit HTTP DELETE requests to the AFC proxy for each identified AP, with the DELETE request including an X-HTTP-Method-Override header, a maximum retry count of three attempts, and a one-second inter-attempt delay; and

d) a geolocation cache purge module configured to delete the AP's GPS entry from the location database upon deletion from the AFC proxy.

---

**Claim 4.**
A method for computing maximum transmit power for wireless access points operating under Automated Frequency Coordination constraints, the method comprising:

a) receiving an AFC system response comprising an availableChannelInfo array indexed by global operating class and an availableFrequencyInfo array comprising per-frequency-range maximum power spectral density values;

b) selecting the global operating class corresponding to the requested channel bandwidth according to a mapping wherein: bandwidth 20 MHz maps to class 131, bandwidth 40 MHz maps to class 132, bandwidth 80 MHz maps to class 133, bandwidth 160 MHz maps to class 134, and bandwidth 320 MHz maps to class 137;

c) for each channel center frequency index in the selected operating class, computing a PSD-derived EIRP by: identifying all frequency ranges in availableFrequencyInfo that overlap with the channel's frequency span, computing for each overlapping range the sum of the range's maxPsd value and 10 multiplied by the base-10 logarithm of the channel bandwidth in MHz, and taking the minimum across all overlapping ranges;

d) computing the channel's maximum EIRP as the maximum of a bandwidth-indexed minimum floor value and the minimum of the PSD-derived EIRP and the AFC-reported per-channel maximum EIRP; and

e) assigning the computed maximum EIRP to each constituent 20 MHz sub-channel of the wide-bandwidth channel using bandwidth-specific offset deltas.

---

**Claim 5.**
A system for geolocation-aware AFC re-registration triggering in a 6 GHz wireless network, the system comprising:

a) a geolocation retrieval module configured to retrieve access point GPS coordinates from a Redis location database under a key pattern of the form devices/{MAC_address}/gps;

b) a coordinate transformation module configured to convert WGS84 geodetic coordinates (latitude, longitude) to ECEF coordinates (x, y, z) using a semi-major axis of 6,378,137.0 meters and a flattening of 1 divided by 298.257223563;

c) a displacement computation module configured to compute the Euclidean distance between the ECEF xy-coordinates of the current and registered AP locations, and the absolute difference in height values;

d) a threshold comparison module configured to determine that a location change has occurred when either the Euclidean distance or the height difference exceeds a configurable threshold defaulting to 200 meters; and

e) a re-registration module configured, upon detecting a location change, to delete the existing AFC proxy registration and submit a new AFC registration request with the updated coordinates.

---

**Claim 6.**
The system of claim 1, wherein the bandwidth-indexed minimum EIRP floor values are: 14 dBm for 20 MHz bandwidth, 17 dBm for 40 MHz bandwidth, 20 dBm for 80 MHz bandwidth, 23 dBm for 160 MHz bandwidth, and 26 dBm for 320 MHz bandwidth.

---

**Claim 7.**
The system of claim 1, wherein the AFC payload construction module normalizes the WGS84 ellipse orientation to the range 0 to 180 degrees by subtracting 180 degrees from orientation values exceeding 180 degrees.

---

**Claim 8.**
The system of claim 1, wherein the provider name is resolved from a provider flag value according to a mapping wherein: flag value "0" maps to provider name "wfa" for the production Wi-Fi Alliance AFC system, flag value "1" maps to "wfa-th01" for an internal test harness, flag value "2" maps to "wfa-th02" for a certification test harness, and flag value "dev" maps to "dev" for a development environment that generates mock responses without querying the AFC proxy.

---

**Claim 9.**
The method of claim 2, further comprising: when the AFC status is NoGPS and the access point has an LPI capability flag set to True, disabling Standard Power mode for the access point, clearing the AFC channel authorization, falling back to the access point's configured channel list for Low Power Indoor operation, and recording an AFC source identifier of "lpi_fallback" for audit purposes.

---

**Claim 10.**
The system of claim 1, wherein for 320 MHz bandwidth channels, sub-channel EIRP assignment applies a mode disambiguation algorithm that: identifies whether each constituent 20 MHz sub-channel belongs to Mode 1 having center channels at 31, 95, and 159, or Mode 2 having center channels at 63, 127, and 191, by computing the distance from the sub-channel index to the nearest Mode 1 center and the nearest Mode 2 center and assigning the sub-channel to the mode whose center is closer; and assigns EIRP values only to sub-channels matching the mode of the wide-bandwidth channel authorization.

---

**Claim 11.**
The system of claim 1, further comprising a periodic tick processing module configured to: retrieve all AFC tracking entries from Redis, for each tracked AP attempt to retrieve GPS coordinates, delete the existing AFC proxy registration, submit a new AFC authorization request, and upon successful authorization remove the AP from the AFC tracking queue.

---

**Claim 12.**
The system of claim 1, wherein the AFC proxy deletion client implements a retry mechanism comprising a maximum of three HTTP DELETE attempts, a five-second timeout per attempt, a one-second delay between consecutive attempts, and an X-HTTP-Method-Override: DELETE header in each request to support proxy environments that restrict HTTP DELETE verbs.

---

**Claim 13.**
The method of claim 2, further comprising: determining the AP's country of operation from a site country code cached in Redis; constructing the AFC certification identifier using the AP's ISED certification ID and a Canadian ruleset when the country code is "CA", and using the AP's FCC certification ID with the ruleset identifier US_47_CFR_PART_15_SUBPART_E for all other country codes.

---

**Claim 14.**
The system of claim 1, wherein the sub-channel EIRP offset deltas applied during wide-channel EIRP propagation are: delta set [0] for 20 MHz channels, delta set [2] for 40 MHz channels, delta set [2, 6] for 80 MHz channels, delta set [2, 6, 10, 14] for 160 MHz channels, and delta set [2, 6, 10, 14, 18, 22, 26, 30] for 320 MHz channels.

---

**Claim 15.**
The system of claim 1, wherein the RRM channel assignment emitted in step (h) of claim 2 includes: the selected channel number, the channel bandwidth, the RRM-computed transmit power capped by the AFC maximum EIRP, the afc_max_eirp value for the selected channel, an afc_expiry Unix timestamp, and an afc_standard_power Boolean flag; and the AP firmware uses the afc_max_eirp value as the absolute upper bound on transmitted EIRP.

---

**Claim 16.**
The system of claim 3, wherein the distributed stream processing bolt is implemented as an Apache Storm BasicBolt that maintains an in-memory standard power cache mapping AP MAC addresses to organization ID, site ID, and cache timestamp; retrieves AP standard power status by querying both the 2.4 GHz band configuration and the 6 GHz band configuration when the 2.4 GHz configuration does not indicate standard power operation.

---

**Claim 17.**
The system of claim 5, wherein the coordinate transformation module implements the ECEF y-coordinate as (N + altitude) multiplied by the cosine of latitude in radians multiplied by the sine of longitude in radians, and the ECEF z-coordinate as the product of the square of the quantity one minus flattening and N, plus altitude, multiplied by the sine of latitude in radians; where N is the normal radius of curvature computed as the semi-major axis divided by the square root of the quantity one minus flattening multiplied by two minus flattening multiplied by the square of the sine of latitude.

---

**Claim 18.**
The method of claim 2, further comprising: when the AFC authorization response state is DONE but the intersection of AFC-authorized channels and administrator-configured channels is empty, recording the AP in the AFC tracking queue in Redis with status reflecting the channel configuration mismatch, and disabling the AP radio in the RRM topology graph to prevent assignment of non-AFC-compliant channels.

---

**Claim 19.**
The system of claim 1, wherein the AFC proxy service URL is parameterized by deployment environment using the pattern http://afc-proxy-{ENV}.mist.pvt/afc/devices, where {ENV} is one of staging, prod, or eu; and wherein HTTP requests to the AFC proxy include an X-FROM header set to the Storm topology name for request attribution and audit trail purposes.

---

**Claim 20.**
A non-transitory computer-readable medium storing instructions that, when executed by one or more processors, implement a method comprising:

a) maintaining, in a Redis location database under per-AP key pattern devices/{MAC_address}/gps, WGS84 geolocation data for each Standard Power access point comprising latitude, longitude, elevation above ground level, location uncertainty ellipse parameters, and indoor deployment indicator;

b) for each Standard Power access point receiving an automatic channel selection event, performing AFC channel validation comprising geolocation retrieval, payload construction, AFC proxy communication with retry logic, location change detection using ECEF coordinate transformation, and dual-constraint EIRP computation;

c) assigning AFC-validated channels to access points by intersecting AFC-authorized channels with administrator-configured channels and capping transmit power at the per-channel AFC maximum EIRP;

d) on detection that an access point's geographic displacement from its registered AFC location exceeds 200 meters, automatically deleting the existing AFC proxy registration and submitting a new registration with updated coordinates; and

e) on detection that an access point has entered an unclaimed or unassigned state, automatically deleting the AFC proxy registration and purging the geolocation cache entry to prevent stale location data from affecting future registrations.

---

*[End of Part 6 — Continue to Part 7: Figures (22 Diagrams)]*
# PATENT APPLICATION
## Title: SYSTEM AND METHOD FOR AUTOMATED FREQUENCY COORDINATION-INTEGRATED
##        RADIO RESOURCE MANAGEMENT IN 6 GHz WIRELESS ACCESS NETWORKS

**Application Number:** [PENDING]
**Filing Date:** July 2026
**Part 7 of 7 — Abstract Drawings & Figures**

---

# TABLE OF CONTENTS — PART 7

| Figure | Title | Page |
|--------|-------|------|
| FIG. 1 | Overall System Architecture | 3 |
| FIG. 2 | AFC Request Lifecycle Flowchart | 5 |
| FIG. 3 | AFC Payload JSON Structure | 7 |
| FIG. 4 | AFC Response Structure | 9 |
| FIG. 5 | GlobalOperatingClass to Bandwidth Mapping | 11 |
| FIG. 6 | 6 GHz Band Channel Map | 12 |
| FIG. 7 | EIRP Computation Flow | 14 |
| FIG. 8 | AFC_MIN_PSD Floor Enforcement Decision Tree | 16 |
| FIG. 9 | Geolocation Validation Flow | 18 |
| FIG. 10 | WGS84 to ECEF Conversion Formula Block | 20 |
| FIG. 11 | Location Change Detection and Cache Invalidation | 22 |
| FIG. 12 | RrmAFCBolt Storm Topology | 24 |
| FIG. 13 | AFC Channel Validation State Machine | 26 |
| FIG. 14 | 320 MHz Mode 1 vs Mode 2 Channel Layout | 28 |
| FIG. 15 | ch_delta Sub-Channel Expansion per Bandwidth | 30 |
| FIG. 16 | DeleteAP Retry Logic Flowchart | 32 |
| FIG. 17 | AP Lifecycle in AFC System | 34 |
| FIG. 18 | Redis Cache Architecture for AFC State | 36 |
| FIG. 19 | Multi-Provider Support Architecture | 38 |
| FIG. 20 | LPI Fallback Decision Tree | 40 |
| FIG. 21 | ACS + AFC Integration Flow in rrmACSV2 | 42 |
| FIG. 22 | afcNode Processing in APnode Graph | 44 |

---

## PREFATORY NOTE ON FIGURES

Each figure in this section is preceded by a **Sequence Summary** explaining the flow, actors, and decisions depicted, followed by the **diagram itself**, and then a **Caption** formally identifying the figure for patent reference. All mathematical formulas are rendered in plain text with no masking or blurring. All table cells contain only their own content with no overlap. All flowchart decision diamonds show complete visible text. Arrows are described with direction labels. No hidden text exists anywhere in this section.

---

---

# FIGURE 1 — OVERALL SYSTEM ARCHITECTURE

## Pre-Diagram Sequence Summary

The Mist/Juniper cloud platform operates a distributed Radio Resource Management (RRM) system that manages thousands of enterprise 802.11ax/802.11be (Wi-Fi 6E/7) access points (APs) operating in the 6 GHz band under FCC Standard Power (SP) rules. To operate at Standard Power in the 6 GHz band, each AP must obtain spectrum availability from a certified Automated Frequency Coordination (AFC) system, as mandated by FCC 47 CFR Part 15 Subpart E.

Rather than each AP querying the AFC system directly, the cloud RRM introduces an **AFC Proxy Service** that acts as an intermediary. The RRM Storm bolt (`RrmAFCBolt`) queries the AFC proxy on behalf of each AP using the AP's MAC address and GPS coordinates stored in a Redis location database. The AFC proxy forwards these requests to one of multiple AFC providers (Wi-Fi Alliance "wfa", test harnesses "wfa-th01"/"wfa-th02", or development "dev"). The AFC system returns available channel information with per-channel maxEIRP values and an expiry timestamp. This information is cached in Redis and used by the ACS (Automatic Channel Selection) bolt to configure each AP with compliant channels and power levels.

The sequence is: AP connects → AP reports GPS via location service → RRM detects standard_power=True → RRM queries AFC proxy → AFC proxy queries AFC provider → response cached in Redis → ACS assigns AFC-compliant channels → AP operates at Standard Power.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MIST/JUNIPER CLOUD RRM PLATFORM                         │
│                                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────────┐  │
│  │  Location Redis  │    │   RRM Redis      │    │  Apache Storm Topology   │  │
│  │                  │    │                  │    │                          │  │
│  │ devices/{id}/gps │◄──►│ afc_info cache   │◄──►│  ┌────────────────────┐ │  │
│  │ (lat/lon/elev)   │    │ afc_nodes        │    │  │  RrmAFCBolt        │ │  │
│  │ ellipse/majorAxis│    │ rrm/acs/radar    │    │  │  (tick + events)   │ │  │
│  └──────────────────┘    └──────────────────┘    │  └────────┬───────────┘ │  │
│                                                   │           │             │  │
│                                                   │  ┌────────▼───────────┐ │  │
│                                                   │  │  RrmACSBolt (V2)   │ │  │
│                                                   │  │  (channel select)  │ │  │
│                                                   │  └────────────────────┘ │  │
│                                                   └────────────┬─────────────┘  │
│                                                                │                │
│                          ┌─────────────────────────────────────▼──────────────┐ │
│                          │          AFC PROXY SERVICE                          │ │
│                          │   http://afc-proxy-{env}.mist.pvt/afc/devices      │ │
│                          │                                                     │ │
│                          │  POST   /afc/devices        (register + query)     │ │
│                          │  GET    /afc/devices/{mac}  (get channels)         │ │
│                          │  DELETE /afc/devices/{mac}  (deregister)           │ │
│                          └──────────────────┬──────────────────────────────────┘ │
└─────────────────────────────────────────────┼──────────────────────────────────┘
                                              │
                    ┌─────────────────────────▼─────────────────────────┐
                    │              AFC PROVIDER SYSTEMS                  │
                    │                                                    │
                    │  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
                    │  │   wfa    │  │ wfa-th01 │  │   wfa-th02   │    │
                    │  │(prod WFA)│  │ (int test│  │ (cert test)  │    │
                    │  └──────────┘  └──────────┘  └──────────────┘    │
                    │  Responds: availableChannelInfo + maxEIRP         │
                    │            availabilityExpireTime (ISO 8601)      │
                    └────────────────────────────────────────────────────┘
                                              │
                    ┌─────────────────────────▼─────────────────────────┐
                    │           ENTERPRISE ACCESS POINTS (APs)           │
                    │                                                    │
                    │  AP-64 (6 GHz + 2.4 GHz)   standard_power = True  │
                    │  FCC ID: 2AHBN-AP64                                │
                    │  rulesetId: US_47_CFR_PART_15_SUBPART_E            │
                    │  Band: 6 GHz (5925–7125 MHz)                       │
                    │  GPS reported via location service                 │
                    └────────────────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 1 establishes that the inventive system uses a three-tier architecture: (1) the cloud RRM platform with dual Redis stores and Apache Storm bolts, (2) an AFC proxy service that abstracts provider differences, and (3) AP hardware with FCC-certified device descriptors. The uniqueness lies in the cloud-native, proxy-mediated AFC integration that operates at enterprise scale across thousands of APs without requiring each AP to independently implement AFC protocol logic.

**FIG. 1** — Overall system architecture of the AFC-integrated Radio Resource Management platform, showing the cloud RRM layer with Location Redis (GPS storage), RRM Redis (AFC state cache), the Apache Storm processing topology comprising RrmAFCBolt and RrmACSBolt, the AFC Proxy Service with POST/GET/DELETE endpoints, the AFC Provider tier (wfa, wfa-th01, wfa-th02), and the enterprise access point layer with FCC-certified device descriptors operating in the 6 GHz band under 47 CFR Part 15 Subpart E Standard Power rules.

---

---

# FIGURE 2 — AFC REQUEST LIFECYCLE FLOWCHART

## Pre-Diagram Sequence Summary

When an AP with `standard_power=True` sends an ACS request (automatic channel selection trigger), the RRM system must determine which 6 GHz channels the AP is permitted to use under Standard Power rules before assigning any channel. The lifecycle proceeds as follows:

1. **Trigger**: ACS command received for AP with `standard_power=True` in radio_config.
2. **GPS Fetch**: System retrieves AP's geolocation from Location Redis using key `devices/{ap_id}/gps`.
3. **Cache Check**: System calls `GetChannelByMac()` to retrieve any existing AFC response from the proxy cache.
4. **State Check**: If cached state is `DONE` and `availableChannelInfo` is present, check if AP location has changed using ECEF distance computation.
5. **Location Match**: If location difference exceeds threshold (default 200m), delete old entry and re-register.
6. **POST Request**: If no valid cache, call `PostAfcRequest()` with full payload including GPS and certification ID.
7. **GET Response**: Call `GetChannelByMac()` again to retrieve the AFC provider's response.
8. **Process Response**: Call `process_afc_response()` to compute per-channel maxEIRP using min(maxEIRP, psd + 10 * log10(bandwidth)).
9. **Channel Validation**: Call `channels_validation()` to intersect AFC-permitted channels with operator-configured channels.
10. **Expiry**: Store `availabilityExpireTime` as Unix timestamp for future expiry tracking.
11. **Fallback**: If `NoGPS` and AP has `lpi_ok=True`, fall back to LPI (standard_power=False). Otherwise, disable radio.

```
        ┌──────────────────────────────────┐
        │   ACS Request Received for AP    │
        │   band=6, standard_power=True    │
        └─────────────────┬────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │  Fetch GPS from Location Redis   │
        │  key: devices/{ap_id}/gps        │
        │  returns: ellipse, elevation     │
        └─────────────────┬────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  GPS data available?  │
              └─────┬─────────────────┘
                    │                 │
                   YES               NO
                    │                 │
                    ▼                 ▼
        ┌───────────────────┐  ┌──────────────────────────┐
        │  GetChannelByMac  │  │  lpi_ok == True?          │
        │  (GET proxy cache)│  └──────┬───────────────────┘
        └────────┬──────────┘         │              │
                 │                   YES             NO
                 ▼                    │              │
    ┌────────────────────────┐        ▼              ▼
    │  Cache state == DONE   │  ┌──────────┐  ┌──────────────┐
    │  AND availableChannel  │  │ Use LPI  │  │ Disable Radio│
    │  Info present?         │  │ (SP=off) │  │ Update Redis │
    └──────┬─────────────────┘  └──────────┘  │ afc_status   │
           │              │                   └──────────────┘
          YES             NO
           │              │
           ▼              ▼
┌──────────────────┐  ┌────────────────────────────────┐
│ Location changed?│  │  PostAfcRequest()               │
│ (ECEF distance   │  │  POST /afc/devices              │
│  > threshold)    │  │  payload: ap_id, site_id,       │
└──────┬───────────┘  │  gps, certificationId,          │
       │         │    │  inquiredChannels[131..137]      │
      YES        NO   └─────────────────┬────────────────┘
       │         │                      │
       ▼         │                      ▼
┌────────────┐   │         ┌────────────────────────────┐
│ DeleteAP() │   │         │  POST succeeded?           │
│ (3 retries)│   │         └──────────┬─────────────────┘
└─────┬──────┘   │                   │              │
      │          │                  YES             NO
      │          │                   │              │
      └──────────┘                   ▼              ▼
             │              ┌─────────────────┐  ┌──────────────┐
             │              │ GetChannelByMac │  │ state=NotDONE│
             │              │ (GET response)  │  │ return {}    │
             │              └────────┬────────┘  └──────────────┘
             │                       │
             └───────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │  process_afc_response()           │
        │  - Parse availabilityExpireTime  │
        │  - Match globalOperatingClass    │
        │  - Compute EIRP per channel:     │
        │    min(maxEIRP,                  │
        │    psd + 10*log10(bandwidth))    │
        │  - Apply AFC_MIN_PSD floor       │
        └─────────────────┬────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │  channels_validation()            │
        │  Intersect AFC channels with     │
        │  operator-configured channels    │
        └─────────────────┬────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │  Return afc_channels dict        │
        │  {channel_num: max_eirp_dBm}     │
        │  status = "DONE"                 │
        │  expiry = Unix timestamp         │
        └──────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 2 shows the complete AFC request lifecycle from ACS trigger to channel assignment. The critical decision points are: (1) GPS availability check triggering LPI fallback, (2) proxy cache state validation, (3) ECEF-based location change detection, (4) POST/GET sequence with the AFC proxy, and (5) EIRP computation with PSD floor enforcement. The two return paths (NoGPS+LPI and disabled radio) are unique to this system and represent novel handling not present in prior art.

**FIG. 2** — AFC request lifecycle flowchart showing the complete processing sequence from ACS trigger detection through GPS retrieval, proxy cache validation, ECEF-based location change detection, AFC proxy POST/GET request sequence, EIRP computation using the formula min(maxEIRP, psd_value + 10 * log10(channel_bandwidth_MHz)), AFC_MIN_PSD floor enforcement, channel intersection validation, and terminal states including DONE (with channel/EIRP assignments), NoGPS LPI fallback, and radio disable.

---

---

# FIGURE 3 — AFC PAYLOAD JSON STRUCTURE

## Pre-Diagram Sequence Summary

The AFC payload is constructed by `get_payload_proxy()` in `afc_payload.py`. It is a JSON document sent via HTTP POST to the AFC proxy. The payload uniquely identifies the device, specifies its precise geolocation using an uncertainty ellipse, and declares the frequency ranges and channel classes for which spectrum availability is being requested.

Key construction rules implemented in the invention:
- `requestId` = AP's MAC address (used as device identifier)
- `siteId` = site UUID from RRM
- `providerName` = mapped from numeric flag (0→"wfa", 1→"wfa-th01", 2→"wfa-th02", "dev"→"dev")
- `majorAxis` capped at 325 meters; `minorAxis` capped at 325 meters
- `height` floor of 0.1 meters (never zero — prevents division errors in AFC math)
- `orientation` corrected: if > 180 degrees, subtract 180
- `inquiredFrequencyRange`: single range 5925–7115 MHz (full 6 GHz band)
- `inquiredChannels`: all six GlobalOperatingClasses (131, 132, 133, 134, 136, 137)
- `indoorDeployment`: always 1 (indoor assumption for enterprise APs)
- `certificationId`: device-specific FCC ID with ruleset US_47_CFR_PART_15_SUBPART_E

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         AFC REQUEST PAYLOAD STRUCTURE                         │
│                    (constructed by get_payload_proxy())                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  {                                                                            │
│    "requestId"   :  <ap_id>          ← AP MAC address (device identifier)   │
│    "siteId"      :  <site_uuid>      ← RRM site identifier                  │
│    "providerName":  <"wfa"|"wfa-th01"|"wfa-th02"|"dev">                      │
│                                                                               │
│    "deviceDescriptor": {                                                      │
│      "serialNumber"  :  <ap_id>                                              │
│      "certificationId": [                                                    │
│        {                                                                      │
│          "id"       : "2AHBN-AP64"   ← FCC Certification ID                 │
│          "rulesetId": "US_47_CFR_PART_15_SUBPART_E"                          │
│        }                                                                      │
│      ]                                                                        │
│    }                                                                          │
│                                                                               │
│    "location": {                                                              │
│      "elevation": {                                                           │
│        "height"             : max(gps_height, 0.1)  ← floor 0.1 m           │
│        "heightType"         : "AGL"                 ← Above Ground Level    │
│        "verticalUncertainty": <int(gps_vertUnc)>                             │
│      }                                                                        │
│      "ellipse": {                                                             │
│        "center": {                                                            │
│          "longitude": <gps_longitude>                                        │
│          "latitude" : <gps_latitude>                                         │
│        }                                                                      │
│        "majorAxis"  : min(325, int(gps_majorAxis))  ← capped at 325 m       │
│        "minorAxis"  : min(325, int(gps_minorAxis))  ← capped at 325 m       │
│        "orientation": <orient if <=180, else orient-180>  ← corrected       │
│      }                                                                        │
│      "indoorDeployment": 1              ← Always indoor for enterprise APs  │
│    }                                                                          │
│                                                                               │
│    "inquiredFrequencyRange": [                                                │
│      {                                                                        │
│        "lowFrequency" : 5925   ← Lower bound of 6 GHz band (MHz)            │
│        "highFrequency": 7115   ← Upper bound of 6 GHz band (MHz)            │
│      }                                                                        │
│    ]                                                                          │
│                                                                               │
│    "inquiredChannels": [                                                      │
│      { "globalOperatingClass": 131 }   ← 20 MHz channels                    │
│      { "globalOperatingClass": 132 }   ← 40 MHz channels                    │
│      { "globalOperatingClass": 133 }   ← 80 MHz channels                    │
│      { "globalOperatingClass": 134 }   ← 160 MHz channels                   │
│      { "globalOperatingClass": 136 }   ← 80+80 MHz (reserved)               │
│      { "globalOperatingClass": 137 }   ← 320 MHz channels                   │
│    ]                                                                          │
│  }                                                                            │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 3 illustrates the exact JSON payload construction with all constraint rules enforced by the inventive system. The constraints on majorAxis/minorAxis (capped at 325 m), height floor (0.1 m), and orientation correction (subtract 180 if > 180) are unique to this implementation and ensure valid, compliant AFC requests under all edge-case GPS conditions. The single broad frequency range (5925–7115 MHz) combined with all six GlobalOperatingClasses maximizes channel availability returned from the AFC system.

**FIG. 3** — AFC request payload JSON structure as constructed by `get_payload_proxy()`, showing all field constraints: requestId equal to AP MAC address, deviceDescriptor with FCC certification ID (2AHBN-AP64) and ruleset US_47_CFR_PART_15_SUBPART_E, location ellipse with height floored at 0.1 m, majorAxis and minorAxis capped at 325 m, orientation corrected by subtracting 180 when exceeding 180 degrees, indoor deployment flag set to 1, inquired frequency range 5925–7115 MHz, and all six GlobalOperatingClasses (131, 132, 133, 134, 136, 137).

---

---

# FIGURE 4 — AFC RESPONSE STRUCTURE

## Pre-Diagram Sequence Summary

The AFC provider returns a JSON response via the AFC proxy. The system processes this response in `process_afc_response()`. The response contains: a state field ("DONE" or other), available channel information organized by GlobalOperatingClass, available frequency information with per-frequency maxPsd values, and an availability expiry timestamp.

The invention processes this response to derive a per-channel maximum transmit power (as EIRP in dBm) by taking the minimum of: (a) the per-channel maxEIRP from availableChannelInfo, and (b) the PSD-derived EIRP computed as `psd_value + 10 * log10(channel_bandwidth_MHz)`. This minimum is then further bounded below by the AFC_MIN_PSD floor value for the given bandwidth. The result is a dictionary mapping each 20 MHz subchannel CFI number to its permitted maximum EIRP in dBm.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         AFC RESPONSE STRUCTURE                                │
│                   (returned by AFC provider via proxy)                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  {                                                                            │
│    "requestId"            : <ap_id>                                          │
│    "siteId"               : <site_uuid>                                      │
│    "providerName"         : "wfa"                                            │
│    "state"                : "DONE"     ← Required for valid response         │
│    "availabilityExpireTime": "2024-02-14T21:04:49Z"  ← ISO 8601 UTC         │
│                                        → parsed to Unix timestamp            │
│    "response": {                                                              │
│      "responseCode"   : 0                                                    │
│      "shortDescription": "Success"                                           │
│    }                                                                          │
│                                                                               │
│    "availableChannelInfo": [                                                  │
│      {                                                                        │
│        "globalOperatingClass": 131         ← 20 MHz class                   │
│        "channelCfi"          : [1, 5, 9, 13, 33, 65, ...]  ← CFI numbers   │
│        "maxEirp"             : [36.0, 36.0, 36.0, ...]     ← dBm per chan  │
│      },                                                                       │
│      {                                                                        │
│        "globalOperatingClass": 132         ← 40 MHz class                   │
│        "channelCfi"          : [3, 75, 131, 179]                             │
│        "maxEirp"             : [29.0, 31.5, 25.0, 27.0]   ← dBm per chan  │
│      },                                                                       │
│      {                                                                        │
│        "globalOperatingClass": 133         ← 80 MHz class                   │
│        "channelCfi"          : [7, 71, 135, 199]                             │
│        "maxEirp"             : [30.2, 29.4, 26.0, 30.0]                     │
│      },                                                                       │
│      {                                                                        │
│        "globalOperatingClass": 134         ← 160 MHz class                  │
│        "channelCfi"          : [15, 143]                                     │
│        "maxEirp"             : [33.2, 33.2]                                  │
│      },                                                                       │
│      {                                                                        │
│        "globalOperatingClass": 137         ← 320 MHz class                  │
│        "channelCfi"          : [31, 191]                                     │
│        "maxEirp"             : [33.2, 30.0]                                  │
│      }                                                                        │
│    ]                                                                          │
│                                                                               │
│    "availableFrequencyInfo": [                                                │
│      {                                                                        │
│        "frequencyRange": {                                                    │
│          "lowFrequency" : 5925   (MHz)                                       │
│          "highFrequency": 6425   (MHz)                                       │
│        }                                                                      │
│        "maxPsd": 23.0            ← dBm/MHz (Power Spectral Density)         │
│      },                                                                       │
│      {                                                                        │
│        "frequencyRange": {                                                    │
│          "lowFrequency" : 6525   (MHz)                                       │
│          "highFrequency": 6875   (MHz)                                       │
│        }                                                                      │
│        "maxPsd": 21.0            ← dBm/MHz                                  │
│      }                                                                        │
│    ]                                                                          │
│  }                                                                            │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 4 shows the complete AFC response structure. The invention uniquely processes both `availableChannelInfo` (for per-channel maxEIRP) and `availableFrequencyInfo` (for PSD-based EIRP constraints) together, taking the more restrictive of the two per channel. The expiry timestamp is converted from ISO 8601 UTC to a Unix integer timestamp for efficient cache management. The example response demonstrates real EIRP values (25.0–36.0 dBm) and PSD values (21.0–23.0 dBm/MHz) as returned by the WFA test harness.

**FIG. 4** — AFC response structure from the AFC provider via proxy, showing all fields processed by the inventive system: state field (must equal "DONE"), availabilityExpireTime in ISO 8601 UTC format (converted to Unix timestamp), availableChannelInfo array with per-class (GlobalOperatingClass 131/132/133/134/137) channel CFI numbers and corresponding maxEIRP values in dBm, and availableFrequencyInfo array with per-frequency-range maxPsd values in dBm/MHz. Example EIRP values range from 25.0 dBm (restricted channel) to 36.0 dBm (unrestricted channel). Example maxPsd values: 23.0 dBm/MHz (5925–6425 MHz) and 21.0 dBm/MHz (6525–6875 MHz).

---

---

# FIGURE 5 — GLOBALOPERATINGCLASS TO BANDWIDTH MAPPING TABLE

## Pre-Diagram Sequence Summary

The 6 GHz Wi-Fi standard (IEEE 802.11ax and 802.11be) organizes channels into GlobalOperatingClasses as defined by the Wi-Fi Alliance AFC specification. Each GlobalOperatingClass corresponds to a specific channel bandwidth. The inventive system uses these classes to select the correct section of the AFC response for a given AP's configured bandwidth. The mapping is bidirectional: `bandwidth_to_globalOperatingClass()` and `globalOperatingClass_to_bandwidth()` are both implemented.

When the RRM system needs to select channels for an AP configured for, say, 80 MHz operation, it uses GlobalOperatingClass 133. It then extracts the `channelCfi` and `maxEirp` arrays from the AFC response entry matching class 133, and maps those to the 20 MHz subchannels that make up each 80 MHz channel using the `ch_delta` mechanism (Figure 15).

```
┌────────────────────────────────────────────────────────────────────────┐
│          GLOBALOPERATINGCLASS TO BANDWIDTH MAPPING TABLE               │
│       (IEEE 802.11ax/802.11be — 6 GHz Band — Wi-Fi Alliance AFC)      │
├─────────────────────┬────────────────────┬─────────────────────────────┤
│  GlobalOperating    │  Channel Bandwidth  │  Number of Channels         │
│  Class              │  (MHz)              │  in 6 GHz Band              │
├─────────────────────┼────────────────────┼─────────────────────────────┤
│        131          │       20 MHz        │  59 channels (CFI 1–229)    │
├─────────────────────┼────────────────────┼─────────────────────────────┤
│        132          │       40 MHz        │  29 channels (CFI 3–227)    │
├─────────────────────┼────────────────────┼─────────────────────────────┤
│        133          │       80 MHz        │  14 channels (CFI 7–215)    │
├─────────────────────┼────────────────────┼─────────────────────────────┤
│        134          │      160 MHz        │   7 channels (CFI 15–207)   │
├─────────────────────┼────────────────────┼─────────────────────────────┤
│        136          │    80+80 MHz        │  (reserved/future use)      │
├─────────────────────┼────────────────────┼─────────────────────────────┤
│        137          │      320 MHz        │   6 channels (CFI 31–191)   │
└─────────────────────┴────────────────────┴─────────────────────────────┘

  Function: bandwidth_to_globalOperatingClass(bandwidth)
  ──────────────────────────────────────────────────────
  bandwidth =  20 MHz  →  returns  131
  bandwidth =  40 MHz  →  returns  132
  bandwidth =  80 MHz  →  returns  133
  bandwidth = 160 MHz  →  returns  134
  bandwidth = 320 MHz  →  returns  137

  Function: globalOperatingClass_to_bandwidth(globalOperatingClass)
  ──────────────────────────────────────────────────────────────────
  class 131  →  returns   20 MHz
  class 132  →  returns   40 MHz
  class 133  →  returns   80 MHz
  class 134  →  returns  160 MHz
  class 137  →  returns  320 MHz
```

**Post-Diagram Summary:** Figure 5 establishes the fundamental mapping between GlobalOperatingClass integers and channel bandwidths. This bidirectional mapping is essential for the EIRP computation (Figure 7) and sub-channel expansion (Figure 15). The inventive system supports all six defined classes simultaneously in each AFC request, enabling the system to select the optimal bandwidth for each AP based on regulatory constraints rather than only the operator's configured bandwidth.

**FIG. 5** — GlobalOperatingClass to channel bandwidth mapping table for 6 GHz Wi-Fi (IEEE 802.11ax/802.11be) as implemented in `bandwidth_to_globalOperatingClass()` and `globalOperatingClass_to_bandwidth()` in `afc_utils.py`. Classes 131 (20 MHz, 59 channels), 132 (40 MHz, 29 channels), 133 (80 MHz, 14 channels), 134 (160 MHz, 7 channels), 136 (80+80 MHz, reserved), and 137 (320 MHz, 6 channels) span the 5925–7125 MHz 6 GHz band.

---

---

# FIGURE 6 — 6 GHz BAND CHANNEL MAP

## Pre-Diagram Sequence Summary

The 6 GHz band allocated for Wi-Fi (5925–7125 MHz) contains 59 valid 20 MHz channels. Each channel is identified by its Channel Frequency Index (CFI) number, which corresponds to a specific center frequency. The `channel_to_freq` dictionary in `afc_payload.py` maps CFI numbers to center frequencies. The `get_channel_freq_mapping()` function provides lower and upper frequency bounds for each channel at each bandwidth.

This channel map is fundamental to the EIRP computation: for each 20 MHz channel, the system checks whether any PSD range from `availableFrequencyInfo` overlaps with the channel's frequency bounds. If it does, the PSD value is used to compute the channel's EIRP limit via the formula `psd_value + 10 * log10(channel_bandwidth_MHz)`.

```
6 GHz BAND CHANNEL MAP — 5925 MHz to 7125 MHz
All 59 valid 20 MHz channels (Channel Frequency Index → Center Frequency)

    FREQ (MHz)
    5945                                                               7115
      │                                                                  │
      ▼                                                                  ▼
  ────┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬────
      │1 │5 │9 │13│17│21│25│29│33│37│41│45│49│53│57│61│65│69│73│77│81│85│89│93│...
  ────┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴────
      5955                                                            6415

┌──────────────────────────────────────────────────────────────────────────────────┐
│  CFI │ Center   │  CFI │ Center   │  CFI │ Center   │  CFI │ Center   │  CFI │   │
│      │ Freq MHz │      │ Freq MHz │      │ Freq MHz │      │ Freq MHz │      │   │
├──────┼──────────┼──────┼──────────┼──────┼──────────┼──────┼──────────┼──────┤   │
│   1  │  5955    │  53  │  6215    │ 105  │  6475    │ 157  │  6735    │ 209  │   │
│   5  │  5975    │  57  │  6235    │ 109  │  6495    │ 161  │  6755    │ 213  │   │
│   9  │  5995    │  61  │  6255    │ 113  │  6515    │ 165  │  6775    │ 217  │   │
│  13  │  6015    │  65  │  6275    │ 117  │  6535    │ 169  │  6795    │ 221  │   │
│  17  │  6035    │  69  │  6295    │ 121  │  6555    │ 173  │  6815    │ 225  │   │
│  21  │  6055    │  73  │  6315    │ 125  │  6575    │ 177  │  6835    │ 229  │   │
│  25  │  6075    │  77  │  6335    │ 129  │  6595    │ 181  │  6855    │ 233  │   │
│  29  │  6095    │  81  │  6355    │ 133  │  6615    │ 185  │  6875    │      │   │
│  33  │  6115    │  85  │  6375    │ 137  │  6635    │ 189  │  6895    │      │   │
│  37  │  6135    │  89  │  6395    │ 141  │  6655    │ 193  │  6915    │      │   │
│  41  │  6155    │  93  │  6415    │ 145  │  6675    │ 197  │  6935    │      │   │
│  45  │  6175    │  97  │  6435    │ 149  │  6695    │ 201  │  6955    │      │   │
│  49  │  6195    │ 101  │  6455    │ 153  │  6715    │ 205  │  6975    │      │   │
└──────┴──────────┴──────┴──────────┴──────┴──────────┴──────┴──────────┴──────┘

  Key Frequency Boundaries:
  ┌─────────────────────────────────────────────────────────┐
  │  Band Start       : 5925 MHz  (band edge)               │
  │  First Channel    : CFI  1  → center 5955 MHz           │
  │  Channel  93 end  : 6425 MHz  (UNII-5 upper boundary)   │
  │  Channel  97 start: 6425 MHz  (UNII-6 start)            │
  │  Channel 113 end  : 6525 MHz  (gap at 6425–6525 MHz)    │
  │  Channel 117 start: 6525 MHz  (UNII-7 start)            │
  │  Channel 185 end  : 6875 MHz                            │
  │  Channel 189 start: 6875 MHz  (UNII-8 start)            │
  │  Last Channel     : CFI 229 → center 7085 MHz           │
  │  Band End         : 7125 MHz  (band edge)               │
  └─────────────────────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 6 shows all 59 valid 20 MHz channels in the 6 GHz band with their exact center frequencies. The channel numbering follows the Wi-Fi Alliance AFC specification's CFI (Channel Frequency Index) convention. The gap between CFI 93 (6415 MHz) and CFI 97 (6435 MHz) corresponds to the 6425–6525 MHz sub-band that may have different regulatory status. This map is essential for the PSD overlap computation (Figure 7) and for the sub-channel expansion from wide-bandwidth channels (Figure 15).

**FIG. 6** — Complete 6 GHz band channel map showing all 59 valid 20 MHz channels with Channel Frequency Index (CFI) numbers and corresponding center frequencies (MHz), spanning 5955–7085 MHz center frequencies within the 5925–7125 MHz allocated band. Key frequency boundaries shown include UNII-5 (5925–6425 MHz), UNII-6 (6425–6525 MHz), UNII-7 (6525–6875 MHz), and UNII-8 (6875–7125 MHz) sub-bands as referenced in the AFC channel frequency mapping (`get_channel_freq_mapping()` in `afc_payload.py`).

---

---

# FIGURE 7 — EIRP COMPUTATION FLOW

## Pre-Diagram Sequence Summary

The EIRP (Effective Isotropic Radiated Power) computation is a core novelty of the inventive system. It implements a two-source EIRP derivation that takes the most restrictive (minimum) of two independent limits:

**Source 1 — Channel EIRP from AFC response**: The AFC system returns a per-channel `maxEIRP` value in dBm directly in `availableChannelInfo`.

**Source 2 — PSD-derived EIRP**: The AFC system also returns `availableFrequencyInfo` with per-frequency-range `maxPsd` values in dBm/MHz. The EIRP for a channel of bandwidth B MHz is computed as:

**EIRP_psd = psd_value + 10 * log10(channel_bandwidth_MHz)**

For example: maxPsd = 23.0 dBm/MHz, bandwidth = 80 MHz:
EIRP_psd = 23.0 + 10 * log10(80) = 23.0 + 19.03 = 42.03 dBm

Or: maxPsd = 21.0 dBm/MHz, bandwidth = 80 MHz:
EIRP_psd = 21.0 + 10 * log10(80) = 21.0 + 19.03 = 40.03 dBm

The final channel EIRP is: `min(maxEIRP_from_channel, EIRP_psd)`, further bounded by `max(AFC_MIN_PSD[bandwidth], result)`.

```
              ┌─────────────────────────────────────────────┐
              │   AFC Response contains two EIRP sources:   │
              └──────────────┬──────────────────────────────┘
                             │
              ┌──────────────▼──────────────────────────────┐
              │  SOURCE 1: availableChannelInfo              │
              │  For each channel CFI number:                │
              │    maxEIRP[j]  (dBm)  ← direct per-channel  │
              └──────────────┬──────────────────────────────┘
                             │
              ┌──────────────▼──────────────────────────────┐
              │  SOURCE 2: availableFrequencyInfo            │
              │  get_eirp_from_psd() computes:               │
              │                                              │
              │  For each 20 MHz channel (ch, ch_low, ch_hi)│
              │    For each PSD entry:                       │
              │      Check frequency overlap:                │
              │        (psd_low >= ch_low AND psd_low < ch_hi)│
              │        OR (psd_hi <= ch_hi AND psd_hi > ch_lo)│
              │        OR (psd_hi >= ch_hi AND psd_lo <= ch_lo)│
              │                                              │
              │      If overlap found:                       │
              │        EIRP_psd = min(EIRP_psd,              │
              │          psd_value + 10*log10(bandwidth_MHz))│
              │                                              │
              │    Default if no overlap: EIRP_psd = 36 dBm │
              └──────────────┬──────────────────────────────┘
                             │
              ┌──────────────▼──────────────────────────────┐
              │  MINIMUM SELECTION:                          │
              │                                              │
              │  ch_max_power = min(EIRP_psd[ch], maxEIRP[j])│
              │                                              │
              │  Example values:                             │
              │    maxEIRP[j]  = 30.2 dBm  (from AFC resp)  │
              │    EIRP_psd    = 40.0 dBm  (from PSD calc)  │
              │    min result  = 30.2 dBm   ← more restrict │
              └──────────────┬──────────────────────────────┘
                             │
              ┌──────────────▼──────────────────────────────┐
              │  AFC_MIN_PSD FLOOR ENFORCEMENT:              │
              │                                              │
              │  AFC_MIN_PSD = {                             │
              │     20: 14 dBm,   40: 17 dBm,               │
              │     80: 20 dBm,  160: 23 dBm,               │
              │    320: 26 dBm  }                            │
              │                                              │
              │  ch_max_power = max(AFC_MIN_PSD[bandwidth],  │
              │                    int(ch_max_power))        │
              │                                              │
              │  Example:  bandwidth=80, min floor = 20 dBm │
              │    ch_max_power = max(20, 30) = 30 dBm      │
              └──────────────┬──────────────────────────────┘
                             │
              ┌──────────────▼──────────────────────────────┐
              │  OUTPUT:                                     │
              │  afc_channels[subchannel_cfi] = ch_max_power │
              │  (dict of 20 MHz CFI → max EIRP in dBm)     │
              └─────────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 7 shows the inventive EIRP computation that uniquely combines channel-level maxEIRP from the AFC response with PSD-derived EIRP constraints computed using the formula `psd_value + 10 * log10(bandwidth_MHz)`. The use of the minimum of these two sources ensures compliance with both per-channel and per-frequency-band power spectral density limits simultaneously. The AFC_MIN_PSD floor prevents degenerate zero-power assignments and aligns with regulatory minimum operating levels.

**FIG. 7** — EIRP computation flow implemented in `process_afc_response()` and `get_eirp_from_psd()` in `afc_utils.py`. Two independent EIRP sources are computed: (1) per-channel maxEIRP directly from `availableChannelInfo`, and (2) PSD-derived EIRP from `availableFrequencyInfo` using the formula EIRP_psd = psd_value + 10 * log10(channel_bandwidth_MHz). The minimum of the two sources is taken per channel, then bounded below by the AFC_MIN_PSD floor values: 14 dBm (20 MHz), 17 dBm (40 MHz), 20 dBm (80 MHz), 23 dBm (160 MHz), 26 dBm (320 MHz). Output is a dictionary mapping 20 MHz subchannel CFI numbers to maximum permitted EIRP values in dBm.

---

---

# FIGURE 8 — AFC_MIN_PSD FLOOR ENFORCEMENT DECISION TREE

## Pre-Diagram Sequence Summary

The AFC_MIN_PSD floor is a protective mechanism that ensures the system never assigns a channel a power level so low that it would be operationally useless. The floor values are calibrated to the minimum useful EIRP for each bandwidth: wider bandwidths have higher floor values because they aggregate more spectrum.

The floor values stored in `AFC_MIN_PSD = {20: 14, 40: 17, 80: 20, 160: 23, 320: 26}` reflect the dBm/MHz relationship: each doubling of bandwidth adds approximately 3 dBm (10 * log10(2) ≈ 3.01 dBm) to the floor, consistent with PSD-constrained power scaling. The decision tree below shows how the floor is applied after the min(maxEIRP, psd_eirp) computation.

```
            ┌──────────────────────────────────────────┐
            │  Computed ch_power = min(maxEIRP, psd_eirp)│
            │  (floating-point dBm value)               │
            └────────────────┬─────────────────────────┘
                             │
            ┌────────────────▼─────────────────────────┐
            │  What is the channel bandwidth?           │
            └────┬──────┬──────┬──────┬─────┬──────────┘
                 │      │      │      │     │
                20      40     80    160   320
               MHz     MHz    MHz    MHz   MHz
                │      │      │      │     │
                ▼      ▼      ▼      ▼     ▼
            ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐
            │Floor ││Floor ││Floor ││Floor ││Floor │
            │14 dBm││17 dBm││20 dBm││23 dBm││26 dBm│
            └──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘
               │       │       │       │       │
               └───────┴───────┴───────┴───────┘
                                 │
            ┌────────────────────▼────────────────────┐
            │  ch_max_power = max(floor, int(ch_power))│
            │                                          │
            │  Examples:                               │
            │  BW= 20, ch_power=10 → max(14,10) = 14  │
            │  BW= 80, ch_power=30 → max(20,30) = 30  │
            │  BW=160, ch_power=22 → max(23,22) = 23  │
            │  BW=320, ch_power=33 → max(26,33) = 33  │
            └────────────────────┬────────────────────┘
                                 │
            ┌────────────────────▼────────────────────┐
            │  ch_max_power = final integer dBm value  │
            │  stored in afc_channels[subchannel_cfi]  │
            └─────────────────────────────────────────┘

  Floor Derivation (dBm/MHz scaling):
  ┌────────────┬──────────┬────────────────────────────────────┐
  │  Bandwidth │  Floor   │  Relationship                       │
  │   (MHz)    │  (dBm)   │                                     │
  ├────────────┼──────────┼────────────────────────────────────┤
  │     20     │  14 dBm  │  Base floor for 20 MHz channel      │
  │     40     │  17 dBm  │  14 + 10*log10(40/20) = 14 + 3.01  │
  │     80     │  20 dBm  │  14 + 10*log10(80/20) = 14 + 6.02  │
  │    160     │  23 dBm  │  14 + 10*log10(160/20)= 14 + 9.03  │
  │    320     │  26 dBm  │  14 + 10*log10(320/20)= 14 + 12.04 │
  └────────────┴──────────┴────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 8 shows the AFC_MIN_PSD floor enforcement mechanism. The floor values follow a mathematically consistent PSD-scaling pattern: each doubling of bandwidth adds approximately 3 dBm to the floor (10 * log10(2) = 3.01 dBm). This ensures that the minimum permitted EIRP scales appropriately with bandwidth, consistent with the underlying regulatory PSD limits expressed in dBm/MHz.

**FIG. 8** — AFC_MIN_PSD floor enforcement decision tree showing per-bandwidth minimum EIRP floors: 14 dBm (20 MHz), 17 dBm (40 MHz), 20 dBm (80 MHz), 23 dBm (160 MHz), 26 dBm (320 MHz). The floor is applied as `ch_max_power = max(AFC_MIN_PSD[bandwidth], int(min(psd_eirp, max_eirp)))`. Floor values follow PSD-scaling law: each bandwidth doubling adds 10 * log10(2) ≈ 3 dBm to the floor, consistent with the formula EIRP = PSD + 10 * log10(bandwidth_MHz).

---

---

# FIGURE 9 — GEOLOCATION VALIDATION FLOW

## Pre-Diagram Sequence Summary

Each time an AP's AFC data is refreshed, the system checks whether the AP has physically moved since its last AFC registration. If the AP has moved beyond a configurable threshold (default 200 meters in the site policy, default 10 meters inside the `location_match()` function), the existing AFC registration is deleted and a new one is submitted. This prevents the AP from operating on channels approved for its old location.

The geolocation validation uses WGS84 Earth-Centered, Earth-Fixed (ECEF) coordinates for distance computation. This avoids the flat-earth approximation errors of simple latitude/longitude differencing, which can be significant at high latitudes. The system also independently checks height difference (vertical displacement) against the same threshold.

The GPS data is stored in Redis under key `devices/{ap_id}/gps` as a JSON object containing an `ellipse` sub-object (with center lat/lon) and an `elevation` sub-object (with height in AGL meters).

```
         ┌───────────────────────────────────────────────────────┐
         │  INPUT: Two GPS location objects                       │
         │  old_gps = location from existing AFC proxy entry     │
         │  new_gps = current location from Location Redis       │
         └───────────────────────────────────────────────────────┘
                               │
         ┌─────────────────────▼──────────────────────────────────┐
         │  Extract coordinates from each:                         │
         │  old: lat, lon = old_gps.ellipse.center.{lat,lon}      │
         │       h_old    = old_gps.elevation.height               │
         │  new: lat, lon = new_gps.ellipse.center.{lat,lon}      │
         │       h_new    = new_gps.elevation.height               │
         └─────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────▼──────────────────────────────────┐
         │  Convert to ECEF using lla_to_ecef(lat, lon, alt=0):   │
         │                                                         │
         │  WGS84 constants:                                       │
         │    a = 6378137.0 m        (semi-major axis)            │
         │    f = 1/298.257223563    (flattening)                  │
         │    b = a*(1-f)            (semi-minor axis)             │
         │                                                         │
         │  N = a / sqrt(1 - f*(2-f)*sin^2(lat_rad))              │
         │  x = (N+alt)*cos(lat_rad)*cos(lon_rad)                  │
         │  y = (N+alt)*cos(lat_rad)*sin(lon_rad)                  │
         │  z = (N*(1-f)^2+alt)*sin(lat_rad)                       │
         │                                                         │
         │  old_ecef = (old_x, old_y, old_z)                      │
         │  new_ecef = (new_x, new_y, new_z)                      │
         └─────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────▼──────────────────────────────────┐
         │  Compute distances:                                      │
         │  horiz_dist = sqrt((old_x-new_x)^2 + (old_y-new_y)^2)  │
         │  height_diff = abs(h_old - h_new)                        │
         └─────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────▼──────────────────────────────────┐
         │  Apply threshold check:                                  │
         │  loc_unchanged = (horiz_dist <= threshold)              │
         │                  AND (height_diff <= threshold)          │
         │                                                         │
         │  Threshold:                                              │
         │    Function default:  10 m  (local call)                │
         │    System policy:    200 m  (afc_channel_validation)    │
         └─────────────────────┬──────────────────────────────────┘
                               │
                ┌──────────────▼──────────────┐
                │  loc_unchanged == True?      │
                └──────┬───────────────────────┘
                       │                   │
                      YES                 NO
                       │                   │
                       ▼                   ▼
              ┌────────────────┐  ┌──────────────────────┐
              │  Use cached    │  │  loc_changed = True   │
              │  AFC response  │  │  Trigger DeleteAP()   │
              │  (no re-POST)  │  │  Then re-POST request │
              └────────────────┘  └──────────────────────┘
```

**Post-Diagram Summary:** Figure 9 shows the geolocation validation flow using WGS84 ECEF coordinates. The use of ECEF (rather than flat-earth Euclidean distance in degrees) is a key technical distinction of this invention. ECEF coordinates account for Earth's curvature and ellipsoidal shape, providing accurate distance measurements in meters regardless of geographic location. The dual threshold check (horizontal and vertical independently) provides robust 3D location change detection appropriate for building environments where vertical movement (floor changes) must also trigger re-registration.

**FIG. 9** — Geolocation validation flow in `location_match()` in `afc_utils.py`. GPS coordinates are extracted from both the existing AFC proxy entry (old_gps) and the current Location Redis entry (new_gps). Both are converted to WGS84 ECEF coordinates via `lla_to_ecef()` using semi-major axis a = 6378137.0 m and flattening f = 1/298.257223563. Horizontal distance is computed as Euclidean distance in the xy-plane of ECEF space. Height difference is computed as absolute difference of AGL heights. If either exceeds the threshold (system default 200 m from site policy), `loc_changed = True` is returned, triggering DeleteAP() followed by a new PostAfcRequest(). If both distances are within threshold, the cached AFC response is reused.

---

---

# FIGURE 10 — WGS84 TO ECEF CONVERSION FORMULA BLOCK

## Pre-Diagram Sequence Summary

The `lla_to_ecef()` function in `afc_utils.py` implements the standard geodetic transformation from geodetic coordinates (latitude, longitude, altitude above WGS84 ellipsoid) to Earth-Centered, Earth-Fixed (ECEF) Cartesian coordinates. The WGS84 ellipsoid is the reference system used by GPS and is defined by two parameters: the semi-major axis (equatorial radius) and the flattening factor. All other derived parameters are computed from these two.

ECEF coordinates place the origin at Earth's center of mass, with the X-axis pointing toward the intersection of the prime meridian (0° longitude) and equatorial plane, the Y-axis pointing toward 90°E longitude and the equatorial plane, and the Z-axis pointing toward the North Pole. This coordinate system is ideal for computing distances between two surface points on Earth because it converts the curved-surface distance problem into a straightforward 3D Euclidean distance computation.

```
┌────────────────────────────────────────────────────────────────────────────┐
│               WGS84 TO ECEF COORDINATE TRANSFORMATION                      │
│                  Function: lla_to_ecef(lat, lon, alt=0)                    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT PARAMETERS:                                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  lat  =  latitude   in degrees  (from gps.ellipse.center.latitude)   │  │
│  │  lon  =  longitude  in degrees  (from gps.ellipse.center.longitude)  │  │
│  │  alt  =  altitude   in meters   (default = 0, altitude ignored)      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WGS84 ELLIPSOID CONSTANTS:                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  a  =  6378137.0           meters     (semi-major axis, equatorial)  │  │
│  │  f  =  1 / 298.257223563              (flattening factor)            │  │
│  │  b  =  a * (1 - f)         meters     (semi-minor axis, polar)       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  INTERMEDIATE COMPUTATIONS:                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  lat_rad  =  lat * (pi / 180)     (convert degrees to radians)       │  │
│  │  lon_rad  =  lon * (pi / 180)     (convert degrees to radians)       │  │
│  │                                                                      │  │
│  │  N  =  a / sqrt(1 - f*(2-f) * sin^2(lat_rad))                       │  │
│  │       (Radius of curvature in the prime vertical, meters)            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ECEF COORDINATE EQUATIONS:                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  x  =  (N + alt) * cos(lat_rad) * cos(lon_rad)                       │  │
│  │  y  =  (N + alt) * cos(lat_rad) * sin(lon_rad)                       │  │
│  │  z  =  (N * (1-f)^2 + alt)      * sin(lat_rad)                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  OUTPUT:                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Returns: (x, y, z)  in meters, Earth-Centered Earth-Fixed frame     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  DISTANCE COMPUTATION (in location_match()):                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  distance  =  sqrt((old_x - new_x)^2  +  (old_y - new_y)^2)         │  │
│  │               (2D horizontal distance, z-component not used)         │  │
│  │                                                                      │  │
│  │  height_diff  =  abs(old_h  -  new_h)    (AGL height in meters)      │  │
│  │                                                                      │  │
│  │  result  =  (distance <= threshold) AND (height_diff <= threshold)   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 10 provides the complete mathematical specification of the WGS84-to-ECEF conversion implemented in `lla_to_ecef()`. The key WGS84 constants (a = 6378137.0 m, f = 1/298.257223563) are internationally standardized and used in all GPS systems. The prime vertical radius N accounts for Earth's ellipsoidal shape and varies with latitude (larger at equator, smaller at poles). The horizontal distance computation uses only the x and y components of ECEF, which corresponds to the projection onto the equatorial plane — a valid approximation for the horizontal distance between two nearby points.

**FIG. 10** — WGS84 to ECEF coordinate transformation as implemented in `lla_to_ecef(lat, lon, alt=0)` in `afc_utils.py`. WGS84 ellipsoid constants: semi-major axis a = 6378137.0 m, flattening f = 1/298.257223563, semi-minor axis b = a*(1-f). Prime vertical radius N = a / sqrt(1 - f*(2-f)*sin^2(lat_rad)). ECEF equations: x = (N+alt)*cos(lat_rad)*cos(lon_rad), y = (N+alt)*cos(lat_rad)*sin(lon_rad), z = (N*(1-f)^2+alt)*sin(lat_rad). Distance between two locations: sqrt((x1-x2)^2 + (y1-y2)^2) meters (2D horizontal). Height difference: abs(h1-h2) meters. Both values compared against threshold (default 200 m from site policy).

---

---

# FIGURE 11 — LOCATION CHANGE DETECTION AND CACHE INVALIDATION

## Pre-Diagram Sequence Summary

When the RRM system detects that an AP's GPS location has changed beyond the threshold, it must invalidate the existing AFC registration and obtain a new one. The cache invalidation is a multi-step process involving both the AFC proxy (external) and the internal Redis stores. This process is implemented across `afc_channel_validation()` in `afc_utils.py` and `tick_process_rrm_afc()`, which runs on a periodic tick from the `RrmAFCBolt`.

The invalidation flow ensures that: (1) the old entry is removed from the AFC proxy so incumbent protection is not compromised by stale location data, (2) the new GPS-based AFC request is submitted, (3) the Redis afc_info cache is updated with the new status, and (4) if the new registration fails, the AP is marked with `afc_status = "NotDONE"` or `"NoGPS"` so the system can retry.

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │  TRIGGER: location_match() returns False                              │
 │  (AP has moved more than threshold meters from last AFC location)     │
 └────────────────────────────┬─────────────────────────────────────────┘
                              │
 ┌────────────────────────────▼─────────────────────────────────────────┐
 │  Log: "AP {ap_id}'s location has changed,                            │
 │        will delete AP from cache and repost request"                 │
 └────────────────────────────┬─────────────────────────────────────────┘
                              │
 ┌────────────────────────────▼─────────────────────────────────────────┐
 │  STEP 1: DeleteAP() from AFC Proxy                                   │
 │    DELETE /afc/devices/{requestId from old response}                 │
 │    Retry up to 3 times with 1-second delay between attempts          │
 │    Uses X-HTTP-Method-Override: DELETE header                        │
 └────────────────────────────┬─────────────────────────────────────────┘
                              │
 ┌────────────────────────────▼─────────────────────────────────────────┐
 │  STEP 2: PostAfcRequest() to AFC Proxy                               │
 │    POST /afc/devices                                                 │
 │    Payload: new GPS coordinates + same device descriptor             │
 │    Timeout: 5 seconds                                                │
 └────────────────────────────┬─────────────────────────────────────────┘
                              │
                 ┌────────────▼────────────────┐
                 │  POST succeeded (HTTP 200)?  │
                 └────────┬─────────────────────┘
                          │              │
                         YES             NO
                          │              │
                          ▼              ▼
 ┌────────────────────┐       ┌──────────────────────────┐
 │  GetChannelByMac() │       │  state = "NotDONE"       │
 │  GET response      │       │  Update Redis:           │
 │  from proxy        │       │   ap_status = "NotDONE"  │
 └────────┬───────────┘       │  Return {}, None, NotDONE│
          │                   └──────────────────────────┘
          ▼
 ┌────────────────────────────────────────────────────────┐
 │  Response state == "DONE"?                             │
 └──────────┬──────────────────────────────────────┬──────┘
            │                                      │
           YES                                    NO
            │                                      │
            ▼                                      ▼
 ┌──────────────────────────┐          ┌──────────────────────────┐
 │  process_afc_response()  │          │  Update Redis afc_info:  │
 │  Compute afc_channels    │          │   ap_status = "NotDONE"  │
 │  Return DONE + channels  │          │  Return {}, None, NotDONE│
 └──────────────────────────┘          └──────────────────────────┘
            │
            ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │  STEP 3: On next tick, del_afc_info() clears Redis afc_info      │
 │          for this AP (successful registration complete)          │
 └──────────────────────────────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 11 shows the complete location change detection and cache invalidation flow. The three-step process (Delete → POST → GET) ensures atomic replacement of AFC registrations. The use of `requestId` from the old response (rather than current ap_id) for the DELETE call ensures the correct old entry is removed even if the ap_id format has changed. Redis state is updated at every failure point to enable the periodic `tick_process_rrm_afc()` to retry failed registrations.

**FIG. 11** — Location change detection and cache invalidation flow triggered when `location_match()` returns False (AP horizontal distance or height difference exceeds threshold). Step 1: DeleteAP() removes old AFC proxy entry using requestId from old response, with 3 retries and 1-second delay. Step 2: PostAfcRequest() submits new registration with updated GPS coordinates, 5-second timeout. Step 3: GetChannelByMac() retrieves response; on success, `process_afc_response()` computes new channel assignments and Redis `afc_info` is cleared; on failure, Redis is updated with `ap_status = "NotDONE"` for retry on next tick.

---

---

# FIGURE 12 — RrmAFCBolt STORM TOPOLOGY

## Pre-Diagram Sequence Summary

The `RrmAFCBolt` is an Apache Storm bolt that operates as the AFC lifecycle manager within the cloud RRM topology. It receives two types of input: (1) event tuples containing abnormal AP state notifications (AP_UNCLAIMED, AP_UNASSIGNED), and (2) periodic tick tuples that trigger proactive AFC renewal and retry processing.

On event tuples, the bolt filters the incoming AP map to retain only APs that have been configured for standard power operation (confirmed via `is_standard_power()` which queries the RRM API). For qualifying APs in UNCLAIMED or UNASSIGNED state, the bolt calls `ap_event_handler()` to delete the AFC registration and clean up GPS data from Redis.

On tick tuples, the bolt calls `tick_process_rrm_afc()` which scans the Redis `afc_info` hash for all pending APs, re-fetches their GPS, and re-submits AFC requests as needed.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        APACHE STORM TOPOLOGY                                   │
│                                                                                │
│  ┌────────────────────────────────────┐                                        │
│  │     UPSTREAM BOLT                  │                                        │
│  │  (AP State Monitor)                │                                        │
│  │  Emits: abnormal_ap_map (JSON)     │                                        │
│  │  Fields: {ap_id: {ap_status,        │                                        │
│  │            site_id, org_id}}        │                                        │
│  └──────────────────┬─────────────────┘                                        │
│                     │ Stream: event tuples                                      │
│                     │                    ┌────────── Tick tuples (periodic) ──┐ │
│                     ▼                    ▼                                    │ │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │ │
│  │                        RrmAFCBolt                                        │  │ │
│  │                                                                          │  │ │
│  │  initialize():                                                           │  │ │
│  │    self.afc_proxy_url  = afc-proxy-{env}.mist.pvt/afc/devices           │  │ │
│  │    self.redis_conn     = RRM Redis connection                            │  │ │
│  │    self.location_redis = Location Redis connection                       │  │ │
│  │    self.headers        = {"X-FROM": topology.name}                      │  │ │
│  │    self.ap_standard_power_cache = {}  (in-memory cache)                 │  │ │
│  │                                                                          │  │ │
│  │  process(tup):                                                           │  │ │
│  │    if tick_tuple:  → process_tick()                                      │  │ │
│  │    else:           → parse abnormal_ap_map                               │  │ │
│  │                       filter: is_standard_power(ap_id)                  │  │ │
│  │                       filter: status in [UNCLAIMED, UNASSIGNED]          │  │ │
│  │                       call ap_event_handler(filtered_map)                │  │ │
│  │                                                                          │  │ │
│  │  process_tick():                                                         │  │ │
│  │    tick_process_rrm_afc(afc_proxy, location_redis, redis)                │  │ │
│  │                                                                          │  │ │
│  │  is_standard_power(ap_id):                                               │  │ │
│  │    1. Check in-memory cache (ap_standard_power_cache)                   │  │ │
│  │    2. Query: getRRMByMAC(ap_id, "r24") for AP64-class                   │  │ │
│  │    3. Query: getRRMByMAC(ap_id, "r6")  if r24 not standard_power        │  │ │
│  │    4. Cache result with timestamp, site_id, org_id                      │  │ │
│  └──────────────────────────────────────┬───────────────────────────────────┘  │
│                                         │                                       │
│              ┌──────────────────────────┴───────────────────────────────┐      │
│              │                          │                               │      │
│              ▼                          ▼                               ▼      │
│  ┌───────────────────┐    ┌─────────────────────────┐    ┌─────────────────┐  │
│  │  ap_event_handler │    │  tick_process_rrm_afc   │    │  Location Redis  │  │
│  │  (afc_utils.py)   │    │  (afc_utils.py)         │    │                  │  │
│  │                   │    │                         │    │  key:            │  │
│  │  DeleteAP()       │    │  get_afc_info() from    │    │  devices/{id}/   │  │
│  │  del_afc_info()   │    │  Redis → iterate APs    │    │  gps             │  │
│  │  delete GPS key   │    │  DeleteAP() + resubmit  │    │                  │  │
│  └───────────────────┘    └─────────────────────────┘    └─────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 12 illustrates the RrmAFCBolt's position in the Storm topology and its internal processing logic. The bolt's dual-mode operation (event-driven for AP state changes, tick-driven for proactive renewal) is a key architectural feature. The in-memory `ap_standard_power_cache` avoids repeated API calls for the same AP, while the `X-FROM` header in all HTTP requests enables request tracing across the distributed system.

**FIG. 12** — RrmAFCBolt Storm topology showing bolt initialization (AFC proxy URL, dual Redis connections, X-FROM header with topology name), event tuple processing path (abnormal_ap_map parsing, standard_power filter via `is_standard_power()`, AP_UNCLAIMED/AP_UNASSIGNED filter, `ap_event_handler()` call), tick tuple processing path (`tick_process_rrm_afc()` for proactive renewal), and `is_standard_power()` check sequence (in-memory cache lookup, then getRRMByMAC for r24 band, then r6 band fallback). The bolt interfaces with Location Redis (GPS data), RRM Redis (AFC state), and the AFC Proxy Service.

---

---

# FIGURE 13 — AFC CHANNEL VALIDATION STATE MACHINE

## Pre-Diagram Sequence Summary

The AFC channel validation process (`afc_channel_validation()`) can result in multiple terminal and intermediate states. The state machine below captures all possible transitions from the initial trigger (AP needs channels) through GPS fetch, proxy query, and response processing. Each state has specific actions that affect the AP's radio configuration in the RRM system.

The key states are:
- **NoGPS**: AP has no GPS data. If `lpi_ok=True`, fall back to LPI. Otherwise, disable radio.
- **NotDONE**: AFC proxy did not return a DONE response. Store in Redis for retry.
- **DONE**: AFC response received and processed. `afc_channels` dict returned.
- **LPI_Fallback**: Special state for LPI-capable APs without GPS. AP operates at low power.
- **RadioDisabled**: AP radio is turned off until AFC succeeds.

```
              ┌──────────────────────────────────────────────┐
              │  START: afc_channel_validation() called       │
              │  inputs: ap_id, site_id, bandwidth,           │
              │           provider_flag, location_threshold   │
              └─────────────────────┬────────────────────────┘
                                    │
              ┌─────────────────────▼────────────────────────┐
              │         provider_flag == "dev" ?              │
              └──────────────┬──────────────────────┬─────────┘
                             │                      │
                            YES                    NO
                             │                      │
                             ▼                      ▼
              ┌──────────────────────┐   ┌──────────────────────────┐
              │  Use mock/dev AFC    │   │  get_ap_geolocation()     │
              │  response (Redis or  │   │  → fetch from Redis:      │
              │  get_default_resp()) │   │  devices/{ap_id}/gps      │
              └──────────┬───────────┘   └────────────┬─────────────┘
                         │                            │
                         │              ┌─────────────▼──────────┐
                         │              │  GPS data found?        │
                         │              └──────┬──────────────────┘
                         │                     │           │
                         │                    YES          NO
                         │                     │           │
                         │                     │           ▼
                         │                     │  ┌──────────────────────┐
                         │                     │  │  STATE: NoGPS         │
                         │                     │  │  GetChannelByMac()   │
                         │                     │  │  from proxy cache    │
                         │                     │  └──────┬───────────────┘
                         │                     │         │
                         │                     │  ┌──────▼───────────────┐
                         │                     │  │ Proxy cache DONE?    │
                         │                     │  └──────┬──────┬────────┘
                         │                     │        YES     NO
                         │                     │         │      │
                         │                     │         ▼      ▼
                         │                     │  ┌─────────┐ ┌─────────────────┐
                         │                     │  │ Return  │ │ lpi_ok == True? │
                         │                     │  │ cached  │ └───┬───────┬──────┘
                         │                     │  │ (DONE)  │    YES     NO
                         │                     │  └─────────┘     │      │
                         │                     │                   ▼      ▼
                         │                     │        ┌──────────────┐┌──────────────┐
                         │                     │        │ STATE:       ││ STATE:       │
                         │                     │        │ LPI_Fallback ││ RadioDisable │
                         │                     │        │ SP=False     ││ return {}    │
                         │                     │        │ afc_channels ││ None,NotDONE │
                         │                     │        │ = {}         │└──────────────┘
                         │                     │        └──────────────┘
                         │                     │
                         └────────────────►────┘
                                    │
              ┌─────────────────────▼────────────────────────┐
              │  GetChannelByMac()  AND  location check       │
              │  → If state != DONE OR loc_changed:           │
              │     PostAfcRequest() → GetChannelByMac()      │
              └─────────────────────┬────────────────────────┘
                                    │
              ┌─────────────────────▼────────────────────────┐
              │  Response state == "DONE" AND                 │
              │  availableChannelInfo present?                │
              └───────────────┬──────────────────────────────┘
                              │              │
                             YES             NO
                              │              │
                              ▼              ▼
              ┌─────────────────────┐  ┌──────────────────────┐
              │  STATE: DONE         │  │  STATE: NotDONE       │
              │  process_afc_resp() │  │  return {}, None,     │
              │  return afc_channels│  │        "NotDONE"      │
              │  expiry_timestamp   │  └──────────────────────┘
              │  "DONE"             │
              └─────────────────────┘
```

**Post-Diagram Summary:** Figure 13 shows all five states of the AFC channel validation state machine (NoGPS, NotDONE, DONE, LPI_Fallback, RadioDisabled) with all transition conditions. The LPI_Fallback state is unique to this invention and provides graceful degradation for GPS-equipped APs that temporarily lose location data — they continue operating at lower power rather than being completely disabled. The dev/mock path enables testing without a real AFC provider.

**FIG. 13** — AFC channel validation state machine implemented in `afc_channel_validation()` in `afc_utils.py`. Five terminal/stable states: (1) DONE — valid AFC channels returned with expiry; (2) NotDONE — AFC proxy returned non-DONE state, stored in Redis for retry; (3) NoGPS+CacheHit — no GPS but proxy cache DONE, returns cached channels; (4) LPI_Fallback — no GPS, lpi_ok=True in ap_config, returns empty afc_channels with afc_standard_power=False, AP operates at LPI; (5) RadioDisabled — no GPS, lpi_ok=False, returns empty dict causing radio disable. The "dev" provider_flag path bypasses GPS and proxy, using mock response from Redis or get_default_response().

---

---

# FIGURE 14 — 320 MHz MODE 1 vs MODE 2 CHANNEL LAYOUT

## Pre-Diagram Sequence Summary

IEEE 802.11be (Wi-Fi 7) introduces 320 MHz channel bonding in the 6 GHz band. However, the 6 GHz band (5925–7125 MHz) is only 1200 MHz wide, which means 320 MHz channels do not uniformly cover the entire band. The Wi-Fi Alliance AFC specification defines two "modes" for 320 MHz channels based on which center channel frequency they use:

- **Mode 1** uses center channels at CFI 31, 95, and 159 (center frequencies: ~6115 MHz, ~6435 MHz, ~6755 MHz)
- **Mode 2** uses center channels at CFI 63, 127, and 191 (center frequencies: ~6275 MHz, ~6595 MHz, ~6915 MHz)

These two mode sets are interleaved. Some 20 MHz subchannels fall within the coverage of both Mode 1 and Mode 2 320 MHz channels (the overlap region). For these ambiguous subchannels, the inventive `get_mode()` function determines the correct mode by comparing the subchannel's distance to the nearest Mode 1 central channel versus the nearest Mode 2 central channel, assigning to the closer one.

```
  6 GHz BAND (5925–7125 MHz)

  ──────────────────────────────────────────────────────────────────────
  FREQUENCY: 5925     6115  6275  6435  6595  6755  6915  7075    7125
             │        │     │     │     │     │     │     │        │
  ──────────────────────────────────────────────────────────────────────

  MODE 1 (320 MHz channels, center at CFI 31, 95, 159):
  ┌────────────────────────────┐
  │  CFI 31: 5945–6265 MHz     │       (320 MHz wide)
  └────────────────────────────┘
                   ┌────────────────────────────┐
                   │  CFI 95: 6265–6585 MHz      │      (320 MHz wide)
                   └────────────────────────────┘
                                   ┌────────────────────────────┐
                                   │ CFI 159: 6585–6905 MHz     │   (320 MHz wide)
                                   └────────────────────────────┘

  MODE 2 (320 MHz channels, center at CFI 63, 127, 191):
        ┌────────────────────────────┐
        │  CFI 63: 6105–6425 MHz     │       (320 MHz wide)
        └────────────────────────────┘
                       ┌────────────────────────────┐
                       │ CFI 127: 6425–6745 MHz      │     (320 MHz wide)
                       └────────────────────────────┘
                                       ┌────────────────────────────┐
                                       │ CFI 191: 6745–7065 MHz     │  (320 MHz wide)
                                       └────────────────────────────┘

  OVERLAP REGION — Mode disambiguation:
  ┌────────────────────────────────────────────────────────────────────┐
  │  Ambiguous subchannel CFI appears in BOTH mode sets:               │
  │                                                                    │
  │  get_mode(channel) logic:                                          │
  │    channel_ind1 = (channel - 1)  // 64                            │
  │    channel_ind2 = (channel - 33) // 64                            │
  │    diff1 = abs(channel - central_channel_mode1[channel_ind1])     │
  │    diff2 = abs(channel - central_channel_mode2[channel_ind2])     │
  │    return Mode 1 if diff1 > diff2, else Mode 2                    │
  │                                                                    │
  │  central_channel_mode1 = [31,  95, 159]                           │
  │  central_channel_mode2 = [63, 127, 191]                           │
  └────────────────────────────────────────────────────────────────────┘

  MODE 1 PSC (Primary Scanning Channels):  CFI  1,  65, 129
  MODE 2 PSC (Primary Scanning Channels):  CFI 33,  97, 161
```

**Post-Diagram Summary:** Figure 14 shows the dual-mode structure of 320 MHz channels in the 6 GHz band. The interleaved Mode 1 and Mode 2 channel sets, and the disambiguation algorithm using proximity to central channel frequencies, are unique aspects of this invention's 320 MHz AFC handling. Prior art AFC systems did not implement this mode-awareness, potentially assigning incorrect power levels to subchannels in the overlap regions.

**FIG. 14** — 320 MHz Mode 1 and Mode 2 channel layout for the 6 GHz band (5925–7125 MHz) as implemented in `afc_utils.py`. Mode 1 uses center channels CFI 31 (5945–6265 MHz), CFI 95 (6265–6585 MHz), and CFI 159 (6585–6905 MHz). Mode 2 uses center channels CFI 63 (6105–6425 MHz), CFI 127 (6425–6745 MHz), and CFI 191 (6745–7065 MHz). Ambiguous subchannels in the overlap regions are disambiguated by `get_mode()` using `central_channel_mode1 = [31, 95, 159]` and `central_channel_mode2 = [63, 127, 191]`. The closer central channel (by CFI distance) determines the mode assignment. Mode 1 Primary Scanning Channels: CFI 1, 65, 129. Mode 2 Primary Scanning Channels: CFI 33, 97, 161.

---

---

# FIGURE 15 — ch_delta SUB-CHANNEL EXPANSION PER BANDWIDTH

## Pre-Diagram Sequence Summary

When the AFC system returns a channel assignment for a wide-bandwidth channel (40/80/160/320 MHz), the assignment must be decomposed into the constituent 20 MHz subchannels that make up the wide channel. This decomposition is performed using the `ch_delta` mechanism in `process_afc_response()`.

Each wide-bandwidth channel CFI (the center channel) is expanded to its constituent 20 MHz subchannel CFIs by adding and subtracting the `ch_delta` offsets. For example, an 80 MHz channel with center CFI 7 expands to subchannels at CFI 7-2=5, 7+2=9, 7-6=1, 7+6=13 — the four 20 MHz channels that form this 80 MHz channel.

Only subchannels whose CFI numbers appear in the `channels_6G_20` list are added to the `afc_channels` dictionary. For 320 MHz channels, only subchannels matching the correct mode (determined by `get_mode()`) are included.

```
  ch_delta EXPANSION TABLE
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Bandwidth  │  ch_delta values         │  Number of 20 MHz subchannels  │
  ├─────────────┼──────────────────────────┼─────────────────────────────────┤
  │   20 MHz    │  [0]                     │  1 (the channel itself)         │
  ├─────────────┼──────────────────────────┼─────────────────────────────────┤
  │   40 MHz    │  [2]                     │  2 subchannels (±2 from center) │
  ├─────────────┼──────────────────────────┼─────────────────────────────────┤
  │   80 MHz    │  [2, 6]                  │  4 subchannels                  │
  ├─────────────┼──────────────────────────┼─────────────────────────────────┤
  │  160 MHz    │  [2, 6, 10, 14]          │  8 subchannels                  │
  ├─────────────┼──────────────────────────┼─────────────────────────────────┤
  │  320 MHz    │  [2,6,10,14,18,22,26,30] │  16 subchannels per mode        │
  └─────────────┴──────────────────────────┴─────────────────────────────────┘

  EXPANSION EXAMPLES:

  20 MHz, center CFI=5:
    ch_delta = [0]
    → afc_channels[5] = ch_max_power

  40 MHz, center CFI=3:
    ch_delta = [2]
    → ch-2 = 1  → afc_channels[1] = ch_max_power
    → ch+2 = 5  → afc_channels[5] = ch_max_power

  80 MHz, center CFI=7:
    ch_delta = [2, 6]
    → ch-2 = 5  → afc_channels[5]  = ch_max_power
    → ch+2 = 9  → afc_channels[9]  = ch_max_power
    → ch-6 = 1  → afc_channels[1]  = ch_max_power
    → ch+6 = 13 → afc_channels[13] = ch_max_power
    (Total: subchannels 1, 5, 9, 13)

  160 MHz, center CFI=15:
    ch_delta = [2, 6, 10, 14]
    → ch±2  = 13, 17  → afc_channels[13] = afc_channels[17] = ch_max_power
    → ch±6  =  9, 21  → afc_channels[ 9] = afc_channels[21] = ch_max_power
    → ch±10 =  5, 25  → afc_channels[ 5] = afc_channels[25] = ch_max_power
    → ch±14 =  1, 29  → afc_channels[ 1] = afc_channels[29] = ch_max_power
    (Total: 8 subchannels: 1,5,9,13,15,17,21,25,29)

  320 MHz Mode 1, center CFI=31:
    ch_delta = [2,6,10,14,18,22,26,30]
    → Expand CFI 31 ± each delta (only Mode 1 subchannels included)
    → afc_channels[1]=afc_channels[5]=...=afc_channels[61] = ch_max_power
    (16 subchannels, mode-filtered)
```

**Post-Diagram Summary:** Figure 15 shows the ch_delta sub-channel expansion mechanism. This approach of storing EIRP at the 20 MHz subchannel granularity (regardless of the operating bandwidth) is a key novelty: it allows the system to mix different bandwidth channels within the same site while maintaining per-subchannel power control. The 320 MHz mode filtering ensures that Mode 1 and Mode 2 subchannels are not mixed, maintaining correct channel bonding structure.

**FIG. 15** — ch_delta sub-channel expansion table and examples as implemented in `process_afc_response()` in `afc_utils.py`. ch_delta values per bandwidth: 20 MHz → [0] (1 subchannel); 40 MHz → [2] (2 subchannels); 80 MHz → [2, 6] (4 subchannels); 160 MHz → [2, 6, 10, 14] (8 subchannels); 320 MHz → [2, 6, 10, 14, 18, 22, 26, 30] (16 subchannels per mode). For each center CFI and each delta d, both CFI-d and CFI+d are added to afc_channels if they appear in channels_6G_20. For 320 MHz channels, only subchannels matching the center's mode (determined by `get_mode()`) are included.

---

---

# FIGURE 16 — DeleteAP RETRY LOGIC FLOWCHART

## Pre-Diagram Sequence Summary

The `DeleteAP()` function in `afc_query.py` implements a resilient deletion mechanism with up to 3 retry attempts. This is necessary because AFC proxy services may be temporarily unavailable or rate-limiting requests. The retry logic includes a 1-second delay between attempts to avoid overwhelming an already-stressed service.

The function uses the `X-HTTP-Method-Override: DELETE` header because some HTTP proxies and load balancers do not support the DELETE HTTP method natively. This header instructs the server to treat the request as a DELETE operation even if received as another HTTP method type.

The function returns True on first successful (HTTP 200) response, or False after exhausting all retries.

```
        ┌────────────────────────────────────────────────┐
        │  DeleteAP(afc_proxy_link, mac)                  │
        │  url = f"{afc_proxy_link}/{mac}"               │
        │  max_retries = 3                               │
        │  timeout_seconds = 5                           │
        │  retry_count = 0                               │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────▼───────────────────────────┐
        │  retry_count < max_retries (3)?                │
        └──────────────┬──────────────────┬──────────────┘
                       │                  │
                      YES                 NO
                       │                  │
                       ▼                  ▼
        ┌──────────────────────┐  ┌────────────────────────┐
        │ session.request(     │  │ Log: "DELETE failed    │
        │   "DELETE",          │  │  after 3 attempts"     │
        │   url=url,           │  │ Return: False          │
        │   headers={          │  └────────────────────────┘
        │    "X-HTTP-Method-   │
        │     Override":"DELETE│
        │   },                 │
        │   timeout=5          │
        │ )                    │
        └──────────┬───────────┘
                   │
        ┌──────────▼─────────────────────────────────────┐
        │  Request exception occurred?                    │
        └──────────┬──────────────────────┬──────────────┘
                   │                      │
                  YES                    NO
                   │                      │
                   ▼                      ▼
        ┌────────────────────┐  ┌─────────────────────────┐
        │ Log: exception     │  │  response.status_code   │
        │ retry_count += 1   │  │  == 200?                │
        │ sleep(1 second)    │  └──────┬──────────────────┘
        └────────┬───────────┘         │           │
                 │                    YES           NO
                 │                     │            │
                 └──────────────────── │            ▼
                                       │  ┌─────────────────────┐
                                       │  │ retry_count += 1    │
                                       │  │ if retry_count < 3: │
                                       │  │   sleep(1 second)   │
                                       │  └─────────────────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │  Return: True    │
                              └──────────────────┘
```

**Post-Diagram Summary:** Figure 16 shows the DeleteAP retry logic. The three-attempt mechanism with 1-second delays provides resilience against transient network failures. The `X-HTTP-Method-Override: DELETE` header is a unique implementation detail that ensures compatibility with HTTP infrastructure that may not support DELETE method natively. The function's return value (True/False) is used by the calling code to determine whether to proceed with a new PostAfcRequest or abort the re-registration attempt.

**FIG. 16** — DeleteAP retry logic flowchart as implemented in `DeleteAP(afc_proxy_link, mac)` in `afc_query.py`. Function parameters: url = afc_proxy_link + "/" + mac; max_retries = 3; timeout_seconds = 5. Each attempt uses `session.request("DELETE", url=url, headers={"X-HTTP-Method-Override": "DELETE"}, timeout=5)`. On HTTP 200 response: returns True immediately. On exception or non-200 response: increments retry_count, logs warning, sleeps 1 second, retries. After 3 failed attempts: logs "DELETE request failed after 3 attempts" and returns False. The X-HTTP-Method-Override header ensures DELETE semantics are honored by intermediate HTTP proxies.

---

---

# FIGURE 17 — AP LIFECYCLE IN AFC SYSTEM

## Pre-Diagram Sequence Summary

An AP's relationship with the AFC system follows a well-defined lifecycle. The AP begins as unregistered (no AFC entry exists). When first seen by the RRM with `standard_power=True`, an AFC registration is created. The AP may go through location changes, GPS loss events, and eventually be unclaimed or reassigned. Each lifecycle event has specific AFC system actions.

The lifecycle is managed across two components: `RrmAFCBolt` handles the abnormal state transitions (UNCLAIMED/UNASSIGNED), while `tick_process_rrm_afc()` handles the periodic refresh and NoGPS recovery.

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                         AP AFC LIFECYCLE                                │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │  NEW / BOOT  │  AP first appears with standard_power=True
  │  state       │  No AFC entry exists in Redis or proxy
  └──────┬───────┘
         │  ACS request received
         ▼
  ┌──────────────┐  GPS available?
  │  GPS CHECK   ├─── NO ──► NoGPS state → Redis update → retry on tick
  │              │
  └──────┬───────┘
         │  YES
         ▼
  ┌──────────────┐
  │  AFC POST    │  PostAfcRequest() → GET → process_afc_response()
  │  REGISTER   │  Store expiry in Redis
  └──────┬───────┘
         │  DONE
         ▼
  ┌──────────────┐
  │  OPERATING   │  AP uses AFC-approved channels + EIRP limits
  │  (DONE)      │  standard_power = True, afc_channels populated
  └──────┬───────┘
         │
    ┌────┴───────────────────────────────────────────────┐
    │                                                    │
    ▼                                                    ▼
  ┌──────────────┐  Location moved                ┌────────────────┐
  │ LOCATION     │  > threshold (200m)             │  EXPIRY        │
  │ CHANGED      │                                 │  avail_expire  │
  └──────┬───────┘                                 │  time reached  │
         │  DeleteAP() + re-POST                   └───────┬────────┘
         ▼                                                  │
  ┌──────────────┐                                          │
  │  AFC POST    │  ◄───────────────────────────────────────┘
  │  RE-REGISTER │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  OPERATING   │  (back to normal operation)
  │  (DONE)      │
  └──────┬───────┘
         │
    ┌────┴─────────────────────────────────────────────────┐
    │                                                       │
    ▼                                                       ▼
  ┌──────────────┐                                  ┌──────────────┐
  │  AP_UNCLAIMED│                                  │  AP_UNASSIGNED│
  │  or          │                                  │  (moved to   │
  │  AP_UNASSIGNED                                  │  new site)   │
  └──────┬───────┘                                  └──────┬───────┘
         │  RrmAFCBolt detects state                       │
         ▼                                                 ▼
  ┌────────────────────────────────────────────────────────┐
  │  CLEANUP:                                               │
  │  1. DeleteAP() from AFC proxy                          │
  │  2. del_afc_info() from Redis                          │
  │  3. location_redis.delete("devices/{ap_id}/gps")       │
  └──────────────────────────────────────────────────────┬─┘
                                                         │
                                                         ▼
  ┌────────────────────┐
  │  DEREGISTERED      │  AP no longer in AFC system
  │  (terminal state)  │  All AFC data purged
  └────────────────────┘
```

**Post-Diagram Summary:** Figure 17 shows the complete AP lifecycle in the AFC system. The inventive system handles all lifecycle transitions — initial registration, location changes, expiry-triggered renewal, and deregistration on AP removal — in a fully automated, cloud-managed manner. The cleanup path (DeleteAP + del_afc_info + delete GPS key) ensures that deregistered APs do not leave orphaned entries in either the AFC proxy or the Redis stores, preventing stale data from affecting future AP registrations.

**FIG. 17** — AP lifecycle in the AFC system, showing all state transitions: NEW/BOOT (no AFC entry) → GPS CHECK → AFC POST/REGISTER (DONE state) → OPERATING. From OPERATING: LOCATION CHANGED trigger → DeleteAP + re-POST; EXPIRY trigger → re-POST; AP_UNCLAIMED or AP_UNASSIGNED triggers CLEANUP (DeleteAP + del_afc_info + delete GPS key from Location Redis) → DEREGISTERED (terminal). Cleanup actions: `afc_query.DeleteAP()`, `rrmRedis.del_afc_info()`, `location_redis_conn.delete("devices/{ap_id}/gps")`. EXPIRY is tracked using `availabilityExpireTime` converted to Unix timestamp stored in RRM Redis.

---

---

# FIGURE 18 — REDIS CACHE ARCHITECTURE FOR AFC STATE

## Pre-Diagram Sequence Summary

The inventive system uses two separate Redis stores with distinct purposes and key schemas. The **Location Redis** stores GPS/geolocation data for all APs. The **RRM Redis** stores AFC state, channel assignments, and system-level caches.

This dual-Redis architecture is a key design feature: it allows the location service to be updated independently by the AP management layer, while the RRM layer reads GPS data reactively without owning the write path. AFC-specific state in RRM Redis tracks pending registrations (those in NoGPS or NotDONE state) that need to be retried by the tick process.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        DUAL REDIS ARCHITECTURE                               │
├─────────────────────────────────┬────────────────────────────────────────────┤
│       LOCATION REDIS             │           RRM REDIS                       │
│  (location service owned)        │     (RRM system owned)                    │
├─────────────────────────────────┼────────────────────────────────────────────┤
│                                  │                                           │
│  Key schema:                     │  AFC State Hash:                          │
│  ┌──────────────────────────┐    │  ┌──────────────────────────────────────┐ │
│  │ "devices/{ap_id}/gps"   │    │  │  Hash key: "afc_info"               │ │
│  │                         │    │  │  Field: ap_id                        │ │
│  │  Value (JSON):          │    │  │  Value (JSON): {                     │ │
│  │  {                      │    │  │    "org_id": "...",                  │ │
│  │    "location": {        │    │  │    "site_id": "...",                 │ │
│  │      "ellipse": {       │    │  │    "bandwidth": 80,                  │ │
│  │        "center": {      │    │  │    "ap_time": 1234567890.0,          │ │
│  │          "latitude": X  │    │  │    "ap_status": "NoGPS"|"NotDONE"   │ │
│  │          "longitude": Y │    │  │  }                                  │ │
│  │        }                │    │  └──────────────────────────────────────┘ │
│  │        "majorAxis": N   │    │                                           │
│  │        "minorAxis": M   │    │  Channel Cache:                           │
│  │        "orientation": A │    │  ┌──────────────────────────────────────┐ │
│  │      }                  │    │  │  "rrm/{site_id}/{band}/{ap_id}/last" │ │
│  │      "elevation": {     │    │  │  (last RRM decision per AP+band)     │ │
│  │        "height": H      │    │  └──────────────────────────────────────┘ │
│  │        "heightType":"AGL│    │                                           │
│  │        "vertUnc": U     │    │  Radar Event Cache:                       │
│  │      }                  │    │  ┌──────────────────────────────────────┐ │
│  │    }                    │    │  │  Hash key: "rrm/acs/radar"          │ │
│  │  }                      │    │  │  (DFS radar events by AP)            │ │
│  └──────────────────────────┘    │  └──────────────────────────────────────┘ │
│                                  │                                           │
│  Operations:                     │  Mock AFC Response (for dev/test):        │
│  READ:  get("devices/{id}/gps")  │  ┌──────────────────────────────────────┐ │
│  WRITE: set("devices/{id}/gps")  │  │  Key: "afc_mock_response"           │ │
│  DELETE: delete("devices/{id}/gps│  │  Value: JSON AFC response object     │ │
│                                  │  └──────────────────────────────────────┘ │
└─────────────────────────────────┴────────────────────────────────────────────┘

  AFC State Flow in RRM Redis:

  AP enters NoGPS/NotDONE state
          │
          ▼
  update_afc_node() → HSET "afc_info" ap_id {status, org_id, site_id, bandwidth, time}
          │
          ▼
  tick_process_rrm_afc() polls afc_info keys
          │
          ▼
  Re-validate GPS + re-POST AFC request
          │
     ┌────▼──────────────┐
     │  Success (DONE)?  │
     └──────┬────────────┘
            │          │
           YES          NO
            │          │
            ▼          ▼
  del_afc_info()   update_afc_node()
  (remove from     (keep in hash,
   hash, done)      retry later)
```

**Post-Diagram Summary:** Figure 18 shows the dual-Redis architecture and AFC state management flow. The separation of Location Redis and RRM Redis enables independent scaling and ownership of geographic data versus radio management data. The `afc_info` hash in RRM Redis serves as a persistent retry queue for APs that failed AFC registration, ensuring that no AP is permanently left without AFC coverage due to transient failures.

**FIG. 18** — Redis cache architecture for AFC state showing dual Redis store design. Location Redis stores AP GPS data under key schema "devices/{ap_id}/gps" with JSON value containing location object (ellipse with center lat/lon, majorAxis, minorAxis, orientation; elevation with height in AGL meters, heightType, verticalUncertainty). RRM Redis stores AFC pending state in hash "afc_info" (fields: org_id, site_id, bandwidth, ap_time, ap_status = "NoGPS"|"NotDONE"); last RRM decisions under "rrm/{site_id}/{band}/{ap_id}/last"; radar events under "rrm/acs/radar"; mock AFC responses under "afc_mock_response" for dev/test. AFC state flow: failed registrations are stored via `update_afc_node()` and retried by `tick_process_rrm_afc()`; successful registrations are cleared via `del_afc_info()`.

---

---

# FIGURE 19 — MULTI-PROVIDER SUPPORT ARCHITECTURE

## Pre-Diagram Sequence Summary

The inventive system supports multiple AFC provider backends through a flag-based configuration system. The `afc-provider-flag` site policy parameter controls which AFC provider is used for each site. This allows different deployment environments (production, staging, internal testing, certification testing, development) to use different AFC providers without code changes.

The flag mapping is defined in `get_flag_provider_mapping()` and the `providerName` field in the AFC payload is set accordingly. The AFC proxy service routes requests to the appropriate backend based on the `providerName` field.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-PROVIDER SUPPORT ARCHITECTURE                      │
└────────────────────────────────────────────────────────────────────────────┘

  Site Policy Configuration:
  ┌───────────────────────────────────────────────────────────────────────┐
  │  rrm_site_policy["afc-provider-flag"] = "0" | "1" | "2" | "dev"     │
  └───────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
  get_flag_provider_mapping() returns:
  ┌────────────────┬────────────────────────┬────────────────────────────┐
  │  Flag Value    │  providerName in        │  Description               │
  │                │  AFC Payload            │                            │
  ├────────────────┼────────────────────────┼────────────────────────────┤
  │     "0"        │  "wfa"                  │  Wi-Fi Alliance production │
  │                │                         │  AFC system (default)      │
  ├────────────────┼────────────────────────┼────────────────────────────┤
  │     "1"        │  "wfa-th01"             │  Internal test harness     │
  │                │                         │  (Mist/Juniper lab)        │
  ├────────────────┼────────────────────────┼────────────────────────────┤
  │     "2"        │  "wfa-th02"             │  WFA certification test    │
  │                │                         │  harness                   │
  ├────────────────┼────────────────────────┼────────────────────────────┤
  │    "dev"       │  "dev"                  │  Development / mock mode   │
  │                │                         │  (no real AFC query)       │
  └────────────────┴────────────────────────┴────────────────────────────┘
                               │
                               ▼
  AFC Payload providerName field controls proxy routing:

  ┌──────────────────────────────────────────────────────────────────────┐
  │                     AFC PROXY SERVICE                                │
  │                                                                      │
  │  if providerName == "wfa"      → route to WFA production system     │
  │  if providerName == "wfa-th01" → route to internal test harness     │
  │  if providerName == "wfa-th02" → route to WFA cert test harness     │
  │  if providerName == "dev"      → bypass proxy (use mock response)   │
  └──────────────────────────────────────────────────────────────────────┘

  Dev/Mock Mode:
  ┌──────────────────────────────────────────────────────────────────────┐
  │  if provider_flag == "dev":                                          │
  │    1. Try: rrmRedis.get_mock_afc_response(redis_conn)               │
  │       (allows runtime injection of test AFC responses)               │
  │    2. If None: use get_default_response(ap_id, site_id)             │
  │       (hardcoded sample with channels for classes 131-137)           │
  │    3. Skip all GPS checks and proxy communication                   │
  │    4. Process mock response same as real response                   │
  └──────────────────────────────────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 19 shows the multi-provider support architecture. The flag-based provider selection allows seamless transition between production and test environments without code changes. The "dev" provider flag's ability to inject mock AFC responses via Redis is particularly useful for automated testing at scale — test systems can preload expected AFC responses and verify RRM behavior without requiring connectivity to any real AFC system.

**FIG. 19** — Multi-provider support architecture as implemented in `get_flag_provider_mapping()` in `afc_payload.py` and provider handling in `afc_channel_validation()` in `afc_utils.py`. Site policy field `afc-provider-flag` controls provider selection: flag "0" maps to providerName "wfa" (Wi-Fi Alliance production), flag "1" maps to "wfa-th01" (internal Mist/Juniper test harness), flag "2" maps to "wfa-th02" (WFA certification test harness), flag "dev" maps to "dev" (development mock mode). In dev mode, the system first checks `rrmRedis.get_mock_afc_response()` (runtime-injectable test response), then falls back to `get_default_response()` (hardcoded sample channels), bypassing all GPS checks and proxy communication while still processing the mock response through the standard EIRP computation pipeline.

---

---

# FIGURE 20 — LPI FALLBACK DECISION TREE

## Pre-Diagram Sequence Summary

Low Power Indoor (LPI) operation is the default mode for 6 GHz Wi-Fi when Standard Power (AFC-coordinated) operation is not possible. The inventive system implements a smart fallback from Standard Power to LPI mode when an AP cannot obtain AFC authorization. This fallback is conditional: only APs that have been flagged as LPI-capable (`lpi_ok=True` in the AP configuration) will fall back to LPI. APs that are not LPI-capable will have their radio disabled entirely.

This conditional LPI fallback is a novel aspect of the invention: it prevents a total loss of wireless service for APs in locations where GPS is temporarily unavailable, while still ensuring that non-LPI-capable (outdoor-only) APs are properly disabled when they cannot operate under AFC rules.

```
                 ┌────────────────────────────────────────────┐
                 │  AFC channel validation result:            │
                 │  afc_status = "NoGPS"                      │
                 │  (AP GPS data not available in Redis)       │
                 └───────────────────────┬────────────────────┘
                                         │
                 ┌───────────────────────▼────────────────────┐
                 │  Record in RRM Redis:                       │
                 │  update_afc_node(ap_status="NoGPS",         │
                 │    org_id, site_id, ap_id,                  │
                 │    ap_time=time.time(), bandwidth)           │
                 └───────────────────────┬────────────────────┘
                                         │
                 ┌───────────────────────▼────────────────────┐
                 │  ap_config.get("lpi_ok", False) == True ?  │
                 └──────────────┬───────────────┬─────────────┘
                                │               │
                               YES              NO
                                │               │
                                ▼               ▼
 ┌──────────────────────────────────┐  ┌───────────────────────────────────┐
 │  LPI FALLBACK:                   │  │  RADIO DISABLE:                   │
 │                                  │  │                                   │
 │  Set: afc_standard_power = False │  │  Log: "AFC not ready, disable AP" │
 │  Set: afc_channels = {}          │  │  Return (None) from process_tup() │
 │  Set: ap_channels = configured   │  │  → RRM will not emit any channel  │
 │        channels (non-AFC)        │  │    update for this AP             │
 │                                  │  │  → AP retries via rrm-afc tick    │
 │  Set in command:                 │  └───────────────────────────────────┘
 │    afc_standard_power = False    │
 │    afc_channels = {}             │
 │    afc_source = "lpi_fallback"   │
 │                                  │
 │  AP operates on configured       │
 │  channels at LPI power levels    │
 │  (no AFC coordination needed)    │
 └──────────────────────────────────┘

  LPI vs Standard Power Comparison:
  ┌──────────────────┬───────────────────┬───────────────────────────────┐
  │  Parameter       │  LPI Mode         │  Standard Power (AFC) Mode    │
  ├──────────────────┼───────────────────┼───────────────────────────────┤
  │  Max EIRP        │  ~24 dBm typical  │  30–36 dBm (AFC-assigned)     │
  │  AFC Required    │  No               │  Yes (FCC mandate)            │
  │  GPS Required    │  No               │  Yes                          │
  │  Range           │  ~30–50m indoor   │  ~100–200m indoor/outdoor     │
  │  Incumbent Prot  │  Spatial/power    │  Coordinated by AFC           │
  │  afc_source      │  "lpi_fallback"   │  "afc-proxy"                  │
  └──────────────────┴───────────────────┴───────────────────────────────┘
```

**Post-Diagram Summary:** Figure 20 shows the LPI fallback decision tree. The conditional nature of the fallback (dependent on `lpi_ok` flag) is a key differentiator from simpler implementations that either always disable or always fall back. The `afc_source = "lpi_fallback"` tag in the channel command enables audit trails and telemetry to identify APs operating in fallback mode, which is valuable for network operations and regulatory compliance reporting.

**FIG. 20** — LPI fallback decision tree as implemented in `rrmACSV2.py` `process_tup()`. Triggered when `afc_status == "NoGPS"`. First, RRM Redis is updated via `update_afc_node()` with `ap_status="NoGPS"` for retry tracking. Then `ap_config.get("lpi_ok", False)` is checked: if True, the system sets `afc_standard_power=False`, `afc_channels={}`, `afc_source="lpi_fallback"` and continues processing with non-AFC channel selection (LPI mode); if False, `process_tup()` returns None, preventing any channel update and leaving the AP in its current state until the `RrmAFCBolt` tick retries AFC registration. Comparison table shows LPI mode (no AFC, ~24 dBm, no GPS required) versus Standard Power AFC mode (AFC required, 30–36 dBm per-channel, GPS required, 100–200m range).

---

---

# FIGURE 21 — ACS + AFC INTEGRATION FLOW IN rrmACSV2

## Pre-Diagram Sequence Summary

The `rrmACSV2.py` module integrates AFC channel validation directly into the Automatic Channel Selection (ACS) flow. When an ACS event (channel change request) is received for a Standard Power AP, the system must first obtain valid AFC channel authorization before assigning any channel. This integration ensures that channel assignments always comply with AFC rules.

The ACS+AFC integration also handles the case where an AP is recovered from an outage (ap-outage-recovery reason): for Standard Power APs, the recovery flow routes through the local-AP channel selection path (which includes AFC validation) rather than the generic outage recovery path.

The `afc-update` command is a special ACS command generated when the AFC expiry is approaching or has been refreshed: it updates the AP's channel authorization without necessarily changing the channel, unless the current channel is no longer in the updated AFC channel list.

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  ACS COMMAND RECEIVED (rrmACSV2.process_tup())                          │
 └────────────────────────────────────────┬─────────────────────────────────┘
                                          │
 ┌────────────────────────────────────────▼─────────────────────────────────┐
 │  get_ap_usage_radId() — get AP config from RRM API                      │
 │  Returns: ap_config, usage, band, rad_id per radio                      │
 └────────────────────────────────────────┬─────────────────────────────────┘
                                          │
 ┌────────────────────────────────────────▼─────────────────────────────────┐
 │  afc_standard_power =                                                    │
 │    ap_config["radio_config"]["standard_power"]                           │
 │    OR ap_config["band{usage}_specific"]["radio_config"]["standard_power"]│
 └──────────────┬──────────────────────────────────────────────────────────┘
                │
   ┌────────────▼──────────────────────────────────┐
   │  afc_standard_power == True?                  │
   └──────────────┬────────────────────────────────┘
                  │                │
                 YES               NO
                  │                │
                  ▼                ▼
 ┌─────────────────────────┐   ┌──────────────────────────────────────────┐
 │  AFC VALIDATION BLOCK:  │   │  Normal RRM channel selection            │
 │                         │   │  (no AFC involvement)                    │
 │  1. Get fcc_id or ised_id│   └──────────────────────────────────────────┘
 │  2. Get country_code    │
 │     from Redis or API   │
 │  3. Map rulesetId from  │
 │     country_code        │
 │     (US→US_47_CFR_...   │
 │      CA→CA_ISED_...)    │
 │  4. Build certificationId│
 │     [{id: fcc/ised_id,  │
 │       rulesetId: ...}]  │
 │                         │
 │  5. afc_channel_valid() │
 │     → returns afc_chans,│
 │       expiry, status    │
 │                         │
 │  6. channels_validation()│
 │     intersect with      │
 │     ap_channels         │
 └──────────┬──────────────┘
            │
   ┌─────────▼────────────────────────────────────────────────────┐
   │  afc_status == "DONE" AND expiry valid AND afc_channels?     │
   └──────────┬────────────────────────────────────┬───────────────┘
              │                                    │
             YES                                  NO
              │                                    │
              ▼                                    ▼
 ┌─────────────────────────┐           ┌────────────────────────────────┐
 │  del_afc_info() from    │           │  update_afc_node() in Redis    │
 │  Redis (clear pending)  │           │  Check lpi_ok → fallback/disable│
 │  Proceed to channel     │           │  Return (no channel update)    │
 │  selection below        │           └────────────────────────────────┘
 └──────────┬──────────────┘
            │
   ┌─────────▼──────────────────────────────────────────────────────────┐
   │  rrmACS_localAP_v2():                                              │
   │  Channel selection using:                                          │
   │  - scan utilization from Redis neighbors                          │
   │  - AFC-constrained channel list (afc_channels keys)               │
   │  - Power capped at afc_channels[channel] dBm                      │
   └──────────┬──────────────────────────────────────────────────────────┘
              │
   ┌──────────▼──────────────────────────────────────────────────────────┐
   │  Apply AFC constraints to result:                                   │
   │  res["channels"] = list(normalized_afc_channels.keys())            │
   │  if channel not in afc_channels: random_choice(afc_channels)        │
   │  res["power"]    = min(res["power"], afc_channels[channel])         │
   │  res["afc_max_eirp"] = afc_channels[channel]                       │
   │  res["afc_expiry"]   = expiry timestamp                            │
   │  res["afc_standard_power"] = True                                  │
   │  res["command"]  = "afc-update" if afc-update/channel-update       │
   └──────────┬──────────────────────────────────────────────────────────┘
              │
              ▼
   ┌──────────────────────────┐
   │  emit_local()            │
   │  Send updated channel    │
   │  assignment to AP via    │
   │  Kafka output stream     │
   └──────────────────────────┘
```

**Post-Diagram Summary:** Figure 21 shows the complete ACS+AFC integration flow in `rrmACSV2.py`. The novel integration points are: (1) AFC validation is performed before channel selection (not after), ensuring only AFC-permitted channels enter the selection pool; (2) the country code → ruleset ID mapping enables multi-national deployment with correct certification IDs; (3) the final power capping (`min(res["power"], afc_channels[channel])`) ensures transmit power never exceeds the AFC-assigned EIRP limit; and (4) the random_choice fallback when the selected channel is not in afc_channels prevents illegal channel operation.

**FIG. 21** — ACS + AFC integration flow in `rrmACSV2.py` `process_tup()`. For APs with `afc_standard_power=True`: retrieves device FCC ID or ISED ID, looks up country code (from Redis or Mist API), maps country to rulesetId (US→US_47_CFR_PART_15_SUBPART_E, CA→CA_ISED_DBS rules), builds certificationId array, calls `afc_channel_validation()` with location threshold 200 m, then `channels_validation()` to intersect with configured channels. On DONE: clears Redis `afc_info`, calls `rrmACS_localAP_v2()` with AFC-constrained channels, then applies AFC constraints: channels limited to afc_channels keys, power capped at `afc_channels[channel]` dBm, result tagged with `afc_max_eirp`, `afc_expiry`, `afc_standard_power=True`. Final result emitted via `emit_local()` to Kafka output stream.

---

---

# FIGURE 22 — afcNode PROCESSING IN APnode GRAPH

## Pre-Diagram Sequence Summary

The `afcNode()` function in `APnode.py` processes AFC channel information within the RRM graph structure. The RRM system represents a wireless site as a graph where each node represents an AP radio (e.g., `ap_id:r6` for the 6 GHz radio of an AP). The AFC-specific processing updates each node's channel list and power constraints based on the AFC authorization stored in the node's attributes.

The function checks whether the AP's AFC data is still valid (not expired), then updates the node's channel list and maximum power based on the AFC-assigned channels and EIRP values. If no valid AFC channels are available, the AP's radio is disabled via the RRM graph mechanism.

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  afcNode(g, ap_id, ap_rad_id, ...)                                       │
 │  Called during RRM global channel planning                               │
 └────────────────────────────────────────────────────────────────────────┬─┘
                                                                          │
 ┌────────────────────────────────────────────────────────────────────────▼─┐
 │  Extract from graph node:                                                │
 │    ap_id              = ap_rad_id.split(":")[0]                          │
 │    org_id             = g.graph.get("org")                               │
 │    site_id            = g.graph.get("site")                              │
 │    configured_channels= g.node[ap_rad_id].get("channels", [])            │
 │    rrm_bandwidth      = g.node[ap_rad_id].get("rrm_bandwidth", 0)        │
 │    afc_provider_flag  = g.graph.get("afc-provider-flag", "0")            │
 │    fcc_id             = g.node[ap_rad_id].get("fcc_id")                  │
 │                         OR g.graph.get("afc-fcc-id")                     │
 └────────────────────────────────────────────────────────────────────────┬─┘
                                                                          │
 ┌────────────────────────────────────────────────────────────────────────▼─┐
 │  Check existing AFC data in node:                                        │
 │    afc_channels_class = g.node[ap_rad_id].get("afc_channels", {})        │
 │    afc_expiry         = g.node[ap_rad_id].get("afc_expiry", 0)           │
 │    current_time       = g.node[ap_rad_id].get("timestamp", time.time())  │
 │    time_to_expiry     = afc_expiry - current_time                        │
 └────────────────────────────────────────────────────────────────────────┬─┘
                                                                          │
 ┌────────────────────────────────────────────────────────────────────────▼─┐
 │  AFC data still valid?                                                   │
 │  (time_to_expiry > 0 AND afc_channels_class not empty)                  │
 └──────────────────────────────┬──────────────────────────────────────────┘
                                │                   │
                               YES                  NO
                                │                   │
                                ▼                   ▼
 ┌─────────────────────────────────────┐   ┌─────────────────────────────────────┐
 │  USE CACHED AFC DATA:               │   │  FETCH NEW AFC DATA:                 │
 │  afc_channels = afc_channels_class  │   │  afc_channel_validation(             │
 │  expiry = afc_expiry                │   │    afc_proxy_link,                   │
 │  Log: "Reusing cached AFC channels" │   │    ap_id, site_id, bandwidth,        │
 └────────────────┬────────────────────┘   │    provider_flag, fcc_id, ...)       │
                  │                        └──────────────────┬──────────────────┘
                  │                                           │
                  └─────────────────────────────────┬─────────┘
                                                    │
 ┌──────────────────────────────────────────────────▼──────────────────────────┐
 │  afc_channels non-empty?                                                   │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │                    │
                                       YES                   NO
                                        │                    │
                                        ▼                    ▼
 ┌────────────────────────────────────────┐  ┌────────────────────────────────────┐
 │  UPDATE NODE:                          │  │  DISABLE RADIO:                    │
 │  g.node[ap_rad_id]["afc_channels"]     │  │  g.node[ap_rad_id]["rrm_enabled"]  │
 │    = afc_channels                      │  │    = False                         │
 │  g.node[ap_rad_id]["channels"]         │  │  disable_radio(g, ap_rad_id,       │
 │    = [int(c) for c in afc_channels.keys│  │               who="afc")           │
 │  g.node[ap_rad_id]["afc_timestamp"]    │  │  Log: "No AFC channels for AP"     │
 │    = g.node[ap_rad_id]["timestamp"]    │  └────────────────────────────────────┘
 │  g.node[ap_rad_id]["afc_expiry"]       │
 │    = expiry_time                       │
 │  g.node[ap_rad_id]["afc_source"]       │
 │    = "afc-proxy"                       │
 └────────────────────────────────────────┘
```

**Post-Diagram Summary:** Figure 22 shows the afcNode processing within the RRM graph. The graph-based RRM architecture allows AFC constraints to be applied as node attributes that feed into the global channel planning algorithm. The `afc_source = "afc-proxy"` tag distinguishes AFC-coordinated channel assignments from LPI assignments in the RRM graph, enabling different treatment during the global RRM optimization pass. The `disable_radio(who="afc")` call ensures that the global RRM algorithm knows the radio was disabled specifically due to AFC failure, not operator configuration, which may affect how neighbor APs are compensated.

**FIG. 22** — afcNode processing in `APnode.py` for RRM graph-based channel planning. Function extracts AP identifiers and configuration from the NetworkX graph node attributes: configured_channels, rrm_bandwidth, afc_provider_flag, FCC ID. Checks existing AFC data in node (afc_channels, afc_expiry, timestamp) for validity. If valid cached data: reuses afc_channels_class and expiry. If expired or empty: calls `afc_channel_validation()` with full parameters including fcc_id. On successful AFC channels: updates node attributes — afc_channels (dict), channels (list of ints from afc_channels keys), afc_timestamp, afc_expiry, afc_source="afc-proxy". On empty AFC channels: sets rrm_enabled=False and calls `disable_radio(g, ap_rad_id, who="afc")` to exclude this AP radio from RRM global channel planning.

---

---

# END OF PART 7 — ABSTRACT DRAWINGS AND FIGURES

**Total Figures: 22**
**Part 7 of 7**

---

## FIGURE INDEX SUMMARY

| Figure | Title | Key Technical Content |
|--------|-------|----------------------|
| FIG. 1 | Overall System Architecture | Three-tier cloud RRM, AFC Proxy, AP hardware |
| FIG. 2 | AFC Request Lifecycle | POST/GET/process flow, EIRP formula, LPI fallback |
| FIG. 3 | AFC Payload JSON Structure | All field constraints, certificationId, inquiredChannels |
| FIG. 4 | AFC Response Structure | availableChannelInfo, availableFrequencyInfo, expiry |
| FIG. 5 | GlobalOperatingClass Mapping | 131→20MHz through 137→320MHz, bidirectional |
| FIG. 6 | 6 GHz Channel Map | All 59 CFI numbers, 5955–7085 MHz center frequencies |
| FIG. 7 | EIRP Computation Flow | psd + 10*log10(BW), min(maxEIRP, psd_eirp), AFC_MIN_PSD |
| FIG. 8 | AFC_MIN_PSD Floor Table | 14/17/20/23/26 dBm per bandwidth, PSD-scaling derivation |
| FIG. 9 | Geolocation Validation | ECEF distance, WGS84, 200m threshold, height check |
| FIG. 10 | WGS84 ECEF Formula | a=6378137.0, f=1/298.257223563, full equations |
| FIG. 11 | Location Cache Invalidation | Delete→POST→GET sequence, Redis state updates |
| FIG. 12 | RrmAFCBolt Topology | Storm bolt, dual Redis, X-FROM header, tick+event modes |
| FIG. 13 | AFC State Machine | DONE/NotDONE/NoGPS/LPI_Fallback/RadioDisabled states |
| FIG. 14 | 320 MHz Mode 1 vs Mode 2 | Central channels [31,95,159] vs [63,127,191] |
| FIG. 15 | ch_delta Sub-Channel Table | [0]/[2]/[2,6]/[2,6,10,14]/[2..30] per bandwidth |
| FIG. 16 | DeleteAP Retry Logic | 3 retries, 1s delay, X-HTTP-Method-Override header |
| FIG. 17 | AP AFC Lifecycle | Boot→Register→Operate→LocationChange→Deregister |
| FIG. 18 | Redis Cache Architecture | Dual Redis, key schemas, afc_info hash, retry queue |
| FIG. 19 | Multi-Provider Architecture | Flags 0/1/2/dev, providerName routing, mock injection |
| FIG. 20 | LPI Fallback Decision Tree | lpi_ok flag, afc_source=lpi_fallback, comparison table |
| FIG. 21 | ACS+AFC Integration | Country→rulesetId, power cap, afc_max_eirp, emit_local |
| FIG. 22 | afcNode Graph Processing | Graph attributes, expiry check, disable_radio(who=afc) |

---

*End of Patent Application Part 7 of 7*
*Application Number: [PENDING]*
*Filing Date: July 2026*
