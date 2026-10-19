# Modern Munim user workspace mapping plan

Date: 2026-10-14. Status: **proposal for operator review**. Nothing in this document has been applied.

No roles were changed. No workspace was created. No migration was edited. `seed_data` was not run. The host database was read with `default_transaction_read_only = on`. Spring was not started. Port 8080 was not changed.

## Verdict

**OPERATOR DECISION REQUIRED** before any `workspace_id` migration.

`shuklapratham758@gmail.com` is **not** one of the six host accounts. Neither admin can be shown to own a founder workspace. All six accounts should stay **unassigned** until the operator confirms each purpose. Do not create a workspace for every existing account.

## Facts

Read-only query of host `localhost:5432`, database `marketplace_db`, Alembic `008_user_store_type`, on 2026-10-14.

| Fact | Result |
|---|---|
| User rows | 6 |
| `admin` | 2 |
| `customer` | 4 |
| `manager` | 0 |
| Email equal to `shuklapratham758@gmail.com` | 0 |
| `store_name` / `store_type` | null on all 6 |
| `mfa_enabled` | false on all 6 |
| `mfa_secret` present | no on all 6 |
| `email_otps` rows | 0 |
| Products, vendors, vendor products, expenses, purchase orders, purchase-order items, stock transactions, orders, order items, inventory snapshots | 0 |
| Demand forecasts, stockout predictions, restocking recommendations, dead-stock detections, AI alerts, job runs, vendor performance metrics | 0 |

Passwords, password hashes, MFA secrets, OTP hashes, and tokens were not selected.

`users` columns in code and in revision `008` are `id`, `email`, `password_hash`, `role` (`customer`, `admin`, `manager`), `mfa_enabled`, `mfa_secret`, `store_name`, `store_type`, `created_at`. There is no `workspace_id`. `store_name` is nullable and not unique. `orders.user_id` is the only business foreign key to `users`, and `orders` is empty, so no order needs an owner decision.

Authorization today is global admin, not a workspace. `get_current_admin` checks `role == "admin"`. Spring uses `hasRole("ADMIN")` on business prefixes. Neither checks the founder email.

Commit `9cb755e` (“Add demo customer account abcd@fufu.com to seed data”) inserts that email as `UserRole.CUSTOMER` in `seed_data.py` at that revision. The current working-tree `seed_data.py` does not create users, and `main.py` does not call it. The other five emails do not appear in Git history. Whether user id 2 was inserted by that old seed was not proven from the row alone.

The staging Compose volume was not queried. This plan covers the host database only.

## Proposed mapping

Dispositions below are **proposals**. They are not executed changes.

| id | email | role | store_name | store_type | created_at (UTC) | Founder identity | Proposed disposition | Dedicated workspace now? |
|---|---|---|---|---|---|---|---|---|
| 1 | samle@marketplace.com | admin | null | null | 2026-02-27 17:48:04 | **Contradicted.** Address is not the founder email. | Leave the row unchanged and **unassigned**. Do not treat age or the admin role as founder ownership. | **No.** Create one only after the operator says what this account is for. |
| 2 | abcd@fufu.com | customer | null | null | 2026-07-18 14:39:48 | **Contradicted.** | Leave the row unchanged and **unassigned**. Historical seed named this email as a demo customer. That does not make it a store, and it is not the founder. Do not delete it in the migration. | **No.** |
| 3 | spring.customer@example.com | customer | null | null | 2026-08-10 23:19:44 | **Contradicted.** | Leave the row unchanged and **unassigned**. The address is not in the repository. Purpose is unknown. | **No.** |
| 4 | jwt.verify.customer@example.com | customer | null | null | 2026-08-10 23:44:54 | **Contradicted.** | Leave the row unchanged and **unassigned**. Purpose is unknown. The address text is not proof of who may delete it. | **No.** |
| 5 | jwt.verify.admin@example.com | admin | null | null | 2026-08-10 23:44:54 | **Contradicted.** | Leave the row unchanged and **unassigned**. Do not give this second admin the founder workspace. | **No.** Not until the operator says it is a real second store. |
| 6 | jwt.other.customer@example.com | customer | null | null | 2026-08-10 23:50:21 | **Contradicted.** | Leave the row unchanged and **unassigned**. Purpose is unknown. | **No.** |

