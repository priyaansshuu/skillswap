# Demo accounts that can both teach and learn

This list covers the 20 preconfigured synthetic members added to the original 15 accounts. There are also [20 blank accounts](BLANK_ACCOUNTS.md) you can fill yourself, bringing the current local demo to 55 accounts. Each member listed below has one login, two offered skills, two learning goals, dated online/in-person availability, and 120 starter minutes with the current configuration. Roles are chosen by the exchange, not by the account.

New accounts use the existing DEMO_PASSWORD configured in the local ignored `.env`. Passwords are not included here or in the downloadable archive. Existing account passwords are preserved on subsequent seed runs.

| Account | Can teach | Wants to learn |
|---|---|---|
| member01@example.com | JavaScript, React | Mathematics, Python |
| member02@example.com | JavaScript, Python | English, Mathematics |
| member03@example.com | Mathematics, Python | English, Guitar |
| member04@example.com | English, Mathematics | Guitar, React |
| member05@example.com | English, Guitar | JavaScript, React |
| member06@example.com | Guitar, React | JavaScript, Python |
| member07@example.com | JavaScript, React | Mathematics, Python |
| member08@example.com | JavaScript, Python | English, Mathematics |
| member09@example.com | Mathematics, Python | English, Guitar |
| member10@example.com | English, Mathematics | Guitar, React |
| member11@example.com | English, Guitar | JavaScript, React |
| member12@example.com | Guitar, React | JavaScript, Python |
| member13@example.com | JavaScript, React | Mathematics, Python |
| member14@example.com | JavaScript, Python | English, Mathematics |
| member15@example.com | Mathematics, Python | English, Guitar |
| member16@example.com | English, Mathematics | Guitar, React |
| member17@example.com | English, Guitar | JavaScript, React |
| member18@example.com | Guitar, React | JavaScript, Python |
| member19@example.com | JavaScript, React | Mathematics, Python |
| member20@example.com | JavaScript, Python | English, Mathematics |

Current additional-member availability starts 15 October 2026 at 15:30 IST. Users can add new intervals through their own availability endpoint.

Recreate the same members with `python -m app.cli seed --extra-members 20`. Increasing the target count adds more members; repeating it does not duplicate accounts or starter grants.
