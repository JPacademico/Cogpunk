using System;
using Cogpunk.Content.Desert.Items;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Desert.NPCs.CoghawkRigData;

namespace Cogpunk.Content.Desert.NPCs
{
	/// <summary>
	/// Coghawk (user-set 2026-11-03: "a new enemy for the desert that attacks with a quick swoop that can be dodged by
	/// jumping, a bit stronger than the vulture"): a hawk of brass and iron built round a cog. It circles above its target,
	/// <see cref="HoverHeight"/> up and <see cref="HoverSide"/> to the side; every <see cref="SwoopCooldown"/> ticks, with the
	/// target in sight and in <see cref="SwoopRange"/>, it screeches and flares its wings (the telegraph,
	/// <see cref="WindupTicks"/> ticks, flying to the top of its arc), then swoops: a parabola <see cref="SwoopTicks"/> ticks
	/// long, <see cref="SwoopHalfWidth"/> to each side of its lowest point, which is locked on the target's feet as the
	/// windup ends. At the bottom it skims <see cref="SkimHeight"/> px over the ground with its talons out, so a jump clears
	/// it (its hitbox is <see cref="Height"/> px tall; a jump lifts the feet ~6 tiles). Then it climbs away and circles again.
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor the Vulture, decompiled 1.4.4 NPC 61: 40 life, 4
	/// defense, 15 contact in Classic = 80 / 4 / 30 in Expert): <see cref="Life"/> life, <see cref="Defense"/> defense,
	/// <see cref="ContactDamage"/> contact. Spawns on the desert's surface (<see cref="SpawnWeight"/>), day and night. Drops
	/// the Vulture's coins, 1-2 Rusted Cogs and, 1 in <see cref="HawkEyeOdds"/> (user-set 10%, 2026-11-04), the
	/// <see cref="HawkEye"/>.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer; the server targets and decides; during the windup <c>ai[2]</c> is
	/// the swoop's side, during the swoop <c>ai[2]</c> = side x the low point's x and <c>ai[3]</c> its y (locked by the server,
	/// synced with the state change); every side steers along the same arc from them. D0: the ground search is bounded and
	/// goes through <see cref="TileSafety"/>; a blocked swoop gives up. D1: no allocation; sounds and dust on clients.</para>
	/// </summary>
	public class Coghawk : GridWalkerNPC
	{
		private enum Phase { Hover, Windup, Swoop, Recover }

		public const int Life = 100, ContactDamage = 36, Defense = 6;   // Expert
		public const int Width = 36, Height = 26;
		public const float KnockbackResist = 0.7f;
		public const float HoverHeight = 10f * 16f, HoverSide = 8f * 16f;
		public const float HoverSpeed = 4.5f, HoverAccel = 0.14f;
		public const int SwoopCooldown = 150;
		public const float SwoopRange = 32f * 16f;
		public const int WindupTicks = 30;
		public const int SwoopTicks = 48;
		public const float SwoopHalfWidth = 14f * 16f, SwoopDepth = 9f * 16f;
		public const float SkimHeight = 4f;
		public const float SwoopMaxSpeed = 16f;
		public const int RecoverTicks = 40;
		public const int GroundSearchTiles = 8;
		public const int FlapTicks = 5, ScreechTicks = 4;
		public const float SpawnWeight = 0.15f;
		public const int HawkEyeOdds = 10;                 // 10% (user-set 2026-11-04)

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "Coghawk_GoreHead", "Coghawk_GoreWing", "Coghawk_GoreCog" };

