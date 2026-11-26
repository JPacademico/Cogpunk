using System;
using System.Collections.Generic;
using Cogpunk.Content.Dungeon.Items;
using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Mechanist;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// Metal Wrench (user-set 2026-10-30): a big, slow wrench of polished metal swung like a sword (<see cref="UseTime"/>
	/// ticks a swing). Redrawn 2026-11-03 (user: "a big thick metal wrench the size of a sword like the Blade of Grass"):
	/// a 68x68 pipe wrench drawn from the user's reference image (a long silver handle with a hanging hole, the knurled
	/// nut, the heel and hook jaws), the Blade of Grass's 1.4.4 sprite size (a swing's hitbox is the sprite's frame, decompiled
	/// <c>Player.ItemCheck_GetMeleeHitbox</c>; the item's own 40x40 is only its hitbox on the ground, as the Blade of
	/// Grass's) that deals +<see cref="MechanicalBonus"/>% to mechanical enemies
	/// (<see cref="CogpunkSets.Mechanical"/>, like the Screwdriver).
	/// <para>It swings towards the cursor: each swing, auto-swing included, turns the player to the cursor's side as it starts
	/// (user, 2026-11-26: it kept the first click's side "until the player lets go and clicks again"; vanilla only turns a
	/// player for items that shoot, decompiled <c>Player.ItemCheck_Shoot</c>). Its right-click parry was taken off on
	/// 2026-11-26 (user: "remove the parry passive as we will use in another weapon on the future"): the parry and riposte
	/// live on in <see cref="MetalWrenchPlayer"/> for a weapon that declares <see cref="IParryWeapon"/>.</para>
	/// Balance: docs/balance/weapons.csv (anchor: Blade of Grass).
	/// <para><b>The slam</b> (user, 2026-11-05b: "change the attack animation for the metal wrench to look like a faster (in
	/// animation, not in use time) slam that stops on the ground/player foot line, like the updated terraria chlorophyte
	/// claymore does"; 1.4.5.7 reworked the Claymore into a ground slam, terraria.wiki.gg): the same <see cref="UseTime"/>,
	/// a new curve over it (fractions of the use, so attack speed scales it). It heaves the wrench up from the ground and
	/// back over the head (to <see cref="LiftEnd"/>), hangs there (<see cref="HangEnd"/>), slams it down through
	/// <see cref="RaisedAngle"/> to the ground in a sixth of the use, accelerating (<see cref="ImpactAt"/>: the jaws strike
	/// the player's foot line, <see cref="GroundAngle"/>, never below it), recoils off it (<see cref="BounceEnd"/>) and rests
	/// there to the end. It hits only while it comes down and recoils (vanilla's one hit per enemy a swing), along the head
	/// and the shaft as drawn (<see cref="CanMeleeAttackCollideWithNPC"/>, swept over the last tick). The strike throws the
	/// ground's own dust and sparks with a heavy thud and shakes the swinger's screen a little; in the air it whiffs.
	/// The arm turns with it (composite arms, <see cref="SwingPose"/>); <see cref="MetalWrenchSmearLayer"/> trails the fast
	/// part. D2: everything follows the synced use (itemAnimation, direction) on every client; only the hits are the
	/// owner's, as vanilla's. D1: arithmetic only.</para>
	/// </summary>
	public class MetalWrench : CogpunkItem
	{
		/// <summary>32 (user-set 2026-10-30), +20% (user, 2026-11-05: "increase the damage of the metal wrench in 20% since
		/// it does not shoot projectiles"): 38.4, rounded to 38; 4 less (user, 2026-11-26: "nerf metal wrench damage by 4
		/// points"): 34.</summary>
		public const int Damage = 34;
		public const int UseTime = 30;
		public const int MechanicalBonus = 50;            // percent


		// --- the slam (2026-11-05b): fractions of the use; angles in the facing frame (radians, 0 ahead, + down) -------
		public const float LiftEnd = 0.2f, HangEnd = 0.26f, ImpactAt = 0.42f, BounceEnd = 0.54f;
		public const float RaisedAngle = -2.7f;           // up and behind the head
		public const float HangDrift = 0.06f;             // the wind-up's last inch further back
		public const float BounceLift = 0.14f;            // the recoil off the ground
		public const float RestMin = -0.5f, RestMax = 1.2f;
		// the sprite measured along its diagonal from the handle corner (game px at scale 1; MetalWrench.png): the shaft from
		// 14 px (4 px below the diagonal), the jaws from 44 to 78 px, 14 px either side
		public const float ShaftStart = 14f, HeadStart = 44f, HeadEnd = 78f, ShaftBelow = 4f, ShaftRadius = 6f, HeadRadius = 14f;
		private static readonly SoundStyle SwingSound = SoundID.Item1 with { Pitch = -0.45f, Volume = 0.9f };
		private static readonly SoundStyle ThudSound = SoundID.DD2_MonkStaffGroundImpact with { Pitch = -0.25f, Volume = 0.85f, MaxInstances = 3 };
		private static readonly SoundStyle WhiffSound = SoundID.DD2_MonkStaffGroundMiss with { Pitch = -0.2f, Volume = 0.6f, MaxInstances = 3 };

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MechanicalBonus);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = 2;                                 // + the player's base 4% = 6% (user-set)
			Item.knockBack = 6.5f;
			Item.DamageType = DamageClass.Melee;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.UseSound = null;                          // the slam plays its whoosh as it comes down (UseStyle)
			Item.width = 40;
			Item.height = 40;
			Item.value = Item.sellPrice(silver: 60);
			Item.rare = ItemRarityID.Orange;
		}

		/// <summary>The owner turns to the cursor's side as every swing starts, auto-swing included (vanilla calls this on every
		/// tick of a swing that shoots nothing, so only on its first: a turn mid-swing would flip the slam); the direction
		/// reaches the other clients with the player's controls, as vanilla's own turns do.</summary>
		public override bool? UseItem(Player player) {
			if (player.whoAmI == Main.myPlayer && player.ItemAnimationJustStarted) {
				player.ChangeDir(Main.MouseWorld.X >= player.Center.X ? 1 : -1);
			}
			return null;
		}

		public override void ModifyHitNPC(Player player, NPC target, ref NPC.HitModifiers modifiers) {
			if (CogpunkSets.IsMechanical(target)) {
				modifiers.SourceDamage *= 1f + MechanicalBonus / 100f;
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// The slam
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>0..1: how far <paramref name="player"/>'s swing has run (every side counts the same synced ticks).</summary>
		public static float Done(Player player, int ticksBack = 0) {
			int max = Math.Max(1, player.itemAnimationMax);
			return 1f - (player.itemAnimation + ticksBack) / (float)max;
		}

		/// <summary>The facing-frame angle at which the jaws' lower edge meets the foot line: the hand rides the arm
		/// (<c>Player.GetFrontHandPosition</c>, Full: 10 px out along the arm, 2 px up, 3 px across it), so the edge's height
		/// below the arm's pivot is <c>(10 + L) sin a + (3 + W) cos a - 2</c>; that equals the pivot's height over the feet at
		/// <c>a = asin(D / R) - atan2(3 + W, 10 + L)</c>. Upright gravity (vanilla mirrors the pose after).</summary>
		public static float GroundAngle(Player player, float scale) {
			float reach = 10f + HeadEnd * scale;
			float below = 3f + HeadRadius * scale;
			float drop = (player.gravDir == -1f ? player.MountedCenter.Y - player.position.Y : player.position.Y + player.height - player.MountedCenter.Y) + 2f;
			float r = MathF.Sqrt(reach * reach + below * below);
			float angle = MathF.Asin(MathHelper.Clamp(drop / r, -1f, 1f)) - MathF.Atan2(below, reach);
			return float.IsFinite(angle) ? MathHelper.Clamp(angle, RestMin, RestMax) : 0f;
		}

		/// <summary>The slam's facing-frame angle at <paramref name="done"/> of the use.</summary>
		public static float SlamAngle(float done, float ground) {
			if (done < LiftEnd) {
				return MathHelper.Lerp(ground, RaisedAngle, SwingPose.EaseOutCubic(SwingPose.Phase(done, 0f, LiftEnd)));
			}
			if (done < HangEnd) {
				return RaisedAngle - HangDrift * SwingPose.Phase(done, LiftEnd, HangEnd);
			}
			if (done < ImpactAt) {
				return MathHelper.Lerp(RaisedAngle - HangDrift, ground, SwingPose.EaseInCubic(SwingPose.Phase(done, HangEnd, ImpactAt)));
			}
			if (done < BounceEnd) {
				return ground - BounceLift * MathF.Sin(MathHelper.Pi * SwingPose.Phase(done, ImpactAt, BounceEnd));
			}
			return ground;
		}

		/// <summary>The slam's angle for <paramref name="player"/>, <paramref name="ticksBack"/> ticks ago.</summary>
		public float SlamAngle(Player player, int ticksBack = 0) {
			return SlamAngle(Done(player, ticksBack), GroundAngle(player, player.GetAdjustedItemScale(Item)));
		}

		public override void UseStyle(Player player, Rectangle heldItemFrame) {
			float done = Done(player);
			float prev = Done(player, 1);
			float facing = SlamAngle(player);
			SwingPose.Apply(player, facing);
			if (Main.dedServ) {
				return;
			}
			if (prev < HangEnd && done >= HangEnd) {
				SoundEngine.PlaySound(SwingSound, player.Center);          // the whoosh as it comes down
			}
			if (prev < ImpactAt && done >= ImpactAt) {
				Impact(player, facing);
			}
		}

		/// <summary>Clients: the jaws strike the foot line. On the ground: the ground's own dust (vanilla's
		/// <c>Collision.HitTiles</c>), sparks and a puff, a heavy thud, a small punch of the swinger's camera (behind the
		/// Screen Shake option); in the air: a whiff. <c>Collision.SolidCollision</c> and <c>HitTiles</c> clamp their tile
		/// ranges to the world (decompiled), so a swing at the world's edge is safe.</summary>
		private void Impact(Player player, float facing) {
			float scale = player.GetAdjustedItemScale(Item);
			Vector2 jaw = SwingPose.BladePoint(player, player.itemLocation, facing, HeadEnd * scale * 0.85f, HeadRadius * scale * 0.6f);
			Vector2 probe = new(jaw.X - 8f, jaw.Y - 4f);
			if (!MathSafety.IsFinite(probe)) {
				return;
			}
			if (!Collision.SolidCollision(probe, 16, 12, true)) {
				SoundEngine.PlaySound(WhiffSound, jaw);
				return;
			}
			SoundEngine.PlaySound(ThudSound, jaw);
			if (CogpunkClientConfig.RollEffect()) {
				Collision.HitTiles(probe, new Vector2(0f, 3f), 16, 12);
				for (int i = 0; i < 5; i++) {
					if (SafeSpawn.TryNewDust(probe, 16, 8, DustID.Iron, out Dust spark)) {
						spark.velocity = new Vector2(Main.rand.NextFloat(-2.5f, 2.5f), -Main.rand.NextFloat(1.5f, 4f));
						spark.noGravity = false;
					}
				}
				if (SafeSpawn.TryNewDust(probe, 16, 8, DustID.Smoke, out Dust puff, 0f, -0.6f, 140, default, 1.2f)) {
					puff.noGravity = true;
				}
			}
			if (player.whoAmI == Main.myPlayer && (CogpunkClientConfig.Instance?.ScreenShake ?? true)) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(jaw, Vector2.UnitY, 2.5f, 8f, 10, 800f, "Cogpunk:WrenchSlam"));
			}
		}

		/// <summary>Only while it comes down and recoils; the box is the jaws' bounds (vanilla still cuts grass and pots with
		/// it), the real test is <see cref="CanMeleeAttackCollideWithNPC"/>.</summary>
		public override void UseItemHitbox(Player player, ref Rectangle hitbox, ref bool noHitbox) {
			float done = Done(player);
			if (done < HangEnd || done >= BounceEnd) {
				noHitbox = true;
				return;
			}
			float scale = player.GetAdjustedItemScale(Item);
			float facing = SlamAngle(player);
			Vector2 a = SwingPose.BladePoint(player, player.itemLocation, facing, HeadStart * scale, 0f);
			Vector2 b = SwingPose.BladePoint(player, player.itemLocation, facing, HeadEnd * scale, 0f);
			if (!MathSafety.IsFinite(a) || !MathSafety.IsFinite(b)) {
				noHitbox = true;
				return;
			}
			float r = HeadRadius * scale;
			int left = (int)(MathF.Min(a.X, b.X) - r), top = (int)(MathF.Min(a.Y, b.Y) - r);
			hitbox = new Rectangle(left, top, (int)(MathF.Abs(a.X - b.X) + 2f * r), (int)(MathF.Abs(a.Y - b.Y) + 2f * r));
		}

		/// <summary>The wrench as drawn: the shaft and the jaws as two capsules, at this tick's angle and half a tick and a
		/// tick back (it turns ~30 degrees a tick coming down, and an enemy between two poses must not slip through).</summary>
		public override bool? CanMeleeAttackCollideWithNPC(Rectangle meleeAttackHitbox, Player player, NPC target) {
			float scale = player.GetAdjustedItemScale(Item);
			float ground = GroundAngle(player, scale);
			float now = SlamAngle(Done(player), ground);
			float before = SlamAngle(Done(player, 1), ground);
			Rectangle box = target.Hitbox;
			return BladeHits(player, now, scale, box) || BladeHits(player, (now + before) * 0.5f, scale, box) || BladeHits(player, before, scale, box);
		}

		private static bool BladeHits(Player player, float facing, float scale, Rectangle box) {
			SwingPose.Compute(player, facing, out Vector2 hand, out _);
			Vector2 shaftA = SwingPose.BladePoint(player, hand, facing, ShaftStart * scale, ShaftBelow * scale);
			Vector2 shaftB = SwingPose.BladePoint(player, hand, facing, HeadStart * scale, ShaftBelow * scale);
			Vector2 headA = SwingPose.BladePoint(player, hand, facing, HeadStart * scale, 0f);
			Vector2 headB = SwingPose.BladePoint(player, hand, facing, HeadEnd * scale, 0f);
			return SwingPose.CapsuleHitsRect(headA, headB, HeadRadius * scale, box) || SwingPose.CapsuleHitsRect(shaftA, shaftB, ShaftRadius * scale, box);
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<PolishedMetal>(22)
				.AddIngredient<CondensedTar>(4)
				.AddIngredient<RustedCog>(19)                          // 16 -> 19, x1.2 rounded (user, 2026-11-26)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
