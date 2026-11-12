using System;
using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// Firesaw (Serra de Fogo), a Mechanist chainsaw greatsword with a petrol engine (user-set 2026-11-09: 7 brass bars + 11
	/// polished metal + 8 condensed tar; 2 steam every 0.2 s, 4 on fire; very low knockback; right click: the blade infused
	/// with fire, +2 tiles of reach, On Fire!). <b>Reworked 2026-11-10</b> (user: "redesign the firesaw, it needs more
	/// steampunk (image for reference) and rework how it works: it should slash like a sword now (cool animation like the
	/// melee rework mods do) and on the right mouse it should gain a fire effect that increases range and applies fire on the
	/// enemy; increase the damage to 39 per hit"):
	/// <list type="bullet">
	/// <item>A swung greatsword: <see cref="Damage"/> a hit, one hit per enemy per swing (vanilla's melee cooldown), every
	/// enemy the blade passes through, <see cref="UseTime"/> ticks a swing. Each swing pulls back (the wind-up, eased out),
	/// slashes through (eased in and out, <see cref="WindEnd"/> to <see cref="SlashEnd"/>), overshoots and settles, and the
	/// next one comes back the other way: a down-slash, an up-slash, a down-slash... (a pause starts again with a
	/// down-slash). The arm follows the blade (<see cref="SwingPose"/>), the chain runs, and the slash leaves a smear
	/// (<see cref="FiresawLayer"/>).</item>
	/// <item>Right click: the same slash with the blade on fire: flames off the teeth and a jet past the nose,
	/// <see cref="FireReach"/> - <see cref="Reach"/> px (two tiles) more reach, On Fire! for <see cref="OnFireTicks"/> ticks,
	/// and twice the steam.</item>
	/// <item>Steam: <see cref="Steam"/> a swing, <see cref="FireSteam"/> a fire swing (user-set 2026-11-10b: "consume 2 steam
	/// per attack (instead of every 0.2 seconds) but 5 per attack on the right mouse secondary attack"). Running dry
	/// overheats, as every Mechanist weapon does.</item>
	/// <item>2026-11-10b (user): <see cref="Damage"/> 42 a hit, a <see cref="CritBonus"/> crit bonus over the player's 4%
	/// for 12% ("its base crit should be 12%"), and "a slight phantom slash trail to each swing so it has more cool motion
	/// animation" (<see cref="FiresawLayer"/>).</item>
	/// </list>
	/// <para>D2: the swing is vanilla's item use, so every client plays it from the synced controls; the pose is a function
	/// of the use's progress and the swing's direction (<see cref="FiresawPlayer"/>, flipped on every side at each use), the
	/// hits are the owner's (vanilla). The right click isn't synced by vanilla (<c>altFunctionUse</c> is the owner's), so a
	/// fire swing spawns a <see cref="FiresawFlame"/> on the owner: a synced, harmless projectile every client reads to draw
	/// the fire. D1: arithmetic only; textures cached in the layer. D0: non-finite poses ignored (<see cref="SwingPose"/>),
	/// spawns through <see cref="SafeSpawn"/>.</para>
	/// <para>Balance: docs/balance/weapons.csv (anchor the Muramasa). Recipe at the Rust Polisher. Art:
	/// art/mechanist/make_firesaw_art.py (the 2026-11-09 saw in previous/).</para>
	/// </summary>
	public class Firesaw : MechanistWeapon
	{
		public const int Damage = 42;                             // user-set 2026-11-10b (39 on 2026-11-10)
		public const int CritBonus = 8;                           // user-set 2026-11-10b: 12% with the player's own 4% (D3 rule 9)
		public const int UseTime = 26;                            // my call (2026-11-10): 108.6 effective DPS, +30.5% on the Muramasa
		public const int Steam = 2, FireSteam = 5;                // user-set 2026-11-10b: a swing, a fire swing
		public const float Knockback = 0.5f;                      // user-set (2026-11-09): "very low"
		public const int OnFireTicks = 180;                       // the Volcano's 3 s
		public const int BarCost = 7, MetalCost = 11, TarCost = 8;   // user-set

		// --- the swing: fractions of the use; angles in the facing frame (radians, 0 ahead, + down, - up) -------------------
		public const float WindEnd = 0.24f, SlashEnd = 0.5f, OverEnd = 0.62f, SettleEnd = 0.85f;
		public const float HitFrom = WindEnd, HitTo = 0.56f;
		public const float High = -2.2f, Low = 1.0f;              // the slash's two ends: up behind the head, down ahead
		public const float PullBack = 0.3f, Overshoot = 0.2f;

		// --- the sprite (FiresawSwing.png, 80x80 frames; FiresawFire.png, 104x104, their bottom-left corners shared) -----
		public const int Size = 80, FireSize = 104, Frames = 3, FrameTicks = 2, Gap = 2;
		public const int GripX = 23, GripY = 57, FireGripY = 81;  // the hand, on the blade's axis
		// measured along the axis from the hand (game px at scale 1): the bar from 22 to the nose at 76, 8.5 px either side
		// of the axis with the teeth; the fire's jet to 109 (two tiles past the nose) and its flames 14 px off the teeth
		public const float BladeStart = 22f, Reach = 77f, FireReach = 109f, BladeRadius = 9f, FireRadius = 13f, FireBelow = 3f;

		private static readonly SoundStyle SwingSound = SoundID.Item1 with { Pitch = -0.35f, Volume = 0.85f, PitchVariance = 0.15f };
		private static readonly SoundStyle RevSound = SoundID.Item22 with { Pitch = -0.1f, Volume = 0.45f, PitchVariance = 0.2f, MaxInstances = 2 };
		private static readonly SoundStyle FireSound = SoundID.Item34 with { Volume = 0.45f, PitchVariance = 0.2f, MaxInstances = 2 };

		public override int SteamCost => Steam;

		/// <summary>The right click infuses the blade with fire: <see cref="FireSteam"/> instead of <see cref="Steam"/>.</summary>
		public override int SteamCostFor(Player player) => player.altFunctionUse == 2 ? FireSteam : Steam;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(FireSteam, OnFireTicks / 60);

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			ItemID.Sets.ItemsThatAllowRepeatedRightClick[Type] = true;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = CritBonus;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.knockBack = Knockback;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noUseGraphic = true;                        // FiresawLayer draws it (the chain runs, the fire burns)
			Item.UseSound = null;                            // the slash plays its own (UseStyle)
			Item.shoot = ModContent.ProjectileType<FiresawFlame>();   // only fire swings spawn it (Shoot)
			Item.shootSpeed = 1f;
			Item.width = 40;
			Item.height = 40;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Orange;
		}

		public override bool AltFunctionUse(Player player) => true;

		public override bool? UseItem(Player player) {
			player.GetModPlayer<FiresawPlayer>().BeginSwing(player);   // every side: the swing's direction
			return base.UseItem(player);                     // the owner pays the steam
		}

		/// <summary>The owner: a fire swing spawns its flame (the synced mark every client draws the fire from).</summary>
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			if (player.altFunctionUse == 2) {
				SafeSpawn.TryNewProjectile(source, player.MountedCenter, Vector2.Zero, type, 0, 0f, out _, player.whoAmI, player.itemAnimationMax);
			}
			return false;
		}

		// ------------------------------------------------------------------------------------------------------------
		// The swing
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>0..1: how far <paramref name="player"/>'s swing has run, <paramref name="ticksBack"/> ticks ago.</summary>
		public static float Done(Player player, int ticksBack = 0) {
			int max = Math.Max(1, player.itemAnimationMax);
			return 1f - (player.itemAnimation + ticksBack) / (float)max;
		}

		private static float EaseInOutCubic(float t) => t < 0.5f ? 4f * t * t * t : 1f - MathF.Pow(-2f * t + 2f, 3f) * 0.5f;

		/// <summary>The blade's facing-frame angle at <paramref name="done"/> of a down-slash (<paramref name="up"/> false) or
		/// an up-slash: from where the last slash ended, pulled back past its start, slashed through to the far end, over it
		/// and back.</summary>
		public static float SwingAngle(float done, bool up) {
			float from = up ? Low : High;                    // where the other slash left the blade
			float to = up ? High : Low;
			float sign = up ? -1f : 1f;                      // the slash's way: down (+) or up (-)
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

		/// <summary><paramref name="player"/>'s blade angle, <paramref name="ticksBack"/> ticks ago (same swing).</summary>
		public static float SwingAngle(Player player, int ticksBack = 0) {
			return SwingAngle(Math.Max(0f, Done(player, ticksBack)), player.GetModPlayer<FiresawPlayer>().Upswing);
		}

		/// <summary>True while the blade is on fire (every client: the owner's synced flame is out).</summary>
		public static bool Burning(Player player) => player.ownedProjectileCounts[ModContent.ProjectileType<FiresawFlame>()] > 0
			|| (player.whoAmI == Main.myPlayer && player.altFunctionUse == 2);

		public override void UseStyle(Player player, Rectangle heldItemFrame) {
			float done = Done(player);
			float prev = Done(player, 1);
			SwingPose.Apply(player, SwingAngle(done, player.GetModPlayer<FiresawPlayer>().Upswing));
			if (Main.dedServ || !(prev < WindEnd && done >= WindEnd)) {
				return;
			}
			SoundEngine.PlaySound(SwingSound, player.Center);      // the slash comes through: a whoosh, the engine revs
			SoundEngine.PlaySound(RevSound, player.Center);
			if (Burning(player)) {
				SoundEngine.PlaySound(FireSound, player.Center);
			}
		}

		/// <summary>Only while the slash comes through; the box is the blade's bounds (vanilla cuts grass and pots with it),
		/// the real test is <see cref="CanMeleeAttackCollideWithNPC"/>.</summary>
		public override void UseItemHitbox(Player player, ref Rectangle hitbox, ref bool noHitbox) {
			float done = Done(player);
			if (done < HitFrom || done >= HitTo) {
				noHitbox = true;
				return;
			}
			bool fire = Burning(player);
			float scale = player.GetAdjustedItemScale(Item);
			float facing = SwingAngle(player);
			Vector2 a = SwingPose.BladePoint(player, player.itemLocation, facing, BladeStart * scale, 0f);
			Vector2 b = SwingPose.BladePoint(player, player.itemLocation, facing, (fire ? FireReach : Reach) * scale, fire ? FireBelow * scale : 0f);
			if (!MathSafety.IsFinite(a) || !MathSafety.IsFinite(b)) {
				noHitbox = true;
				return;
			}
			float r = (fire ? FireRadius : BladeRadius) * scale;
			int left = (int)(MathF.Min(a.X, b.X) - r), top = (int)(MathF.Min(a.Y, b.Y) - r);
			hitbox = new Rectangle(left, top, (int)(MathF.Abs(a.X - b.X) + 2f * r), (int)(MathF.Abs(a.Y - b.Y) + 2f * r));
		}

		/// <summary>The blade as drawn (on fire: with its flames and jet), as a capsule, at this tick's angle and half a tick
		/// and a tick back (it turns up to ~50 degrees a tick through the slash: an enemy between two poses must not slip
		/// through).</summary>
		public override bool? CanMeleeAttackCollideWithNPC(Rectangle meleeAttackHitbox, Player player, NPC target) {
			float done = Done(player);
			if (done < HitFrom || done >= HitTo) {
				return false;
			}
			bool fire = Burning(player);
			float scale = player.GetAdjustedItemScale(Item);
			float now = SwingAngle(player);
			float before = SwingAngle(player, 1);
			Rectangle box = target.Hitbox;
			return BladeHits(player, now, scale, fire, box) || BladeHits(player, (now + before) * 0.5f, scale, fire, box)
				|| BladeHits(player, before, scale, fire, box);
		}

		private static bool BladeHits(Player player, float facing, float scale, bool fire, Rectangle box) {
			SwingPose.Compute(player, facing, out Vector2 hand, out _);
			Vector2 a = SwingPose.BladePoint(player, hand, facing, BladeStart * scale, 0f);
			Vector2 b = SwingPose.BladePoint(player, hand, facing, (fire ? FireReach : Reach) * scale, fire ? FireBelow * scale : 0f);
			return SwingPose.CapsuleHitsRect(a, b, (fire ? FireRadius : BladeRadius) * scale, box);
		}

		public override void OnHitNPC(Player player, NPC target, NPC.HitInfo hit, int damageDone) {
			if (Burning(player)) {
				target.AddBuff(BuffID.OnFire, OnFireTicks);
			}
			if (player.whoAmI == Main.myPlayer && (CogpunkClientConfig.Instance?.ScreenShake ?? true)) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(target.Center, SwingPose.BladeDirection(player, SwingAngle(player)), 1.6f, 8f, 6,
					600f, "Cogpunk:Firesaw"));
			}
			if (Main.dedServ || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < 5; i++) {                       // the teeth bite: sparks (and embers on fire)
				if (SafeSpawn.TryNewDust(target.Center - new Vector2(8f), 16, 16, Burning(player) && i % 2 == 0 ? DustID.Torch : DustID.Iron,
					out Dust spark)) {
					spark.velocity = Main.rand.NextVector2Circular(3.5f, 3.5f) - Vector2.UnitY;
					spark.noGravity = i % 2 == 0;
					spark.scale = 1.1f;
				}
			}
		}

		/// <summary>Every client: metal sparks thrown off the running teeth through the slash (embers come from the flame).</summary>
		public override void MeleeEffects(Player player, Rectangle hitbox) {
			float done = Done(player);
			if (Main.dedServ || done < HitFrom || done >= HitTo || !Main.rand.NextBool(2) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			float facing = SwingAngle(player);
			Vector2 at = SwingPose.BladePoint(player, player.itemLocation, facing, Main.rand.NextFloat(BladeStart, Reach), BladeRadius);
			if (MathSafety.IsFinite(at) && SafeSpawn.TryNewDust(at - new Vector2(2f), 4, 4, DustID.Iron, out Dust spark)) {
				spark.velocity = SwingPose.BladeDirection(player, facing) * 2f + Main.rand.NextVector2Circular(1f, 1f);
				spark.noGravity = true;
				spark.scale = 0.9f;
			}
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<TarnishedBrassBar>(BarCost)
				.AddIngredient<PolishedMetal>(MetalCost)
				.AddIngredient<CondensedTar>(TarCost)
				.AddTile<RustPolisherTile>()
				.Register();
		}
	}
}