MFA is off for every row. No OTP row exists for any of these emails.

## Decisions the operator must answer

1. **Which existing admin owns the founder workspace?**  
   **Proposal: neither.** The founder email is absent. Do not assign user 1 or user 5 because they are admins.  
   **OPERATOR DECISION REQUIRED** if the founder workspace should instead be a new account created later through the existing email, password, store, and OTP flow, still without seeding.

2. **What happens to the second admin (id 5, `jwt.verify.admin@example.com`)?**  
   **Proposal: keep the row, change nothing, assign no workspace.**  
   **OPERATOR DECISION REQUIRED** before anyone marks it as a real store, disables it, or removes it.

3. **What happens to each customer-role account (ids 2, 3, 4, and 6)?**  
   **Proposal: keep each row, change nothing, assign no workspace.** They are not confirmed stores. Customer role does not match the current admin-only sign-in path, and business routes reject non-admins. That is not a reason to delete them here.  
   **OPERATOR DECISION REQUIRED** separately for id 2 (named in old seed) and for ids 3, 4, and 6 (no source record).

4. **Should an account stay unassigned until its purpose is confirmed?**  
   **Proposal: yes, for all six.**

5. **Should a workspace be created for every existing account?**  
   **Proposal: no.** Create a workspace only after the operator confirms that account’s purpose. An empty workspace per row would invent tenants.

6. **Business-row ownership**  
   **No host business rows exist**, so none need an owner. Do not assign future rows by id order, creation time, role, or store name. If any catalog row appears before the migration runs, stop and map that row explicitly.

Commit `9cb755e` also wrote a demo password for `abcd@fufu.com` into old docs and seed output. The current `README.md` no longer contains that email. The password is not repeated here. **OPERATOR DECISION REQUIRED** on whether that account’s credential should be reset before the account is used again.

## Migration sequence after written approval

Do not start this sequence until the operator accepts or corrects the table above.

1. Take a new custom-format dump of `marketplace_db`. Do not overwrite the 2026-10-14 pre-`008` dump.
2. Add a new Alembic revision after `008_user_store_type`. Do not edit revisions `001` through `008`.
3. Create `workspaces` and add a **nullable** `workspace_id` on users and on business tables. Do not backfill the six users. Do not delete users, orders, or catalog rows. Null means unassigned.
4. Keep existing rows readable by primary key for operators, but application queries for a normal session must require a workspace id that matches the caller. An unassigned user must not see another workspace and must not fall through to a global catalog.
5. Enforce that on the server. A frontend email check is not sufficient. Founder demo authorization has to be a server-side rule on the founder workspace, applied only after that workspace exists. Do not implement it by renaming user 1 or user 5.
6. Because the host catalog is empty, there is no legacy business backfill. Staging volume rows, if they are still present, are outside this host plan and need their own decision.
7. Do not run the current `seed_data`. Replace it later with a manual founder-only seeder that tags demo rows, writes them only on the founder workspace, skips rows that already exist, and never deletes untagged data. Do not call it from application startup.
8. Rollback of that future revision is: restore the new dump if any assignment or seed was written. Downgrade that drops empty workspace columns is acceptable only while every `workspace_id` is still null and no demo rows were inserted. Do not downgrade `006`–`008` as part of this work. Those downgrades drop store columns and `email_otps`.

## Risks

- Assigning the founder workspace to user 1 or user 5 would attach later demo data to the wrong person. Evidence does not support either assignment.
- Deleting the four customer rows, or the second admin, is irreversible without a dump and is not part of this proposal.
- A nullable `workspace_id` that queries forget to filter would leave the catalog global.
- Running today’s `seed_data` before a tagged founder seeder exists would insert unowned global products and duplicate expenses.
- The old committed demo password for `abcd@fufu.com` may still match that row. This plan does not reset it.

## Recommended next task

Operator: accept this table or send corrections for all six rows, including whether the founder account will be created later as a new user. Do not add `workspace_id` until that approval is explicit.
