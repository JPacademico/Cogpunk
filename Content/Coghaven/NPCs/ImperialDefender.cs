using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent.Bestiary;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using R = Cogpunk.Content.Coghaven.NPCs.ImperialDefenderRigData;

namespace Cogpunk.Content.Coghaven.NPCs
{
	/// <summary>
	/// Imperial Defender (Defensor Imperial), a Coghaven enemy (user-set 2026-11-06: "an imperial guard robot with a dadao
	/// sword that causes heavy contact damage and sometimes stops to parry attacks and projectiles for 2 seconds, once every
	/// 8 seconds"). He marches at his target with the dadao carried low (heavy contact damage). Once every
	/// <see cref="ParryEvery"/> ticks (8 s), with a target within <see cref="GuardRange"/>, he plants his feet facing it,
	/// sweeps the blade up into an upright guard (<see cref="GuardInTicks"/>), holds it for <see cref="ParryTicks"/> (2 s)
	/// and lowers it (<see cref="GuardOutTicks"/>).
	/// <para>While the guard is up, every hit from in front of him is parried: 1 damage (vanilla's floor), no knockback, no
	/// crit, no number; a free-flying projectile that strikes the blade is knocked away (destroyed). Minions, sentries,
	/// whips, yoyos, flails, spears and other held weapons are only blunted, never destroyed. A clang, sparks off the blade
	/// and a "Parried!" tell every player. My call: the guard covers his front and his feet stay planted, so a hit from
	/// behind (a second player, or a jump over him) lands in full.</para>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; Coghaven is a T4 area, user-set 2026-11-06: the anchor is the
	/// Demon, decompiled 1.4.4 NPC 62: 120 life / 8 defense / 32 contact in Classic = 240 / 8 / 64 in Expert):
	/// <see cref="Life"/> life, <see cref="Defense"/> defense, <see cref="ContactDamage"/> contact ("heavy"), knockback
	/// resistance <see cref="KnockbackResist"/>. Spawns only in Coghaven (<see cref="CoghavenSpawnRules.SpawnWeight"/>).</para>
	/// <para>D2: ai[0]/ai[1] state and timer, ai[2] the ticks marched since his last guard (random at spawn, so a squad
	/// doesn't guard in step); the server decides and every side reads the synced state. A hit is computed on the
	/// attacker's client (vanilla) from that state, and the parry's hidden number travels with the strike
	/// (<c>HitInfo.HideCombatText</c>, decompiled NetMessage), so <see cref="HitEffect"/> plays it on every client. The
	/// knocked-away projectile is killed by its owner's client, which syncs the kill. D1: no allocation; effects on
	/// clients only. Art: art/coghaven/make_imperial_defender_art.py.</para>
	/// </summary>
	public class ImperialDefender : GridWalkerNPC
	{
		private enum Phase { March, GuardIn, Guard, GuardOut }

		public const int Life = 300, ContactDamage = 80, Defense = 20;
		public const float KnockbackResist = 0.3f;
		public const float MarchSpeed = 1.3f, MarchAccel = 0.07f, JumpSpeed = 7f;
		public const int ParryEvery = 480, ParryTicks = 120;                // user-set: 2 s, once every 8 s
		public const int FrameTicks = 5;
		public const int GuardInTicks = R.GuardInFrames * FrameTicks, GuardOutTicks = R.GuardOutFrames * FrameTicks;
		public const int MarchTicks = ParryEvery - GuardInTicks - ParryTicks - GuardOutTicks;
		public const float GuardRange = 30f * 16f;
		public const float SpawnWeight = 1f;                                 // against the Jade Golem's in the island's own pool
		public const float Value = 600f;                                     // twice the Demon's (decompiled: value 300)
		private const int ParryTextCooldown = 30;

		private static readonly Color ParryColor = new(255, 199, 90);       // Ember (hostile, D3)
		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "ImperialDefender_GoreHelmet", "ImperialDefender_GoreSword", "ImperialDefender_GoreMirror" };

		private Phase CurrentPhase => (Phase)State;
		private ref float Marched => ref NPC.ai[2];
		private ref float ParryTextWait => ref NPC.localAI[0];              // client-only countdown between "Parried!" texts

		/// <summary>True while his guard is up (every side reads the synced state).</summary>
		public bool Guarding => CurrentPhase == Phase.Guard;

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<CoghavenBiome>().ModBiomeBestiaryInfoElement;

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			far = near = glow = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			CogpunkSets.Mechanical[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
		}

		public override void SetDefaults() {
			NPC.width = 28;                                 // the art's body: coat to boots, up to the helmet's brim (D4: matched hitbox)
			NPC.height = 72;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = Value;
			NPC.aiStyle = -1;
			SpawnModBiomes = new[] { ModContent.GetInstance<CoghavenBiome>().Type };
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			return CoghavenSpawnRules.SpawnWeight(spawnInfo, SpawnWeight);
		}

		public override void OnSpawn(IEntitySource source) {
			if (IsAuthority) {
				Marched = Main.rand.Next(MarchTicks);          // MarchTicks > 0 (const); synced with the spawn
				NPC.netUpdate = true;
			}
		}

