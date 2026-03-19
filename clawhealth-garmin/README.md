# clawhealth-garmin (Skill Package)

This is a lightweight OpenClaw skill package. It does **not** ship the
`clawhealth` source code; it downloads only `src/clawhealth` from GitHub at runtime.

- Main instructions: `SKILL.md`
- Repo overview (recommended reading): `https://github.com/ernestyu/clawhealth`
- Release checklist: `PUBLISH.md`

Quick smoke checks (repo fetch is skipped if not present):

```bash
python {baseDir}/validate_skill.py
python {baseDir}/test_minimal.py
```
