using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// The <see cref="Firesaw"/>'s fire, as a mark (2026-11-10): vanilla keeps the right click to the owner
	/// (<c>Player.altFunctionUse</c> is set only for the local player and never sent, decompiled
	/// <c>ItemCheck_ManageRightClickFeatures</c>), so a fire swing spawns this harmless projectile on the owner; it reaches
	/// every client with the projectile sync, and while it is out <see cref="FiresawLayer"/> draws the blade burning
	/// (<see cref="Firesaw.Burning"/> reads the player's projectile count, which every client keeps for every player,
	/// decompiled <c>Player.UpdateProjectileCaches</c>). It rides its owner's hand, lights the blade and throws embers off it
	/// through the slash, and ends with the swing (or when the next swing starts: a fire swing brings its own).
	/// <para>D0: no damage, no tile collision, a short life it renews only while its swing runs (ai[0] carries the swing's
	/// length). D1: a few lights and at most a couple of dust a tick, on clients.</para>
	/// </summary>
	public class FiresawFlame : CogpunkProjectile
	{
		public override string Texture => "Cogpunk/Content/Mechanist/Weapons/FiresawFire";

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = 60;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			bool first = Projectile.localAI[0] == 0f;
			Projectile.localAI[0] = 1f;
			if (!owner.active || owner.dead || owner.itemAnimation <= 0 || owner.HeldItem.ModItem is not Firesaw
				|| (!first && owner.itemAnimation >= owner.itemAnimationMax)) {
				Projectile.Kill();                               // its swing is over (or the next one began)
				return;
			}
			Projectile.Center = owner.MountedCenter;
			Projectile.timeLeft = 2;
			if (Main.dedServ) {
				return;
			}
			float facing = Firesaw.SwingAngle(owner);
			float scale = owner.GetAdjustedItemScale(owner.HeldItem);
			SwingPose.Compute(owner, facing, out Vector2 hand, out _);
			for (float along = Firesaw.BladeStart; along <= Firesaw.FireReach; along += 29f) {   // 4 lights along the blade
				Lighting.AddLight(SwingPose.BladePoint(owner, hand, facing, along * scale, 0f), 0.85f, 0.45f, 0.12f);
			}
			float done = Firesaw.Done(owner);
			if (done < Firesaw.HitFrom || done >= Firesaw.HitTo || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < 2; i++) {                          // embers thrown off the burning blade through the slash
				Vector2 at = SwingPose.BladePoint(owner, hand, facing, Main.rand.NextFloat(Firesaw.BladeStart, Firesaw.FireReach) * scale,
					Firesaw.FireBelow * scale);
				if (MathSafety.IsFinite(at) && SafeSpawn.TryNewDust(at - new Vector2(4f), 8, 8, DustID.Torch, out Dust ember)) {
					ember.noGravity = true;
					ember.velocity = Main.rand.NextVector2Circular(1.5f, 1.5f) - Vector2.UnitY * 0.6f;
					ember.scale = 1.4f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) => false;   // the fire is drawn with the blade (FiresawLayer)
	}
}
