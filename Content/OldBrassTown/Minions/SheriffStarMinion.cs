using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.OldBrassTown.NPCs.SheriffRigData;

namespace Cogpunk.Content.OldBrassTown.Minions
{
	/// <summary>
	/// A deputy's sheriff star (the <see cref="SheriffBadge"/>'s minion; one minion slot): it floats over its owner's head,
	/// spinning, in a row with its fellows (a shallow arc, the middle ones highest), and every <see cref="AttackCycle"/> ticks
	/// (each star a little after the one before: <see cref="Stagger"/>) it flies at the enemy it has picked
	/// (<see cref="DashSpeed"/> for <see cref="DashTicks"/> ticks, through everything in its way, each enemy once a pass), then
	/// homes back to its place (<see cref="ReturnSpeed"/>), still hitting on the way: the Sheriff's own stars, turned to the
	/// law-abiding side (an aether gem instead of an ember one, D3's colours).
	/// <para>Targeting follows ExampleMod 1.4.4's <c>ExampleSimpleMinion</c>: the owner's whip or right-click target first,
	/// then the nearest chaseable enemy within <see cref="TargetRange"/> of the owner that the star can see; re-chosen every
	/// <see cref="RetargetInterval"/> ticks (D1). Summon damage skips vanilla's crit roll, so <see cref="ModifyHitNPC"/> rolls
	/// <c>CritChance</c> itself (the player's 4% base and summon bonuses), as the Mice-bot does.</para>
	/// <para>D2: <c>ai[0]</c> the mode, <c>ai[1]</c> its timer, <c>ai[2]</c> the dash's heading, all set by the owner's client
	/// and synced on change (<c>netUpdate</c>); every client runs the same motion. D0: NaN guarded, a teleport home past
	/// <see cref="TeleportDistance"/>. D1: no allocation; the place in the row is recounted every
	/// <see cref="RowRecount"/> ticks.</para>
	/// </summary>
	public class SheriffStarMinion : CogpunkProjectile
	{
		private enum Mode { Hover, Dash, Return }

		public const float MinionSlots = 1f;                  // user-set
		public const int AttackCycle = 56;
		public const int Stagger = 9;
		public const int MinHoverTicks = 6;
		public const float DashSpeed = 13f;
		public const int DashTicks = 22;                      // about 18 tiles of reach
		public const float ReturnSpeed = 14f;
		public const float HomeSnap = 10f;
		public const int HitCooldown = 20;
		public const float TargetRange = 40f * 16f;           // from the owner
		public const int RetargetInterval = 10;
		public const int RowRecount = 30;
		public const float RowSpacing = 24f;
		public const float HoverHeight = 30f;                 // over the owner's head
		public const float TeleportDistance = 2000f;
		public const int SpinTicks = 4, FastSpinTicks = 2;
		private const int Size = 26;

		private static Asset<Texture2D> glow;

		private int rowIndex, rowCount = 1, rowTimer;
		private int targetIndex = -1, retargetTimer;

		private Mode CurrentMode {
			get => (Mode)(int)Projectile.ai[0];
			set => Projectile.ai[0] = (float)value;
		}

		private ref float ModeTimer => ref Projectile.ai[1];
		private ref float Heading => ref Projectile.ai[2];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = R.StarSpin;
			Main.projPet[Type] = true;
			ProjectileID.Sets.MinionTargettingFeature[Type] = true;
			ProjectileID.Sets.MinionSacrificable[Type] = true;
			ProjectileID.Sets.CultistIsResistantTo[Type] = true;
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 20;
			Projectile.height = 20;
			Projectile.friendly = true;
			Projectile.minion = true;
			Projectile.minionSlots = MinionSlots;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = HitCooldown;
		}

		public override bool? CanCutTiles() => false;

		public override bool MinionContactDamage() => true;

