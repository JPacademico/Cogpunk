using System;
using Cogpunk.Content.Junkyard.Weapons;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// Cogspring Sword (Espada Molamecânica), a Mechanist sabre (user-set 2026-11-19: "a sword mechanist weapon (under molten
	/// sword, 12% less dps on basic attacks) that can charge attack at right mouse for up to 4x the damage (2 seconds of charge
	/// and a faster slam attack motion for the charged attack, briefly slows down time if it kills an enemy with a fully
	/// charged attack) ... crafts with brass + rusted cogs + chains"; the look is the user's image,
	/// art/mechanist/reference/cogspring_sword_user_2026-11-19.png).
	/// <list type="bullet">
	/// <item><b>Left click</b>: swung like the Firesaw (the same swing: a wind-up, the slash, an overshoot, the next one back
	/// the other way), <see cref="Damage"/> a hit every <see cref="UseTime"/> ticks: 55.1 effective DPS, 11.8% under the
	/// Volcano's 62.4 (decompiled Item 121: 40 damage, use time 40). <see cref="Steam"/> steam a swing.</item>
	/// <item><b>Right click, held</b>: the blade raised behind the head, its core lighting up as the charge builds over
	/// <see cref="ChargeTicks"/> ticks; let go and it comes down in a fast slam (<see cref="CogspringSlam"/>), 1x to
	/// <see cref="MaxMultiplier"/>x the sword's damage by the charge. <see cref="SlamSteam"/> steam, paid as the charge
	/// starts. A fully charged slam that kills an enemy slows time for everyone (the Metal Wrench's slow motion, through
	/// its <see cref="MetalClash"/>).</item>
	/// </list>
	/// <para>D2: the swing is vanilla's item use (every client poses it from the synced use and <see cref="CogspringPlayer"/>);
	/// the charge is a player projectile whose ai carries the state, the charge and the timer, so every client poses and
	/// draws it and the server sees the same slam. D1: arithmetic only, textures cached on clients. D0: non-finite poses
	/// ignored (<see cref="SwingPose"/>), spawns through <see cref="SafeSpawn"/>, the charge's life finite (a held charge lets
	/// go by itself after <see cref="CogspringSlam.MaxHoldTicks"/>).</para>
	/// <para>Balance: docs/balance/weapons.csv (anchor the Volcano). Art: art/mechanist/make_cogspring_art.py.</para>
	/// </summary>
	public class CogspringSword : MechanistWeapon
	{
		public const int Damage = 30;                             // my call: 55.1 effective DPS (user: 12% under the Volcano)
		public const int UseTime = 34;
		public const float Knockback = 6f;                        // the Volcano's 6.5, a touch under
		public const int Steam = 2;                               // my call: a swing (the Firesaw's)
		public const int SlamSteam = 10;                          // my call: a charged slam
		public const int ChargeTicks = 120;                       // user-set: "2 seconds of charge"
		public const float MaxMultiplier = 4f;                    // user-set: "up to 4x the damage"
		public const int BarCost = 12, CogCost = 18, ChainCost = 8;   // the cogs 15 -> 18, x1.2 (user, 2026-11-26);   // my call: the user named the parts, not the counts

		// --- the swing: fractions of the use; angles in the facing frame (radians, 0 ahead, + down, - up) -------------------
		public const float WindEnd = 0.24f, SlashEnd = 0.5f, OverEnd = 0.62f, SettleEnd = 0.85f;
		public const float HitFrom = WindEnd, HitTo = 0.56f;
		public const float High = -2.2f, Low = 1.0f;
		public const float PullBack = 0.3f, Overshoot = 0.2f;

		// --- the sprite (CogspringSword.png, 80x80; the grip on the blade's axis) -------------------------------------------
		public const int Size = 80, GripX = 12, GripY = 66;
		// measured along the axis from the hand (game px at scale 1): the core from 18, the tip at 88, 8 px either side
		public const float BladeStart = 18f, Reach = 88f, BladeRadius = 8f;

		private static readonly SoundStyle SwingSound = SoundID.Item1 with { Pitch = -0.2f, Volume = 0.85f, PitchVariance = 0.15f };

		public override int SteamCost => Steam;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(ChargeTicks / 60, (int)MaxMultiplier, SlamSteam);

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.knockBack = Knockback;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noUseGraphic = true;                            // CogspringLayer draws it at the swing's angle
			Item.UseSound = null;                                // the slash plays its own (UseStyle)
			Item.width = 40;
			Item.height = 40;
			Item.value = Item.sellPrice(gold: 2, silver: 50);
			Item.rare = ItemRarityID.Orange;
		}

		/// <summary>The charged slam's steam after this sword's reforge.</summary>
		public int SlamCost() => ApplyPrefix(SlamSteam, PrefixSteamMultiplier);

		protected override bool CanUseMechanist(Player player) => player.ownedProjectileCounts[ModContent.ProjectileType<CogspringSlam>()] <= 0;

		public override bool? UseItem(Player player) {
			if (player.ItemAnimationJustStarted) {
				player.GetModPlayer<CogspringPlayer>().BeginSwing(player);   // every side, once a swing: its direction
			}
			return base.UseItem(player);                         // the owner pays the steam, once a swing (MechanistWeapon)
		}

		// ------------------------------------------------------------------------------------------------------------
		// The swing (the Firesaw's curve)
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>0..1: how far <paramref name="player"/>'s swing has run, <paramref name="ticksBack"/> ticks ago.</summary>
		public static float Done(Player player, int ticksBack = 0) {
			int max = Math.Max(1, player.itemAnimationMax);
			return 1f - (player.itemAnimation + ticksBack) / (float)max;
		}

		private static float EaseInOutCubic(float t) => t < 0.5f ? 4f * t * t * t : 1f - MathF.Pow(-2f * t + 2f, 3f) * 0.5f;

		/// <summary>The blade's facing-frame angle at <paramref name="done"/> of a down-slash or an up-slash.</summary>
		public static float SwingAngle(float done, bool up) {
			float from = up ? Low : High;
			float to = up ? High : Low;
			float sign = up ? -1f : 1f;
			float start = from - sign * PullBack;
			float over = to + sign * Overshoot;
			if (done < WindEnd) {
				return MathHelper.Lerp(from, start, SwingPose.EaseOutCubic(SwingPose.Phase(done, 0f, WindEnd)));
			}
			if (done < SlashEnd) {
				return MathHelper.Lerp(start, to, EaseInOutCubic(SwingPose.Phase(done, WindEnd, SlashEnd)));
			}
			if (done < OverEnd) {
				return MathHelper.Lerp(to, over, SwingPose.EaseOutCubic(SwingPose.Phase(done, SlashEnd, OverEnd)));
			}
			return MathHelper.Lerp(over, to, EaseInOutCubic(SwingPose.Phase(done, OverEnd, SettleEnd)));
		}

		public static float SwingAngle(Player player, int ticksBack = 0) {
			return SwingAngle(Math.Max(0f, Done(player, ticksBack)), player.GetModPlayer<CogspringPlayer>().Upswing);
		}

		public override void UseStyle(Player player, Rectangle heldItemFrame) {
			float done = Done(player);
			float prev = Done(player, 1);
			SwingPose.Apply(player, SwingAngle(done, player.GetModPlayer<CogspringPlayer>().Upswing));
			if (!Main.dedServ && prev < WindEnd && done >= WindEnd) {
				SoundEngine.PlaySound(SwingSound, player.Center);
			}
		}

		public override void UseItemHitbox(Player player, ref Rectangle hitbox, ref bool noHitbox) {
			float done = Done(player);
			if (done < HitFrom || done >= HitTo) {
				noHitbox = true;
				return;
			}
			float scale = player.GetAdjustedItemScale(Item);
			float facing = SwingAngle(player);
			Vector2 a = SwingPose.BladePoint(player, player.itemLocation, facing, BladeStart * scale, 0f);
			Vector2 b = SwingPose.BladePoint(player, player.itemLocation, facing, Reach * scale, 0f);
			if (!MathSafety.IsFinite(a) || !MathSafety.IsFinite(b)) {
				noHitbox = true;
				return;
			}
			float r = BladeRadius * scale;
			int left = (int)(MathF.Min(a.X, b.X) - r), top = (int)(MathF.Min(a.Y, b.Y) - r);
			hitbox = new Rectangle(left, top, (int)(MathF.Abs(a.X - b.X) + 2f * r), (int)(MathF.Abs(a.Y - b.Y) + 2f * r));
		}

		/// <summary>The blade as a capsule at this tick's angle, half a tick and a tick back (no enemy slips between poses).</summary>
		public override bool? CanMeleeAttackCollideWithNPC(Rectangle meleeAttackHitbox, Player player, NPC target) {
			float done = Done(player);
			if (done < HitFrom || done >= HitTo) {
				return false;
			}
			float scale = player.GetAdjustedItemScale(Item);
			float now = SwingAngle(player);
			float before = SwingAngle(player, 1);
			Rectangle box = target.Hitbox;
			return BladeHits(player, now, scale, box) || BladeHits(player, (now + before) * 0.5f, scale, box) || BladeHits(player, before, scale, box);
		}

		public static bool BladeHits(Player player, float facing, float scale, Rectangle box) {
			SwingPose.Compute(player, facing, out Vector2 hand, out _);
			Vector2 a = SwingPose.BladePoint(player, hand, facing, BladeStart * scale, 0f);
			Vector2 b = SwingPose.BladePoint(player, hand, facing, Reach * scale, 0f);
			return SwingPose.CapsuleHitsRect(a, b, BladeRadius * scale, box);
		}

		public override void OnHitNPC(Player player, NPC target, NPC.HitInfo hit, int damageDone) {
			if (Main.dedServ || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < 4; i++) {                         // the bronze bites: sparks, a green fleck from the core
				if (SafeSpawn.TryNewDust(target.Center - new Vector2(8f), 16, 16, i == 0 ? DustID.GreenTorch : DustID.Copper, out Dust spark)) {
					spark.velocity = Main.rand.NextVector2Circular(3f, 3f) - Vector2.UnitY;
					spark.noGravity = i == 0;
				}
			}
		}

		/// <summary>Draws the sword (and its lights) posed at <paramref name="facing"/> in <paramref name="player"/>'s hand, the
		/// way vanilla poses a held swing, pivoting on the grip: into the player's draw cache (the swing's layer).</summary>
		public static void AddDraw(ref PlayerDrawSet drawInfo, Player player, Texture2D sword, Texture2D glow, float facing, Color light,
			float glowStrength, float scale) {
			SwingPose.Compute(player, facing, out Vector2 hand, out float rotation);
			if (!MathSafety.IsFinite(hand) || !float.IsFinite(rotation)) {
				return;
			}
			Vector2 location = drawInfo.Position + (hand - player.position);
			Vector2 at = new((int)(location.X - Main.screenPosition.X), (int)(location.Y - Main.screenPosition.Y));
			Vector2 origin = Origin(player);
			drawInfo.DrawDataCache.Add(new DrawData(sword, at, null, light, rotation, origin, scale, drawInfo.itemEffect));
			if (glow != null && glowStrength > 0f) {
				drawInfo.DrawDataCache.Add(new DrawData(glow, at, null, Color.White * glowStrength, rotation, origin, scale, drawInfo.itemEffect));
			}
		}

		/// <summary>The grip, in the (possibly mirrored) sprite: the pivot.</summary>
		public static Vector2 Origin(Player player) {
			return new Vector2(player.direction == 1 ? GripX : Size - GripX, player.gravDir == -1f ? Size - GripY : GripY);
		}

		/// <summary>The mirroring a held swing gets (decompiled: <c>itemEffect</c>), for drawing outside the player's layers.</summary>
		public static SpriteEffects Effects(Player player) {
			SpriteEffects fx = player.direction == -1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			return player.gravDir == -1f ? fx | SpriteEffects.FlipVertically : fx;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<TarnishedBrassBar>(BarCost)
				.AddIngredient<RustedCog>(CogCost)
				.AddIngredient(ItemID.Chain, ChainCost)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}

	/// <summary>
	/// The Cogspring Sword's swing direction (the Firesaw's rule: held swings alternate, a pause starts with a down-slash) and
	/// its right click (the Bandit's Dream's pattern: caught before the item check, so it is no item use): on a press it pays
	/// the slam's steam and raises the blade (<see cref="CogspringSlam"/>, which holds the charge while the button is held).
	/// D2: the owner starts it; the projectile carries it to everyone.
	/// </summary>
	public sealed class CogspringPlayer : ModPlayer
	{
		public const int ResetGap = 20;

		public bool Upswing;
		private uint lastSwing;

		public void BeginSwing(Player player) {
			uint now = Main.GameUpdateCount;
			bool chained = now - lastSwing <= (uint)(player.itemAnimationMax + ResetGap);
			Upswing = chained && !Upswing;
			lastSwing = now;
		}

		public override bool PreItemCheck() {
			if (Player.whoAmI != Main.myPlayer || Player.HeldItem?.ModItem is not CogspringSword sword) {
				return true;
			}
			bool rightClick = Player.controlUseTile && Main.mouseRightRelease && !Player.tileInteractionHappened && Player.releaseUseItem
				&& !Player.controlUseItem && !Player.mouseInterface && !Main.HoveringOverAnNPC && !Main.SmartInteractShowingGenuine;
			if (!rightClick || Player.itemAnimation > 0 || Player.CCed || Player.noItems || Player.dead
				|| Player.ownedProjectileCounts[ModContent.ProjectileType<CogspringSlam>()] > 0) {
				return true;
			}
			Main.mouseRightRelease = false;
			if (!Player.GetModPlayer<SteamPlayer>().TryPayAttack(sword.SlamCost(), out _)) {
				return true;                                    // no tank (a hint) or too little steam (an overheat)
			}
			SafeSpawn.TryNewProjectile(Player.GetSource_ItemUse(Player.HeldItem), Player.MountedCenter, Vector2.Zero,
				ModContent.ProjectileType<CogspringSlam>(), Player.GetWeaponDamage(Player.HeldItem), Player.GetWeaponKnockback(Player.HeldItem),
				out _, Player.whoAmI);
			return true;
		}
	}

	/// <summary>
	/// The Cogspring Sword's charge and slam, held in the hand (<c>heldProj</c>; drawn by the player's held-projectile layer).
	/// ai[0] the state (0 charging, 1 slamming), ai[1] the ticks charged (to <see cref="CogspringSword.ChargeTicks"/>),
	/// ai[2] the ticks since the slam began. Charging: the blade rises behind the head (to <see cref="ChargeTo"/>), the core
	/// brightens, and at full charge it flashes once and trembles; the owner lets go (or after <see cref="MaxHoldTicks"/>)
	/// and its damage becomes the sword's times 1 + 3 x the charge. The slam: <see cref="SlamTicks"/> ticks from there to
	/// <see cref="SlamTo"/>, eased in (it gathers speed: faster than a swing's slash), every enemy the blade crosses hit once;
	/// then it rests <see cref="SettleTicks"/> ticks. A fully charged slam that kills drops a <see cref="MetalClash"/> in boss
	/// mode on the body: the clang, the camera punch and the slow motion on every side.
	/// </summary>
	public class CogspringSlam : CogpunkProjectile
	{
		public const int SlamTicks = 6, SettleTicks = 10, MaxHoldTicks = 600;
		public const float ChargeFrom = -2.0f, ChargeTo = -2.6f, SlamTo = 1.1f, Tremble = 0.03f;

		private static Asset<Texture2D> glow;

		private ref float State => ref Projectile.ai[0];
		private ref float Charge => ref Projectile.ai[1];
		private ref float Timer => ref Projectile.ai[2];
		private ref float Flashed => ref Projectile.localAI[0];
		private ref float Slowed => ref Projectile.localAI[1];

		public override string Texture => "Cogpunk/Content/Mechanist/Weapons/CogspringSword";

		public override void SetStaticDefaults() {
			if (!Main.dedServ) {
				glow = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/CogspringSword_Glow");
			}
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = ModContent.GetInstance<MechanistDamage>();
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.ownerHitCheck = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;              // each enemy once a slam
			Projectile.timeLeft = 2;
			Projectile.aiStyle = -1;
			Projectile.hide = true;                          // drawn once, by the owner's held-projectile layer
		}

		/// <summary>0..1: how full the charge is.</summary>
		public float ChargeFraction => MathHelper.Clamp(Charge / CogspringSword.ChargeTicks, 0f, 1f);

		private bool Full => Charge >= CogspringSword.ChargeTicks;

		private float RaisedAngle() => MathHelper.Lerp(ChargeFrom, ChargeTo, SwingPose.EaseOutCubic(ChargeFraction));

		/// <summary>The blade's facing-frame angle now.</summary>
		public float Facing(float ticksBack = 0f) {
			if (State == 0f) {
				float a = RaisedAngle();
				return Full ? a + ((Main.GameUpdateCount / 2) % 2 == 0 ? Tremble : -Tremble) : a;
			}
			float u = SwingPose.Phase(Math.Max(0f, Timer - ticksBack), 0f, SlamTicks);
			return MathHelper.Lerp(RaisedAngle(), SlamTo, SwingPose.EaseInCubic(u));
		}

		public override bool? CanDamage() => State == 1f && Timer <= SlamTicks + 1 ? null : false;

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			if (!owner.active || owner.dead || owner.CCed || owner.HeldItem?.ModItem is not CogspringSword) {
				Projectile.Kill();
				return;
			}
			Projectile.Center = owner.MountedCenter;
			owner.heldProj = Projectile.whoAmI;
			if (State == 0f) {
				Projectile.timeLeft = 2;                      // held: lives while the charge does (every side)
				if (Charge < CogspringSword.ChargeTicks) {
					Charge++;                                 // every side counts it (smooth for onlookers); the owner's syncs win
					if (Projectile.owner == Main.myPlayer && (Charge >= CogspringSword.ChargeTicks || Charge % 30 == 0)) {
						Projectile.netUpdate = true;
					}
				}
				if (Projectile.owner == Main.myPlayer) {
					owner.ChangeDir(Main.MouseWorld.X >= owner.Center.X ? 1 : -1);
					Timer++;
					if (!Main.mouseRight || Timer >= MaxHoldTicks) {
						Release(owner);
					}
				}
				ChargeEffects(owner);
			}
			else {
				Timer++;
				Projectile.timeLeft = 2;
				if (Timer == SlamTicks && !Main.dedServ) {
					Impact(owner);
				}
				if (Timer >= SlamTicks + SettleTicks) {
					Projectile.Kill();
					return;
				}
			}
			SwingPose.Apply(owner, Facing());
		}

		/// <summary>Owner: lets the charge go: the slam, its damage by the charge.</summary>
		private void Release(Player owner) {
			float c = ChargeFraction;
			Item item = owner.HeldItem;
			State = 1f;
			Timer = 0f;
			Projectile.damage = (int)Math.Round(owner.GetWeaponDamage(item) * (1f + (CogspringSword.MaxMultiplier - 1f) * c));
			Projectile.knockBack = owner.GetWeaponKnockback(item) * (1f + c);
			Projectile.CritChance = owner.GetWeaponCrit(item);
			Projectile.netUpdate = true;
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item1 with { Pitch = -0.5f + 0.3f * c, Volume = 0.9f }, owner.Center);
			}
		}

		private void ChargeEffects(Player owner) {
			if (Main.dedServ) {
				return;
			}
			float c = ChargeFraction;
			SwingPose.Compute(owner, Facing(), out Vector2 hand, out _);
			Vector2 core = SwingPose.BladePoint(owner, hand, Facing(), 26f, 0f);
			if (MathSafety.IsFinite(core)) {
				Lighting.AddLight(core, 0.15f + 0.35f * c, 0.5f + 0.5f * c, 0.4f + 0.3f * c);
				if (Main.rand.NextFloat() < 0.15f + 0.35f * c && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(core - new Vector2(3f), 6, 6, DustID.GreenTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(1.5f, 1.5f);
					d.scale = 0.8f + 0.5f * c;
				}
			}
			if (Full && Flashed == 0f) {
				Flashed = 1f;                                 // full: a chime and a burst of light, once
				SoundEngine.PlaySound(SoundID.MaxMana with { Pitch = -0.3f }, owner.Center);
				for (int i = 0; i < 10 && MathSafety.IsFinite(core); i++) {
					if (SafeSpawn.TryNewDust(core - new Vector2(4f), 8, 8, DustID.GreenTorch, out Dust d)) {
						d.noGravity = true;
						d.velocity = Main.rand.NextVector2CircularEdge(3f, 3f);
						d.scale = 1.3f;
					}
				}
			}
		}

		/// <summary>Every client: the blade lands: a thud scaled by the charge, sparks and green light off the tip, the camera
		/// punched for the owner.</summary>
		private void Impact(Player owner) {
			float c = ChargeFraction;
			float facing = Facing();
			SwingPose.Compute(owner, facing, out Vector2 hand, out _);
			Vector2 tip = SwingPose.BladePoint(owner, hand, facing, CogspringSword.Reach * 0.85f, 0f);
			if (!MathSafety.IsFinite(tip)) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item14 with { Pitch = 0.2f - 0.4f * c, Volume = 0.4f + 0.4f * c }, tip);
			if (owner.whoAmI == Main.myPlayer && (CogpunkClientConfig.Instance?.ScreenShake ?? true)) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(tip, Vector2.UnitY, 2f + 5f * c, 10f, 10 + (int)(10 * c), 800f, "Cogpunk:Cogspring"));
			}
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			int n = 6 + (int)(10 * c);
			for (int i = 0; i < n; i++) {
				if (SafeSpawn.TryNewDust(tip - new Vector2(10f, 4f), 20, 8, i % 3 == 0 ? DustID.GreenTorch : DustID.Copper, out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-4f, 4f), -Main.rand.NextFloat(1f, 4f)) * (0.6f + 0.6f * c);
					d.noGravity = i % 3 == 0;
					d.scale = 1f + 0.4f * c;
				}
			}
		}

		/// <summary>The blade as drawn, a capsule, at this tick's angle and three steps back to the last one's (it turns fast
		/// at the end of the slam: nothing slips between two poses).</summary>
		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (State != 1f || Timer <= 0f || Timer > SlamTicks + 1) {
				return false;
			}
			Player owner = Main.player[Projectile.owner];
			float now = Facing(), before = Facing(1f);
			for (int k = 0; k <= 3; k++) {
				if (CogspringSword.BladeHits(owner, MathHelper.Lerp(before, now, k / 3f), 1f, targetHitbox)) {
					return true;
				}
			}
			return false;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (!Full || Slowed != 0f || target.life > 0 || target.friendly || target.CountsAsACritter || target.SpawnedFromStatue
				|| target.lifeMax <= 5 || Projectile.owner != Main.myPlayer) {
				return;
			}
			Slowed = 1f;                                      // one slow motion a slam
			SafeSpawn.TryNewProjectile(Projectile.GetSource_FromThis(), target.Center, Vector2.Zero, ModContent.ProjectileType<MetalClash>(),
				0, 0f, out _, Projectile.owner, MetalClash.BossMode);
		}

		// The sword in the hand at the charge's or the slam's angle, its lights by the charge; through the slam two fading
		// copies a tick and two back (the smear, D4 rule 10).
		public override bool PreDraw(ref Color lightColor) {
			Player owner = Main.player[Projectile.owner];
			Texture2D sword = TextureAssets.Projectile[Type].Value;
			Texture2D lights = glow?.IsLoaded == true ? glow.Value : null;
			float c = ChargeFraction;
			float strength = State == 0f ? 0.35f + 0.65f * c + (Full ? 0.15f * MathF.Sin(Main.GlobalTimeWrappedHourly * 12f) : 0f) : 1f;
			if (State == 1f && Timer <= SlamTicks + 1) {
				for (int k = 2; k >= 1; k--) {
					Draw(owner, sword, null, Facing(k), lightColor * (0.4f / k), 0f);
				}
			}
			Draw(owner, sword, lights, Facing(), lightColor, strength);
			return false;
		}

		private static void Draw(Player owner, Texture2D sword, Texture2D lights, float facing, Color color, float strength) {
			SwingPose.Compute(owner, facing, out Vector2 hand, out float rotation);
			if (!MathSafety.IsFinite(hand) || !float.IsFinite(rotation)) {
				return;
			}
			Vector2 at = (hand - Main.screenPosition + new Vector2(0f, owner.gfxOffY)).Floor();
			Vector2 origin = CogspringSword.Origin(owner);
			SpriteEffects fx = CogspringSword.Effects(owner);
			Main.EntitySpriteDraw(sword, at, null, color, rotation, origin, 1f, fx);
			if (lights != null && strength > 0f) {
				Main.EntitySpriteDraw(lights, at, null, Color.White * MathHelper.Clamp(strength, 0f, 1f), rotation, origin, 1f, fx);
			}
		}
	}

	/// <summary>
	/// Draws the Cogspring Sword through a swing (the item is <c>noUseGraphic</c>): the sword at the swing's angle with its
	/// lights, and through the slash two fading copies a tick and two back (the smear, D4 rule 10). Every client draws every
	/// player's from the synced use. D1: at most 6 draws, textures cached on clients. D0: never touched on a server.
	/// </summary>
	public sealed class CogspringLayer : PlayerDrawLayer
	{
		private static readonly float[] Opacity = { 0.4f, 0.2f };
		private static Asset<Texture2D> sword, lights;
		private static int swordType = -1;

		public override void Load() {
			sword = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/CogspringSword");
			lights = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/CogspringSword_Glow");
		}

		public override void Unload() {
			sword = lights = null;
			swordType = -1;
		}

		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.HeldItem);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) {
			if (swordType < 0) {
				swordType = ModContent.ItemType<CogspringSword>();
			}
			Player player = drawInfo.drawPlayer;
			return drawInfo.shadow == 0f && player.itemAnimation > 0 && player.HeldItem.type == swordType && !player.dead && !player.frozen
				&& !player.pulley;
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (sword?.IsLoaded != true) {
				return;
			}
			Player player = drawInfo.drawPlayer;
			Texture2D glowTex = lights?.IsLoaded == true ? lights.Value : null;
			float scale = player.GetAdjustedItemScale(player.HeldItem);
			Color light = player.HeldItem.GetAlpha(Lighting.GetColor((int)(player.Center.X / 16f), (int)(player.Center.Y / 16f)));
			float done = CogspringSword.Done(player);
			if (done >= CogspringSword.WindEnd && done < CogspringSword.OverEnd) {
				for (int k = Opacity.Length; k >= 1; k--) {
					if (CogspringSword.Done(player, k) < CogspringSword.WindEnd - 0.05f) {
						continue;
					}
					CogspringSword.AddDraw(ref drawInfo, player, sword.Value, null, CogspringSword.SwingAngle(player, k), light * Opacity[k - 1], 0f, scale);
				}
			}
			CogspringSword.AddDraw(ref drawInfo, player, sword.Value, glowTex, CogspringSword.SwingAngle(player), light, 0.6f, scale);
		}
	}
}
