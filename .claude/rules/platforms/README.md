# rules/platforms/

Empty on purpose. These sims are local desktop Python — no cloud runtime, no deploy target, no
mobile platform. Add a file here only if that changes (e.g. packaging for distribution).

The one platform-ish quirk lives in `.claude/skills/verify/SKILL.md`: pygame opens real windows, so
headless/CI runs need `SDL_VIDEODRIVER=dummy` and `MPLBACKEND=Agg`.
