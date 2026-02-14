# Training Changes Plan - February 2026

Based on WhatsApp conversation with Trainer A (13 Feb 2026).

## New Trainings to Create

### Ademcirkel 13 maart
- Type: Breath A'dam (4), Location: Grote Trainingsruimte (1)
- Event: 13 Mar 2026 09:30–12:15, max 14
- Trainers: John Doe (1), Trainer A (10), Trainer B (11)
- Inloop 09:00, Amsterdam, Eigen bijdrage 15 euro

### Ademcirkel 8 mei
- Type: Breath A'dam (4), Location: Grote Trainingsruimte (1)
- Event: 8 May 2026 09:30–12:15, max 16
- Trainers: John Doe (1), Trainer A (10), Trainer B (11)

### Bonding 17 Apr 2026
- Type: Bonding (1), Location: Grote Trainingsruimte (1)
- Event: 17 Apr 2026 07:30–13:30, max 14
- Trainers: John Doe (1), Trainer C (9), Trainer B (11)

## Participant Moves (all via API for proper notifications)

### Training 31 (Bonding 13 Mar) → Ademcirkel 13 maart
- De-enroll 14 participants → cancellation emails
- Enroll into new Ademcirkel 13 maart → confirmation emails
- Participants: Student 1 (33), Student 3 (35), Student 4 (7), Student 5 (41), Student 6 (55), Student 8 (32), Jane Smith (47), Student 17 (89), Student 14 (93), Student 12 (91), Student 23 (79), Student 18 (92), Student 16 (101), Student 19 (104, waitlist-invited)

### Training 37 (Bonding 8 May) → Ademcirkel 8 mei
- De-enroll 17 participants → cancellation emails
- Enroll into new Ademcirkel 8 mei → confirmation emails
- Participants: Student 1 (33), Student 7 (26), Student 2 (28), Student 3 (35), Student 4 (7), Student 5 (41), Student 6 (55), Student 8 (32), Student 9 (53), Student 20 (65), Jane Smith (47), Student 21 (46), Student 12 (91), Student 23 (79), Student 13 (76), Student 16 (101), Student 22 (23, waitlist)

### Training 36 (Bonding 24 Apr) → Bonding 17 Apr
- De-enroll 18 participants → cancellation emails
- Enroll into new Bonding 17 Apr → confirmation emails
- Participants: Student 1 (33), John Doe (1), Student 2 (28), Student 3 (35), Student 4 (7), Student 5 (41), Student 6 (55), Student 7 (26), Student 8 (32), Student 9 (53), Jane Smith (47), Student 10 (74), Student 11 (34), Student 12 (91), Student 13 (76), Student 14 (93), Student 15 (31, waitlist), Student 16 (101, waitlist)

## Post-Move: Reset All Enrollment Statuses
- After bulk-move, set all enrollments in new trainings to `enrolled` status
- This ensures waitlisted/invited students from old trainings start fresh as enrolled

## Deactivate Old Trainings
- Training 31 (Bonding 13 Mar)
- Training 36 (Bonding 24 Apr)
- Training 37 (Bonding 8 May)

## Prerequisite
- JWT auth for admin API (see separate implementation plan)

---
*Created: 14 Feb 2026*
