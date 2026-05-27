# Stage 14 — Completeness passes

## Purpose

Close the four functional gaps identified between the doc and the build after Phase 2:

1. **SIM swap workflow** — backend endpoint that swaps a customer's SIM, marks
   the old one `swapped`, and audits the operation (`SIM_SWAP_REQUEST` event,
   per docs §12.4).
2. **Device registry** — distinct from the existing FCM `device-token`. Adds a
   logical device record (per docs §10.1 "Device registration") so login flows
   can recognise known devices and surface a `deviceId` field in audit events
   (per docs §12.1 LOGIN_SUCCESS example).
3. **Usage export — mobile UI** — backend `/api/usage/export?format=csv|json`
   already exists; the Android Usage screen gets a "Download CSV" action that
   calls it and opens the file via FileProvider.
4. **Attachments — mobile UI** — backend
   `POST /api/support/tickets/{ticketId}/attachments` already accepts multipart
   uploads; the Android TicketDetail screen gets a file picker + attachments
   list.

## Inputs

- `docs/VulnMNO.md` §10.1, §10.6, §10.7, §12.1, §12.4, §13.1.
- Phase 1 build at `stages/04_api_build/output/backend/`.
- Phase 1 mobile app at `stages/06_mobile_build/output/android/`.
- Phase 2 admin/gateway extensions (no changes here — additive only).

## Outputs

- New backend module: `app/models/device.py` (`CustomerDevice`), router
  endpoints in `app/routers/auth.py` (device registry) and
  `app/routers/customers.py` (sim-swap).
- New Alembic migration `0003_completeness.py`.
- New Android pieces: `UsageScreen` export action, `TicketDetailScreen`
  attachments section + upload picker.

## Out of scope

- Trusted-device challenges (RBAC + step-up auth would be a Phase 3 concern).
- Storage backends other than local filesystem for attachments.
- ICCID validation against a real SIM provisioning system.
