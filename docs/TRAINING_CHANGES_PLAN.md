# Training Changes Plan - February 2026

Based on WhatsApp conversation with Esther De Vries (13 Feb 2026).

## New Trainings to Create

### Ademcirkel 13 maart
- Type: Breath A'dam (4), Location: Grote Trainingsruimte (1)
- Event: 13 Mar 2026 09:30–12:15, max 14
- Trainers: Brendan Bank (1), Esther de Vries (10), Jaron Salem (11)
- Inloop 09:00, Amsterdam, Eigen bijdrage 15 euro

### Ademcirkel 8 mei
- Type: Breath A'dam (4), Location: Grote Trainingsruimte (1)
- Event: 8 May 2026 09:30–12:15, max 16
- Trainers: Brendan Bank (1), Esther de Vries (10), Jaron Salem (11)

### Bonding 17 Apr 2026
- Type: Bonding (1), Location: Grote Trainingsruimte (1)
- Event: 17 Apr 2026 07:30–13:30, max 14
- Trainers: Brendan Bank (1), Hans van Wechem (9), Jaron Salem (11)

## Participant Moves (all via API for proper notifications)

### Training 31 (Bonding 13 Mar) → Ademcirkel 13 maart
- De-enroll 14 participants → cancellation emails
- Enroll into new Ademcirkel 13 maart → confirmation emails
- Participants: Ine Van Wesel (33), John Bakhtali (35), Fleur Thomese (7), Wouter Van der Wolk (41), Agnes Kleinen Hammans (55), Marit Meijeren (32), Giovanni Lo Galbo (47), Jasper Lowik (89), Romke Vogelzang Kuipers (93), Bibiane Van Velthoven (91), Patrycja Pyzalska (79), Natascha Minnebo (92), Koen Doodeman (101), Izzy Van Unen (104, waitlist-invited)

### Training 37 (Bonding 8 May) → Ademcirkel 8 mei
- De-enroll 17 participants → cancellation emails
- Enroll into new Ademcirkel 8 mei → confirmation emails
- Participants: Ine Van Wesel (33), Rob Megens (26), Simone de Schipper (28), John Bakhtali (35), Fleur Thomese (7), Wouter Van der Wolk (41), Agnes Kleinen Hammans (55), Marit Meijeren (32), Joosje Holstein (53), Ilja Immanuel Groenewegen (65), Giovanni Lo Galbo (47), Neil Tallantire (46), Bibiane Van Velthoven (91), Patrycja Pyzalska (79), Emily ter Steeg (76), Koen Doodeman (101), Annabel Stoker (23, waitlist)

### Training 36 (Bonding 24 Apr) → Bonding 17 Apr
- De-enroll 18 participants → cancellation emails
- Enroll into new Bonding 17 Apr → confirmation emails
- Participants: Ine Van Wesel (33), Brendan Bank (1), Simone de Schipper (28), John Bakhtali (35), Fleur Thomese (7), Wouter Van der Wolk (41), Agnes Kleinen Hammans (55), Rob Megens (26), Marit Meijeren (32), Joosje Holstein (53), Giovanni Lo Galbo (47), Annemieke Krul (74), Melissa Diaz (34), Bibiane Van Velthoven (91), Emily ter Steeg (76), Romke Vogelzang Kuipers (93), Isis Huisman (31, waitlist), Koen Doodeman (101, waitlist)

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
