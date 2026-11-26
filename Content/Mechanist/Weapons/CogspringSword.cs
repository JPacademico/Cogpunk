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
	/// <item><b>Left click</b>: vanilla's sword swing (user, 2026-11-26, 0.2.2: "Cogspring sword should have normal sword terraria
	/// animations for its basic attack, and also a bit quicker use time for the basic attack. add a phantom slash trail for the
	/// swings as it is a visual rule for our melee weapons"; the Firesaw's wind-up, slash and overshoot until then): the game
	/// swings and draws it as any sword (use style Swing, the item sprite in the hand), its lights drawn over it and a green
	/// phantom slash under it (<see cref="CogspringLayer"/>, <see cref="CogspringTrailLayer"/>). <see cref="Damage"/> a hit
	/// every <see cref="UseTime"/> ticks (34 before): 62.4 effective DPS, the Volcano's own (decompiled Item 121: 40 damage, use
	/// time 40); 55.1 before, 11.8% under it. The hits follow the drawn blade (<see cref="BladeHitsHeld"/>), swept from the
	/// last tick. <see cref="Steam"/> steam a swing.</item>
	/// <item><b>Right click, held</b>: the blade raised behind the head, its core lighting up as the charge builds over
	/// <see cref="ChargeTicks"/> ticks; let go and it comes down in a fast slam (<see cref="CogspringSlam"/>), 1x to
	/// <see cref="MaxMultiplier"/>x the sword's damage by the charge. <see cref="SlamSteam"/> steam, paid as the charge
	/// starts. A fully charged slam that kills an enemy slows time for everyone (the Metal Wrench's slow motion, through
	/// its <see cref="MetalClash"/>).</item>
	/// </list>
	/// <para>D2: the swing is vanilla's item use (every client swings it from the synced use; <see cref="CogspringPlayer"/> keeps
	/// each player's last angles for the trail and the hits); the charge is a player projectile whose ai carries the state,
	/// the charge and the timer, so every client poses and draws it and the server sees the same slam. D1: arithmetic only,
	/// a fixed ring of angles a player, textures cached on clients. D0: non-finite poses ignored (<see cref="SwingPose"/>),
	/// spawns through <see cref="SafeSpawn"/>, the charge's life finite (a held charge lets go by itself after
	/// <see cref="CogspringSlam.MaxHoldTicks"/>).</para>
	/// <para>Balance: docs/balance/weapons.csv (anchor the Volcano). Art: art/mechanist/make_cogspring_art.py (the sword, its
	/// lights and the phantom slash).</para>
	/// </summary>
	public class CogspringSword : MechanistWeapon
	{
		public const int Damage = 30;                             // my call: 62.4 effective DPS at use 30 (the Volcano's; 55.1 at 34)
		public const int UseTime = 30;                            // user, 2026-11-26 (0.2.2): "a bit quicker" (34 before)
		public const float Knockback = 6f;                        // the Volcano's 6.5, a touch under
		public const int Steam = 2;                               // my call: a swing (the Firesaw's)
		public const int SlamSteam = 10;                          // my call: a charged slam
		public const int ChargeTicks = 120;                       // user-set: "2 seconds of charge"
		public const float MaxMultiplier = 4f;                    // user-set: "up to 4x the damage"
		public const int BarCost = 12, CogCost = 18, ChainCost = 8;   // the cogs 15 -> 18, x1.2 (user, 2026-11-26);   // my call: the user named the parts, not the counts

		// --- the sprite (CogspringSword.png, 80x80; the grip on the blade's axis) -------------------------------------------
		public const int Size = 80, GripX = 12, GripY = 66;
		// measured along the axis from the hand (game px at scale 1): the core from 18, the tip at 88, 8 px either side
		public const float BladeStart = 18f, Reach = 88f, BladeRadius = 8f;
		/// <summary>Vanilla holds a swung sprite by its bottom-left corner, on the blade's axis 18 px behind the grip: the same
		/// blade measured from there (the charged slam, posed by <see cref="SwingPose"/>, keeps the grip in the hand).</summary>
		public const float CornerToGrip = 18f, HeldBladeStart = BladeStart + CornerToGrip, HeldReach = Reach + CornerToGrip;

		private static readonly SoundStyle SwingSound = SoundID.Item1 with { Pitch = -0.2f, Volume = 0.85f, PitchVariance = 0.15f };

		public override int SteamCost => Steam;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(ChargeTicks / 60, (int)MaxMultiplier, SlamSteam);

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.knockBack = Knockback;
			Item.useStyle = ItemUseStyleID.Swing;                // vanilla's sword swing and its drawing (0.2.2)
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.UseSound = SwingSound;
			Item.width = 40;
			Item.height = 40;
			Item.value = Item.sellPrice(gold: 2, silver: 50);
			Item.rare = ItemRarityID.Orange;
		}

		/// <summary>The charged slam's steam after this sword's reforge.</summary>
		public int SlamCost() => ApplyPrefix(SlamSteam, PrefixSteamMultiplier);

		protected override bool CanUseMechanist(Player player) => player.ownedProjectileCounts[ModContent.ProjectileType<CogspringSlam>()] <= 0;

		// ------------------------------------------------------------------------------------------------------------
		// The swing (vanilla's, 0.2.2)
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>Runs after vanilla has posed the swing this tick (decompiled <c>ItemCheck_ApplyUseStyle</c>, then
		/// <c>ItemLoader.UseStyle</c>): its angle noted for the trail and the hits, on every side.</summary>
		public override void UseStyle(Player player, Rectangle heldItemFrame) {
			player.GetModPlayer<CogspringPlayer>().Note(player);
		}

		/// <summary>The blade's bounds this tick (vanilla cuts grass and pots with it); the real test is
		/// <see cref="CanMeleeAttackCollideWithNPC"/>.</summary>
		public override void UseItemHitbox(Player player, ref Rectangle hitbox, ref bool noHitbox) {
			float scale = player.GetAdjustedItemScale(Item);
			Vector2 dir = SwingPose.HeldBladeDirection(player, player.itemRotation);
			Vector2 a = player.itemLocation + dir * (HeldBladeStart * scale);
			Vector2 b = player.itemLocation + dir * (HeldReach * scale);
			if (!MathSafety.IsFinite(a) || !MathSafety.IsFinite(b)) {
				noHitbox = true;
				return;
			}
			float r = BladeRadius * scale;
			int left = (int)(MathF.Min(a.X, b.X) - r), top = (int)(MathF.Min(a.Y, b.Y) - r);
			hitbox = new Rectangle(left, top, (int)(MathF.Abs(a.X - b.X) + 2f * r), (int)(MathF.Abs(a.Y - b.Y) + 2f * r));
		}

		/// <summary>The drawn blade as a capsule at this tick's angle, half a tick and a tick back (no enemy slips between poses).</summary>
		public override bool? CanMeleeAttackCollideWithNPC(Rectangle meleeAttackHitbox, Player player, NPC target) {
			float scale = player.GetAdjustedItemScale(Item);
			CogspringPlayer swing = player.GetModPlayer<CogspringPlayer>();
			float now = player.itemRotation;
			float before = swing.Rotation(1, now);
			Rectangle box = target.Hitbox;
			return BladeHitsHeld(player, now, scale, box) || BladeHitsHeld(player, (now + before) * 0.5f, scale, box)
				|| BladeHitsHeld(player, before, scale, box);
		}

		/// <summary>The blade vanilla draws at <paramref name="itemRotation"/> (held by its corner at <c>itemLocation</c>) touches
		/// <paramref name="box"/>.</summary>
		public static bool BladeHitsHeld(Player player, float itemRotation, float scale, Rectangle box) {
			Vector2 dir = SwingPose.HeldBladeDirection(player, itemRotation);
			Vector2 a = player.itemLocation + dir * (HeldBladeStart * scale);
			Vector2 b = player.itemLocation + dir * (HeldReach * scale);
			return SwingPose.CapsuleHitsRect(a, b, BladeRadius * scale, box);
		}

		/// <summary>The charged slam's blade, posed by <see cref="SwingPose"/> at <paramref name="facing"/> (the grip in the hand).</summary>
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
	/// The Cogspring Sword's swing angles (0.2.2: vanilla's swing; the last <see cref="History"/> ticks of its
	/// <c>itemRotation</c>, for the phantom slash and the swept hits) and its right click (the Bandit's Dream's pattern: caught
	/// before the item check, so it is no item use): on a press it pays the slam's steam and raises the blade
	/// (<see cref="CogspringSlam"/>, which holds the charge while the button is held). D2: every side notes every player's swing
	/// from the synced use; the owner starts the slam and the projectile carries it to everyone. D1: one small ring a player,
	/// made on its first swing.
	/// </summary>
	public sealed class CogspringPlayer : ModPlayer
	{
		public const int History = 12;

		private float[] rotations;
		private int head, noted, lastAnimation;

		/// <summary>Ticks of this swing noted so far (at most <see cref="History"/>).</summary>
		public int Noted => noted;

		/// <summary>Every side, every tick of a swing (from <see cref="CogspringSword.UseStyle"/>): this tick's angle.</summary>
		public void Note(Player player) {
			rotations ??= new float[History];
			if (player.ItemAnimationJustStarted || player.itemAnimation > lastAnimation) {
				noted = 0;                                    // a new swing (the animation started again): nothing behind it yet
			}
			lastAnimation = player.itemAnimation;
			head = (head + 1) % History;
			rotations[head] = player.itemRotation;
			noted = Math.Min(noted + 1, History);
		}

		/// <summary>The swing's <c>itemRotation</c> <paramref name="ticksBack"/> ticks ago (no further back than its first tick);
		/// <paramref name="fallback"/> before anything is noted.</summary>
		public float Rotation(int ticksBack, float fallback) {
			if (rotations == null || noted <= 0) {
				return fallback;
			}
			int k = Math.Clamp(ticksBack, 0, noted - 1);
			return rotations[(head - k + History) % History];
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
	/// The Cogspring Sword's lights over the sword vanilla draws in a swing (0.2.2): the glow sheet posed exactly as vanilla
	/// poses a swung item (decompiled <c>PlayerDrawLayers.DrawPlayer_27_HeldItem</c>: at <c>itemLocation</c>, turned by
	/// <c>itemRotation</c> about the sprite's bottom corner on the near side, the item's scale, mirrored by <c>itemEffect</c>),
	/// as vanilla draws a glowmask. Every client draws every player's from the synced use. D1: one draw, texture cached on
	/// clients. D0: never touched on a server; a missing texture draws nothing.
	/// </summary>
	public sealed class CogspringLayer : PlayerDrawLayer
	{
		public const float GlowStrength = 0.6f;
		private static Asset<Texture2D> lights;
		private static int swordType = -1;

		public override void Load() {
			lights = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/CogspringSword_Glow");
		}

		public override void Unload() {
			lights = null;
			swordType = -1;
		}

		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.HeldItem);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) => Swinging(drawInfo, ref swordType);

		/// <summary>A player swinging the Cogspring Sword (drawn for real: not a shadow, not frozen, not on a pulley).</summary>
		internal static bool Swinging(PlayerDrawSet drawInfo, ref int swordType) {
			if (swordType < 0) {
				swordType = ModContent.ItemType<CogspringSword>();
			}
			Player player = drawInfo.drawPlayer;
			return drawInfo.shadow == 0f && player.itemAnimation > 0 && player.HeldItem.type == swordType && !player.dead && !player.frozen
				&& !player.pulley && player.HeldItem.useStyle == ItemUseStyleID.Swing;
		}

		/// <summary>Where vanilla draws the held item, on screen (as <c>PlayerDrawSet.ItemLocation</c> is made, whole pixels).</summary>
		internal static Vector2 HeldAt(ref PlayerDrawSet drawInfo, Player player) {
			Vector2 location = drawInfo.Position + (player.itemLocation - player.position);
			return new Vector2((int)(location.X - Main.screenPosition.X), (int)(location.Y - Main.screenPosition.Y));
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (lights?.IsLoaded != true) {
				return;
			}
			Player player = drawInfo.drawPlayer;
			Texture2D tex = lights.Value;
			float scale = player.GetAdjustedItemScale(player.HeldItem);
			Vector2 origin = new(tex.Width * 0.5f - tex.Width * 0.5f * player.direction, player.gravDir == -1f ? 0f : tex.Height);
			drawInfo.DrawDataCache.Add(new DrawData(tex, HeldAt(ref drawInfo, player), null, Color.White * GlowStrength, player.itemRotation, origin,
				scale, drawInfo.itemEffect));
		}
	}

	/// <summary>
	/// The Cogspring Sword's phantom slash (user, 2026-11-26, 0.2.2: "add a phantom slash trail for the swings as it is a visual
	/// rule for our melee weapons"; the Firesaw's, 2026-11-10b): under the sword vanilla draws, a green crescent over the arc the
	/// blade swept in the last <see cref="TrailTicks"/> ticks, pivoting where vanilla holds the sprite (its corner on the blade's
	/// axis, <c>itemLocation</c>), its leading edge on the blade. <c>CogspringTrail.png</c> holds <see cref="TrailFrames"/>
	/// crescents, each <see cref="TrailStep"/> longer (art/mechanist/make_cogspring_art.py); the one nearest the sweep is turned
	/// onto the blade, mirrored for a counter-clockwise sweep (a swing facing left), and added onto what is behind it (alpha 0
	/// under premultiplied blending: light, never a dark smear), fuller the faster the blade turns. D1: one draw; the angles come
	/// from <see cref="CogspringPlayer"/>'s ring. D0: textures never touched on a server; a missing one or a non-finite sweep
	/// draws nothing.
	/// </summary>
	public sealed class CogspringTrailLayer : PlayerDrawLayer
	{
		public const int TrailFrames = 8;
		public const float TrailStep = 12f * MathHelper.Pi / 180f;   // frame k spans (k + 1) steps
		public const int TrailTicks = 7;                             // the sweep it shows
		public const float TrailMin = 0.15f;                         // radians: a shorter sweep shows none
		public const float TrailFull = 0.9f;                         // radians: a sweep this long shows at full opacity
		public const float TrailOpacity = 0.55f;
		public const int Gap = 2;
		// art/mechanist/make_cogspring_art.py prints these: a frame's size and the pivot (the sprite's corner) in it, game px
		public const int TrailW = 128, TrailH = 116, TrailPivotX = 16, TrailPivotY = 112;

		private static Asset<Texture2D> trail;
		private static int swordType = -1;

		public override void Load() {
			trail = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/CogspringTrail");
		}

		public override void Unload() {
			trail = null;
			swordType = -1;
		}

		public override Position GetDefaultPosition() => new BeforeParent(PlayerDrawLayers.HeldItem);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) => CogspringLayer.Swinging(drawInfo, ref swordType);

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (trail?.IsLoaded != true) {
				return;
			}
			Player player = drawInfo.drawPlayer;
			CogspringPlayer swing = player.GetModPlayer<CogspringPlayer>();
			int back = Math.Min(TrailTicks, swing.Noted - 1);
			if (back < 1) {
				return;
			}
			Vector2 now = SwingPose.HeldBladeDirection(player, player.itemRotation);
			Vector2 then = SwingPose.HeldBladeDirection(player, swing.Rotation(back, player.itemRotation));
			float sweep = MathF.Atan2(then.X * now.Y - then.Y * now.X, Vector2.Dot(then, now));   // + clockwise on screen
			float span = MathF.Abs(sweep);
			if (!float.IsFinite(span) || span < TrailMin) {
				return;
			}
			int frame = Math.Clamp((int)(span / TrailStep + 0.5f), 1, TrailFrames) - 1;
			Rectangle source = new(0, frame * (TrailH + Gap), TrailW, TrailH);
			if (source.Bottom > trail.Value.Height) {
				return;
			}
			bool clockwise = sweep > 0f;
			Vector2 origin = new(TrailPivotX, clockwise ? TrailPivotY : TrailH - TrailPivotY);
			float opacity = TrailOpacity * MathHelper.Clamp(span / TrailFull, 0.35f, 1f);
			Color color = new Color(255, 255, 255, 0) * opacity;          // alpha 0: added onto what is behind it
			drawInfo.DrawDataCache.Add(new DrawData(trail.Value, CogspringLayer.HeldAt(ref drawInfo, player), source, color, MathF.Atan2(now.Y, now.X),
				origin, player.GetAdjustedItemScale(player.HeldItem), clockwise ? SpriteEffects.None : SpriteEffects.FlipVertically));
		}
	}
}
