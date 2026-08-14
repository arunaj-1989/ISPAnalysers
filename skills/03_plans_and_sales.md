# Skill 03: Plans, Upgrades & Sales Enquiries

## Issue Code Index
- `NEW_CONNECTION`
- `PLAN_DETAILS_ENQUIRY`
- `PLAN_UPGRADE`
- `SPEED_UPGRADE`

---

### 1. NEW_CONNECTION
- **Keywords:** "new connection booking", "broadband enquiry", "internet availability", "new broadband connection", "new connection", "interested in an internet plan", "internet plan for TV", "internet plan for OTT", "TV and OTT plan", "broadband plan for TV and OTT"
- **Routing note:** A customer asking about getting an internet/broadband plan for TV, OTT, or home use is a new sales/connection enquiry when there is no clear indication that they already have an active connection. Route these requests to `NEW_CONNECTION`, not `INTERNET_ISSUE`.
- **SOP:**
  1. Collect full installation address and pincode.
  2. Check feeder box/DP coverage in area.
  3. Pass qualified lead to local sales team.
- **Recommended next step:** Do not dispatch a repair or connectivity technician for a new sales enquiry. Verify availability and route the qualified lead to sales; schedule field work only after a new installation order is approved.

### 2. PLAN_DETAILS_ENQUIRY
- **Keywords:** "available packages", "tariff details", "plan options", "current offers"
- **SOP:**
  1. Share available unlimited fiber plans (50Mbps, 100Mbps, 300Mbps).
  2. Explain OTT bundle additions or annual discounts if applicable.

### 3. PLAN_UPGRADE
- **Keywords:** "upgrade pack", "change plan", "upgrade subscription", "change internet plan"
- **SOP:**
  1. Confirm requested plan code and price difference.
  2. Clarify if upgrade takes effect immediately or on next bill cycle.
  3. Process upgrade in CRM.

### 4. SPEED_UPGRADE
- **Keywords:** "increase speed only", "increase broadband speed", "upgrade from 50Mbps to 100Mbps"
- **SOP:**
  1. Verify if existing router supports target speed (e.g., Dual-band Gigabit router for >100Mbps).
  2. If compatible, upgrade speed profile immediately. If not, trigger `DEVICE_UPGRADE_REQUEST`.