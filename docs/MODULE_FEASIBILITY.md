# Requested module feasibility — Pocket Realm Vanilla+

Inspected 2026-10-14 against app `de00653c54a283ff73431db86a3b526ac6283ea5`,
CMaNGOS `1d2c026013ed9d75f4449b1dcdbfe4900c08747c` and Playerbots
`9c3bf0d15a8618a9c61181a2cb67b81e65b0b92a`.
This is source inspection and a patch dry run, not an Android compilation or
device compatibility result. No module was applied to the baseline.

The user's current requirements are Hardcore, Transmog, Dual Spec and the entire
Balancing module. Bots may inherit shared balancing changes and need not learn
or use extra spells; human-only balancing isolation is no longer required.
Potentially human-only Classless remains optional. Full Balancing remains the
first requested gameplay integration after a working baseline; its scope must
not be narrowed to one class. Classless coexistence with normal characters is
not assumed. See the current [checkpoint](../CHECKPOINT.md).

## Assessment

Effort below is relative and assumes the shared framework has already been
ported and qualified. None is a switch available in our present core.

| Module | Relative effort | What needs integrating | Bot implications |
|---|---|---|---|
| Dual Spec | Lower–moderate | NPC/item gossip, talent/spell switching, four character tables, per-spec action bars, world SQL and config. README does not require a client MPQ/addon. | Existing guards skip free bots, which is narrower than all bot-controlled characters. Check owned/alt bots and strengthen eligibility. |
| Transmog | Moderate | Appearance/equipment hooks, discovered/active appearance tables, world NPC data, config and the included 1.12 addon. | Already skips free bots at many hooks; audit all command and save/load paths for the same human-only policy. Cosmetics should not change combat stats. |
| Hardcore | Moderate | Death/resurrection hooks, persistent per-character challenge settings, death logs, optional dropped loot/graves, config and SQL. Client patch adds challenge/self-found auras. | Source explicitly lets bots revive and provides separate bot drop rates. Keep those rates zero unless requested. Self-found/group restrictions must be configured to allow intended companion play. |
| Full Balancing, shared with bots | Moderate–high | Custom effects/procs, all affected classes, books and loot, SQL, locale-specific client MPQ/DBC changes and bot compatibility testing. | Shared spell changes are acceptable. Bot stability matters; learning/using extra spells is optional. No human-only isolation is required. |
| Classless, human-only | High / experimental | Finish and repair implementation, human eligibility, optional per-character enrollment, skill/spell/talent and resource rules, discovery content, addon and persistence design. | Human checks exist, but contain source-level compile problems. Current global enable applies to eligible humans generally; no durable character opt-in was found. |

