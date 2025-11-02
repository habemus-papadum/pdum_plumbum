# jq-fu — 43 Streaming Patterns (jq -c)

This cheat sheet collects 43 examples of powerful but not‑obvious `jq` idioms.
All assume you’re running `jq -c` for compact one‑line streaming output (no `[ ... ]`
wrapping). Each example includes a description and a code snippet.

---

## 1️⃣ Tag child items with parent fields
```jq
.[] | .name as $n | .group as $g | .items[] | {name:$n, group:$g, item:.}
```
Add parent fields to every nested item.

## 2️⃣ Keep array index when exploding
```jq
.items | to_entries[] | {idx:.index, item:.value}
```

## 3️⃣ Flatten nested arrays with lineage
```jq
.[] | .id as $pid | .buckets[] as $b | $b.items[] | {parent:$pid, bucket:$b.name, item:.}
```

## 4️⃣ Explode object fields to key/value records
```jq
.props | to_entries[] | {key:.key, value:.value}
```

## 5️⃣ Multi‑condition filter with defaults
```jq
select((.status // "unknown") == "ok" and (.lat? // 0) != 0)
```

## 6️⃣ Drop null/empty fields recursively
```jq
walk(if type=="object" then with_entries(select(.value!=null and .value!=[] and .value!={})) else . end)
```

## 7️⃣ Set defaults
```jq
.price = (.price // 0) | .tags = (.tags // [])
```

## 8️⃣ Remove noisy keys anywhere
```jq
walk(if type=="object" then del(.debug,.temp,.trace) else . end)
```

## 9️⃣ Parse with regex groups
```jq
.label | capture("^(?<cat>[A-Z]{2})-(?<id>\d+)$") | {category:.cat, id:(.id|tonumber)}
```

## 10️⃣ Rewrite path prefix
```jq
.path | gsub("^/api/v\d+/"; "/api/latest/")
```

## 11️⃣ Build interpolated strings
```jq
{slug:"\(.category)/\(.id)", title:(.title|tostring)}
```

## 12️⃣ Safe numeric coercion
```jq
.price = ((.price? // 0) | tonumber) | .qty = ((.qty? // 1) | tonumber)
```

## 13️⃣ Round to 2 decimals
```jq
.total = ((.total // 0) * 100 | round / 100)
```

## 14️⃣ ISO8601 ↔ epoch
```jq
.ts = (.timestamp|fromdateiso8601) | .ts_human = (.ts|todateiso8601)
```

## 15️⃣ Minute buckets
```jq
. | (.timestamp|fromdateiso8601/60|floor) as $m | {minute:$m, event:.}
```

## 16️⃣ Merge parent keys into child
```jq
.name as $n | .region as $r | .items[] | . + {name:$n, region:$r}
```

## 17️⃣ Deep patch
```jq
setpath(["meta","source"];"ingest-1")
```

## 18️⃣ Multiply each price
```jq
.items[] | .price |= (. * 1.05)
```

## 19️⃣ Stateful dedupe by key
(requires `-n` and streaming inputs)
```jq
reduce inputs as $x ({}; ($x.id|tostring) as $k | if .[$k] then . else . + {($k):true}, ($x|select(.id|tostring|in(.|keys_unsorted|map(tostring))|not)) end)
```

## 20️⃣ Running totals
```jq
foreach inputs as $r (0; . + ($r.value // 0); {ts:$r.ts, running:.})
```

## 21️⃣ Windowed aggregation when key changes
```jq
label $out | foreach inputs as $x ({user:null,sum:0};
  if .user==$x.user or .user==null
  then {user:$x.user,sum:(.sum+($x.value//0))}
  else (.,break $out|{user:$x.user,sum:($x.value//0)}) end;
  {user:.user,sum:.sum})
```

## 22️⃣ Join against side table (argfile)
```jq
INDEX($users[];.id) as $U | inputs | . + {user:($U[.user_id]//{})}
```

## 23️⃣ Join and project single field
```jq
INDEX($u[];.id) as $U | inputs | . + {user_name:($U[.user_id].name // "unknown")}
```

## 24️⃣ Rename keys dynamically
```jq
with_entries(.key |= (if .=="oldName" then "newName" elif startswith("x_") then sub("^x_";"") else . end))
```

## 25️⃣ Promote nested key
```jq
if has("meta") and .meta|has("id") then . + {meta_id:.meta.id}|del(.meta.id) else . end
```

## 26️⃣ Emit leaf paths
```jq
paths(scalars) as $p | {path:$p, value:(getpath($p))}
```

## 27️⃣ try/catch fallback
```jq
try (.number|tonumber) catch 0
```

## 28️⃣ Validate records
```jq
select(.id? and (.email?|test(".+@.+\..+")))
```

## 29️⃣ Assert invariant
```jq
. as $o | if ($o.qty // 0)>=0 then $o else error("negative qty") end
```

## 30️⃣ Stable hash of fields
```jq
{sku,qty}|tojson|@base64
```

## 31️⃣ URL/CSV encode
```jq
{url:"https://x/?q="+(.q|@uri), csv:([.a,.b,.c]|@csv)}
```

## 32️⃣ Parse kv logs
```jq
-Rn (input|split(" ")|map(split("="))|from_entries) as $r
| {ip:$r.ip, status:($r.status|tonumber), ms:($r.t|sub("ms$";"")|tonumber)}
```

## 33️⃣ Extract timestamps anywhere
```jq
.. | objects | select(has("timestamp")) | .timestamp
```

## 34️⃣ Cartesian product generator
```jq
-n '[1,2,3] as $a | ["x","y"] as $b | $a[] as $i | $b[] as $j | {i:$i,j:$j}'
```

## 35️⃣ Params from shell args
```jq
-n --arg user "$USER" --argjson cfg '{"k":1}' '{run_by:$user, cfg:$cfg}'
```

## 36️⃣ Branch + recombine
```jq
. as $row | {id:$row.id} | . + {extended:($row.a+$row.b)}
```

## 37️⃣ Switch by type
```jq
type as $t | {type:$t, value:(if $t=="number" then . * 2 elif $t=="string" then .+"!" else . end)}
```

## 38️⃣ Stringify non‑ASCII
```jq
walk(if type=="string" and (.[0:]|test("[^\u0000-\u007F]")) then @json else . end)
```

## 39️⃣ Mask secrets
```jq
walk(if type=="object" then with_entries(if (.key|test("(?i)secret|token|password")) then .value="***" else . end) else . end)
```

## 40️⃣ NDJSON → CSV rows
```jq
[.id, .user, .total] | @csv
```

## 41️⃣ TSV with defaults
```jq
[.id, (.name // ""), (.meta.version // "")] | @tsv
```

## 42️⃣ Propagate parent field to all nested objects
```jq
.name as $n | .. | objects | . + {parent_name:$n}
```

## 43️⃣ Conditionally explode arrays
```jq
if (.items?|type)=="array" then .items[] | . + {parent:.name} else . end
```

---

💡 **Usage tips**
- Always run with `jq -c` to keep outputs one‑per‑line.
- Use `--arg` / `--argjson` to feed parameters from shell.
- For massive NDJSON, prefer `foreach` and avoid slurping.
- Chain `walk`, `with_entries`, and `select` for deep transformations.