		public override bool? CanDamage() => CurrentMode != Mode.Hover ? null : false;

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			int buff = ModContent.BuffType<SheriffStarBuff>();
			if (!owner.active || owner.dead) {
				owner.ClearBuff(buff);
				return;
			}
			if (owner.HasBuff(buff)) {
				Projectile.timeLeft = 2;
			}
			bool isOwner = Projectile.owner == Main.myPlayer;
			if (--rowTimer <= 0) {
				rowTimer = RowRecount;
				CountRow(owner);
			}
			Vector2 home = Home(owner);
			if (isOwner && Vector2.DistanceSquared(owner.Center, Projectile.Center) > TeleportDistance * TeleportDistance) {
				Projectile.Center = home;
				SetMode(Mode.Hover);
			}
			ModeTimer++;
			switch (CurrentMode) {
				case Mode.Dash:
					Projectile.velocity = Heading.ToRotationVector2() * DashSpeed;
					if (isOwner && ModeTimer >= DashTicks) {
						SetMode(Mode.Return);
					}
					break;
				case Mode.Return:
					Vector2 to = home - Projectile.Center;
					float distance = to.Length();
					if (distance < HomeSnap) {
						if (isOwner) {
							SetMode(Mode.Hover);
						}
						Projectile.velocity = Vector2.Zero;
					}
					else {
						Projectile.velocity = to / distance * Math.Min(ReturnSpeed, distance);
					}
					break;
				default:
					// float to the place in the row (eased, so a star joining or the row widening glides), then sit on it
					Vector2 off = home - Projectile.Center;
					Projectile.velocity = off.LengthSquared() > 4f ? off * 0.25f : Vector2.Zero;
					if (off.LengthSquared() <= 4f) {
						Projectile.Center = home;
					}
					// every star keeps the same beat (one pass per AttackCycle at most), each Stagger ticks after the one before
					if (isOwner && ModeTimer >= MinHoverTicks && (Main.GameUpdateCount + (uint)(rowIndex * Stagger)) % AttackCycle == 0) {
						NPC target = AcquireTarget(owner);
						if (target != null) {
							Heading = (target.Center - Projectile.Center).ToRotation();
							SetMode(Mode.Dash);
						}
					}
					break;
			}
			MathSafety.Sanitize(ref Projectile.velocity);
			if (!MathSafety.IsFinite(Projectile.position)) {
				Projectile.Center = owner.Center;
			}
			int spin = CurrentMode == Mode.Hover ? SpinTicks : FastSpinTicks;
			Projectile.frame = (int)(Main.GameUpdateCount / (uint)spin + (uint)rowIndex) % R.StarSpin;
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, 0.25f, 0.22f, 0.5f);
				if (CurrentMode != Mode.Hover && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, DustID.GoldFlame, out Dust spark)) {
					spark.noGravity = true;
					spark.velocity *= 0.3f;
				}
			}
		}

		/// <summary>Owner: a mode change, reaching the others through <c>ai[]</c> (D2).</summary>
		private void SetMode(Mode next) {
			CurrentMode = next;
			ModeTimer = 0f;
			Projectile.netUpdate = true;
		}

		/// <summary>This star's place over the owner's head: a row centred on them, a shallow arc (the middle ones highest),
		/// bobbing by whole pixels.</summary>
		private Vector2 Home(Player owner) {
			float mid = (rowCount - 1) * 0.5f;
			float x = (rowIndex - mid) * RowSpacing;
			float y = -HoverHeight + Math.Abs(rowIndex - mid) * 4f - (Main.GameUpdateCount / 20 + (uint)rowIndex) % 2 * 2f;
			return owner.Top + new Vector2(x, y);
		}

		/// <summary>Where this star stands among its owner's stars (by projectile index), and how many there are. A fixed loop
		/// over the projectiles, every <see cref="RowRecount"/> ticks.</summary>
		private void CountRow(Player owner) {
			int index = 0, count = 0;
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type == Type && p.owner == Projectile.owner) {
					if (p.whoAmI < Projectile.whoAmI) {
						index++;
					}
					count++;
				}
			}
			rowIndex = index;
			rowCount = Math.Max(1, count);
		}

		private NPC AcquireTarget(Player owner) {
			if (--retargetTimer <= 0 || !IsValidTarget(targetIndex, owner)) {
				retargetTimer = RetargetInterval;
				targetIndex = SearchTarget(owner);
			}
			return targetIndex >= 0 ? Main.npc[targetIndex] : null;
		}

		private bool IsValidTarget(int index, Player owner) {
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			NPC npc = Main.npc[index];
			return npc.CanBeChasedBy(Projectile) && Vector2.DistanceSquared(npc.Center, owner.Center) < TargetRange * TargetRange;
		}

		private int SearchTarget(Player owner) {
			int forced = owner.MinionAttackTargetNPC;
			if (IsValidTarget(forced, owner)) {
				return forced;
			}
			int best = -1;
			float bestSq = TargetRange * TargetRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.CanBeChasedBy(Projectile)) {
					continue;
				}
				float sq = Vector2.DistanceSquared(npc.Center, owner.Center);
				if (sq < bestSq && Collision.CanHitLine(Projectile.position, Projectile.width, Projectile.height, npc.position, npc.width, npc.height)) {
					best = npc.whoAmI;
					bestSq = sq;
				}
			}
			return best;
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			// summon damage skips vanilla's crit roll; tModLoader keeps CritChance current for minions (the owner's roll, D2)
			if (Main.rand.Next(100) < Projectile.CritChance) {
				modifiers.SetCrit();
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, R.StarSpin - 1) * (Size + 2), Size, Size);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(Size * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, Color.Lerp(lightColor, Color.White, 0.5f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			if (glow?.IsLoaded == true) {
				Main.EntitySpriteDraw(glow.Value, at, source, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}
	}
}
