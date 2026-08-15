### `skills/01_technical_connectivity.md`

```markdown
# Skill 01: Technical & Connectivity Issues

## Issue Code Index
- `FIBER_CABLE_DAMAGED`
- `FIBER_CUT`
- `INTERNET_ISSUE`
- `LOSS_OF_SIGNAL`
- `OUTAGE_REPORT`
- `ROUTER_ISSUE`
- `SITE_NOT_WORKING`
- `SLOW_SPEED`
- `WIFI_DISCONNECTING`

---

### 1. FIBER_CABLE_DAMAGED
- **Keywords:** "pole cable loose", "wire damaged outside", "damaged fiber cable", "cable hanging"
- **SOP:**
  1. Confirm exact physical location of the damage (e.g., near pole, main gate, street line).
  2. Warn customer not to bend or touch exposed optical fibers.
  3. Create a Field Service Ticket marked high priority for Cable Repair Team.

### 2. FIBER_CUT
- **Keywords:** "digging line cut", "fiber cut", "rain damage", "cut cable"
- **Classification:** `Connectivity Issue` (`FIBER_CUT`); route to the Connectivity and field-support specialist.
- **SOP:**
  1. Verify if LOS light on ONT router is blinking RED.
  2. Cross-check with network operations for major line cuts in the area.
  3. Dispatch field splicer technician.

### 3. INTERNET_ISSUE
- **Keywords:** "no internet access", "net off", "internet not working", "connection down"
- **SOP:**
  1. Check router Power, Internet, and LAN lights.
  2. Ask customer to power-cycle router (30 seconds off, then on).
  3. If power-cycle fails and account is active, log L1 Technical Ticket.

### 4. LOSS_OF_SIGNAL
- **Keywords:** "LOS light red blinking", "red light on router", "LOS red light"
- **SOP:**
  1. Confirm optical signal is not reaching ONT modem.
  2. Check patch cord connection between wall socket and router.
  3. If intact, log an immediate On-site Optical Technician Visit.

### 5. OUTAGE_REPORT
- **Keywords:** "entire street no connection", "mass down", "area outage", "neighborhood internet down"
- **SOP:**
  1. Verify active outage reports for customer node/OLT.
  2. If confirmed, inform customer of the estimated restoration time (ETA).
  3. Link customer account to master outage ticket.

### 6. ROUTER_ISSUE
- **Keywords:** "router burning", "power adapter problem", "router overheating", "router lights not working"
- **SOP:**
  1. Check power adapter and wall outlet functional status.
  2. Check hardware lights. If power light is dead/flickering, flag for Router Hardware Replacement.

### 7. SITE_NOT_WORKING
- **Keywords:** "particular site not opening", "DNS problem", "website not loading", "app not working"
- **SOP:**
  1. Check if other websites load normally.
  2. Guide customer to change DNS settings (e.g., 8.8.8.8) or clear browser cache.
  3. Check if domain is blocked or facing server issues.

### 8. SLOW_SPEED
- **Keywords:** "buffering continuously", "slow browsing", "slow internet", "low speed"
- **SOP:**
  1. Check if high bandwidth apps/downloads are active on other connected devices.
  2. Instruct customer to perform speed test via Ethernet cable near the router.
  3. If speed is below 80% of subscribed plan, escalate for line attenuation check.

### 9. WIFI_DISCONNECTING
- **Keywords:** "Wi-Fi dropping frequently", "Wi-Fi disconnecting", "wireless signal drops"
- **SOP:**
  1. Check router distance and physical barriers (concrete walls, metal sheets).
  2. Recommend connecting to 5GHz band for speed or 2.4GHz for distance.
  3. Change Wi-Fi channel if interferences are high.