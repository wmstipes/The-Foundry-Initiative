# Learning Journal

Use this journal to capture progress without requiring polished prose.

## Entry template

### Date

### What I worked on

### What I learned

### What was difficult

### What I finished

### Next small step

---

## 2026-07-18

### What I worked on

Created the initial structure and guiding documents for The Foundry Initiative.

### What I learned

A project can begin with structure and intent before its first technical implementation is selected.

### What was difficult

Starting something meaningful can create pressure to make it large or perfect immediately.

### What I finished

Established a repository scaffold, roadmap, project vision, contribution workflow, and architecture placeholder.

### Next small step

Choose a first artifact that can be completed and demonstrated in a short development cycle.

---

## 2026-09-08

### What I worked on

Built SignalForge from an initial Raspberry Pi Kubernetes lab into a repeatable application and observability platform. The work progressed through Milestones 001-023 and culminated in Restaurant API `0.7.0` with lightweight Prometheus collection.

### What I learned

- Small milestones make a multi-component platform easier to build, test, and explain.
- A Kubernetes Service is useful for stable application access, but Prometheus should discover and scrape each replica directly when per-Pod counters matter.
- Application metrics and the Kubernetes Metrics API solve different problems; installing Prometheus does not make `kubectl top` available.
- Histogram buckets can be aggregated across replicas, making them appropriate for fleet-wide latency percentiles.
- Metric labels need the same design discipline as an API. Route templates and a bounded `unmatched` value prevent uncontrolled cardinality.
- Automated tests, manifest validation, pinned images, and operator helpers turn successful commands into a repeatable engineering workflow.
- Cross-platform quoting deserves explicit testing when PowerShell launches commands inside Linux containers.

### What was difficult

The most subtle problem was distinguishing a healthy metrics collector from broader cluster resource monitoring. Another challenge was correcting the Prometheus target-check helper after nested PowerShell and shell quoting produced an unterminated-string failure.

Release sequencing also required care: application changes, GitHub Actions, a version tag, the ARM64 image build, Kubernetes deployment, smoke tests, and Prometheus validation each had to complete in the right order.

### What I finished

- Deployed and operated a four-node Kubernetes cluster.
- Released Restaurant API `0.7.0` as three healthy replicas.
- Added application CI, ARM64 image publishing, versioned Kubernetes manifests, and validation automation.
- Added laptop-based deployment, smoke-test, status, log, and metrics helpers.
- Created and exercised an operator runbook.
- Deployed a least-privilege Prometheus collector with three healthy Pod targets.
- Added request latency, application-versus-synthetic traffic classification, and label-cardinality protection.
- Verified the live application, automatic target discovery, and baseline PromQL queries.

### Next small step

Select Milestone 024. Evaluate whether Kubernetes Metrics Server provides enough operational value to justify its footprint in the Raspberry Pi cluster.

---

## 2026-09-08 - Milestone 024

### What I worked on

Evaluated Kubernetes Metrics Server for SignalForge, repaired the cluster's kubelet serving-certificate configuration, and enabled current node and Pod resource visibility.

### What I learned

- Prometheus application metrics and the Kubernetes resource Metrics API are complementary rather than interchangeable.
- A healthy kubelet can still present a serving certificate that is unsuitable for a secure metrics client.
- `rotateCertificates: true` controls kubelet client-certificate rotation; `serverTLSBootstrap: true` is separately required for signed serving certificates.
- Core Kubernetes does not automatically approve kubelet serving CSRs because an operator must confirm that the requested DNS names and IP addresses belong to the requesting node.
- A TLS-authenticated request can correctly return HTTP 401. That response proves the certificate and connection succeeded while unauthenticated application access was rejected.
- `kubectl top` is useful for immediate operational checks, while historical analysis still belongs in Prometheus.

### What was difficult

The initial failure appeared to be a Metrics Server installation problem, but testing exposed three underlying identity issues: Windows SSH used the wrong username, the cluster nodes lacked durable hostname mappings, and kubelets served self-signed certificates containing only DNS SANs. Repairing the trust chain required verified SSH host keys, one-node-at-a-time kubelet changes, and manual inspection of every serving CSR.

### What I finished

- Restored verified, passwordless administrative SSH from `forge-head` to all workers.
- Made the SignalForge hostname mappings durable against cloud-init regeneration.
- Enabled kubelet serving-certificate bootstrap locally and in the kubeadm ConfigMap.
- Reviewed and approved four node-specific `kubernetes.io/kubelet-serving` CSRs.
- Verified Kubernetes-CA trust and InternalIP SANs on every kubelet endpoint.
- Deployed pinned Metrics Server v0.9.0 without `--kubelet-insecure-tls`.
- Enabled `kubectl top nodes` and `kubectl top pods` for all four nodes.
- Measured Metrics Server at 4m CPU and 21 MiB memory and retained it.

### Next small step

Plan persistent NVMe-backed Prometheus storage before replacing the intentionally ephemeral `emptyDir` volume.

---

## 2026-09-09 - Milestone 025

### What I worked on

Compared practical persistent-storage designs for the SignalForge Prometheus server and converted the result into an explicit implementation and recovery plan before touching the NVMe or live cluster.

### What I learned

- Persistence and high availability are separate properties. A local PV preserves data across Pod replacement but cannot follow the workload to another node.
- PV node affinity lets the Kubernetes scheduler understand a local disk's physical location; a plain `hostPath` does not express that relationship as safely in a multi-node cluster.
- Prometheus's TSDB favors a local POSIX filesystem and does not support NFS, even when network storage initially appears more flexible.
- A retention-size limit needs free space for the WAL, head chunks, and compaction. The application limit should stay below the filesystem's full capacity.
- A missing-mount safeguard matters as much as the normal mount path. Otherwise, a valid directory can silently redirect heavy writes back to the SD card.
- Backups must leave the storage node and be restore-tested; `Retain` protects data from Kubernetes deletion behavior but is not a backup.

### What was difficult

The main tradeoff was accepting that the lightest design is intentionally node-bound. Adding NFS or a distributed storage platform would appear to improve mobility, but it would either conflict with Prometheus storage guidance or add more operational burden than this single workload justifies.

It also required keeping the planning milestone distinct from implementation. The approved design is now documented, but the repository still truthfully describes the live collector as ephemeral.

### What I finished

