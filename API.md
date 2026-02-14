# Bcource Admin API

REST API for training and enrollment management.

- **Base URL:** `/admin-api`
- **Swagger UI:** `/admin-api/docs`

## Authentication

### Get a Token

```
POST /admin-api/auth/token
```

```json
{"email": "admin@example.com", "password": "password"}
```

**Response:**
```json
{"token": "eyJhbG...", "expires_in": 86400}
```

Requirements: user must be active, have `db-admin` role, and have 2FA enabled.

### Using the Token

Include in all subsequent requests:

```
Authorization: Bearer <token>
```

JWT tokens skip the 2FA check (token proves identity via SECRET_KEY signature). Session-based auth still requires 2FA.

---

## Endpoints

### Training Types (read-only)

#### List training types

```
GET /admin-api/training-types/
```

```json
[{"id": 1, "name": "Bonding", "description": "..."}]
```

### Locations (read-only)

#### List locations

```
GET /admin-api/locations/
```

```json
[{"id": 1, "name": "Grote Trainingsruimte", "street": "...", "house_number": "...", "postal_code": "...", "city": "Amsterdam", "country": "Netherlands"}]
```

### Students

#### Search students

```
GET /admin-api/students/?q=giovanni
```

Search by name or email (max 50 results, case-insensitive).

```json
[{"id": 47, "fullname": "Giovanni Lo Galbo", "email": "...", "phone_number": "...", "studenttype": "regular", "studentstatus": "active"}]
```

---

### Trainings

#### List trainings

```
GET /admin-api/trainings/?active=true&trainingtype_id=1&q=bonding
```

All query parameters are optional. Results ordered by ID descending.

```json
[{
  "id": 10, "name": "Bonding 13 Mar 2026", "active": true,
  "max_participants": 14, "trainingtype": "Bonding", "trainingtype_id": 1,
  "enrollment_count": 12, "waitlist_count": 2, "event_count": 1
}]
```

`enrollment_count` = enrolled + waitlist-invited (both count against capacity).

#### Get training detail

```
GET /admin-api/trainings/{id}
```

```json
{
  "id": 10, "name": "Bonding 13 Mar 2026", "active": true,
  "max_participants": 14, "apply_policies": true, "trainingtype_id": 1, "trainingtype": "Bonding",
  "trainers": [{"id": 1, "name": "Brendan Bank", "email": "..."}],
  "events": [{"id": 42, "start_time": "2026-03-13T07:30:00", "end_time": "2026-03-13T13:30:00", "location_id": 1, "location_name": "Grote Trainingsruimte", "training_id": 10}],
  "enrollment_count": 12, "waitlist_count": 2, "spots_available": 2
}
```

#### Create training

```
POST /admin-api/trainings/
```

```json
{
  "name": "Bonding 17 Apr 2026",
  "trainingtype_id": 1,
  "max_participants": 14,
  "active": true,
  "apply_policies": true,
  "trainer_ids": [1, 9, 11],
  "events": [{"start_time": "2026-04-17T07:30:00", "end_time": "2026-04-17T13:30:00", "location_id": 1}]
}
```

Returns `201` with `TrainingDetail`. `trainer_ids` and `events` are optional.

#### Update training

```
PUT /admin-api/trainings/{id}
```

```json
{
  "name": "Updated Name",
  "max_participants": 20,
  "trainer_ids": [1, 9]
}
```

All fields optional — only included fields are updated. `trainer_ids` replaces all current assignments.

#### Deactivate training

```
PATCH /admin-api/trainings/{id}/deactivate
```

Sets `active=false`. Does NOT de-enroll students or cancel events.

---

### Training Events

#### List events

```
GET /admin-api/trainings/{training_id}/events
```

Ordered by `start_time`.

#### Create event

```
POST /admin-api/trainings/{training_id}/events
```

```json
{"start_time": "2026-04-17T07:30:00", "end_time": "2026-04-17T13:30:00", "location_id": 1}
```