Sources: [framework](https://github.com/flekz-games/cmangos-modules),
[Dual Spec](https://github.com/flekz-games/cmangos-dualspec),
[Transmog](https://github.com/flekz-games/cmangos-transmog),
[Hardcore](https://github.com/flekz-games/cmangos-hardcore),
[Balancing](https://github.com/flekz-games/cmangos-balancing),
[Classless](https://github.com/flekz-games/cmangos-classless).

## Shared framework prerequisite

The framework is compiled into the core through hooks; this is not a runtime
plugin loader. Its documentation offers a premerged core or a patch and warns
that patching newer core revisions can fail. Replacing our Android core with
the premerged core would discard Pocket Realm's adaptations and is not the
integration strategy.

The published `patches/classic.patch` touches 35 files. Running `git apply
--check` against our unmodified core fails in `src/game/Entities/Player.cpp`
and `src/game/World/World.cpp`. The patch is also older than the current hook
API: hooks used by today's modules, including `OnGetSpellRank`, `OnProc`,
`OnPeriodicTick`, `OnRegenerate`, `OnSetPower` and
`OnGetPlayerClassLevelInfo`, are absent from that patch. A successful manual
resolution of the two reported files would not establish complete support.

Port the required hook set from a pinned framework/core revision into our
existing core. The framework's `main` and its module FetchContent references
must become exact pins or prepopulated source directories. Preserve the
existing Playerbots source pin rather than allowing configure-time refetches.

Pocket Realm links `pocket_world_runtime` rather than relying on the normal
`mangosd` executable. The modules' link dependencies and compile definitions
must reach that library. Config loading currently assumes `SYSCONFDIR`; wire
the staged configs into the supervisor's managed runtime generation. Check
registration/start/stop lifetime: framework `OnWorldPreInitialized()` calls
`AddModules()` on every invocation, so repeated embedded startup must not
accumulate duplicate module objects or stale per-player state.

Append module SQL to Pocket Realm's verified migration ledger. Do not run the
modules' destructive install/uninstall SQL blindly on existing saves. Include
new character tables in backup/restore and persistence checks. The currently
selected MariaDB lane should be qualified first; SQLite compatibility is a
separate task rather than an implied side effect.

## Balancing scope and optional human-only isolation

Current plan: integrate normal shared balancing behavior and verify bot
compatibility. Bots are allowed to benefit from modified existing spells and
talents without using extra abilities. No confirmed general incompatibility
was found. Playerbots uses core spell data and casting checks, although the
presence of an AI action with a matching spell name does not prove its Classic
rotation supports the module's custom version. Separate human-only behavior
below is a possible future design, not a delivery prerequisite.

The inspected SQL introduces 54 spell-template rows in IDs 33393–33446 and
contains 82 UPDATE statements against existing spell templates. It also adds
books, item locales, proc data and creature loot. Existing spell IDs are shared
by humans, bots and, where applicable, creatures. The sole config switch is
`Balancing.Enable`; the C++ handlers have no bot eligibility checks. A helper
also mutates a shared `SpellEntry` when cloning a spell, which requires review
before claiming isolation.

Preserve the full implementation for all eight affected classes: Paladin,
Druid, Shaman, Hunter, Priest, Warrior, Warlock and Mage. Coverage includes
new spells, changed talents, resource/cost/cooldown behavior, proc and periodic
effects, book discovery/loot and matching SQL/client data. The README at the
inspected revision does not list Rogue changes.

If human-only isolation is later requested, a candidate architecture is
per-caster overrides or separate human spell/talent variants, retaining
original templates for bots. This is a design proposal,
not a proven solution. Audit rank chains, learning, talent selection, cooldown
categories, auras, pets/totems and triggered casts; matching MPQ/DBC changes
must agree with the server's selected implementation. Do not globally mutate
the original templates and then rely on a bot guard to undo their effects.

For that optional isolation design, use a single tested eligibility policy
for random bots, owned bots and alts;
the modules' `IsFreeBot` and `isRealPlayer` predicates have different meanings.
Block bots from learning/using the new books and spells while retaining normal
AI. A human's modified buff may still affect bot companions as a spell target;
preserving their own vanilla spellbook/AI is distinct from making them immune
to every human-originated effect. Decide and test the desired target semantics.

Bot breakage has not been demonstrated. What is verified is the shared-data
exposure and the absence of an upstream human-only option. Test bot costs,
cooldowns, talents and rotations against the intended balanced data, then
cover human direct, proc, periodic and owned-unit casts across the complete
module. Bots failing to use an extra spell is acceptable under the current scope.

## Classless readiness

The README describes blank starting characters and spell-book progression,
recommending Warrior as the base. At the inspected revision the install and
uninstall world SQL files are empty, and the visible implementation centers
on resource regeneration, base mana and the `ClasslessPowerBars` 1.12 addon.
No complete book/discovery or blank-spellbook implementation was found there.
The inspected premerged core files still call normal default skill/spell
learning and do not establish the advertised complete mode by themselves.

Several `ENABLE_PLAYERBOTS` branches use `return false` inside void resource
hooks or pointer-returning helpers. Those paths need correction and actual
compilation with bots enabled. CMake also defines `ENABLE_BALANCING` in the
Classless target, a likely copied setting that needs review.

There is only a global `Classless.Enable`; no persistent per-character mode
selector was found. Keeping normal human characters alongside classless ones
therefore needs explicit enrollment state and consistently gated hooks. Keeping
bots normal is a separate requirement. Combining Classless with Dual Spec and
Balancing adds talent, action-bar, power-type and spell-ownership interactions.

## Recommended next patch and validation order

Finish the baseline APK and Thor qualification first. Then add a pinned,
disabled-by-default framework port with no gameplay module enabled; confirm
realm boot, clean stop, persistence and bot parity. Full shared Balancing
remains the first requested gameplay module, with compatibility checks for bots.
Dual Spec, Transmog and Hardcore are required additions after the framework;
Classless stays last, optional and experimental.

Each module gets its own build/config/migration switch and rollback record.
Changes to the user's managed client copy belong in a reversible, hash-verified
patch/import flow, not in the original client or bundled Blizzard assets.
Do not overwrite user addon/controller bindings. Qualify controller navigation
through the new gossip/addon UI on the Thor.

## Inspected source revisions

| Repository | Revision |
|---|---|
| cmangos-modules | `f917cf5338d4eae191cb45fa6928db6941154670` |
| mangos-classic, modules branch | `eed033b751f6bc68d49fe9e18fc79d126a10a4e7` |
| cmangos-hardcore | `fe5033afe516f10501bea515d1b8e8b4dd0933fa` |
| cmangos-transmog | `0abf98b38e80724b5a2847b029ccf72e09d98ef2` |
| cmangos-dualspec | `b211cbab0ee6767a065e0817507aaaa045550651` |
| cmangos-balancing | `ca556e406bdfd97cfcbcad4f171573d2d44776f7` |
| cmangos-classless | `59e91b4948c0339afa3aac3a74aa0f5e553ea997` |
