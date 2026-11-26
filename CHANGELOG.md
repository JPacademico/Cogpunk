# Cogpunk changelog

Every update batch raises `version` in `build.txt` and adds an entry here, newest first: a content batch the minor number,
fixes and tweaks only the patch (user, 2026-11-26: "every following update batch and implementation should increase the
version of our mod so we keep traceability for updates"). Balance rows: `docs/balance/*.csv`; proofs: `docs/media/`.

## 0.2.1 (2026-11-26)

### Changed
- **Bundle of Wands**: 25 mana a shot (28).
- **Cursed Lantern**: 16 mana a cast (7 since 0.2.0, 10 before).

## 0.2.0 (2026-11-26)

### New
- **Artifacts**: once-per-world rare drops and secret items with the artifact tag and a jade-gold rarity. They can't be
  combined at the Combinator or stolen by Delivery Drones, can't be duplicated in Journey mode, and only one artifact
  accessory can be worn at a time. A character's first pickup of each artifact gives a knowledge point and opens the
  research window's new **Artifacts** tab (a record per artifact, "?" until found). Balance: up to 80% over their
  category's anchor (D3 rule 11).
- **Jade Cursed Glaives** are now an artifact: no longer from Jadey, 1% from any enemy killed while turned to jade (once
  per world), +30% damage (27 -> 35).
- **Research nodes**: Passive Income ("?" until a piggy bank is opened; 1 point: the piggy bank makes a copper coin a
  second), Twinkling ("?" until a Crystal Lizard is killed; 1 point: rarer gems on lizards, 1-3 more gold), You Broke It!
  ("?" until an item is reforged; 30 Rusted Cogs: reforging an item with a negative modifier costs 40% less) and, under it,
  Build Terraria 2, make no mistakes. (1 point: negative modifiers rolled at the Goblin Tinkerer are rolled again a
  quarter of the time).
- **Cogfish**, caught in the Junkyard's tar pit, and the **Tar Immunity Potion** (Bottled Water, a Cogfish and 2 Tar Drops
  at a bottle: 4 minutes of immunity to the Tar Plague).

### Changed
- **Jade Golem** redrawn sideways (version 3, from the user's two references: the jade golem's look, the Ice Golem's
  side-on stance): emerald stone plates, a profile Moai head with one glowing eye, rune bands on the wrists, a bronze belt
  with its glowing core in the disc, a skirt of stone leaves; its aiming arm (37 angles), its ray and its charge in the
  emerald glow. Hitbox 46 x 104 (72 x 104 facing the screen).
- **Jade Coin**: between fights each spirit is a jade coin floating over its owner's head; with an enemy in range it spins
  up and bursts into its creature (0.23 s), and back into a coin 0.75 s after its last target.
- **Crystal Lizard**: its back's crystals are the gem it drops (eight gems, the rarer ones less often), and now and then a
  hit makes it drop its tail, which lies twitching for 4 seconds while it runs.
- **Slow motion** (crit kills, the wrench's riposte): 0.7 s, eased in quickly and out smoothly over its last quarter
  second, and held entities glide between their updates instead of stuttering.
- **Boss music**: each boss its own vanilla boss track until its own exists (Trash-Tr0m Boss 1, Tar Tyrant Boss 3, Cursed
  Conductor Boss 5, Jadey Queen Slime, Fungimancer Boss 4).
- **Jadey's arena**: the Jade Vault is 60 x 19 tiles inside (48 x 16) in new worlds; her arena is measured from the vault
  itself, so older worlds keep theirs.
- **Cogscorpion**: 85% of its size, 320 life (380).
- **Cursed Lantern**: 7 mana a cast (10; 16 since 0.2.1).
- **Rusted Cogs and Rusted Metal**: every recipe that takes them takes 20% more (rounded).

### Fixes (the 2026-11-26 playtest)
- The Ancient Research Table and the Combinator no longer close as they open; the Cogspring Sword's swing no longer drains
  the steam; Metal Wrench and Jade Cursed Glaives aim at the cursor; Rust Collectors jump; Living Tar faces the player;
  the Junkyard's water is tar; Cogscorpions walk forwards; Coghaven's arches can be walked through; the Tar Tyrant's claw
  is no longer cut by the ground; the steam gauge fills smoothly; drones never steal manuals.
- Balance: Trash-Tr0m slams more and never sucks twice in a row (and no longer leaves or enrages outside the Junkyard);
  Metal Wrench 34 and its parry removed; Jade Refractor 1 steam, Diamond Cutter 3 steam; Jade Coin's golem became a
  floating arm; Serene Tear lost its steam regeneration; +5 max steam on every item that gives it.

## 0.1.0 (2026-11-25)

The alpha: quality-of-life recipes at the demon altar and the Demon Table, banners for every enemy, knowledge-point tasks,
the economy pass, crit-kill slow motion, the Fungimancer, the Crystal Lizard, the Driller and the Toadstool, the Cogpunk
slot (locked), and the alpha description.