		protected override void UpdateState() {
			if (ParryTextWait > 0f) {
				ParryTextWait--;
			}
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			switch (CurrentPhase) {
				case Phase.GuardIn:
					NPC.velocity.X *= 0.8f;
					if (IsAuthority && Timer >= GuardInTicks) {
						ChangeState((int)Phase.Guard);
					}
					break;
				case Phase.Guard:
					NPC.velocity.X *= 0.8f;                     // feet planted: he keeps the facing he raised the guard to
					if (IsAuthority && Timer >= ParryTicks) {
						ChangeState((int)Phase.GuardOut);
					}
					break;
				case Phase.GuardOut:
					NPC.velocity.X *= 0.8f;
					if (IsAuthority && Timer >= GuardOutTicks) {
						ChangeState((int)Phase.March);
					}
					break;
				default:
					Marched++;
					Run(target != null ? dir : 0, MarchSpeed, MarchAccel, JumpSpeed);
					FaceMotion(dir);
					if (IsAuthority && target != null && Marched >= MarchTicks && Grounded
						&& Vector2.DistanceSquared(target.Center, NPC.Center) < GuardRange * GuardRange) {
						Marched = 0f;
						NPC.direction = NPC.spriteDirection = dir;
						ChangeState((int)Phase.GuardIn);
					}
					break;
			}
			if (!Main.dedServ && CurrentPhase == Phase.GuardIn && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.Item1 with { Pitch = -0.3f, Volume = 0.6f }, NPC.Center);   // the blade swept up
			}
		}

		/// <summary>True if a hit coming from <paramref name="from"/> meets his raised guard (it comes from where he faces).</summary>
		private bool Parries(Vector2 from) {
			return Guarding && (from.X - NPC.Center.X) * NPC.direction >= 0f;
		}

		private static void Blunt(ref NPC.HitModifiers modifiers) {
			modifiers.SetMaxDamage(1);                      // vanilla's floor: a hit always deals at least 1
			modifiers.DisableCrit();
			modifiers.DisableKnockback();
			modifiers.HideCombatText();                     // also the parry's mark, synced with the strike
		}

		public override void ModifyHitByItem(Player player, Item item, ref NPC.HitModifiers modifiers) {
			if (Parries(player.Center)) {
				Blunt(ref modifiers);
			}
		}

		public override void ModifyHitByProjectile(Projectile projectile, ref NPC.HitModifiers modifiers) {
			if (Parries(projectile.Center)) {
				Blunt(ref modifiers);
			}
		}

		/// <summary>The owner's client (vanilla resolves friendly hits there): a free-flying projectile the blade parried is
		/// knocked away; its owner kills it, which syncs.</summary>
		public override void OnHitByProjectile(Projectile projectile, NPC.HitInfo hit, int damageDone) {
			if (hit.HideCombatText && Guarding && projectile.owner == Main.myPlayer && Deflectable(projectile)) {
				projectile.Kill();
			}
		}

		/// <summary>A projectile flying free of its owner: not a minion, sentry, whip, yoyo, flail, spear, drill or any
		/// projectile the player is holding.</summary>
		private static bool Deflectable(Projectile p) {
			if (!p.active || !p.friendly || p.hostile || p.minion || p.sentry || p.ownerHitCheck || ProjectileID.Sets.IsAWhip[p.type]) {
				return false;
			}
			if (p.aiStyle == ProjAIStyleID.Yoyo || p.aiStyle == ProjAIStyleID.Flail || p.aiStyle == ProjAIStyleID.Spear
				|| p.aiStyle == ProjAIStyleID.Drill) {
				return false;
			}
			return p.owner < 0 || p.owner >= Main.maxPlayers || Main.player[p.owner].heldProj != p.whoAmI;
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.GuardIn:
					return R.GuardIn + Math.Min(R.GuardInFrames - 1, (int)(Timer / FrameTicks));
				case Phase.Guard:
					return R.Guard + (int)(Timer / 10f) % R.GuardFrames;
				case Phase.GuardOut:
					return R.GuardOut + Math.Min(R.GuardOutFrames - 1, (int)(Timer / FrameTicks));
			}
			if (!Grounded) {
				return R.Walk + 1;
			}
			if (Math.Abs(NPC.velocity.X) > 0.2f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= R.WalkStep * R.WalkFrames) {
					NPC.frameCounter -= R.WalkStep * R.WalkFrames;
				}
				return R.Walk + (int)(NPC.frameCounter / R.WalkStep) % R.WalkFrames;
			}
			return R.Idle + (int)(Timer / 24f) % R.IdleFrames;
		}

		/// <summary>Where the raised blade's middle is (sparks fly from there).</summary>
		private Vector2 BladePoint => NPC.Bottom + new Vector2(R.GuardBladeX * -NPC.direction, R.GuardBladeY);

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			if (hit.HideCombatText && Guarding && NPC.life > 0) {
				Parried();
				return;
			}
			int count = NPC.life > 0 ? 3 : 14;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Gold : DustID.Iron, out _);
			}
			if (NPC.life > 0) {
				return;
			}
			for (int i = 0; i < GoreNames.Length; i++) {
				if (Mod.TryFind(GoreNames[i], out ModGore gore)) {
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.Center, NPC.velocity * 0.4f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
				}
			}
		}

		/// <summary>A parried hit (clients): the clang, sparks off the blade, "Parried!" at most every
		/// <see cref="ParryTextCooldown"/> ticks.</summary>
		private void Parried() {
			Vector2 at = BladePoint;
			SoundEngine.PlaySound(SoundID.Item37 with { Pitch = 0.5f, Volume = 0.8f, MaxInstances = 3 }, at);
			int sparks = CogpunkClientConfig.RollEffect() ? 6 : 2;
			for (int i = 0; i < sparks; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(4f), 8, 8, DustID.Torch, out Dust d)) {
					d.noGravity = i % 2 == 0;
					d.velocity = new Vector2(NPC.direction * Main.rand.NextFloat(1.5f, 4f), Main.rand.NextFloat(-3f, 0.5f));
					d.scale = 1.2f;
				}
			}
			if (ParryTextWait <= 0f) {
				ParryTextWait = ParryTextCooldown;
				CombatText.NewText(NPC.Hitbox, ParryColor, Language.GetTextValue("Mods.Cogpunk.NPCs.ImperialDefender.Parried"));
			}
		}
	}
}
