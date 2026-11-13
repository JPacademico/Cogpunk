using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Projectiles
{
	/// <summary>
	/// The Cogscorpion's sting (<see cref="NPCs.Cogscorpion"/>): the hurting part of its tail strike, a hostile hitbox
	/// <see cref="Size"/> px square held still at the sting's point for <see cref="Lifetime"/> ticks while the tail hangs at full
	/// reach (the scorpion's own frames show it: this draws nothing). Whoever it hits gets a stack of the jade curse
	/// (<see cref="Gems.JadeCursePlayer.Hit"/>; vanilla runs <c>OnHitPlayer</c> on the hit player's client, where the stacks
	/// live, as for the Jade Golem's ray). D2: spawned by the server; D0: still, short-lived, no tiles.
	/// </summary>
	public class CogscorpionSting : CogpunkProjectile
	{
		public const int Size = 40;
		public const int Lifetime = NPCs.Cogscorpion.StrikeHoldTicks;

		public override string Texture => TextureFallback.Placeholder;      // never drawn

		public override void SetDefaults() {
			Projectile.width = Projectile.height = Size;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Lifetime;
			Projectile.hide = true;
		}

		public override bool ShouldUpdatePosition() => false;

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			Gems.JadeCursePlayer.Hit(target);
		}

		public override bool PreDraw(ref Color lightColor) => false;
	}
}