Returns `201`.

#### Update event

```
PUT /admin-api/trainings/{training_id}/events/{event_id}
```

Same body as create.

#### Delete event

```
DELETE /admin-api/trainings/{training_id}/events/{event_id}
```

Returns `204`.

---

### Enrollments

#### List enrollments

```
GET /admin-api/trainings/{training_id}/enrollments?status=enrolled
```

`status` filter is optional. Ordered by `enrole_date`.

```json
[{
  "student_id": 47, "training_id": 10,
  "student_name": "Giovanni Lo Galbo", "student_email": "...",
  "status": "enrolled", "enrole_date": "2026-02-10T14:30:00",
  "invite_date": null, "paid": false
}]
```

**Status values:** `enrolled`, `waitlist`, `waitlist-invited`, `waitlist-invite-expired`, `waitlist-declined`

#### Enroll student

```
POST /admin-api/trainings/{training_id}/enrollments
```

```json
{"student_id": 47}
```

Returns `201`. Uses standard enrollment flow:
- Spots available → `enrolled` (sends confirmation email + trainer notification)
- Training full → `waitlist` (sends waitlist email + trainer notification)
- Booking policies are NOT enforced (admin bypass)
- Student must be active, training must not have started

Returns `409` if student already enrolled.

#### Get enrollment

```
GET /admin-api/trainings/{training_id}/enrollments/{student_id}
```

#### Remove enrollment

```
DELETE /admin-api/trainings/{training_id}/enrollments/{student_id}
```

Returns `204`. Sends de-enrollment notifications. Does NOT cascade waitlist invitations (admin control — use `invite` action manually).

#### Enrollment actions

```
POST /admin-api/trainings/{training_id}/enrollments/{student_id}/action
```

```json
{"action": "invite"}
```

| Action | From | To | Notes |
|--------|------|----|-------|
| `invite` | `waitlist` | `waitlist-invited` | Checks capacity. Sends email + SMS + trainer notification. |
| `deinvite` | `waitlist-invited` | `waitlist-invite-expired` | Sends expiry notification. |
| `return-to-waitlist` | `waitlist-invited` | `waitlist` | Silent, no notifications. Keeps queue position. |
| `force-enroll` | `waitlist` | `enrolled` | Bypasses capacity. Sends confirmation. |
| `decline` | `waitlist-invited` | `waitlist-declined` | Cascades: auto-invites next eligible waitlisted student(s). |
| `toggle-paid` | any | any | Flips the `paid` flag. |

**Response:**
```json
{"student_id": 47, "training_id": 10, "status": "waitlist-invited", "action": "invite"}
```

#### Bulk move

```
POST /admin-api/trainings/{source_training_id}/enrollments/bulk-move
```

```json
{
  "student_ids": [33, 35, 7, 41],
  "target_training_id": 92,
  "operation": "move",
  "override_status": "enrolled"
}
```

| Field | Description |
|-------|-------------|
| `student_ids` | List of student IDs to move/copy |
| `target_training_id` | Destination training ID |
| `operation` | `"move"` (deletes from source) or `"copy"` (keeps source) |
| `override_status` | Optional: force all to this status instead of preserving original |

**Response:**
```json
{"moved": [33, 35, 7], "skipped": [41], "errors": []}
```

- `skipped`: already enrolled in target (duplicate prevention)
- No notifications sent, no policy checks — direct DB operation
- Preserves `paid` flag

---

## Error Responses

```json
{"errors": {"detail": "Error message"}}
```

| Code | Meaning |
|------|---------|
| `400` | Validation error |
| `401` | Missing/invalid auth or expired token |
| `403` | Account inactive, missing 2FA, or missing db-admin role |
| `404` | Resource not found |
| `409` | Conflict (duplicate enrollment, no capacity) |

## Practice Scoping

All data is automatically filtered by the authenticated user's default practice. Only trainings, locations, training types, and students from that practice are visible.