		private Phase CurrentPhase => (Phase)State;

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Desert;

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
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.noGravity = true;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 60f;                                // the Vulture's (decompiled NPC.SetDefaults, type 61)
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player player = spawnInfo.Player;
			return player.ZoneDesert && player.ZoneOverworldHeight && !player.ZoneBeach && !spawnInfo.PlayerInTown && !spawnInfo.Water
				? SpawnWeight : 0f;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedCog>(), 1, 1, 2));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<HawkEye>(), HawkEyeOdds));
		}

		protected override void UpdateState() {
			Retarget();
			Player target = Target;
			if (target == null) {
				NPC.velocity.Y = Math.Max(NPC.velocity.Y - 0.1f, -HoverSpeed);   // nothing to hunt: it climbs away
				NPC.EncourageDespawn(10);
				FaceMotion(NPC.direction == 0 ? -1 : NPC.direction);
				return;
			}
			switch (CurrentPhase) {
				case Phase.Windup:
					DoWindup(target);
					break;
				case Phase.Swoop:
					DoSwoop();
					break;
				case Phase.Recover:
					NPC.velocity.X *= 0.97f;
					NPC.velocity.Y = Math.Max(NPC.velocity.Y - 0.3f, -HoverSpeed);
					if (IsAuthority && Timer >= RecoverTicks) {
						ChangeState((int)Phase.Hover);
					}
					FaceMotion(NPC.direction == 0 ? -1 : NPC.direction);
					break;
				default:
					DoHover(target);
					break;
			}
		}

		private void DoHover(Player target) {
			float side = NPC.Center.X >= target.Center.X ? 1f : -1f;
			Vector2 goal = target.Center + new Vector2(side * HoverSide, -HoverHeight + (float)Math.Sin(Timer * 0.05f) * 12f);
			if (NPC.collideX || NPC.collideY) {
				goal.Y -= 64f;                               // blocked by the ground or a wall: up and over
			}
			Vector2 want = (goal - NPC.Center).SafeNormalize(Vector2.Zero) * HoverSpeed;
			NPC.velocity = Vector2.Lerp(NPC.velocity, want, HoverAccel);
			FaceMotion(target.Center.X >= NPC.Center.X ? 1 : -1);
			if (IsAuthority && Timer >= SwoopCooldown && Vector2.DistanceSquared(target.Center, NPC.Center) < SwoopRange * SwoopRange
				&& Collision.CanHitLine(NPC.position, NPC.width, NPC.height, target.position, target.width, target.height)) {
				ChangeState((int)Phase.Windup);
				NPC.ai[2] = target.Center.X >= NPC.Center.X ? 1f : -1f;   // the side it swoops towards (synced with the change)
			}
		}

		/// <summary>The telegraph: it screeches, flares and flies to the top of its arc over the target (every side, from the
		/// target's synced position), then the server locks the low point and starts the swoop.</summary>
		private void DoWindup(Player target) {
			int dir = NPC.ai[2] >= 0f ? 1 : -1;
			Vector2 low = LowPoint(target);
			Vector2 start = low + new Vector2(-dir * SwoopHalfWidth, -SwoopDepth);
			Vector2 want = (start - NPC.Center).SafeNormalize(Vector2.Zero) * Math.Min(HoverSpeed * 1.6f, Vector2.Distance(start, NPC.Center) * 0.2f);
			NPC.velocity = Vector2.Lerp(NPC.velocity, want, 0.2f);
			NPC.direction = NPC.spriteDirection = dir;
			if (Timer == 1f && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.DD2_WyvernScream with { Pitch = 0.5f, Volume = 0.55f, MaxInstances = 3 }, NPC.Center);
			}
			if (IsAuthority && Timer >= WindupTicks) {
				ChangeState((int)Phase.Swoop);
				NPC.ai[2] = dir * low.X;
				NPC.ai[3] = low.Y;
			}
		}

		/// <summary>Steers along the arc: the point a tick ahead, its velocity capped. A blocked swoop (a hill in the way)
		/// gives up and climbs.</summary>
		private void DoSwoop() {
			int dir = NPC.ai[2] >= 0f ? 1 : -1;
			Vector2 low = new(Math.Abs(NPC.ai[2]), NPC.ai[3]);
			if (Timer == 1f && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.DD2_WyvernDiveDown with { Pitch = 0.3f, Volume = 0.7f, MaxInstances = 3 }, NPC.Center);
			}
			float u = Math.Min(1f, (Timer + 1f) / SwoopTicks);
			float s = 2f * u - 1f;
			Vector2 next = low + new Vector2(dir * SwoopHalfWidth * s, -SwoopDepth * s * s);
			Vector2 step = next - NPC.Center;
			if (step.LengthSquared() > SwoopMaxSpeed * SwoopMaxSpeed) {
				step = step.SafeNormalize(Vector2.Zero) * SwoopMaxSpeed;
			}
			NPC.velocity = step;
			NPC.direction = NPC.spriteDirection = dir;
			if (IsAuthority && (Timer >= SwoopTicks || (Timer > 4f && (NPC.collideX || NPC.collideY)))) {
				ChangeState((int)Phase.Recover);
			}
		}

		/// <summary>The swoop's lowest point: over the target, its hitbox bottom <see cref="SkimHeight"/> px above the ground
		/// under the target's feet (within <see cref="GroundSearchTiles"/> tiles), else above the feet themselves.</summary>
		private static Vector2 LowPoint(Player target) {
			float feet = target.Bottom.Y;
			int x = (int)(target.Center.X / 16f);
			int y0 = (int)(feet / 16f);
			for (int k = 0; k < GroundSearchTiles; k++) {
				if (TileSafety.TryGetTile(x, y0 + k, out Tile tile) && tile.HasTile && (Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType])
					&& !tile.IsActuated) {
					feet = (y0 + k) * 16f;
					break;
				}
			}
			return new Vector2(target.Center.X, feet - SkimHeight - Height * 0.5f);
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Windup:
					return R.Screech + (int)(Timer / ScreechTicks) % R.ScreechFrames;
				case Phase.Swoop:
					return NPC.velocity.Y > 2f ? R.Dive : (NPC.velocity.Y < -2f ? R.Climb : R.Skim);
				case Phase.Recover:
					return R.Flap + (int)(Timer / (FlapTicks - 2)) % R.FlapFrames;
			}
			if (NPC.velocity.Y > 1.2f) {
				return R.Glide;
			}
			return R.Flap + (int)((Timer + NPC.whoAmI * 3) / FlapTicks) % R.FlapFrames;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 14;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Copper : DustID.Iron, out _);
			}
			if (NPC.life <= 0) {
				foreach (string name in GoreNames) {
					if (Mod.TryFind(name, out ModGore gore)) {
						SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.position + new Vector2(Main.rand.Next(NPC.width), Main.rand.Next(NPC.height)),
							NPC.velocity * 0.5f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
					}
				}
			}
		}
	}
}
