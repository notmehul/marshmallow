From: Fatima Okonkwo <fokonkwo@harborline.internal>
To: Juno Castillo <jcastillo@harborline.internal>
Cc: Jessamine Lee <jlee@harborline.internal>, Glenn Wexler <gwexler@harborline.internal>
Subject: HOLD — HarborPass cutover blocked pending rollback token test

Juno —

I'm placing a hard gate on **HarborPass migration** until the **rollback token test** completes clean in staging. This is non-negotiable from my side as **fatima okonkwo** on HP-MIGRATE.

**Rollback token test** status (as of 26 May 17:00):
- Token issuance: pass  
- Simulated cutover rollback: pass  
- Pier 3 + Pier 5 reader failover: FAIL on second attempt (stale cache)  
- Re-test window booked tonight 21:00–23:00

We are still targeting **HarborPass 2.0** **go-live 2026-06-02** — that's the published **june 2 go-live** date Jessamine can cite externally once I clear the hold. Do not let pier leads promise earlier.

Jessamine — hold the **passenger notice** draft until I green-light. Outage copy can stay in your doc; just don't publish boards.

Juno — badge templates from P9-GATE week must not be recycled for HarborPass contractor access. Separate pool.

Glenn pinged about overtime for tonight's re-test crew. Approved if we finish before midnight.

— Fatima

P.S. Legacy Pier 7 barcode readers stay on the old stack until mid-June regardless — different sunset track.
