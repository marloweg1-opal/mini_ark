# Scope And Project Bleed Audit

## Purpose

This note keeps Mini ARK aligned with Project ARK and prevents adjacent projects from taking over the cockpit.

## Parent Scope

Project ARK is the parent continuity system.

Mini ARK is the local tool that helps ARK scan, classify, report, review handoffs, prepare proposals, and apply approved reversible operations.

## Module Scope

CareBloomOS is a flagship subsystem under ARK. It deserves first-class indexing and care, but it must remain one module lane among other ARK lanes.

Known module lanes:

- Project ARK
- Mini ARK
- Ark OS
- CareBloomOS
- HEXSEED
- Welfare Witchcraft
- media organization and cleanup operations
- Avatar_Ark
- Archmagus_Ark
- Accountant_Ark

## Project Bleed Found

CareBloomOS has dominated recent Project ARK control-folder scripts and reports. That makes sense historically because it has had active Rainmeter and Wallpaper Engine work, but it creates a naming and priority risk.

Observed bleed patterns:

- Project ARK scripts include multiple CareBloom-specific runtime scripts.
- The latest earlier status framing drifted toward CareBloomOS as the MVP.
- Some ARK handoff text points future work toward CareBloom source mapping as the default next mission.
- Mini ARK has handoff fixtures and review packets that include CareBloom/Cloverstone material.

## Corrective Rule

Every Mini ARK status surface should answer in this order:

1. What is the state of Mini ARK itself?
2. What is the state of parent Project ARK?
3. Which module or persona is in focus?
4. What is safe to do next?

CareBloomOS can be focus item 3, never item 1 or 2 unless the user explicitly asks for CareBloomOS.

## Current Inconsistencies To Address

- ARK handoff should be refreshed so the current next mission is Mini ARK stabilization, not CareBloom source mapping.
- Mini ARK should have a cockpit command or launcher visible from `ark.py`.
- GitHub archival needs an ignore policy before any repository initialization, because `ark.sqlite` and backup SQLite files are large local state.
- Handoff review count should be reduced from 6 by classifying each review JSON as accepted, superseded, or pending user decision.

## No-Go List Without Approval

- Do not apply pending proposals.
- Do not quarantine empty folders.
- Do not move CareBloomOS runtime files.
- Do not initialize or push a GitHub repository.
- Do not commit SQLite ledgers or local backup databases.
- Do not alter system app settings.