- Selected a static `local` PV on a dedicated ext4 partition ïN-¢G§²ÚîÆ­yÒ7–çF†WF–2FW7B66W2à ¤Væv–æVW&–æræ÷FW3¢ÆW'B–FVçF—G’&VÆöæw2–â7F&ÆRÆ&VÇ3²6†æv–ærF–væ÷7F–26÷VçG2&VÆöær–âææ÷FF–öç2âf–ÆVB67&W2ÂÖ—76–ærF—66÷fW'’6W&–W2ÂæB7F÷VBWfÇVF–öâ&RF–ffW&VçB6—GVF–öç2âG&ç6—F–öâ&WGvVVâv&æ–æræB7&—F–6Â6öæF—F–öç27F'G2F†R÷F†W"'VÆRw2–æFWVæFVçBFVÆ’Â6òâW‡Æ–6—BVæF–ærÖöæÇ’–çFW'fÂ—2'BöbF†R66WFVBFW6–vââF†R7&—F–6ÂW‡&W76–öâw2'6VçB'&æ6‚FöW2æ÷B&WGW&â†VÇF‡’×F&vWB6÷VçBæB×W7Bæ÷B&RFW67&–&VB2öæRà ¥6÷W&6RÖÆWfVÂFW7G2æB–æ7F—fRÖ6öæf–wW&F–öâwV&G276VBÂ'WBF†W’Fòæ÷B&÷fR&öÕÂ&V†f–÷"âF†R&W&F–öâVçf—&öæÖVçBÆ6¶VB&ö×FööÂæBFö6¶W#²7V'6WVVçB´v—D‡V"7F–öç2'Vâ3CSC#ss5Ò†‡GG3¢òöv—F‡V"æ6öÒ÷v×7F—W2õF†RÔf÷VæG'’Ô–æ—F–F—fRö7F–öç2÷'Vç2ó3CSC#ss2’7WÆ–VBF†RÖ—76–ærWf–FVæ6Rf÷"6öÖÖ—B#–fS3¢&VÂ&ö×FööÂ2ã2ã"fÆ–FFVB&÷F‚'VÆW2æB76VBÆÂ’66Væ&–÷2â"3RÆFW"ÖW&vVBBcFS3†VâöffÆ–æR6÷'&V7FæW72FöW2æ÷BW7F&Æ—6‚÷W&F–öæÂFVÆ’7V—F&–Æ—G’÷"WF†÷&—¦R7F—fF–öâà ¢22##bÓ’ÓÒÖ–ÆW7FöæR37F—fF–öâ&Wf–Wr&W&F–öà ¥F†R7F—fF–öâ6æF–FFR&WW6W2F†R6öæf–tÖÇ&VG’Ö÷VçFVBBöWF2÷&öÖWF†WW6¢öæRVÖ&VFFVB6æöæ–6Â'VÆRf–ÆRæBöæRW†7B'VÆUöf–ÆW6VçG'’&R7Vff–6–VçBÂv—F‚æòFWÆ÷–ÖVçBÂ$$2Â7F÷&vRÂw&fæ÷"&V6V—fW"6†ævRà ¥F†R6fWG’&÷VæF'’&VÆöæw2–âF†R÷W&F÷"F‚2vVÆÂ2F†RÖæ–fW7BâF†R†VÇW"F†W&Vf÷&RFVfVÇG2Fò–ç7V7F–öâÂ6Æ76–f–W2F†RÆ—fR6öæf–tÖ'’æ÷&ÖÆ—¦VB†6†W2Â&WV—&W2F†R¶æ÷vâ6öçFW‡Bö–ÖvR÷&WÆ–6÷F&vWB&6VÆ–æRÂ6†÷w2&V6VçB6÷fW&vR†—7F÷'’æB·V&V7FÂF–ffÂæB7F÷2&Vf÷&R×WFF–öââW‡Æ–6—B7F—fF–öâf—'7Bw&—FW2fÆ–FFVB&V6÷fW'’ö&¦V7C²f–ÆVB÷7BÖ6†ævRfW&–f–6F–öâG&–vvW'2&öÆÆ&6²â&W÷6—F÷'’FW6—&VB7FFRÂWfÇVF÷"×f—6–&ÆRf—&–ær7FFRæBFVÆ—fW&VBæ÷F–f–6F–öâ&RF‡&VRF–ffW&VçB6Æ–×2æB×W7B&VÖ–â6W&FRà ¤æW‡B6ÖÆÂ7FW¢&Wf–WrF†R&W÷6—F÷'’F–fbæB&VBÖöæÇ’Æ—fRÆââöæÇ’6W&FR÷W&F÷"FV6—6–öâ6âWF†÷&—¦R7F—fF–öâà ¢22##bÓ’ÓÒÖ–ÆW7FöæR3wV&FVB7F—fF–öà ¥F†R&VBÖöæÇ’Æâf÷VæBF†RW†7B&6VÆ–æRÂF‡&VR†VÇF‡’F&vWG2ÂæòÆöFVB'VÆW2ÂæBæò&VÆ÷r×F‡&VR6×ÆW27&÷72#B†÷W'2â—G2f—'7BGvòGFV×G2W‡÷6VBv–æF÷w2×7V6–f–2FWF–Ã¢·V&V7FÂF–ffæVVG2âW‡FW&æÂF–fbæW†VÂv†–ÆRv–æF÷w2÷vW%6†VÆÂFVf–æW2F–ff2âÆ–2f÷"6ö×&RÔö&¦V7Fâ&W7G&–7F–ærFWFV7F–öâFòâÆ–6F–öâæBÆö6F–ærv—Bf÷"v–æF÷w2r'VæFÆVBW†V7WF&ÆRÖFRF†R&Wf–Wr÷'F&ÆRv—F†÷WB6†æv–ærF†R6ÇW7FW"à ¤gFW""3bÖW&vVBæBÖ–¶RW‡Æ–6—FÇ’&÷fVB7F—fF–öâÂF†R†VÇW"6fVBæBfW&–f–VBF†R&6VÆ–æR6öæf–tÖÂÆ–VBöæÇ’F†R66WFVB6öæf–tÖÂ&W7F'FVBöæÇ’&öÖWF†WW2ÂæB6ö×ÆWFVBÆÂ÷7BÖ6†ævR6†V6·2ââ–æFWVæFVçBÆâF†Vâf÷VæBæò&W÷6—F÷'’öÆ—fRF–fbæB&V6öæf—&ÖVBF‡&VR†VÇF‡’F&vWG2v—F‚&÷F‚'VÆW2†VÇF‡’æB–æ7F—fRâF†R&V6÷fW'’f–ÆR—2&WF–æVBv—F‚&V6÷&FVB4„Ó#Sc²&öÆÆ&6²v2æ÷BæVVFVBà ¥F†RÖ–âÆW76öâ—2F†BFW6—&VB7FFRÂWfÇVF÷"7FFRæBæ÷F–f–6F–öâFVÆ—fW'’&R6W&FRWf–FVæ6R6Æ–×2âÖ–ÆW7FöæR3W7F&Æ—6†W2F†Rf—'7BGvòÂv†–ÆRæ÷F–f–6F–öâFVÆ—fW'’æB–æFWVæFVçBÖöæ—F÷&–ær&VÖ–âFVÆ–&W&FVÇ’FVfW'&VBâæW‡C¢ö'6W'fRæGW&Â&V†f–÷"&F†W"F†âÖçVf7GW&–ærf–ÇW&RÂF†Vâ&Wf—6—BF†RG&–ÂFVÆ—2&Vf÷&R6öç6–FW&–ærFVÆ—fW'’à  ¢ÒÒĞ ¢22##bÓ’ÓÒÖ–ÆW7FöæR3  ¢222v†B’v÷&¶VBöà ¤'V–ÇBæBFWÆ÷–VBf÷&vR”ÔÂv÷&¶&Væ6‚Â'&÷w6W"ÖÆö6Â·V&W&æWFW2Öæ–fW7B–ç7V7F÷"v—F‚×VÇF’ÖFö7VÖVçB'6–ærÂf÷&ÖGF–ærÂ‡VÖâ×&VF&ÆR7VÖÖ&–W2Â&÷VæFVB÷W&F–öæÂf–æF–æw2ÂæBâW‡æF&ÆRö&¦V7BG&VRà ¢222v†B’ÆV&æV@ ¢Ò7FF–2'&÷w6W"Æ–6F–öâ6â&÷f–FRW6VgVÂÖæ–fW7B&Wf–Wrv—F†÷WB·V&W&æWFW27&VFVçF–Ç2Â&6¶VæB7F÷&vRÂ÷"6W'fW"×6–FR&ö6W76–ærà¢Ò&VÆV6R6fWG’–×&÷fW2v†Vâ6÷W&6RFW7G2Â×VÇF’Ö&6†—FV7GW&R–ÖvR'V–ÆG2Â–Ö×WF&ÆRF–vW7G2Â6W'fW"×6–FRG'’×'VâÂÆ—fRF–fbÂæBW‡Æ–6—BFWÆ÷–ÖVçB&÷fÂ&VÖ–â6W&FRvFW2à¢Òf÷&ÖGFW"×W7B&÷VæB×G&—×VÇF’ÖFö7VÖVçB–çWC²&W6W'f–ærFö7VÖVçBw2W†—7F–ær7F'BÖ&¶W"v†–ÆRÇ6ò¦ö–æ–ærFö7VÖVçG2v—F‚ÒÒÖ6â6–ÆVçFÇ’7&VFRâV×G’Fö7VÖVçBà¢Ò'&÷w6W"66WFæ6R6F6†W2–çFW&7F–öâFVfV7G2F†B6÷W&6RÖÆWfVÂFW7G2Ö’Ö—72âF†Rf–ÆVBFW7BF—&V7FÇ’&öGV6VB6—‡F‚&Vw&W76–öâFW7BæB6÷'&V7FVBF6‚&VÆV6Rà¢Ò–FV×÷FVçBT’7F–öç2Ö’æVVBf—6–&ÆR6öæf—&ÖF–öâWfVâv†VâF†W’7V66VVBæB&öGV6RÆ—GFÆRf—7VÂ6†ævRà ¢222v†Bv2F–ff–7VÇ@ ¥F†Rf—'7BããFWÆ÷–ÖVçBv2†VÇF‡’BF†R6öçF–æW"æB·V&W&æWFW2Æ–W'2Â'WB6Æ–6¶–ærf÷&ÖBöâF†R6×ÆRW‡÷6VBâÆ–6F–öâFVfV7BâF†R”ÔÂÆ–'&'’&W6W'fVBF†R6V6öæBFö7VÖVçBw27F'BÖ&¶W"Âv†–ÆRF†Rf÷&ÖGFW"FFVBæ÷F†W"6W&F÷"âF†B7&VFVBâV×G’Fö7VÖVçB"FW7—FRF†R÷&–v–æÂ6×ÆR&V–ærfÆ–Bà ¥v–æF÷w2·V&V7FÂF–ffÇ6ò&WV—&VBv—Bf÷"v–æF÷w2r'VæFÆVBF–fbæW†VFò&RFFVBFV×÷&&–Ç’FòD†â¶VW–ærF†R–çfW7F–vF–öâ&VBÖöæÇ’VçF–ÂV6‚×WFF–öâv26W&FVÇ’&÷fVB&W6W'fVB6ÆV"÷W&F–öæÂ&÷VæF'’à ¢222v†B’f–æ—6†V@ ¢ÒFFVBÆö6¶VBæöFRFWVæFVæ6–W2Â6—‚æÇ—¦W"FW7G2Â4’ÂVF—BÂæBÔCcBô$ÓcB6öçF–æW"fÆ–FF–öâà¢ÒV&Æ—6†VBfW'6–öæVB–ÖvW2F‡&÷Vv‚wV&FVBFrv÷&¶fÆ÷rv—F†÷WBfÆöF–ærÆFW7FFrà¢ÒFWÆ÷–VB&W7G&–7FVBÂæöâ×&ö÷BÂ&VBÖöæÇ’v÷&¶&Væ6‚v—F‚æò·V&W&æWFW2–FVçF—G’÷"W'6—7FVB”ÔÂà¢ÒV&Æ—6†VBæB–ææVB6÷'&V7FVB&VÆV6RããBô4’–æFW‚F–vW7B6†#Sc£SS6CScC“C&3†cvV33Cc63†66&fSSƒC&63s3FCF#sF&CFVcƒcc–à¢ÒfW&–f–VBöæR&VG’&WÆ–6v—F‚¦W&ò&W7F'G2ÂÖF6†–ær'VçF–ÖR–ÖvT”BÂæöFU÷'B†VÇF‚Â6V7W&—G’†VFW'2ÂæB'&÷w6W"&V†f–÷"à¢Ò6öæf—&ÖVB×VÇF’ÖFö7VÖVçBf÷&ÖGF–ær&WF–ç2F†RFWÆ÷–ÖVçBæB6W'f–6RÂæBf—6–&Ç’&Vf÷&ÖGFVBfÆ÷r×7G–ÆR”ÔÂ&VÖ–ç2fÆ–Bà ¢222æW‡B6ÖÆÂ7FW  ¤6ö×ÆWFRf–æÂ&Wf–WræBÖW&vRöb"3‚v—F‚W‡Æ–6—B&÷fÂâG&VBç’÷6—F—fRf÷&ÖB×7FGW2ÖW76vR÷"'&öFW"66†VÖfÆ–FF–öâ26W&FRgWGW&R–æ7&VÖVçBà  ¢ÒÒĞ ¢22##bÓ’Ó"ÒÖ–ÆW7FöæR32v÷&¶&Væ6‚W6&–Æ—G’æBãã"&öÆÆ÷W@ ¢222v†B’v÷&¶VBöà ¤–×&÷fVBf÷&vR”ÔÂv÷&¶&Væ6‚–çFW&7F–öâ6Æ&—G’æBF–væ÷7F–2&V6—6–öâv—F†÷WB6†æv–ær—G2'&÷w6W"ÖÆö6ÂG'W7B&÷VæF'’âF†R&VÆV6RFG2W‡Æ–6—B7F–öâfVVF&6²Â6Æ–6¶&ÆR'6W"Æö6F–öç2Âf–ÆVæÖR&W6W'fF–öâÂ¶W–&ö&B6†÷'F7WG2Â&÷FV7FVB6ÆV&–ærÂ66W76–&ÆRF"7FFRÂæBDôÒ–çFW&7F–öâFW7G2à ¢222v†B’ÆV&æV@ ¢Ò6ÖÆÂ'&÷w6W"66WFæ6RFW7G2W‡÷6RW6&–Æ—G’FVfV7G2F†BæÇ—¦W"FW7G26ææ÷B6VS²F†Rf—'7BF–væ÷7F–2Öæf–vF–öâ72f÷VæB7FÆR&VBfVVF&6²gFW"F†R”ÔÂv26÷'&V7FVBà¢Ò–FV×÷FVçB7F–öç27F–ÆÂæVVBW‡Æ–6—B6öæf—&ÖF–öââ&W÷'F–ærF†B”ÔÂ—2Ç&VG’f÷&ÖGFVB&VÖ÷fW2Ö&–wV—G’v—F†÷WB6†æv–ærF†RFö7VÖVçBà¢Ò&VÆV6RV&Æ–6F–öâÂ–Ö×WF&ÆRF–vW7B–ææ–ærÂ6W'fW"×6–FRG'’×'VâÂÆ—fRF–fb&Wf–WrÂFWÆ÷–ÖVçB&÷fÂÂ&öÆÆ÷WBfW&–f–6F–öâÂæB'&÷w6W"66WFæ6R&RF—7F–æ7BWf–FVæ6RvFW2à¢Ò'VçF–ÖR–ÖvT”BÖF6†–ærF†R&Wf–WvVBô4’–æFW‚F–vW7B&÷fW2F†R6ÇW7FW"—2'Vææ–ærF†R&÷fVB×VÇF’Ö&6†—FV7GW&R&VÆV6R&F†W"F†âÖW&VÇ’G'W7F–ær—G2Frà ¢222v†B’f–æ—6†V@ ¢ÒW‡æFVBWFöÖFVB6÷fW&vRFò"æÇ—¦W"æBDôÒ–çFW&7F–öâFW7G2à¢ÒV&Æ—6†VBãã&f÷"ÔCcBæB$ÓcBv—F†÷WBfÆöF–ærFrà¢Ò–ææVBô4’–æFW‚F–vW7B6†#Sc£vc3F&S363SV&6V#v&cS3#SVCC–SCƒ36SS#3–Vf&FC“ƒ#33Cc†SS63và¢Ò&öÆÆVB÷WBöæÇ’F†R&÷fVBv÷&¶&Væ6‚FWÆ÷–ÖVçBæBfW&–f–VBöæR&VG’&WÆ–6v—F‚¦W&ò&W7F'G2à¢ÒfW&–f–VBF†R&VG’VæGö–çE6Æ–6RÂæöFU÷'B†VÇF‚Â6V7W&—G’†VFW'2ÂæBÆÂ6WfVâÆ—fR'&÷w6W"6Öö¶R6†V6·2à ¢222æW‡B6ÖÆÂ7FW  ¥"3’ÖW&vVBBvFVFFâ&Vv–âÖ–ÆW7FöæR3B26W&FR&÷VæFVB6†ævRf÷"FVWW"FWFW&Ö–æ—7F–2·V&W&æWFW26†V6·2v—F‚&V6—6R”ÔÂF‡2æB7VvvW7FVB6÷'&V7F–öç2à ¢ÒÒĞ ¢22##bÓ’Ó2ÒÖ–ÆW7FöæR3BFWFW&Ö–æ—7F–26†V6·2æB7F–öæ&ÆR&VÖVF–F–öà ¢222v†B’v÷&¶VBöà ¤W‡æFVBf÷&vR”ÔÂv÷&¶&Væ6‚g&öÒ'6W"Öfö7W6VBfVVF&6²–çFò&÷VæFVB·V&W&æWFW2Öæ–fW7B–ç7V7F–öâFööÂâf–æF–æw2æ÷r–æ6ÇVFR6Æ–6¶&ÆR”ÔÂF‡2ÂÆ–âÖÆæwVvR&—6²W‡ÆæF–öç2Â&V6öÖÖVæFVB6†ævW2Â6÷–&ÆR”ÔÂW†×ÆW2Â÷W&F–öæÂ6WF–öç2ÂæB–æ—F–Âõt5·V&W&æWFW2F÷£##R³&VfW&Væ6W2âFWFW&Ö–æ—7F–27&÷72ÖFö7VÖVçB6†V6·26÷fW"v÷&¶ÆöB6VÆV7F÷'2ÂGWÆ–6FR–FVçF—F–W2Â6W'f–6R6VÆV7F–öâÂæÖVBF&vWB÷'G2Â†÷7BæÖW76W2Â6öçF–æW"†&FVæ–ærÂæB6V66ö×6öæf–wW&F–öâà ¢222v†B’ÆV&æV@ ¢Òf–æF–ær&V6öÖW27V'7FçF–ÆÇ’Ö÷&RW6VgVÂv†Vâ—B–FVçF–f–W2F†RW†7Bf–VÆBÂW‡Æ–ç2v‡’—BÖGFW'2ÂæB6†÷w2&Wf–Wv&ÆR6÷'&V7F–öâà¢ÒÖ—76–ærÖf–VÆBF–væ÷7F–72æVVBFòæf–vFRFòF†RæV&W7BW†—7F–ær&VçB&V6W6RF†RFW6—&VBÆ–æRFöW2æ÷B–WBW†—7Bà¢Ò'&÷w6W"ÖÆö6ÂæÇ—6—26â&÷f–FRÖVæ–ævgVÂ÷W&F–öæÂwV–Fæ6Rv†–ÆRÖ–çF–æ–ærâW‡Æ–6—B&÷VæF'’&÷VæB·V&W&æWFW266†VÖÂFÖ—76–öâÂæB6ÇW7FW"Ö6öçFW‡B6Æ–×2à¢ÒV&Æ—6†–ærÂF–vW7B–ææ–ærÂ6W'fW"×6–FRG'’×'VâÂF–fb&Wf–WrÂFWÆ÷–ÖVçB&÷fÂÂ'VçF–ÖRfW&–f–6F–öâÂæB'&÷w6W"66WFæ6R&VÖ–â6W&FRWf–FVæ6RvFW2à ¢222v†B’f–æ—6†V@ ¢ÒW‡æFVBWFöÖFVB6÷fW&vRFò#2æÇ—¦W"æBDôÒ–çFW&7F–öâFW7G2à¢ÒV&Æ—6†VBã"ãf÷"ÔCcBæB$ÓcBv—F†÷WBfÆöF–ærFrà¢Ò–ææVBæBfW&–f–VBô4’–æFW‚F–vW7B6†#Sc£&S3“C&f3–6cc#“f##ƒs&C3c63fSF#FSƒs“Csf#F&#33c6f#Sss#à¢Ò&öÆÆVB÷WBöæÇ’F†R&÷fVBv÷&¶&Væ6‚FWÆ÷–ÖVçBæBfW&–f–VBöæR&VG’&WÆ–6v—F‚¦W&ò&W7F'G2à¢ÒfW&–f–VBVæGö–çE6Æ–6R&÷WF–ærÂæöFU÷'B†VÇF‚Â6V7W&—G’†VFW'2Â6Æ–6¶&ÆRF‡2ÂW‡æF&ÆRf—‚wV–Fæ6RÂ6Æ—&ö&BW†×ÆW2Â6WF–öç2ÂæBõt5&VfW&Væ6W2–âF†RÆ—fRÆ–6F–öâà ¢222æW‡B6ÖÆÂ7FW  ¤6ö×ÆWFRf–æÂ&Wf–WræBÖW&vRöb"3â&Vv–âvVæW&Â”ÔÂ–ç7V7F–öâÖöFR2Ö–ÆW7FöæR3R–âæWr6†BÂÆVf–ær·V&W&æWFW266†VÖfÆ–FF–öâæB'&öFW"õt56÷fW&vRf÷"Ö–ÆW7FöæW23bæB3rà ¢ÒÒĞ ¢22##bÓ’Ó2ÒÖ–ÆW7FöæR3RvVæW&Â”ÔÂ–ç7V7F–öà ¢222v†B’v÷&¶VBöà ¤FFVBâW‡Æ–6—BvVæW&Â”ÔÂ–ç7V7F–öâÖöFR&W6–FRF†RW†—7F–ær·V&W&æWFW2ÖöFRâ·V&W&æWFW2&VÖ–ç2F†R7F'GWFVfVÇBÂæB7v—F6†–ærÖöFW2&W6W'fW2F†RVF—F÷"6öçFVçG2v†–ÆR&WW6–ærF†R6ÖR'&÷w6W"ÖÆö6Â'6W"Âf÷&ÖGFW"ÂF–væ÷7F–72Âf–ÆR†æFÆ–ærÂæBFö7VÖVçBG&VRà ¢222v†B’ÆV&æV@ ¢Ò'6–æræB&W6VçFF–öâ&÷VæF&–W26â&R6W&FVB6ÆVæÇ“¢&÷F‚ÖöFW26†&R7–çF‚†æFÆ–ærÂv†–ÆRöæÇ’·V&W&æWFW2ÖöFRW&f÷&×2&W6÷W&6R–çFW'&WFF–öâæB÷W&F–öæÂ6†V6·2à¢ÒvVæW&Â”ÔÂæVVG2FòG&VBÖ–æw2Â6WVVæ6W2ÂæB66Æ'22fÆ–BFö7VÖVçB&ö÷G2–ç7FVBöb77VÖ–ærWfW'’Fö7VÖVçB&W&W6VçG2âö&¦V7Bà¢ÒW‡Æ–6—BÖöFRÆ&VÇ2æB&W÷'BÖ&÷VæF'’FW‡B&WfVçB7V66W76gVÂvVæW&Â”ÔÂ'6Rg&öÒ&V–ærÖ—7F¶Vâf÷"·V&W&æWFW2fÆ–FF–öâà ¢222v†B’f–æ—6†V@ ¢ÒFFVBÖ–ærÂ6WVVæ6RÂæB66Æ"7VÖÖ&–W2f÷"vVæW&Â”ÔÂà¢Ò7W&W76VB·V&W&æWFW2ÖöæÇ’f–æF–æw2Â&VÖVF–F–öâwV–Fæ6RÂæBõt5&VfW&Væ6W2÷WG6–FR·V&W&æWFW2ÖöFRà¢Ò&W6W'fVB·V&W&æWFW2&V†f–÷"2F†RFW7FVBFVfVÇBà¢ÒW‡æFVBæÇ—¦W"æB'&÷w6W"–çFW&7F–öâ6÷fW&vRg&öÒ#2Fò376–ærFW7G2à¢Ò&VÆV6VB6¶vRÖWFFF2ã2ãà¢Ò76VBVÆÂ×&WVW7B4’æBF†Ræöâ×V&Æ—6†–ærÔCcBô$ÓcB–ÖvR'V–ÆBà¢ÒV&Æ—6†VB&÷fVB–ÖvRv×7F—W2÷6–væÆf÷&vR×–ÖÂ×v÷&¶&Væ6ƒ£ã2ãF‡&÷Vv‚v—D‡V"7F–öç2à¢ÒfW&–f–VBF†R&Vv—7G'’w2ÔCcBæB$ÓcBÖæ–fW7G2æB&V6÷&FVBô4’–æFW‚F–vW7B6†#Sc£6&CC#“&cf6&CSfF&3“sc“#FC&#c6cƒ“6scS6S#cSFVfVF3#vS6c3ƒffà¢Ò&Wf–WvVBF†R6W'fW"×6–FRG'’×'VâæBÆ—fRFWÆ÷–ÖVçBÖöæÇ’F–fb&Vf÷&RÇ––ærF†R&÷fVB6æF–FFRà¢ÒFWÆ÷–VBÖF6†–ærã2ãfW'6–öâÆ&VÇ2æBF†R–Ö×WF&ÆRô4’–æFW‚F–vW7Bv—F‚öæR&VG’&WÆ–6Â¦W&ò&W7F'G2ÂæBÖF6†–ær'VçF–ÖR–ÖvT”Bà¢ÒfW&–f–VB&VG’&÷WF–ærÂ…EE#†VÇF‚æBvR&W7öç6W2Â&÷F‚ÖöFRÖ&¶W'2ÂæBF†RW‡V7FVB6V7W&—G’†VFW'2à¢Ò6ö×ÆWFVBÆ—fR'&÷w6W"66WFæ6Rf÷"&÷F‚ÖöFW2Â–æ6ÇVF–ær6öçFVçB×&W6W'f–ær7v—F6†W2Â·V&W&æWFW2Öf–æF–ær7W&W76–öâÂæBÖ–ærÂ6WVVæ6RÂ66Æ"ÂæBW‡Æ–6—BçVÆÂ&ö÷G2à¢ÒÖW&vVB"3B#CVVS&gFW"ÆÂ6†V6·2æB&÷fÂvFW276VBà ¢222æW‡B6ÖÆÂ7FW  ¤&Vv–âÖ–ÆW7FöæR3b26W&FR&÷VæFVB–æ7&VÖVçBf÷"'&÷w6W"ÖÆö6Â·V&W&æWFW266†VÖfÆ–FF–öâv–ç7BöæR–ææVB·V&W&æWFW2fW'6–öââ&W÷'BVç7W÷'FVB&W6÷W&6W2æBVæf–Æ&ÆR5$B66†VÖ2W‡Æ–6—FÇ’Â&W6W'fRvVæW&Â”ÔÂ&V†f–÷"ÂæB¶VWV&Æ–6F–öâÂFWÆ÷–ÖVçBÂæBÖW&vR26W&FVÇ’&÷fVB6†V6·ö–çG2à ¢ÒÒĞ ¢22##bÓ’Ó2ÒÖ–ÆW7FöæR3b'&÷w6W"ÖÆö6Â·V&W&æWFW266†VÖfÆ–FF–öà ¢222v†B’v÷&¶VBöà ¤FFVBâöffÆ–æR·V&W&æWFW266†VÖÆ–W"Fòf÷&vR”ÔÂv÷&¶&Væ6‚v†–ÆR&WF–æ–ærF†R'&÷w6W"ÖöæÇ’G'W7B&÷VæF'’â·V&W&æWFW2&VÖ–ç2F†RFVfVÇBÖöFRâF†RfÆ–FF–öâ&W÷'Bæ÷r6W&FW2”ÔÂ7–çF‚Â·V&W&æWFW2Fö7VÖVçB6†RÂFWFW&Ö–æ—7F–2÷W&F–öæÂ&Wf–WrÂæB66†VÖ&W7VÇG2âvVæW&Â”ÔÂ6öçF–çVW2Fò&÷f–FR7–çF‚æB7G'V7GW&R–ç7V7F–öâv—F†÷WB·V&W&æWFW2f–æF–æw2à ¢222v†B’ÆV&æV@ ¢Ò66†VÖ×fÆ–B&W7VÇBæVVG2âW†7BfW'6–öâæB7W÷'B×6WBÆ&VÃ²v—F†÷WB&÷F‚Â—B6â–×Ç’'&öFW"6ö×F–&–Æ—G’F†âv27GVÆÇ’FW7FVBà¢ÒVç7W÷'FVB'V–ÇBÖ–â&W6÷W&6W2æB7W7FöÒ&W6÷W&6W2v—F‚Væf–Æ&ÆR5$B66†VÖ2&R¶æ÷vÆVFvRÖ&÷VæF'’7FFW2Âæ÷B7V66W76W2÷"f–ÇW&W2à¢Ò·V&W&æWFW2–çD÷%7G&–ævf–VÆG2æVVBW‡Æ–6—Bæ÷&ÖÆ—¦F–öâv†Vâ6öç7VÖ–ærF†R–ææVB÷Vä’c"Fö7VÖVçBF‡&÷Vv‚¥4ôâ66†VÖfÆ–FF÷"à¢Ò'VæFÆ–æröæÇ’F†RG&ç6—F—fRFVf–æ—F–öç2f÷"âW‡Æ–6—Bud²6WB¶VW2F†R7FF–2Æ–6F–öâ&÷VæFVBv†–ÆR&W6W'f–æröffÆ–æR÷W&F–öâà ¢222v†B’f–æ—6†V@ ¢Ò–ææVBF†R6÷W&6R66†VÖFò·V&W&æWFW2cã3bãFæB&V6÷&FVBF†RW7G&VÒ4„Ó#Sbà¢ÒFFVB&W&öGV6–&ÆRvVæW&F–öâöb"Ôud²Â“bÖFVf–æ—F–öâ'&÷w6W"'VæFÆRà¢ÒFFVBW‡Æ–6—BfÆ–FÂ–çfÆ–FÂVç7W÷'FVFÂ66†VÖ×Væf–Æ&ÆVÂæBæ÷BÖWfÇVFVF7FFW2à¢ÒFFVB6Æ–6¶&ÆR66†VÖÖW'&÷"F‡2æB6ÆV"T’6FVv÷'’6W&F–öâà¢Ò&W6W'fVBvVæW&Â”ÔÂ&V†f–÷"æBF†R'6Væ6Röb·V&W&æWFW266†VÖf–æF–æw2–âF†BÖöFRà¢ÒW‡æFVBWFöÖFVB6÷fW&vRg&öÒ3FòC"76–ærFW7G2Â–æ6ÇVF–ær6ö×–ÆF–öâöbWfW'’7W÷'FVB66†VÖà¢Ò76VBF†R&öGV7F–öâ'V–ÆBÂFWVæFVæ7’VF—BÂæBv†—FW76RfÆ–FF–öâà¢ÒV&Æ—6†VBG&gB"32æB76VBv÷&¶&Væ6‚4’ÇW2F†Ræöâ×V&Æ—6†–ærÔCcBô$ÓcB6öçF–æW"'V–ÆBà¢ÒV&Æ—6†VBF†R6W&FVÇ’&÷fVBãBãô4’–æFW‚B6†#Sc£“fS6C†SF#Sc6CVCs“S#&&C†cCVcfc6S6Vf36#““ƒSC#ƒf#FS3CsvæBfW&–f–VB7F—fRÆ–çW‚ÔCcBæB$ÓcBÖæ–fW7G2à¢ÒÆ–VBF†R6W&FVÇ’&Wf–WvVBFWÆ÷–ÖVçBÖöæÇ’WFFRæBfW&–f–VBöæR&VG’öBv—F‚¦W&ò&W7F'G2ÂF†RW‡V7FVB'VçF–ÖR–ÖvRF–vW7BÂöæR&VG’VæGö–çBÂ…EE#†VÇF‚æBvR&W7öç6W2ÂæBF†RW‡V7FVB55æBæ÷6æ–ff†VFW'2à¢Òf÷VæB&Ææ²×vRFVfV7BGW&–ærÆ—fR'&÷w6W"66WFæ6S¢¥bw2'VçF–ÖR66†VÖ6ö×–ÆW"W6W2G–æÖ–26öFRvVæW&F–öâÂv†–6‚F†R&öGV7F–öâ67&—B×7&2w6VÆbvöÆ–7’6÷'&V7FÇ’&Æö6·2à¢Ò¶WBF†R7G&–7B55Væ6†ævVBæB&W&VBÆö6ÂãBã6÷'&V7F–öâF†B6†V6·2–â&W&öGV6–&ÆR7FæFÆöæRfÆ–FF÷'2vVæW&FVBB'V–ÆBF–ÖRà¢ÒFFVB&öGV7F–öâÖ'VæFÆRwV&BF†Bf–Ç2–bWfÆ÷"æWrgVæ7F–öæ—2&W6VçC²ÆÂC"FW7G2ÂF†R&öGV7F–öâ'V–ÆBÂfÆ–FF÷"&W&öGV6–&–Æ—G’ÂæBF†RFWVæFVæ7’VF—B72Æö6ÆÇ’à¢ÒV&Æ—6†VBF†R6W&FVÇ’&÷fVBãBã6÷'&V7F–öâ–â'Vâ3Csƒss3“v²—G27F—fRÔCcBô$ÓcBô4’–æFW‚—26†#Sc£“f3sV3“3†cc3ccƒc“S#“Cƒ#–3cccvcsv#3S6&C&FcV–f3cv&FFc&à¢Ò&Wf–WvVBF†R6W'fW"×6–FRG'’×'VâæBÆ—fRF–fbÂF†VâFWÆ÷–VBF†R6W&FVÇ’&÷fVB–Ö×WF&ÆRãBã–æFW‚à¢ÒfW&–f–VBöæR&VG’öBv—F‚¦W&ò&W7F'G2ÂF†RW†7B'VçF–ÖR–ÖvT”BÂöæR&VG’VæGö–çE6Æ–6RÂ…EE#†VÇF‚æBvR&W7öç6W2ÂæBF†RVæ6†ævVB55æBæ÷6æ–ff†VFW'2à¢Ò&WVFVB'&÷w6W"66WFæ6R7V66W76gVÆÇ’7&÷72·V&W&æWFW2æBvVæW&Â”ÔÂÖöFW2Â–æ6ÇVF–ær66†VÖ×fÆ–BÂ66†VÖÖ–çfÆ–BÂVç7W÷'FVBÂVæf–Æ&ÆRÔ5$BÂæB”ÔÂ×7–çF‚7FFW2à¢ÒÖ&¶VB"32&VG’öæÇ’gFW"'&÷w6W"66WFæ6S²—BÖW&vVBBf3fCà ¢222æW‡B6ÖÆÂ7FW  ¤&Vv–âÖ–ÆW7FöæR3r2&÷VæFVBÂ–ææVBõt5·V&W&æWFW2F÷£##R&Wf–Wr&öf–ÆRâ&W6W'fR'&÷w6W"ÖÆö6Â&ö6W76–æræBÆ&VÂF—&V7BÂ'F–ÂÂæB6ÇW7FW"Ö6öçFW‡B×&WV—&VB6÷fW&vRW‡Æ–6—FÇ’à ¢ÒÒĞ ¢22##bÓ’Ó2ÒÖ–ÆW7FöæR3r–ææVBõt5·V&W&æWFW2&Wf–Wr&öf–ÆP ¢222v†B’v÷&¶VBöà ¤W‡æFVBf÷&vR”ÔÂv÷&¶&Væ6‚g&öÒ–æF—f–GVÂ³&VfW&Væ6W2–çFòFVâÖ6FVv÷'’õt5·V&W&æWFW2F÷£##R&Wf–Wr&öf–ÆR–ææVBFòâW†7BW7G&VÒ6öÖÖ—Bà ¢222v†B’ÆV&æV@ ¢Ò6÷fW&vRæB÷WF6öÖR&RF–ffW&VçB6öæ6WG3¢6FVv÷'’6â†fRF—&V7B÷"'F–ÂÖæ–fW7Bf—6–&–Æ—G’v—F†÷WB76–ær6V7W&—G’76W76ÖVçBà¢ÒVffV7F—fR$$2ÂFÖ—76–öâÂæWGv÷&¶–ærÂ6ö×öæVçBÂWF†VçF–6F–öâÂ6Æ÷VBÂVF—BÂÆövv–ærÂæBÖöæ—F÷&–ær7FFR6ææ÷B&R–æfW'&VB6fVÇ’g&öÒ7FVBf–ÆRà¢ÒöæRÖæ–fW7B6öæF—F–öâ6â–æf÷&Ò×VÇF—ÆR&—6·2Â6òF†RT’æVVG26†&VBÖ–æw2v—F†÷WBGWÆ–6F–ærF†RVæFW&Ç––ærf–æF–ærà¢Ò¦W&òÖF6†–ær6–væÇ2×W7B&RÆ&VÆVBW‡Æ–6—FÇ’2(	Ææ÷B72&W7VÇBî(	Ğ ¢222v†B’f–æ—6†VBÆö6ÆÇ ¢Ò–ææVBÆÂFVâõt56FVv÷'’Æ–æ·2FòW7G&VÒ6öÖÖ—Bƒ#†6f&S&Cvcc66Fcs#V3–6ƒs#cVCscS–6à¢ÒÆ&VÆVB³F—&V7C²³"Ô³bÂ³‚ÂæB³’'F–Ã²æB³rÇW2³6ÇW7FW"Ö6öçFW‡B×&WV—&VBà¢ÒFFVB&÷VæFVB$$2Â6V7&WBÖVçf—&öæÖVçBÂæÖW76RöÆ–7’ÖÆ&VÂÂW‡FW&æÂÖW‡÷7W&RÂæBÆ—FW&Â6Æ÷VBÖ7&VFVçF–Âf–æF–æw2à¢ÒFFVB6†&VB³ô³’æB³2ô³‚Ö–æw2à¢Ò&VæFW&VBF†RFVâÖ6FVv÷'’&öf–ÆRgFW"F†RW†—7F–ær7–çF‚Â÷W&F–öæÂÂæB66†VÖ6V7F–öç2à¢Ò&W6W'fVBvVæW&Â”ÔÂ7W&W76–öâæBF†RæòÖ&6¶VæBÂæòÖ6ÇW7FW"Ö66W72&÷VæF'’à¢ÒW‡æFVBWFöÖFVB6÷fW&vRg&öÒC"FòC’76–ærFW7G2à¢Ò76VBfÆ–FF÷"&W&öGV6–&–Æ—G’ÂF†Rsbã32´"òãC"´"w¦—&öGV7F–öâ'V–ÆBÂF†R5566âÂ¦W&ò×gVÆæW&&–Æ—G’FWVæFVæ7’VF—BÂ&W÷6—F÷'’Öæ–fW7BfÆ–FF–öâÂæBv†—FW76RfÆ–FF–öâà¢ÒV&Æ—6†VBG&gB"3BgFW"W‡Æ–6—B&÷fÃ²ÆÂ’&VÖ÷FRf–ÆW2ÖF6†VBF†RfW&–f–VBÆö6Â6öçFVçG2æBÆÂF‡&VRæöâ×V&Æ—6†–ærv÷&¶fÆ÷w276VBà¢ÒV&Æ—6†VBF†R6W&FVÇ’&÷fVBãRãÔCcBô$ÓcB–ÖvR–â'Vâ3Csƒs#Ss3&à¢ÒfW&–f–VBô4’–æFW‚6†#Sc£S†f63C“ƒ–fSvF6F33S3#sƒf#ƒƒ–“†#f–6#ƒ&S“s–ƒ#3VCsSff6#†VÂÔCcBÖæ–fW7B6†#Sc£&Cs#–csccsS“SF6SVS“#vSFFfSC&&F#v6SSƒSf66C&cCCsƒ##3&VÂæB$ÓcBÖæ–fW7B6†#Sc¦cFSƒ“c&c&FSƒ“fCƒ“vS&f66SvCS#Ccƒƒ3“–fVSfVS6V6ccsv#6à¢Ò7FvVBæB6W&FVÇ’FWÆ÷–VBF†R–Ö×WF&ÆRãRã6æF–FFRà¢ÒfW&–f–VBF†RÆ—fRöB—2&VG’v—F‚¦W&ò&W7F'G2Â—G26öæf–wW&VBæB'VçF–ÖR–ÖvT”BÖF6‚F†R&Wf–WvVBô4’–æFW‚ÂF†RVæGö–çE6Æ–6R†2öæR&VG’FG&W72Âö†VÇF‡¦æBF†RvR&WGW&â…EE#ÂæBF†R7G&–7B6V7W&—G’†VFW'2&VÖ–â&W6VçBà¢Ò'&÷w6W"66WFæ6R6öæf—&ÖVBF†Rõt5&öf–ÆRæBvVæW&Â”ÔÂ—6öÆF–öâÂF†Vâf÷VæBF†B”ÔÂF‚÷"Æ–æRö6öÇVÖâ6öçG&öÂ6VÆV7FVBF†R6÷'&V7BFW‡Bv—F†÷WB67&öÆÆ–ærF†RVF—F÷"Fò—Bà¢ÒFFVB6VçFW&VBVF—F÷"67&öÆÆ–æræBÆöærÖÖæ–fW7B'&÷w6W"&Vw&W76–öâFW7B2Æö6ÂF6‚6æF–FFRãRã²SFW7G2Â&öGV7F–öâ'V–ÆBÂæB5566â72à¢ÒV&Æ—6†VBF†R6W&FVÇ’&÷fVBãRãÔCcBô$ÓcBF6‚–ÖvR–â'Vâ3Csƒ“#3“&à¢ÒfW&–f–VBô4’–æFW‚6†#Sc£CCs†FS3vc“3fCcS“ƒVcvCƒvC3cS##6S&&6ffCsVVS#“cCfFF6CS&cFffÂÔCcBÖæ–fW7B6†#Sc¦V&C#SS3“cf–C†cvfCS6FfC&3ScSSfFcƒsSsFcfF#ƒ3ScC“ƒCVCVÂæB$ÓcBÖæ–fW7B6†#Sc¦&f&CvcCcƒcVF#ƒ†C†#Ss“SFF3F33&FF6#ssS3“#6Sc36#f6#&Sƒ#3†à¢Ò7FvVBæB6W&FVÇ’FWÆ÷–VBF†R–Ö×WF&ÆRãRãF6‚à¢ÒfW&–f–VBF†R6÷'&V7FVBöB—2&VG’v—F‚¦W&ò&W7F'G2Â—G26öæf–wW&VBæB'VçF–ÖR–ÖvT”BÖF6‚F†R&Wf–WvVBô4’–æFW‚Â†VÇF‚æBvR&WVW7G2&WGW&â…EE#ÂæBF†R7G&–7B6V7W&—G’†VFW'2&VÖ–â&W6VçBà¢Ò&WVFVBÆ—fR'&÷w6W"66WFæ6RæB6öæf—&ÖVBf–æF–ærÆ–æ·2æ÷rWFöÖF–6ÆÇ’67&öÆÂFòæB6VÆV7BF†R6÷'&V7B”ÔÂÆö6F–öâà¢ÒÖ&¶VB"3B&VG’öæÇ’gFW"6÷'&V7FVB'&÷w6W"66WFæ6RÂF†Vâ7V6‚ÖÖW&vVB—BBFCCf†à¢Ò÷7BÖÖW&vRv÷&¶&Væ6‚4’'Vâ3Csƒ““csSƒ†Â·V&W&æWFW2Öæ–fW7BfÆ–FF–öâ'Vâ3Csƒ““cscS&ÂæB&W7FW&çB’Fö6¶W"'V–ÆB'Vâ3Csƒ““cscSv76VBöâÖ–æà ¢222æW‡B6ÖÆÂ7FW  ¥6VÆV7BF†RæW‡B&÷VæFVBÖ–ÆW7FöæRg&öÒF†R&öFÖv†–ÆR&W6W'f–ærF†Rv÷&¶&Væ6‚G'W7B&÷VæF'’æBvFVB&VÆV6Rv÷&¶fÆ÷rà