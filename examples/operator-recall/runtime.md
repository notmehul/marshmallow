# Marshmallow Alignment Router

Run this workspace's `recall` flow when available. It returns relevant context
plus bounded personal-guidance examples showing how the work should be done.
Then check `indexes/` or search `graph/` only when deeper context is needed. Use
`projections/` only for focused recall packets.

Do not crawl the whole graph by default. Do not treat `sources/` or `inbox/` as
ordinary runtime context. Do not load extra personal nodes merely to fill
context; the bounded personal-guidance layer stays below twenty percent of the
estimated response budget. Capture only unmistakable feedback.
