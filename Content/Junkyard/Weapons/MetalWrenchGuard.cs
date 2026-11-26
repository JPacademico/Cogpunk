using System;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The Metal Wrench on guard (the parry window, <see cref="WrenchParry.ParryTicks"/>): the wrench swings up from the hip
	/// in <see cref="RaiseTicks"/> ticks and is held up across the body, head high, in the front hand (vanilla's composite
	/// arm, posed the way its own swings pose it: decompiled <c>Player.ItemCheck_ApplyUseStyle_Inner</c>,
	/// <c>SetCompositeArmFront</c> + <c>GetFrontHandPosition</c>). Purely visual: the window itself is
	/// <see cref="MetalWrenchPlayer"/>'s, which kills this when the guard ends early (a parry).
	/// <para>D2: the owner spawns it, so every client sees the guard; it only reads its owner. D1: no allocation. Drawn by the
	/// player as their held projectile with the item's own sprite, rotated to the pose like any swung weapon.</para>
	/// </summary>
	public class MetalWrenchGuard : CogpunkProjectile
	{
		public const int RaiseTicks = 6;
		private const float RestAngle = 0.35f;            // radians, facing right: the wrench low and forward
		private const float GuardAngle = -1.4f;           // held up across the body, head high
		private const float ArmAngle = -1.05f;            // the front arm raised forward
		private const float SpriteAxis = -MathHelper.PiOver4;   // the item sprite points to the top right
		private const float GripInsetX = 16f, GripInsetY = 11f;   // the hand on the handle, in from the bottom-left corner (make_tar_weapons.wrench_grip_inset)

		public override string Texture => "Cogpunk/Content/Junkyard/Weapons/MetalWrench";

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.hide = true;                        // drawn by the player as heldProj
			Projectile.timeLeft = WrenchParry.ParryTicks + 2;
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage() => false;

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player player = Main.player[Projectile.owner];
			if (!player.active || player.dead || !WrenchParry.Wields(player)) {
				Projectile.Kill();
				return;
			}
			int age = WrenchParry.ParryTicks + 2 - Projectile.timeLeft;
			if (age == 0 && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item1 with { Pitch = -0.6f, Volume = 0.6f }, player.Center);
			}
			player.heldProj = Projectile.whoAmI;
			Projectile.direction = Projectile.spriteDirection = player.direction;
			float raise = MathHelper.Clamp(age / (float)RaiseTicks, 0f, 1f);
			raise = 1f - (1f - raise) * (1f - raise);
			float arm = MathHelper.Lerp(0.6f, ArmAngle, raise) - MathHelper.PiOver2;
			if (player.direction < 0) {
				arm = -arm;
			}
			player.SetCompositeArmFront(true, Player.CompositeArmStretchAmount.Full, arm);
			Projectile.Center = player.GetFrontHandPosition(Player.CompositeArmStretchAmount.Full, arm);
			Projectile.velocity = Vector2.Zero;
			float axis = MathHelper.Lerp(RestAngle, GuardAngle, raise);
			// a held guard trembles a hair as blows threaten; the rotation is the sprite's turn from its own axis
			axis += (float)Math.Sin(age * 0.9f) * 0.015f;
			Projectile.rotation = player.direction > 0 ? axis - SpriteAxis : -(axis - SpriteAxis);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			bool left = Projectile.direction < 0;
			Vector2 origin = left ? new Vector2(texture.Width - GripInsetX, texture.Height - GripInsetY) : new Vector2(GripInsetX, texture.Height - GripInsetY);
			Vector2 position = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Main.EntitySpriteDraw(texture, position, null, Projectile.GetAlpha(lightColor), Projectile.rotation, origin, 1f,
				left ? SpriteEffects.FlipHorizontally : SpriteEffects.None);
			return false;
		}
	}
}
